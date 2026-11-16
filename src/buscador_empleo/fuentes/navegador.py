"""Utilidades para buscar en LinkedIn con un navegador (el de Claude en el chat o Playwright).

Arma:
- las URLs a visitar (`consultas`): feed de inicio, hashtags y búsquedas por palabras, y
- el script extractor (`script_extractor`) con la configuración ya incluida.
"""

from __future__ import annotations

import json
from urllib.parse import quote

from ..config import RAIZ, Perfil
from ..extraccion import PAISES, normalizar

RUTA_JS = RAIZ / "extractor" / "linkedin_posts.js"
URL_FEED = "https://www.linkedin.com/feed/"


def url_busqueda_linkedin(consulta: str, periodo: str = "past-month", orden: str = "relevancia") -> str:
    """URL de búsqueda de *publicaciones* (no de empleos).

    `orden="relevancia"` trae más resultados que `"fecha"` (aprendido el 15-nov-2026).
    Un hashtag se busca igual que una palabra: keywords=%23trabajosihay.
    """
    url = (
        "https://www.linkedin.com/search/results/content/?keywords="
        + quote(consulta)
        + f"&datePosted=%22{periodo}%22"
    )
    if orden == "fecha":
        url += "&sortBy=%22date_posted%22"
    return url


def _hashtag(h: str) -> str:
    h = h.strip()
    return h if h.startswith("#") else "#" + h


def consultas(perfil: Perfil, tipos: set[str] | None = None) -> list[dict]:
    """Lista ordenada de lo que se visita: feed, hashtags generales y luego cada línea.

    Cada elemento: {"linea", "tipo" ("feed" | "hashtag" | "palabras"), "consulta", "url"}.
    `tipos` permite pedir solo algunos (p. ej. {"hashtag"}).
    """
    b = perfil.busqueda
    periodo = b.get("periodo_linkedin", "past-week")
    orden = b.get("orden_linkedin", "relevancia")
    salida: list[dict] = []
    if b.get("linkedin_feed", False):
        salida.append({"linea": "general", "tipo": "feed", "consulta": "feed de inicio", "url": URL_FEED})
    for h in b.get("hashtags_generales", []) or []:
        h = _hashtag(h)
        salida.append({"linea": "general", "tipo": "hashtag", "consulta": h,
                       "url": url_busqueda_linkedin(h, periodo, orden)})
    for clave, linea in perfil.lineas.items():
        for h in linea.hashtags:
            h = _hashtag(h)
            salida.append({"linea": clave, "tipo": "hashtag", "consulta": h,
                           "url": url_busqueda_linkedin(h, periodo, orden)})
        for c in linea.consultas:
            salida.append({"linea": clave, "tipo": "palabras", "consulta": c,
                           "url": url_busqueda_linkedin(c, periodo, orden)})
    # Sin repetidos (un hashtag puede estar en dos líneas).
    vistos, unicos = set(), []
    for s in salida:
        if s["url"] not in vistos and (not tipos or s["tipo"] in tipos):
            vistos.add(s["url"])
            unicos.append(s)
    return unicos


def config_extractor(perfil: Perfil, conocidos: set[str], incluir_imagenes: bool = False,
                     scrolls: int | None = None) -> dict:
    pais = perfil.ubicacion.get("pais", "")
    excluir = [p for p in PAISES if p != pais] if pais else []
    claves = sorted({normalizar(k) for l in perfil.lineas.values() for k in l.palabras_clave if len(k) > 3})
    return {
        "conocidos": sorted(conocidos),
        "claves": claves,
        "excluirPaises": excluir,
        "scrolls": scrolls or perfil.busqueda.get("scrolls", 12),
        "maxTexto": perfil.busqueda.get("max_texto", 900),
        "incluirImagenes": bool(incluir_imagenes),
        "maxImagenes": int((perfil.datos.get("imagenes") or {}).get("max_por_post", 3)),
    }


def script_extractor(perfil: Perfil, conocidos: set[str], incluir_imagenes: bool = False,
                     scrolls: int | None = None) -> str:
    """JS listo para pegar/inyectar, con la configuración ya incluida."""
    cfg = config_extractor(perfil, conocidos, incluir_imagenes, scrolls)
    return f"window.__CTI_CONFIG = {json.dumps(cfg, ensure_ascii=False)};\n" + RUTA_JS.read_text(encoding="utf-8")


