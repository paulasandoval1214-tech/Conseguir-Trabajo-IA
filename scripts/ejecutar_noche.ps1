# Ejecución nocturna: revisa respuestas, busca vacantes y deja borradores en Gmail.
# Nunca envía correos. Deja log en datos\logs\.
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force -Path datos\logs | Out-Null
$log = "datos\logs\noche_$(Get-Date -Format yyyy-MM-dd).log"
& .\.venv\Scripts\python.exe -m buscador_empleo -p config\perfil.yaml noche *>&1 | Tee-Object -FilePath $log
