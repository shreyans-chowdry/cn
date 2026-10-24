package com.scamshield.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.scamshield.app.detector.Analysis
import com.scamshield.app.detector.LangId
import com.scamshield.app.detector.Verdict
import kotlin.math.abs
import kotlin.math.roundToInt

@Composable
fun SectionLabel(text: String) {
    Text(text, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier.padding(top = 14.dp, bottom = 6.dp))
}

@Composable
fun Card(modifier: Modifier = Modifier, borderColor: Color? = null, content: @Composable () -> Unit) {
    Box(modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(MaterialTheme.colorScheme.surface)
        .border(1.dp, borderColor ?: MaterialTheme.colorScheme.outline, RoundedCornerShape(16.dp)).padding(16.dp)) {
        content()
    }
}

@Composable
fun VerdictPill(v: Verdict) {
    val c = verdictColor(v)
    Text(v.label, color = c, style = MaterialTheme.typography.labelMedium,
        modifier = Modifier.clip(RoundedCornerShape(50)).background(c.copy(alpha = 0.12f)).padding(horizontal = 10.dp, vertical = 4.dp))
}

@Composable
fun ProbabilityBar(p: DoubleArray) {
    val colors = listOf(verdictColor(Verdict.LEGIT), verdictColor(Verdict.PROMO), verdictColor(Verdict.SCAM))
    Row(Modifier.fillMaxWidth().height(10.dp).clip(RoundedCornerShape(5.dp)), horizontalArrangement = Arrangement.spacedBy(2.dp)) {
        for (k in 0..2) if (p[k] > 0.005) Box(Modifier.weight(p[k].toFloat()).height(10.dp).background(colors[k]))
    }
    Row(Modifier.fillMaxWidth().padding(top = 6.dp), horizontalArrangement = Arrangement.SpaceBetween) {
        listOf("Genuine", "Promotion", "Scam").forEachIndexed { k, s ->
            Text("$s ${(p[k] * 100).roundToInt()}%", style = MaterialTheme.typography.labelMedium, color = colors[k])
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun LanguageTokens(lang: LangId.Result) {
    FlowRow(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        for (t in lang.tokens.take(60)) {
            val c = when (t.tag) {
                LangId.Tag.TA, LangId.Tag.TA_ROM -> Signal.tamil
                LangId.Tag.EN -> Signal.english
                LangId.Tag.MIX -> Color(0xFF00897B)
                else -> MaterialTheme.colorScheme.onSurfaceVariant
            }
            Text(t.text, style = MaterialTheme.typography.labelMedium, color = c,
                modifier = Modifier.clip(RoundedCornerShape(6.dp)).background(c.copy(alpha = 0.10f)).padding(horizontal = 6.dp, vertical = 2.dp))
        }
    }
    Row(Modifier.padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(14.dp)) {
        Legend(Signal.english, "English")
        Legend(Signal.tamil, "Tamil")
        Legend(Color(0xFF00897B), "mixed in one word")
    }
}

@Composable
private fun Legend(c: Color, s: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(8.dp).clip(RoundedCornerShape(2.dp)).background(c))
        Spacer(Modifier.width(4.dp))
        Text(s, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun AnalysisView(a: Analysis) {
    val vc = verdictColor(a.verdict)
    Column {
        Card(borderColor = vc) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(when (a.verdict) {
                        Verdict.SCAM -> "Likely scam"
                        Verdict.PROMO -> "Promotion"
                        Verdict.LEGIT -> "Looks genuine"
                    }, style = MaterialTheme.typography.headlineSmall, color = vc)
                    Spacer(Modifier.weight(1f))
                    Text(a.language.name, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Text(when (a.verdict) {
                    Verdict.SCAM -> "Don't reply, don't open the link, never enter your UPI PIN to receive money."
                    Verdict.PROMO -> "An advertisement. Safe to ignore."
                    Verdict.LEGIT -> "No scam pattern found. Still never share your PIN or OTP."
                }, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp, bottom = 12.dp))
                ProbabilityBar(a.probs)
            }
        }

        val risky = a.links.filter { it.risk >= 0.5 }
        if (a.cues.isNotEmpty() || risky.isNotEmpty()) {
            SectionLabel("Why")
            Card {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    for (c in a.cues) Reason(c.text)
                    for (l in risky) Reason("Contains a dangerous link (${l.host}), details below.")
                }
            }
        }

        SectionLabel("The message, as the model read it")
        Card {
            val maxAbs = a.highlights.maxOfOrNull { abs(it.score) }?.takeIf { it > 0 } ?: 1.0
            val scam = verdictColor(Verdict.SCAM)
            val ok = verdictColor(Verdict.LEGIT)
            Text(buildAnnotatedString {
                a.highlights.forEachIndexed { i, h ->
                    val s = (h.score / maxAbs).toFloat()
                    val bg = if (s > 0.15f) scam.copy(alpha = 0.10f + 0.30f * s) else if (s < -0.15f) ok.copy(alpha = 0.08f + 0.2f * -s) else Color.Transparent
                    withStyle(SpanStyle(background = bg, fontWeight = if (s > 0.5f) FontWeight.SemiBold else null)) { append(h.token) }
                    if (i < a.highlights.size - 1) append(" ")
                }
            }, style = MaterialTheme.typography.bodyLarge)
        }

        SectionLabel("Language · detected automatically · code-mixing index ${a.language.cmi.roundToInt()}")
        Card { Column { LanguageTokens(a.language) } }

        if (a.links.isNotEmpty()) {
            SectionLabel("Links")
            Card {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    for (l in a.links) {
                        Column {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(l.host, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                                Text("risk ${(l.risk * 100).roundToInt()}%", style = MaterialTheme.typography.labelMedium,
                                    color = if (l.risk >= 0.5) scamColor() else MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            if (l.addresses.isNotEmpty()) Text("DNS: " + l.addresses.joinToString(", ") +
                                (l.dnsMs?.let { " · ${"%.0f".format(it)} ms" } ?: ""),
                                style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            if (l.reasons.isEmpty()) Text("Nothing suspicious about this link", style = MaterialTheme.typography.bodyMedium)
                            else Column(Modifier.padding(top = 6.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                for (r in l.reasons) Reason(r)
                            }
                        }
                    }
                }
            }
        }
        Text("${a.source} · ${"%.1f".format(a.millis)} ms", style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 12.dp))
    }
}

@Composable
private fun scamColor() = verdictColor(Verdict.SCAM)

@Composable
private fun Reason(text: String) {
    Row {
        Box(Modifier.padding(top = 7.dp).size(6.dp).clip(RoundedCornerShape(3.dp)).background(scamColor()))
        Spacer(Modifier.width(10.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}
