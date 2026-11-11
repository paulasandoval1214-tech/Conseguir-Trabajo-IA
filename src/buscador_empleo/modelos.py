"""Estructuras de datos compartidas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PostCrudo:
    """Un post o resultado tal como sale de una fuente (navegador, Google, LinkedIn)."""

    texto: str
    correos: list[str] = field(default_factory=list)
    autor: str = ""
    hace: str = ""
    url: str = ""
    fuente: str = ""

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> "PostCrudo":
        def limpio(x: Any) -> str:
            # El navegador puede cortar un emoji a la mitad (surrogate suelto).
            return str(x or "").encode("utf-8", "replace").decode("utf-8")

        return cls(
            texto=limpio(d.get("texto") or d.get("text")),
            correos=list(d.get("correos") or d.get("emails") or []),
            autor=limpio(d.get("autor")),
            hace=str(d.get("hace") or ""),
            url=str(d.get("url") or ""),
            fuente=str(d.get("fuente") or ""),
        )


@dataclass
class Vacante:
    """Vacante normalizada, lista para filtrar y redactar."""

    correo: str
    cargo: str = ""
    empresa: str = ""
    ciudad: str = ""
    modalidad: str = ""
    salario: str = ""
    asunto_exigido: str = ""
    anios_experiencia: int | None = None
    ingles_exigido: str = ""  # "", "basico", "intermedio", "avanzado"
    pais_detectado: str = ""
    linea: str = ""  # clave de la línea del perfil (p. ej. "datos", "gestion_humana")
    puntaje: float = 0.0
    motivo_descarte: str = ""
    notas: str = ""
    autor: str = ""
    hace: str = ""
    url: str = ""
    fuente: str = ""
    texto: str = ""

    @property
    def aceptada(self) -> bool:
        return not self.motivo_descarte

    def a_dict(self, incluir_texto: bool = False) -> dict[str, Any]:
        d = asdict(self)
        if not incluir_texto:
            d.pop("texto", None)
        return d

    @classmethod
    def desde_dict(cls, d: dict[str, Any]) -> "Vacante":
        campos = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**campos)
