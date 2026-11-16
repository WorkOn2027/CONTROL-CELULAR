"""CONTROL CELULAR - servidor de la PC.

Sirve la página del control y recibe por WebSocket lo que se toca en cada celular.
Cada celular es un jugador (hasta 4) con su propio control de Xbox 360 virtual (ViGEmBus + vgamepad).

Protocolo (texto, mensajes cortos):
  celular -> PC:  "a <codigo|token>"     emparejar / reconectar
                  "b <BOTON> <0|1>"      botón apretado / suelto
                  "t <L|R> <0-255>"      gatillo
                  "s <L|R> <x> <y>"      stick, x/y en -1000..1000 (y positivo = arriba)
                  "r"                    soltar todo
                  "p <n>"                ping (la PC contesta lo mismo, para medir la demora)
                  "k <clave> <valor>"    guardar un ajuste de ESTE celular en la PC (valor vacío = borrarlo)
                  "d <nombre>"           nombre del celular (su modelo), para reconocerlo en las listas
                  "l"                    pedir la lista de otros celulares con ajustes guardados
                  "cp <id>"              copiar los ajustes de otro celular a este
                  "m <xbox|ds4>"         qué control ve la PC (Xbox 360 o DualShock 4)
                  "g gx gy gz ax ay az"  giroscopio y acelerómetro (solo DualShock 4, unidades del DS4)
  PC -> celular:  "ok <token>" | "no" | "lleno"   resultado del emparejamiento
                  "espera <segundos>"    demasiados códigos equivocados: esperar antes de reintentar
                  "lc <json>"            lista de otros celulares [{id, nombre, visto}]
                  "cc <json>"            ajustes recién copiados (aplicarlos y recargar)
                  "n <jugador>"          qué número de jugador es (1-4)
                  "c <json>"             los ajustes de este celular guardados en la PC (al conectarse)
                  "v <grande> <chico>"   vibración (0-255 cada motor)
                  "j <appid> <tipo> <nombre>" | "j 0"   juego de Steam abierto en la PC (o ninguno)
                  "p <n>"                respuesta al ping
  HTTP(S):        /juegos?t=<token>      biblioteca de Steam (JSON)   /portada/<appid>?t=<token>  portada
                  /qr                    QR para conectarse (solo desde esta misma PC)
"""

import asyncio
import json
import mimetypes
import secrets
import socket
import ssl
import sys
import time
from urllib.parse import parse_qs, urlsplit

import vgamepad as vg
from websockets.asyncio.server import serve
from websockets.datastructures import Headers
from websockets.http11 import Response

import certs
import red
import rutas
import steam

PUERTO = 8765          # HTTP: página para instalar el certificado
PUERTO_SEGURO = 8443   # HTTPS: el control
MAX_JUGADORES = 4
WEB = rutas.RECURSOS / "web"
TOKENS = rutas.DATOS / "tokens.json"
AJUSTES = rutas.DATOS / "ajustes.json"
DESCARGA_VIGEMBUS = "https://github.com/nefarius/ViGEmBus/releases"
MINIMIZADO = "--minimizado" in sys.argv  # al arrancar con Windows: ventana oculta, sin preguntas


def salir(codigo_salida: int = 0) -> None:
    """En el .exe la ventana se cerraría sola y no se leería el mensaje: esperar un Enter."""
    if rutas.EMPAQUETADO and not MINIMIZADO:
        try:
            input("  Presioná Enter para cerrar...")
        except (EOFError, OSError):
            pass
    raise SystemExit(codigo_salida)


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


