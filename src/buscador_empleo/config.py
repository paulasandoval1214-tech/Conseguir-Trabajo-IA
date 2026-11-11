"""Carga del perfil (YAML) y de secretos (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parents[2]


def cargar_env(ruta: Path | None = None) -> None:
    """Lee un .env sencillo (CLAVE=valor) sin pisar variables ya definidas."""
    ruta = ruta or RAIZ / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


@dataclass
class Linea:
    clave: str
    nombre: str
    cv: str
    plantilla: str
    experiencia_correo: str
    palabras_clave: list[str] = field(default_factory=list)
    palabras_excluir: list[str] = field(default_factory=list)
    consultas: list[str] = field(default_factory=list)


@dataclass
class Perfil:
    datos: dict[str, Any]
    lineas: dict[str, Linea]
    ruta: Path

    # --- accesos cómodos -------------------------------------------------
    @property
    def candidato(self) -> dict[str, Any]:
        return self.datos.get("candidato", {})

    @property
    def ubicacion(self) -> dict[str, Any]:
        return self.datos.get("ubicacion", {})

    @property
    def busqueda(self) -> dict[str, Any]:
        return self.datos.get("busqueda", {})

    @property
    def ia(self) -> dict[str, Any]:
        return self.datos.get("ia", {})

    @property
    def gmail(self) -> dict[str, Any]:
        return self.datos.get("gmail", {})

    @property
    def correos_ignorar(self) -> list[str]:
        return list(self.datos.get("correos_ignorar", []))

    @property
    def carpeta_datos(self) -> Path:
        return self.resolver(self.datos.get("carpeta_datos", "datos"))

    def resolver(self, ruta: str | Path) -> Path:
        """Rutas relativas se resuelven desde la raíz del repo."""
        p = Path(ruta)
        return p if p.is_absolute() else RAIZ / p


def cargar_perfil(ruta: str | Path) -> Perfil:
    ruta = Path(ruta)
    if not ruta.is_absolute():
        ruta = (Path.cwd() / ruta) if (Path.cwd() / ruta).exists() else RAIZ / ruta
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    lineas = {}
    for clave, l in (datos.get("lineas") or {}).items():
        lineas[clave] = Linea(
            clave=clave,
            nombre=l.get("nombre", clave),
            cv=l.get("cv", ""),
            plantilla=l.get("plantilla", ""),
            experiencia_correo=l.get("experiencia_correo", ""),
            palabras_clave=list(l.get("palabras_clave", [])),
            palabras_excluir=list(l.get("palabras_excluir", [])),
            consultas=list(l.get("consultas", [])),
        )
    if not lineas:
        raise ValueError(f"El perfil {ruta} no define ninguna línea en 'lineas:'")
    cargar_env()
    return Perfil(datos=datos, lineas=lineas, ruta=ruta)
