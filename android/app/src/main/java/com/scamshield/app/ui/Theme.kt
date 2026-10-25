package com.scamshield.app.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.scamshield.app.detector.Verdict

object Signal {
    val scam = Color(0xFFC62828)
    val promo = Color(0xFFB26A00)
    val legit = Color(0xFF2E7D32)
    val scamDark = Color(0xFFFF6B63)
    val promoDark = Color(0xFFE3A92A)
    val legitDark = Color(0xFF5CC27A)
    val native = Color(0xFF1C6FB0)
    val english = Color(0xFF6B4FBB)
}

@Composable
fun verdictColor(v: Verdict): Color {
    val dark = isSystemInDarkTheme()
    return when (v) {
        Verdict.SCAM -> if (dark) Signal.scamDark else Signal.scam
        Verdict.PROMO -> if (dark) Signal.promoDark else Signal.promo
        Verdict.LEGIT -> if (dark) Signal.legitDark else Signal.legit
    }
}

private val Light = lightColorScheme(
    primary = Color(0xFF1E3A6E), onPrimary = Color.White,
    primaryContainer = Color(0xFFDCE4F5), onPrimaryContainer = Color(0xFF0E1E3D),
    secondary = Color(0xFF4A5A70), background = Color(0xFFF3F5F9), surface = Color.White,
    surfaceVariant = Color(0xFFE8ECF2), onSurface = Color(0xFF14202E), onSurfaceVariant = Color(0xFF4A5A6C),
    outline = Color(0xFFCBD3DE),
)
private val Dark = darkColorScheme(
    primary = Color(0xFF9DB6F0), onPrimary = Color(0xFF0E1E3D),
    primaryContainer = Color(0xFF243B66), onPrimaryContainer = Color(0xFFDCE4F5),
    secondary = Color(0xFFA9B6C5), background = Color(0xFF0F1620), surface = Color(0xFF17212D),
    surfaceVariant = Color(0xFF223042), onSurface = Color(0xFFE8EDF3), onSurfaceVariant = Color(0xFFA9B6C5),
    outline = Color(0xFF2E3D50),
)

private val Type = Typography(
    headlineSmall = TextStyle(fontSize = 24.sp, fontWeight = FontWeight.SemiBold, lineHeight = 30.sp),
    titleLarge = TextStyle(fontSize = 20.sp, fontWeight = FontWeight.SemiBold, lineHeight = 26.sp),
    titleMedium = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.SemiBold, lineHeight = 22.sp),
    bodyLarge = TextStyle(fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontSize = 14.sp, lineHeight = 20.sp),
    labelMedium = TextStyle(fontSize = 12.sp, fontWeight = FontWeight.Medium, lineHeight = 16.sp),
)

@Composable
fun ScamShieldTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (isSystemInDarkTheme()) Dark else Light, typography = Type, content = content)
}
