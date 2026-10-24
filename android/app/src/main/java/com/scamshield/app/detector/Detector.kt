package com.scamshield.app.detector

import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.sqrt

enum class Verdict(val label: String) { LEGIT("Genuine"), PROMO("Promotion"), SCAM("Likely scam") }

data class Cue(val id: String, val text: String)
data class Highlight(val token: String, val score: Double)

data class Analysis(
    val text: String,
    val verdict: Verdict,
    val probs: DoubleArray,            // fused: legit, promo, scam
    val textProbs: DoubleArray,        // text model only
    val language: LangId.Result,
    val links: List<LinkIntel.Link>,
    val linkRisk: Double,
    val cues: List<Cue>,
    val highlights: List<Highlight>,
    val normalized: String,
    val millis: Double,
    val source: String = "on-device",
)

/**
 * On-device port of scamshield.detector: canonicalise -> char 2-5-gram TF-IDF (sklearn char_wb)
 * -> multinomial logistic regression -> fuse with link intelligence.
 */
class Detector(json: String) {
    private val terms: HashMap<String, Int>
    private val idf: DoubleArray
    private val coef: Array<DoubleArray>
    private val intercept: DoubleArray
    private val minN: Int
    private val maxN: Int
    private val sublinear: Boolean
    val linkWeight: Double
    val scamThreshold: Double
    val normalizer: Normalizer
    val langId: LangId
    val linkIntel: LinkIntel
    private val cues: List<Triple<String, String, List<Regex>>>
    private val safeCues: List<Regex>
    val trainedOn: String

    init {
        val m = JSONObject(json)
        val t = m.getJSONArray("terms")
        terms = HashMap(t.length() * 2)
        for (i in 0 until t.length()) terms[t.getString(i)] = i
        idf = m.getJSONArray("idf").toDoubleArray()
        val c = m.getJSONArray("coef")
        coef = Array(c.length()) { c.getJSONArray(it).toDoubleArray() }
        intercept = m.getJSONArray("intercept").toDoubleArray()
        val ng = m.getJSONArray("ngram_range")
        minN = ng.getInt(0); maxN = ng.getInt(1)
        sublinear = m.getBoolean("sublinear_tf")
        linkWeight = m.getDouble("link_weight")
        scamThreshold = m.getDouble("scam_threshold")
        val sa = m.getJSONArray("scripts")
        Normalizer.scripts = (0 until sa.length()).map { i ->
            val o = sa.getJSONObject(i)
            Script(o.getString("code"), o.getString("name"), o.getInt("lo"), o.getInt("hi"),
                o.getJSONArray("roman").toStringList().toHashSet(), Regex(o.getString("roman_regex")))
        }
        val n = m.getJSONObject("normalize")
        normalizer = Normalizer(n.getJSONObject("homoglyphs").toStringMap(), n.getJSONObject("deleet").toStringMap(),
            n.getJSONObject("lookalikes").toStringMap(), n.getJSONObject("native2en").toStringMap())
        langId = LangId(m.getJSONObject("langid"))
        linkIntel = LinkIntel(m.getJSONObject("links"))
        val cs = m.getJSONArray("cues")
        cues = (0 until cs.length()).map { i ->
            val o = cs.getJSONObject(i)
            val pats = o.getJSONArray("patterns")
            Triple(o.getString("id"), o.getString("text"),
                (0 until pats.length()).map { Regex(pats.getString(it), RegexOption.IGNORE_CASE) })
        }
        val sc = m.getJSONArray("safe_cues")
        safeCues = (0 until sc.length()).map { Regex(sc.getString(it), RegexOption.IGNORE_CASE) }
        trainedOn = m.optJSONObject("meta")?.optString("trained") ?: ""
    }

    /** sklearn's char_wb analyzer, on code points. */
    private fun charWbNgrams(doc: String): List<String> {
        val out = ArrayList<String>()
        for (word in splitWhitespace(doc)) {
            val w = Normalizer.cps(" $word ")
            for (n in minN..maxN) {
                var offset = 0
                out.add(String(w, 0, minOf(n, w.size)))
                while (offset + n < w.size) {
                    offset += 1
                    out.add(String(w, offset, n))
                }
                if (offset == 0) break
            }
        }
        return out
    }

