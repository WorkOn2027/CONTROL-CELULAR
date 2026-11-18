"""La animación de arranque: sus planos, sus cuadros y cuándo se muestra (sin abrir ventanas)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import animacion  # noqa: E402

WEB = Path(__file__).resolve().parent.parent / "web"


def test_los_tres_planos_en_orden():
    # 1. parado, apagado
    assert animacion.giro(.3) == 0 and animacion.pantalla(.3) == 0 and animacion.brillo(.3) == 0
    # 2. gira hasta quedar acostado, todavía apagado
    assert 0 < animacion.giro(.95) < 1 and animacion.giro(1.4) == 1 and animacion.pantalla(1.4) == 0
    # 3. se prende la pantalla y el neón del control parpadea y se afirma
    assert animacion.pantalla(1.8) == 1
    assert animacion.brillo(1.76) > .5 and animacion.brillo(1.85) < .2 and animacion.brillo(2.5) == 1
    # aparece y se desvanece
    assert animacion.opacidad(0) == 0 and animacion.opacidad(1.5) == 255 and animacion.opacidad(animacion.DURACION) == 0


def _neon(img):
    """Cuántos píxeles brillan con color (el neón)."""
    hsv = img.convert("RGB").convert("HSV")
    return sum(1 for s, v in zip(hsv.getchannel("S").tobytes(), hsv.getchannel("V").tobytes()) if s > 120 and v > 180)


def test_cuadros():
    c = animacion.Cuadros(WEB)
    parado, acostado, control = c.cuadro(.3), c.cuadro(1.4), c.cuadro(2.6)
    assert parado.size == acostado.size == control.size == c.tam
    # parado es más alto que ancho; acostado, al revés (lo que no es negro es el celular)
    def caja(img):
        return img.convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()
    x0, y0, x1, y1 = caja(parado)
    assert y1 - y0 > x1 - x0
    x0, y0, x1, y1 = caja(acostado)
    assert x1 - x0 > y1 - y0
    # con la pantalla apagada no hay neón; con el control prendido, mucho
    assert _neon(acostado) == 0 and _neon(control) > 2000
    assert len(animacion._bgra_premultiplicado(control)) == c.tam[0] * c.tam[1] * 4


@pytest.mark.parametrize("argumento", ["--minimizado", "--tras-instalar"])
def test_no_sale_al_arrancar_oculto(monkeypatch, argumento):
    monkeypatch.setattr(sys, "argv", ["x", argumento])
    assert not animacion.debe_mostrarse()


def test_se_puede_apagar(monkeypatch):
    monkeypatch.setenv("CONTROL_SIN_ANIMACION", "1")
    assert not animacion.debe_mostrarse()
