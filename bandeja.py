"""Ícono de Control Celular al lado del reloj de Windows (área de notificación).

Menú: mostrar el QR para conectar, mostrar u ocultar la ventana, iniciar con Windows y salir.
Al pasar el mouse muestra cuántos celulares hay conectados.
"""

import ctypes
import sys
import threading
import webbrowser
import winreg
from pathlib import Path

import pystray
from PIL import Image

import rutas

CLAVE_INICIO = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOMBRE_INICIO = "ControlCelular"
_k32 = ctypes.windll.kernel32
_u32 = ctypes.windll.user32


# ---------- Ventana de la consola ----------

def _ventana():
    return _k32.GetConsoleWindow()


def ventana_visible() -> bool:
    h = _ventana()
    return bool(h) and bool(_u32.IsWindowVisible(h))


def mostrar_ventana(si: bool) -> None:
    h = _ventana()
    if h:
        _u32.ShowWindow(h, 5 if si else 0)  # SW_SHOW / SW_HIDE
        if si:
            _u32.SetForegroundWindow(h)


# ---------- Iniciar con Windows ----------

def _comando_inicio() -> str:
    if rutas.EMPAQUETADO:
        return f'"{sys.executable}" --minimizado'
    bat = Path(__file__).resolve().parent / "iniciar.bat"
    return f'"{bat}" --minimizado'


def inicio_activado() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_INICIO) as k:
            winreg.QueryValueEx(k, NOMBRE_INICIO)
            return True
    except OSError:
        return False


def cambiar_inicio(activar: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_INICIO, 0, winreg.KEY_SET_VALUE) as k:
        if activar:
            winreg.SetValueEx(k, NOMBRE_INICIO, 0, winreg.REG_SZ, _comando_inicio())
        else:
            try:
                winreg.DeleteValue(k, NOMBRE_INICIO)
            except OSError:
                pass


# ---------- Ícono ----------

def _texto(conectados: list[int]) -> str:
    if not conectados:
        return "Control Celular: esperando un celular"
    if len(conectados) == 1:
        return f"Control Celular: jugador {conectados[0]} conectado"
    return "Control Celular: jugadores " + ", ".join(map(str, conectados)) + " conectados"


def iniciar(url_qr: str, al_salir, minimizado: bool):
    """Pone el ícono (en su propio hilo) y devuelve una función para avisarle los jugadores conectados."""
    imagen = Image.open(rutas.RECURSOS / "web" / "icono-192.png")

    menu = pystray.Menu(
        pystray.MenuItem("Mostrar QR para conectar", lambda: webbrowser.open(url_qr), default=True),
        pystray.MenuItem("Mostrar la ventana", lambda: mostrar_ventana(not ventana_visible()),
                         checked=lambda _: ventana_visible()),
        pystray.MenuItem("Iniciar con Windows", lambda: cambiar_inicio(not inicio_activado()),
                         checked=lambda _: inicio_activado()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Salir", lambda icono: (icono.stop(), al_salir())),
    )
    icono = pystray.Icon("ControlCelular", imagen, _texto([]), menu)
    threading.Thread(target=icono.run, name="bandeja", daemon=True).start()
    if minimizado:
        mostrar_ventana(False)

    def avisar(conectados: list[int]) -> None:
        icono.title = _texto(conectados)
    return avisar
