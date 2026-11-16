@echo off
REM Doble clic: actualiza la lista de personas y páginas para seguir/conectar en LinkedIn
REM (datos\personas_para_conectar.csv y .md) y abre el CSV. No conecta con nadie.
cd /d "%~dp0.."
.venv\Scripts\python.exe -m buscador_empleo -p config\perfil.yaml personas
start "" "datos\personas_para_conectar.csv"
pause
