"""Las páginas web (en el mismo puerto que el WebSocket) y el QR para conectarse.

HTTPS: el control (con app instalable y giroscopio).
HTTP:  la página de configuración para instalar el certificado (y el control sin extras, por si acaso).
El iPhone tiene su propia versión de las páginas (archivos aparte, para que no se mezclen con las de Android).
"""

import io
import json
import mimetypes
import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlsplit

from websockets.datastructures import Headers
from websockets.http11 import Response

import certs
import steam
from idioma import T

ES_IOS = re.compile(r"iPhone|iPad|iPod")
# La app de Android trae sus propias páginas y le pide a la PC la biblioteca de Steam (con el token del celular):
# el navegador de la app necesita este permiso para leerla desde otro origen.
PARA_LA_APP = [("Access-Control-Allow-Origin", "*")]
# La app de Android, siempre la última versión publicada (el archivo de Releases se tiene que llamar así)
DESCARGA_APP = "https://github.com/WorkOn2027/CONTROL-CELULAR/releases/latest/download/ControlCelular.apk"


@dataclass
class Contexto:
    """Lo que las páginas necesitan saber del servidor."""
    web: Path
    es_celular_emparejado: Callable[[str], bool]
    biblioteca: Callable[[], list]
    juego_abierto: Callable[[], int | None]
    url_qr: Callable[[], str]
    codigo: Callable[[], str]
    # La ventana de la PC (panel.py): solo desde esta misma PC y con la clave del panel
    panel_clave: Callable[[], str] | None = None
    panel_estado: Callable[[], dict] | None = None
    panel_accion: Callable[[str, dict], dict] | None = None


def respuesta(cuerpo: bytes, tipo: str, extra=(), cache="no-cache") -> Response:
    if tipo.startswith("text") or tipo.endswith(("json", "javascript", "svg+xml")):
        tipo += "; charset=utf-8"
    headers = Headers([("Content-Type", tipo), ("Content-Length", str(len(cuerpo))),
                       ("Cache-Control", cache), *extra])
    return Response(200, "OK", headers, cuerpo)


# ---------- QR ----------

def qr_svg(url: str) -> bytes:
    import segno
    buf = io.BytesIO()
    segno.make(url, error="m").save(buf, kind="svg", scale=10, border=3, dark="#2b3138")
    return buf.getvalue()


def pagina_qr(url: str, codigo: str) -> bytes:
    svg = qr_svg(url).decode("utf-8")
    svg = svg[svg.index("<svg"):]
    return f"""<!doctype html><html lang="{T("es", "en")}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{T("Conectar el celular", "Connect your phone")}</title>
<style>body{{margin:0;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;
gap:14px;background:#eceef1;color:#3d444d;font:17px/1.4 system-ui,sans-serif;text-align:center;padding:16px}}
.caja{{background:#fff;border-radius:20px;padding:18px;box-shadow:0 0 0 1px #dfe2e6}} svg{{width:min(70vw,340px);height:auto}}
code{{font-size:15px;background:#fff;padding:4px 8px;border-radius:8px}} b{{font-size:28px;letter-spacing:4px}}</style></head>
<body><h1 style="margin:0;font-size:24px">{T("Escaneá con la cámara del celular", "Scan with your phone's camera")}</h1>
<div class="caja">{svg}</div>
<div>{T("O abrí en el navegador:", "Or open in your browser:")} <code>{url.split("?")[0]}</code> {T("y poné el código", "and enter the code")} <b>{codigo}</b></div>
<div style="opacity:.7;font-size:14px">{T("El celular tiene que estar en el mismo WiFi que esta PC.", "Your phone must be on the same WiFi as this PC.")}</div></body></html>""".encode()


def mostrar_qr_en_consola(url: str) -> None:
    try:
        import segno
        segno.make(url, error="m").terminal(compact=True, border=2)
    except Exception:
        pass  # si la consola no puede dibujarlo, queda la dirección escrita y el QR del ícono


# ---------- Páginas ----------

def pagina_inicial(seguro: bool, user_agent: str) -> str:
    """Qué archivo se muestra en "/" según la conexión (HTTP/HTTPS) y el celular (Android/iPhone)."""
    ios = bool(ES_IOS.search(user_agent or ""))
    if seguro:
        return "/iphone.html" if ios else "/index.html"
    return "/configurar-iphone.html" if ios else "/configurar.html"


