"""Cómo la app de Android encuentra la PC (faro) y el Bluetooth (pedazos, rearmado y la conexión de mentira)."""

import asyncio
import socket

import enlaces


def test_mensaje_del_faro_ida_y_vuelta():
    datos = enlaces.mensaje_faro(8765, "PC de  la casa")
    assert datos == b"CONTROLCELULAR 1 8765 PC de la casa"
    assert enlaces.leer_faro(datos) == (8765, "PC de la casa")
    assert enlaces.leer_faro(b"OTRA COSA") is None
    assert enlaces.leer_faro(b"CONTROLCELULAR 1 no-numero x") is None


def test_el_faro_llega_por_udp():
    async def prueba():
        receptor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receptor.bind(("127.0.0.1", 0))
        receptor.settimeout(3)
        puerto = receptor.getsockname()[1]
        original = enlaces.PUERTO_FARO
        enlaces.PUERTO_FARO = puerto
        try:
            tarea = asyncio.ensure_future(enlaces.faro(8765, "Mi PC", destinos=[("127.0.0.1", "127.0.0.1")], cada=.1))
            datos = await asyncio.to_thread(receptor.recvfrom, 200)
            tarea.cancel()
        finally:
            enlaces.PUERTO_FARO = original
            receptor.close()
        return datos

    datos, origen = asyncio.run(prueba())
    assert enlaces.leer_faro(datos) == (8765, "Mi PC") and origen[0] == "127.0.0.1"


def test_partir_y_rearmar():
    largo = "c " + "{\"x\": \"" + "á" * 300 + "\"}"
    pedazos = enlaces.partir(largo, 20)
    assert all(len(p) <= 20 for p in pedazos) and len(pedazos) > 10
    r = enlaces.Rearmador()
    mensajes = []
    for p in pedazos + enlaces.partir("b A 1", 20):
        mensajes += r.agregar(p)
    assert mensajes == [largo, "b A 1"]  # las letras con tilde no se rompen aunque se corten a la mitad


class ClienteFalso:
    mtu_size = 23

    def __init__(self):
        self.escrito, self.cerrado = [], False

    async def write_gatt_char(self, uuid, datos, response=None):
        assert uuid == enlaces.SALIDA
        self.escrito.append(bytes(datos))

    async def disconnect(self):
        self.cerrado = True


def test_conexion_bluetooth_se_comporta_como_el_websocket():
    async def prueba():
        cliente = ClienteFalso()
        c = enlaces.ConexionBT(cliente, "AA:BB:CC:DD:EE:FF")
        for p in enlaces.partir("a 1234", 4) + enlaces.partir("b A 1", 4):
            c.recibido(None, bytearray(p))
        primero = await c.recv()
        recibidos = []

        async def leer_todo():
            async for m in c:
                recibidos.append(m)

        lector = asyncio.ensure_future(leer_todo())
        await c.send("ok token-largo-de-prueba")
        await asyncio.sleep(.05)
        c.desconectado()
        await asyncio.wait_for(lector, 2)
        return primero, recibidos, cliente

    primero, recibidos, cliente = asyncio.run(prueba())
    assert primero == "a 1234" and recibidos == ["b A 1"]
    assert all(len(p) <= 20 for p in cliente.escrito)
    assert b"".join(cliente.escrito) == b"ok token-largo-de-prueba\n"


def test_un_celular_por_bluetooth_juega_igual_que_por_wifi():
    """El servidor de verdad atiende una conexión Bluetooth (sin radio): empareja, contesta y aprieta botones."""
    import server

    async def prueba():
        cliente = ClienteFalso()
        c = enlaces.ConexionBT(cliente, "AA:BB:CC:DD:EE:01")
        for m in (f"a {server.registro.codigo}", "d Celular BT", "b A 1"):
            for p in enlaces.partir(m, 20):
                c.recibido(None, bytearray(p))
        tarea = asyncio.ensure_future(server.atender(c))
        await asyncio.sleep(.3)
        jugador = next(j for j in server.jugadores.values() if j.ws is c)
        apretado = set(jugador.pad.botones)  # el control virtual (de mentira en las pruebas)
        estado = server.estado_panel()["jugadores"]
        c.desconectado()
        await asyncio.wait_for(tarea, 3)
        return cliente, apretado, estado

    cliente, apretado, estado = asyncio.run(prueba())
    respuestas = b"".join(cliente.escrito).decode().split("\n")
    assert respuestas[0].startswith("ok ")  # emparejado: la PC le dio su permiso
    assert any(r.startswith("n ") for r in respuestas)
    assert any(j.get("conexion") == "bluetooth" and j.get("nombre") == "Celular BT" for j in estado)
    assert len(apretado) == 1  # «b A 1» llegó por Bluetooth y apretó el botón A del control virtual
