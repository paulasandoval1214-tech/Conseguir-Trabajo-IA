from buscador_empleo import filtros
from buscador_empleo.extraccion import (extraer_anios, extraer_asunto, extraer_cargo,
                                        extraer_ingles, detectar_pais, post_a_vacantes)
from buscador_empleo.historial import Historial, Registro
from buscador_empleo.redaccion import redactar


def _vacantes(posts, perfil, conocidos=frozenset()):
    vs = []
    for p in posts:
        vs += post_a_vacantes(p, perfil.correos_ignorar)
    return {v.correo: v for v in filtros.aplicar(vs, perfil, set(conocidos))}


def test_extraccion_basica():
    assert extraer_anios("Mínimo 1 año de experiencia en cargos similares") == 1
    assert extraer_anios("Entre 3 y 6 años de experiencia en BI") == 3
    assert extraer_ingles("Nivel de inglés avanzado C1") == "avanzado"
    assert extraer_ingles("Inglés deseable, no indispensable") == ""
    assert detectar_pais("Ubicación: Quito, Ecuador #EmpleoColombia") == "ecuador"
    assert extraer_asunto('Asunto: Profesional de Análisis de Información - Bogotá 🚀') \
        == "Profesional de Análisis de Información - Bogotá"
    assert "Analista de Selección" in extraer_cargo("Buscamos Analista de Selección y Desarrollo en Bogotá")


def test_filtros_y_lineas(posts, perfil):
    v = _vacantes(posts, perfil)
    assert v["seleccion@empresa-ejemplo.com.co"].aceptada
    assert v["seleccion@empresa-ejemplo.com.co"].linea == "datos"
    assert v["talento@demo-ejemplo.com"].linea == "gestion_humana"
    assert v["seleccion@uni-ejemplo.edu.co"].asunto_exigido.startswith("Profesional de Análisis")
    assert not v["hh@headhunter-ejemplo.com"].aceptada          # inglés C1 / 3 años / senior
    assert "país" in v["rrhh@ecuador-ejemplo.com"].motivo_descarte
    assert not v["contable@firma-ejemplo.com"].aceptada          # otra profesión
    assert not v["persona@candidato-ejemplo.com"].aceptada          # persona buscando empleo


def test_no_repite_postulados(posts, perfil):
    v = _vacantes(posts, perfil, {"talento@demo-ejemplo.com"})
    assert "ya postulada" in v["talento@demo-ejemplo.com"].motivo_descarte


def test_redaccion_usa_plantilla(posts, perfil):
    v = _vacantes(posts, perfil)["talento@demo-ejemplo.com"]
    b = redactar(v, perfil)
    assert b.asunto.startswith("Analista de Selección")
    assert "Estoy interesada en la vacante de Analista de Selección" in b.cuerpo
    assert "selección, onboarding" in b.cuerpo
    assert b.cv.endswith("CV_Gestion_Humana.pdf")


def test_historial_ida_y_vuelta(tmp_path):
    ruta = tmp_path / "historial.md"
    h = Historial()
    h.agregar(Registro("2026-01-01", "Demo", "Analista", "Bogotá", "a@demo-ejemplo.com",
                       "datos", "linkedin", "Borrador listo"))
    assert not h.agregar(Registro("2026-01-02", "Demo", "Analista", "Bogotá", "A@demo-ejemplo.com",
                                  "datos", "linkedin", "Enviado"))
    h.escribir(ruta, {"datos": "Analista de datos"})
    h2 = Historial.leer(ruta)
    assert h2.correos() == {"a@demo-ejemplo.com"}
    assert h2.registros[0].estado == "Borrador listo"


def test_historial_lee_tablas_editadas_a_mano(tmp_path):
    ruta = tmp_path / "h.md"
    ruta.write_text(
        "# H\n\n## Línea 1\n\n| Fecha | Empresa | Cargo | Ciudad / modalidad | Correo | CV | Fuente | Estado | Respuesta / notas |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        "| 2026-11-11 | X | Analista | Bogotá | x@demo-ejemplo.com | Datos | LinkedIn | Enviado | |\n",
        encoding="utf-8")
    h = Historial.leer(ruta)
    assert h.correos() == {"x@demo-ejemplo.com"}
    assert h.registros[0].estado == "Enviado"


def test_historial_conserva_secciones_libres(tmp_path):
    ruta = tmp_path / "h.md"
    ruta.write_text(
        "# H\n\nCorreo de envío: algo\n\n## Datos\n\n| Fecha | Empresa | Cargo | Ciudad | Correo | Línea | Fuente | Estado | Notas |\n"
        "|---|---|---|---|---|---|---|---|---|\n| 2026-11-11 | X | A | B | x@demo-ejemplo.com | datos | L | Enviado | |\n\n"
        "## Descartadas\n- Vacante Y: pide inglés\n\n## Aprendizajes / ajustes\n- aprendizaje 1\n",
        encoding="utf-8")
    h = Historial.leer(ruta)
    h.escribir(ruta, {"datos": "Datos"})
    texto = ruta.read_text(encoding="utf-8")
    assert "Correo de envío: algo" in texto
    assert "## Descartadas" in texto and "Vacante Y" in texto
    assert "- aprendizaje 1" in texto and texto.count("x@demo-ejemplo.com") == 1


def test_fecha_limite_vencida():
    import datetime as dt
    from buscador_empleo.filtros import fecha_limite_vencida
    hoy = dt.date(2026, 11, 11)
    assert fecha_limite_vencida("envia tu hoja de vida hasta el jueves 15 de octubre", hoy)
    assert fecha_limite_vencida("fecha limite: 22 de octubre", hoy)
    assert not fecha_limite_vencida("fecha limite: 20 de noviembre de 2026", hoy)


def test_correo_con_tilde_no_se_recorta():
    from buscador_empleo.extraccion import RE_CORREO
    # "Matías.x@..." no es un correo válido: no debe salir "as.x@..." recortado
    assert RE_CORREO.findall("escribe a Matías.perez@demo-ejemplo.com hoy") == []
    assert RE_CORREO.findall("escribe a matias.perez@demo-ejemplo.com") == ["matias.perez@demo-ejemplo.com"]
