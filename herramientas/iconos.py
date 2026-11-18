"""Genera los íconos de Control Celular con Pillow: un control acostado con bordes de neón (celeste → verde)
sobre fondo oscuro. Sin logos ni marcas de nadie (el botón central es un círculo que brilla).

  web/icono-192.png, web/icono-512.png   → app del celular y página (fondo oscuro redondeado)
  web/icono-maskable-512.png             → app del celular en Android (fondo a sangre, el control en la zona segura)
  web/icono-bandeja.png                  → ícono al lado del reloj (solo el control, líneas más gruesas)
  web/animacion-cuerpo.png, web/animacion-neon.png → capas de la animación de arranque (animacion.py)
  herramientas/icono.ico                 → .exe, instalador y acceso directo (16 a 256 px)
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).resolve().parent
WEB = AQUI.parent / "web"

S = 1280  # se dibuja grande y se achica (bordes suaves)
CELESTE = (40, 175, 255)
VERDE = (60, 240, 125)
CUERPO = (34, 39, 46)
OSCURO = (22, 26, 31)
TECLA = (58, 65, 74)


def p(v):
    return int(v * S)


def degradado(alto_alfa=255):
    """Imagen del tamaño total con el degradado horizontal celeste → verde."""
    tira = Image.new("RGB", (S, 1))
    for x in range(S):
        t = min(max((x / S - .22) / .56, 0), 1)
        tira.putpixel((x, 0), tuple(round(a + (b - a) * t) for a, b in zip(CELESTE, VERDE)))
    return tira.resize((S, S))


def mascara():
    return Image.new("L", (S, S), 0)


def circulo(d, cx, cy, r, **k):
    d.ellipse([p(cx - r), p(cy - r), p(cx + r), p(cy + r)], **k)


def _curva(tramos, n=48):
    """Une curvas de Bézier cúbicas: tramos = [(c1, c2, fin), ...] empezando en tramos[0][0] (punto inicial)."""
    inicio, *resto = tramos
    puntos = [inicio]
    x0, y0 = inicio
    for (ax, ay), (bx, by), (x3, y3) in resto:
        for i in range(1, n + 1):
            t = i / n
            u = 1 - t
            puntos.append((u ** 3 * x0 + 3 * u * u * t * ax + 3 * u * t * t * bx + t ** 3 * x3,
                           u ** 3 * y0 + 3 * u * u * t * ay + 3 * u * t * t * by + t ** 3 * y3))
        x0, y0 = x3, y3
    return puntos


def _espejo(mitad):
    """De la mitad derecha (de arriba al centro, abajo al centro) arma la figura entera."""
    izquierda = [(1 - x, y) for x, y in reversed(mitad)]
    return [(p(x), p(y)) for x, y in mitad + izquierda]


# Contorno de un control de verdad (mitad derecha): hombro redondeado, costado que baja al agarre, agarre que
# termina redondo abajo y la curva de adentro que vuelve al centro.
MITAD_CUERPO = _curva([
    (.50, .335),
    ((.60, .335), (.66, .333), (.70, .335)),     # borde de arriba, entre los gatillos
    ((.75, .337), (.785, .35), (.80, .375)),     # esquina del hombro, redonda
    ((.83, .44), (.865, .53), (.875, .62)),      # el costado se abre en diagonal hacia el agarre
    ((.885, .70), (.875, .755), (.84, .755)),    # abajo del agarre, redondo
    ((.805, .755), (.78, .74), (.76, .715)),     # vuelve hacia adentro
    ((.735, .685), (.70, .645), (.66, .64)),     # sube por adentro del agarre
    ((.60, .638), (.55, .64), (.50, .64)),       # fondo de la «U» entre los agarres
])

# Gatillos (LB/RB): una pieza curva sobre cada hombro (queda detrás del cuerpo: solo se ve el borde de arriba)
MITAD_GATILLO = _curva([
    (.62, .338),
    ((.66, .312), (.70, .297), (.745, .298)),
    ((.78, .30), (.80, .325), (.803, .36)),
    ((.76, .36), (.68, .345), (.62, .338)),
])


def cuerpo_del_control():
    """Silueta del control (cuerpo y agarres), suavizada para que las uniones queden redondas."""
    m = mascara()
    ImageDraw.Draw(m).polygon(_espejo(MITAD_CUERPO), fill=255)
    return m.filter(ImageFilter.GaussianBlur(p(.006))).point(lambda v: 255 if v > 128 else 0)


def gatillos():
    m = mascara()
    d = ImageDraw.Draw(m)
    derecho = [(p(x), p(y)) for x, y in MITAD_GATILLO]
    d.polygon(derecho, fill=255)
    d.polygon([(S - x, y) for x, y in derecho], fill=255)
    return m.filter(ImageFilter.GaussianBlur(p(.004))).point(lambda v: 255 if v > 128 else 0)


def borde(m, ancho):
    """Contorno de una máscara, de `ancho` (fracción de S)."""
    n = max(3, p(ancho) | 1)
    return ImageChops.subtract(m.filter(ImageFilter.MaxFilter(n)), m.filter(ImageFilter.MinFilter(n)))


def dibujar(fondo=True, grosor=1.0, letras=True, capas=False):
    """Con capas=True devuelve (control sin neón, máscara del neón) para la animación de arranque."""
    lienzo = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    color = degradado()

    if fondo:
        f = Image.new("RGB", (S, S))
        df = ImageDraw.Draw(f)
        for y in range(S):  # degradado vertical apenas más claro arriba
            t = y / S
            df.line([0, y, S, y], fill=tuple(round(a + (b - a) * t) for a, b in zip((38, 44, 52), (14, 17, 21))))
        forma = mascara()
        ImageDraw.Draw(forma).rounded_rectangle([0, 0, S - 1, S - 1], radius=p(.19), fill=255)
        lienzo.paste(f, (0, 0), forma)

    cuerpo = cuerpo_del_control()
    gat = gatillos()
    # Rellenos: gatillos (detrás) y cuerpo
    lienzo.paste(TECLA, (0, 0), gat)
    lienzo.paste(CUERPO, (0, 0), cuerpo)

    neon = mascara()  # todo lo que brilla
    dn = ImageDraw.Draw(neon)
    neon = ImageChops.lighter(neon, borde(cuerpo, .018 * grosor))
    neon = ImageChops.lighter(neon, ImageChops.subtract(borde(gat, .014 * grosor), cuerpo))
    dn = ImageDraw.Draw(neon)
    detalles = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(detalles)

    # Cruceta
    circulo(dd, .31, .45, .085, fill=OSCURO)
    a, l = .028, .065
    dd.rounded_rectangle([p(.31 - a), p(.45 - l), p(.31 + a), p(.45 + l)], radius=p(.01), fill=TECLA)
    dd.rounded_rectangle([p(.31 - l), p(.45 - a), p(.31 + l), p(.45 + a)], radius=p(.01), fill=TECLA)
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):  # flechitas de neón
        cx, cy, t = .31 + dx * .043, .45 + dy * .043, .011
        if dx == 0:
            pts = [(cx - t, cy - dy * t * .6), (cx + t, cy - dy * t * .6), (cx, cy + dy * t)]
        else:
            pts = [(cx - dx * t * .6, cy - t), (cx - dx * t * .6, cy + t), (cx + dx * t, cy)]
        dn.polygon([(p(x), p(y)) for x, y in pts], fill=255)

    # Botón central (redondo, sin logo) y dos botoncitos
    circulo(dd, .5, .395, .045, fill=OSCURO)
    circulo(dn, .5, .395, .03, fill=255)
    for cx in (.435, .565):
        circulo(dd, cx, .465, .022, fill=OSCURO)
        circulo(dn, cx, .465, .022, outline=255, width=p(.007 * grosor))

    # Sticks
    for cx in (.405, .595):
        circulo(dd, cx, .535, .062, fill=OSCURO)
        circulo(dn, cx, .535, .052, outline=255, width=p(.012 * grosor))
        circulo(dd, cx, .535, .032, fill=TECLA)

    # A B X Y
    botones = {"Y": (.69, .385), "X": (.635, .45), "B": (.745, .45), "A": (.69, .515)}
    fuente = None
    if letras:
        try:
            fuente = ImageFont.truetype("arialbd.ttf", p(.04))
        except OSError:
            fuente = None
    for letra, (cx, cy) in botones.items():
        circulo(dd, cx, cy, .03, fill=OSCURO)
        circulo(dn, cx, cy, .03, outline=255, width=p(.007 * grosor))
        if fuente:
            dn.text((p(cx), p(cy)), letra, font=fuente, fill=255, anchor="mm")

    lienzo.alpha_composite(detalles)
    if capas:
        return lienzo, neon
    # Brillo: el neón desenfocado, debajo de la línea nítida
    for radio, fuerza in ((.03, .55), (.01, .8)):
        halo = neon.filter(ImageFilter.GaussianBlur(p(radio))).point(lambda v, f=fuerza: min(255, int(v * f * 1.6)))
        capa = color.copy().convert("RGBA")
        capa.putalpha(halo)
        lienzo.alpha_composite(capa)
    capa = color.copy().convert("RGBA")
    capa.putalpha(neon)
    lienzo.alpha_composite(capa)
    return lienzo


def guardar(img, tam, ruta):
    img.resize((tam, tam), Image.LANCZOS).save(ruta, optimize=True)
    print("ok", ruta.name)


if __name__ == "__main__":
    normal = dibujar()
    for t in (192, 512):
        guardar(normal, t, WEB / f"icono-{t}.png")

    # Android recorta el ícono "maskable" con su forma: fondo a sangre y el control achicado al centro
    solo_control = dibujar(fondo=False)
    base = Image.new("RGBA", (S, S))
    # fondo a sangre: el mismo degradado oscuro, sin esquinas
    for y in range(S):
        t = y / S
        base.paste(tuple(round(a + (b - a) * t) for a, b in zip((38, 44, 52), (14, 17, 21))) + (255,), (0, y, S, y + 1))
    base.alpha_composite(solo_control.resize((p(.8), p(.8)), Image.LANCZOS), (p(.1), p(.1)))
    guardar(base, 512, WEB / "icono-maskable-512.png")

    # Al lado del reloj: solo el control, recortado y con líneas más gruesas (se ve a 16-32 px)
    bandeja = dibujar(fondo=False, grosor=2.2, letras=False)
    caja = bandeja.getbbox()
    lado = max(caja[2] - caja[0], caja[3] - caja[1])
    cuadro = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    cuadro.alpha_composite(bandeja.crop(caja), ((lado - (caja[2] - caja[0])) // 2, (lado - (caja[3] - caja[1])) // 2))
    guardar(cuadro, 64, WEB / "icono-bandeja.png")

    # Animación de arranque en la PC: el control sin neón y, aparte, la máscara del neón (se enciende en animacion.py)
    cuerpo, neon = dibujar(fondo=False, capas=True)
    x0, y0, x1, y1 = ImageChops.lighter(cuerpo.getchannel("A"), neon).getbbox()
    m = p(.06)  # margen para el brillo
    caja = (max(0, x0 - m), max(0, y0 - m), min(S, x1 + m), min(S, y1 + m))
    ancho = 560
    alto = round(ancho * (caja[3] - caja[1]) / (caja[2] - caja[0]))
    cuerpo.crop(caja).resize((ancho, alto), Image.LANCZOS).save(WEB / "animacion-cuerpo.png", optimize=True)
    neon.crop(caja).resize((ancho, alto), Image.LANCZOS).save(WEB / "animacion-neon.png", optimize=True)
    print("ok animación", ancho, alto)

    # App de Android: ícono clásico (5 tamaños) y adaptable (el control sobre el fondo oscuro, Android lo recorta)
    res = AQUI.parent / "android" / "app" / "src" / "main" / "res"
    for carpeta, tam in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        (res / f"mipmap-{carpeta}").mkdir(parents=True, exist_ok=True)
        normal.resize((tam, tam), Image.LANCZOS).save(res / f"mipmap-{carpeta}" / "ic_launcher.png", optimize=True)
    caja = solo_control.getbbox()
    control = solo_control.crop(caja)
    ancho = round(432 * .64)
    control = control.resize((ancho, round(ancho * control.height / control.width)), Image.LANCZOS)
    primer_plano = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    primer_plano.alpha_composite(control, ((432 - control.width) // 2, (432 - control.height) // 2))
    (res / "drawable").mkdir(parents=True, exist_ok=True)
    primer_plano.save(res / "drawable" / "ic_launcher_foreground.png", optimize=True)
    print("ok íconos de Android")

    normal.resize((256, 256), Image.LANCZOS).save(
        AQUI / "icono.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("ok icono.ico")
