"""Búsqueda de posts públicos de LinkedIn vía Google (API de Serper).

No inicia sesión en LinkedIn. Cada consulta cuesta 1 crédito de Serper
(la cuenta gratis trae créditos de prueba). Clave en .env: SERPER_API_KEY.
"""

from __future__ import annotations

import os
import re
import time

import requests

from ..config import Perfil
from ..modelos import PostCrudo

SERPER_URL = "https://google.serper.dev/search"
CABECERAS_WEB = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) conseguir-trabajo-ia/0.1"}


def _consulta_google(texto: str, ciudad: str) -> str:
    return (
        f'site:linkedin.com/posts {texto} {ciudad} '
        '("hoja de vida" OR "envía tu CV" OR "envíanos tu hoja de vida") "@"'
    )


def _texto_post_publico(url: str) -> str:
    """Intenta leer el texto de un post público (sin sesión)."""
    try:
        r = requests.get(url, headers=CABECERAS_WEB, timeout=20)
    except requests.RequestException:
        return ""
    if r.status_code != 200:
        return ""
    h = r.text
    partes = re.findall(r'<meta (?:name|property)="(?:og:)?description" content="([^"]+)"', h)
    cuerpo = re.search(r'"articleBody"\s*:\s*"(.*?)"\s*,\s*"', h, re.S)
    texto = " ".join(partes)
    if cuerpo:
        texto = cuerpo.group(1).encode().decode("unicode_escape", "ignore") + " " + texto
    return re.sub(r"\s+", " ", texto)


def buscar(perfil: Perfil, max_consultas: int | None = None) -> list[PostCrudo]:
    clave = os.environ.get("SERPER_API_KEY")
    if not clave:
        raise SystemExit("Falta SERPER_API_KEY en .env (ver docs/INSTALACION_WINDOWS.md)")
    ciudad = perfil.candidato.get("ciudad", "")
    periodo = perfil.busqueda.get("periodo_google", "qdr:m")  # qdr:w = semana, qdr:m = mes
    max_consultas = max_consultas or perfil.busqueda.get("max_consultas_google", 12)

    posts: list[PostCrudo] = []
    hechas = 0
    for linea in perfil.lineas.values():
        for c in linea.consultas:
            if hechas >= max_consultas:
                return posts
            hechas += 1
            body = {"q": _consulta_google(c, ciudad), "gl": "co", "hl": "es", "num": 20, "tbs": periodo}
            r = requests.post(SERPER_URL, json=body, headers={"X-API-KEY": clave}, timeout=30)
            r.raise_for_status()
            for item in r.json().get("organic", []):
                url = item.get("link", "")
                texto = f"{item.get('title', '')}. {item.get('snippet', '')}"
                if "@" not in texto and url:
                    time.sleep(1.5)  # cortesía con el sitio
                    texto = _texto_post_publico(url) or texto
                posts.append(PostCrudo(texto=texto, url=url, fuente="google", autor=item.get("title", "")[:80]))
    return posts
