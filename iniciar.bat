@echo off
chcp 65001 >nul
title CONTROL CELULAR
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo   Primera vez: instalando lo necesario...
  call "%~dp0instalar.bat" || exit /b 1
)
".venv\Scripts\python.exe" -u arranque.py %*
pause
