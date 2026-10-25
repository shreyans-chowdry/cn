package com.scamshield.app.ui

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.scamshield.app.data.HistoryItem
import com.scamshield.app.data.Repository
import com.scamshield.app.detector.Analysis
import com.scamshield.app.detector.Verdict
import com.scamshield.app.net.Ssp
import com.scamshield.app.net.SspClient
import com.scamshield.app.sms.Notifier
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

val SAMPLES = listOf(
    "Code-mixed scam" to "प्रिय ग्राहक, आपका SBI account आज रात 12 बजे block कर दिया जाएगा। तुरंत KYC update करने के लिए इस link पर click करें http://sbi-kyc-update.xyz/a9",
    "Another script" to "உங்கள் SBI account இன்று இரவு 12 மணிக்கு block செய்யப்படும். உடனே KYC update செய்ய இந்த link-ஐ click செய்யவும் http://sbi-kyc-update.xyz/a9",
    "UPI PIN trick" to "Congratulations! You have received ₹4,999 cashback. To receive the money accept the request on PhonePe and enter your UPI PIN",
    "Disguised spelling" to "Y0ur HDFC acc0unt will be bl0cked t0day. Upd@te K.Y.C n0w: hdfc-verify.top/k",
    "Romanised" to "Aapka refund ₹2,000 pending hai. Turant collect request approve karo aur PIN daalo",
    "Genuine bank alert" to "உங்கள் A/c XX4821-லிருந்து 12-10-26 அன்று ₹1,250 VPA swiggy@ybl-க்கு debit செய்யப்பட்டது. UPI Ref 412398765432. நீங்கள் செய்யவில்லையா? 1800-123-4567 அழைக்கவும் -SBI",
    "Promotion" to "Swiggy Diwali sale is live! Up to 60% off on all orders. Shop now https://swiggy.onelink.me/x7",
)

@Composable
fun ScreenColumn(content: @Composable () -> Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp, vertical = 12.dp)) {
        content()
        Spacer(Modifier.height(24.dp))
    }
}

// ------------------------------------------------------------------ Messages
@Composable
fun MessagesScreen(repo: Repository, openItem: (HistoryItem) -> Unit) {
    val ctx = LocalContext.current
    val history by repo.history.collectAsState()
    fun granted(p: String) = ContextCompat.checkSelfPermission(ctx, p) == PackageManager.PERMISSION_GRANTED
    var smsOk by remember { mutableStateOf(granted(Manifest.permission.RECEIVE_SMS)) }
    var notifOk by remember { mutableStateOf(Build.VERSION.SDK_INT < 33 || granted(Manifest.permission.POST_NOTIFICATIONS)) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
        smsOk = granted(Manifest.permission.RECEIVE_SMS)
        notifOk = Build.VERSION.SDK_INT < 33 || granted(Manifest.permission.POST_NOTIFICATIONS)
    }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            val on = smsOk && notifOk
            Card(borderColor = if (on) verdictColor(Verdict.LEGIT) else MaterialTheme.colorScheme.outline) {
                Column {
                    Text(if (on) "Protection is on" else "Protection is off", style = MaterialTheme.typography.titleLarge)
                    Text(if (on) "Every incoming SMS is checked on this phone. You get a notification when one looks like a scam."
                    else "Allow ScamShield to read incoming SMS and show notifications so it can warn you about scams.",
                        style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp))
                    if (!on) Button(onClick = {
                        val perms = mutableListOf(Manifest.permission.RECEIVE_SMS)
                        if (Build.VERSION.SDK_INT >= 33) perms += Manifest.permission.POST_NOTIFICATIONS
                        launcher.launch(perms.toTypedArray())
                    }, modifier = Modifier.padding(top = 12.dp)) { Text("Turn on protection") }
                    val scams = history.count { it.verdict == Verdict.SCAM }
                    if (history.isNotEmpty()) Text("${history.size} messages checked · $scams flagged as scams",
                        style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 10.dp))
                }
            }
        }
        if (history.isEmpty()) item {
            Text("No messages checked yet. Incoming SMS will appear here. You can also try the samples on the Check tab.",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 24.dp, start = 4.dp, end = 4.dp))
        }
        items(history, key = { it.id }) { h -> HistoryRow(h) { openItem(h) } }
        if (history.isNotEmpty()) item {
            TextButton(onClick = { repo.clear() }) { Text("Clear history") }
        }
    }
}

