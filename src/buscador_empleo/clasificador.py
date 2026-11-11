"""Segunda opinión con IA (Claude Haiku) para las vacantes que pasaron las reglas.

Solo se llama para vacantes ya aceptadas por las reglas, así el costo es de
centavos por noche. Clave en .env: ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
import os
import re

from .config import Perfil
from .modelos import Vacante

INSTRUCCIONES = """Eres un asistente que filtra vacantes de empleo para una candidata.
Perfil de la candidata:
{perfil}

Líneas de búsqueda posibles: {lineas}

Lee el post de la vacante y responde SOLO un JSON con estas claves:
{{"encaja": true/false, "linea": "<una de las líneas o vacío>", "cargo": "<cargo exacto>",
  "empresa": "<empresa o vacío>", "ciudad": "<ciudad o Remoto o vacío>",
  "motivo": "<máx 15 palabras>"}}
"encaja" es false si: piden inglés avanzado y ella no lo tiene, piden bastante más experiencia
de la que tiene, es otra profesión (contador, desarrollador, etc.), es fuera del país, o el post
es de una persona buscando empleo y no una vacante."""


def _resumen_perfil(perfil: Perfil) -> str:
    c = perfil.candidato
    return (
        f"Profesión: {c.get('profesion', '')}. Experiencia: {c.get('anios_experiencia', '?')} años. "
        f"Inglés: {c.get('nivel_ingles', '?')}. Ciudad: {c.get('ciudad', '')}. "
        f"Fortalezas: {c.get('resumen', '')}"
    )


def revisar(vacantes: list[Vacante], perfil: Perfil) -> list[Vacante]:
    if not perfil.ia.get("usar", False):
        return vacantes
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[IA] Sin ANTHROPIC_API_KEY: se usan solo las reglas.")
        return vacantes
    try:
        import anthropic
    except ImportError:
        print("[IA] Falta `pip install anthropic`: se usan solo las reglas.")
        return vacantes

    cliente = anthropic.Anthropic()
    modelo = perfil.ia.get("modelo", "claude-haiku-5-5")
    tope = int(perfil.ia.get("max_por_ejecucion", 60))
    sistema = INSTRUCCIONES.format(
        perfil=_resumen_perfil(perfil),
        lineas=", ".join(f"{k} ({l.nombre})" for k, l in perfil.lineas.items()),
    )
    revisadas = 0
    for v in vacantes:
        if not v.aceptada or revisadas >= tope:
            continue
        revisadas += 1
        try:
            r = cliente.messages.create(
                model=modelo, max_tokens=300, system=sistema,
                messages=[{"role": "user", "content": v.texto[:2500]}],
            )
            crudo = r.content[0].text
            d = json.loads(re.search(r"\{.*\}", crudo, re.S).group(0))
        except Exception as e:  # la IA es opcional: si falla, mandan las reglas
            v.notas = (v.notas + f" | IA no disponible: {type(e).__name__}").strip(" |")
            continue
        if not d.get("encaja", True):
            v.motivo_descarte = "IA: " + str(d.get("motivo", "no encaja"))
        if d.get("linea") in perfil.lineas:
            v.linea = d["linea"]
        v.cargo = d.get("cargo") or v.cargo
        v.empresa = d.get("empresa") or v.empresa
        v.ciudad = d.get("ciudad") or v.ciudad
        if d.get("motivo") and v.aceptada:
            v.notas = (v.notas + " | " + str(d["motivo"])).strip(" |")
    return vacantes