def ip_local() -> str:
    """IP de la PC en la red de casa (no manda nada a internet)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def _leer_json(ruta, vacio):
    try:
        return json.loads(ruta.read_text("utf-8"))
    except (OSError, ValueError):
        return vacio


def _guardar_json(ruta, datos) -> None:
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False), "utf-8")
    tmp.replace(ruta)


def _cargar_celulares() -> dict[str, dict]:
    """Celulares emparejados: token -> {nombre, visto}. (Antes era una lista de tokens: se convierte sola.)"""
    d = _leer_json(TOKENS, {})
    if isinstance(d, list):
        d = {t: {"nombre": f"Celular {i + 1}", "visto": 0} for i, t in enumerate(d)}
    return d if isinstance(d, dict) else {}


def _cargar_ajustes() -> dict:
    """Ajustes de cada celular: {"celulares": {token: {clave: valor}}}. None = borrado.
    Si el archivo es del formato viejo (uno solo para toda la PC), no se le da a nadie: se guarda como respaldo.
    Cada celular tiene su propia copia y la vuelve a subir sola al conectarse."""
    d = _leer_json(AJUSTES, {})
    if not isinstance(d, dict) or "celulares" not in d:
        if d:
            _guardar_json(AJUSTES.with_name("ajustes-formato-viejo.json"), d)
        d = {"celulares": {}}
    return d


celulares: dict[str, dict] = _cargar_celulares()
ajustes: dict = _cargar_ajustes()
codigo = f"{secrets.randbelow(10000):04d}"
loop: asyncio.AbstractEventLoop | None = None


def guardar_celulares() -> None:
    _guardar_json(TOKENS, celulares)


def guardar_ajustes() -> None:
    _guardar_json(AJUSTES, ajustes)


def ajustes_de(token: str) -> dict:
    return ajustes["celulares"].setdefault(token, {})


def id_corto(token: str) -> str:
    """Identificador para mostrar o elegir un celular sin revelar su token."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()[:10]


# ---------- Límite de intentos con el código de emparejamiento ----------
# Cada 5 códigos equivocados desde un mismo equipo: bloqueo que se duplica (30 s, 1 min, 2 min... hasta 1 h).
# Si en 10 minutos hay 40 fallos en total (aunque vengan de varios equipos), el código cambia solo.
INTENTOS, BLOQUEO_BASE, BLOQUEO_MAX = 5, 30, 3600
fallos: dict[str, list] = {}  # ip -> [fallos seguidos, bloqueado hasta, veces bloqueado]
fallos_recientes: list[float] = []


def segundos_bloqueado(ip: str) -> int:
    f = fallos.get(ip)
    return max(0, int(f[1] - time.time()) + 1) if f and time.time() < f[1] else 0


def anotar_fallo(ip: str) -> None:
    global codigo
    f = fallos.setdefault(ip, [0, 0.0, 0])
    f[0] += 1
    if f[0] >= INTENTOS:
        f[0], f[2] = 0, f[2] + 1
        espera = min(BLOQUEO_MAX, BLOQUEO_BASE * 2 ** (f[2] - 1))
        f[1] = time.time() + espera
        print(f"  {INTENTOS} códigos equivocados desde {ip}: bloqueado {espera} segundos.")
    ahora = time.time()
    fallos_recientes.append(ahora)
    while fallos_recientes and ahora - fallos_recientes[0] > 600:
        fallos_recientes.pop(0)
    if len(fallos_recientes) >= 40:
        fallos_recientes.clear()
        codigo = f"{secrets.randbelow(10000):04d}"
        direccion["qr"] = f"http://{direccion['ip']}:{PUERTO}/?c={codigo}"
        print(f"  Demasiados intentos fallidos: cambié el código de emparejamiento. Nuevo código: {codigo}")
        print("  (el QR del ícono ya tiene el código nuevo)")


# ---------- Jugadores (un control virtual por celular) ----------

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


class Jugador:
    """Un celular = un control virtual. Puede ser de Xbox 360 o DualShock 4 (lo elige cada celular)."""

    def __init__(self, numero: int, tipo: str = "xbox"):
        self.numero = numero
        self.ws = None
        self.token = None
        self.pad = None
        self.tipo = None
        self.cambiar_tipo(tipo)

    def cambiar_tipo(self, tipo: str) -> None:
        if tipo not in TIPOS_MANDO or tipo == self.tipo:
            return
        if self.pad is not None:
            self.soltar()
            self.pad = None  # al soltarlo, vgamepad lo desenchufa de Windows
        self.pad = vg.VDS4Gamepad() if tipo == "ds4" else vg.VX360Gamepad()
        self.tipo = tipo
        self.cruceta = {"UP": 0, "DOWN": 0, "LEFT": 0, "RIGHT": 0}
        self.pad.reset()
        self.pad.update()  # arrancar con todo en cero (si no, los sticks quedan corridos)
        self.pad.register_notification(callback_function=self._al_vibrar)

    def _al_vibrar(self, client, target, grande, chico, led, user_data):
        """Lo llama el driver (desde otro hilo) cuando un juego hace vibrar ESTE control."""
        if self.ws is not None and loop is not None:
            loop.call_soon_threadsafe(asyncio.ensure_future, enviar(self.ws, f"v {grande} {chico}"))

    def soltar(self) -> None:
        self.cruceta = {"UP": 0, "DOWN": 0, "LEFT": 0, "RIGHT": 0}
        self.pad.reset()
        self.pad.update()

    def aplicar(self, msg: str) -> None:
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


