"""CONTROL CELULAR - servidor de la PC.

Sirve la página del control y recibe por WebSocket lo que se toca en el celular.
Lo vuelca en un control de Xbox 360 virtual (ViGEmBus + vgamepad).

Protocolo (texto, mensajes cortos):
  celular -> PC:  "a <codigo|token>"     emparejar / reconectar
                  "b <BOTON> <0|1>"      botón apretado / suelto
                  "t <L|R> <0-255>"      gatillo
                  "s <L|R> <x> <y>"      stick, x/y en -1000..1000 (y positivo = arriba)
                  "r"                    soltar todo
  PC -> celular:  "ok <token>" | "no"    resultado del emparejamiento
                  "v <grande> <chico>"   vibración (0-255 cada motor)
                  "j <appid> <tipo> <nombre>" | "j 0"   juego de Steam abierto en la PC (o ninguno)
  HTTP(S):        /juegos?t=<token>      biblioteca de Steam (JSON)   /portada/<appid>?t=<token>  portada
"""

import asyncio
import json
import mimetypes
import secrets
import socket
import ssl
from pathlib import Path

import time
from urllib.parse import parse_qs, urlsplit

import vgamepad as vg

import certs
import steam
from websockets.asyncio.server import serve
from websockets.datastructures import Headers
from websockets.http11 import Response

PUERTO = 8765          # HTTP: página para instalar el certificado
PUERTO_SEGURO = 8443   # HTTPS: el control
CARPETA = Path(__file__).parent
WEB = CARPETA / "web"
TOKENS = CARPETA / "tokens.json"

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


def cargar_tokens() -> set[str]:
    try:
        return set(json.loads(TOKENS.read_text("utf-8")))
    except (OSError, ValueError):
        return set()


def guardar_tokens(tokens: set[str]) -> None:
    TOKENS.write_text(json.dumps(sorted(tokens)), "utf-8")


tokens = cargar_tokens()
codigo = f"{secrets.randbelow(10000):04d}"
try:
    pad = vg.VX360Gamepad()
except Exception as e:  # casi siempre: falta el driver ViGEmBus
    print()
    print("  No pude crear el control virtual de Xbox:", e)
    print("  Falta el driver ViGEmBus. Instalalo desde:")
    print("    https://github.com/nefarius/ViGEmBus/releases  (archivo ViGEmBus_..._x64_x86_arm64.exe)")
    print("  y después volvé a abrir iniciar.bat.")
    print()
    raise SystemExit(1)
cliente = None  # conexión activa (una sola a la vez)
loop = None


def limitar(v: float) -> float:
    return max(-1.0, min(1.0, v))


def aplicar(msg: str) -> None:
    p = msg.split()
    if not p:
        return
    tipo = p[0]
    if tipo == "b" and len(p) == 3 and p[1] in BOTONES:
        if p[2] == "1":
            pad.press_button(BOTONES[p[1]])
        else:
            pad.release_button(BOTONES[p[1]])
    elif tipo == "t" and len(p) == 3:
        valor = max(0, min(255, int(p[2])))
        (pad.left_trigger if p[1] == "L" else pad.right_trigger)(valor)
    elif tipo == "s" and len(p) == 4:
        x, y = limitar(int(p[2]) / 1000), limitar(int(p[3]) / 1000)
        if p[1] == "L":
            pad.left_joystick_float(x, y)
        else:
            pad.right_joystick_float(x, y)
    elif tipo == "r":
        pad.reset()
    else:
        return
    pad.update()


def al_vibrar(client, target, grande, chico, led, user_data):
    """Lo llama el driver (desde otro hilo) cuando un juego pide vibración."""
    if cliente is not None and loop is not None:
        loop.call_soon_threadsafe(
            asyncio.ensure_future, enviar(f"v {grande} {chico}")
        )


async def enviar(texto: str) -> None:
    try:
        if cliente is not None:
            await cliente.send(texto)
    except Exception:
        pass


async def atender(ws):
    global cliente
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
    if clave in tokens:
        token = clave
    elif clave == codigo:
        token = secrets.token_urlsafe(16)
        tokens.add(token)
        guardar_tokens(tokens)
    else:
        await ws.send("no")
        print("  Intento con código incorrecto desde", ws.remote_address[0])
        return

    await ws.send(f"ok {token}")
    if cliente is not None:
        await cliente.close()
    cliente = ws
    print("  Celular conectado:", ws.remote_address[0])
    await ws.send(mensaje_abierto())
    try:
        async for msg in ws:
            try:
                aplicar(msg)
            except (ValueError, IndexError):
                pass
    except Exception:
        pass
    finally:
        if cliente is ws:
            cliente = None
            pad.reset()
            pad.update()
            print("  Celular desconectado (se soltaron todos los botones)")


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
    """Cada 4 segundos se fija qué juego está abierto y, si cambió, le avisa al celular."""
    while True:
        try:
            actual = await asyncio.to_thread(lambda: steam.juego_abierto(biblioteca()))
        except Exception:
            actual = None
        if actual != abierto["id"]:
            abierto["id"] = actual
            await enviar(mensaje_abierto())
        await asyncio.sleep(4)


def respuesta(cuerpo: bytes, tipo: str, extra=(), cache="no-cache") -> Response:
    if tipo.startswith("text") or tipo.endswith(("json", "javascript")):
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
        if ruta == "/juegos" or ruta.startswith("/portada/"):
            # La biblioteca es privada: solo para celulares emparejados.
            if parse_qs(partes.query).get("t", [""])[0] not in tokens:
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
    pad.reset()
    pad.update()  # arrancar con todo en cero (si no, los sticks quedan corridos)
    pad.register_notification(callback_function=al_vibrar)
    ip = ip_local()
    crt, key = certs.preparar(ip)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(crt, key)
    opciones = dict(compression=None, ping_interval=5, ping_timeout=10)
    async with serve(atender, "0.0.0.0", PUERTO, process_request=servir_archivos(False), **opciones), \
            serve(atender, "0.0.0.0", PUERTO_SEGURO, process_request=servir_archivos(True), ssl=tls,
                  **opciones) as seguro:
        print()
        print("  CONTROL CELULAR listo")
        print(f"  Control (app):         https://{ip}:{PUERTO_SEGURO}")
        print(f"  Primera vez / ayuda:   http://{ip}:{PUERTO}")
        print(f"  Código de emparejamiento:  {codigo}")
        print("  El celular tiene que estar en la misma red WiFi que esta PC.")
        print("  ¿No conecta? Ejecutá permitir-firewall.bat (una sola vez) y fijate que tu red sea «Privada».")
        print("  (Ctrl+C para cerrar)")
        print()
        await asyncio.to_thread(biblioteca)
        print(f"  Biblioteca de Steam: {len(biblioteca())} juegos")
        asyncio.ensure_future(vigilar_juego())
        await seguro.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
