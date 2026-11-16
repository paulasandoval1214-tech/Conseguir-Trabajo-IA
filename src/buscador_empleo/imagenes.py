"""Lectura de afiches de vacantes (imágenes de LinkedIn). Pensado para el computador local.

Por qué existe
--------------
Muchas empresas publican la vacante como un afiche: el texto del post dice "¡Únete a
nuestro equipo!" y el cargo, la ciudad y el correo están SOLO dentro de la imagen. El
extractor de LinkedIn (extractor/linkedin_posts.js) marca esos posts con `sinCorreo: true`
y guarda las URLs de sus imágenes. Este módulo las lee y deja lo leído en
`PostCrudo.texto_imagen`, para que `importar` las trate como cualquier otro post.

Cómo lee (de lo más barato a lo más caro)
-----------------------------------------
1. Texto alternativo (`alt`) que LinkedIn a veces trae: gratis.
2. OCR con Tesseract (local, gratis). Requiere instalar Tesseract (ver
   docs/INSTALACION_WINDOWS.md) y `pip install pytesseract pillow`.
3. Solo si el OCR no encontró ningún correo: Claude Haiku con visión (centavos por
   imagen). Requiere ANTHROPIC_API_KEY. Tiene un tope por ejecución.

Las imágenes se guardan en datos/imagenes/ (ignorada por git: los afiches traen
teléfonos y correos). Si una imagen ya se leyó, no se vuelve a leer (caché por URL).

Configuración en el perfil (sección `imagenes:`, todas opcionales):
    usar: true                    # activa la lectura en `buscar` / `noche`
    idioma_ocr: "spa+eng"
    tesseract_cmd: ""             # Windows: C:\\Program Files\\Tesseract-OCR\\tesseract.exe
    usar_ia_si_ocr_falla: true
    max_por_ejecucion: 40         # imágenes leídas por ejecución (OCR)
    max_ia_por_ejecucion: 15      # imágenes enviadas a Haiku por ejecución
    leer_con_correo: false        # leer también afiches de posts que YA traen correo
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Callable

from .config import Perfil
from .extraccion import RE_CORREO
from .modelos import PostCrudo

ALT_INUTIL = re.compile(r"^(ver imagen|ver la imagen|imagen|image|no hay texto alternativo|"
                        r"no alternative text|ver imagen de celebraci[oó]n)\b", re.IGNORECASE)

INSTRUCCION_IA = (
    "Esta imagen es un afiche de una vacante de empleo publicado en LinkedIn. "
    "Transcribe en texto plano lo importante: empresa, cargo(s), ciudad o modalidad, "
    "requisitos, salario y TODOS los correos electrónicos exactamente como aparecen "
    "(también asunto del correo si lo piden). Si hay varios cargos, ponlos uno por línea. "
    "No agregues comentarios ni inventes datos. Si la imagen no es una vacante, responde "
    "solo: NO_ES_VACANTE"
)


# ----------------------------------------------------------------------------- utilidades
def config(perfil: Perfil | None) -> dict:
    base = {"usar": False, "idioma_ocr": "spa+eng", "tesseract_cmd": "", "usar_ia_si_ocr_falla": True,
            "max_por_ejecucion": 40, "max_ia_por_ejecucion": 15, "leer_con_correo": False}
    if perfil is not None:
        base.update(perfil.datos.get("imagenes") or {})
    return base


def necesita_lectura(post: PostCrudo, cfg: dict) -> bool:
    """¿Vale la pena leer las imágenes de este post?"""
    if not post.imagenes or post.texto_imagen:
        return False
    return post.sin_correo or bool(cfg.get("leer_con_correo"))


def clave_imagen(url: str) -> str:
    """Nombre de archivo estable: la URL sin la firma (?e=...&t=...) que cambia con el tiempo."""
    return hashlib.sha1(url.split("?")[0].encode("utf-8")).hexdigest()[:16]


def normalizar_texto_ocr(texto: str) -> str:
    """Arregla los errores típicos del OCR en correos y espacios.

    "seleccion @ empresa-ejemplo .com" -> "seleccion@empresa-ejemplo.com"; "(at)"/"[at]" -> "@".
    """
    t = texto.replace("\r", "\n")
    t = re.sub(r"\s*[\(\[]\s*(?:at|arroba)\s*[\)\]]\s*", "@", t, flags=re.IGNORECASE)
    t = re.sub(r"(?<=[\w.-])\s+@\s*(?=[\w-])|(?<=[\w.-])\s*@\s+(?=[\w-])", "@", t)
    # Espacios antes del dominio final: "empresa .com" / "empresa. com.co"
    t = re.sub(r"(@[\w-]+(?:\.[\w-]+)*)\s*\.\s*(com|co|org|net|edu|gov)\b", r"\1.\2", t, flags=re.IGNORECASE)
    t = re.sub(r"(@[\w-]+\.(?:com|edu|gov|org|net))\s*\.\s*(co)\b", r"\1.\2", t, flags=re.IGNORECASE)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


def texto_alt(post: PostCrudo) -> str:
    """Texto alternativo útil de las imágenes (LinkedIn a veces lo genera)."""
    partes = []
    for im in post.imagenes:
        alt = (im.get("alt") or "").strip()
        if len(alt) > 25 and not ALT_INUTIL.search(alt):
            partes.append(alt)
    return " ".join(partes)


# ------------------------------------------------------------------------- piezas de I/O
def descargar(url: str, carpeta: Path, timeout: int = 20) -> Path:
    """Descarga la imagen (o la toma de la caché) y devuelve la ruta local."""
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"{clave_imagen(url)}.jpg"
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    import requests

    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    destino.write_bytes(r.content)
    return destino


def ocr_tesseract(ruta: Path, idioma: str = "spa+eng", tesseract_cmd: str = "") -> str:
    """OCR local. Agranda y pasa a gris las imágenes pequeñas: mejora mucho los afiches."""
    try:
        import pytesseract
        from PIL import Image, ImageOps
    except ImportError as e:
        raise RuntimeError("Falta `pip install pytesseract pillow` (y Tesseract instalado)") from e
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    with Image.open(ruta) as im:
        im = ImageOps.exif_transpose(im).convert("L")
        if im.width < 1200:
            f = 1200 / max(im.width, 1)
            im = im.resize((int(im.width * f), int(im.height * f)))
        im = ImageOps.autocontrast(im)
        return pytesseract.image_to_string(im, lang=idioma)


def leer_con_ia(ruta: Path, modelo: str = "claude-haiku-5-5") -> str:
    """Transcribe el afiche con Claude Haiku (visión). Requiere ANTHROPIC_API_KEY."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("sin ANTHROPIC_API_KEY")
    import anthropic

    datos = base64.standard_b64encode(ruta.read_bytes()).decode("ascii")
    tipo = "image/png" if ruta.read_bytes()[:4] == b"\x89PNG" else "image/jpeg"
    r = anthropic.Anthropic().messages.create(
        model=modelo, max_tokens=700,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": tipo, "data": datos}},
            {"type": "text", "text": INSTRUCCION_IA},
        ]}],
    )
    return r.content[0].text


