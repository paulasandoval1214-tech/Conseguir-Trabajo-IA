# Instalación en Windows (PowerShell). Ejecutar desde la carpeta del repo:
#   powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv")) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[local]"

New-Item -ItemType Directory -Force -Path cvs, datos, secretos | Out-Null
if (-not (Test-Path "config\perfil.yaml")) { Copy-Item config\perfil.example.yaml config\perfil.yaml }
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }

Write-Host ""
Write-Host "Listo. Siguientes pasos:"
Write-Host "  1. Edita config\perfil.yaml con tus datos y líneas de búsqueda."
Write-Host "  2. Copia tus CV en PDF a la carpeta cvs\ (nombres iguales a los del perfil)."
Write-Host "  3. Pon tus claves en .env y credentials.json en secretos\ (ver docs\INSTALACION_WINDOWS.md)."
Write-Host "  4. Prueba:  .\.venv\Scripts\python.exe -m buscador_empleo borradores --simular"
