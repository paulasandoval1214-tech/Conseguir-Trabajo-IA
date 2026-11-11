@echo off
REM Doble clic: pone el CV correcto en los borradores de Gmail que no tienen adjunto
REM (por ejemplo, los que Claude dejó desde el chat). No envía nada.
cd /d "%~dp0.."
.venv\Scripts\python.exe -m buscador_empleo -p config\perfil.yaml adjuntar
pause