@Composable
fun HistoryRow(h: HistoryItem, onClick: () -> Unit) {
    val fmt = remember { SimpleDateFormat("d MMM, HH:mm", Locale.getDefault()) }
    Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(14.dp)).background(MaterialTheme.colorScheme.surface).clickable(onClick = onClick)
        .padding(14.dp)) {
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                VerdictPill(h.verdict)
                Spacer(Modifier.width(8.dp))
                Text(h.sender, style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f))
                Text(fmt.format(Date(h.time)), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Text(h.text, style = MaterialTheme.typography.bodyMedium, maxLines = 2, overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 6.dp))
            Text("${h.language} · ${h.source}", style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 4.dp))
        }
    }
}

// ------------------------------------------------------------------ Check
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun CheckScreen(repo: Repository, initial: String? = null) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var text by remember { mutableStateOf(initial ?: "") }
    var result by remember { mutableStateOf<Analysis?>(null) }
    var busy by remember { mutableStateOf(false) }
    var note by remember { mutableStateOf<String?>(null) }

    fun run(simulate: Boolean) {
        if (text.isBlank()) return
        busy = true
        note = null
        scope.launch {
            val a = withContext(Dispatchers.Default) { repo.analyse(text).first }
            result = a
            busy = false
            if (simulate) {
                val item = repo.add("Simulated SMS", a)
                Notifier.maybeNotify(ctx, item, true)
                note = if (a.verdict == Verdict.LEGIT) "Added to Messages. Genuine messages do not raise a notification."
                else "Added to Messages and a notification was posted, just like a real incoming SMS."
            }
        }
    }
    LaunchedEffect(initial) { if (!initial.isNullOrBlank()) run(false) }

    ScreenColumn {
        Text("Check a message", style = MaterialTheme.typography.headlineSmall)
        Text("Paste any SMS in English or a mix of English and another language. The language is detected for you.",
            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp, bottom = 12.dp))
        OutlinedTextField(value = text, onValueChange = { text = it }, modifier = Modifier.fillMaxWidth().height(150.dp),
            placeholder = { Text("Paste a message") })
        SectionLabel("Try a sample")
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            for ((label, s) in SAMPLES) OutlinedButton(onClick = { text = s; run(false) }) { Text(label) }
        }
        Row(Modifier.padding(top = 12.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Button(onClick = { run(false) }, enabled = !busy && text.isNotBlank()) { Text(if (busy) "Checking…" else "Check message") }
            FilledTonalButton(onClick = { run(true) }, enabled = !busy && text.isNotBlank()) { Text("Simulate as incoming SMS") }
        }
        note?.let { Text(it, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 8.dp)) }
        result?.let {
            Spacer(Modifier.height(16.dp))
            AnalysisView(it)
        }
    }
}

