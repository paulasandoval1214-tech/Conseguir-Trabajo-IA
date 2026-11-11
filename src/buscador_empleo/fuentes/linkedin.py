"""Modo LinkedIn con sesión (Playwright). APAGADO por defecto.

ADVERTENCIA: automatizar LinkedIn con una cuenta personal va contra sus
términos de uso y puede terminar en bloqueo de la cuenta. Si decides usarlo:
- actívalo explícitamente en el perfil (`busqueda.linkedin_con_sesion: true`),
- deja pocas consultas por noche (máx. 8) y pausas largas,
- nunca lo uses para enviar mensajes ni para recolectar perfiles de personas.

La primera vez abre un navegador visible para que inicies sesión a mano; la
sesión queda en `secretos/perfil_navegador/` (ignorado por git).
"""

from __future__ import annotations

import json
import random
import time

from ..config import Perfil
from ..modelos import PostCrudo
from .navegador import consultas, script_extractor


def buscar(perfil: Perfil, conocidos: set[str]) -> list[PostCrudo]:
    if not perfil.busqueda.get("linkedin_con_sesion", False):
        return []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover
        raise SystemExit("Instala Playwright: pip install playwright && playwright install chromium") from e

    carpeta = perfil.resolver("secretos/perfil_navegador")
    max_c = min(int(perfil.busqueda.get("max_consultas_linkedin", 6)), 8)
    pausa = perfil.busqueda.get("pausa_segundos", [25, 60])
    js = script_extractor(perfil, conocidos)
    posts: list[PostCrudo] = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(carpeta), headless=False)
        page = ctx.new_page()
        page.goto("https://www.linkedin.com/feed/")
        if "login" in page.url or "uas/" in page.url:
            input("Inicia sesión en LinkedIn en la ventana abierta y presiona Enter aquí... ")
        for item in consultas(perfil)[:max_c]:
            page.goto(item["url"])
            crudo = page.evaluate(js)
            for d in json.loads(crudo or "[]"):
                d["fuente"] = "linkedin"
                posts.append(PostCrudo.desde_dict(d))
            time.sleep(random.uniform(*pausa))
        ctx.close()
    return posts
