@echo off
chcp 65001 >nul
title CONTROL CELULAR - Instalacion
cd /d "%~dp0"
echo.
echo   === CONTROL CELULAR: instalacion ===
echo.

rem --- Buscar Python 3.10 o mas nuevo ---
set "PY="
where py >nul 2>nul && py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo   No encontre Python 3.10 o mas nuevo.
  echo   Instalalo desde https://www.python.org/downloads/ ^(marca "Add python.exe to PATH"^)
  echo   y despues volve a ejecutar este archivo.
  echo.
  pause
  exit /b 1
)

rem --- Entorno propio del proyecto ---
if not exist ".venv\Scripts\python.exe" (
  echo   Creando el entorno de Python del proyecto ^(.venv^)...
  %PY% -m venv .venv || goto :error
)

echo   Instalando librerias ^(puede tardar unos minutos^)...
echo   Si se abre el instalador de ViGEmBus, acepta y segui los pasos.
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error

echo.
echo   Listo. Ejecuta iniciar.bat cada vez que quieras usar el control.
echo.
pause
exit /b 0

:error
echo.
echo   Algo fallo durante la instalacion. Revisa el mensaje de arriba.
echo.
pause
exit /b 1
