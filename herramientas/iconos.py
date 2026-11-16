"""Genera los íconos de la app (web/icono-192.png y web/icono-512.png) sin librerías externas."""

import math
import struct
import zlib
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"

FONDO = (236, 238, 241)
CUERPO = (251, 251, 252)
BORDE = (205, 210, 216)
TECLA = (150, 158, 168)
COLORES = [(201, 162, 39), (58, 114, 196), (201, 72, 63), (60, 154, 95)]  # Y X B A


def caja_redondeada(x, y, cx, cy, w, h, r):
    dx = max(abs(x - cx) - (w / 2 - r), 0)
    dy = max(abs(y - cy) - (h / 2 - r), 0)
    return math.hypot(dx, dy) <= r


def color(x, y):
    """x, y en 0..1. Dibuja un control acostado simplificado (zona segura para íconos 'maskable')."""
    if caja_redondeada(x, y, .5, .5, .70, .40, .20):
        if not caja_redondeada(x, y, .5, .5, .67, .37, .185):
            return BORDE
        # Cruceta
        if (abs(x - .32) < .03 and abs(y - .5) < .09) or (abs(y - .5) < .03 and abs(x - .32) < .09):
            return TECLA
        # A B X Y
        for (bx, by), c in zip([(.68, .43), (.62, .5), (.74, .5), (.68, .57)], COLORES):
            if math.hypot(x - bx, y - by) < .033:
                return c
        return CUERPO
    return FONDO


def png(tam, ruta, sub=3):
    filas = bytearray()
    for py in range(tam):
        filas.append(0)
        for px in range(tam):
            acc = [0, 0, 0]
            for sy in range(sub):
                for sx in range(sub):
                    c = color((px + (sx + .5) / sub) / tam, (py + (sy + .5) / sub) / tam)
                    acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]
            filas += bytes(v // (sub * sub) for v in acc)

    def trozo(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))

    ruta.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + trozo(b"IHDR", struct.pack(">IIBBBBB", tam, tam, 8, 2, 0, 0, 0))
                     + trozo(b"IDAT", zlib.compress(bytes(filas), 9))
                     + trozo(b"IEND", b""))


def ico(ruta_png: Path, ruta_ico: Path) -> None:
    """Ícono de Windows (.ico) con una imagen PNG de 256x256 adentro (formato aceptado desde Windows Vista)."""
    datos = ruta_png.read_bytes()
    cabecera = struct.pack("<HHH", 0, 1, 1)
    entrada = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(datos), 6 + 16)  # 0 = 256 px
    ruta_ico.write_bytes(cabecera + entrada + datos)


if __name__ == "__main__":
    for t in (192, 512):
        png(t, WEB / f"icono-{t}.png")
        print("ok", t)
    aqui = Path(__file__).resolve().parent
    png(256, aqui / "icono-256.png")
    ico(aqui / "icono-256.png", aqui / "icono.ico")
    (aqui / "icono-256.png").unlink()
    print("ok icono.ico")