// ------------------------------------------------------------------ Network
@Composable
fun NetworkScreen(repo: Repository) {
    val s by repo.settings.collectAsState()
    val scope = rememberCoroutineScope()
    var host by remember(s.host) { mutableStateOf(s.host) }
    var port by remember(s.port) { mutableStateOf(s.port.toString()) }
    var status by remember { mutableStateOf<String?>(null) }
    var exchange by remember { mutableStateOf<SspClient.Result?>(null) }

    ScreenColumn {
        Text("Network", style = MaterialTheme.typography.headlineSmall)
        Text("By default every check runs on this phone. Server mode sends the message to a ScamShield server on your network using the ScamShield protocol over TCP, where the server also looks up every link in DNS.",
            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 4.dp))

        SectionLabel("Server")
        Card {
            Column {
                SettingRow("Use server mode", "Fall back to on-device checks if the server is unreachable", s.serverMode) {
                    repo.update(s.copy(serverMode = it))
                }
                HorizontalDivider(Modifier.padding(vertical = 10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(host, { host = it }, label = { Text("Server IP") }, modifier = Modifier.weight(2f), singleLine = true)
                    OutlinedTextField(port, { port = it.filter(Char::isDigit) }, label = { Text("TCP port") }, modifier = Modifier.weight(1f),
                        singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                }
                Row(Modifier.padding(top = 10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = {
                        repo.update(s.copy(host = host.trim(), port = port.toIntOrNull() ?: 9099))
                        status = "Connecting…"
                        scope.launch {
                            status = withContext(Dispatchers.IO) {
                                try {
                                    val c = SspClient(host.trim(), port.toIntOrNull() ?: 9099)
                                    val rtts = (1..5).map { c.ping() }
                                    "Connected. Round-trip time ${"%.1f".format(rtts.min())}–${"%.1f".format(rtts.max())} ms over 5 pings."
                                } catch (e: Exception) {
                                    "Could not reach $host:$port (${e.javaClass.simpleName}). Check the server is running and both devices are on the same Wi-Fi."
                                }
                            }
                        }
                    }) { Text("Save and test") }
                    OutlinedButton(onClick = {
                        status = "Sending sample…"
                        scope.launch {
                            withContext(Dispatchers.IO) {
                                try {
                                    exchange = SspClient(host.trim(), port.toIntOrNull() ?: 9099).classify(SAMPLES[0].second)
                                    status = "Classified by the server in ${"%.1f".format(exchange!!.rttMs)} ms."
                                } catch (e: Exception) {
                                    status = "Server error: ${e.message ?: e.javaClass.simpleName}"
                                }
                            }
                        }
                    }) { Text("Send a sample") }
                }
                status?.let { Text(it, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 10.dp)) }
            }
        }

        SectionLabel("Link checks")
        Card {
            SettingRow("Look up links in DNS", "Resolve each link and flag ones that point to private or reserved addresses", s.dnsChecks) {
                repo.update(s.copy(dnsChecks = it))
            }
        }

        exchange?.let { ex ->
            SectionLabel("Last protocol exchange")
            Card {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Request frame (${ex.requestFrame.size} bytes)", style = MaterialTheme.typography.titleMedium)
                    FrameFields(ex.requestFrame)
                    Text(Ssp.hex(ex.requestFrame, 40), fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.labelMedium)
                    HorizontalDivider(Modifier.padding(vertical = 6.dp))
                    Text("Response: ${ex.responseFrame.payload.size + 20} bytes, CRC-32 0x${"%08x".format(ex.responseFrame.crc)} verified",
                        style = MaterialTheme.typography.titleMedium)
                    Text("Verdict from server: ${ex.response.optString("label")}", style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
        SectionLabel("Run the server on a laptop")
        Card {
            Text("python -m scamshield.net.service --tcp 9099\n\nUse the laptop's Wi-Fi IP address above (ipconfig / ifconfig).",
                fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable
private fun FrameFields(f: ByteArray) {
    val b = java.nio.ByteBuffer.wrap(f)
    val magic = b.short.toInt() and 0xFFFF
    val ver = b.get().toInt()
    val type = b.get().toInt()
    val flags = b.get().toInt()
    val win = b.get().toInt()
    val seq = b.int.toLong() and 0xFFFFFFFFL
    val ack = b.int.toLong() and 0xFFFFFFFFL
    val len = b.short.toInt() and 0xFFFF
    val crc = java.nio.ByteBuffer.wrap(f, f.size - 4, 4).int.toLong() and 0xFFFFFFFFL
    val rows = listOf("MAGIC" to "0x%04x ('SS')".format(magic), "VER" to "$ver", "TYPE" to "$type (CLASSIFY_REQ)",
        "FLAGS" to "0x%02x (JSON payload)".format(flags), "WIN" to "$win", "SEQ" to "$seq", "ACK" to "$ack",
        "LEN" to "$len bytes", "CRC-32" to "0x%08x".format(crc))
    Column {
        for ((k, v) in rows) Row {
            Text(k, fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.labelMedium, modifier = Modifier.width(72.dp),
                color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(v, fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable
fun SettingRow(title: String, sub: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(sub, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Spacer(Modifier.width(12.dp))
        Switch(checked = checked, onCheckedChange = onChange)
    }
}

// ------------------------------------------------------------------ About
@Composable
fun AboutScreen(repo: Repository) {
    val s by repo.settings.collectAsState()
    ScreenColumn {
        Text("About ScamShield", style = MaterialTheme.typography.headlineSmall)
        SectionLabel("Notifications")
        Card {
            SettingRow("Also notify for promotions", "Scams always raise a notification; genuine messages never do", s.notifyPromos) {
                repo.update(s.copy(notifyPromos = it))
            }
        }
        SectionLabel("How it works")
        Card {
            Text("Each SMS is cleaned up first, undoing tricks scammers use to slip past filters: look-alike letters, invisible characters, " +
                "digits in place of letters (P1N), dotted words (K.Y.C) and English words written in another script. A character-level " +
                "model trained on English and code-mixed UPI messages then scores it, and every link is checked: raw IP addresses, " +
                "look-alike bank domains, shorteners and, if enabled, where the domain really resolves in DNS.",
                style = MaterialTheme.typography.bodyMedium)
        }
        SectionLabel("Privacy")
        Card {
            Text("Messages are checked on this phone and never uploaded. Only in server mode is a message sent, to the server address you enter.",
                style = MaterialTheme.typography.bodyMedium)
        }
        SectionLabel("Project")
        Card {
            Text("Computer Networks project, VIT Vellore. Model trained ${repo.detector().trainedOn}.",
                style = MaterialTheme.typography.bodyMedium)
        }
    }
}
