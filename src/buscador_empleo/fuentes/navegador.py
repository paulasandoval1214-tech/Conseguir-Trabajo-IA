"""Utilidades para el modo "asistente con navegador"."""

from __future__ import annotations

import json
from urllib.parse import quote

from ..config import RAIZ, Perfil
from ..extraccion import PAISES, normalizar

RUTA_JS = RAIZ / "extractor" / "linkedin_posts.js"


def url_busqueda_linkedin(consulta: str, periodo: str = "past-month") -> str:
    """URL de búsqueda de *publicaciones* (no de empleos) ordenada por fecha."""
    return (
        "https://www.linkedin.com/search/results/content/?keywords="
        + quote(consulta)
        + f"&datePosted=%22{periodo}%22&sortBy=%22date_posted%22"
    )


def consultas(perfil: Perfil) -> list[dict]:
    periodo = perfil.busqueda.get("periodo_linkedin", "past-month")
    salida = []
    for clave, linea in perfil.lineas.items():
        for c in linea.consultas:
            salida.append({"linea": clave, "consulta": c, "url": url_busqueda_linkedin(c, periodo)})
    return salida


def script_extractor(perfil: Perfil, conocidos: set[str]) -> str:
    """JS listo para pegar/inyectar, con la configuración ya incluida."""
    pais = perfil.ubicacion.get("pais", "")
    excluir = [p for p in PAISES if p != pais] if pais else []
    claves = sorted({normalizar(k) for l in perfil.lineas.values() for k in l.palabras_clave if len(k) > 3})
    cfg = {
        "conocidos": sorted(conocidos),
        "claves": claves,
        "excluirPaises": excluir,
        "scrolls": perfil.busqueda.get("scrolls", 12),
        "maxTexto": perfil.busqueda.get("max_texto", 900),
    }
    return f"window.__CTI_CONFIG = {json.dumps(cfg, ensure_ascii=False)};\n" + RUTA_JS.read_text(encoding="utf-8")
