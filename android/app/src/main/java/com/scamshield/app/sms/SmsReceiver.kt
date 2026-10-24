package com.scamshield.app.sms

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Telephony
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.scamshield.app.MainActivity
import com.scamshield.app.detector.Normalizer
import com.scamshield.app.R
import com.scamshield.app.data.HistoryItem
import com.scamshield.app.data.Repository
import com.scamshield.app.detector.Verdict
import kotlin.concurrent.thread

/** Receives every incoming SMS, classifies it and raises a notification for likely scams. */
class SmsReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return
        val parts = Telephony.Sms.Intents.getMessagesFromIntent(intent) ?: return
        // long messages arrive as several parts: join them per sender
        val bySender = parts.groupBy { it.displayOriginatingAddress ?: "unknown" }
            .mapValues { (_, ps) -> ps.joinToString("") { it.displayMessageBody ?: "" } }
        val pending = goAsync()
        thread(name = "scamshield-sms") {
            try {
                val repo = Repository.get(context)
                for ((sender, body) in bySender) {
                    val (analysis, _) = repo.analyse(body)
                    val item = repo.add(sender, analysis)
                    Notifier.maybeNotify(context, item, repo.settings.value.notifyPromos)
                }
            } finally {
                pending.finish()
            }
        }
    }
}

object Notifier {
    const val CHANNEL_SCAM = "scam_alerts"
    const val CHANNEL_PROMO = "promotions"

    fun createChannels(ctx: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = ctx.getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(NotificationChannel(CHANNEL_SCAM, "Scam alerts", NotificationManager.IMPORTANCE_HIGH)
                .apply { description = "Warnings for SMS that look like UPI or payment scams" })
            nm.createNotificationChannel(NotificationChannel(CHANNEL_PROMO, "Promotions", NotificationManager.IMPORTANCE_LOW)
                .apply { description = "Optional notes for promotional SMS" })
        }
    }

    /** "Scam warning" in the message's own language, when it is written in a supported native script. */
    private val WARNINGS = mapOf("hi" to "धोखाधड़ी की चेतावनी", "ta" to "மோசடி எச்சரிக்கை")

    private fun localWarning(text: String): String =
        Normalizer.dominant(text)?.let { WARNINGS[it] }?.let { " · $it" } ?: ""

    fun maybeNotify(ctx: Context, item: HistoryItem, notifyPromos: Boolean) {
        if (item.verdict == Verdict.LEGIT || (item.verdict == Verdict.PROMO && !notifyPromos)) return
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
        val open = PendingIntent.getActivity(ctx, item.id.toInt(), Intent(ctx, MainActivity::class.java)
            .putExtra("history_id", item.id).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val scam = item.verdict == Verdict.SCAM
        val title = if (scam) "Likely scam from ${item.sender}" + localWarning(item.text) else "Promotion from ${item.sender}"
        val why = item.reasons.firstOrNull() ?: "Message pattern matches known UPI scams"
        val body = if (scam) "$why\nDo not share your PIN or OTP, and do not open the link." else item.text
        val n = NotificationCompat.Builder(ctx, if (scam) CHANNEL_SCAM else CHANNEL_PROMO)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle(title)
            .setContentText(why)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body + "\n\n“" + item.text.take(160) + "”"))
            .setPriority(if (scam) NotificationCompat.PRIORITY_HIGH else NotificationCompat.PRIORITY_LOW)
            .setColor(if (scam) 0xFFC62828.toInt() else 0xFFB26A00.toInt())
            .setContentIntent(open)
            .setAutoCancel(true)
            .build()
        NotificationManagerCompat.from(ctx).notify(item.id.toInt(), n)
    }
}