jugadores: dict[int, Jugador] = {}


def crear_primer_control() -> None:
    """El jugador 1 se crea al arrancar: así, si falta ViGEmBus, se avisa enseguida."""
    try:
        jugadores[1] = Jugador(1)
    except Exception as e:  # casi siempre: falta el driver ViGEmBus
        print()
        print("  No pude crear el control virtual de Xbox:", e)
        print("  Falta el driver ViGEmBus (es gratis y oficial). Te abro la página para descargarlo:")
        print(f"    {DESCARGA_VIGEMBUS}")
        print("  Bajá el archivo ViGEmBus_..._x64_x86_arm64.exe, instalalo y volvé a abrir Control Celular.")
        print()
        try:
            import webbrowser
            webbrowser.open(DESCARGA_VIGEMBUS)
        except Exception:
            pass
        salir(1)


def lugar_para(token: str) -> Jugador | None:
    """El mismo celular vuelve siempre a su número de jugador; uno nuevo toma el primer lugar libre."""
    for j in jugadores.values():
        if j.token == token:
            return j
    for n in range(1, MAX_JUGADORES + 1):
        j = jugadores.get(n)
        if j is None:
            jugadores[n] = Jugador(n)
            return jugadores[n]
        if j.ws is None:
            return j
    return None


def conectados() -> list[Jugador]:
    return [j for j in jugadores.values() if j.ws is not None]


al_cambiar_conexiones = None  # lo usa el ícono de la barra para mostrar cuántos hay


def avisar_conexiones() -> None:
    if al_cambiar_conexiones:
        try:
            al_cambiar_conexiones([j.numero for j in conectados()])
        except Exception:
            pass


def limitar(v: float) -> float:
    return max(-1.0, min(1.0, v))


async def enviar(ws, texto: str) -> None:
    try:
        await ws.send(texto)
    except Exception:
        pass


async def a_todos(texto: str) -> None:
    for j in conectados():
        await enviar(j.ws, texto)


def guardar_ajuste(token: str, resto: str) -> None:
    clave, _, valor = resto.partition(" ")
    if not clave or len(clave) > 100 or len(valor) > 200_000:
        return
    ajustes_de(token)[clave] = valor if valor != "" else None
    guardar_ajustes()


def otros_celulares(token: str) -> list[dict]:
    """Los demás celulares que tienen ajustes guardados (para copiarlos)."""
    lista = []
    for t, info in celulares.items():
        a = ajustes["celulares"].get(t) or {}
        if t != token and any(v is not None for v in a.values()):
            lista.append({"id": id_corto(t), "nombre": info.get("nombre") or "Celular", "visto": info.get("visto", 0)})
    return sorted(lista, key=lambda c: -c["visto"])


def copiar_ajustes(token: str, id_origen: str) -> bool:
    origen = next((t for t in celulares if id_corto(t) == id_origen and t != token), None)
    if origen is None:
        return False
    ajustes["celulares"][token] = dict(ajustes["celulares"].get(origen) or {})
    guardar_ajustes()
    return True


