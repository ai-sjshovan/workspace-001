package com.codexfoundry.derpyowl

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.codexfoundry.derpyowl.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.gameWebView.settings.javaScriptEnabled = true
        binding.gameWebView.settings.domStorageEnabled = true
        binding.gameWebView.settings.allowFileAccess = true
        binding.gameWebView.settings.allowContentAccess = true
        binding.gameWebView.settings.mediaPlaybackRequiresUserGesture = false
        binding.gameWebView.isVerticalScrollBarEnabled = false
        binding.gameWebView.isHorizontalScrollBarEnabled = false
        binding.gameWebView.webChromeClient = WebChromeClient()
        binding.gameWebView.addJavascriptInterface(AndroidAuthBridge(binding.gameWebView), "AndroidAuth")
        binding.gameWebView.loadUrl("file:///android_asset/index.html")
    }
}

private class AndroidAuthBridge(private val webView: WebView) {
    @JavascriptInterface
    fun beginGoogleLogin() {
        webView.post {
            Toast.makeText(
                webView.context,
                "Google sign-in is stubbed for the Android MVP build.",
                Toast.LENGTH_SHORT,
            ).show()
            webView.evaluateJavascript("window.handleNativeGoogleLogin('Google Play stub')", null)
        }
    }
}
