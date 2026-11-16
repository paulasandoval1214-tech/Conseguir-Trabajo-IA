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
    autor_url: str = ""                      # perfil o página de quien publicó
    hashtags: list[str] = field(default_factory=list)
    imagenes: list[dict[str, str]] = field(default_factory=list)  # [{"src": url, "alt": texto}]
    sin_correo: bool = False                 # el correo no está en el texto (quizá en el afiche)
    texto_imagen: str = ""                   # lo que se leyó de las imágenes (OCR / IA)
    lectura_imagen: str = ""                 # "ocr", "ia", "alt", "error: ..." (diagnóstico)

    @property
    def texto_completo(self) -> str:
        """Texto del post + lo leído en sus imágenes (si hay)."""
        if not self.texto_imagen:
            return self.texto
        return f"{self.texto}\n[Texto de la imagen] {self.texto_imagen}"

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
            autor_url=str(d.get("autor_url") or d.get("autorUrl") or ""),
            hashtags=[str(h) for h in (d.get("hashtags") or [])],
            imagenes=[i if isinstance(i, dict) else {"src": str(i), "alt": ""} for i in (d.get("imagenes") or [])],
            sin_correo=bool(d.get("sin_correo") or d.get("sinCorreo")),
            texto_imagen=limpio(d.get("texto_imagen")),
            lectura_imagen=str(d.get("lectura_imagen") or ""),
        )

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    autor_url: str = ""
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
