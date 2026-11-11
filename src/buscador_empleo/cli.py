"""Línea de comandos: `python -m buscador_empleo <comando> -p config/perfil.yaml`.

Comandos pensados para el asistente en el chat (sin red, sin credenciales):
  consultas   URLs de búsqueda de LinkedIn por línea.
  js          Script extractor listo para inyectar en el navegador.
  importar    JSON crudo del extractor -> vacantes filtradas + borradores redactados.
  registrar   Agrega al historial las vacantes aceptadas (estado "Borrador listo").
  resumen     Conteo por estado del historial.

Comandos para el modo local (Windows, con credenciales):
  buscar      Google/Serper (+ LinkedIn opcional) -> importar.
  borradores  Crea borradores en Gmail con el CV adjunto (nunca envía).
  adjuntar    Pone el CV correcto en borradores que no tienen adjunto.
  respuestas  Marca enviados y detecta rechazos / entrevistas.
  noche       buscar + borradores + respuestas, y deja un reporte.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import clasificador, filtros
from .config import Perfil, cargar_perfil
from .extraccion import post_a_vacantes
from .historial import Historial, Registro, hoy
from .modelos import PostCrudo, Vacante
from .redaccion import redactar


# --------------------------------------------------------------------------- utilidades
def _ruta_historial(perfil: Perfil, arg: str | None) -> Path:
    return Path(arg) if arg else perfil.carpeta_datos / "historial.md"


def _leer_crudos(archivos: list[str]) -> list[PostCrudo]:
    posts = []
    for a in archivos:
        contenido = Path(a).read_text(encoding="utf-8").strip()
        datos = json.loads(contenido)
        if isinstance(datos, str):  # el navegador a veces devuelve el JSON como string
            datos = json.loads(datos)
        posts += [PostCrudo.desde_dict(d) for d in datos]
    return posts


def _procesar(posts: list[PostCrudo], perfil: Perfil, hist: Historial, usar_ia: bool) -> list[Vacante]:
    vacantes: list[Vacante] = []
    for p in posts:
        vacantes += post_a_vacantes(p, perfil.correos_ignorar)
    vacantes = filtros.aplicar(vacantes, perfil, hist.correos())
    if usar_ia:
        vacantes = clasificador.revisar(vacantes, perfil)
    return sorted(vacantes, key=lambda x: (not x.aceptada, x.linea, -x.puntaje))


def _guardar_resultado(vacantes: list[Vacante], perfil: Perfil) -> tuple[Path, Path]:
    carpeta = perfil.carpeta_datos
    carpeta.mkdir(parents=True, exist_ok=True)
    sello = hoy()
    rv = carpeta / f"vacantes_{sello}.json"
    rb = carpeta / f"borradores_{sello}.json"
    rv.write_text(json.dumps([v.a_dict(incluir_texto=True) for v in vacantes], ensure_ascii=False, indent=1),
                  encoding="utf-8")
    borradores = []
    for v in vacantes:
        if v.aceptada:
            b = redactar(v, perfil)
            borradores.append({"para": b.para, "asunto": b.asunto, "cuerpo": b.cuerpo,
                               "cv": Path(b.cv).name, "linea": b.linea})
    rb.write_text(json.dumps(borradores, ensure_ascii=False, indent=1), encoding="utf-8")
    return rv, rb


def _imprimir_tabla(vacantes: list[Vacante]) -> None:
    acept = [v for v in vacantes if v.aceptada]
    desc = [v for v in vacantes if not v.aceptada]
    print(f"\nACEPTADAS ({len(acept)})")
    for v in acept:
        print(f"  [{v.linea}] {v.cargo or '?'} | {v.empresa or '?'} | {v.ciudad or '?'} "
              f"{v.modalidad} | {v.correo}" + (f" | asunto: {v.asunto_exigido}" if v.asunto_exigido else ""))
    motivos: dict[str, int] = {}
    for v in desc:
        m = v.motivo_descarte.split("(")[0].strip()
        motivos[m] = motivos.get(m, 0) + 1
    print(f"DESCARTADAS ({len(desc)}): " + ", ".join(f"{k}: {n}" for k, n in motivos.items()))


def _registrar(vacantes: list[Vacante], perfil: Perfil, hist: Historial, estado: str) -> int:
    n = 0
    for v in vacantes:
        if not v.aceptada:
            continue
        ciudad = " ".join(x for x in [v.ciudad, v.modalidad, v.salario] if x)
        r = Registro(fecha=hoy(), empresa=v.empresa, cargo=v.cargo, ciudad_modalidad=ciudad,
                     correo=v.correo, linea=v.linea, fuente=v.fuente or "?", estado=estado,
                     notas=v.notas)
        n += hist.agregar(r)
    return n


# ----------------------------------------------------------------------------- comandos
def cmd_consultas(a, perfil):
    from .fuentes.navegador import consultas
    print(json.dumps(consultas(perfil), ensure_ascii=False, indent=1))


def cmd_js(a, perfil):
    from .fuentes.navegador import script_extractor
    hist = Historial.leer(_ruta_historial(perfil, a.historial))
    js = script_extractor(perfil, hist.correos())
    if a.salida:
        Path(a.salida).write_text(js, encoding="utf-8")
        print(f"Script guardado en {a.salida} ({len(js)} caracteres)")
    else:
        print(js)


def cmd_importar(a, perfil):
    hist = Historial.leer(_ruta_historial(perfil, a.historial))
    vacantes = _procesar(_leer_crudos(a.archivos), perfil, hist, a.ia)
    rv, rb = _guardar_resultado(vacantes, perfil)
    _imprimir_tabla(vacantes)
    print(f"\nVacantes: {rv}\nBorradores redactados: {rb}")


def cmd_registrar(a, perfil):
    ruta = _ruta_historial(perfil, a.historial)
    hist = Historial.leer(ruta)
    vacantes = [Vacante.desde_dict(d) for d in json.loads(Path(a.archivo).read_text(encoding="utf-8"))]
    if a.solo:
        solo = {c.lower() for c in a.solo}
        vacantes = [v for v in vacantes if v.correo.lower() in solo]
    n = _registrar(vacantes, perfil, hist, a.estado)
    hist.escribir(ruta, {k: l.nombre for k, l in perfil.lineas.items()})
    print(f"{n} registros nuevos en {ruta}")


def cmd_resumen(a, perfil):
    hist = Historial.leer(_ruta_historial(perfil, a.historial))
    print(json.dumps(hist.resumen(), ensure_ascii=False, indent=1))


def _buscar(perfil, hist):
    from .fuentes import google, linkedin
    posts = google.buscar(perfil) if perfil.busqueda.get("usar_google", True) else []
    posts += linkedin.buscar(perfil, hist.correos())
    carpeta = perfil.carpeta_datos / "crudo"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"crudo_{hoy()}.json").write_text(
        json.dumps([p.__dict__ for p in posts], ensure_ascii=False, indent=1), encoding="utf-8")
    return posts


def cmd_buscar(a, perfil):
    hist = Historial.leer(_ruta_historial(perfil, a.historial))
    vacantes = _procesar(_buscar(perfil, hist), perfil, hist, perfil.ia.get("usar", False))
    _guardar_resultado(vacantes, perfil)
    _imprimir_tabla(vacantes)


def _crear_borradores(perfil, hist, vacantes, simular):
    from . import gmail_api
    svc = None if simular else gmail_api.servicio(perfil)
    firma = "" if simular else gmail_api.firma_html(svc, perfil.candidato.get("correo_envio", ""))
    creados = []
    for v in vacantes:
        if not v.aceptada or v.correo in hist.correos():
            continue
        b = redactar(v, perfil)
        if not simular:
            gmail_api.crear_borrador(svc, b, firma)
        creados.append(v)
        print(f"  borrador -> {b.para} | {b.asunto} | {Path(b.cv).name}")
    _registrar(creados, perfil, hist, "Borrador listo")
    return creados


def cmd_borradores(a, perfil):
    ruta = _ruta_historial(perfil, a.historial)
    hist = Historial.leer(ruta)
    archivo = Path(a.archivo) if a.archivo else perfil.carpeta_datos / f"vacantes_{hoy()}.json"
    vacantes = [Vacante.desde_dict(d) for d in json.loads(archivo.read_text(encoding="utf-8"))]
    creados = _crear_borradores(perfil, hist, vacantes, a.simular)
    if not a.simular:
        hist.escribir(ruta, {k: l.nombre for k, l in perfil.lineas.items()})
    print(f"{len(creados)} borradores {'(simulación)' if a.simular else 'creados'}")


def cmd_adjuntar(a, perfil):
    from . import gmail_api
    for h in gmail_api.adjuntar_pendientes(gmail_api.servicio(perfil), perfil, a.simular):
        print(f"  {h['para']} | {h['asunto']} -> {h['resultado']}")


def cmd_respuestas(a, perfil):
    from . import gmail_api
    ruta = _ruta_historial(perfil, a.historial)
    hist = Historial.leer(ruta)
    cambios = gmail_api.revisar_respuestas(gmail_api.servicio(perfil), hist)
    hist.escribir(ruta, {k: l.nombre for k, l in perfil.lineas.items()})
    for c in cambios:
        print(f"  {c['correo']} -> {c['estado']}")
    print(f"{len(cambios)} cambios de estado")


def cmd_noche(a, perfil):
    from . import gmail_api
    ruta = _ruta_historial(perfil, a.historial)
    hist = Historial.leer(ruta)
    print("== Respuestas ==")
    svc = gmail_api.servicio(perfil)
    cambios = gmail_api.revisar_respuestas(svc, hist)
    print("== Búsqueda ==")
    vacantes = _procesar(_buscar(perfil, hist), perfil, hist, perfil.ia.get("usar", False))
    _guardar_resultado(vacantes, perfil)
    _imprimir_tabla(vacantes)
    print("== Borradores ==")
    creados = _crear_borradores(perfil, hist, vacantes, simular=False)
    hist.escribir(ruta, {k: l.nombre for k, l in perfil.lineas.items()})
    reporte = perfil.carpeta_datos / f"reporte_{hoy()}.md"
    reporte.write_text(
        f"# Reporte {hoy()}\n\n- Borradores nuevos: {len(creados)}\n- Cambios de estado: {len(cambios)}\n"
        f"- Historial: {json.dumps(hist.resumen(), ensure_ascii=False)}\n", encoding="utf-8")
    print(f"Reporte: {reporte}")


# --------------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="buscador_empleo", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-p", "--perfil", default="config/perfil.yaml")
    ap.add_argument("--historial", help="Ruta al historial .md (por defecto datos/historial.md)")
    sub = ap.add_subparsers(dest="comando", required=True)

    sub.add_parser("consultas").set_defaults(f=cmd_consultas)
    s = sub.add_parser("js"); s.add_argument("-o", "--salida"); s.set_defaults(f=cmd_js)
    s = sub.add_parser("importar"); s.add_argument("archivos", nargs="+")
    s.add_argument("--ia", action="store_true", help="Revisar aceptadas con Claude Haiku"); s.set_defaults(f=cmd_importar)
    s = sub.add_parser("registrar"); s.add_argument("archivo")
    s.add_argument("--estado", default="Borrador listo"); s.add_argument("--solo", nargs="*")
    s.set_defaults(f=cmd_registrar)
    sub.add_parser("resumen").set_defaults(f=cmd_resumen)
    sub.add_parser("buscar").set_defaults(f=cmd_buscar)
    s = sub.add_parser("borradores"); s.add_argument("archivo", nargs="?")
    s.add_argument("--simular", action="store_true"); s.set_defaults(f=cmd_borradores)
    s = sub.add_parser("adjuntar"); s.add_argument("--simular", action="store_true"); s.set_defaults(f=cmd_adjuntar)
    sub.add_parser("respuestas").set_defaults(f=cmd_respuestas)
    sub.add_parser("noche").set_defaults(f=cmd_noche)

    a = ap.parse_args(argv)
    perfil = cargar_perfil(a.perfil)
    a.f(a, perfil)
    return 0


if __name__ == "__main__":
    sys.exit(main())
