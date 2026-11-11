# Crea una tarea programada de Windows que corre la búsqueda todas las noches.
#   powershell -ExecutionPolicy Bypass -File scripts\programar_tarea.ps1 -Hora "21:30"
param([string]$Hora = "21:30", [string]$Nombre = "ConseguirTrabajoIA")
$repo = Split-Path $PSScriptRoot -Parent
$accion = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\ejecutar_noche.ps1`"" `
  -WorkingDirectory $repo
$disparador = New-ScheduledTaskTrigger -Daily -At $Hora
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd
Register-ScheduledTask -TaskName $Nombre -Action $accion -Trigger $disparador -Settings $ajustes -Force
Write-Host "Tarea '$Nombre' programada todos los días a las $Hora."
Write-Host "Para quitarla: Unregister-ScheduledTask -TaskName $Nombre"
