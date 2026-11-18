"""Animación de arranque en la PC: «tu celular ahora es tu control».

Tres planos en una sola animación, sobre un fondo negro en el centro de la pantalla:
  1. Un celular parado, con la pantalla apagada.
  2. Gira (limpio, sin saltos) hasta quedar acostado.
  3. Se prende la pantalla y aparece el control de neón: el celular ahora es tu control.

Sale solo cuando el programa se abre de cero (no al arrancar oculto con Windows, ni si ya estaba abierto, ni al
volver de minimizado). Dura ~3,4 s y corre en su propio hilo mientras el programa arranca: no agrega espera. Al
terminar, si el programa ya arrancó, se abre su ventana (panel.py).

Ventana "layered" de Windows (transparencia por píxel, no se puede tocar ni toma el foco), con ctypes: sin
librerías nuevas. El celular se dibuja acá; el control sale de web/animacion-cuerpo.png y web/animacion-neon.png
(las genera herramientas/iconos.py). CONTROL_SIN_ANIMACION=1 la apaga.
"""

import ctypes
import os
import socket
import sys
import threading
import time
from ctypes import wintypes

DURACION = 3.4  # segundos
FPS = 45
ANCHO, ALTO = 640, 440  # el fondo negro (a escala 100 %; con la pantalla escalada se dibuja más grande)
listo = threading.Event()      # el programa arrancó y va a abrir su ventana (lo marca server.py)
terminada = threading.Event()  # la animación terminó (o no hubo): ya se puede abrir la ventana
terminada.set()

CELESTE = (40, 175, 255)
VERDE = (60, 240, 125)


