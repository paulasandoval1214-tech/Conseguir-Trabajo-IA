@echo off
REM Doble clic: lee los afiches (OCR) de lo último que se extrajo y vuelve a filtrar.
REM Útil cuando la búsqueda se hizo desde el chat con `js --imagenes`. No envía nada.
cd /d "%~dp0.."
.venv\Scripts\python.exe -m buscador_empleo -p config\perfil.yaml importar --imagenes "datos\crudo\*.json"
pause
