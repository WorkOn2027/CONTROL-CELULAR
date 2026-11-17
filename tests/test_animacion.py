"""La animación de arranque: sus cuadros y cuándo se muestra (sin abrir ventanas)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import animacion  # noqa: E402

WEB = Path(__file__).resolve().parent.parent / "web"


def test_se_enciende_parpadeando_y_se_desvanece():
    assert animacion.brillo(0) == 0
    assert animacion.brillo(.34) > .5 and animacion.brillo(.43) < .2  # parpadeo
    assert animacion.brillo(1.5) == 1
    assert animacion.giro(.5) == 0 and animacion.giro(2.5) == 1  # una vuelta de colores entera
    assert animacion.opacidad(1) == 255 and animacion.opacidad(animacion.DURACION) == 0


def test_cuadros():
    c = animacion.Cuadros(WEB)
    vacio, encendido = c.cuadro(0), c.cuadro(1.5)
    assert vacio.size == encendido.size == c.tam
    assert vacio.getchannel("A").getextrema()[1] == 0  # al principio no se ve nada
    # encendido: el neón brilla (algún píxel con color fuerte)
    assert max(banda.getextrema()[1] for banda in encendido.convert("RGB").split()) > 200
    assert len(animacion._bgra_premultiplicado(encendido)) == c.tam[0] * c.tam[1] * 4


@pytest.mark.parametrize("argumento", ["--minimizado", "--tras-instalar"])
def test_no_sale_al_arrancar_oculto(monkeypatch, argumento):
    monkeypatch.setattr(sys, "argv", ["x", argumento])
    assert not animacion.debe_mostrarse()


def test_se_puede_apagar(monkeypatch):
    monkeypatch.setenv("CONTROL_SIN_ANIMACION", "1")
    assert not animacion.debe_mostrarse()
