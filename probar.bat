@echo off
chcp 65001 >nul
title CONTROL CELULAR - Pruebas
cd /d "%~dp0"
rem Corre todas las pruebas automáticas. No tocan tus datos ni tus puertos y no necesitan ViGEmBus.

if not exist ".venv\Scripts\python.exe" call "%~dp0instalar.bat" || exit /b 1
".venv\Scripts\python.exe" -m pip install -q -r requirements-dev.txt || goto :error

echo.
echo   1/2  ¿La versión de iPhone está al día con la de Android?
".venv\Scripts\python.exe" herramientas\hacer_iphone.py --comprobar || goto :error

echo.
echo   2/2  Pruebas (servidor, celulares, controles, certificados, Steam y las páginas en Chrome)...
".venv\Scripts\python.exe" -m pytest tests -q || goto :error

echo.
echo   Todo bien.
if "%1"=="" pause
exit /b 0

:error
echo.
echo   Alguna prueba falló. Revisá el mensaje de arriba.
if "%1"=="" pause
exit /b 1
