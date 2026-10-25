package com.scamshield.app.detector

import org.json.JSONObject

/**
 * Port of scamshield.langid: automatic language identification, token by token.
 * Language-agnostic: the native scripts come from model.json (Normalizer.scripts).
 *
 * Token tags: "en", "<code>" (native script), "<code>-rom" (romanised native word), "mix" (English stem with a
 * native case suffix), "univ" (numbers, URLs, IDs), "other".
 */
class LangId(cfg: JSONObject) {
    data class Token(val text: String, val tag: String) {
        /** The language this token is evidence for, for colouring: "en", a script code, "mix" or "univ". */
        val family: String get() = if (tag.endsWith("-rom")) tag.removeSuffix("-rom") else tag
    }
    data class Result(val code: String, val name: String, val tokens: List<Token>, val cmi: Double,
                      val nativeShare: Double)

    private val enVocab = cfg.getJSONArray("en_vocab").toStringList().toHashSet()

    private fun scripts() = Normalizer.scripts

    private fun romanScript(w: String): String? {
        val l = w.lowercase()
        for (s in scripts()) if (l in s.roman) return s.code
        if (l in enVocab || l.length <= 3) return null
        for (s in scripts()) if (s.romanRe.containsMatchIn(l)) return s.code
        return null
    }

    fun nameOf(code: String): String {
        if (code == "en") return "English"
        if (code == "other") return "Other"
        val base = code.substringBefore('-')
        val kind = if (code.contains('-')) code.substringAfter('-') else ""
        val name = scripts().first { it.code == base }.name
        return when (kind) { "en" -> "$name–English"; "rom" -> "$name (romanised)"; else -> name }
    }

    fun tag(tok: String): String {
        if (tok.isEmpty() || Normalizer.skip(tok)) return "univ"
        val core0 = Normalizer.splitAffixes(tok).second
        if (core0.isEmpty() || core0.codePoints().noneMatch { Normalizer.isAlpha(it) }) return "univ"
        val core = core0
        val c = Normalizer.cps(core)
        val nat = Normalizer.dominant(core)
        val nNat = c.count { Normalizer.isNative(it) }
        val lat = c.count { it < 128 && Character.isLetter(it) }
        val letters = c.count { Character.isLetter(it) }
        if (nNat > 0 && lat > 0) {
            val (stem, _, suffix) = Normalizer.partition(core)
            if (suffix.isNotEmpty() && suffix.codePoints().anyMatch { Normalizer.isNative(it) } &&
                stem.codePoints().noneMatch { Normalizer.isNative(it) }) return "mix"
        }
        if (nNat > 0 && nNat >= lat) return nat!!
        if (lat > 0 && lat >= letters * 0.6) {
            val r = romanScript(Normalizer.partition(core.lowercase()).first)
            return if (r != null) "$r-rom" else "en"
        }
        if (nNat > 0) return nat!!
        return "other"
    }

    fun identify(text: String): Result {
        val toks = text.split(Regex("\\s+")).filter { it.isNotEmpty() }.map { Token(it, tag(it)) }
        val counts = HashMap<String, Int>()
        for (t in toks) counts[t.tag] = (counts[t.tag] ?: 0) + 1
        val mix = counts["mix"] ?: 0
        val en = (counts["en"] ?: 0) + mix
        val other = counts["other"] ?: 0
        val mixTarget = Normalizer.dominant(text)
        val native = scripts().associate { s ->
            s.code to ((counts[s.code] ?: 0) + (if (s.code == mixTarget) mix else 0))
        }
        val rom = scripts().associate { s -> s.code to (counts["${s.code}-rom"] ?: 0) }
        val n = en + other + native.values.sum() + rom.values.sum()
        val total = scripts().associate { s -> s.code to (native[s.code]!! + rom[s.code]!!) }
        var best: String? = null
        var bestN = -1
        for (s in scripts()) if (total[s.code]!! > bestN) { best = s.code; bestN = total[s.code]!! }
        val code = when {
            n == 0 -> "en"
            other > n / 2.0 -> "other"
            best == null || total[best] == 0 -> "en"
            native[best] == 0 && rom[best]!!.toDouble() / n < 0.25 -> "en"
            en == 0 || en.toDouble() / n < 0.08 -> if (native[best]!! >= rom[best]!!) best else "$best-rom"
            rom[best]!! > native[best]!! -> "$best-rom"
            else -> "$best-en"
        }
        val biggest = (listOf(en, other) + total.values).maxOrNull() ?: 0
        val cmi = if (n == 0) 0.0 else 100.0 * (1 - biggest.toDouble() / n)
        val nativeShare = if (n == 0) 0.0 else total.values.sum().toDouble() / n
        return Result(code, nameOf(code), toks, cmi, nativeShare)
    }
}
