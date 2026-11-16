"""El control virtual: que cada mensaje del celular llegue como el botón correcto (Xbox 360 y DualShock 4)."""

import vgamepad as vg

from mandos import BOTONES, Jugador, PadFalso

X = vg.XUSB_BUTTON
D4 = vg.DS4_BUTTONS
DIR = vg.DS4_DPAD_DIRECTIONS


def jugador(tipo="xbox"):
    return Jugador(1, tipo, fabrica=PadFalso)


def test_xbox_botones_gatillos_y_sticks():
    j = jugador()
    j.aplicar("b A 1")
    j.aplicar("b UP 1")
    j.aplicar("t R 255")
    j.aplicar("s L 1000 -500")
    p = j.pad
    assert p.botones == {X.XUSB_GAMEPAD_A, X.XUSB_GAMEPAD_DPAD_UP}
    assert p.gatillos == {"L": 0, "R": 255}
    assert p.sticks["L"] == (1.0, -0.5)
    j.aplicar("b A 0")
    assert X.XUSB_GAMEPAD_A not in p.botones


def test_todos_los_nombres_de_botones_xbox():
    j = jugador()
    for nombre, valor in BOTONES.items():
        j.aplicar(f"b {nombre} 1")
        assert valor in j.pad.botones, nombre


def test_valores_fuera_de_rango_se_limitan():
    j = jugador()
    j.aplicar("t L 999")
    j.aplicar("s R 5000 -5000")
    assert j.pad.gatillos["L"] == 255
    assert j.pad.sticks["R"] == (1.0, -1.0)


def test_mensajes_raros_no_rompen_nada():
    j = jugador()
    antes = j.pad.actualizaciones
    for m in ["", "b", "b NOEXISTE 1", "z 1 2", "s L 1", "g 1 2 3 4 5 6"]:  # g solo vale en DualShock 4
        j.aplicar(m)
    assert j.pad.botones == set() and j.pad.actualizaciones == antes


def test_soltar_todo():
    j = jugador()
    j.aplicar("b A 1")
    j.aplicar("t L 100")
    j.aplicar("r")
    assert j.pad.botones == set() and j.pad.gatillos == {"L": 0, "R": 0}


def test_ds4_traduce_los_botones():
    j = jugador("ds4")
    for xbox, ds4 in [("A", D4.DS4_BUTTON_CROSS), ("B", D4.DS4_BUTTON_CIRCLE), ("X", D4.DS4_BUTTON_SQUARE),
                      ("Y", D4.DS4_BUTTON_TRIANGLE), ("LB", D4.DS4_BUTTON_SHOULDER_LEFT),
                      ("START", D4.DS4_BUTTON_OPTIONS), ("BACK", D4.DS4_BUTTON_SHARE)]:
        j.aplicar(f"b {xbox} 1")
        assert ds4 in j.pad.botones, xbox
    j.aplicar("b GUIDE 1")
    j.aplicar("b TOUCH 1")
    assert j.pad.especiales == {vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS,
                                vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD}


def test_ds4_cruceta_de_8_direcciones():
    j = jugador("ds4")
    j.aplicar("b UP 1")
    assert j.pad.cruceta == DIR.DS4_BUTTON_DPAD_NORTH
    j.aplicar("b RIGHT 1")
    assert j.pad.cruceta == DIR.DS4_BUTTON_DPAD_NORTHEAST
    j.aplicar("b UP 0")
    assert j.pad.cruceta == DIR.DS4_BUTTON_DPAD_EAST
    j.aplicar("b RIGHT 0")
    assert j.pad.cruceta == DIR.DS4_BUTTON_DPAD_NONE


def test_ds4_gatillo_con_su_boton_y_eje_y_invertido():
    j = jugador("ds4")
    j.aplicar("t L 200")
    assert j.pad.gatillos["L"] == 200 and D4.DS4_BUTTON_TRIGGER_LEFT in j.pad.botones
    j.aplicar("t L 0")
    assert D4.DS4_BUTTON_TRIGGER_LEFT not in j.pad.botones
    j.aplicar("s L 0 1000")  # arriba en el celular = abajo en el eje del DualShock 4
    assert j.pad.sticks["L"] == (0.0, -1.0)


def test_ds4_giroscopio():
    j = jugador("ds4")
    j.aplicar("g 160 -320 99999 0 8192 0")
    assert j.pad.giro == (160, -320, 32767) and j.pad.acel == (0, 8192, 0)


def test_cambiar_de_xbox_a_ds4_y_vibracion():
    vibraciones = []
    j = Jugador(2, "xbox", al_vibrar=lambda jug, g, c: vibraciones.append((jug.numero, g, c)), fabrica=PadFalso)
    j.cambiar_tipo("ds4")
    assert j.tipo == "ds4" and j.pad.tipo == "ds4"
    j.pad.callback(None, None, 200, 50, None, None)  # el juego hace vibrar el control
    assert vibraciones == [(2, 200, 50)]
    j.cambiar_tipo("otra-cosa")
    assert j.tipo == "ds4"
