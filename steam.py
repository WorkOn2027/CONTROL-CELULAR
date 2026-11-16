"""Lee la biblioteca de Steam de esta PC (solo archivos locales, nada se manda a internet).

- Juegos instalados: steamapps/appmanifest_*.acf de cada biblioteca (libraryfolders.vdf).
- Nombre y etiquetas de la tienda (Carreras, Disparos...): appcache/appinfo.vdf (formato binario v28/v29).
- Portadas: appcache/librarycache/<appid>/header.jpg
- Juego abierto: el proceso que corre desde steamapps/common/<carpeta del juego>.
"""

import re
import struct
import winreg
from pathlib import Path


def carpeta_steam() -> Path | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            return Path(winreg.QueryValueEx(k, "SteamPath")[0])
    except OSError:
        return None


def bibliotecas(steam: Path) -> list[Path]:
    libs = [steam / "steamapps"]
    try:
        texto = (steam / "steamapps" / "libraryfolders.vdf").read_text("utf-8", "replace")
        for ruta in re.findall(r'"path"\s+"([^"]+)"', texto):
            p = Path(ruta.replace("\\\\", "\\")) / "steamapps"
            if p not in libs:
                libs.append(p)
    except OSError:
        pass
    return [p for p in libs if p.is_dir()]


# ---------- appinfo.vdf ----------

def _cstr(datos: bytes, i: int) -> tuple[str, int]:
    fin = datos.index(b"\0", i)
    return datos[i:fin].decode("utf-8", "replace"), fin + 1


def _kv(datos: bytes, i: int, tabla: list[str] | None) -> tuple[dict, int]:
    """Key-values binarios de Valve. En v29 las claves son índices a una tabla de textos."""
    res = {}
    while True:
        tipo = datos[i]; i += 1
        if tipo == 0x08:
            return res, i
        if tabla is not None:
            clave = tabla[struct.unpack_from("<I", datos, i)[0]]; i += 4
        else:
            clave, i = _cstr(datos, i)
        if tipo == 0x00:
            res[clave], i = _kv(datos, i, tabla)
        elif tipo == 0x01:
            res[clave], i = _cstr(datos, i)
        elif tipo in (0x02, 0x06):
            res[clave] = struct.unpack_from("<i", datos, i)[0]; i += 4
        elif tipo == 0x03:
            res[clave] = struct.unpack_from("<f", datos, i)[0]; i += 4
        elif tipo in (0x07, 0x0A):
            res[clave] = struct.unpack_from("<Q", datos, i)[0]; i += 8
        else:
            raise ValueError(f"tipo desconocido {tipo:#x}")


def leer_appinfo(steam: Path, quiero: set[int]) -> dict[int, dict]:
    """Devuelve {appid: sección 'common'} solo para los juegos pedidos."""
    try:
        datos = (steam / "appcache" / "appinfo.vdf").read_bytes()
    except OSError:
        return {}
    magia = struct.unpack_from("<I", datos, 0)[0]
    if magia not in (0x07564428, 0x07564429):
        return {}
    tabla, i = None, 8
    if magia == 0x07564429:
        pos = struct.unpack_from("<q", datos, 8)[0]; i = 16
        cant = struct.unpack_from("<I", datos, pos)[0]; j = pos + 4
        tabla = []
        for _ in range(cant):
            s, j = _cstr(datos, j)
            tabla.append(s)
    res = {}
    while i + 8 <= len(datos):
        appid, tam = struct.unpack_from("<II", datos, i)
        if appid == 0:
            break
        inicio = i + 8
        if appid in quiero:
            try:
                kv, _ = _kv(datos, inicio + 60, tabla)
                res[appid] = kv.get("appinfo", kv).get("common", {})
            except (ValueError, IndexError, struct.error):
                pass
        i = inicio + tam
    return res


# ---------- Tipo de juego ----------

