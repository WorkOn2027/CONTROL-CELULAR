"""Dónde están las cosas, tanto corriendo como script de Python como empaquetado en ControlCelular.exe.

- RECURSOS: archivos que vienen con el programa (la página web). En el .exe están dentro del propio .exe.
- DATOS: lo que se crea en cada PC (certificados, celulares emparejados). En el .exe se guarda en
  %LOCALAPPDATA%\\ControlCelular, así el .exe puede estar en cualquier carpeta (incluso en Descargas).
"""

import os
import sys
from pathlib import Path

EMPAQUETADO = getattr(sys, "frozen", False)
_AQUI = Path(__file__).resolve().parent

RECURSOS = Path(getattr(sys, "_MEIPASS", _AQUI))
if os.environ.get("CONTROL_DATOS"):  # las pruebas usan una carpeta aparte, para no tocar tus datos
    DATOS = Path(os.environ["CONTROL_DATOS"])
elif EMPAQUETADO:
    DATOS = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "ControlCelular"
else:
    DATOS = _AQUI
DATOS.mkdir(parents=True, exist_ok=True)