    private fun splitWhitespace(s: String): List<String> {
        val out = ArrayList<String>()
        val sb = StringBuilder()
        s.codePoints().forEach { cp ->
            if (Character.isWhitespace(cp) || Character.isSpaceChar(cp)) {
                if (sb.isNotEmpty()) { out.add(sb.toString()); sb.setLength(0) }
            } else sb.appendCodePoint(cp)
        }
        if (sb.isNotEmpty()) out.add(sb.toString())
        return out
    }

    /** Sparse TF-IDF vector (index -> weight), L2-normalised. */
    fun vectorize(normalized: String): Map<Int, Double> {
        val counts = HashMap<Int, Int>()
        for (g in charWbNgrams(normalized)) terms[g]?.let { counts[it] = (counts[it] ?: 0) + 1 }
        val v = HashMap<Int, Double>(counts.size)
        var norm = 0.0
        for ((i, cnt) in counts) {
            val tf = if (sublinear) 1.0 + ln(cnt.toDouble()) else cnt.toDouble()
            val w = tf * idf[i]
            v[i] = w
            norm += w * w
        }
        norm = sqrt(norm)
        if (norm > 0) for (k in v.keys) v[k] = v[k]!! / norm
        return v
    }

    fun proba(text: String): DoubleArray = probaVec(vectorize(normalizer.normalize(text)))

    private fun probaVec(x: Map<Int, Double>): DoubleArray {
        val z = DoubleArray(coef.size) { k -> intercept[k] + x.entries.sumOf { (i, w) -> w * coef[k][i] } }
        val mx = z.max()
        val e = z.map { exp(it - mx) }
        val s = e.sum()
        return DoubleArray(z.size) { e[it] / s }
    }

    fun explainCues(text: String): List<Cue> {
        val t = normalizer.normalize(text)
        var hits = cues.filter { (_, _, pats) -> pats.any { it.containsMatchIn(t) } }.map { Cue(it.first, it.second) }
        if (safeCues.any { it.containsMatchIn(t) }) hits = hits.filter { it.id != "share_otp" && it.id != "pin_to_receive" }
        return hits
    }

    private fun highlights(text: String, x: Map<Int, Double>): List<Highlight> {
        return text.split(Regex("\\s+")).filter { it.isNotEmpty() }.map { tok ->
            val core = Normalizer.splitAffixes(tok).second
            var score = 0.0
            if (core.isNotEmpty()) {
                for (word in splitWhitespace(normalizer.normalize(core))) {
                    val w = Normalizer.cps(" $word ")
                    for (n in minN..maxN) {
                        val last = maxOf(1, w.size - n + 1)
                        for (i in 0 until last) {
                            val g = String(w, i, minOf(n, w.size - i))
                            val j = terms[g] ?: continue
                            val xi = x[j] ?: continue
                            val rel = coef[2][j] - (coef[0][j] + coef[1][j] + coef[2][j]) / 3.0
                            score += xi * rel
                        }
                    }
                }
            }
            Highlight(tok, score)
        }
    }

    /** Full analysis. `resolveDns` performs real DNS lookups of the links (call off the main thread). */
    fun analyse(text: String, resolveDns: Boolean = false): Analysis {
        val t0 = System.nanoTime()
        val normalized = normalizer.normalize(text)
        val x = vectorize(normalized)
        val p = probaVec(x)
        val links = linkIntel.analyse(text, resolveDns)
        val risk = links.maxOfOrNull { it.risk } ?: 0.0
        val fused = p.copyOf()
        if (risk > 0) {
            val ps = 1 - (1 - p[2]) * (1 - linkWeight * risk)
            val rest = 1 - p[2]
            fused[0] = if (rest > 0) p[0] * (1 - ps) / rest else 0.0
            fused[1] = if (rest > 0) p[1] * (1 - ps) / rest else 0.0
            fused[2] = ps
        }
        val verdict = when {
            fused[2] >= scamThreshold -> Verdict.SCAM
            fused[1] > fused[0] -> Verdict.PROMO
            else -> Verdict.LEGIT
        }
        return Analysis(text, verdict, fused, p, langId.identify(text), links, risk, explainCues(text),
            highlights(text, x), normalized, (System.nanoTime() - t0) / 1e6)
    }
}

fun JSONArray.toDoubleArray() = DoubleArray(length()) { getDouble(it) }

fun JSONObject.toStringMap(): Map<String, String> {
    val out = HashMap<String, String>()
    keys().forEach { out[it] = getString(it) }
    return out
}

fun JSONArray.toStringList(): List<String> = (0 until length()).map { getString(it) }
