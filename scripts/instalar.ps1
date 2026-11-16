# Instalación en Windows (PowerShell). Ejecutar desde la carpeta del repo:
#   powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
# Opciones:
#   -SinLinkedIn   no instala Playwright/Chromium (sin búsqueda en LinkedIn desde el PC)
#   -SinOCR        no instala Tesseract ni los idiomas (sin lectura de afiches)
param([switch]$SinLinkedIn, [switch]$SinOCR)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

# 1) Entorno de Python y dependencias
if (-not (Test-Path ".venv")) { python -m venv .venv }
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip
$extras = "local"
if (-not $SinOCR) { $extras += ",imagenes" }
if (-not $SinLinkedIn) { $extras += ",linkedin" }
& $py -m pip install -e ".[$extras]"

# 2) Navegador para LinkedIn (Playwright)
if (-not $SinLinkedIn) { & $py -m playwright install chromium }

# 3) OCR de afiches: Tesseract + idiomas español e inglés (sin permisos de administrador)
if (-not $SinOCR) {
  $tess = Get-Command tesseract -ErrorAction SilentlyContinue
  $rutas = @("C:\Program Files\Tesseract-OCR\tesseract.exe", "$env:LOCALAPPDATA\Programs\Tesseract-OCR\tesseract.exe")
  if (-not $tess -and -not ($rutas | Where-Object { Test-Path $_ })) {
    Write-Host "Instalando Tesseract OCR con winget (puede pedir confirmación)..."
    try { winget install --id UB-Mannheim.TesseractOCR -e --accept-source-agreements --accept-package-agreements }
    catch { Write-Host "No se pudo con winget. Instálalo a mano: https://github.com/UB-Mannheim/tesseract/wiki" }
  }
  $tessdata = "herramientas\tessdata"
  New-Item -ItemType Directory -Force -Path $tessdata | Out-Null
  foreach ($idioma in @("spa", "eng")) {
    $destino = Join-Path $tessdata "$idioma.traineddata"
    if (-not (Test-Path $destino)) {
      Write-Host "Descargando idioma $idioma para el OCR..."
      Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_fast/raw/main/$idioma.traineddata" -OutFile $destino
    }
  }
}

# 4) Carpetas privadas y archivos de configuración
New-Item -ItemType Directory -Force -Path cvs, datos, secretos | Out-Null
if (-not (Test-Path "config\perfil.yaml")) { Copy-Item config\perfil.example.yaml config\perfil.yaml }
if (-not (Test-Path ".env")) { Copy-Item .env.example .env }

Write-Host ""
Write-Host "Listo. Siguientes pasos:"
Write-Host "  1. Edita config\perfil.yaml con tus datos y líneas de búsqueda."
Write-Host "  2. Copia tus CV en PDF a la carpeta cvs\ (nombres iguales a los del perfil)."
Write-Host "  3. Pon tus claves en .env y credentials.json en secretos\ (ver docs\INSTALACION_WINDOWS.md)."
if (-not $SinLinkedIn) { Write-Host "  4. Inicia sesión en LinkedIn una vez: doble clic en scripts\iniciar_sesion_linkedin.bat" }
Write-Host "  5. Prueba:  .\.venv\Scripts\python.exe -m buscador_empleo borradores --simular"
Write-Host "  6. Programa la noche: powershell -ExecutionPolicy Bypass -File scripts\programar_tarea.ps1 -Hora 21:30"
