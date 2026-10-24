package com.scamshield.app

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import app.cash.paparazzi.DeviceConfig
import app.cash.paparazzi.Paparazzi
import com.scamshield.app.data.HistoryItem
import com.scamshield.app.detector.Detector
import com.scamshield.app.detector.Verdict
import com.scamshield.app.ui.AnalysisView
import com.scamshield.app.ui.Card
import com.scamshield.app.ui.HistoryRow
import com.scamshield.app.ui.SAMPLES
import com.scamshield.app.ui.ScamShieldTheme
import org.junit.Rule
import org.junit.Test
import java.io.File

/** Renders the main screens on the JVM (no device needed): ./gradlew recordPaparazziDebug */
class ScreenshotTest {
    @get:Rule
    val paparazzi = Paparazzi(deviceConfig = DeviceConfig.PIXEL_6.copy(screenHeight = 3400), maxPercentDifference = 1.0)

    private val detector by lazy { Detector(File("src/main/assets/model.json").readText()) }

    @Test
    fun scamAnalysis() {
        val a = detector.analyse(SAMPLES[0].second)
        paparazzi.snapshot {
            ScamShieldTheme {
                Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(16.dp)) {
                    Text("Check a message", style = MaterialTheme.typography.headlineSmall, modifier = Modifier.padding(bottom = 12.dp))
                    AnalysisView(a)
                }
            }
        }
    }

    @Test
    fun genuineAnalysis() {
        val a = detector.analyse(SAMPLES[4].second)
        paparazzi.snapshot {
            ScamShieldTheme {
                Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(16.dp)) { AnalysisView(a) }
            }
        }
    }

    @Test
    fun messages() {
        val now = 1_792_700_000_000L
        val items = SAMPLES.mapIndexed { i, (_, text) ->
            val a = detector.analyse(text)
            HistoryItem(i.toLong() + 1, listOf("VM-SBIINB", "+91 98400 12345", "AX-HDFCBK", "+91 90031 55555", "VM-SBIUPI", "JD-SWIGGY")[i],
                text, a.verdict, a.probs[2], a.language.name, now - i * 3_600_000L, "on-device", emptyList())
        }
        paparazzi.snapshot {
            ScamShieldTheme {
                Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Card(borderColor = com.scamshield.app.ui.verdictColor(Verdict.LEGIT)) {
                        Column {
                            Text("Protection is on", style = MaterialTheme.typography.titleLarge)
                            Text("Every incoming SMS is checked on this phone. You get a notification when one looks like a scam.",
                                style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
                            Text("${items.size} messages checked · ${items.count { it.verdict == Verdict.SCAM }} flagged as scams",
                                style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(top = 10.dp))
                        }
                    }
                    for (h in items) HistoryRow(h) {}
                }
            }
        }
    }
}
