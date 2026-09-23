# C2T MOBILES - Production Android APK Project

This folder contains the complete, production-ready native Android wrapper project for **C2T MOBILES** (`com.c2tmobiles.app`).

---

## 🌟 Key Features

1. **WebView Integration**:
   - Loads production HTTPS URL (`https://c2tmobiles.com`).
   - Complete support for JavaScript, DOM storage, session storage, and persistent cookies (`CookieManager`).
   - Hardware acceleration and smooth viewport zooming.

2. **Owner/Admin File & Image Picker Support**:
   - Integrated custom `WebChromeClient.onShowFileChooser`.
   - Supports camera photo capture and gallery image selection using Android `FileProvider`.
   - Enables stock management photo uploads directly within the Android app.

3. **WhatsApp & System Deep Linking**:
   - Intercepts WhatsApp links (`wa.me`, `whatsapp://`, `api.whatsapp.com`) and opens them directly in the official WhatsApp app.
   - Intercepts `tel:` links to launch the device dialer with `9994645492`.
   - Intercepts `mailto:` links for customer care email dispatch.

4. **Offline Error Handling**:
   - Built-in network connectivity detection (`ConnectivityManager`).
   - Automatic transition to custom offline UI (`activity_offline.xml`) with a **Retry Connection** button upon network loss or timeout.

5. **Splash Screen**:
   - Professional loading splash screen (`SplashActivity`) displaying the official C2T logo and brand tagline.

6. **Signed Release Keystore**:
   - Generated signed release keystore: `app/c2t-release-key.jks`.
   - Configured release signing in `app/build.gradle` via `app/keystore.properties`.

---

## 📁 Project Structure

```
android/
├── build.gradle                       # Top-level build configuration
├── settings.gradle                    # Project module inclusions
├── gradle.properties                  # AndroidX & JVM settings
├── README.md                          # Android project documentation
├── gradle/
│   └── wrapper/
│       └── gradle-wrapper.properties  # Gradle wrapper settings
└── app/
    ├── build.gradle                   # App module dependencies & signing config
    ├── keystore.properties            # Release keystore credentials reference
    ├── c2t-release-key.jks            # Production signed keystore file
    ├── proguard-rules.pro             # ProGuard / R8 code obfuscation rules
    └── src/
        └── main/
            ├── AndroidManifest.xml    # App permissions & activity declarations
            ├── java/com/c2tmobiles/app/
            │   ├── SplashActivity.java # Animated splash screen launcher
            │   └── MainActivity.java   # WebView engine, file chooser, WhatsApp links
            └── res/
                ├── drawable/          # Splash logo & button drawables
                ├── layout/            # activity_splash, activity_main, activity_offline
                ├── mipmap-*/          # App launcher icons across all screen densities
                ├── values/            # colors, strings, styles
                └── xml/               # network_security_config, file_paths
```

---

## 🛠️ How to Build the APK

### Method 1: Android Studio (Recommended)

1. Open **Android Studio**.
2. Select **Open an Existing Project** and browse to `c:\Users\madhavan\Desktop\C2T\android`.
3. Allow Android Studio to sync Gradle dependencies.
4. To build a debug APK:
   - Click **Build > Build APK(s)**.
5. To build a signed Production APK:
   - Click **Build > Generate Signed Bundle / APK...**
   - Choose **APK** and click **Next**.
   - Select Key Store Path: `app/c2t-release-key.jks`.
   - Keystore Password: `C2TMobilesSecureStorePass2026!`
   - Key Alias: `c2t-key-alias`
   - Key Password: `C2TMobilesSecureStorePass2026!`
   - Choose **release** build variant and click **Create**.
   - The signed production APK will be created in `app/build/outputs/apk/release/app-release.apk`.

### Method 2: Command Line (Gradle Wrapper)

Ensure JDK 17+ or JDK 21 is set in your `JAVA_HOME` environment variable, then run:

```bash
cd android
./gradlew assembleRelease
```

The compiled release APK will be located at:
`app/build/outputs/apk/release/app-release.apk`

---

## ⚙️ Changing Production Web URL

To update or change the target URL loaded by the application (for staging or custom domains):

1. Open `app/src/main/res/values/strings.xml`.
2. Edit the `<string name="app_url">` value:
   ```xml
   <!-- Production URL -->
   <string name="app_url">https://c2tmobiles.com</string>

   <!-- Local Emulator Testing URL -->
   <!-- <string name="app_url">http://10.0.2.2:5000</string> -->
   ```

---

## 🔒 Security & Keystore Details

- **Keystore Location**: `android/app/c2t-release-key.jks`
- **Keystore Alias**: `c2t-key-alias`
- **Store Password**: `C2TMobilesSecureStorePass2026!`
- **Key Password**: `C2TMobilesSecureStorePass2026!`
- **Validity**: 10,000 Days

> ⚠️ Keep `c2t-release-key.jks` backed up safely. It is required to publish updates to Google Play Store.

---

## 🔑 Permissions Declared

- `android.permission.INTERNET`
- `android.permission.ACCESS_NETWORK_STATE`
- `android.permission.CAMERA`
- `android.permission.READ_MEDIA_IMAGES`
- `android.permission.READ_EXTERNAL_STORAGE`