def _panel(connection, ruta: str, consulta: str, seguro: bool, ctx: Contexto):
    """La ventana de la PC: la página, su estado (JSON) y sus acciones. Solo en esta PC y con la clave."""
    if seguro or connection.remote_address[0] not in ("127.0.0.1", "::1") or ctx.panel_clave is None:
        return connection.respond(403, "Solo desde la PC\n")
    if ruta == "/panel":
        return respuesta((ctx.web / "panel.html").read_bytes(), "text/html")
    datos = {k: v[0] for k, v in parse_qs(consulta).items()}
    if not secrets.compare_digest(datos.get("k", ""), ctx.panel_clave()):
        return connection.respond(403, "Clave equivocada\n")
    if ruta == "/panel/estado":
        return respuesta(json.dumps(ctx.panel_estado(), ensure_ascii=False).encode(), "application/json")
    if ruta == "/panel/accion":
        return respuesta(json.dumps(ctx.panel_accion(datos.get("que", ""), datos)).encode(), "application/json")
    return connection.respond(404, "No encontrado\n")


def servir_archivos(seguro: bool, ctx: Contexto):
    def atender_http(connection, request):
        if request.headers.get("Upgrade", "").lower() == "websocket":
            return None
        partes = urlsplit(request.path)
        ruta = partes.path
        if ruta == "/panel" or ruta.startswith("/panel/"):
            return _panel(connection, ruta, partes.query, seguro, ctx)
        if ruta == "/app.apk":  # la app de Android, desde la PC (para instalarla sin internet en el celular)
            for apk in (ctx.web.parent / "app" / "ControlCelular.apk", ctx.web.parent / "dist" / "ControlCelular.apk"):
                if apk.is_file():
                    return respuesta(apk.read_bytes(), "application/vnd.android.package-archive",
                                     [("Content-Disposition", 'attachment; filename="ControlCelular.apk"')])
            return connection.respond(404, "La app no viene en esta version\n")
        if ruta == "/qr-app.svg":  # para bajar la app de Android (no lleva nada privado)
            return respuesta(qr_svg(DESCARGA_APP), "image/svg+xml", cache="max-age=3600")
        if ruta in ("/qr", "/qr.svg"):
            # El QR lleva el código de emparejamiento: solo se muestra en esta misma PC.
            if connection.remote_address[0] not in ("127.0.0.1", "::1"):
                return connection.respond(403, "Solo desde la PC\n")
            if ruta == "/qr.svg":
                return respuesta(qr_svg(ctx.url_qr()), "image/svg+xml")
            return respuesta(pagina_qr(ctx.url_qr(), ctx.codigo()), "text/html")
        if ruta == "/juegos" or ruta.startswith("/portada/"):
            # La biblioteca es privada: solo para celulares emparejados.
            if not ctx.es_celular_emparejado(parse_qs(partes.query).get("t", [""])[0]):
                return connection.respond(403, "Sin permiso\n")
            if ruta == "/juegos":
                lista = [{k: j[k] for k in ("id", "nombre", "tipo")} for j in ctx.biblioteca()]
                cuerpo = json.dumps({"abierto": ctx.juego_abierto(), "juegos": lista}, ensure_ascii=False)
                return respuesta(cuerpo.encode("utf-8"), "application/json", PARA_LA_APP)
            numero = ruta.rsplit("/", 1)[1]
            p = steam.portada(int(numero)) if numero.isdigit() else None
            if not p:
                return connection.respond(404, "Sin portada\n")
            return respuesta(p.read_bytes(), "image/jpeg", PARA_LA_APP, cache="max-age=86400")
        if ruta == "/ca.crt":
            return respuesta(certs.ca_der(), "application/x-x509-ca-cert",
                             [("Content-Disposition", 'attachment; filename="control-celular-ca.crt"')])
        if ruta == "/ping":
            return respuesta(b"ok", "text/plain", [("Access-Control-Allow-Origin", "*")])
        if ruta == "/":
            ruta = pagina_inicial(seguro, request.headers.get("User-Agent", ""))
        archivo = (ctx.web / ruta.lstrip("/")).resolve()
        if ctx.web.resolve() not in archivo.parents or not archivo.is_file():
            return connection.respond(404, "No encontrado\n")
        tipo = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
        if archivo.suffix == ".webmanifest":
            tipo = "application/manifest+json"
        return respuesta(archivo.read_bytes(), tipo)
    return atender_http
