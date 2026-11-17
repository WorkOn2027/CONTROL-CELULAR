"""La limpieza de versiones viejas del instalador: borra SOLO lo de Control Celular, nunca otra cosa."""

import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "herramientas" / "limpiar_viejas.ps1"
pytestmark = pytest.mark.skipif(shutil.which("powershell") is None, reason="sin PowerShell")


def test_borra_solo_versiones_viejas_de_control_celular(tmp_path):
    descargas, escritorio, temporal = tmp_path / "Descargas", tmp_path / "Escritorio", tmp_path / "Temp"
    for c in (descargas, escritorio, temporal):
        c.mkdir()
    se_borran = [descargas / "ControlCelular.exe", descargas / "ControlCelular (1).exe",
                 descargas / "ControlCelular-Instalar-1.4.0.exe", escritorio / "ControlCelular-Instalar-1.3.0 (2).exe"]
    quedan = [descargas / "ControlCelular-Instalar-1.5.0.exe",  # el instalador que se está usando ahora
              descargas / "MiControlCelular.exe", descargas / "ControlCelularViejo.exe",
              descargas / "ControlCelular.txt", descargas / "otro-programa.exe", escritorio / "Control Celular.lnk"]
    for f in se_borran + quedan:
        f.write_text("x")
    # Restos temporales: uno de Control Celular (se borra), uno de otro programa y una carpeta cualquiera (quedan)
    nuestro = temporal / "_MEI12345"
    (nuestro / "web").mkdir(parents=True)
    (nuestro / "web" / "index.html").write_text("x")
    (nuestro / "terceros").mkdir()
    (nuestro / "terceros" / "ViGEmBus_1.22.0_x64_x86_arm64.exe").write_text("x")
    ajeno = temporal / "_MEI99999"
    (ajeno / "web").mkdir(parents=True)
    (ajeno / "web" / "index.html").write_text("x")
    cualquiera = temporal / "OtraCarpeta"
    cualquiera.mkdir()

    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT),
                        "-Actual", str(descargas / "ControlCelular-Instalar-1.5.0.exe"),
                        "-Carpetas", f"{descargas}|{escritorio}", "-Temporal", str(temporal)],
                       capture_output=True, text=True, timeout=60)
    assert "total: 5" in r.stdout, r.stdout + r.stderr
    for f in se_borran:
        assert not f.exists(), f"tendría que haberse borrado: {f.name}"
    assert not nuestro.exists()
    for f in quedan:
        assert f.exists(), f"NO tendría que haberse borrado: {f.name}"
    assert ajeno.exists() and cualquiera.exists()
