"""Pruebas de la lectura de afiches. Las de OCR real se saltan si no hay Tesseract."""

import shutil
from pathlib import Path

import pytest

from buscador_empleo import imagenes
from buscador_empleo.extraccion import post_a_vacantes
from buscador_empleo.modelos import PostCrudo


def _post_con_afiche(**extra):
    base = dict(texto="Hitss Colombia 16 h ¡Estamos contratando! Únete a nuestro equipo #hiring",
                autor="Empresa Ejemplo", sin_correo=True,
                imagenes=[{"src": "https://media.licdn.com/dms/image/v2/X/feedshare-shrink_800/0/1?e=1&t=a", "alt": "Ver imagen"}])
    base.update(extra)
    return PostCrudo(**base)


def test_normalizar_texto_ocr_arregla_correos():
    t = imagenes.normalizar_texto_ocr("Envía tu HV a seleccion @ empresa-ejemplo .com\n\n\nAsunto: Analista")
    assert "seleccion@empresa-ejemplo.com" in t
    assert imagenes.normalizar_texto_ocr("talento(at)empresa-ejemplo.com.co") == "talento@empresa-ejemplo.com.co"
    assert "rrhh@empresa-ejemplo.com.co" in imagenes.normalizar_texto_ocr("rrhh@empresa-ejemplo.com . co")


def test_clave_imagen_ignora_firma():
    a = "https://media.licdn.com/dms/image/v2/X/feedshare-shrink_800/0/1?e=111&t=aaa"
    b = "https://media.licdn.com/dms/image/v2/X/feedshare-shrink_800/0/1?e=222&t=bbb"
    assert imagenes.clave_imagen(a) == imagenes.clave_imagen(b)


def test_necesita_lectura():
    cfg = imagenes.config(None)
    assert imagenes.necesita_lectura(_post_con_afiche(), cfg)
    assert not imagenes.necesita_lectura(_post_con_afiche(sin_correo=False), cfg)
    assert not imagenes.necesita_lectura(_post_con_afiche(imagenes=[]), cfg)
    assert imagenes.necesita_lectura(_post_con_afiche(sin_correo=False), {**cfg, "leer_con_correo": True})


def test_leer_posts_ocr_y_cache(tmp_path):
    post = _post_con_afiche()
    llamadas = {"ocr": 0, "ia": 0}

    def ocr(_ruta):
        llamadas["ocr"] += 1
        return "ANALISTA DE SELECCIÓN\nBogotá\nEnvía tu hoja de vida a talento @ empresa-ejemplo.com"

    def ia(_ruta):
        llamadas["ia"] += 1
        return "no debería llamarse"

    est = imagenes.leer_posts([post], None, tmp_path, usar_ia=True,
                              descargar_fn=lambda u, c: tmp_path / "x.jpg", ocr_fn=ocr, ia_fn=ia)
    assert est["con_correo"] == 1 and llamadas == {"ocr": 1, "ia": 0}
    assert "talento@empresa-ejemplo.com" in post.texto_imagen

    # Segunda vez: sale de la caché, sin volver a leer.
    post2 = _post_con_afiche()
    imagenes.leer_posts([post2], None, tmp_path, usar_ia=True,
                        descargar_fn=lambda u, c: tmp_path / "x.jpg", ocr_fn=ocr, ia_fn=ia)
    assert llamadas["ocr"] == 1 and "cache" in post2.lectura_imagen


def test_leer_posts_usa_ia_si_ocr_no_encuentra_correo(tmp_path):
    post = _post_con_afiche()
    est = imagenes.leer_posts([post], None, tmp_path, usar_ia=True,
                              descargar_fn=lambda u, c: tmp_path / "x.jpg",
                              ocr_fn=lambda r: "texto borroso sin correo",
                              ia_fn=lambda r: "Cargo: Analista de Datos\nCorreo: datos@empresa-ejemplo.com")
    assert est["ia"] == 1 and "datos@empresa-ejemplo.com" in post.texto_imagen


def test_vacante_desde_afiche(perfil, tmp_path):
    post = _post_con_afiche(texto_imagen="Buscamos Analista de Selección en Bogotá. "
                                         "Envía tu hoja de vida a seleccion@empresa-ejemplo.com")
    vs = post_a_vacantes(post, perfil.correos_ignorar)
    assert [v.correo for v in vs] == ["seleccion@empresa-ejemplo.com"]
    assert vs[0].ciudad == "Bogotá"
    assert "selecci" in vs[0].cargo.lower()


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract no instalado")
def test_ocr_real_con_tesseract(tmp_path):
    pytest.importorskip("pytesseract")
    from PIL import Image, ImageDraw, ImageFont

    fuente = None
    for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
        if Path(f).exists():
            fuente = ImageFont.truetype(f, 40)
    if fuente is None:
        pytest.skip("sin fuente TrueType para dibujar el afiche")
    im = Image.new("RGB", (900, 500), "white")
    d = ImageDraw.Draw(im)
    for i, linea in enumerate(["¡ESTAMOS BUSCANDO!", "Analista de Datos", "Bogotá - Híbrido",
                               "hv@empresa-ejemplo.com"]):
        d.text((40, 40 + i * 100), linea, fill="black", font=fuente)
    ruta = tmp_path / "afiche.png"
    im.save(ruta)
    texto = imagenes.normalizar_texto_ocr(imagenes.ocr_tesseract(ruta, "spa+eng"))
    assert "hv@empresa-ejemplo.com" in texto
    assert "Analista de Datos" in texto


def test_cli_importar_con_imagenes(tmp_path, monkeypatch, perfil, capsys):
    """Flujo completo: crudo con un post sin correo -> `importar --imagenes` -> vacante aceptada."""
    import json

    from buscador_empleo import cli

    perfil.datos["carpeta_datos"] = str(tmp_path)
    perfil.datos["imagenes"] = {"usar": True, "usar_ia_si_ocr_falla": False}
    monkeypatch.setattr(cli, "cargar_perfil", lambda _r: perfil)
    monkeypatch.setattr(imagenes, "descargar", lambda url, carpeta, timeout=20: tmp_path / "a.jpg")
    monkeypatch.setattr(imagenes, "ocr_tesseract", lambda ruta, idioma="", cmd="":
                        "VACANTE\nAnalista de Selección\nBogotá\nHV a: seleccion@empresa-ejemplo.com")
    crudo = tmp_path / "crudo.json"
    crudo.write_text(json.dumps([_post_con_afiche().a_dict()], ensure_ascii=False), encoding="utf-8")
    cli.main(["--historial", str(tmp_path / "h.md"), "importar", "--imagenes", str(crudo)])
    salida = capsys.readouterr().out
    assert "ACEPTADAS (1)" in salida and "seleccion@empresa-ejemplo.com" in salida
    # Lo leído queda guardado en el mismo crudo (no se vuelve a pagar OCR/IA).
    assert "seleccion@empresa-ejemplo.com" in json.loads(crudo.read_text(encoding="utf-8"))[0]["texto_imagen"]


def test_js_con_imagenes(tmp_path, monkeypatch, perfil):
    from buscador_empleo import cli

    monkeypatch.setattr(cli, "cargar_perfil", lambda _r: perfil)
    destino = tmp_path / "ext.js"
    cli.main(["--historial", str(tmp_path / "no.md"), "js", "--imagenes", "-o", str(destino)])
    assert '"incluirImagenes": true' in destino.read_text(encoding="utf-8")
