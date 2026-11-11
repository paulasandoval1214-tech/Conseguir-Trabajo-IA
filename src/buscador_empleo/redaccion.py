"""Arma asunto y cuerpo de cada correo a partir de plantillas de texto."""

from __future__ import annotations

from dataclasses import dataclass
from string import Template

from .config import Perfil
from .modelos import Vacante


@dataclass
class Borrador:
    para: str
    asunto: str
    cuerpo: str
    cv: str
    linea: str
    vacante: Vacante


def asunto_para(v: Vacante) -> str:
    """Respeta el asunto exigido por la vacante; si no hay, usa el cargo."""
    if v.asunto_exigido:
        return v.asunto_exigido
    return v.cargo or "Postulación"


def redactar(v: Vacante, perfil: Perfil) -> Borrador:
    linea = perfil.lineas[v.linea]
    plantilla = perfil.resolver(linea.plantilla).read_text(encoding="utf-8")
    cargo = v.cargo or "la vacante publicada"
    cuerpo = Template(plantilla).safe_substitute(
        cargo=cargo,
        empresa=v.empresa or "su empresa",
        ciudad=v.ciudad,
        experiencia=linea.experiencia_correo,
        nombre=perfil.candidato.get("nombre", ""),
    ).strip()
    return Borrador(
        para=v.correo,
        asunto=asunto_para(v),
        cuerpo=cuerpo,
        cv=str(perfil.resolver(linea.cv)),
        linea=v.linea,
        vacante=v,
    )
