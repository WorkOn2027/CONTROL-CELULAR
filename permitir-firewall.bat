@echo off
chcp 65001 >nul
title CONTROL CELULAR - Firewall
rem Abre los puertos 8765 y 8443 SOLO en redes privadas y SOLO para equipos de tu misma red.
rem Windows pide permiso de administrador para hacerlo.

net session >nul 2>nul
if errorlevel 1 (
  echo   Windows va a pedir permiso de administrador: toca "Si".
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo.
echo   === CONTROL CELULAR: firewall ===
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try {" ^
  "  Get-NetFirewallRule -DisplayName 'CONTROL CELULAR' -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction Stop;" ^
  "  New-NetFirewallRule -DisplayName 'CONTROL CELULAR' -Description 'Control de juegos desde el celular (solo red local privada)' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765,8443 -Profile Private -RemoteAddress LocalSubnet -ErrorAction Stop | Out-Null;" ^
  "  Write-Host '  OK: regla creada (puertos 8765 y 8443, solo redes privadas y solo tu red local).'" ^
  "} catch { Write-Host ('  ERROR: no se pudo crear la regla: ' + $_.Exception.Message) }"

echo.
powershell -NoProfile -Command ^
  "Get-NetConnectionProfile | ForEach-Object { Write-Host ('  Red ''' + $_.Name + ''' (' + $_.InterfaceAlias + '): ' + $_.NetworkCategory) }"
echo.
echo   Si tu red de casa dice "Public", el celular no se va a poder conectar.
set /p RESP="  Marcar las redes conectadas ahora como PRIVADAS? Hacelo solo si es la red de tu casa (S/N): "
if /i "%RESP%"=="S" (
  powershell -NoProfile -Command ^
    "try { Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private -ErrorAction Stop; Write-Host '  OK: red marcada como privada.' }" ^
    "catch { Write-Host ('  ERROR: no se pudo cambiar la red: ' + $_.Exception.Message) }"
) else (
  echo   No se cambio nada. Podes hacerlo despues en Configuracion ^> Red e Internet ^> tu red ^> Privada.
)
echo.
pause
