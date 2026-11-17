"""Animación de arranque en la PC: el control de neón se enciende flotando en el centro de la pantalla.

Sale solo cuando el programa se abre de cero (no al arrancar oculto con Windows, ni si ya estaba abierto, ni al
volver de minimizado). Dura ~2,5 s y corre en su propio hilo mientras el programa arranca: no agrega espera.
Mientras tanto la ventana del programa queda oculta; al terminar se muestra (con el QR).

Ventana "layered" de Windows (transparencia por píxel, no se puede tocar ni toma el foco), con ctypes: sin
librerías nuevas. Las capas (web/animacion-cuerpo.png y web/animacion-neon.png) las genera herramientas/iconos.py.
CONTROL_SIN_ANIMACION=1 la apaga.
"""

import colorsys
import ctypes
import math
import os
import socket
import sys
import threading
import time
from ctypes import wintypes

DURACION = 2.6  # segundos
FPS = 40


def _suave(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def brillo(t: float) -> float:
    """Cuánto está encendido el neón (0 a 1): parpadea como un tubo que arranca y después se afirma."""
    tramos = ((.30, 0), (.38, .7), (.48, .08), (.55, .9), (.62, .25))
    for fin, valor in tramos:
        if t < fin:
            return valor
    if t < 1.0:
        return .6 + .4 * _suave((t - .62) / .38)
    return 1.0


def giro(t: float) -> float:
    """Vuelta de colores (0 a 1): el neón pasa por el arcoíris y vuelve al celeste → verde."""
    return _suave((t - 1.0) / 1.0)


def opacidad(t: float) -> int:
    """Opacidad de toda la ventana: al final se desvanece."""
    return round(255 * (1 - _suave((t - 2.2) / (DURACION - 2.2))))


class Cuadros:
    """Arma cada cuadro de la animación con Pillow, a partir de las dos capas."""

    def __init__(self, web):
        from PIL import Image, ImageFilter
        self.Image = Image
        self.cuerpo = Image.open(web / "animacion-cuerpo.png").convert("RGBA")
        self.neon = Image.open(web / "animacion-neon.png").convert("L")
        self.tam = self.cuerpo.size
        ancho = self.tam[0]
        self.halo_ancho = self.neon.filter(ImageFilter.GaussianBlur(ancho * .022))
        self.halo_corto = self.neon.filter(ImageFilter.GaussianBlur(ancho * .007))
        self.alfa_cuerpo = self.cuerpo.getchannel("A")

    def _degradado(self, vuelta: float):
        """Celeste (izquierda) → verde (derecha), con el tono corrido `vuelta` (0 a 1 = una vuelta entera)."""
        w, h = self.tam
        tira = self.Image.new("RGB", (w, 1))
        izq, der = 203 / 360, 142 / 360
        abanico = 1 + 3 * math.sin(math.pi * vuelta)  # en medio de la vuelta, el arcoíris entero a lo ancho
        for x in range(w):
            tx = min(max((x / w - .15) / .7, 0), 1)
            r, g, b = colorsys.hsv_to_rgb((izq + (der - izq) * tx * abanico + vuelta) % 1, .78, 1)
            tira.putpixel((x, 0), (round(r * 255), round(g * 255), round(b * 255)))
        return tira.resize((w, h)).convert("RGBA")

    @staticmethod
    def _escala(mascara, k: float):
        return mascara.point([min(255, int(v * k)) for v in range(256)])

    def cuadro(self, t: float):
        a = _suave(t / .4)  # el cuerpo aparece primero, oscuro
        b = brillo(t)
        halo = b * (.35 + .65 * _suave((t - .6) / .6))  # el brillo alrededor crece después del parpadeo
        img = self.Image.new("RGBA", self.tam, (0, 0, 0, 0))
        cuerpo = self.cuerpo.copy()
        cuerpo.putalpha(self._escala(self.alfa_cuerpo, a))
        img.alpha_composite(cuerpo)
        color = self._degradado(giro(t))
        for mascara, fuerza in ((self.halo_ancho, .9 * halo), (self.halo_corto, 1.3 * halo),
                                (self.neon, max(b, .12 * a))):  # apagado, el tubo se ve apenas
            capa = color.copy()
            capa.putalpha(self._escala(mascara, fuerza))
            img.alpha_composite(capa)
        return img


def debe_mostrarse() -> bool:
    if sys.platform != "win32" or os.environ.get("CONTROL_SIN_ANIMACION") == "1":
        return False
    if any(a in sys.argv for a in ("--minimizado", "--tras-instalar")):
        return False
    try:
        if not sys.stdout.isatty():  # sin ventana (pruebas, salida a un archivo)
            return False
    except (AttributeError, ValueError):
        return False
    try:  # si ya está abierto, no: va a avisar «ya está abierto»
        puerto = int(os.environ.get("CONTROL_PUERTO", "8765"))
        with socket.create_connection(("127.0.0.1", puerto), timeout=.15):
            return False
    except (OSError, ValueError):
        return True


# ---------------------------------------------------------------- Windows

class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", _BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


class _BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte),
                ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_ubyte)]


_WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class _WNDCLASSEXW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("style", wintypes.UINT), ("lpfnWndProc", _WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON), ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR), ("hIconSm", wintypes.HICON)]


def _win32():
    u = ctypes.WinDLL("user32", use_last_error=True)
    g = ctypes.WinDLL("gdi32")
    k = ctypes.WinDLL("kernel32")
    V, H = ctypes.c_void_p, wintypes.HWND
    u.DefWindowProcW.argtypes = [H, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    u.DefWindowProcW.restype = ctypes.c_ssize_t
    u.RegisterClassExW.argtypes = [ctypes.POINTER(_WNDCLASSEXW)]
    u.RegisterClassExW.restype = wintypes.ATOM
    u.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
    u.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int,
                                  ctypes.c_int, ctypes.c_int, ctypes.c_int, H, wintypes.HMENU, wintypes.HINSTANCE, V]
    u.CreateWindowExW.restype = H
    u.DestroyWindow.argtypes = [H]
    u.ShowWindow.argtypes = [H, ctypes.c_int]
    u.SetForegroundWindow.argtypes = [H]
    u.GetDC.argtypes = [H]
    u.GetDC.restype = wintypes.HDC
    u.ReleaseDC.argtypes = [H, wintypes.HDC]
    u.UpdateLayeredWindow.argtypes = [H, wintypes.HDC, ctypes.POINTER(wintypes.POINT), ctypes.POINTER(wintypes.SIZE),
                                      wintypes.HDC, ctypes.POINTER(wintypes.POINT), wintypes.DWORD,
                                      ctypes.POINTER(_BLENDFUNCTION), wintypes.DWORD]
    u.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), H, wintypes.UINT, wintypes.UINT, wintypes.UINT]
    u.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    u.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    g.CreateCompatibleDC.argtypes = [wintypes.HDC]
    g.CreateCompatibleDC.restype = wintypes.HDC
    g.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.POINTER(_BITMAPINFO), wintypes.UINT, ctypes.POINTER(V),
                                   wintypes.HANDLE, wintypes.DWORD]
    g.CreateDIBSection.restype = wintypes.HBITMAP
    g.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    g.SelectObject.restype = wintypes.HGDIOBJ
    g.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    g.DeleteDC.argtypes = [wintypes.HDC]
    k.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    k.GetModuleHandleW.restype = wintypes.HMODULE
    k.GetConsoleWindow.restype = H
    return u, g, k


def _bgra_premultiplicado(img) -> bytes:
    from PIL import Image
    r, g, b, a = img.convert("RGBa").split()  # "RGBa" = colores ya multiplicados por la transparencia
    return Image.merge("RGBA", (b, g, r, a)).tobytes()


