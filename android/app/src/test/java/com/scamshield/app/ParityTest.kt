package com.scamshield.app

import com.scamshield.app.detector.Detector
import com.scamshield.app.net.Ssp
import org.json.JSONArray
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.DataInputStream
import java.io.File

/**
 * The phone must give the same answers as the Python model. parity.json is written by
 * scripts/train_production.py: 300 messages (clean, obfuscated, public corpus) with the
 * Python canonicalised text and probabilities.
 */
class ParityTest {
    private val detector by lazy { Detector(File("src/main/assets/model.json").readText()) }

    @Test
    fun normaliserAndProbabilitiesMatchPython() {
        val cases = JSONArray(javaClass.classLoader!!.getResource("parity.json")!!.readText())
        var normMismatch = 0
        var maxDiff = 0.0
        var labelMismatch = 0
        for (i in 0 until cases.length()) {
            val c = cases.getJSONObject(i)
            val text = c.getString("text")
            val norm = detector.normalizer.normalize(text)
            if (norm != c.getString("normalized")) {
                normMismatch++
                if (normMismatch <= 5) println("normalise mismatch:\n  py: ${c.getString("normalized")}\n  kt: $norm")
            }
            val p = detector.proba(text)
            val q = c.getJSONArray("probs")
            for (k in 0..2) maxDiff = maxOf(maxDiff, kotlin.math.abs(p[k] - q.getDouble(k)))
            val argP = p.indices.maxBy { p[it] }
            val argQ = (0..2).maxBy { q.getDouble(it) }
            if (argP != argQ) labelMismatch++
        }
        println("cases=${cases.length()} normaliser mismatches=$normMismatch label mismatches=$labelMismatch max |dp|=$maxDiff")
        assertTrue("normaliser differs on $normMismatch messages", normMismatch <= 2)
        assertEquals(0, labelMismatch)
        assertTrue("max probability difference $maxDiff", maxDiff < 1e-3)
    }

    @Test
    fun detectsCodeMixedScamsInEveryScript() {
        val cases = mapOf(
            "hi-en" to "आपका SBI account आज रात block कर दिया जाएगा। तुरंत KYC update करने के लिए इस link पर click करें http://sbi-kyc-update.xyz/a9",
            "ta-en" to "உங்கள் SBI account இன்று இரவு block செய்யப்படும். உடனே KYC update செய்ய link-ஐ click செய்யவும் http://sbi-kyc-update.xyz/a9",
        )
        for ((code, text) in cases) {
            val a = detector.analyse(text)
            assertEquals(code, a.language.code)
            assertTrue(a.links.first().risk > 0.5)
            assertEquals(com.scamshield.app.detector.Verdict.SCAM, a.verdict)
        }
    }

    @Test
    fun sspFrameRoundTripAndCrc() {
        val payload = """{"text":"உங்கள் KYC"}""".toByteArray()
        val frame = Ssp.encode(Ssp.CLASSIFY_REQ, payload, 7, Ssp.FLAG_JSON)
        val f = Ssp.read(DataInputStream(ByteArrayInputStream(frame)))
        assertEquals(7L, f.seq)
        assertEquals(String(payload), String(f.payload))
        frame[20] = (frame[20].toInt() xor 4).toByte()
        var caught = false
        try { Ssp.read(DataInputStream(ByteArrayInputStream(frame))) } catch (e: Ssp.CorruptFrame) { caught = true }
        assertTrue("CRC-32 must catch a flipped bit", caught)
    }
}