# Etiquetas de la tienda de Steam (id -> tipo de control). La primera que coincide manda.
ETIQUETAS = [
    ("carreras", {699, 1644}),                 # Racing, Driving
    ("pelea", {1743, 4158}),                   # Fighting, Beat 'em up
    ("deportes", {701, 1254}),                 # Sports, Soccer (antes que disparos: muchos tienen "Shooter")
    ("disparos", {1663, 3814, 1774}),          # FPS, Third-Person Shooter, Shooter
    ("plataformas", {1625}),                   # Platformer
    ("estrategia", {9, 1677}),                 # Strategy, Turn-Based
]
PALABRAS = [
    ("carreras", r"racing|kart|forza|drive|rally|speed|f1\b|moto"),
    ("pelea", r"tekken|street fighter|mortal kombat|smash|fighter"),
    ("disparos", r"call of duty|counter-strike|doom|halo|battlefield|shooter|helldivers|fortress|space marine"),
    ("deportes", r"fifa|fc \d|nba|pes|rematch|rocket league|golf|tennis"),
]


def tipo_de(nombre: str, common: dict) -> str:
    tags = set()
    for clave in ("store_tags", "genres"):
        valores = common.get(clave, {})
        if isinstance(valores, dict):
            tags |= {int(v) for v in valores.values() if str(v).isdigit()}
    for tipo, ids in ETIQUETAS:
        if tags & ids:
            return tipo
    for tipo, patron in PALABRAS:
        if re.search(patron, nombre, re.I):
            return tipo
    return "accion"


# ---------- Biblioteca ----------

NO_JUEGOS = {228980, 431960}  # Redistributables, Wallpaper Engine


def juegos() -> list[dict]:
    steam = carpeta_steam()
    if not steam:
        return []
    instalados = {}
    for lib in bibliotecas(steam):
        for acf in lib.glob("appmanifest_*.acf"):
            t = acf.read_text("utf-8", "replace")
            m = re.search(r'"appid"\s+"(\d+)"', t)
            if not m:
                continue
            appid = int(m.group(1))
            carpeta = re.search(r'"installdir"\s+"([^"]+)"', t)
            nombre = re.search(r'"name"\s+"([^"]+)"', t)
            instalados[appid] = {
                "nombre": nombre.group(1) if nombre else "",
                "carpeta": str(lib / "common" / carpeta.group(1)) if carpeta else "",
            }
    info = leer_appinfo(steam, set(instalados))
    lista = []
    for appid, d in instalados.items():
        c = info.get(appid, {})
        if appid in NO_JUEGOS or str(c.get("type", "game")).lower() not in ("game", "demo"):
            continue
        nombre = c.get("name") or d["nombre"]
        if not nombre or nombre.startswith("appid_"):
            continue
        lista.append({"id": appid, "nombre": nombre, "tipo": tipo_de(nombre, c),
                      "mando": str(c.get("controller_support", "")), "carpeta": d["carpeta"]})
    lista.sort(key=lambda j: j["nombre"].lower())
    return lista


def portada(appid: int) -> Path | None:
    steam = carpeta_steam()
    if not steam:
        return None
    cache = steam / "appcache" / "librarycache"
    carpeta = cache / str(appid)
    viejo = cache / f"{appid}_header.jpg"
    if viejo.is_file():
        return viejo
    if not carpeta.is_dir():
        return None
    # Steam nuevo guarda cada imagen en una subcarpeta con nombre de hash. De mejor a peor opción:
    for nombre in ("header.jpg", "library_header.jpg", "library_hero.jpg"):
        for p in [carpeta / nombre, *carpeta.glob(f"*/{nombre}")]:
            if p.is_file():
                return p
    return None


def juego_abierto(lista: list[dict]) -> int | None:
    """El juego que está corriendo ahora (por la carpeta del ejecutable)."""
    import ctypes
    from ctypes import wintypes
    carpetas = {j["carpeta"].lower(): j["id"] for j in lista if j["carpeta"]}
    k32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    ids = (wintypes.DWORD * 4096)()
    usados = wintypes.DWORD()
    if not psapi.EnumProcesses(ids, ctypes.sizeof(ids), ctypes.byref(usados)):
        return None
    buf = ctypes.create_unicode_buffer(1024)
    for pid in ids[: usados.value // 4]:
        h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            continue
        try:
            n = wintypes.DWORD(1024)
            if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                ruta = buf.value.lower()
                for carpeta, appid in carpetas.items():
                    if ruta.startswith(carpeta + "\\"):
                        return appid
        finally:
            k32.CloseHandle(h)
    return None


if __name__ == "__main__":
    lista = juegos()
    abierto = juego_abierto(lista)
    for j in lista:
        print(f"{j['id']:>8}  {j['tipo']:<12} {j['mando']:<8} {'<- ABIERTO' if j['id'] == abierto else '':<10} {j['nombre']}")
