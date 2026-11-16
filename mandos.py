"""Los controles virtuales: un jugador = un celular = un control de Xbox 360 o DualShock 4.

El celular siempre manda los nombres de Xbox (A, B, LB, START...); acá se traducen al control elegido.
Con la variable de entorno CONTROL_MANDO_FALSO=1 se usa un control "de mentira" que solo anota lo que recibe:
sirve para las pruebas automáticas, sin necesitar el driver ViGEmBus.
"""

import os

import vgamepad as vg

B = vg.XUSB_BUTTON
BOTONES = {
    "A": B.XUSB_GAMEPAD_A, "B": B.XUSB_GAMEPAD_B,
    "X": B.XUSB_GAMEPAD_X, "Y": B.XUSB_GAMEPAD_Y,
    "LB": B.XUSB_GAMEPAD_LEFT_SHOULDER, "RB": B.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "BACK": B.XUSB_GAMEPAD_BACK, "START": B.XUSB_GAMEPAD_START,
    "GUIDE": B.XUSB_GAMEPAD_GUIDE,
    "LS": B.XUSB_GAMEPAD_LEFT_THUMB, "RS": B.XUSB_GAMEPAD_RIGHT_THUMB,
    "UP": B.XUSB_GAMEPAD_DPAD_UP, "DOWN": B.XUSB_GAMEPAD_DPAD_DOWN,
    "LEFT": B.XUSB_GAMEPAD_DPAD_LEFT, "RIGHT": B.XUSB_GAMEPAD_DPAD_RIGHT,
}

D4 = vg.DS4_BUTTONS
BOTONES_DS4 = {  # los nombres del celular son los de Xbox; en DualShock 4 se traducen
    "A": D4.DS4_BUTTON_CROSS, "B": D4.DS4_BUTTON_CIRCLE, "X": D4.DS4_BUTTON_SQUARE, "Y": D4.DS4_BUTTON_TRIANGLE,
    "LB": D4.DS4_BUTTON_SHOULDER_LEFT, "RB": D4.DS4_BUTTON_SHOULDER_RIGHT,
    "BACK": D4.DS4_BUTTON_SHARE, "START": D4.DS4_BUTTON_OPTIONS,
    "LS": D4.DS4_BUTTON_THUMB_LEFT, "RS": D4.DS4_BUTTON_THUMB_RIGHT,
}
ESPECIALES_DS4 = {"GUIDE": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS,
                  "TOUCH": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD}
_DIR = vg.DS4_DPAD_DIRECTIONS
CRUCETA_DS4 = {  # (arriba, abajo, izquierda, derecha) -> dirección del DualShock 4
    (1, 0, 0, 0): _DIR.DS4_BUTTON_DPAD_NORTH, (0, 1, 0, 0): _DIR.DS4_BUTTON_DPAD_SOUTH,
    (0, 0, 1, 0): _DIR.DS4_BUTTON_DPAD_WEST, (0, 0, 0, 1): _DIR.DS4_BUTTON_DPAD_EAST,
    (1, 0, 0, 1): _DIR.DS4_BUTTON_DPAD_NORTHEAST, (1, 0, 1, 0): _DIR.DS4_BUTTON_DPAD_NORTHWEST,
    (0, 1, 0, 1): _DIR.DS4_BUTTON_DPAD_SOUTHEAST, (0, 1, 1, 0): _DIR.DS4_BUTTON_DPAD_SOUTHWEST,
}
TIPOS_MANDO = ("xbox", "ds4")


def limitar(v: float) -> float:
    return max(-1.0, min(1.0, v))


class PadFalso:
    """Control de mentira para las pruebas: tiene los mismos métodos que los de vgamepad y anota el estado."""

    def __init__(self, tipo: str):
        self.tipo = tipo
        self.reset()
        self.actualizaciones = 0
        self.callback = None

    def reset(self):
        self.botones, self.especiales = set(), set()
        self.gatillos = {"L": 0, "R": 0}
        self.sticks = {"L": (0.0, 0.0), "R": (0.0, 0.0)}
        self.cruceta = None
        self.giro = self.acel = None

    def update(self): self.actualizaciones += 1
    def press_button(self, b): self.botones.add(b)
    def release_button(self, b): self.botones.discard(b)
    def press_special_button(self, b): self.especiales.add(b)
    def release_special_button(self, b): self.especiales.discard(b)
    def left_trigger(self, v): self.gatillos["L"] = v
    def right_trigger(self, v): self.gatillos["R"] = v
    def left_joystick_float(self, x, y): self.sticks["L"] = (x, y)
    def right_joystick_float(self, x, y): self.sticks["R"] = (x, y)
    def directional_pad(self, d): self.cruceta = d
    def gyroscope(self, x, y, z): self.giro = (x, y, z)
    def accelerometer(self, x, y, z): self.acel = (x, y, z)
    def register_notification(self, callback_function): self.callback = callback_function