async def atender(ws):
    ip = ws.remote_address[0]
    # Emparejamiento: primer mensaje = código (primera vez) o token guardado.
    try:
        primero = await asyncio.wait_for(ws.recv(), timeout=30)
    except Exception:
        return
    partes = primero.split()
    if len(partes) != 2 or partes[0] != "a":
        await ws.send("no")
        return
    clave = partes[1]
    if clave in celulares:
        token = clave
    else:
        espera = segundos_bloqueado(ip)
        if espera:
            await ws.send(f"espera {espera}")
            return
        if clave != codigo:
            anotar_fallo(ip)
            await ws.send("no")
            print("  Intento con código incorrecto desde", ip)
            return
        fallos.pop(ip, None)
        token = secrets.token_urlsafe(16)
        celulares[token] = {"nombre": "Celular", "visto": 0}
    celulares[token]["visto"] = int(time.time())
    guardar_celulares()

    j = lugar_para(token)
    if j is None:
        await ws.send("lleno")
        print(f"  Ya hay {MAX_JUGADORES} celulares conectados; no entra otro.")
        return
    if j.ws is not None:  # el mismo celular se reconectó: cerrar la conexión vieja
        viejo, j.ws = j.ws, None
        await viejo.close()
    j.ws, j.token = ws, token
    await ws.send(f"ok {token}")
    j.cambiar_tipo(celulares[token].get("mando", "xbox"))  # cada celular recuerda si es Xbox o DualShock 4
    await ws.send(f"n {j.numero}")
    await ws.send(f"m {j.tipo}")
    await ws.send("c " + json.dumps(ajustes_de(token), ensure_ascii=False))
    await ws.send(mensaje_abierto())
    print(f"  Jugador {j.numero} conectado ({celulares[token]['nombre']}):", ip)
    avisar_conexiones()
    try:
        async for msg in ws:
            if token not in celulares:  # lo olvidaron desde el ícono mientras estaba conectado
                break
            try:
                if msg.startswith("p "):
                    await ws.send(msg)
                elif msg.startswith("k "):
                    guardar_ajuste(token, msg[2:])
                elif msg.startswith("d "):  # el celular dice su modelo, para reconocerlo en las listas
                    nombre = " ".join(msg[2:].split())[:40]
                    if nombre and celulares.get(token, {}).get("nombre") != nombre:
                        celulares[token]["nombre"] = nombre
                        guardar_celulares()
                        avisar_conexiones()
                elif msg.startswith("m "):  # qué control ve la PC: Xbox 360 o DualShock 4
                    nuevo = msg[2:].strip()
                    if nuevo in TIPOS_MANDO and nuevo != j.tipo:
                        j.cambiar_tipo(nuevo)
                        celulares[token]["mando"] = nuevo
                        guardar_celulares()
                        nombre_mando = "DualShock 4" if nuevo == "ds4" else "Xbox 360"
                        print(f"  Jugador {j.numero} ahora es un control {nombre_mando}")
                    await ws.send(f"m {j.tipo}")
                elif msg == "l":
                    await ws.send("lc " + json.dumps(otros_celulares(token), ensure_ascii=False))
                elif msg.startswith("cp "):
                    if copiar_ajustes(token, msg[3:].strip()):
                        await ws.send("cc " + json.dumps(ajustes_de(token), ensure_ascii=False))
                else:
                    j.aplicar(msg)
            except (ValueError, IndexError):
                pass
    except Exception:
        pass
    finally:
        if j.ws is ws:
            j.ws = None
            j.soltar()
            print(f"  Jugador {j.numero} desconectado (se soltaron todos sus botones)")
            avisar_conexiones()


# ---------- Olvidar celulares (desde el ícono de la barra) ----------

def lista_para_bandeja() -> list[dict]:
    conectados_tok = {j.token for j in conectados()}
    return sorted(({"id": id_corto(t), "nombre": i.get("nombre") or "Celular", "visto": i.get("visto", 0),
                    "conectado": t in conectados_tok} for t, i in celulares.items()), key=lambda c: -c["visto"])


async def _olvidar(ids: set[str] | None) -> None:
    """Saca celulares emparejados (None = todos): pierden el permiso y sus ajustes, y se desconectan."""
    objetivo = [t for t in celulares if ids is None or id_corto(t) in ids]
    for t in objetivo:
        celulares.pop(t, None)
        ajustes["celulares"].pop(t, None)
        for j in jugadores.values():
            if j.token == t:
                j.token = None
                if j.ws is not None:
                    await j.ws.close()
    guardar_celulares()
    guardar_ajustes()
    print(f"  Olvidé {len(objetivo)} celular(es). Para volver a usarlos hay que emparejarlos de nuevo (QR).")
    avisar_conexiones()


def olvidar_desde_bandeja(ids: set[str] | None) -> None:
    """Lo llama el ícono (otro hilo): hace el trabajo dentro del servidor."""
    if loop is not None:
        loop.call_soon_threadsafe(asyncio.ensure_future, _olvidar(ids))


# ---------- Biblioteca de Steam ----------
_biblio = {"hora": 0.0, "lista": []}
abierto = {"id": None}


