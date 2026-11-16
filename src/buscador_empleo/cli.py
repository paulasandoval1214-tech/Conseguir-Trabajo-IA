"""Línea de comandos: `python -m buscador_empleo <comando> -p config/perfil.yaml`.

Comandos que no necesitan credenciales (los usa el asistente en el chat y también el modo local):
  consultas   URLs a visitar en LinkedIn: feed, hashtags y búsquedas por palabras.
  js          Script extractor listo para inyectar en el navegador.
  importar    JSON crudo del extractor -> vacantes filtradas + borradores redactados.
  registrar   Agrega al historial las vacantes aceptadas (estado "Borrador listo").
  resumen     Conteo por estado del historial.
  hashtags    Ranking de hashtags según cuántas vacantes útiles trajeron (afina docs/HASHTAGS.md).
  personas    Ranking de autores que publican vacantes útiles -> lista para seguir/conectar a mano.

Comandos para el modo local (Windows, con credenciales o programas instalados):
  imagenes    Lee los afiches de los posts sin correo (OCR Tesseract y, si falla, Claude Haiku).
  buscar      LinkedIn con sesión (opcional) + Google/Serper -> imágenes -> importar.
  borradores  Crea borradores en Gmail con el CV adjunto (nunca envía).
  adjuntar    Pone el CV correcto en borradores que no tienen adjunto.
  respuestas  Marca enviados y detecta rechazos / entrevistas.
  noche       respuestas + buscar + borradores + hashtags + personas, y deja un reporte.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import datetime as dt
import glob

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


def _archivos(patrones: list[str]) -> list[str]:
    """Expande comodines también en Windows (PowerShell no expande `datos/crudo/*.json`)."""
    salida: list[str] = []
    for p in patrones:
        salida += sorted(glob.glob(p)) if any(c in p for c in "*?[") else [p]
    return salida


def _crudos_con_fecha(perfil: Perfil) -> list[tuple[PostCrudo, str]]:
    """Todos los posts guardados en datos/crudo, con la fecha del archivo (para rankings)."""
    salida: list[tuple[PostCrudo, str]] = []
    vistos: set[str] = set()

    def agregar(p: PostCrudo, fecha: str) -> None:
        k = p.texto[:160]
        if k not in vistos:
            vistos.add(k)
            salida.append((p, fecha))

    for a in sorted((perfil.carpeta_datos / "crudo").glob("*.json")):
        fecha = dt.date.fromtimestamp(a.stat().st_mtime).isoformat()
        try:
            for p in _leer_crudos([str(a)]):
                agregar(p, fecha)
        except ValueError:
            print(f"  (se omite {a.name}: no es JSON válido)")
    # Las vacantes procesadas guardan el texto del post: sirven para días sin crudo guardado.
    for a in sorted(perfil.carpeta_datos.glob("vacantes_*.json")):
        fecha = a.stem.replace("vacantes_", "")
        try:
            datos = json.loads(a.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for d in datos:
            if d.get("texto"):
                agregar(PostCrudo(texto=d["texto"], correos=[d.get("correo", "")], autor=d.get("autor", ""),
                                  autor_url=d.get("autor_url", ""), url=d.get("url", ""),
                                  fuente=d.get("fuente", "")), fecha)
    return salida


def _guardar_crudos(posts: list[PostCrudo], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps([p.a_dict() for p in posts], ensure_ascii=False, indent=1), encoding="utf-8")


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
    from .fuentes.navegador import consultas, elegir_consultas
    if a.hoy:
        # Lo de hoy, en rotación: guarda dónde quedó para que la próxima sesión siga desde ahí.
        ruta = perfil.carpeta_datos / "rotacion_linkedin.json"
        estado = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
        lista, nuevo = elegir_consultas(perfil, a.hoy, estado)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(nuevo), encoding="utf-8")
    else:
        lista = consultas(perfil, set(a.tipo) if a.tipo else None)
    print(json.dumps(lista, ensure_ascii=False, indent=1))


def cmd_js(a, perfil):
    from .fuentes.navegador import script_extractor
    hist = Historial.leer(_ruta_historial(perfil, a.historial))
    js = script_extractor(perfil, hist.correos(), incluir_imagenes=a.imagenes, scrolls=a.scrolls)
    if a.salida:
        Path(a.salida).write_text(js, encoding="utf-8")
        print(f"Script guardado en {a.salida} ({len(js)} caracteres)")
    else:
        print(js)


def _leer_imagenes(posts: list[PostCrudo], perfil: Perfil, usar_ia: bool | None = None) -> dict:
    from . import imagenes
    est = imagenes.leer_posts(posts, perfil, usar_ia=usar_ia)
    if est["candidatos"]:
        print(f"[imágenes] posts con afiche: {est['candidatos']} · leídos: {est['leidos']} · "
              f"con correo: {est['con_correo']} · OCR: {est['ocr']} · IA: {est['ia']} · errores: {est['errores']}")
    return est


def cmd_imagenes(a, perfil):
    """Lee los afiches y guarda lo leído DENTRO de los mismos archivos crudos."""
    total = {"candidatos": 0, "leidos": 0, "con_correo": 0, "ocr": 0, "ia": 0, "errores": 0}
    for archivo in _archivos(a.archivos):
        posts = _leer_crudos([archivo])
        est = _leer_imagenes(posts, perfil, usar_ia=False if a.sin_ia else None)
        if est["leidos"]:
            _guardar_crudos(posts, Path(archivo))
        for k in total:
            total[k] += est[k]
    print(json.dumps(total, ensure_ascii=False))


def cmd_importar(a, perfil):
    hist = Historial.leer(_ruta_historial(perfil, a.historial))
    archivos = _archivos(a.archivos)
    if a.imagenes:
        cmd_imagenes(argparse.Namespace(archivos=archivos, sin_ia=False), perfil)
    vacantes = _procesar(_leer_crudos(archivos), perfil, hist, a.ia)
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
    posts = linkedin.buscar(perfil, hist.correos())
    posts += google.buscar(perfil) if perfil.busqueda.get("usar_google", True) else []
    if perfil.imagenes.get("usar", False):
        _leer_imagenes(posts, perfil)
    _guardar_crudos(posts, perfil.carpeta_datos / "crudo" / f"crudo_{hoy()}.json")
    return posts


def cmd_hashtags(a, perfil):
    from . import hashtags
    posts = [p for p, _ in _crudos_con_fecha(perfil)]
    filas = hashtags.analizar(posts, perfil, minimo_posts=a.minimo)
    tabla = hashtags.tabla_markdown(filas, perfil, a.maximo)
    ruta = perfil.carpeta_datos / "hashtags_ranking.md"
    ruta.write_text(f"# Ranking de hashtags ({hoy()})\n\nPosts analizados: {len(posts)}\n\n{tabla}\n",
                    encoding="utf-8")
    print(tabla)
    print(f"\nGuardado en {ruta}")
    if a.actualizar_doc:
        cambio = hashtags.actualizar_doc(tabla, hoy(), len(posts))
        print("docs/HASHTAGS.md actualizado" if cambio else "docs/HASHTAGS.md sin cambios")


def cmd_personas(a, perfil):
    from . import personas
    hist = Historial.leer(_ruta_historial(perfil, a.historial))
    filas = personas.agrupar(_crudos_con_fecha(perfil), perfil, personas.fuentes_del_historial(hist))
    ruta_csv, ruta_md = personas.escribir(filas, perfil.carpeta_datos)
    pendientes = [f for f in filas if f["estado"] == "Pendiente"]
    print(f"{len(filas)} autores en el ranking ({len(pendientes)} pendientes). Los primeros:")
    for f in pendientes[: a.top]:
        print(f"  {f['puntaje']:>3}  {f['nombre'][:40]:40} {f['tipo']:10} {f['lineas'][:25]:25} {f['url']}")
    print(f"\nCSV: {ruta_csv}\nMD:  {ruta_md}")


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
    print("== Rankings (hashtags y personas) ==")
    try:
        cmd_hashtags(argparse.Namespace(minimo=2, maximo=40, actualizar_doc=False), perfil)
        cmd_personas(argparse.Namespace(top=10, historial=a.historial), perfil)
    except Exception as e:  # los rankings son ayuda, no deben tumbar la noche
        print(f"  (rankings no disponibles: {type(e).__name__}: {e})")
    reporte = perfil.carpeta_datos / f"reporte_{hoy()}.md"
    reporte.write_text(
        f"# Reporte {hoy()}\n\n- Borradores nuevos: {len(creados)}\n- Cambios de estado: {len(cambios)}\n"
        f"- Historial: {json.dumps(hist.resumen(), ensure_ascii=False)}\n"
        f"- Personas para conectar: datos/personas_para_conectar.md\n"
        f"- Hashtags: datos/hashtags_ranking.md\n", encoding="utf-8")
    print(f"Reporte: {reporte}")


# --------------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="buscador_empleo", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-p", "--perfil", default="config/perfil.yaml")
    ap.add_argument("--historial", help="Ruta al historial .md (por defecto datos/historial.md)")
    sub = ap.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("consultas", help="URLs a visitar (feed, hashtags, palabras)")
    s.add_argument("--tipo", nargs="*", choices=["feed", "hashtag", "palabras"])
    s.add_argument("--hoy", type=int, metavar="N", help="Solo N para hoy, en rotación entre sesiones")
    s.set_defaults(f=cmd_consultas)
    s = sub.add_parser("js", help="Script extractor con la configuración del perfil")
    s.add_argument("-o", "--salida")
    s.add_argument("--imagenes", action="store_true", help="Traer también posts sin correo pero con afiche")
    s.add_argument("--scrolls", type=int, help="Cuántas veces bajar la página (feed: 25)")
    s.set_defaults(f=cmd_js)
    s = sub.add_parser("importar", help="Crudo -> vacantes filtradas + borradores redactados")
    s.add_argument("archivos", nargs="+")
    s.add_argument("--ia", action="store_true", help="Revisar aceptadas con Claude Haiku")
    s.add_argument("--imagenes", action="store_true", help="Leer antes los afiches (OCR / Haiku)")
    s.set_defaults(f=cmd_importar)
    s = sub.add_parser("imagenes", help="Lee afiches de posts sin correo (OCR y Haiku)")
    s.add_argument("archivos", nargs="+"); s.add_argument("--sin-ia", action="store_true", dest="sin_ia")
    s.set_defaults(f=cmd_imagenes)
    s = sub.add_parser("hashtags", help="Ranking de hashtags útiles")
    s.add_argument("--minimo", type=int, default=2, help="Posts mínimos para aparecer (por defecto 2)")
    s.add_argument("--maximo", type=int, default=40)
    s.add_argument("--actualizar-doc", action="store_true", dest="actualizar_doc",
                   help="Reescribe la tabla de docs/HASHTAGS.md")
    s.set_defaults(f=cmd_hashtags)
    s = sub.add_parser("personas", help="Ranking de autores para seguir/conectar a mano")
    s.add_argument("--top", type=int, default=15); s.set_defaults(f=cmd_personas)
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
