"""Configuración común de las pruebas.

Las pruebas nunca tocan tus datos ni tus puertos: usan una carpeta temporal, otros puertos y un control "de
mentira" (no hace falta ViGEmBus).
"""

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "herramientas"))

# Antes de importar cualquier módulo del proyecto: datos en una carpeta temporal y control de mentira.
if "CONTROL_DATOS" not in os.environ:
    os.environ["CONTROL_DATOS"] = tempfile.mkdtemp(prefix="control-celular-pruebas-")
    atexit.register(shutil.rmtree, os.environ["CONTROL_DATOS"], True)  # no dejar carpetas en Temp
os.environ["CONTROL_MANDO_FALSO"] = "1"
os.environ["CONTROL_SIN_FARO"] = "1"       # las pruebas no avisan por la red
os.environ["CONTROL_SIN_BLUETOOTH"] = "1"  # ni buscan celulares por Bluetooth
