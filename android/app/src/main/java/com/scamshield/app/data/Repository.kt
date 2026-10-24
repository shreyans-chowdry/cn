package com.scamshield.app.data

import android.content.Context
import android.content.SharedPreferences
import com.scamshield.app.detector.Analysis
import com.scamshield.app.detector.Detector
import com.scamshield.app.detector.Verdict
import com.scamshield.app.net.SspClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

data class HistoryItem(
    val id: Long, val sender: String, val text: String, val verdict: Verdict, val scamProb: Double,
    val language: String, val time: Long, val source: String, val reasons: List<String>,
)

data class Settings(
    val serverMode: Boolean = false, val host: String = "192.168.1.10", val port: Int = 9099,
    val dnsChecks: Boolean = true, val notifyPromos: Boolean = false,
)

/** App-wide state: the on-device model, settings and the history of checked messages. */
class Repository private constructor(private val ctx: Context) {
    companion object {
        @Volatile private var instance: Repository? = null
        fun get(ctx: Context) = instance ?: synchronized(this) {
            instance ?: Repository(ctx.applicationContext).also { instance = it }
        }
    }

    private val prefs: SharedPreferences = ctx.getSharedPreferences("scamshield", Context.MODE_PRIVATE)
    private val historyFile = File(ctx.filesDir, "history.json")

    @Volatile private var detector: Detector? = null
    fun detector(): Detector = detector ?: synchronized(this) {
        detector ?: Detector(ctx.assets.open("model.json").bufferedReader().use { it.readText() }).also { detector = it }
    }

    private val _settings = MutableStateFlow(loadSettings())
    val settings: StateFlow<Settings> = _settings
    private val _history = MutableStateFlow(loadHistory())
    val history: StateFlow<List<HistoryItem>> = _history

    private fun loadSettings() = Settings(
        prefs.getBoolean("server", false), prefs.getString("host", "192.168.1.10")!!, prefs.getInt("port", 9099),
        prefs.getBoolean("dns", true), prefs.getBoolean("promos", false),
    )

    fun update(s: Settings) {
        prefs.edit().putBoolean("server", s.serverMode).putString("host", s.host).putInt("port", s.port)
            .putBoolean("dns", s.dnsChecks).putBoolean("promos", s.notifyPromos).apply()
        _settings.value = s
    }

    /**
     * Classify a message. On-device by default; in server mode the message is sent over TCP using the
     * ScamShield protocol, and the phone falls back to the on-device model if the server is unreachable.
     * Must be called off the main thread.
     */
    fun analyse(text: String): Pair<Analysis, SspClient.Result?> {
        val s = _settings.value
        val local = detector().analyse(text, resolveDns = s.dnsChecks)
        if (!s.serverMode) return local to null
        return try {
            val r = SspClient(s.host, s.port).classify(text)
            val j = r.response
            val probs = j.getJSONObject("probs")
            val p = doubleArrayOf(probs.getDouble("legit"), probs.getDouble("promo"), probs.getDouble("scam"))
            val verdict = when (j.getString("label")) { "scam" -> Verdict.SCAM; "promo" -> Verdict.PROMO; else -> Verdict.LEGIT }
            val links = j.optJSONArray("links") ?: JSONArray()
            val linkList = (0 until links.length()).map { i ->
                val l = links.getJSONObject(i)
                val dns = l.optJSONObject("dns")
                val addrs = dns?.optJSONArray("addresses")?.let { a -> (0 until a.length()).map { a.getString(it) } } ?: emptyList()
                com.scamshield.app.detector.LinkIntel.Link(l.getString("url"), l.getString("host"), l.getDouble("risk"),
                    (0 until l.getJSONArray("reasons").length()).map { l.getJSONArray("reasons").getString(it) },
                    addrs, dns?.optDouble("elapsed_ms"))
            }
            val cues = j.optJSONArray("cues")?.let { a -> (0 until a.length()).map {
                com.scamshield.app.detector.Cue(a.getJSONObject(it).getString("id"), a.getJSONObject(it).getString("text")) } }
                ?: local.cues
            local.copy(verdict = verdict, probs = p, links = linkList, linkRisk = j.optDouble("link_risk", 0.0), cues = cues,
                source = "server ${s.host}:${s.port}", millis = r.rttMs) to r
        } catch (e: Exception) {
            local.copy(source = "on-device (server unreachable: ${e.javaClass.simpleName})") to null
        }
    }

    fun add(sender: String, a: Analysis): HistoryItem {
        val item = HistoryItem(System.currentTimeMillis(), sender, a.text, a.verdict, a.probs[2], a.language.name,
            System.currentTimeMillis(), a.source, a.cues.map { it.text } + a.links.flatMap { it.reasons })
        _history.value = (listOf(item) + _history.value).take(300)
        saveHistory()
        return item
    }

    fun clear() {
        _history.value = emptyList()
        saveHistory()
    }

    private fun saveHistory() {
        val arr = JSONArray()
        for (h in _history.value) arr.put(JSONObject().put("id", h.id).put("sender", h.sender).put("text", h.text)
            .put("verdict", h.verdict.name).put("scam", h.scamProb).put("lang", h.language).put("time", h.time)
            .put("source", h.source).put("reasons", JSONArray(h.reasons)))
        historyFile.writeText(arr.toString())
    }

    private fun loadHistory(): List<HistoryItem> = try {
        val arr = JSONArray(historyFile.readText())
        (0 until arr.length()).map { i ->
            val o = arr.getJSONObject(i)
            val r = o.getJSONArray("reasons")
            HistoryItem(o.getLong("id"), o.getString("sender"), o.getString("text"), Verdict.valueOf(o.getString("verdict")),
                o.getDouble("scam"), o.getString("lang"), o.getLong("time"), o.getString("source"),
                (0 until r.length()).map { r.getString(it) })
        }
    } catch (e: Exception) {
        emptyList()
    }
}
