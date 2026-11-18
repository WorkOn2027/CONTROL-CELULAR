package io.github.markbackend.controlcelular

import android.content.Context
import android.net.wifi.WifiManager
import android.os.SystemClock
import org.json.JSONArray
import org.json.JSONObject
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetSocketAddress
import java.util.concurrent.ConcurrentHashMap
import kotlin.concurrent.thread

/**
 * Escucha el aviso de la PC («CONTROLCELULAR 1 <puerto> <nombre>», cada segundo por UDP, puerto 8766).
 * Llega por el WiFi y también por el cable USB (con «Anclaje USB» el cable arma una red propia entre los dos).
 */
class Buscador(contexto: Context) {

    data class Pc(val ip: String, val puerto: Int, val nombre: String, val visto: Long)

    private val pcs = ConcurrentHashMap<String, Pc>()
    @Volatile private var activo = false
    @Volatile private var socket: DatagramSocket? = null
    private val candado = (contexto.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager)
        .createMulticastLock("controlcelular").apply { setReferenceCounted(false) }

    fun empezar() {
        if (activo) return
        activo = true
        try { candado.acquire() } catch (e: Exception) { }
        thread(name = "buscador", isDaemon = true) { escuchar() }
    }

    fun parar() {
        activo = false
        socket?.close()
        try { if (candado.isHeld) candado.release() } catch (e: Exception) { }
    }

    private fun escuchar() {
        try {
            val s = DatagramSocket(null)
            socket = s
            s.reuseAddress = true
            s.broadcast = true
            s.bind(InetSocketAddress(Protocolo.PUERTO_FARO))
            val buffer = ByteArray(512)
            while (activo) {
                val paquete = DatagramPacket(buffer, buffer.size)
                s.receive(paquete)
                val partes = String(paquete.data, 0, paquete.length, Charsets.UTF_8).split(" ", limit = 4)
                if (partes.size < 3 || partes[0] != "CONTROLCELULAR" || partes[1] != "1") continue
                val puerto = partes[2].toIntOrNull() ?: continue
                val ip = paquete.address?.hostAddress ?: continue
                pcs[ip] = Pc(ip, puerto, partes.getOrElse(3) { "PC" }, SystemClock.elapsedRealtime())
            }
        } catch (e: Exception) {
            // se cerró (la app pasó a segundo plano) o el puerto está ocupado: se vuelve a abrir al volver
        } finally {
            socket?.close()
        }
    }

    /** Las PCs que avisaron en los últimos 4 segundos, para la pantalla «Conectá con tu PC». */
    fun lista(): String {
        val ahora = SystemClock.elapsedRealtime()
        val arreglo = JSONArray()
        pcs.values.filter { ahora - it.visto < 4000 }.sortedBy { it.nombre }.forEach {
            arreglo.put(JSONObject().put("ip", it.ip).put("puerto", it.puerto).put("nombre", it.nombre))
        }
        return arreglo.toString()
    }
}
