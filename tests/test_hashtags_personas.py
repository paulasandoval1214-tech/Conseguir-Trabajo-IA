"""Rankings de hashtags y de personas para conectar (datos ficticios)."""

import csv

from buscador_empleo import hashtags, personas
from buscador_empleo.fuentes.navegador import consultas, url_busqueda_linkedin
from buscador_empleo.historial import Historial, Registro
from buscador_empleo.modelos import PostCrudo

VACANTE_GH = ("Estamos buscando Analista de Selección en Bogotá. Envía tu hoja de vida a "
              "{c} #TrabajoSiHay #VacantesBogota")
VACANTE_CONTADOR = "Buscamos Contador en Bogotá. Envía tu hoja de vida a {c} #TrabajoSiHay #Contabilidad"


def _post(texto, correo, autor="Ana Pérez Gómez", url="https://www.linkedin.com/in/ana-ejemplo/"):
    return PostCrudo(texto=texto.format(c=correo), correos=[correo], autor=autor, autor_url=url,
                     hashtags=[h.lower() for h in __import__("re").findall(r"#\w+", texto)])


def test_ranking_hashtags(perfil):
    posts = [
        _post(VACANTE_GH, "uno@empresa-ejemplo.com"),
        _post(VACANTE_GH, "dos@empresa-ejemplo.com"),
        _post(VACANTE_CONTADOR, "tres@empresa-ejemplo.com"),
    ]
    filas = {f["hashtag"]: f for f in hashtags.analizar(posts, perfil)}
    assert filas["#trabajosihay"]["posts"] == 3 and filas["#trabajosihay"]["utiles"] == 2
    assert filas["#vacantesbogota"]["tasa"] == 1.0
    assert filas["#contabilidad"]["utiles"] == 0
    assert filas["#vacantesbogota"]["por_linea"] == {"gestion_humana": 2}


def test_actualizar_doc_entre_marcas(tmp_path):
    doc = tmp_path / "HASHTAGS.md"
    doc.write_text(f"# Hashtags\n\nTexto curado.\n\n{hashtags.MARCA_INICIO}\nviejo\n{hashtags.MARCA_FIN}\n\nFin.\n",
                   encoding="utf-8")
    assert hashtags.actualizar_doc("| tabla |", "2026-11-16", 10, doc)
    texto = doc.read_text(encoding="utf-8")
    assert "Texto curado." in texto and "| tabla |" in texto and "viejo" not in texto and "Fin." in texto


def test_personas_ranking_y_estados(perfil, tmp_path):
    posts = [
        (_post(VACANTE_GH, "uno@empresa-ejemplo.com"), "2026-11-15"),
        (_post(VACANTE_GH, "dos@empresa-ejemplo.com"), "2026-11-16"),
        # El mismo post repetido (crudo + vacantes) no debe contar dos veces.
        (_post(VACANTE_GH, "dos@empresa-ejemplo.com"), "2026-11-16"),
        (_post(VACANTE_CONTADOR, "tres@empresa-ejemplo.com", autor="Página Contable",
               url="https://www.linkedin.com/company/contable-ejemplo/"), "2026-11-16"),
    ]
    hist = Historial(registros=[Registro("2026-11-11", "Empresa", "Analista de Selección", "Bogotá",
                                         "cuatro@empresa-ejemplo.com", "gestion_humana",
                                         "LinkedIn (Empresa / Luis Ejemplo Ruiz)", "Enviado")])
    filas = personas.agrupar(posts, perfil, personas.fuentes_del_historial(hist))
    por_nombre = {f["nombre"]: f for f in filas}
    ana = por_nombre["Ana Pérez Gómez"]
    assert ana["posts"] == 2 and ana["utiles"] == 2 and ana["tipo"] == "persona"
    assert ana["url"] == "https://www.linkedin.com/in/ana-ejemplo/"
    assert "Página Contable" not in por_nombre  # un solo post sin vacante útil
    luis = por_nombre["Luis Ejemplo Ruiz"]
    assert luis["tipo"] == "persona?" and "/search/results/people/" in luis["url"]

    ruta_csv, ruta_md = personas.escribir(filas, tmp_path)
    # La persona marca a mano "Conectado": la siguiente ejecución lo respeta.
    with ruta_csv.open(encoding="utf-8-sig", newline="") as fh:
        filas_csv = list(csv.DictReader(fh))
    for f in filas_csv:
        if f["nombre"] == "Ana Pérez Gómez":
            f["estado"], f["notas"] = "Conectado", "aceptó"
    with ruta_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=personas.COLUMNAS)
        w.writeheader()
        w.writerows(filas_csv)
    filas2 = personas.agrupar(posts, perfil, personas.fuentes_del_historial(hist))
    personas.escribir(filas2, tmp_path)
    ana2 = next(f for f in filas2 if f["nombre"] == "Ana Pérez Gómez")
    assert ana2["estado"] == "Conectado" and ana2["notas"] == "aceptó"
    assert "Ana Pérez Gómez" in ruta_md.read_text(encoding="utf-8")


def test_consultas_incluye_feed_y_hashtags(perfil):
    perfil.datos["busqueda"] = {**perfil.busqueda, "linkedin_feed": True,
                                "hashtags_generales": ["trabajosihay", "#VacantesBogota"]}
    cs = consultas(perfil)
    assert cs[0]["tipo"] == "feed"
    urls = [c["url"] for c in cs]
    assert url_busqueda_linkedin("#trabajosihay", perfil.busqueda.get("periodo_linkedin", "past-week")) in urls
    assert all("sortBy" not in u for u in urls)  # relevancia por defecto
    assert {c["tipo"] for c in consultas(perfil, {"hashtag"})} == {"hashtag"}


def test_rotacion_de_consultas(perfil):
    from buscador_empleo.fuentes.navegador import elegir_consultas

    perfil.datos["busqueda"] = {**perfil.busqueda, "linkedin_feed": True, "rotar_consultas": True,
                                "hashtags_generales": ["#a", "#b"]}
    total = len(consultas(perfil)) - 1  # sin el feed
    dia1, est = elegir_consultas(perfil, 4, {"inicio": 0})
    dia2, est = elegir_consultas(perfil, 4, est)
    assert dia1[0]["tipo"] == "feed" and dia2[0]["tipo"] == "feed"
    assert len(dia1) == 4 and {c["url"] for c in dia1[1:]}.isdisjoint({c["url"] for c in dia2[1:]})
    # Después de suficientes días se han visitado todas.
    vistas = {c["url"] for c in dia1[1:] + dia2[1:]}
    for _ in range(total):
        d, est = elegir_consultas(perfil, 4, est)
        vistas |= {c["url"] for c in d[1:]}
    assert len(vistas) == total
