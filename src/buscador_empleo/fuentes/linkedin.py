"""Modo LinkedIn con sesión (Playwright), para el computador local. APAGADO por defecto.

ADVERTENCIA: automatizar LinkedIn con una cuenta personal va contra sus términos de uso y
puede terminar en bloqueo de la cuenta. Si decides usarlo:
- actívalo explícitamente en el perfil (`busqueda.linkedin_con_sesion: true`),
- deja pocas consultas por noche (máx. 8) y pausas largas,
- nunca lo uses para enviar mensajes, seguir, conectar ni para recolectar perfiles en masa.
  (La lista de "personas para conectar" se arma solo con autores de vacantes ya vistas y
  la acción de conectar la hace la persona, a mano.)

Qué hace en cada ejecución:
1. Abre el navegador con la sesión guardada en `secretos/perfil_navegador/` (la primera vez
   pide iniciar sesión a mano; nunca se guardan contraseñas).
2. Visita lo que elija `navegador.elegir_consultas()`: el feed de inicio (si
   `linkedin_feed: true`) y, hasta completar `max_consultas_linkedin`, hashtags y búsquedas
   por palabras EN ROTACIÓN (cada noche sigue donde quedó la anterior; el estado se guarda
   en datos/rotacion_linkedin.json).
3. En cada página corre extractor/linkedin_posts.js. Si `imagenes.usar: true`, el extractor
   también trae posts SIN correo en el texto pero con afiche, y aquí mismo se descargan sus
   imágenes con la sesión del navegador (datos/imagenes/) para que `imagenes.py` las lea.
4. Si LinkedIn responde "No se han encontrado resultados" dos veces seguidas, se detiene:
   es la señal de que está limitando las búsquedas (aprendido el 15-nov-2026).
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

from ..config import Perfil
from ..modelos import PostCrudo
from .navegador import elegir_consultas, script_extractor

SIN_RESULTADOS = ("No se han encontrado resultados", "No results found")


def _descargar_imagenes(ctx, posts: list[PostCrudo], carpeta: Path) -> int:
    """Descarga los afiches con la sesión del navegador (más fiable que sin cookies)."""
    from ..imagenes import clave_imagen

    carpeta.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in posts:
        for im in p.imagenes:
            url = im.get("src") or ""
            if not url or im.get("archivo"):
                continue
            destino = carpeta / f"{clave_imagen(url)}.jpg"
            try:
                if not destino.exists():
                    r = ctx.request.get(url, timeout=20000)
                    if not r.ok:
                        continue
                    destino.write_bytes(r.body())
                    n += 1
                im["archivo"] = str(destino)
            except Exception:  # una imagen vencida no debe tumbar la búsqueda
                continue
    return n


def buscar(perfil: Perfil, conocidos: set[str]) -> list[PostCrudo]:
    b = perfil.busqueda
    if not b.get("linkedin_con_sesion", False):
        return []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover
        raise SystemExit("Instala Playwright: pip install playwright && playwright install chromium") from e

    carpeta = perfil.resolver("secretos/perfil_navegador")
    max_c = min(int(b.get("max_consultas_linkedin", 6)), 8)
    pausa = b.get("pausa_segundos", [25, 60])
    con_imagenes = bool(perfil.imagenes.get("usar", False))
    js_normal = script_extractor(perfil, conocidos, incluir_imagenes=con_imagenes)
    js_feed = script_extractor(perfil, conocidos, incluir_imagenes=con_imagenes,
                               scrolls=int(b.get("scrolls_feed", 25)))
    posts: list[PostCrudo] = []
    vacias_seguidas = 0
    ruta_estado = perfil.carpeta_datos / "rotacion_linkedin.json"
    estado = json.loads(ruta_estado.read_text(encoding="utf-8")) if ruta_estado.exists() else {}
    de_hoy, estado_nuevo = elegir_consultas(perfil, max_c, estado)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(carpeta), headless=False)
        page = ctx.new_page()
        page.goto("https://www.linkedin.com/feed/")
        if "login" in page.url or "uas/" in page.url:
            input("Inicia sesión en LinkedIn en la ventana abierta y presiona Enter aquí... ")
        for item in de_hoy:
            page.goto(item["url"])
            crudo = page.evaluate(js_feed if item["tipo"] == "feed" else js_normal)
            nuevos = [PostCrudo.desde_dict({**d, "fuente": "linkedin"}) for d in json.loads(crudo or "[]")]
            print(f"  [{item['tipo']}] {item['consulta']}: {len(nuevos)} posts")
            if not nuevos and any(t in (page.inner_text("main") or "") for t in SIN_RESULTADOS):
                vacias_seguidas += 1
                if vacias_seguidas >= 2:
                    print("  LinkedIn está limitando las búsquedas: se detiene por hoy.")
                    break
            else:
                vacias_seguidas = 0
            if con_imagenes:
                _descargar_imagenes(ctx, [x for x in nuevos if x.imagenes], perfil.carpeta_datos / "imagenes")
            posts += nuevos
            time.sleep(random.uniform(*pausa))
        ctx.close()
    ruta_estado.parent.mkdir(parents=True, exist_ok=True)
    ruta_estado.write_text(json.dumps(estado_nuevo), encoding="utf-8")
    return posts
