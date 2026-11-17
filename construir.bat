@echo off
chcp 65001 >nul
title CONTROL CELULAR - Construir
cd /d "%~dp0"
rem Arma, en dist\:
rem   ControlCelular-Instalar-<versión>.exe   el instalador (lo recomendado para compartir)
rem   ControlCelular.exe                      la versión portátil (un solo archivo, sin instalar)
rem La versión en carpeta (para el instalador) se arma en %TEMP%: dentro de OneDrive se traba al borrarla.

if not exist ".venv\Scripts\python.exe" call "%~dp0instalar.bat" || exit /b 1
".venv\Scripts\python.exe" -m pip install -q -r requirements-dev.txt || goto :error
".venv\Scripts\python.exe" herramientas\hacer_iphone.py || goto :error
rem Antes de armar se corren las pruebas: si algo está roto, no se arma.
call "%~dp0probar.bat" sin-pausa || goto :error
".venv\Scripts\python.exe" herramientas\iconos.py || goto :error
".venv\Scripts\python.exe" -c "import version; print(version.VERSION)" > "%TEMP%\control-celular-version.txt" || goto :error
set /p VERSION=<"%TEMP%\control-celular-version.txt"
echo   Versión: %VERSION%

set OPCIONES=--noconfirm --clean --console --name ControlCelular --icon "%~dp0herramientas\icono.ico" ^
  --add-data "%~dp0web;web" --add-data "%~dp0terceros;terceros" --collect-all vgamepad ^
  --hidden-import pystray._win32 --hidden-import bandeja ^
  --workpath "%TEMP%\ControlCelular-build" --specpath "%TEMP%\ControlCelular-build"

echo.
echo   1/3  Versión portátil (un solo archivo)...
".venv\Scripts\python.exe" -m PyInstaller %OPCIONES% --onefile --distpath dist arranque.py || goto :error

echo.
echo   2/3  Versión en carpeta, para el instalador (arranca más rápido)...
".venv\Scripts\python.exe" -m PyInstaller %OPCIONES% --onedir --distpath "%TEMP%\ControlCelular-carpeta" arranque.py || goto :error

echo.
echo   3/3  Instalador...
set ISCC=
for %%r in ("%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe") do if exist %%r set ISCC=%%r
if not defined ISCC (
  echo   No encontré Inno Setup 6: se armó solo la versión portátil. Para el instalador, instalá Inno Setup.
  goto :listo
)
%ISCC% /Q /DVersion=%VERSION% /DOrigen="%TEMP%\ControlCelular-carpeta\ControlCelular" herramientas\instalador.iss || goto :error

:listo
echo.
echo   Listo, en la carpeta dist:
echo     ControlCelular-Instalar-%VERSION%.exe   (instalador)
echo     ControlCelular.exe                      (portátil)
echo.
if "%1"=="" pause
exit /b 0

:error
echo.
echo   Algo falló al construir. Revisá el mensaje de arriba.
if "%1"=="" pause
exit /b 1