def _suave(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _entre(t: float, desde: float, hasta: float) -> float:
    return _suave((t - desde) / (hasta - desde))


def giro(t: float) -> float:
    """Plano 1 → 2: 0 = parado, 1 = acostado."""
    return _entre(t, .55, 1.35)


def pantalla(t: float) -> float:
    """Plano 3: cuánto está prendida la pantalla (0 a 1)."""
    return _entre(t, 1.45, 1.7)


def brillo(t: float) -> float:
    """El neón del control: parpadea como un tubo que arranca y después se afirma."""
    tramos = ((1.72, 0), (1.80, .7), (1.88, .1), (1.95, .9), (2.01, .3))
    for fin, valor in tramos:
        if t < fin:
            return valor
    if t < 2.35:
        return .65 + .35 * _suave((t - 2.01) / .34)
    return 1.0


def opacidad(t: float) -> int:
    """Opacidad de toda la ventana: aparece al principio y se desvanece al final."""
    return round(255 * _entre(t, 0, .3) * (1 - _entre(t, 2.95, DURACION)))


class Cuadros:
    """Arma cada cuadro con Pillow. Lo pesado (dibujar el celular, los brillos) se prepara una sola vez."""

    def __init__(self, web, escala: float = 1.0):
        """`escala`: la de la pantalla (1.25 = 125 %), así se dibuja nítido en vez de estirado."""
        from PIL import Image, ImageChops, ImageDraw, ImageFilter
        self.Image, self.ImageChops = Image, ImageChops
        self.W, self.H = round(ANCHO * escala), round(ALTO * escala)
        self.tam = (self.W, self.H)

        # Fondo negro con las esquinas redondeadas
        self.fondo = Image.new("RGBA", self.tam, (0, 0, 0, 0))
        forma = Image.new("L", (self.W * 3, self.H * 3), 0)
        ImageDraw.Draw(forma).rounded_rectangle([0, 0, self.W * 3 - 1, self.H * 3 - 1], radius=round(84 * escala),
                                               fill=255)
        self.fondo.putalpha(forma.resize(self.tam, Image.LANCZOS))
        negro = Image.new("RGBA", self.tam, (0, 0, 0, 255))
        negro.putalpha(self.fondo.getchannel("A"))
        self.fondo = negro

        # El celular, acostado (cámara a la izquierda), en su tamaño final
        self.cel, self.caja_pantalla, mascara_pantalla = self._celular(round(430 * escala), round(206 * escala))
        cw, ch = self.cel.size
        self.pos_cel = ((self.W - cw) // 2, (self.H - ch) // 2)

        # Lo que se ve en la pantalla prendida: fondo oscuro con un degradado y el control de neón
        x0, y0, x1, y1 = self.caja_pantalla
        sw, sh = x1 - x0, y1 - y0
        fondo_pantalla = Image.new("RGBA", (sw, sh))
        dp = ImageDraw.Draw(fondo_pantalla)
        for y in range(sh):
            k = y / sh
            dp.line([0, y, sw, y], fill=tuple(round(a + (b - a) * k) for a, b in zip((36, 43, 52), (11, 14, 18))) + (255,))
        self.pantalla_fondo = fondo_pantalla
        self.mascara_pantalla = mascara_pantalla  # esquinas redondeadas de la pantalla

        cuerpo = Image.open(web / "animacion-cuerpo.png").convert("RGBA")
        neon = Image.open(web / "animacion-neon.png").convert("L")
        escala = min(sw * 1.02 / cuerpo.width, sh * 1.0 / cuerpo.height)
        tam_control = (round(cuerpo.width * escala), round(cuerpo.height * escala))
        self.control = cuerpo.resize(tam_control, Image.LANCZOS)
        self.control_alfa = self.control.getchannel("A")
        neon = neon.resize(tam_control, Image.LANCZOS)
        self.pos_control = ((sw - tam_control[0]) // 2, (sh - tam_control[1]) // 2 + 2)
        color = self._degradado(tam_control)
        self.neon = [(color, neon, 1.0),
                     (color, neon.filter(ImageFilter.GaussianBlur(tam_control[0] * .02)), 1.6),
                     (color, neon.filter(ImageFilter.GaussianBlur(tam_control[0] * .007)), 1.3)]

        # La luz de la pantalla prendida que se derrama sobre el fondo negro
        luz = Image.new("L", self.tam, 0)
        luz.paste(mascara_pantalla, (self.pos_cel[0] + x0, self.pos_cel[1] + y0))
        self.luz = luz.filter(ImageFilter.GaussianBlur(26 * escala))
        self.luz_color = self._degradado(self.tam, de=.30, a=.70)

    def _degradado(self, tam, de=.15, a=.85):
        """Celeste (izquierda) → verde (derecha)."""
        w, h = tam
        tira = self.Image.new("RGB", (w, 1))
        for x in range(w):
            k = min(max((x / w - de) / (a - de), 0), 1)
            tira.putpixel((x, 0), tuple(round(c1 + (c2 - c1) * k) for c1, c2 in zip(CELESTE, VERDE)))
        return tira.resize((w, h)).convert("RGBA")

    def _celular(self, w, h):
        """Dibuja el celular acostado (más grande y achicado, para que los bordes queden suaves)."""
        from PIL import ImageDraw
        e = 3
        W, H = w * e, h * e
        img = self.Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        radio = round(H * .16)
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=radio, fill=(30, 34, 40, 255))      # cuerpo
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=radio, outline=(88, 97, 110, 255), width=2 * e)  # canto
        d.rounded_rectangle([3 * e, 3 * e, W - 1 - 3 * e, H - 1 - 3 * e], radius=radio - 3 * e,
                            outline=(16, 18, 22, 255), width=2 * e)                            # marco interno
        b = round(H * .06)  # borde alrededor de la pantalla
        caja = [b, b, W - 1 - b, H - 1 - b]
        mascara = self.Image.new("L", (W, H), 0)
        ImageDraw.Draw(mascara).rounded_rectangle(caja, radius=radio - b, fill=255)
        img.paste((5, 6, 8, 255), (0, 0), mascara)                                              # pantalla apagada
        camara = self.Image.new("RGBA", (W, H), (0, 0, 0, 0))  # aparte: queda arriba de la pantalla prendida
        cx, cy, r = b + round(H * .055), H // 2, round(H * .022)
        ImageDraw.Draw(camara).ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 11, 13, 255),
                                       outline=(44, 50, 58, 255), width=e)
        # Reflejo apenas visible en la pantalla apagada
        reflejo = self.Image.new("L", (W, H), 0)
        ImageDraw.Draw(reflejo).polygon([(W * .55, b), (W * .72, b), (W * .5, H - b), (W * .33, H - b)], fill=14)
        img.paste((255, 255, 255, 255), (0, 0), self.ImageChops.multiply(reflejo, mascara))
        img.alpha_composite(camara)
        img = img.resize((w, h), self.Image.LANCZOS)
        self.camara = camara.resize((w, h), self.Image.LANCZOS)
        caja = tuple(round(v / e) for v in caja)
        mascara = mascara.resize((w, h), self.Image.LANCZOS).crop(caja)  # primero achicar, después recortar
        return img, caja, mascara

    @staticmethod
    def _escala(mascara, k: float):
        return mascara.point([min(255, int(v * k)) for v in range(256)])

    def _pantalla_prendida(self, p: float, b: float):
        """La pantalla con el control, según cuánto está prendida (p) y cuánto brilla el neón (b)."""
        sw, sh = self.pantalla_fondo.size
        img = self.Image.new("RGBA", (sw, sh), (5, 6, 8, 255))
        fondo = self.pantalla_fondo.copy()
        fondo.putalpha(round(255 * p))
        img.alpha_composite(fondo)
        if p > .5:  # el control aparece cuando la pantalla ya está prendida
            control = self.control.copy()
            control.putalpha(self._escala(self.control_alfa, _suave((p - .5) * 2)))
            img.alpha_composite(control, self.pos_control)
        for color, mascara, fuerza in self.neon:
            if b > 0:
                capa = color.copy()
                capa.putalpha(self._escala(mascara, fuerza * b))
                img.alpha_composite(capa, self.pos_control)
        destello = max(0.0, 1 - abs(p - .55) / .45) * .18  # el «flash» de una pantalla que se prende
        if destello > 0:
            img.alpha_composite(self.Image.new("RGBA", (sw, sh), (200, 230, 255, round(255 * destello))))
        img.putalpha(self.mascara_pantalla)
        return img

    def cuadro(self, t: float):
        img = self.fondo.copy()
        g, p, b = giro(t), pantalla(t), brillo(t)
        if p > 0:  # la luz de la pantalla sobre el fondo negro
            luz = self.luz_color.copy()
            luz.putalpha(self.ImageChops.multiply(self._escala(self.luz, .25 * p + .45 * b), self.fondo.getchannel("A")))
            img.alpha_composite(luz)
        cel = self.cel
        if p > 0:
            cel = cel.copy()
            cel.alpha_composite(self._pantalla_prendida(p, b), self.caja_pantalla[:2])
            cel.alpha_composite(self.camara)
        if g < 1:  # girando: parado (cámara arriba) → acostado, y se acerca un poco
            escala = .74 + .26 * g
            w, h = cel.size
            cel = cel.resize((max(1, round(w * escala)), max(1, round(h * escala))), self.Image.BICUBIC)
            cel = cel.rotate(-90 * (1 - g), resample=self.Image.BICUBIC, expand=True)
        x = (self.W - cel.width) // 2
        y = (self.H - cel.height) // 2
        img.alpha_composite(cel, (x, y))
        return img


