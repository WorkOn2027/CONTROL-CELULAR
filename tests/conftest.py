"""Configuración común de las pruebas.

Las pruebas nunca tocan tus datos ni tus puertos: usan una carpeta temporal, otros puertos y un control "de
mentira" (no hace falta ViGEmBus).
"""

import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "herramientas"))

# Antes de importar cualquier módulo del proyecto: datos en una carpeta temporal y control de mentira.
os.environ.setdefault("CONTROL_DATOS", tempfile.mkdtemp(prefix="control-celular-pruebas-"))
os.environ["CONTROL_MANDO_FALSO"] = "1"
