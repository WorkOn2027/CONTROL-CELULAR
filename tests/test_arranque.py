"""El arranque nunca se cierra sin explicar: sin ViGEmBus avisa qué instalar; con otro error lo muestra y lo guarda.

(Una PC sin ViGEmBus hacía que el .exe se cerrara al instante, sin mensaje: vgamepad busca el driver apenas se carga.)
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def arrancar(**variables):
    datos = tempfile.mkdtemp(prefix="control-celular-arranque-")
    entorno = dict(os.environ, CONTROL_DATOS=datos, CONTROL_SIN_NAVEGADOR="1", CONTROL_SIN_FIREWALL="1",
                   CONTROL_SIN_BANDEJA="1", PYTHONIOENCODING="utf-8", **variables)
    r = subprocess.run([sys.executable, str(RAIZ / "arranque.py")], cwd=RAIZ, env=entorno, input="",
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    return r, Path(datos)


def test_sin_vigembus_avisa_que_instalar_y_no_se_cierra_solo():
    r, _ = arrancar(CONTROL_SIMULAR_SIN_VIGEM="1")
    salida = r.stdout + r.stderr
    assert r.returncode == 1
    assert "ViGEmBus" in salida and "github.com/nefarius/ViGEmBus/releases" in salida
    assert "Enter" in salida            # espera un Enter antes de cerrar (acá stdin está vacío y sigue)
    assert "Traceback" not in salida    # nada de errores en inglés técnico


def test_otro_error_se_muestra_y_queda_guardado():
    r, datos = arrancar(CONTROL_PUERTO="no-es-un-numero")  # provoca un error al cargar el servidor
    salida = r.stdout + r.stderr
    assert r.returncode == 1 and "no-es-un-numero" in salida and "Enter" in salida
    assert "no-es-un-numero" in (datos / "error.txt").read_text("utf-8")
