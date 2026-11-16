@echo off
REM Doble clic UNA vez: abre un navegador para que inicies sesión en LinkedIn a mano.
REM La sesión queda guardada en secretos\perfil_navegador\ (nunca se guarda la contraseña).
REM La búsqueda nocturna la reutiliza. Repítelo solo si LinkedIn cierra la sesión.
cd /d "%~dp0.."
.venv\Scripts\python.exe -m buscador_empleo -p config\perfil.yaml sesion-linkedin
pause
