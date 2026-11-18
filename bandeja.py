"""Ícono de Control Celular al lado del reloj de Windows (área de notificación).

Un toque abre la ventana de Control Celular (panel.py). Menú: abrir la ventana, iniciar con Windows,
celulares emparejados, versión y desinstalar, y salir.
Al pasar el mouse muestra cuántos celulares hay conectados.
"""

import ctypes
import json
import shutil
import sys
import threading
import webbrowser
import winreg
from pathlib import Path

import pystray
from PIL import Image

import red
import rutas
import version
from idioma import T

CONFIG = rutas.DATOS / "config.json"
VERSION_NUEVA = {"v": None}  # la última versión publicada, si es más nueva (la muestra también la ventana)


def leer_config() -> dict:
    try:
        return json.loads(CONFIG.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def guardar_config(clave: str, valor) -> None:
    c = leer_config()
    c[clave] = valor
    try:
        CONFIG.write_text(json.dumps(c), "utf-8")
    except OSError:
        pass


def buscar_versiones_activado() -> bool:
    return leer_config().get("buscarVersiones", True)

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
        return T("Control Celular: esperando un celular", "Control Celular: waiting for a phone")
    if len(conectados) == 1:
        return T(f"Control Celular: jugador {conectados[0]} conectado", f"Control Celular: player {conectados[0]} connected")
    return T("Control Celular: jugadores ", "Control Celular: players ") + ", ".join(map(str, conectados)) + T(" conectados", " connected")


def confirmar(texto: str) -> bool:
    """Cartel de Windows con Sí / No."""
    MB_YESNO, MB_ICONQUESTION, MB_TOPMOST, IDYES = 0x4, 0x20, 0x40000, 6
    return _u32.MessageBoxW(None, texto, "Control Celular", MB_YESNO | MB_ICONQUESTION | MB_TOPMOST) == IDYES


def avisar_cartel(texto: str) -> None:
    MB_OK, MB_ICONINFORMATION, MB_TOPMOST = 0x0, 0x40, 0x40000
    _u32.MessageBoxW(None, texto, "Control Celular", MB_OK | MB_ICONINFORMATION | MB_TOPMOST)


# ---------- Desinstalar ----------

def desinstalar(al_salir) -> None:
    """Deja la PC como estaba: saca la regla del firewall, el arranque con Windows y (en el .exe) los datos."""
    datos = (T("tus datos (certificado, celulares emparejados y ajustes guardados)",
                "your data (certificate, paired phones and saved settings)") if rutas.EMPAQUETADO else
             T("nada más: como lo usás con Python, tus datos quedan en la carpeta del proyecto",
               "nothing else: since you run it with Python, your data stays in the project folder"))
    if not confirmar(T("¿Desinstalar Control Celular de esta PC?\n\nSe va a sacar:\n"
                       "  • la regla del firewall (Windows pide permiso)\n"
                       "  • el arranque con Windows\n"
                       f"  • {datos}\n\nDespués el programa se cierra.",
                       "Uninstall Control Celular from this PC?\n\nThis removes:\n"
                       "  • the firewall rule (Windows asks for permission)\n"
                       "  • starting with Windows\n"
                       f"  • {datos}\n\nThen the program closes.")):
        return
    hechos, fallos = [], []
    if red.regla_existe():
        (hechos if red.quitar_regla() else fallos).append(T("la regla del firewall", "the firewall rule"))
    cambiar_inicio(False)
    hechos.append(T("el arranque con Windows", "starting with Windows"))
    if rutas.EMPAQUETADO:
        try:
            shutil.rmtree(rutas.DATOS)
            hechos.append(T("tus datos", "your data"))
        except OSError:
            fallos.append(T(f"la carpeta {rutas.DATOS}", f"the folder {rutas.DATOS}"))
    texto = T("Listo. Se sacó: ", "Done. Removed: ") + ", ".join(hechos) + "."
    if fallos:
        texto += T("\nNo se pudo sacar: ", "\nCouldn't remove: ") + ", ".join(fallos) + "."
    texto += T("\n\nPara terminar, si querés:\n"
               "  • Borrá ControlCelular.exe (o la carpeta del proyecto).\n"
               "  • ViGEmBus se desinstala desde Configuración > Aplicaciones (\"Nefarius Virtual Gamepad "
               "Emulation Bus\").\n"
               "  • En el celular: Ajustes > Seguridad > Credenciales de usuario > borrá \"CONTROL CELULAR\", "
               "y desinstalá la app.",
               "\n\nTo finish, if you want:\n"
               "  • Delete ControlCelular.exe (or the project folder).\n"
               "  • Uninstall ViGEmBus from Settings > Apps (\"Nefarius Virtual Gamepad Emulation Bus\").\n"
               "  • On your phone: remove the \"CONTROL CELULAR\" certificate (Android: Settings > Security > User "
               "credentials; iPhone: Settings > General > VPN & Device Management) and uninstall the app.")
    avisar_cartel(texto)
    al_salir()


def _hace(visto: int) -> str:
    import time
    if not visto:
        return T("sin usar todavía", "not used yet")
    s = time.time() - visto
    if s < 3600:
        return T("usado hace un rato", "used a moment ago")
    if s < 86400:
        return T(f"usado hace {int(s // 3600)} h", f"used {int(s // 3600)} h ago")
    return T(f"usado hace {int(s // 86400)} días", f"used {int(s // 86400)} days ago")


def iniciar(url_qr: str, al_salir, minimizado: bool, listar_celulares, olvidar, abrir_panel=None):
    """Pone el ícono (en su propio hilo) y devuelve una función para avisarle los jugadores conectados."""
    imagen = Image.open(rutas.RECURSOS / "web" / "icono-bandeja.png")

    def olvidar_uno(c):
        def accion():
            if confirmar(T(f"¿Olvidar «{c['nombre']}»?\n\nVa a perder el permiso para conectarse y sus ajustes "
                           "guardados en la PC. Para volver a usarlo hay que emparejarlo de nuevo con el QR.",
                           f"Forget “{c['nombre']}”?\n\nIt will lose permission to connect and its settings saved "
                           "on the PC. To use it again you'll need to pair it again with the QR code.")):
                olvidar({c["id"]})
        return accion

    def olvidar_todos():
        if confirmar(T("¿Olvidar TODOS los celulares emparejados?\n\nTodos pierden el permiso para conectarse y sus "
                       "ajustes guardados en la PC. Para volver a usarlos hay que emparejarlos de nuevo con el QR.",
                       "Forget ALL paired phones?\n\nThey all lose permission to connect and their settings saved "
                       "on the PC. To use them again you'll need to pair them again with the QR code.")):
            olvidar(None)

    def items_celulares():
        lista = listar_celulares()
        if not lista:
            yield pystray.MenuItem(T("No hay celulares emparejados", "No paired phones"), None, enabled=False)
            return
        for c in lista:
            estado = T("conectado ahora", "connected now") if c["conectado"] else _hace(c["visto"])
            yield pystray.MenuItem(T(f"Olvidar «{c['nombre']}» ({estado})", f"Forget “{c['nombre']}” ({estado})"), olvidar_uno(c))
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem(T("Olvidar todos", "Forget all"), olvidar_todos)

    nueva = VERSION_NUEVA

    def items_version():
        yield pystray.MenuItem(f"Control Celular {version.VERSION}", None, enabled=False)
        if nueva["v"]:
            yield pystray.MenuItem(T(f"Descargar la versión {nueva['v']}", f"Download version {nueva['v']}"),
                                   lambda: webbrowser.open(version.PAGINA_RELEASES))
        yield pystray.MenuItem(T("Buscar versiones nuevas", "Check for new versions"),
                               lambda: guardar_config("buscarVersiones", not buscar_versiones_activado()),
                               checked=lambda _: buscar_versiones_activado())
        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem(T("Desinstalar…", "Uninstall…"), lambda: desinstalar(al_salir))

    abrir = abrir_panel or (lambda: webbrowser.open(url_qr))
    menu = pystray.Menu(
        pystray.MenuItem(T("Abrir Control Celular", "Open Control Celular"), lambda: abrir(), default=True),
        pystray.MenuItem(T("Iniciar con Windows", "Start with Windows"), lambda: cambiar_inicio(not inicio_activado()),
                         checked=lambda _: inicio_activado()),
        pystray.MenuItem(T("Celulares emparejados", "Paired phones"), pystray.Menu(items_celulares)),
        pystray.MenuItem(T("Versión y desinstalar", "Version and uninstall"), pystray.Menu(items_version)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(T("Salir", "Exit"), lambda icono: (icono.stop(), al_salir())),
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

    def buscar_version():
        if not buscar_versiones_activado():
            return
        v = version.version_nueva()
        if v:
            nueva["v"] = v
            print(T(f"  Hay una versión nueva de Control Celular: {v}. Bajala desde {version.PAGINA_RELEASES}", f"  A new version of Control Celular is available: {v}. Download it from {version.PAGINA_RELEASES}"))
            try:
                icono.update_menu()
                icono.notify(T(f"Hay una versión nueva: {v}. Abrí el ícono → Versión y desinstalar.", f"New version available: {v}. Open the icon → Version and uninstall."), "Control Celular")
            except Exception:
                pass
    threading.Thread(target=buscar_version, name="version", daemon=True).start()
    return avisar
