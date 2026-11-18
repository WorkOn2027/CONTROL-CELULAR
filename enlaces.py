"""Cómo encuentra y se conecta la app de Android con la PC, además del navegador.

- **Faro (WiFi y cable USB):** cada segundo la PC avisa por UDP, en cada placa de red, «acá está Control Celular».
  La app lo escucha y se conecta sola al WebSocket de siempre (puerto 8765), sin escribir direcciones. Con el
  «Anclaje USB» del celular, el cable arma una red propia entre los dos: el faro sale también por ahí, así que anda
  aunque el router no deje que los equipos se vean.
- **Bluetooth LE:** la app se anuncia con el servicio de Control Celular; la PC la encuentra, se conecta y la trata
  igual que a un celular por WiFi (`ConexionBT` se comporta como el WebSocket). Los mensajes son los mismos, cada
  uno terminado en «\\n» y partido en pedazos del tamaño que permite el Bluetooth.

Para las pruebas: CONTROL_SIN_FARO=1 y CONTROL_SIN_BLUETOOTH=1 los apagan.
"""

import asyncio
import os
import socket

# Los mismos números están en la app de Android (Conexion.kt): si se cambian acá, hay que cambiarlos allá.
PUERTO_FARO = 8766
SERVICIO = "6f1c2e5a-7b3d-4c8e-9a21-c0e7a11e0001"
ENTRADA = "6f1c2e5a-7b3d-4c8e-9a21-c0e7a11e0002"  # celular → PC (notificaciones)
SALIDA = "6f1c2e5a-7b3d-4c8e-9a21-c0e7a11e0003"   # PC → celular (escritura)


# ---------- Faro ----------

def mensaje_faro(puerto: int, nombre: str) -> bytes:
    nombre = " ".join(nombre.split())[:40] or "PC"
    return f"CONTROLCELULAR 1 {puerto} {nombre}".encode()


def leer_faro(datos: bytes) -> tuple[int, str] | None:
    """(puerto, nombre de la PC) si es un aviso de Control Celular; si no, None."""
    try:
        partes = datos.decode("utf-8", "replace").split(" ", 3)
        if len(partes) >= 3 and partes[0] == "CONTROLCELULAR" and partes[1] == "1":
            return int(partes[2]), (partes[3] if len(partes) > 3 else "PC")
    except ValueError:
        pass
    return None


def ips_locales() -> list[str]:
    """Las direcciones IPv4 de esta PC en cada placa de red (incluida la del cable USB, cuando está)."""
    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith(("127.", "169.254.")))


async def faro(puerto: int, nombre: str | None = None, destinos=None, cada: float = 1.0) -> None:
    """Avisa para siempre que Control Celular está acá. `destinos` (para las pruebas) reemplaza a la difusión."""
    nombre = nombre or socket.gethostname()
    datos = mensaje_faro(puerto, nombre)
    while True:
        objetivos = destinos if destinos is not None else [(ip, "255.255.255.255") for ip in ips_locales()]
        for local, destino in objetivos:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    s.bind((local, 0))  # sale por esa placa de red
                    s.sendto(datos, (destino, PUERTO_FARO))
                    if destino == "255.255.255.255" and local.count(".") == 3:  # y a la red /24, por las dudas
                        s.sendto(datos, (local.rsplit(".", 1)[0] + ".255", PUERTO_FARO))
            except OSError:
                pass  # una placa que se fue (desenchufaron el cable): sigue con las demás
        await asyncio.sleep(cada)


# ---------- Bluetooth LE ----------

def partir(texto: str, tam: int) -> list[bytes]:
    """Un mensaje (con su «\\n» al final) en pedazos de `tam` bytes como mucho."""
    datos = (texto + "\n").encode("utf-8")
    tam = max(1, tam)
    return [datos[i:i + tam] for i in range(0, len(datos), tam)]


class Rearmador:
    """Junta los pedazos que llegan por Bluetooth y devuelve los mensajes completos."""

    def __init__(self):
        self._resto = b""

    def agregar(self, pedazo: bytes) -> list[str]:
        self._resto += bytes(pedazo)
        *completos, self._resto = self._resto.split(b"\n")
        return [m.decode("utf-8", "replace") for m in completos if m]


class _Cerrada(Exception):
    pass


class ConexionBT:
    """Un celular conectado por Bluetooth, con la misma forma que el WebSocket (recv, send, close, async for)."""

    tipo = "bluetooth"

    def __init__(self, cliente, direccion: str):
        self._cliente = cliente
        self.remote_address = (direccion, 0)
        self._cola: asyncio.Queue = asyncio.Queue()
        self._rearmar = Rearmador()
        self._cerrada = False

    # El Bluetooth avisa que llegó algo (lo llama bleak)
    def recibido(self, _caracteristica, datos: bytearray) -> None:
        for m in self._rearmar.agregar(datos):
            self._cola.put_nowait(m)

    def desconectado(self, *_):
        self._cerrada = True
        self._cola.put_nowait(_Cerrada())

    async def recv(self) -> str:
        m = await self._cola.get()
        if isinstance(m, _Cerrada):
            self._cola.put_nowait(m)  # que lo vean también los que esperen después
            raise ConnectionError("Bluetooth desconectado")
        return m

    def __aiter__(self):
        return self

    async def __anext__(self) -> str:
        try:
            return await self.recv()
        except ConnectionError:
            raise StopAsyncIteration

    async def send(self, texto: str) -> None:
        if self._cerrada:
            raise ConnectionError("Bluetooth desconectado")
        tam = max(20, (getattr(self._cliente, "mtu_size", 23) or 23) - 3)
        for pedazo in partir(texto, tam):
            await self._cliente.write_gatt_char(SALIDA, pedazo, response=True)

    async def close(self) -> None:
        if not self._cerrada:
            self._cerrada = True
            try:
                await self._cliente.disconnect()
            except Exception:
                pass
            self._cola.put_nowait(_Cerrada())


class Bluetooth:
    """Busca celulares con la app abierta (anunciando el servicio de Control Celular) y se les conecta."""

    def __init__(self):
        self.estado = "apagado"  # apagado | buscando | sin-bluetooth | sin-libreria
        self._conectados: dict[str, ConexionBT] = {}

    async def correr(self, atender) -> None:
        try:
            from bleak import BleakClient, BleakScanner
        except Exception:
            self.estado = "sin-libreria"
            return
        while True:
            try:
                encontrados = await BleakScanner.discover(timeout=4.0, service_uuids=[SERVICIO])
                self.estado = "buscando"
            except Exception:  # la PC no tiene Bluetooth (o está apagado): se reintenta cada tanto
                self.estado = "sin-bluetooth"
                await asyncio.sleep(20)
                continue
            for disp in encontrados:
                if disp.address not in self._conectados:
                    asyncio.ensure_future(self._conectar(disp, atender, BleakClient))
            await asyncio.sleep(1.5)

    async def _conectar(self, disp, atender, BleakClient) -> None:
        conexion = None
        try:
            cliente = BleakClient(disp, disconnected_callback=lambda c: conexion and conexion.desconectado())
            conexion = ConexionBT(cliente, disp.address)
            self._conectados[disp.address] = conexion
            await cliente.connect()
            await cliente.start_notify(ENTRADA, conexion.recibido)
            await atender(conexion)
        except Exception:
            pass
        finally:
            if conexion is not None:
                await conexion.close()
            self._conectados.pop(disp.address, None)


def faro_activado() -> bool:
    return os.environ.get("CONTROL_SIN_FARO") != "1"


def bluetooth_activado() -> bool:
    return os.environ.get("CONTROL_SIN_BLUETOOTH") != "1"

