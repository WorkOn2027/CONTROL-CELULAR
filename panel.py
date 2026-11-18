"""La ventana de Control Celular en la PC (el «panel»): QR, jugadores, celulares emparejados y opciones.

Es una página (web/panel.html) que se abre en una ventana propia con Edge en modo app (viene con Windows 10 y 11;
si no está, Chrome; si tampoco, el navegador). Sin librerías nuevas. Cerrar la ventana no apaga el programa: sigue
en el ícono al lado del reloj.

Seguridad: la página y sus datos se sirven solo a esta misma PC (127.0.0.1) y los datos y las acciones piden una
clave al azar que cambia cada vez que arranca el programa (así ninguna página web puede usarlos). La clave se guarda
en la carpeta de datos para que, si se abre el programa otra vez, traiga esta ventana en vez de avisar «ya está
abierto».
"""

import collections
import ctypes
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from ctypes import wintypes
from pathlib import Path

import rutas

TITULO = "Control Celular"
ARCHIVO_CLAVE = rutas.DATOS / "panel.clave"
CARPETA_NAVEGADOR = rutas.DATOS / "ventana"  # perfil aparte del navegador, solo para esta ventana
clave = secrets.token_urlsafe(18)
actividad: collections.deque = collections.deque(maxlen=80)  # lo que el programa fue avisando


# ---------- Actividad (lo que antes solo se veía en la consola) ----------

def _anotar(linea: str) -> None:
    t = linea.strip()
    if not t or t.startswith("===") or any(c in t for c in "█▀▄"):  # vacías, título y el QR de texto
        return
    actividad.append({"hora": time.strftime("%H:%M"), "texto": t})


class _Copia:
    """Sigue escribiendo en la consola y además anota cada línea para la ventana."""

    def __init__(self, original):
        self._o, self._resto = original, ""

    def write(self, s):
        try:
            self._o.write(s)
        except Exception:
            pass
        self._resto += s
        while "\n" in self._resto:
            linea, self._resto = self._resto.split("\n", 1)
            _anotar(linea)
        return len(s)

    def flush(self):
        try:
            self._o.flush()
        except Exception:
            pass

    def __getattr__(self, nombre):
        return getattr(self._o, nombre)


def capturar_actividad() -> None:
    if not isinstance(sys.stdout, _Copia):
        sys.stdout = _Copia(sys.stdout)


# ---------- Clave ----------

def guardar_clave(puerto: int) -> None:
    try:
        ARCHIVO_CLAVE.write_text(json.dumps({"puerto": puerto, "clave": clave}), "utf-8")
    except OSError:
        pass


def url(puerto: int, k: str | None = None) -> str:
    return f"http://127.0.0.1:{puerto}/panel?k={k or clave}"


# ---------- Ventana ----------

def debe_abrirse() -> bool:
    if sys.platform != "win32" or os.environ.get("CONTROL_SIN_PANEL") == "1" or "--minimizado" in sys.argv:
        return False
    import dialogos
    return dialogos.interactivo()  # pruebas o salida a un archivo: no


def _navegador() -> str | None:
    import winreg
    for exe in ("msedge.exe", "chrome.exe"):
        for raiz in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(raiz, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{exe}") as k:
                    ruta = winreg.QueryValue(k, None)
                if ruta and Path(ruta.strip('"')).is_file():
                    return ruta.strip('"')
            except OSError:
                pass
    for ruta in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        if Path(ruta).is_file():
            return ruta
    return None


def _ventanas() -> list:
    """Las ventanas abiertas del panel (título «Control Celular», ventana de Edge/Chrome)."""
    u = ctypes.windll.user32
    encontradas = []
    PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def ver(h, _):
        titulo = ctypes.create_unicode_buffer(256)
        clase = ctypes.create_unicode_buffer(256)
        u.GetWindowTextW(h, titulo, 256)
        u.GetClassNameW(h, clase, 256)
        if titulo.value == TITULO and clase.value.startswith("Chrome_WidgetWin") and u.IsWindowVisible(h):
            encontradas.append(h)
        return True

    u.EnumWindows(PROC(ver), 0)
    return encontradas


def abrir(puerto: int, k: str | None = None) -> bool:
    """Trae la ventana si ya está abierta; si no, la abre. Devuelve si pudo."""
    try:
        abiertas = _ventanas()
        if abiertas:
            u = ctypes.windll.user32
            u.ShowWindow(abiertas[0], 9)  # SW_RESTORE
            u.SetForegroundWindow(abiertas[0])
            return True
        nav = _navegador()
        if nav:
            subprocess.Popen([nav, f"--app={url(puerto, k)}", f"--user-data-dir={CARPETA_NAVEGADOR}",
                              "--window-size=1040,720", "--no-first-run", "--no-default-browser-check",
                              "--disable-sync", "--disable-features=Translate,msEdgeSidebarV2,msHubApps"],
                             creationflags=0x08000000)  # CREATE_NO_WINDOW
            return True
        return webbrowser.open(url(puerto, k))
    except Exception:
        return False


def cerrar() -> None:
    """Cierra la ventana (al salir del programa)."""
    try:
        for h in _ventanas():
            ctypes.windll.user32.PostMessageW(h, 0x0010, 0, 0)  # WM_CLOSE
    except Exception:
        pass


def abrir_el_que_ya_esta(puerto: int) -> bool:
    """Si Control Celular ya está abierto, trae su ventana. Devuelve True si lo hizo (y no hay que arrancar otro)."""
    try:
        with socket.create_connection(("127.0.0.1", puerto), timeout=.3):
            pass
        datos = json.loads(ARCHIVO_CLAVE.read_text("utf-8"))
        if datos.get("puerto") != puerto:
            return False
        with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/panel/estado?k={datos['clave']}", timeout=2) as r:
            json.loads(r.read())
        return abrir(puerto, datos["clave"])
    except Exception:
        return False
