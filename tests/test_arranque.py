"""El arranque nunca se cierra sin explicar, y si falta ViGEmBus ofrece instalar el que viene incluido.

(Una PC sin ViGEmBus hacía que el .exe se cerrara al instante, sin mensaje: vgamepad busca el driver apenas se carga.)
"""

import atexit
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import arranque

RAIZ = Path(__file__).resolve().parent.parent


def arrancar(respuesta="", **variables):
    datos = tempfile.mkdtemp(prefix="control-celular-arranque-")
    atexit.register(shutil.rmtree, datos, True)  # se borra al terminar las pruebas
    entorno = dict(os.environ, CONTROL_DATOS=datos, CONTROL_SIN_NAVEGADOR="1", CONTROL_SIN_FIREWALL="1",
                   CONTROL_SIN_BANDEJA="1", PYTHONIOENCODING="utf-8", **variables)
    r = subprocess.run([sys.executable, str(RAIZ / "arranque.py")], cwd=RAIZ, env=entorno, input=respuesta,
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    return r, r.stdout + r.stderr, Path(datos)


def test_el_instalador_incluido_es_el_oficial():
    p = RAIZ / "terceros" / arranque.INSTALADOR_VIGEMBUS
    assert p.is_file(), "falta el instalador de ViGEmBus en terceros/"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == arranque.SHA256_INSTALADOR
    assert (RAIZ / "terceros" / "LICENCIA-ViGEmBus.txt").is_file()  # la licencia BSD pide incluir el aviso


def test_sin_vigembus_ofrece_instalarlo_y_si_dice_que_no_explica_como():
    r, salida, _ = arrancar("n\n", CONTROL_SIMULAR_SIN_VIGEM="1")
    assert r.returncode == 1
    assert "¿Lo instalo ahora?" in salida or "Install it now?" in salida
    assert "github.com/nefarius/ViGEmBus/releases" in salida  # si no quiere, cómo bajarlo a mano
    assert "Traceback" not in salida


def test_sin_vigembus_dice_que_si_instala_y_vuelve_a_abrir():
    # El instalador se simula (no abre nada). Como en la prueba el driver sigue "faltando", al volver a abrirse
    # tiene que pedir reiniciar la PC en vez de ofrecer instalar otra vez (no entra en un bucle).
    r, salida, _ = arrancar("s\n", CONTROL_SIMULAR_SIN_VIGEM="1", CONTROL_SIMULAR_INSTALADOR="1")
    assert "quedó instalado" in salida or "is installed" in salida
    assert "Reiniciá la PC" in salida or "Restart your PC" in salida
    assert salida.count("¿Lo instalo ahora?") + salida.count("Install it now?") == 1


def test_otro_error_se_muestra_y_queda_guardado():
    r, salida, datos = arrancar(CONTROL_PUERTO="no-es-un-numero")  # provoca un error al cargar el servidor
    assert r.returncode == 1 and "no-es-un-numero" in salida and "Enter" in salida
    assert "no-es-un-numero" in (datos / "error.txt").read_text("utf-8")