def debe_mostrarse() -> bool:
    if sys.platform != "win32" or os.environ.get("CONTROL_SIN_ANIMACION") == "1":
        return False
    if any(a in sys.argv for a in ("--minimizado", "--tras-instalar")):
        return False
    import dialogos
    if not dialogos.interactivo():  # pruebas, salida a un archivo
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


def _escala_de_pantalla() -> float:
    """Hace que la ventana de la animación (solo la de este hilo) use píxeles reales, y devuelve la escala de la
    pantalla (1.25 = 125 %). Así Windows no la estira ni queda borrosa."""
    try:
        u = ctypes.windll.user32
        u.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
        u.SetThreadDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        if u.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4)):  # PER_MONITOR_AWARE_V2
            return max(1.0, min(3.0, u.GetDpiForSystem() / 96))
    except Exception:
        pass
    return 1.0


def _correr() -> None:
    _mostrar_consola(False)
    try:
        import rutas
        reproducir(Cuadros(rutas.RECURSOS / "web", _escala_de_pantalla()))
    except Exception:  # la animación es un adorno: si falla, el programa sigue igual (y queda anotado por qué)
        try:
            import traceback
            import rutas
            (rutas.DATOS / "animacion-error.txt").write_text(traceback.format_exc(), "utf-8")
        except Exception:
            pass
    finally:
        if not listo.wait(2):  # no arrancó todavía: seguro está preguntando algo en la consola
            _mostrar_consola(True)
        terminada.set()


def empezar() -> None:
    """Arranca la animación en otro hilo, si corresponde. No espera."""
    if debe_mostrarse():
        terminada.clear()
        threading.Thread(target=_correr, name="animacion", daemon=True).start()
