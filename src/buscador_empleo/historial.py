"""Histórico de postulaciones en Markdown (legible para personas y para la IA).

El mismo archivo sirve en los dos modos:
- local: `datos/historial.md` (ignorado por git, tiene correos);
- chat: el asistente lo copia desde/hacia el proyecto de Claude.

El lector acepta cualquier tabla Markdown cuyo encabezado tenga una columna
"Correo"; así se pueden editar a mano las tablas sin romper nada.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

COLUMNAS = ["Fecha", "Empresa", "Cargo", "Ciudad / modalidad", "Correo", "Línea",
            "Fuente", "Estado", "Notas"]

ESTADOS = ["Borrador listo", "Programado", "Enviado", "En proceso", "Rechazado",
           "Sin respuesta", "Oferta", "Descartada"]


@dataclass
class Registro:
    fecha: str
    empresa: str
    cargo: str
    ciudad_modalidad: str
    correo: str
    linea: str
    fuente: str
    estado: str
    notas: str = ""

    def fila(self) -> list[str]:
        return [self.fecha, self.empresa, self.cargo, self.ciudad_modalidad, self.correo,
                self.linea, self.fuente, self.estado, self.notas]


@dataclass
class Historial:
    registros: list[Registro] = field(default_factory=list)
    titulo: str = "Histórico de postulaciones"
    aprendizajes: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------ lectura
    @classmethod
    def leer(cls, ruta: Path) -> "Historial":
        h = cls()
        if not ruta.exists():
            return h
        encabezado: list[str] | None = None
        en_aprendizajes = False
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            s = linea.strip()
            if s.startswith("# "):
                h.titulo = s[2:].strip()
            if s.lower().startswith("## aprendizajes"):
                en_aprendizajes = True
                continue
            if s.startswith("## "):
                en_aprendizajes = False
            if en_aprendizajes and s.startswith("- "):
                h.aprendizajes.append(s[2:])
                continue
            if not s.startswith("|"):
                encabezado = None
                continue
            celdas = [c.strip() for c in s.strip("|").split("|")]
            if encabezado is None:
                encabezado = [c.lower() for c in celdas]
                continue
            if set(s.replace("|", "").strip()) <= {"-", ":", " "}:
                continue
            if "correo" not in encabezado:
                continue
            fila = dict(zip(encabezado, celdas))

            def col(*nombres: str) -> str:
                for n in nombres:
                    for k, v in fila.items():
                        if k.startswith(n):
                            return v
                return ""

            h.registros.append(Registro(
                fecha=col("fecha"), empresa=col("empresa"), cargo=col("cargo"),
                ciudad_modalidad=col("ciudad"), correo=col("correo").lower(),
                linea=col("línea", "linea", "cv"), fuente=col("fuente"),
                estado=col("estado"), notas=col("notas", "respuesta"),
            ))
        return h

    # ---------------------------------------------------------------- escritura
    def escribir(self, ruta: Path, nombres_lineas: dict[str, str] | None = None) -> None:
        nombres_lineas = nombres_lineas or {}
        partes = [f"# {self.titulo}", "",
                  "Estados: " + " → ".join(ESTADOS[:3]) + " → En proceso / Rechazado / Sin respuesta / Oferta",
                  ""]
        grupos: dict[str, list[Registro]] = {}
        for r in self.registros:
            grupos.setdefault(r.linea or "sin línea", []).append(r)
        for linea, regs in grupos.items():
            partes += [f"## {nombres_lineas.get(linea, linea)}", "",
                       "| " + " | ".join(COLUMNAS) + " |",
                       "|" + "---|" * len(COLUMNAS)]
            for r in regs:
                celdas = [str(c).replace("|", "/").replace("\n", " ") for c in r.fila()]
                partes.append("| " + " | ".join(celdas) + " |")
            partes.append("")
        partes += ["## Aprendizajes / ajustes", ""]
        partes += [f"- {a}" for a in self.aprendizajes] or ["- (Anotar motivos de rechazo y qué cambiar.)"]
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text("\n".join(partes) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------- consultas
    def correos(self) -> set[str]:
        return {r.correo.lower() for r in self.registros if r.correo}

    def buscar(self, correo: str) -> Registro | None:
        correo = correo.lower()
        return next((r for r in self.registros if r.correo == correo), None)

    def agregar(self, r: Registro) -> bool:
        if self.buscar(r.correo):
            return False
        self.registros.append(r)
        return True

    def resumen(self) -> dict[str, int]:
        cuenta: dict[str, int] = {}
        for r in self.registros:
            cuenta[r.estado or "?"] = cuenta.get(r.estado or "?", 0) + 1
        return cuenta


def hoy() -> str:
    return dt.date.today().isoformat()
