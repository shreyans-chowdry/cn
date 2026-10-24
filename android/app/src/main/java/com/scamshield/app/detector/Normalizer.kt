package com.scamshield.app.detector

import java.text.Normalizer as JNormalizer

/**
 * Kotlin port of scamshield.obfuscation.normalize (the script-aware canonicaliser).
 * Must stay byte-for-byte compatible with the Python version: ParityTest checks it on 300 messages.
 */
class Normalizer(
    private val homoglyphs: Map<String, String>,
    private val deleet: Map<String, String>,
    private val taDigits: Map<String, String>,
    private val ta2en: Map<String, String>,
) {
    companion object {
        private val ZW = Regex("[​‌‍⁠﻿]")
        private const val SEP = "[\\.\\-_\\* ]"
        private val SPACED_LAT = Regex("\\b(?:[A-Za-z]$SEP){2,}[A-Za-z]\\b")
        private val SPACED_TA = Regex("(?:[஀-௿]+[\\._\\*]){2,}[஀-௿]+")
        private val INTRA_SEP = Regex("(?<=[A-Za-z])[\\.\\-_\\*](?=[A-Za-z])")
        private val TA_INTRA_SEP = Regex("(?<=[஀-௿])[\\._\\*](?=[஀-௿])")
        private val SKIP = Regex(
            "(@|://|www\\.|\\.(com|in|xyz|top|ly|gd|me|it|co|info|live|site|net|click|support|online|sbi)\\b|/)",
            RegexOption.IGNORE_CASE
        )
        private val RUNS = Regex("([A-Za-z])\\1{2,}")

        fun isTamil(cp: Int) = cp in 0x0B80..0x0BFF

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

        fun tamilShare(token: String): Double {
            var letters = 0
            var ta = 0
            token.codePoints().forEach { cp ->
                if (isAlpha(cp) || isTamil(cp)) {
                    letters++
                    if (isTamil(cp)) ta++
                }
            }
            return if (letters == 0) 0.0 else ta.toDouble() / letters
        }

        fun scriptOf(word: String) = if (tamilShare(word) >= 0.5) "ta" else "lat"

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
        if (tok.codePoints().anyMatch { isTamil(it) }) {
            val sb = StringBuilder()
            tok.codePoints().forEach { cp ->
                val ch = String(Character.toChars(cp))
                sb.append(taDigits[ch] ?: ch)
            }
            tok = TA_INTRA_SEP.replace(sb.toString(), "")
            val (pre, core, post) = splitAffixes(tok)
            val (stem, sep, suffix) = partition(core)
            ta2en[stem]?.let { return pre + it + sep + suffix + post }
            ta2en[core]?.let { return pre + it + post }
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
        t = SPACED_TA.replace(t) { m -> m.value.replace(Regex("[\\._\\*]"), "") }
        t = t.split(" ").joinToString(" ") { foldToken(it) }
        t = RUNS.replace(t) { m -> m.groupValues[1].repeat(2) }
        return t.lowercase(java.util.Locale.ROOT)
    }
}