def biblioteca() -> list[dict]:
    """Lista de juegos instalados (se relee cada 5 minutos, leerla cuesta un poco)."""
    if time.time() - _biblio["hora"] > 300:
        try:
            _biblio["lista"] = steam.juegos()
        except Exception as e:  # nunca tirar abajo el servidor por esto
            print("  No pude leer la biblioteca de Steam:", e)
        _biblio["hora"] = time.time()
    return _biblio["lista"]


def mensaje_abierto() -> str:
    j = next((j for j in biblioteca() if j["id"] == abierto["id"]), None)
    return f"j {j['id']} {j['tipo']} {j['nombre']}" if j else "j 0"


async def vigilar_juego():
    """Cada 4 segundos se fija qué juego está abierto y, si cambió, les avisa a los celulares."""
    while True:
        try:
            actual = await asyncio.to_thread(lambda: steam.juego_abierto(biblioteca()))
        except Exception:
            actual = None
        if actual != abierto["id"]:
            abierto["id"] = actual
            await a_todos(mensaje_abierto())
        await asyncio.sleep(4)


# ---------- QR para conectarse ----------
direccion = {"qr": "", "ip": ""}


def qr_svg() -> bytes:
    import io
    import segno
    buf = io.BytesIO()
    segno.make(direccion["qr"], error="m").save(buf, kind="svg", scale=10, border=3, dark="#2b3138")
    return buf.getvalue()


