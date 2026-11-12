"""Reglas para decidir si una vacante encaja, a qué línea va y si ya se envió."""

from __future__ import annotations

import datetime as dt
import re

from .config import Perfil
from .extraccion import normalizar
from .modelos import Vacante

NIVELES_INGLES = {"": 0, "basico": 1, "intermedio": 2, "avanzado": 3}

RE_CERRADA = re.compile(
    r"vacante (cerrada|cubierta)|ya no recibe|proceso (cerrado|finalizado)|no recibe mas aplicaciones"
)
RE_BUSCA_EMPLEO = re.compile(
    r"(estoy|me encuentro) en (la )?busqueda de (nuevas )?oportunidades|#opentowork|busco empleo|"
    r"disponibilidad inmediata para"
)


MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
RE_FECHA_LIMITE = re.compile(
    r"(?:hasta el|fecha l[ií]mite|plazo|antes del?)\s*[:\-]?\s*(?:[a-z]+\s+)?(\d{1,2})\s+de\s+([a-z]+)"
)


def fecha_limite_vencida(texto_norm: str, hoy: dt.date | None = None) -> bool:
    """True si el post dice "hasta el 15 de octubre" y esa fecha ya pasó."""
    hoy = hoy or dt.date.today()
    for dia, mes in RE_FECHA_LIMITE.findall(texto_norm):
        if mes not in MESES:
            continue
        try:
            fecha = dt.date(hoy.year, MESES[mes], int(dia))
        except ValueError:
            continue
        # Publicaciones de hace pocas semanas: un mes muy posterior es del año anterior.
        if fecha > hoy and (fecha - hoy).days > 180:
            fecha = fecha.replace(year=hoy.year - 1)
        if fecha < hoy:
            return True
    return False


def _contar(palabras: list[str], texto_norm: str) -> int:
    total = 0
    for p in palabras:
        p = normalizar(p)
        if not p:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(p)}(?![a-z0-9])", texto_norm):
            total += 1
    return total


def clasificar_linea(v: Vacante, perfil: Perfil) -> tuple[str, float]:
    """Devuelve (clave_linea, puntaje). Puntaje 0 = no encaja en ninguna."""
    cargo = normalizar(v.cargo)
    texto = normalizar(v.texto)
    mejor, mejor_p = "", 0.0
    minimo_texto = perfil.busqueda.get("minimo_coincidencias_texto", 3)
    for clave, linea in perfil.lineas.items():
        en_cargo = _contar(linea.palabras_clave, cargo)
        en_texto = _contar(linea.palabras_clave, texto)
        if not en_cargo and en_texto < minimo_texto:
            continue  # el cargo no es de esta línea y el texto apenas la menciona
        p = 3 * en_cargo + en_texto
        p -= 4 * _contar(linea.palabras_excluir, cargo)
        p -= 1 * _contar(linea.palabras_excluir, texto)
        if p > mejor_p:
            mejor, mejor_p = clave, float(p)
    return mejor, mejor_p


def motivo_descarte(v: Vacante, perfil: Perfil, ya_postulados: set[str]) -> str:
    """Primera regla que falla, o "" si la vacante pasa."""
    texto = normalizar(v.texto)
    cand = perfil.candidato
    ubic = perfil.ubicacion

    if v.correo.lower() in ya_postulados:
        return "ya postulada (correo en historial)"
    if RE_BUSCA_EMPLEO.search(texto) and not re.search(r"buscamos|estamos buscando|vacante", texto):
        return "es una persona buscando empleo, no una vacante"
    if RE_CERRADA.search(texto):
        return "vacante cerrada"
    if fecha_limite_vencida(texto):
        return "fecha límite vencida"

    pais = normalizar(ubic.get("pais", ""))
    if pais and v.pais_detectado and v.pais_detectado != pais:
        return f"fuera del país ({v.pais_detectado})"

    aceptadas = [normalizar(c) for c in ubic.get("ciudades_aceptadas", [])]
    if aceptadas and v.ciudad:
        if normalizar(v.ciudad) not in aceptadas and v.modalidad != "Remoto":
            return f"ciudad no aceptada ({v.ciudad})"
    if aceptadas and not v.ciudad and not ubic.get("aceptar_sin_ciudad", True):
        return "sin ciudad"

    nivel = NIVELES_INGLES.get(normalizar(cand.get("nivel_ingles", "")), 0)
    if NIVELES_INGLES.get(v.ingles_exigido, 0) > max(nivel, 1):
        return f"pide inglés {v.ingles_exigido}"

    anios = cand.get("anios_experiencia")
    tolerancia = perfil.busqueda.get("tolerancia_anios", 1)
    if anios is not None and v.anios_experiencia is not None:
        if v.anios_experiencia > anios + tolerancia:
            return f"pide {v.anios_experiencia} años de experiencia"

    if not v.linea:
        return "no coincide con ninguna línea del perfil"
    return ""


def aplicar(vacantes: list[Vacante], perfil: Perfil, ya_postulados: set[str]) -> list[Vacante]:
    """Clasifica, deduplica y marca descartes. Devuelve aceptadas primero."""
    vistos: dict[str, Vacante] = {}
    for v in vacantes:
        v.linea, v.puntaje = clasificar_linea(v, perfil)
        v.motivo_descarte = motivo_descarte(v, perfil, ya_postulados)
        clave = v.correo.lower()
        previo = vistos.get(clave)
        # Mismo correo varias veces (reposts): se queda la versión aceptada con más puntaje.
        if previo is None or (v.aceptada, v.puntaje) > (previo.aceptada, previo.puntaje):
            vistos[clave] = v
    return sorted(vistos.values(), key=lambda x: (not x.aceptada, -x.puntaje))