def reproducir(cuadros: Cuadros) -> None:
    """Muestra la animación (bloquea ~DURACION segundos)."""
    u, g, k = _win32()
    w, h = cuadros.tam
    instancia = k.GetModuleHandleW(None)
    proc = _WNDPROC(lambda hw, m, wp, lp: u.DefWindowProcW(hw, m, wp, lp))
    clase = "ControlCelularAnimacion"
    wc = _WNDCLASSEXW(cbSize=ctypes.sizeof(_WNDCLASSEXW), lpfnWndProc=proc, hInstance=instancia, lpszClassName=clase)
    u.RegisterClassExW(ctypes.byref(wc))
    # Capas, siempre arriba, sin botón en la barra, deja pasar los clics y no roba el foco
    estilo_ex = 0x00080000 | 0x00000008 | 0x00000080 | 0x00000020 | 0x08000000
    x = (u.GetSystemMetrics(0) - w) // 2
    y = (u.GetSystemMetrics(1) - h) // 2
    hwnd = u.CreateWindowExW(estilo_ex, clase, "Control Celular", 0x80000000, x, y, w, h, None, None, instancia, None)
    if not hwnd:
        u.UnregisterClassW(clase, instancia)
        return
    pantalla = u.GetDC(None)
    memoria = g.CreateCompatibleDC(pantalla)
    info = _BITMAPINFO()
    info.bmiHeader = _BITMAPINFOHEADER(biSize=ctypes.sizeof(_BITMAPINFOHEADER), biWidth=w, biHeight=-h,  # de arriba abajo
                                       biPlanes=1, biBitCount=32, biCompression=0)
    bits = ctypes.c_void_p()
    mapa = g.CreateDIBSection(memoria, ctypes.byref(info), 0, ctypes.byref(bits), None, 0)
    anterior = g.SelectObject(memoria, mapa)
    origen, tam, pos = wintypes.POINT(0, 0), wintypes.SIZE(w, h), wintypes.POINT(x, y)
    msg = wintypes.MSG()
    try:
        inicio = time.perf_counter()
        mostrada = False
        while True:
            t = time.perf_counter() - inicio
            if t >= DURACION:
                break
            datos = _bgra_premultiplicado(cuadros.cuadro(t))
            ctypes.memmove(bits, datos, len(datos))
            mezcla = _BLENDFUNCTION(0, 0, opacidad(t), 1)  # AC_SRC_OVER, AC_SRC_ALPHA
            u.UpdateLayeredWindow(hwnd, pantalla, ctypes.byref(pos), ctypes.byref(tam), memoria,
                                  ctypes.byref(origen), 0, ctypes.byref(mezcla), 2)  # ULW_ALPHA
            if not mostrada:
                u.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
                mostrada = True
            while u.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                u.TranslateMessage(ctypes.byref(msg))
                u.DispatchMessageW(ctypes.byref(msg))
            espera = 1 / FPS - (time.perf_counter() - inicio - t)
            if espera > 0:
                time.sleep(espera)
    finally:
        u.DestroyWindow(hwnd)
        g.SelectObject(memoria, anterior)
        g.DeleteObject(mapa)
        g.DeleteDC(memoria)
        u.ReleaseDC(None, pantalla)
        u.UnregisterClassW(clase, instancia)


def _mostrar_consola(si: bool) -> None:
    try:
        u, _, k = _win32()
        h = k.GetConsoleWindow()
        if h:
            u.ShowWindow(h, 5 if si else 0)  # SW_SHOW / SW_HIDE
            if si:
                u.SetForegroundWindow(h)
    except Exception:
        pass


def _correr() -> None:
    _mostrar_consola(False)
    try:
        import rutas
        reproducir(Cuadros(rutas.RECURSOS / "web"))
    except Exception:
        pass  # la animación es un adorno: si falla, el programa sigue igual
    finally:
        _mostrar_consola(True)


def empezar() -> None:
    """Arranca la animación en otro hilo, si corresponde. No espera."""
    if debe_mostrarse():
        threading.Thread(target=_correr, name="animacion", daemon=True).start()
