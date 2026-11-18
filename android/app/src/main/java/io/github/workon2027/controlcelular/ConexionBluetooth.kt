package io.github.workon2027.controlcelular

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothGattServer
import android.bluetooth.BluetoothGattServerCallback
import android.bluetooth.BluetoothGattService
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.BluetoothLeAdvertiser
import android.content.Context
import android.os.Build
import android.os.ParcelUuid
import java.io.ByteArrayOutputStream
import java.util.UUID

/**
 * Bluetooth LE: el celular se anuncia con el servicio de Control Celular y la PC (enlaces.py) se le conecta.
 *  - ENTRADA (celular → PC): notificaciones. Cuando la PC se suscribe, la conexión está lista ("open").
 *  - SALIDA (PC → celular): la PC escribe ahí.
 * Cada mensaje termina en "\n" y se parte en pedazos del tamaño que permite el Bluetooth (MTU).
 * Los permisos (Android 12+) y prender el Bluetooth los pide MainActivity antes de crear esta conexión.
 */
@SuppressLint("MissingPermission")
class ConexionBluetooth(private val contexto: Context, private val eventos: Eventos) : Conexion {

    private val manager = contexto.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
    private var servidor: BluetoothGattServer? = null
    private var anunciador: BluetoothLeAdvertiser? = null
    @Volatile private var pc: BluetoothDevice? = null
    @Volatile private var lista = false
    @Volatile private var cerrada = false
    @Volatile private var mtu = 23
    private val cola = ArrayDeque<ByteArray>()
    private var enviando = false
    private val llegando = ByteArrayOutputStream()

    private val entrada = BluetoothGattCharacteristic(
        Protocolo.ENTRADA,
        BluetoothGattCharacteristic.PROPERTY_NOTIFY or BluetoothGattCharacteristic.PROPERTY_READ,
        BluetoothGattCharacteristic.PERMISSION_READ
    ).apply {
        addDescriptor(BluetoothGattDescriptor(CCCD,
            BluetoothGattDescriptor.PERMISSION_READ or BluetoothGattDescriptor.PERMISSION_WRITE))
    }
    private val salida = BluetoothGattCharacteristic(
        Protocolo.SALIDA,
        BluetoothGattCharacteristic.PROPERTY_WRITE or BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE,
        BluetoothGattCharacteristic.PERMISSION_WRITE
    )

    /** Empieza a anunciarse. Devuelve un texto de error para la persona, o null si arrancó bien. */
    fun empezar(): String? {
        val adaptador = manager.adapter ?: return contexto.getString(R.string.sin_bluetooth)
        if (!adaptador.isEnabled) return contexto.getString(R.string.prender_bluetooth)
        anunciador = adaptador.bluetoothLeAdvertiser ?: return contexto.getString(R.string.sin_anuncio)
        servidor = manager.openGattServer(contexto, retorno) ?: return contexto.getString(R.string.sin_bluetooth)
        val servicio = BluetoothGattService(Protocolo.SERVICIO, BluetoothGattService.SERVICE_TYPE_PRIMARY)
        servicio.addCharacteristic(entrada)
        servicio.addCharacteristic(salida)
        servidor!!.addService(servicio)  // al terminar (onServiceAdded) empieza a anunciarse
        return null
    }

    private fun anunciar() {
        if (cerrada) return
        val ajustes = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .setConnectable(true)
            .setTimeout(0)
            .build()
        val datos = AdvertiseData.Builder()
            .setIncludeDeviceName(false)
            .addServiceUuid(ParcelUuid(Protocolo.SERVICIO))
            .build()
        try {
            anunciador?.stopAdvertising(alAnunciar)
            anunciador?.startAdvertising(ajustes, datos, alAnunciar)
        } catch (e: Exception) {
            eventos("error", contexto.getString(R.string.sin_anuncio))
        }
    }

    private val alAnunciar = object : AdvertiseCallback() {
        override fun onStartFailure(errorCode: Int) {
            if (errorCode != ADVERTISE_FAILED_ALREADY_STARTED) eventos("error", contexto.getString(R.string.sin_anuncio))
        }
    }