# ------------------------------------------------------------------------------- proceso
def leer_posts(
    posts: list[PostCrudo],
    perfil: Perfil | None = None,
    carpeta: Path | None = None,
    *,
    usar_ia: bool | None = None,
    descargar_fn: Callable[[str, Path], Path] | None = None,
    ocr_fn: Callable[[Path], str] | None = None,
    ia_fn: Callable[[Path], str] | None = None,
) -> dict:
    """Lee las imágenes de los posts que lo necesitan. Modifica los posts en el sitio.

    Devuelve estadísticas: {"candidatos", "leidos", "con_correo", "ocr", "ia", "errores"}.
    Las funciones *_fn permiten probar sin red ni Tesseract (ver tests).
    """
    cfg = config(perfil)
    carpeta = carpeta or ((perfil.carpeta_datos if perfil else Path("datos")) / "imagenes")
    usar_ia = cfg["usar_ia_si_ocr_falla"] if usar_ia is None else usar_ia
    modelo = (perfil.ia.get("modelo") if perfil else None) or "claude-haiku-5-5"
    descargar_fn = descargar_fn or descargar
    ocr_fn = ocr_fn or (lambda r: ocr_tesseract(r, cfg["idioma_ocr"], cfg["tesseract_cmd"]))
    ia_fn = ia_fn or (lambda r: leer_con_ia(r, modelo))
    cache_ruta = carpeta / "lecturas.json"
    cache: dict[str, dict] = {}
    if cache_ruta.exists():
        try:
            cache = json.loads(cache_ruta.read_text(encoding="utf-8"))
        except ValueError:
            cache = {}

    est = {"candidatos": 0, "leidos": 0, "con_correo": 0, "ocr": 0, "ia": 0, "errores": 0}
    tope_ocr, tope_ia = int(cfg["max_por_ejecucion"]), int(cfg["max_ia_por_ejecucion"])
    ocr_sin_tesseract = False
    for post in posts:
        if not necesita_lectura(post, cfg):
            continue
        est["candidatos"] += 1
        textos, metodos = [], []
        alt = texto_alt(post)
        if alt:
            textos.append(alt)
            metodos.append("alt")
        for im in post.imagenes:
            url = im.get("src") or ""
            if not url:
                continue
            k = clave_imagen(url)
            if k in cache:  # ya se leyó en otra ejecución
                textos.append(cache[k]["texto"])
                metodos.append(cache[k]["metodo"] + "(cache)")
                continue
            if est["ocr"] >= tope_ocr:
                break
            try:
                ruta = Path(im["archivo"]) if im.get("archivo") else descargar_fn(url, carpeta)
            except Exception as e:  # imagen vencida o sin red: se sigue con las demás
                est["errores"] += 1
                metodos.append(f"error descarga: {type(e).__name__}")
                continue
            texto, metodo = "", ""
            if not ocr_sin_tesseract:
                try:
                    texto, metodo = normalizar_texto_ocr(ocr_fn(ruta)), "ocr"
                    est["ocr"] += 1
                except Exception as e:
                    # Sin Tesseract no tiene sentido reintentar en cada imagen.
                    ocr_sin_tesseract = isinstance(e, RuntimeError) or "tesseract" in str(e).lower()
                    metodos.append(f"error ocr: {type(e).__name__}")
            if usar_ia and not RE_CORREO.search(texto) and est["ia"] < tope_ia:
                try:
                    t_ia = normalizar_texto_ocr(ia_fn(ruta))
                    est["ia"] += 1
                    if "NO_ES_VACANTE" in t_ia:
                        texto, metodo = texto or "", metodo or "ia: no es vacante"
                    else:
                        texto, metodo = t_ia, "ia"
                except Exception as e:
                    est["errores"] += 1
                    metodos.append(f"error ia: {type(e).__name__}")
            if texto:
                cache[k] = {"texto": texto[:3000], "metodo": metodo}
                textos.append(texto)
                metodos.append(metodo)
        if textos:
            post.texto_imagen = "\n".join(textos)[:4000]
            est["leidos"] += 1
            if RE_CORREO.search(post.texto_imagen):
                est["con_correo"] += 1
        post.lectura_imagen = ", ".join(metodos)

    if cache:
        carpeta.mkdir(parents=True, exist_ok=True)
        cache_ruta.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return est
