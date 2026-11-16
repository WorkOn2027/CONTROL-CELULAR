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


def confirmar(texto: str) -> bool:
    """Cartel de Windows con Sí / No."""
    MB_YESNO, MB_ICONQUESTION, MB_TOPMOST, IDYES = 0x4, 0x20, 0x40000, 6
    return _u32.MessageBoxW(None, texto, "Control Celular", MB_YESNO | MB_ICONQUESTION | MB_TOPMOST) == IDYES


def _hace(visto: int) -> str:
    import time
    if not visto:
        return "sin usar todavía"
    s = time.time() - visto
    if s < 3600:
        return "usado hace un rato"
    if s < 86400:
        return f"usado hace {int(s // 3600)} h"
    return f"usado hace {int(s // 86400)} días"


def iniciar(url_qr: str, al_salir, minimizado: bool, listar_celulares, olvidar):
    """Pone el ícono (en su propio hilo) y devuelve una función para avisarle los jugadores conectados."""
    imagen = Image.open(rutas.RECURSOS / "web" / "icono-192.png")

    def olvidar_uno(c):
        def accion():
            if confirmar(f"¿Olvidar «{c['nombre']}»?\n\nVa a perder el permiso para conectarse y sus ajustes "
                         "guardados en la PC. Para volver a usarlo hay que emparejarlo de nuevo con el QR."):
                olvidar({c["id"]})
        return accion

    def olvidar_todos():
        if confirmar("¿Olvidar TODOS los celulares emparejados?\n\nTodos pierden el permiso para conectarse y sus "
                     "ajustes guardados en la PC. Para volver a usarlos hay que emparejarlos de nuevo con el QR."):
            olvidar(None)

    def items_celulares():
        lista = listar_celulares()
        if not lista:
            yield pystray.MenuItem("No hay celulares emparejados", None, enabled=False)
            return
        for c in lista:
            estado = "conectado ahora" if c["conectado"] else _hace(c["visto"])
            yield pystray.MenuItem(f"Olvidar «{c['nombre']}» ({estado})", olvidar_uno(c))
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem("Olvidar todos", olvidar_todos)

    menu = pystray.Menu(
        pystray.MenuItem("Mostrar QR para conectar", lambda: webbrowser.open(url_qr), default=True),
        pystray.MenuItem("Mostrar la ventana", lambda: mostrar_ventana(not ventana_visible()),
                         checked=lambda _: ventana_visible()),
        pystray.MenuItem("Iniciar con Windows", lambda: cambiar_inicio(not inicio_activado()),
                         checked=lambda _: inicio_activado()),
        pystray.MenuItem("Celulares emparejados", pystray.Menu(items_celulares)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Salir", lambda icono: (icono.stop(), al_salir())),
    )
    icono = pystray.Icon("ControlCelular", imagen, _texto([]), menu)
    threading.Thread(target=icono.run, name="bandeja", daemon=True).start()
    if minimizado:
        mostrar_ventana(False)

    def avisar(conectados: list[int]) -> None:
        icono.title = _texto(conectados)
        try:
            icono.update_menu()  # para que la lista de celulares esté al día
        except Exception:
            pass
    return avisar
