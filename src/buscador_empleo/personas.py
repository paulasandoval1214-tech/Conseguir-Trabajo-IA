"""Lista de personas y páginas para seguir o conectar en LinkedIn.

Por qué existe
--------------
Las búsquedas de LinkedIn se agotan rápido (límite por cuenta), pero el feed de inicio no:
lo que publican las personas que sigues te llega solo. Si la candidata sigue o conecta con
quienes publican vacantes que SÍ le encajan (reclutadoras, líderes de gestión humana,
páginas de empleo), su feed se vuelve una fuente de vacantes que no gasta búsquedas, y de
paso su perfil queda a la vista de quien contrata.

Qué hace
--------
Lee lo ya extraído (`datos/crudo/*.json`) y la columna "Fuente" del historial, pasa cada
post por las reglas de `importar` y arma un ranking de autores:
    puntaje = 3 × (posts con vacante útil) + (posts con correo)
Escribe:
    datos/personas_para_conectar.csv   (para filtrar / marcar en Excel)
    datos/personas_para_conectar.md    (para leer rápido)
La columna "estado" (Pendiente / Seguido / Conectado / Descartar) y "notas" se conservan
entre ejecuciones: márcalas a mano en el CSV y el siguiente ranking las respeta.

Qué NO hace
-----------
No sigue, no conecta ni escribe a nadie: eso lo hace la persona, a mano y de a pocos
(10–15 por día). Solo usa autores de publicaciones de vacantes que ya se vieron, no
recorre perfiles. La lista queda en datos/ (ignorada por git).
"""

from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path
from urllib.parse import quote

from . import filtros
from .config import Perfil
from .extraccion import limpiar_autor, normalizar, post_a_vacantes
from .historial import Historial
from .modelos import PostCrudo

COLUMNAS = ["estado", "puntaje", "nombre", "tipo", "url", "posts", "utiles", "lineas", "cargos",
            "empresas", "visto", "notas"]
ESTADOS = ("Pendiente", "Seguido", "Conectado", "Descartar")
RE_FUENTE = re.compile(r"linkedin\s*\(([^)]+)\)", re.IGNORECASE)
RE_AGREGADOR = re.compile(r"ofertas? ?de ?trabajo|empleos?|vacantes|trabajo ?si ?hay|bolsa|jobs|talent(o)? ?hub",
                          re.IGNORECASE)
RE_EMPRESA = re.compile(
    r"\b(s\.?a\.?s?|ltda|group|grupo|colombia|banco|compa[ñn][ií]as?|talent|security|world|consulting|"
    r"hoteles?|cine|universidad|fundaci[oó]n|corporaci[oó]n|cl[ií]nica|laboratorios?|seguros|bpo|"
    r"outsourcing|soluciones|servicios|digital|est|temporales?|inc|corp|s\.a)\b",
    re.IGNORECASE)


def _clave(nombre: str, url: str) -> str:
    return url.rstrip("/").lower() if url else "nombre:" + normalizar(nombre)


def tipo_de(nombre: str, url: str) -> str:
    if "/company/" in url or "/school/" in url:
        return "agregador" if RE_AGREGADOR.search(nombre) else "empresa"
    if "/in/" in url:
        return "persona"
    if RE_AGREGADOR.search(nombre) or re.search(r"\.(co|com)\b", nombre):
        return "agregador"
    palabras = nombre.split()
    if RE_EMPRESA.search(nombre) or len(palabras) == 1 or (nombre.isupper() and len(nombre) > 4):
        return "empresa?"
    return "persona?" if 2 <= len(palabras) <= 5 else "empresa?"


def url_busqueda(nombre: str, tipo: str) -> str:
    """Si no hay enlace al perfil, una búsqueda de LinkedIn por el nombre (para hacerlo a mano)."""
    seccion = "people" if tipo.startswith("persona") else "companies"
    return f"https://www.linkedin.com/search/results/{seccion}/?keywords={quote(nombre)}"


