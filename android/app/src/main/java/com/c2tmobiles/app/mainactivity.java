package com.c2tmobiles.app;

import android.annotation.SuppressLint;
import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkInfo;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Log;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.SslErrorHandler;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.FileProvider;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "C2T_WEBVIEW_DEBUG";

    private WebView webView;
    private SwipeRefreshLayout swipeRefreshLayout;
    private ProgressBar loadingProgress;
    private View offlineView;
    private TextView txtOfflineTitle;
    private TextView txtOfflineMsg;
    private TextView txtErrorDetails;
    private Button btnRetry;

    private ValueCallback<Uri[]> filePathCallback;
    private String cameraPhotoPath;
    private ActivityResultLauncher<Intent> fileChooserLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();
        setupLaunchers();
        setupCookies();
        setupWebView();
        setupBackNavigation();

        loadUrl(getString(R.string.app_url));
    }

    private void initViews() {
        webView = findViewById(R.id.webView);
        swipeRefreshLayout = findViewById(R.id.swipeRefreshLayout);
        loadingProgress = findViewById(R.id.loadingProgress);
        offlineView = findViewById(R.id.offlineView);
        txtOfflineTitle = findViewById(R.id.txtOfflineTitle);
        txtOfflineMsg = findViewById(R.id.txtOfflineMsg);
        txtErrorDetails = findViewById(R.id.txtErrorDetails);
        btnRetry = findViewById(R.id.btnRetry);

        swipeRefreshLayout.setColorSchemeResources(R.color.accent);
        swipeRefreshLayout.setOnRefreshListener(() -> {
            Log.d(TAG, "Pull-to-refresh triggered.");
            if (isDeviceConnected()) {
                hideErrorView();
                webView.reload();
            } else {
                swipeRefreshLayout.setRefreshing(false);
                showErrorView("OFFLINE_DEVICE", "No Internet Connection", getString(R.string.offline_message), null);
            }
        });

        btnRetry.setOnClickListener(v -> {
            Log.d(TAG, "Retry button clicked.");
            if (!isDeviceConnected()) {
                showErrorView("OFFLINE_DEVICE", getString(R.string.offline_title), getString(R.string.offline_message), "Device active network interface is disconnected.");
                Toast.makeText(this, R.string.offline_title, Toast.LENGTH_SHORT).show();
            } else {
                hideErrorView();
                loadingProgress.setVisibility(View.VISIBLE);
                webView.reload();
            }
        });
    }

    private void setupCookies() {
        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, true);
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);

        String defaultUA = settings.getUserAgentString();
        settings.setUserAgentString(defaultUA + " C2TMobilesApp/1.0");

        webView.setWebViewClient(new CustomWebViewClient());
        webView.setWebChromeClient(new CustomWebChromeClient());
    }

    private void setupLaunchers() {
        fileChooserLauncher = registerForActivityResult(
            new ActivityResultContracts.StartActivityForResult(),
            result -> {
                if (filePathCallback == null) return;

                Uri[] results = null;
                if (result.getResultCode() == RESULT_OK) {
                    Intent data = result.getData();
                    if (data != null && data.getDataString() != null) {
                        results = new Uri[]{Uri.parse(data.getDataString())};
                    } else if (cameraPhotoPath != null) {
                        File file = new File(cameraPhotoPath);
                        if (file.exists() && file.length() > 0) {
                            results = new Uri[]{Uri.fromFile(file)};
                        }
                    }
                }

                filePathCallback.onReceiveValue(results);
                filePathCallback = null;
            }
        );
    }

    private void setupBackNavigation() {
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (webView != null && webView.canGoBack()) {
                    webView.goBack();
                } else {
                    setEnabled(false);
                    getOnBackPressedDispatcher().onBackPressed();
                }
            }
        });
    }

    private void loadUrl(String url) {
        Log.d(TAG, "Attempting to load URL: " + url);
        if (!isDeviceConnected()) {
            Log.w(TAG, "Device reports offline state.");
            showErrorView("OFFLINE_DEVICE", getString(R.string.offline_title), getString(R.string.offline_message), "No active network interface.");
        } else {
            hideErrorView();
            webView.loadUrl(url);
        }
    }

    /**
     * Modern Android network connectivity check using NetworkCapabilities (API 29+)
     * with fallback for legacy API levels.
     */
    private boolean isDeviceConnected() {
        ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm == null) return false;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            Network activeNetwork = cm.getActiveNetwork();
            if (activeNetwork == null) return false;
            NetworkCapabilities caps = cm.getNetworkCapabilities(activeNetwork);
            return caps != null && (
                caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) ||
                caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
            );
        } else {
            @SuppressWarnings("deprecation")
            NetworkInfo activeNetwork = cm.getActiveNetworkInfo();
            return activeNetwork != null && activeNetwork.isConnectedOrConnecting();
        }
    }

    private void showErrorView(String category, String title, String message, String details) {
        Log.e(TAG, "Error displayed -> Category: " + category + " | Title: " + title + " | Details: " + details);
        txtOfflineTitle.setText(title);
        txtOfflineMsg.setText(message);
        
        if (details != null && !details.isEmpty()) {
            txtErrorDetails.setText("Diagnostic: " + details);
            txtErrorDetails.setVisibility(View.VISIBLE);
        } else {
            txtErrorDetails.setVisibility(View.GONE);
        }

        offlineView.setVisibility(View.VISIBLE);
        webView.setVisibility(View.GONE);
        loadingProgress.setVisibility(View.GONE);
        swipeRefreshLayout.setRefreshing(false);
    }

    private void hideErrorView() {
        offlineView.setVisibility(View.GONE);
        webView.setVisibility(View.VISIBLE);
    }

    // Custom WebChromeClient for Progress & File Uploads
    private class CustomWebChromeClient extends WebChromeClient {
        @Override
        public void onProgressChanged(WebView view, int newProgress) {
            if (newProgress < 100) {
                loadingProgress.setVisibility(View.VISIBLE);
                loadingProgress.setProgress(newProgress);
            } else {
                loadingProgress.setVisibility(View.GONE);
                swipeRefreshLayout.setRefreshing(false);
            }
        }

        @Override
        public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
            if (MainActivity.this.filePathCallback != null) {
                MainActivity.this.filePathCallback.onReceiveValue(null);
            }
            MainActivity.this.filePathCallback = filePathCallback;

            Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            if (takePictureIntent.resolveActivity(getPackageManager()) != null) {
                File photoFile = null;
                try {
                    photoFile = createImageFile();
                    takePictureIntent.putExtra("PhotoPath", cameraPhotoPath);
                } catch (IOException ex) {
                    Log.e(TAG, "Error creating image file for camera photo", ex);
                }

                if (photoFile != null) {
                    Uri photoURI = FileProvider.getUriForFile(
                        MainActivity.this,
                        getString(R.string.file_provider_authority),
                        photoFile
                    );
                    takePictureIntent.putExtra(MediaStore.EXTRA_OUTPUT, photoURI);
                } else {
                    takePictureIntent = null;
                }
            }

            Intent contentSelectionIntent = new Intent(Intent.ACTION_GET_CONTENT);
            contentSelectionIntent.addCategory(Intent.CATEGORY_OPENABLE);
            contentSelectionIntent.setType("image/*");

            Intent[] intentArray = (takePictureIntent != null) ? new Intent[]{takePictureIntent} : new Intent[0];

            Intent chooserIntent = new Intent(Intent.ACTION_CHOOSER);
            chooserIntent.putExtra(Intent.EXTRA_INTENT, contentSelectionIntent);
            chooserIntent.putExtra(Intent.EXTRA_TITLE, "Select Mobile Image");
            chooserIntent.putExtra(Intent.EXTRA_INITIAL_INTENTS, intentArray);

            fileChooserLauncher.launch(chooserIntent);
            return true;
        }
    }

    private File createImageFile() throws IOException {
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
        String imageFileName = "JPEG_" + timeStamp + "_";
        File storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        File image = File.createTempFile(imageFileName, ".jpg", storageDir);
        cameraPhotoPath = image.getAbsolutePath();
        return image;
    }

    // Custom WebViewClient for error classification, SSL validation, and link interception
    private class CustomWebViewClient extends WebViewClient {

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            String url = request.getUrl().toString();
            return handleCustomUrl(url);
        }

        @Override
        @SuppressWarnings("deprecation")
        public boolean shouldOverrideUrlLoading(WebView view, String url) {
            return handleCustomUrl(url);
        }

        private boolean handleCustomUrl(String url) {
            if (url == null) return false;
            Log.d(TAG, "Navigating to URL: " + url);

            if (url.contains("wa.me") || url.contains("whatsapp://") || url.contains("api.whatsapp.com")) {
                try {
                    Intent whatsappIntent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    startActivity(whatsappIntent);
                } catch (ActivityNotFoundException e) {
                    Toast.makeText(MainActivity.this, "WhatsApp app is not installed", Toast.LENGTH_SHORT).show();
                }
                return true;
            }

            if (url.startsWith("tel:")) {
                Intent dialIntent = new Intent(Intent.ACTION_DIAL, Uri.parse(url));
                startActivity(dialIntent);
                return true;
            }

            if (url.startsWith("mailto:")) {
                Intent emailIntent = new Intent(Intent.ACTION_SENDTO, Uri.parse(url));
                startActivity(emailIntent);
                return true;
            }

            return false;
        }

        @Override
        public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
            if (request != null && request.isForMainFrame()) {
                String failingUrl = request.getUrl() != null ? request.getUrl().toString() : "";
                int errorCode = error.getErrorCode();
                CharSequence description = error.getDescription();

                Log.e(TAG, "onReceivedError [MainFrame] -> URL: " + failingUrl + " | Code: " + errorCode + " | Desc: " + description);
                classifyAndShowError("NETWORK_ERROR", errorCode, description != null ? description.toString() : "Page load error", failingUrl);
            } else if (request != null) {
                Log.w(TAG, "onReceivedError [SubResource] -> URL: " + request.getUrl() + " | Code: " + error.getErrorCode());
            }
        }

        @Override
        @SuppressWarnings("deprecation")
        public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
            Log.e(TAG, "onReceivedError (legacy) -> URL: " + failingUrl + " | Code: " + errorCode + " | Desc: " + description);
            classifyAndShowError("NETWORK_ERROR", errorCode, description, failingUrl);
        }

        @Override
        public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse errorResponse) {
            if (request != null && request.isForMainFrame()) {
                int statusCode = errorResponse.getStatusCode();
                String reason = errorResponse.getReasonPhrase();
                String failingUrl = request.getUrl() != null ? request.getUrl().toString() : "";

                Log.e(TAG, "onReceivedHttpError [MainFrame] -> Code: " + statusCode + " | Reason: " + reason + " | URL: " + failingUrl);

                if (statusCode >= 500) {
                    showErrorView("SERVER_ERROR", getString(R.string.http_error_title), getString(R.string.http_error_message), "HTTP " + statusCode + " " + reason);
                }
            }
        }

        @Override
        public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
            String failingUrl = error != null ? error.getUrl() : "";
            int primaryError = error != null ? error.getPrimaryError() : -1;

            Log.e(TAG, "onReceivedSslError -> SSL Error Code: " + primaryError + " | URL: " + failingUrl);
            
            // SECURITY REQUIREMENT: Never call handler.proceed() on SSL error!
            handler.cancel();

            showErrorView("SSL_ERROR", getString(R.string.ssl_error_title), getString(R.string.ssl_error_message), "SSL Certificate Primary Error Code: " + primaryError);
        }

        private void classifyAndShowError(String defaultCategory, int errorCode, String description, String url) {
            if (!isDeviceConnected()) {
                showErrorView("OFFLINE_DEVICE", getString(R.string.offline_title), getString(R.string.offline_message), "No active internet connection on device.");
                return;
            }

            // Device is connected to Internet (4G+/Wi-Fi working), but server/DNS failed!
            if (errorCode == ERROR_HOST_LOOKUP || errorCode == ERROR_CONNECT || errorCode == ERROR_TIMEOUT) {
                showErrorView("DNS_HOST_UNREACHABLE", 
                    getString(R.string.server_unreachable_title), 
                    getString(R.string.server_unreachable_message), 
                    "DNS / Host Lookup Failed (" + description + " | Code: " + errorCode + ")"
                );
            } else {
                showErrorView(defaultCategory, 
                    "Page Load Error", 
                    "An error occurred while loading C2T MOBILES (" + url + ").", 
                    description + " (Code: " + errorCode + ")"
                );
            }
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            Log.d(TAG, "onPageFinished -> " + url);
            swipeRefreshLayout.setRefreshing(false);
            loadingProgress.setVisibility(View.GONE);
            CookieManager.getInstance().flush();
        }
    }
}
