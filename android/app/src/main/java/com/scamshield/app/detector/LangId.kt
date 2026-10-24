package com.scamshield.app.detector

import org.json.JSONObject

/** Port of scamshield.langid: automatic English / Tamil / Tamil–English identification, token by token. */
class LangId(cfg: JSONObject) {
    enum class Tag { EN, TA, TA_ROM, MIX, UNIV, OTHER }

    data class Token(val text: String, val tag: Tag)
    data class Result(val code: String, val name: String, val tokens: List<Token>, val cmi: Double,
                      val tamilShare: Double)

    private val romanTamil = cfg.getJSONArray("roman_tamil").toStringList().toHashSet()
    private val enVocab = cfg.getJSONArray("en_vocab").toStringList().toHashSet()
    private val romanRe = Regex(cfg.getString("roman_regex"))

    private fun looksRomanTamil(w: String): Boolean {
        val l = w.lowercase()
        return l in romanTamil || (l !in enVocab && l.length > 3 && romanRe.containsMatchIn(l))
    }

    fun tag(tok: String): Tag {
        if (tok.isEmpty() || Normalizer.skip(tok)) return Tag.UNIV
        val core = Normalizer.splitAffixes(tok).second
        if (core.isEmpty() || core.codePoints().noneMatch { Normalizer.isAlpha(it) }) return Tag.UNIV
        val c = Normalizer.cps(core)
        val ta = c.count { Normalizer.isTamil(it) }
        val lat = c.count { it < 128 && Character.isLetter(it) }
        val letters = c.count { Character.isLetter(it) }
        if (ta > 0 && lat > 0) {
            val (stem, _, suffix) = Normalizer.partition(core)
            if (suffix.isNotEmpty() && suffix.codePoints().anyMatch { Normalizer.isTamil(it) } &&
                stem.codePoints().noneMatch { Normalizer.isTamil(it) }) return Tag.MIX
        }
        if (ta > 0 && ta >= lat) return Tag.TA
        if (lat > 0 && lat >= letters * 0.6) {
            val stem = Normalizer.partition(core.lowercase()).first
            return if (looksRomanTamil(stem)) Tag.TA_ROM else Tag.EN
        }
        if (ta > 0) return Tag.TA
        return Tag.OTHER
    }

    fun identify(text: String): Result {
        val toks = text.split(Regex("\\s+")).filter { it.isNotEmpty() }.map { Token(it, tag(it)) }
        var en = toks.count { it.tag == Tag.EN || it.tag == Tag.MIX }
        var ta = toks.count { it.tag == Tag.TA || it.tag == Tag.MIX }
        val rom = toks.count { it.tag == Tag.TA_ROM }
        val other = toks.count { it.tag == Tag.OTHER }
        val n = en + ta + rom + other
        val tamilTotal = ta + rom
        val (code, name) = when {
            n == 0 -> "en" to "English"
            other > n / 2.0 -> "other" to "Other"
            tamilTotal == 0 -> "en" to "English"
            en == 0 || en.toDouble() / n < 0.08 -> if (ta >= rom) "ta" to "Tamil" else "ta-rom" to "Tamil (romanised)"
            rom > ta -> "ta-rom" to "Tamil (romanised)"
            else -> "mixed" to "Tamil–English"
        }
        val cmi = if (n == 0) 0.0 else 100.0 * (1 - maxOf(en, tamilTotal, other).toDouble() / n)
        return Result(code, name, toks, cmi, if (n == 0) 0.0 else tamilTotal.toDouble() / n)
    }
}
