package com.scamshield.app.net

import org.json.JSONObject
import java.io.DataInputStream
import java.io.EOFException
import java.net.InetSocketAddress
import java.net.Socket
import java.nio.ByteBuffer
import java.util.zip.CRC32

/**
 * Kotlin implementation of SSP, the ScamShield Protocol (same wire format as scamshield/net/protocol.py):
 *
 *   MAGIC 'SS' | VER | TYPE | FLAGS | WIN | SEQ(u32) | ACK(u32) | LEN(u16) | PAYLOAD | CRC-32 (IEEE 802.3)
 */
object Ssp {
    const val MAGIC = 0x5353
    const val VERSION = 1
    const val HEADER = 16
    const val CLASSIFY_REQ = 1
    const val CLASSIFY_RESP = 2
    const val PING = 5
    const val PONG = 6
    const val ERROR = 7
    const val FLAG_JSON = 8

    data class Frame(val type: Int, val flags: Int, val window: Int, val seq: Long, val ack: Long,
                     val payload: ByteArray, val crc: Long, val raw: ByteArray) {
        fun json() = JSONObject(String(payload, Charsets.UTF_8))
    }

    fun encode(type: Int, payload: ByteArray, seq: Long, flags: Int = 0, ack: Long = 0, window: Int = 0): ByteArray {
        val buf = ByteBuffer.allocate(HEADER + payload.size + 4)
        buf.putShort(MAGIC.toShort()).put(VERSION.toByte()).put(type.toByte()).put(flags.toByte()).put(window.toByte())
            .putInt(seq.toInt()).putInt(ack.toInt()).putShort(payload.size.toShort()).put(payload)
        val crc = CRC32().apply { update(buf.array(), 0, HEADER + payload.size) }.value
        buf.putInt(crc.toInt())
        return buf.array()
    }

    fun encodeJson(type: Int, obj: JSONObject, seq: Long) =
        encode(type, obj.toString().toByteArray(Charsets.UTF_8), seq, FLAG_JSON)

    class CorruptFrame(msg: String) : Exception(msg)

    fun read(input: DataInputStream): Frame {
        val head = ByteArray(HEADER)
        input.readFully(head)
        val b = ByteBuffer.wrap(head)
        val magic = b.short.toInt() and 0xFFFF
        if (magic != MAGIC) throw CorruptFrame("bad magic")
        b.get()
        val type = b.get().toInt() and 0xFF
        val flags = b.get().toInt() and 0xFF
        val win = b.get().toInt() and 0xFF
        val seq = b.int.toLong() and 0xFFFFFFFFL
        val ack = b.int.toLong() and 0xFFFFFFFFL
        val len = b.short.toInt() and 0xFFFF
        val payload = ByteArray(len)
        input.readFully(payload)
        val crc = input.readInt().toLong() and 0xFFFFFFFFL
        val calc = CRC32().apply { update(head); update(payload) }.value
        if (calc != crc) throw CorruptFrame("CRC mismatch")
        return Frame(type, flags, win, seq, ack, payload, crc, head + payload)
    }

    fun hex(bytes: ByteArray, max: Int = 32) =
        bytes.take(max).joinToString(" ") { "%02x".format(it) } + if (bytes.size > max) " …" else ""
}

/** Blocking TCP client for the ScamShield server (call from a background thread). */
class SspClient(private val host: String, private val port: Int, private val timeoutMs: Int = 4000) {
    data class Result(val response: JSONObject, val rttMs: Double, val requestFrame: ByteArray, val responseFrame: Ssp.Frame)

    private var seq = 1L

    private fun <T> withSocket(block: (Socket, DataInputStream) -> T): T {
        Socket().use { s ->
            s.tcpNoDelay = true
            s.soTimeout = timeoutMs
            s.connect(InetSocketAddress(host, port), timeoutMs)
            return block(s, DataInputStream(s.getInputStream()))
        }
    }

    fun ping(): Double = withSocket { s, input ->
        val t0 = System.nanoTime()
        s.getOutputStream().write(Ssp.encode(Ssp.PING, "x".toByteArray(), seq++))
        val f = Ssp.read(input)
        if (f.type != Ssp.PONG) throw EOFException("unexpected frame ${f.type}")
        (System.nanoTime() - t0) / 1e6
    }

    fun classify(text: String): Result = withSocket { s, input ->
        val req = JSONObject().put("id", seq).put("text", text).put("explain", true).put("dns", true)
        val frame = Ssp.encodeJson(Ssp.CLASSIFY_REQ, req, seq++)
        val t0 = System.nanoTime()
        s.getOutputStream().write(frame)
        val f = Ssp.read(input)
        val rtt = (System.nanoTime() - t0) / 1e6
        if (f.type != Ssp.CLASSIFY_RESP) throw EOFException("server error: ${String(f.payload)}")
        Result(f.json(), rtt, frame, f)
    }
}
