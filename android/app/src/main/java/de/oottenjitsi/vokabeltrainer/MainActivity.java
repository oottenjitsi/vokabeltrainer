package de.oottenjitsi.vokabeltrainer;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.util.Locale;

/** Zeigt den Vokabeltrainer in einer eingebauten Android-Ansicht – ganz ohne Chrome. */
public class MainActivity extends Activity {
    private static final String START = "https://oottenjitsi.github.io/vokabeltrainer/";
    private static final int FILE_REQ = 7;

    private WebView web;
    private TextToSpeech tts;
    private volatile boolean ttsReady = false;
    private ValueCallback<Uri[]> fileCallback;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.parseColor("#2f80ed"));
        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setUserAgentString(s.getUserAgentString() + " VokabelApp/1");

        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                int r = tts.setLanguage(Locale.UK);
                if (r < 0) r = tts.setLanguage(Locale.US);
                ttsReady = r >= 0;
            }
        });
        web.addJavascriptInterface(new Bridge(), "AndroidTTS");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                String host = req.getUrl().getHost();
                if (host == null) return true;
                // Nur die eigene Seite und die Dienste der App erlauben – keine fremden Links (kein Browser fürs Kind).
                return !(host.endsWith("github.io") || host.endsWith("firebaseapp.com")
                        || host.endsWith("googleapis.com") || host.endsWith("gstatic.com"));
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
                if (req.isForMainFrame()) {
                    view.loadDataWithBaseURL(null,
                        "<html><body style='font-family:sans-serif;text-align:center;padding:40px;background:#eef4fb'>"
                        + "<h2>Keine Internetverbindung</h2><p>Beim ersten Start braucht die App einmal Internet.</p>"
                        + "<button style='font-size:18px;padding:12px 20px;border-radius:12px;border:0;background:#2f80ed;color:#fff'"
                        + " onclick=\"location.href='" + START + "'\">Nochmal versuchen</button></body></html>",
                        "text/html", "utf-8", null);
                }
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> cb, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = cb;
                Intent i = new Intent(Intent.ACTION_GET_CONTENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("*/*");
                try {
                    startActivityForResult(Intent.createChooser(i, "Datei auswählen"), FILE_REQ);
                } catch (Exception e) {
                    fileCallback = null;
                    return false;
                }
                return true;
            }
        });

        if (state != null) web.restoreState(state); else web.loadUrl(START);
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        if (req == FILE_REQ && fileCallback != null) {
            fileCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(res, data));
            fileCallback = null;
        } else {
            super.onActivityResult(req, res, data);
        }
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onDestroy() {
        if (tts != null) tts.shutdown();
        if (web != null) web.destroy();
        super.onDestroy();
    }

    /** Wird von der Web-App als window.AndroidTTS aufgerufen. */
    private class Bridge {
        @JavascriptInterface public boolean available() { return ttsReady; }

        @JavascriptInterface public void speak(String text, float rate, boolean flush) {
            if (!ttsReady || text == null) return;
            tts.setSpeechRate(rate > 0 ? rate : 0.9f);
            tts.speak(text, flush ? TextToSpeech.QUEUE_FLUSH : TextToSpeech.QUEUE_ADD, null, "u" + System.nanoTime());
        }

        @JavascriptInterface public void stop() { if (tts != null) tts.stop(); }
    }
}
