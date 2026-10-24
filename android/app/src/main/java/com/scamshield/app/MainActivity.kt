package com.scamshield.app

import android.app.Application
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import com.scamshield.app.data.Repository
import com.scamshield.app.sms.Notifier
import com.scamshield.app.ui.AboutScreen
import com.scamshield.app.ui.CheckScreen
import com.scamshield.app.ui.MessagesScreen
import com.scamshield.app.ui.NetworkScreen
import com.scamshield.app.ui.ScamShieldTheme
import kotlin.concurrent.thread

class ScamShieldApp : Application() {
    override fun onCreate() {
        super.onCreate()
        Notifier.createChannels(this)
        thread(name = "model-preload") { Repository.get(this).detector() }   // parse the model once, off the UI thread
    }
}

class MainActivity : ComponentActivity() {
    private var openText by mutableStateOf<String?>(null)
    private var tab by mutableIntStateOf(0)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        handle(intent)
        val repo = Repository.get(this)
        setContent {
            ScamShieldTheme {
                val tabs = listOf(
                    Triple("Messages", R.drawable.ic_inbox, 0), Triple("Check", R.drawable.ic_search, 1),
                    Triple("Network", R.drawable.ic_network, 2), Triple("About", R.drawable.ic_shield, 3),
                )
                Scaffold(containerColor = MaterialTheme.colorScheme.background, bottomBar = {
                    NavigationBar {
                        for ((label, icon, i) in tabs) NavigationBarItem(selected = tab == i, onClick = { tab = i },
                            icon = { Icon(painterResource(icon), contentDescription = null) }, label = { Text(label) })
                    }
                }) { pad ->
                    Box(Modifier.padding(pad)) {
                        when (tab) {
                            0 -> MessagesScreen(repo) { openText = it.text; tab = 1 }
                            1 -> CheckScreen(repo, openText)
                            2 -> NetworkScreen(repo)
                            else -> AboutScreen(repo)
                        }
                    }
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handle(intent)
    }

    private fun handle(intent: Intent?) {
        val id = intent?.getLongExtra("history_id", -1L) ?: -1L
        if (id > 0) {
            Repository.get(this).history.value.firstOrNull { it.id == id }?.let { openText = it.text; tab = 1 }
        }
        intent?.getStringExtra(Intent.EXTRA_TEXT)?.let { openText = it; tab = 1 }   // "Share" a message to ScamShield
    }
}