    private val retorno = object : BluetoothGattServerCallback() {
        override fun onServiceAdded(status: Int, service: BluetoothGattService) {
            if (status == BluetoothGatt.GATT_SUCCESS) anunciar()
            else eventos("error", contexto.getString(R.string.sin_bluetooth))
        }

        override fun onConnectionStateChange(device: BluetoothDevice, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_DISCONNECTED && device.address == pc?.address) {
                pc = null
                lista = false
                synchronized(cola) { cola.clear(); enviando = false }
                eventos("close", "")
                anunciar()  // para que la PC se pueda volver a conectar
            }
        }

        override fun onMtuChanged(device: BluetoothDevice, nuevo: Int) {
            mtu = nuevo
        }

        override fun onDescriptorWriteRequest(device: BluetoothDevice, requestId: Int, descriptor: BluetoothGattDescriptor,
                                              preparedWrite: Boolean, responseNeeded: Boolean, offset: Int, value: ByteArray?) {
            if (responseNeeded) servidor?.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, null)
            if (descriptor.uuid == CCCD && value != null &&
                value.contentEquals(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)) {
                pc = device  // la PC se suscribió: ya se puede hablar
                lista = true
                eventos("open", "")
            }
        }

        override fun onCharacteristicWriteRequest(device: BluetoothDevice, requestId: Int, characteristic: BluetoothGattCharacteristic,
                                                  preparedWrite: Boolean, responseNeeded: Boolean, offset: Int, value: ByteArray?) {
            if (responseNeeded) servidor?.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, null)
            if (characteristic.uuid != Protocolo.SALIDA || value == null) return
            val completos = mutableListOf<String>()
            synchronized(llegando) {
                for (b in value) {
                    if (b == '\n'.code.toByte()) {
                        if (llegando.size() > 0) completos.add(llegando.toString("UTF-8"))
                        llegando.reset()
                    } else llegando.write(b.toInt())
                }
            }
            completos.forEach { eventos("msg", it) }
        }

        override fun onCharacteristicReadRequest(device: BluetoothDevice, requestId: Int, offset: Int,
                                                 characteristic: BluetoothGattCharacteristic) {
            servidor?.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, ByteArray(0))
        }

        override fun onNotificationSent(device: BluetoothDevice, status: Int) {
            synchronized(cola) { enviando = false }
            siguiente()
        }
    }

    override fun enviar(mensaje: String) {
        if (!lista) return
        val datos = (mensaje + "\n").toByteArray(Charsets.UTF_8)
        val tam = (mtu - 3).coerceAtLeast(20)
        synchronized(cola) {
            var i = 0
            while (i < datos.size) {
                cola.addLast(datos.copyOfRange(i, minOf(i + tam, datos.size)))
                i += tam
            }
        }
        siguiente()
    }

    /** Las notificaciones salen de a una: la próxima, cuando el Bluetooth avisa que mandó la anterior. */
    private fun siguiente() {
        val destino = pc ?: return
        val pedazo: ByteArray
        synchronized(cola) {
            if (enviando || cola.isEmpty()) return
            pedazo = cola.removeFirst()
            enviando = true
        }
        val ok = try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                servidor?.notifyCharacteristicChanged(destino, entrada, false, pedazo) == BluetoothGatt.GATT_SUCCESS
            } else {
                @Suppress("DEPRECATION")
                entrada.value = pedazo
                @Suppress("DEPRECATION")
                servidor?.notifyCharacteristicChanged(destino, entrada, false) == true
            }
        } catch (e: Exception) {
            false
        }
        if (!ok) synchronized(cola) { enviando = false }
    }

    override fun cerrar() {
        cerrada = true
        lista = false
        try { anunciador?.stopAdvertising(alAnunciar) } catch (e: Exception) { }
        try { pc?.let { servidor?.cancelConnection(it) } } catch (e: Exception) { }
        try { servidor?.close() } catch (e: Exception) { }
        servidor = null
    }

    companion object {
        private val CCCD: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
    }
}
