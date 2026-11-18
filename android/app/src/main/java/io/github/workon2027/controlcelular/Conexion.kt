package io.github.workon2027.controlcelular

import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.UUID
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

/** Una conexión con la PC. Avisa con eventos: "open", "msg" (con el mensaje) y "close". */
interface Conexion {
    fun enviar(mensaje: String)
    fun cerrar()
}

typealias Eventos = (tipo: String, dato: String) -> Unit

/** Los mismos números que usa la PC (enlaces.py): si se cambian acá, hay que cambiarlos allá. */
object Protocolo {
    const val PUERTO_FARO = 8766
    val SERVICIO: UUID = UUID.fromString("6f1c2e5a-7b3d-4c8e-9a21-c0e7a11e0001")
    val ENTRADA: UUID = UUID.fromString("6f1c2e5a-7b3d-4c8e-9a21-c0e7a11e0002")  // celular → PC
    val SALIDA: UUID = UUID.fromString("6f1c2e5a-7b3d-4c8e-9a21-c0e7a11e0003")   // PC → celular
}

/** WiFi o cable USB: el WebSocket de siempre, al puerto 8765 de la PC. */
class ConexionRed(url: String, private val eventos: Eventos) : Conexion {
    private val cerrado = AtomicBoolean(false)
    private val socket: WebSocket = cliente.newWebSocket(Request.Builder().url(url).build(), object : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) = eventos("open", "")
        override fun onMessage(webSocket: WebSocket, text: String) = eventos("msg", text)
        override fun onClosed(webSocket: WebSocket, code: Int, reason: String) = terminar()
        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) = terminar()
    })

    private fun terminar() {
        if (cerrado.compareAndSet(false, true)) eventos("close", "")
    }

    override fun enviar(mensaje: String) {
        socket.send(mensaje)
    }

    override fun cerrar() {
        cerrado.set(true)
        socket.close(1000, null)
    }

    companion object {
        private val cliente = OkHttpClient.Builder()
            .connectTimeout(4, TimeUnit.SECONDS)
            .readTimeout(0, TimeUnit.MILLISECONDS)
            .build()
    }
}
