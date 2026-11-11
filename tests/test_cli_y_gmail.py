import json
from email import message_from_bytes

from buscador_empleo import cli, gmail_api
from buscador_empleo.config import RAIZ


def test_cli_importar_y_registrar(tmp_path, monkeypatch, perfil, capsys):
    perfil.datos["carpeta_datos"] = str(tmp_path)
    monkeypatch.setattr(cli, "cargar_perfil", lambda _r: perfil)
    hist = tmp_path / "historial.md"
    cli.main(["--historial", str(hist), "importar", str(RAIZ / "tests/fixtures/posts_ejemplo.json")])
    salida = capsys.readouterr().out
    assert "ACEPTADAS (3)" in salida
    vacantes = next(tmp_path.glob("vacantes_*.json"))
    borradores = json.loads(next(tmp_path.glob("borradores_*.json")).read_text(encoding="utf-8"))
    assert {b["linea"] for b in borradores} == {"datos", "gestion_humana"}

    cli.main(["--historial", str(hist), "registrar", str(vacantes)])
    texto = hist.read_text(encoding="utf-8")
    assert "talento@demo-ejemplo.com" in texto and "Borrador listo" in texto

    # Una segunda importación ya no propone las mismas vacantes
    cli.main(["--historial", str(hist), "importar", str(RAIZ / "tests/fixtures/posts_ejemplo.json")])
    assert "ACEPTADAS (0)" in capsys.readouterr().out


def test_js_incluye_configuracion(tmp_path, monkeypatch, perfil):
    monkeypatch.setattr(cli, "cargar_perfil", lambda _r: perfil)
    destino = tmp_path / "ext.js"
    cli.main(["--historial", str(tmp_path / "no.md"), "js", "-o", str(destino)])
    js = destino.read_text(encoding="utf-8")
    assert js.startswith("window.__CTI_CONFIG")
    assert '"ecuador"' in js and "power bi" in js


def test_mime_con_adjunto_y_firma(tmp_path):
    cv = tmp_path / "CV.pdf"
    cv.write_bytes(b"%PDF-1.4 prueba")
    msg = gmail_api._mime("rh@demo-ejemplo.com", "Analista", "Hola\n\nGracias", "<b>Firma</b>", cv)
    m = message_from_bytes(msg.as_bytes())
    partes = [p.get_content_type() for p in m.walk()]
    assert "application/pdf" in partes and "text/html" in partes
    assert m["To"] == "rh@demo-ejemplo.com"


def test_adivinar_linea(perfil):
    assert gmail_api.adivinar_linea("Analista de Datos", "experiencia en Power BI", perfil) == "datos"
    assert gmail_api.adivinar_linea("Analista de Selección", "procesos de selección y onboarding",
                                     perfil) == "gestion_humana"