def pagina_qr() -> bytes:
    svg = qr_svg().decode("utf-8")
    svg = svg[svg.index("<svg"):]
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Conectar el celular</title>
<style>body{{margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;
gap:14px;background:#eceef1;color:#3d444d;font:17px/1.4 system-ui,sans-serif;text-align:center;padding:16px}}
.caja{{background:#fff;border-radius:20px;padding:18px;box-shadow:0 0 0 1px #dfe2e6}} svg{{width:min(70vw,340px);height:auto}}
code{{font-size:15px;background:#fff;padding:4px 8px;border-radius:8px}} b{{font-size:28px;letter-spacing:4px}}</style></head>
<body><h1 style="margin:0;font-size:24px">Escaneá con la cámara del celular</h1>
<div class="caja">{svg}</div>
<div>O abrí en Chrome: <code>{direccion["qr"].split("?")[0]}</code> y poné el código <b>{codigo}</b></div>
<div style="opacity:.7;font-size:14px">El celular tiene que estar en el mismo WiFi que esta PC.</div></body></html>""".encode()


def mostrar_qr_en_consola() -> None:
    try:
        import segno
        segno.make(direccion["qr"], error="m").terminal(compact=True, border=2)
    except Exception:
        pass  # si la consola no puede dibujarlo, queda la dirección escrita y el QR del ícono


# ---------- Página web ----------

def respuesta(cuerpo: bytes, tipo: str, extra=(), cache="no-cache") -> Response:
    if tipo.startswith("text") or tipo.endswith(("json", "javascript", "svg+xml")):
        tipo += "; charset=utf-8"
    headers = Headers([("Content-Type", tipo), ("Content-Length", str(len(cuerpo))),
                       ("Cache-Control", cache), *extra])
    return Response(200, "OK", headers, cuerpo)


def servir_archivos(seguro: bool):
    """Sirve la página web en el mismo puerto que el WebSocket.

    HTTPS: el control (con app instalable y giroscopio).
    HTTP:  la página de configuración para instalar el certificado (y el control sin extras, por si acaso).
    """
    def atender_http(connection, request):
        if request.headers.get("Upgrade", "").lower() == "websocket":
            return None
        partes = urlsplit(request.path)
        ruta = partes.path
        if ruta in ("/qr", "/qr.svg"):
            # El QR lleva el código de emparejamiento: solo se muestra en esta misma PC.
            if connection.remote_address[0] not in ("127.0.0.1", "::1"):
                return connection.respond(403, "Solo desde la PC\n")
            if ruta == "/qr.svg":
                return respuesta(qr_svg(), "image/svg+xml")
            return respuesta(pagina_qr(), "text/html")
        if ruta == "/juegos" or ruta.startswith("/portada/"):
            # La biblioteca es privada: solo para celulares emparejados.
            if parse_qs(partes.query).get("t", [""])[0] not in celulares:
                return connection.respond(403, "Sin permiso\n")
            if ruta == "/juegos":
                lista = [{k: j[k] for k in ("id", "nombre", "tipo")} for j in biblioteca()]
                cuerpo = json.dumps({"abierto": abierto["id"], "juegos": lista}, ensure_ascii=False)
                return respuesta(cuerpo.encode("utf-8"), "application/json")
            p = steam.portada(int(ruta.rsplit("/", 1)[1])) if ruta.rsplit("/", 1)[1].isdigit() else None
            if not p:
                return connection.respond(404, "Sin portada\n")
            return respuesta(p.read_bytes(), "image/jpeg", cache="max-age=86400")
        if ruta == "/ca.crt":
            return respuesta(certs.ca_der(), "application/x-x509-ca-cert",
                             [("Content-Disposition", 'attachment; filename="control-celular-ca.crt"')])
        if ruta == "/ping":
            return respuesta(b"ok", "text/plain", [("Access-Control-Allow-Origin", "*")])
        if ruta == "/":
            ruta = "/index.html" if seguro else "/configurar.html"
        archivo = (WEB / ruta.lstrip("/")).resolve()
        if WEB.resolve() not in archivo.parents or not archivo.is_file():
            return connection.respond(404, "No encontrado\n")
        tipo = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
        if archivo.suffix == ".webmanifest":
            tipo = "application/manifest+json"
        return respuesta(archivo.read_bytes(), tipo)
    return atender_http


async def main():
    global loop
    loop = asyncio.get_running_loop()
    ip = ip_local()
    direccion["ip"] = ip
    direccion["qr"] = f"http://{ip}:{PUERTO}/?c={codigo}"
    crt, key = certs.preparar(ip)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(crt, key)
    opciones = dict(compression=None, ping_interval=5, ping_timeout=10)
    async with serve(atender, "0.0.0.0", PUERTO, process_request=servir_archivos(False), **opciones), \
            serve(atender, "0.0.0.0", PUERTO_SEGURO, process_request=servir_archivos(True), ssl=tls,
                  **opciones) as seguro:
        print()
        print("  CONTROL CELULAR listo. Escaneá este QR con la cámara del celular:")
        print()
        mostrar_qr_en_consola()
        print()
        print(f"  O abrí en Chrome:  http://{ip}:{PUERTO}   y poné el código  {codigo}")
        print(f"  (con el certificado ya instalado, la app es:  https://{ip}:{PUERTO_SEGURO})")
        print("  El celular tiene que estar en la misma red WiFi que esta PC. Hasta 4 celulares a la vez.")
        print("  ¿No conecta? Cerrá y volvé a abrir: te ofrezco abrir el firewall y marcar la red como privada.")
        print("  El ícono del control, al lado del reloj, tiene el QR y más opciones.")
        print()
        try:
            import bandeja
            global al_cambiar_conexiones
            al_cambiar_conexiones = bandeja.iniciar(f"http://127.0.0.1:{PUERTO}/qr", soltar_todo_y_salir,
                                                     MINIMIZADO, lista_para_bandeja, olvidar_desde_bandeja)
        except Exception as e:
            print("  (No pude poner el ícono en la barra de tareas:", e, ")")
        await asyncio.to_thread(biblioteca)
        print(f"  Biblioteca de Steam: {len(biblioteca())} juegos")
        asyncio.ensure_future(vigilar_juego())
        await seguro.serve_forever()


def soltar_todo_y_salir() -> None:
    for j in jugadores.values():
        try:
            j.soltar()
        except Exception:
            pass
    import os
    os._exit(0)


if __name__ == "__main__":
    try:
        # Que los mensajes salgan al instante. Si la salida no es una ventana (va a un archivo), en UTF-8:
        # así se ven los acentos y el QR (en la ventana de Windows ya se ven siempre).
        if sys.stdout.isatty():
            sys.stdout.reconfigure(line_buffering=True)
        else:
            sys.stdout.reconfigure(line_buffering=True, encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    import version
    print()
    print(f"  === CONTROL CELULAR {version.VERSION} ===")
    print()
    red.revisar(preguntar=not MINIMIZADO)  # firewall y red privada: solo pregunta si falta algo
    crear_primer_control()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except OSError as e:
        print()
        print("  No pude arrancar:", e)
        if getattr(e, "winerror", None) == 10048:
            print("  Parece que Control Celular ya está abierto en otra ventana. Cerrala y probá de nuevo.")
        salir(1)
    except Exception as e:
        print()
        print("  Error inesperado:", repr(e))
        salir(1)