def agrupar(posts_con_fecha: list[tuple[PostCrudo, str]], perfil: Perfil,
            fuentes_historial: list[tuple[str, str, str, str]] | None = None) -> list[dict]:
    """Agrupa por autor. `fuentes_historial` = [(nombre, linea, fecha, correo)] del historial."""
    propio = normalizar(perfil.candidato.get("nombre", ""))
    grupos: dict[str, dict] = {}
    correos_contados: set[str] = set()  # para no sumar dos veces el mismo post con otro nombre

    def fila(nombre: str, url: str) -> dict | None:
        nombre = limpiar_autor(nombre)
        if len(nombre) < 3 or (propio and normalizar(nombre) == propio):
            return None
        k = _clave(nombre, url)
        f = grupos.setdefault(k, {"nombre": nombre, "url": url, "posts": 0, "utiles": 0, "lineas": set(),
                                  "cargos": [], "empresas": set(), "visto": "", "claves": set()})
        if url and not f["url"]:
            f["url"] = url
        return f

    for post, fecha in posts_con_fecha:
        f = fila(post.autor, post.autor_url)
        if f is None:
            continue
        vs = post_a_vacantes(post, perfil.correos_ignorar)
        if not vs and not post.sin_correo:
            continue
        # El mismo post puede venir del crudo y de vacantes_*.json: se cuenta una vez.
        clave_post = ",".join(sorted(v.correo for v in vs)) or normalizar(post.texto[:120])
        if clave_post in f["claves"]:
            continue
        f["claves"].add(clave_post)
        correos_contados.update(v.correo for v in vs)
        f["posts"] += 1
        f["visto"] = max(f["visto"], fecha)
        util = False
        for v in vs:
            v.linea, v.puntaje = filtros.clasificar_linea(v, perfil)
            if not filtros.motivo_descarte(v, perfil, set()):
                util = True
                f["lineas"].add(v.linea)
                if v.cargo and v.cargo not in f["cargos"]:
                    f["cargos"].append(v.cargo)
                if v.empresa:
                    f["empresas"].add(v.empresa)
        f["utiles"] += 1 if util else 0

    for nombre, linea, fecha, correo in fuentes_historial or []:
        if correo.lower() in correos_contados:
            continue  # ese post ya se contó desde el crudo (con el nombre completo del autor)
        f = fila(nombre, "")
        if f is None:
            continue
        correos_contados.add(correo.lower())
        f["claves"].add(correo.lower())
        f["posts"] += 1
        f["utiles"] += 1
        if linea:
            f["lineas"].add(linea)
        f["visto"] = max(f["visto"], fecha)

    salida = []
    for f in grupos.values():
        if not f["utiles"] and f["posts"] < 2:
            continue  # un solo post sin vacante útil no justifica seguir a alguien
        tipo = tipo_de(f["nombre"], f["url"])
        salida.append({
            "estado": "Pendiente", "puntaje": 3 * f["utiles"] + f["posts"], "nombre": f["nombre"],
            "tipo": tipo, "url": f["url"] or url_busqueda(f["nombre"], tipo), "posts": f["posts"],
            "utiles": f["utiles"], "lineas": ", ".join(sorted(f["lineas"])),
            "cargos": "; ".join(f["cargos"][:3]), "empresas": ", ".join(sorted(f["empresas"]))[:80],
            "visto": f["visto"], "notas": "",
        })
    return sorted(salida, key=lambda r: (-r["puntaje"], r["nombre"]))


def fuentes_del_historial(hist: Historial) -> list[tuple[str, str, str, str]]:
    """Nombres que aparecen en la columna Fuente: "LinkedIn (Ana P.)"."""
    salida = []
    for r in hist.registros:
        m = RE_FUENTE.search(r.fuente or "")
        if m:
            # "LinkedIn (Empresa / Ana P.)": la última parte es quien publicó.
            nombre = m.group(1).split("/")[-1].strip()
            salida.append((nombre, r.linea, r.fecha, r.correo))
    return salida


def leer_estados(ruta_csv: Path) -> dict[str, dict]:
    """Estados y notas puestos a mano en una ejecución anterior."""
    if not ruta_csv.exists():
        return {}
    estados = {}
    with ruta_csv.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            url = r.get("url", "")
            k = _clave(r.get("nombre", ""), url if "/search/" not in url else "")
            estados[k] = {"estado": r.get("estado") or "Pendiente", "notas": r.get("notas", "")}
    return estados


def escribir(filas: list[dict], carpeta: Path) -> tuple[Path, Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_csv = carpeta / "personas_para_conectar.csv"
    ruta_md = carpeta / "personas_para_conectar.md"
    previos = leer_estados(ruta_csv)
    for f in filas:
        k = _clave(f["nombre"], f["url"] if "/search/" not in f["url"] else "")
        if k in previos:
            f["estado"], f["notas"] = previos[k]["estado"], previos[k]["notas"]
    with ruta_csv.open("w", encoding="utf-8-sig", newline="") as fh:  # utf-8-sig: Excel lee bien las tildes
        w = csv.DictWriter(fh, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    pendientes = [f for f in filas if f["estado"] == "Pendiente"]
    lineas_md = [
        f"# Personas y páginas para seguir o conectar ({dt.date.today().isoformat()})",
        "",
        "Ranking de quienes publican vacantes que encajan con el perfil. **Conectar a mano**, de a",
        "10–15 por día. Marca la columna `estado` en el CSV (Pendiente / Seguido / Conectado /",
        "Descartar): la próxima ejecución lo respeta.",
        "",
        f"Total: {len(filas)} · Pendientes: {len(pendientes)}",
        "",
        "| # | Estado | Nombre | Tipo | Útiles | Posts | Líneas | Ejemplos de cargos | Enlace |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, f in enumerate(filas, 1):
        enlace = f"[perfil]({f['url']})" if "/search/" not in f["url"] else f"[buscar]({f['url']})"
        lineas_md.append(f"| {i} | {f['estado']} | {f['nombre']} | {f['tipo']} | {f['utiles']} | {f['posts']} | "
                         f"{f['lineas']} | {f['cargos']} | {enlace} |")
    ruta_md.write_text("\n".join(lineas_md) + "\n", encoding="utf-8")
    return ruta_csv, ruta_md
