@echo off
chcp 65001 >nul
title CONTROL CELULAR - Construir el .exe
cd /d "%~dp0"
rem Arma dist\ControlCelular.exe: un solo archivo con Python, las librerías y la página del control adentro.

if not exist ".venv\Scripts\python.exe" call "%~dp0instalar.bat" || exit /b 1
".venv\Scripts\python.exe" -m pip install -q -r requirements-dev.txt || goto :error
".venv\Scripts\python.exe" herramientas\hacer_iphone.py || goto :error
rem Antes de armar el .exe se corren las pruebas: si algo está roto, no se arma.
call "%~dp0probar.bat" sin-pausa || goto :error
".venv\Scripts\python.exe" herramientas\iconos.py || goto :error

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --console ^
  --name ControlCelular ^
  --icon "%~dp0herramientas\icono.ico" ^
  --add-data "%~dp0web;web" ^
  --collect-all vgamepad ^
  --hidden-import pystray._win32 ^
  --hidden-import bandeja ^
  --distpath dist --workpath "%TEMP%\ControlCelular-build" --specpath "%TEMP%\ControlCelular-build" ^
  server.py || goto :error

echo.
echo   Listo: dist\ControlCelular.exe
echo.
pause
exit /b 0

:error
echo.
echo   Algo fallo al construir. Revisa el mensaje de arriba.
pause
exit /b 1
