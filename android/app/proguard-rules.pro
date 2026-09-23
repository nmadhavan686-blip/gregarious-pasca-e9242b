# ProGuard rules for C2T MOBILES Android App

# Preserve WebKit JavaScript Interfaces
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep WebChromeClient & WebViewClient
-keep public class * extends android.webkit.WebViewClient
-keep public class * extends android.webkit.WebChromeClient

# Keep FileProvider
-keep public class androidx.core.content.FileProvider
