"""Gmail API para uso local: borradores con CV adjunto, adjuntar CVs y revisar respuestas.

Nunca envía correos: solo crea o actualiza borradores. La persona revisa y
da "Enviar".

Requiere (solo en modo local):
    pip install google-api-python-client google-auth-oauthlib
y un `credentials.json` de Google Cloud (ver docs/INSTALACION_WINDOWS.md).
"""

from __future__ import annotations

import base64
import html
import mimetypes
import re
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from .config import Perfil
from .extraccion import normalizar
from .historial import Historial, hoy
from .redaccion import Borrador

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

RE_RECHAZO = re.compile(
    r"no (fue|has sido|ha sido) seleccionad|no continua|no continuar|otro candidato|otros candidatos|"
    r"perfil no se ajusta|no se ajusta al perfil|decidimos avanzar con|lamentamos informar|"
    r"en esta ocasion no|proceso ha sido cerrado|vacante (fue )?cubierta"
)
RE_AVANCE = re.compile(
    r"entrevista|prueba tecnica|prueba psicotecnica|agendar|citacion|disponibilidad para|"
    r"siguiente etapa|continuar en el proceso|te queremos conocer|assessment"
)


def servicio(perfil: Perfil) -> Any:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "Falta instalar las librerías de Gmail: pip install -r requirements-local.txt"
        ) from e

    cred_path = perfil.resolver(perfil.gmail.get("credenciales", "secretos/credentials.json"))
    token_path = perfil.resolver(perfil.gmail.get("token", "secretos/token.json"))
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not cred_path.exists():
                raise SystemExit(f"No encuentro {cred_path}. Sigue docs/INSTALACION_WINDOWS.md")
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def firma_html(svc: Any, correo: str = "") -> str:
    """Firma configurada en Gmail web (la API no la agrega sola)."""
    try:
        alias = svc.users().settings().sendAs().list(userId="me").execute().get("sendAs", [])
    except Exception:
        return ""
    for a in alias:
        if (correo and a.get("sendAsEmail", "").lower() == correo.lower()) or (not correo and a.get("isDefault")):
            return a.get("signature", "") or ""
    return alias[0].get("signature", "") if alias else ""


def _mime(para: str, asunto: str, texto: str, firma: str, adjunto: Path | None,
          remitente: str = "") -> EmailMessage:
    msg = EmailMessage()
    msg["To"] = para
    msg["Subject"] = asunto
    if remitente:
        msg["From"] = remitente
    msg.set_content(texto + ("\n\n--\n" + re.sub(r"<[^>]+>", " ", firma) if firma else ""))
    cuerpo_html = "<div dir=\"auto\">" + html.escape(texto).replace("\n", "<br>") + "</div>"
    if firma:
        cuerpo_html += "<br><div class=\"gmail_signature\">" + firma + "</div>"
    msg.add_alternative(cuerpo_html, subtype="html")
    if adjunto:
        tipo, _ = mimetypes.guess_type(adjunto.name)
        principal, sub = (tipo or "application/pdf").split("/")
        msg.add_attachment(adjunto.read_bytes(), maintype=principal, subtype=sub, filename=adjunto.name)
    return msg


def _raw(msg: EmailMessage) -> str:
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def crear_borrador(svc: Any, b: Borrador, firma: str = "", remitente: str = "") -> str:
    cv = Path(b.cv)
    if not cv.exists():
        raise FileNotFoundError(f"No existe el CV {cv}")
    msg = _mime(b.para, b.asunto, b.cuerpo, firma, cv, remitente)
    d = svc.users().drafts().create(userId="me", body={"message": {"raw": _raw(msg)}}).execute()
    return d["id"]


# --------------------------------------------------------------------------- adjuntar
def _texto_mensaje(payload: dict) -> tuple[str, str, bool]:
    """(texto_plano, html, tiene_adjunto) de un payload de Gmail."""
    plano, rico, adj = "", "", False
    pila = [payload]
    while pila:
        p = pila.pop()
        if p.get("filename"):
            adj = True
        data = p.get("body", {}).get("data")
        if data and p.get("mimeType") == "text/plain":
            plano += base64.urlsafe_b64decode(data).decode("utf-8", "replace")
        if data and p.get("mimeType") == "text/html":
            rico += base64.urlsafe_b64decode(data).decode("utf-8", "replace")
        pila.extend(p.get("parts", []) or [])
    return plano, rico, adj


