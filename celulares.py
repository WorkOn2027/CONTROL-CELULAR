"""Celulares emparejados, sus ajustes, el código de emparejamiento y el límite de intentos.

Archivos (en la carpeta de datos):
  tokens.json   token -> {nombre, visto, mando}   (el formato viejo, una lista de tokens, se convierte solo)
  ajustes.json  {"celulares": {token: {clave: valor}}}   (valor None = borrado)
"""

import hashlib
import json
import secrets
import time
from pathlib import Path

# Cada 5 códigos equivocados desde un mismo equipo: bloqueo que se duplica (30 s, 1 min, 2 min... hasta 1 h).
# Si en 10 minutos hay 40 fallos en total (aunque vengan de varios equipos), el código cambia solo.
INTENTOS, BLOQUEO_BASE, BLOQUEO_MAX = 5, 30, 3600
FALLOS_PARA_CAMBIAR, VENTANA_FALLOS = 40, 600


def _leer_json(ruta: Path, vacio):
    try:
        return json.loads(ruta.read_text("utf-8"))
    except (OSError, ValueError):
        return vacio


def _guardar_json(ruta: Path, datos) -> None:
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False), "utf-8")
    tmp.replace(ruta)


def id_corto(token: str) -> str:
    """Identificador para mostrar o elegir un celular sin revelar su token."""
    return hashlib.sha256(token.encode()).hexdigest()[:10]


class Registro:
    def __init__(self, carpeta: Path, reloj=time.time):
        self.carpeta = Path(carpeta)
        self.archivo_tokens = self.carpeta / "tokens.json"
        self.archivo_ajustes = self.carpeta / "ajustes.json"
        self.reloj = reloj
        self.celulares: dict[str, dict] = self._cargar_celulares()
        self.ajustes: dict = self._cargar_ajustes()
        self.codigo = self._codigo_nuevo()
        self.fallos: dict[str, list] = {}  # ip -> [fallos seguidos, bloqueado hasta, veces bloqueado]
        self.fallos_recientes: list[float] = []
        self.al_cambiar_codigo = None     # se llama con el código nuevo cuando cambia solo
        self.al_bloquear = None           # se llama con (ip, segundos)

    # ---------- Carga y guardado ----------
    @staticmethod
    def _codigo_nuevo() -> str:
        return f"{secrets.randbelow(10000):04d}"

    def _cargar_celulares(self) -> dict[str, dict]:
        d = _leer_json(self.archivo_tokens, {})
        if isinstance(d, list):
            d = {t: {"nombre": f"Celular {i + 1}", "visto": 0} for i, t in enumerate(d)}
        return d if isinstance(d, dict) else {}

    def _cargar_ajustes(self) -> dict:
        """Si el archivo es del formato viejo (uno solo para toda la PC), no se le da a nadie: queda de respaldo.
        Cada celular tiene su propia copia y la vuelve a subir sola al conectarse."""
        d = _leer_json(self.archivo_ajustes, {})
        if not isinstance(d, dict) or "celulares" not in d:
            if d:
                _guardar_json(self.archivo_ajustes.with_name("ajustes-formato-viejo.json"), d)
            d = {"celulares": {}}
        return d

    def guardar_celulares(self) -> None:
        _guardar_json(self.archivo_tokens, self.celulares)

    def guardar_ajustes(self) -> None:
        _guardar_json(self.archivo_ajustes, self.ajustes)

    # ---------- Emparejamiento ----------
    def segundos_bloqueado(self, ip: str) -> int:
        f = self.fallos.get(ip)
        ahora = self.reloj()
        return max(0, int(f[1] - ahora) + 1) if f and ahora < f[1] else 0

    def anotar_fallo(self, ip: str) -> None:
        f = self.fallos.setdefault(ip, [0, 0.0, 0])
        f[0] += 1
        ahora = self.reloj()
        if f[0] >= INTENTOS:
            f[0], f[2] = 0, f[2] + 1
            espera = min(BLOQUEO_MAX, BLOQUEO_BASE * 2 ** (f[2] - 1))
            f[1] = ahora + espera
            if self.al_bloquear:
                self.al_bloquear(ip, espera)
        self.fallos_recientes.append(ahora)
        while self.fallos_recientes and ahora - self.fallos_recientes[0] > VENTANA_FALLOS:
            self.fallos_recientes.pop(0)
        if len(self.fallos_recientes) >= FALLOS_PARA_CAMBIAR:
            self.fallos_recientes.clear()
            self.codigo = self._codigo_nuevo()
            if self.al_cambiar_codigo:
                self.al_cambiar_codigo(self.codigo)

    def emparejar(self, clave: str, ip: str) -> tuple[str, str | int | None]:
        """Devuelve ("ok", token), ("no", None) o ("espera", segundos)."""
        if clave in self.celulares:
            token = clave
        else:
            espera = self.segundos_bloqueado(ip)
            if espera:
                return "espera", espera
            if clave != self.codigo:
                self.anotar_fallo(ip)
                return "no", None
            self.fallos.pop(ip, None)
            token = secrets.token_urlsafe(16)
            self.celulares[token] = {"nombre": "Celular", "visto": 0}
        self.celulares[token]["visto"] = int(self.reloj())
        self.guardar_celulares()
        return "ok", token

    # ---------- Datos de cada celular ----------
    def poner(self, token: str, clave: str, valor) -> bool:
        """Cambia un dato del celular (nombre, mando). Devuelve True si cambió."""
        info = self.celulares.get(token)
        if info is None or info.get(clave) == valor:
            return False
        info[clave] = valor
        self.guardar_celulares()
        return True

    def ajustes_de(self, token: str) -> dict:
        return self.ajustes["celulares"].setdefault(token, {})

    def guardar_ajuste(self, token: str, resto: str) -> None:
        """resto = "<clave> <valor>" (valor vacío = borrarlo)."""
        clave, _, valor = resto.partition(" ")
        if not clave or len(clave) > 100 or len(valor) > 200_000:
            return
        self.ajustes_de(token)[clave] = valor if valor != "" else None
        self.guardar_ajustes()

    def otros(self, token: str) -> list[dict]:
        """Los demás celulares que tienen ajustes guardados (para copiarlos)."""
        lista = []
        for t, info in self.celulares.items():
            a = self.ajustes["celulares"].get(t) or {}
            if t != token and any(v is not None for v in a.values()):
                lista.append({"id": id_corto(t), "nombre": info.get("nombre") or "Celular",
                              "visto": info.get("visto", 0)})
        return sorted(lista, key=lambda c: -c["visto"])

    def copiar(self, token: str, id_origen: str) -> bool:
        origen = next((t for t in self.celulares if id_corto(t) == id_origen and t != token), None)
        if origen is None:
            return False
        self.ajustes["celulares"][token] = dict(self.ajustes["celulares"].get(origen) or {})
        self.guardar_ajustes()
        return True

    def lista(self, conectados: set[str]) -> list[dict]:
        return sorted(({"id": id_corto(t), "nombre": i.get("nombre") or "Celular", "visto": i.get("visto", 0),
                        "conectado": t in conectados} for t, i in self.celulares.items()),
                      key=lambda c: -c["visto"])

    def olvidar(self, ids: set[str] | None) -> list[str]:
        """Saca celulares (None = todos): pierden el permiso y sus ajustes. Devuelve los tokens olvidados."""
        objetivo = [t for t in self.celulares if ids is None or id_corto(t) in ids]
        for t in objetivo:
            self.celulares.pop(t, None)
            self.ajustes["celulares"].pop(t, None)
        self.guardar_celulares()
        self.guardar_ajustes()
        return objetivo