def crear_pad(tipo: str):
    if os.environ.get("CONTROL_MANDO_FALSO") == "1":
        return PadFalso(tipo)
    return vg.VDS4Gamepad() if tipo == "ds4" else vg.VX360Gamepad()


class Jugador:
    """Un celular = un control virtual. Puede ser de Xbox 360 o DualShock 4 (lo elige cada celular).

    al_vibrar(jugador, grande, chico): lo llama el driver (desde otro hilo) cuando un juego hace vibrar el control.
    """

    def __init__(self, numero: int, tipo: str = "xbox", al_vibrar=None, fabrica=crear_pad):
        self.numero = numero
        self.ws = None
        self.token = None
        self.pad = None
        self.tipo = None
        self._al_vibrar_cb = al_vibrar
        self._fabrica = fabrica
        self.cambiar_tipo(tipo)

    def cambiar_tipo(self, tipo: str) -> None:
        if tipo not in TIPOS_MANDO or tipo == self.tipo:
            return
        if self.pad is not None:
            self.soltar()
            self.pad = None  # al soltarlo, vgamepad lo desenchufa de Windows
        self.pad = self._fabrica(tipo)
        self.tipo = tipo
        self.cruceta = {"UP": 0, "DOWN": 0, "LEFT": 0, "RIGHT": 0}
        self.pad.reset()
        self.pad.update()  # arrancar con todo en cero (si no, los sticks quedan corridos)
        self.pad.register_notification(callback_function=self._al_vibrar)

    def _al_vibrar(self, client, target, grande, chico, led, user_data):
        if self._al_vibrar_cb is not None:
            self._al_vibrar_cb(self, grande, chico)

    def soltar(self) -> None:
        self.cruceta = {"UP": 0, "DOWN": 0, "LEFT": 0, "RIGHT": 0}
        self.pad.reset()
        self.pad.update()

    def aplicar(self, msg: str) -> None:
        """Aplica un mensaje del celular ("b A 1", "t L 255", "s L 500 -200", "g ...", "r")."""
        p = msg.split()
        if not p:
            return
        pad, ds4, tipo = self.pad, self.tipo == "ds4", p[0]
        if tipo == "b" and len(p) == 3:
            on, b = p[2] == "1", p[1]
            if not ds4:
                if b not in BOTONES:
                    return
                (pad.press_button if on else pad.release_button)(BOTONES[b])
            elif b in self.cruceta:
                self.cruceta[b] = int(on)
                c = self.cruceta
                pad.directional_pad(CRUCETA_DS4.get((c["UP"], c["DOWN"], c["LEFT"], c["RIGHT"]),
                                                    _DIR.DS4_BUTTON_DPAD_NONE))
            elif b in ESPECIALES_DS4:
                (pad.press_special_button if on else pad.release_special_button)(ESPECIALES_DS4[b])
            elif b in BOTONES_DS4:
                (pad.press_button if on else pad.release_button)(BOTONES_DS4[b])
            else:
                return
        elif tipo == "t" and len(p) == 3:
            valor = max(0, min(255, int(p[2])))
            (pad.left_trigger if p[1] == "L" else pad.right_trigger)(valor)
            if ds4:  # el DualShock 4 también tiene un "botón" L2/R2 además del valor analógico
                bit = D4.DS4_BUTTON_TRIGGER_LEFT if p[1] == "L" else D4.DS4_BUTTON_TRIGGER_RIGHT
                (pad.press_button if valor > 0 else pad.release_button)(bit)
        elif tipo == "s" and len(p) == 4:
            x, y = limitar(int(p[2]) / 1000), limitar(int(p[3]) / 1000)
            if ds4:
                y = -y  # en el DualShock 4, el eje Y va al revés (positivo = abajo)
            (pad.left_joystick_float if p[1] == "L" else pad.right_joystick_float)(x, y)
        elif tipo == "g" and len(p) == 7 and ds4:
            # Giroscopio y acelerómetro del celular, ya en unidades del DualShock 4 (los calcula el celular).
            v = [max(-32768, min(32767, int(n))) for n in p[1:]]
            pad.gyroscope(v[0], v[1], v[2])
            pad.accelerometer(v[3], v[4], v[5])
        elif tipo == "r":
            self.soltar()
            return
        else:
            return
        pad.update()
