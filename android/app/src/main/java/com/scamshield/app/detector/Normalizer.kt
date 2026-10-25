package com.scamshield.app.detector

import java.text.Normalizer as JNormalizer

/** A native script registered in the Python scamshield.scripts module (exported in model.json). */
data class Script(val code: String, val name: String, val lo: Int, val hi: Int,
                  val roman: Set<String>, val romanRe: Regex)

/**
 * Kotlin port of scamshield.obfuscation.normalize (the script-aware canonicaliser).
 * Language-agnostic: every script comes from model.json, so a new language needs no code change here.
 * Must stay byte-for-byte compatible with the Python version: ParityTest checks it on 300 messages.
 */
class Normalizer(
    private val homoglyphs: Map<String, String>,
    private val deleet: Map<String, String>,
    private val lookalikes: Map<String, String>,
    private val native2en: Map<String, String>,
) {
    companion object {
        private val ZW = Regex("[​‌‍⁠﻿]")
        private const val SEP = "[\\.\\-_\\* ]"
        private val SPACED_LAT = Regex("\\b(?:[A-Za-z]$SEP){2,}[A-Za-z]\\b")
        private val INTRA_SEP = Regex("(?<=[A-Za-z])[\\.\\-_\\*](?=[A-Za-z])")

        /** Registered native scripts; set once by Detector from model.json. */
        var scripts: List<Script> = emptyList()
            set(value) {
                field = value
                val ranges = value.joinToString("") { "\\x{%X}-\\x{%X}".format(it.lo, it.hi) }
                spacedNat = Regex("(?:[$ranges]+[\\._\\*]){2,}[$ranges]+")
                natIntraSep = Regex("(?<=[$ranges])[\\._\\*](?=[$ranges])")
            }
        private var spacedNat = Regex("(?!)")
        private var natIntraSep = Regex("(?!)")
        private val SKIP = Regex(
            "(@|://|www\\.|\\.(com|in|xyz|top|ly|gd|me|it|co|info|live|site|net|click|support|online|sbi)\\b|/)",
            RegexOption.IGNORE_CASE
        )
        private val RUNS = Regex("([A-Za-z])\\1{2,}")

        fun scriptCode(cp: Int): String? = scripts.firstOrNull { cp in it.lo..it.hi }?.code
        fun isNative(cp: Int) = scriptCode(cp) != null

        /** Python str.isalpha */
        fun isAlpha(cp: Int) = Character.isLetter(cp)

        /** Python str.isalnum (letters + any numeric category) */
        fun isAlnum(cp: Int): Boolean {
            if (Character.isLetter(cp)) return true
            val t = Character.getType(cp)
            return t == Character.DECIMAL_DIGIT_NUMBER.toInt() || t == Character.LETTER_NUMBER.toInt() ||
                t == Character.OTHER_NUMBER.toInt()
        }

        fun isMark(cp: Int): Boolean {
            val t = Character.getType(cp)
            return t == Character.NON_SPACING_MARK.toInt() || t == Character.COMBINING_SPACING_MARK.toInt() ||
                t == Character.ENCLOSING_MARK.toInt()
        }

        fun isWordChar(cp: Int) = isAlnum(cp) || isMark(cp)

        /** Python str.isdigit for a whole string */
        fun isDigitString(s: String): Boolean {
            if (s.isEmpty()) return false
            return s.codePoints().allMatch { Character.isDigit(it) }
        }

        fun cps(s: String): IntArray = s.codePoints().toArray()

        fun splitAffixes(tok: String): Triple<String, String, String> {
            val c = cps(tok)
            var i = 0
            var j = c.size
            while (i < j && !isWordChar(c[i])) i++
            while (j > i && !isWordChar(c[j - 1])) j--
            return Triple(String(c, 0, i), String(c, i, j - i), String(c, j, c.size - j))
        }

        /** Python scripts.dominant: most frequent registered script (ties -> first registered). */
        fun dominant(text: String): String? {
            val counts = LinkedHashMap<String, Int>()
            text.codePoints().forEach { cp -> scriptCode(cp)?.let { counts[it] = (counts[it] ?: 0) + 1 } }
            var best: String? = null
            var bestN = 0
            for ((k, v) in counts) if (v > bestN) { best = k; bestN = v }
            return best
        }

        private fun share(token: String, s: Script): Double {
            var letters = 0
            var n = 0
            token.codePoints().forEach { cp ->
                val inS = cp in s.lo..s.hi
                if (isAlpha(cp) || inS) {
                    letters++
                    if (inS) n++
                }
            }
            return if (letters == 0) 0.0 else n.toDouble() / letters
        }

        /** Python scripts.script_of */
        fun scriptOf(word: String): String {
            val c = dominant(word) ?: return "lat"
            val s = scripts.first { it.code == c }
            return if (share(word, s) >= 0.5) c else "lat"
        }

        fun skip(tok: String): Boolean {
            if (SKIP.containsMatchIn(tok)) return true
            val c = cps(tok)
            val digits = c.count { Character.isDigit(it) }
            return digits >= maxOf(1, c.size / 2)
        }

        /** Python str.partition("-") */
        fun partition(s: String): Triple<String, String, String> {
            val k = s.indexOf('-')
            return if (k < 0) Triple(s, "", "") else Triple(s.substring(0, k), "-", s.substring(k + 1))
        }

        fun isAscii(s: String) = s.all { it.code < 128 }
    }

    private fun deleetToken(tok: String): String {
        val c = cps(tok)
        val letters = c.count { isAlpha(it) }
        val subs = c.count { deleet.containsKey(String(Character.toChars(it))) }
        if (letters >= 2 && subs > 0 && letters >= subs && !isDigitString(tok) && isAscii(tok)) {
            val sb = StringBuilder()
            for (cp in c) {
                val ch = String(Character.toChars(cp))
                sb.append(deleet[ch] ?: ch)
            }
            return sb.toString()
        }
        return tok
    }

    private fun foldToken(tokIn: String): String {
        var tok = tokIn
        if (skip(tok)) return tok
        run {
            val (pre, core, post) = splitAffixes(tok)
            val (stem, sep, suffix) = partition(core)
            if (sep.isNotEmpty() && stem.isNotEmpty() && suffix.isNotEmpty() && scriptOf(stem) != scriptOf(suffix)) {
                return pre + foldToken(stem) + sep + foldToken(suffix) + post
            }
        }
        val nat = tok.codePoints().filter { isNative(it) || lookalikes.containsKey(String(Character.toChars(it))) }.count()
        val letters = tok.codePoints().filter { isAlpha(it) }.count()
        if (nat > 0 && nat * 2 >= letters) {
            val sb = StringBuilder()
            tok.codePoints().forEach { cp ->
                val ch = String(Character.toChars(cp))
                sb.append(lookalikes[ch] ?: ch)
            }
            tok = natIntraSep.replace(sb.toString(), "")
            val (pre, core, post) = splitAffixes(tok)
            val (stem, sep, suffix) = partition(core)
            native2en[stem]?.let { return pre + it + sep + suffix + post }
            native2en[core]?.let { return pre + it + post }
            return tok
        }
        tok = INTRA_SEP.replace(tok, "")
        return deleetToken(tok)
    }

    fun normalize(text: String): String {
        var t = JNormalizer.normalize(text, JNormalizer.Form.NFKC)
        t = ZW.replace(t, "")
        val sb = StringBuilder()
        t.codePoints().forEach { cp ->
            val ch = String(Character.toChars(cp))
            sb.append(homoglyphs[ch] ?: ch)
        }
        t = sb.toString()
        t = SPACED_LAT.replace(t) { m -> m.value.replace(Regex(SEP), "") }
        t = spacedNat.replace(t) { m -> m.value.replace(Regex("[\\._\\*]"), "") }
        t = t.split(" ").joinToString(" ") { foldToken(it) }
        t = RUNS.replace(t) { m -> m.groupValues[1].repeat(2) }
        return t.lowercase(java.util.Locale.ROOT)
    }
}