def elegir_consultas(perfil: Perfil, maximo: int, estado: dict | None = None) -> tuple[list[dict], dict]:
    """Elige qué visitar hoy sin pasarse del máximo (LinkedIn limita las búsquedas).

    - El feed (si está activo) va siempre: no es una búsqueda.
    - El resto rota: cada ejecución sigue donde quedó la anterior (`estado["inicio"]`), así en
      pocos días se cubren todos los hashtags y consultas sin repetir siempre los primeros.
    Devuelve (consultas_de_hoy, estado_nuevo). Con `rotar_consultas: false` toma siempre las primeras.
    """
    todas = consultas(perfil)
    feed = [c for c in todas if c["tipo"] == "feed"]
    resto = [c for c in todas if c["tipo"] != "feed"]
    cupo = max(maximo - len(feed), 0)
    if not resto or not cupo:
        return feed[:maximo], dict(estado or {})
    if not perfil.busqueda.get("rotar_consultas", True):
        return feed + resto[:cupo], dict(estado or {})
    if estado and "inicio" in estado:
        inicio = int(estado["inicio"]) % len(resto)
    else:
        # Sin estado guardado (p. ej. una sesión nueva en el chat): el punto de partida depende
        # de la fecha, así cada día toca un grupo distinto aunque no haya memoria entre sesiones.
        import datetime as dt

        inicio = (dt.date.today().toordinal() * cupo) % len(resto)
    hoy = [resto[(inicio + i) % len(resto)] for i in range(min(cupo, len(resto)))]
    return feed + hoy, {"inicio": (inicio + len(hoy)) % len(resto)}


ENVOLTURA = (
    "(async () => {"
    " const c = JSON.parse(localStorage.cti_cfg);"
    " const extra = JSON.parse(localStorage.cti_extra || '{}');"
    " window.__CTI_CONFIG = Object.assign({}, c, extra);"
    " const r = await eval(localStorage.cti_body);"
    " JSON.parse(r).forEach((x) => c.conocidos.push(...x.correos));"
    " localStorage.cti_cfg = JSON.stringify(c);"
    " return r; })()"
)


def version_extractor() -> str:
    """Huella corta del extractor: si cambia, hay que volver a cargarlo en el navegador."""
    import hashlib

    return hashlib.sha1(RUTA_JS.read_bytes()).hexdigest()[:8]


def script_cargador(perfil: Perfil, conocidos: set[str], incluir_imagenes: bool = False) -> str:
    """JS que deja el extractor GUARDADO en el navegador (localStorage de linkedin.com).

    Se pega una sola vez (y otra vez solo si cambia la versión). Después, en cada página,
    basta con ejecutar exactamente:  await eval(localStorage.cti_run)
    - Devuelve el mismo JSON que el extractor.
    - Agrega a `conocidos` los correos devueltos: la siguiente consulta no los repite.
    - Para el feed, antes: localStorage.cti_extra = '{"scrolls":25}'  (y '{}' para volver).
    Ahorra tokens: el script (~10 KB) no viaja en cada consulta.
    Nota: LinkedIn bloquea `eval` si va junto a otras instrucciones; la llamada debe ir sola.
    """
    cfg = config_extractor(perfil, conocidos, incluir_imagenes)
    cuerpo = RUTA_JS.read_text(encoding="utf-8")
    return (
        f"localStorage.cti_cfg = {json.dumps(json.dumps(cfg, ensure_ascii=False), ensure_ascii=False)};\n"
        f"localStorage.cti_body = {json.dumps(cuerpo, ensure_ascii=False)};\n"
        f"localStorage.cti_run = {json.dumps(ENVOLTURA)};\n"
        f"localStorage.cti_extra = '{{}}';\n"
        f"localStorage.cti_version = {json.dumps(version_extractor())};\n"
        "'extractor guardado: version ' + localStorage.cti_version + ', conocidos: ' + "
        "JSON.parse(localStorage.cti_cfg).conocidos.length;\n"
    )