def adivinar_linea(asunto: str, texto: str, perfil: Perfil) -> str:
    t = normalizar(asunto + " " + texto)
    mejor, mejor_p = "", 0
    for clave, l in perfil.lineas.items():
        p = sum(1 for k in l.palabras_clave + [l.experiencia_correo] if k and normalizar(k) in t)
        if p > mejor_p:
            mejor, mejor_p = clave, p
    return mejor


def adjuntar_pendientes(svc: Any, perfil: Perfil, simular: bool = False) -> list[dict]:
    """Agrega el CV correcto a los borradores que no tienen adjunto."""
    hechos = []
    firma = firma_html(svc, perfil.candidato.get("correo_envio", ""))
    resp = svc.users().drafts().list(userId="me", q="-has:attachment", maxResults=100).execute()
    for d in resp.get("drafts", []):
        full = svc.users().drafts().get(userId="me", id=d["id"], format="full").execute()
        msg = full["message"]
        cab = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        para, asunto = cab.get("to", ""), cab.get("subject", "")
        plano, _rico, tiene = _texto_mensaje(msg["payload"])
        if tiene or not para:
            continue
        linea = adivinar_linea(asunto, plano, perfil)
        if not linea:
            hechos.append({"para": para, "asunto": asunto, "resultado": "sin línea, no se tocó"})
            continue
        cv = perfil.resolver(perfil.lineas[linea].cv)
        if not simular:
            texto = plano.strip()
            ya_firma = bool(firma) and normalizar(re.sub(r"<[^>]+>", " ", firma))[:30] in normalizar(texto)
            nuevo = _mime(para, asunto, texto, "" if ya_firma else firma, cv)
            svc.users().drafts().update(
                userId="me", id=d["id"],
                body={"id": d["id"], "message": {"raw": _raw(nuevo), "threadId": msg.get("threadId")}},
            ).execute()
        hechos.append({"para": para, "asunto": asunto, "resultado": f"adjuntado {cv.name}"})
    return hechos


# ------------------------------------------------------------------------- respuestas
def _consulta_remitente(correo: str) -> str:
    dominio = correo.split("@")[-1]
    publicos = {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "live.com"}
    return f"from:{correo}" if dominio in publicos else f"from:@{dominio}"


def revisar_respuestas(svc: Any, h: Historial, dias: int = 60) -> list[dict]:
    """Marca enviados y detecta rechazos/avances en la bandeja de entrada."""
    cambios = []
    for r in h.registros:
        if r.estado in ("Rechazado", "Oferta", "Descartada"):
            continue
        if r.estado in ("Borrador listo", "Programado"):
            env = svc.users().messages().list(userId="me", q=f"in:sent to:{r.correo}", maxResults=1).execute()
            if env.get("messages"):
                r.estado = "Enviado"
                cambios.append({"correo": r.correo, "estado": "Enviado"})
        if r.estado not in ("Enviado", "En proceso"):
            continue
        q = f"{_consulta_remitente(r.correo)} newer_than:{dias}d -in:sent"
        res = svc.users().messages().list(userId="me", q=q, maxResults=5).execute()
        for m in res.get("messages", []):
            full = svc.users().messages().get(userId="me", id=m["id"], format="full").execute()
            plano, rico, _ = _texto_mensaje(full["payload"])
            t = normalizar(plano or re.sub(r"<[^>]+>", " ", rico))
            if RE_RECHAZO.search(t):
                r.estado, r.notas = "Rechazado", (r.notas + f" | rechazo {hoy()}").strip(" |")
            elif RE_AVANCE.search(t):
                r.estado, r.notas = "En proceso", (r.notas + f" | respuesta {hoy()}").strip(" |")
            else:
                continue
            cambios.append({"correo": r.correo, "estado": r.estado})
            break
    return cambios
