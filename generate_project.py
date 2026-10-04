import os
import sys
import argparse
import base64
import subprocess
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--app-name', default='My App')
parser.add_argument('--package-name', default='com.myapp.app')
parser.add_argument('--web-url', default='https://example.com')
parser.add_argument('--theme-color', default='#0284c7')
parser.add_argument('--build-id', default='ucd_1')
parser.add_argument('--icon-base64', default='')
args = parser.parse_args()

app_name = args.app_name.strip() or 'My App'
package_name = args.package_name.strip() or 'com.myapp.app'
web_url = args.web_url.strip() or 'https://example.com'
theme_color = args.theme_color.strip() or '#0284c7'
build_id = args.build_id.strip() or 'ucd_1'
clean_name = "".join([c for c in app_name if c.isalnum()]) or "MyApp"

project_dir = 'android-app'
if os.path.exists(project_dir):
    shutil.rmtree(project_dir)

os.makedirs(project_dir, exist_ok=True)
package_path = os.path.join(project_dir, 'app', 'src', 'main', 'java', *package_name.split('.'))
res_dir = os.path.join(project_dir, 'app', 'src', 'main', 'res')
os.makedirs(package_path, exist_ok=True)
os.makedirs(os.path.join(res_dir, 'layout'), exist_ok=True)
os.makedirs(os.path.join(res_dir, 'values'), exist_ok=True)
os.makedirs(os.path.join(res_dir, 'mipmap-anydpi-v26'), exist_ok=True)
os.makedirs(os.path.join(res_dir, 'drawable'), exist_ok=True)
os.makedirs(os.path.join(project_dir, 'gradle', 'wrapper'), exist_ok=True)

# settings.gradle.kts
with open(os.path.join(project_dir, 'settings.gradle.kts'), 'w') as f:
    f.write(f'''pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}
rootProject.name = "{clean_name}"
include(":app")
''')

# Root build.gradle.kts
with open(os.path.join(project_dir, 'build.gradle.kts'), 'w') as f:
    f.write('''plugins {
    id("com.android.application") version "8.2.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
}
''')

# gradle.properties
with open(os.path.join(project_dir, 'gradle.properties'), 'w') as f:
    f.write('''org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
kotlin.code.style=official
''')

# gradle-wrapper.properties
with open(os.path.join(project_dir, 'gradle', 'wrapper', 'gradle-wrapper.properties'), 'w') as f:
    f.write('''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.2-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
''')

# app/build.gradle.kts
with open(os.path.join(project_dir, 'app', 'build.gradle.kts'), 'w') as f:
    f.write(f'''plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}}

android {{
    namespace = "{package_name}"
    compileSdk = 34

    defaultConfig {{
        applicationId = "{package_name}"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }}
    }}
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
    kotlinOptions {{
        jvmTarget = "17"
    }}
}}

dependencies {{
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.swiperefreshlayout:swiperefreshlayout:1.1.0")
    implementation("androidx.webkit:webkit:1.10.0")
}}
''')

# AndroidManifest.xml
with open(os.path.join(project_dir, 'app', 'src', 'main', 'AndroidManifest.xml'), 'w') as f:
    f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />

    <application
        android:allowBackup="true"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:fullBackupContent="@xml/backup_rules"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher"
        android:supportsRtl="true"
        android:theme="@style/Theme.{clean_name}"
        android:usesCleartextTraffic="true"
        tools:targetApi="31">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:theme="@style/Theme.{clean_name}">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
''')

# Backup & extraction rules
os.makedirs(os.path.join(res_dir, 'xml'), exist_ok=True)
with open(os.path.join(res_dir, 'xml', 'backup_rules.xml'), 'w') as f:
    f.write('''<?xml version="1.0" encoding="utf-8"?>
<full-backup-content>
</full-backup-content>''')

with open(os.path.join(res_dir, 'xml', 'data_extraction_rules.xml'), 'w') as f:
    f.write('''<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
    </cloud-backup>
    <device-transfer>
    </device-transfer>
</data-extraction-rules>''')

# strings.xml & colors.xml & themes.xml
with open(os.path.join(res_dir, 'values', 'strings.xml'), 'w') as f:
    f.write(f'''<resources>
    <string name="app_name">{app_name}</string>
</resources>''')

with open(os.path.join(res_dir, 'values', 'colors.xml'), 'w') as f:
    f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="theme_primary">{theme_color}</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
</resources>''')

with open(os.path.join(res_dir, 'values', 'themes.xml'), 'w') as f:
    f.write(f'''<resources xmlns:tools="http://schemas.android.com/tools">
    <style name="Theme.{clean_name}" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <item name="colorPrimary">@color/theme_primary</item>
        <item name="android:statusBarColor">@color/theme_primary</item>
    </style>
</resources>''')

# activity_main.xml layout
with open(os.path.join(res_dir, 'layout', 'activity_main.xml'), 'w') as f:
    f.write('''<?xml version="1.0" encoding="utf-8"?>
<androidx.swiperefreshlayout.widget.SwipeRefreshLayout 
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/swipeRefreshLayout"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <RelativeLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent">

        <ProgressBar
            android:id="@+id/progressBar"
            style="?android:attr/progressBarStyleHorizontal"
            android:layout_width="match_parent"
            android:layout_height="4dp"
            android:layout_alignParentTop="true"
            android:indeterminate="false"
            android:max="100"
            android:visibility="gone" />

        <WebView
            android:id="@+id/webView"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:layout_below="@id/progressBar" />

        <LinearLayout
            android:id="@+id/offlineLayout"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:gravity="center"
            android:orientation="vertical"
            android:padding="24dp"
            android:background="#FFFFFF"
            android:visibility="gone">

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="Connection Unavailable"
                android:textSize="20sp"
                android:textStyle="bold"
                android:textColor="#0F172A" />

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginTop="8dp"
                android:gravity="center"
                android:text="Please verify your internet connection and tap retry to reload."
                android:textColor="#64748B"
                android:textSize="14sp" />

            <Button
                android:id="@+id/retryBtn"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginTop="20dp"
                android:backgroundTint="@color/theme_primary"
                android:text="Retry Loading" />
        </LinearLayout>
    </RelativeLayout>
</androidx.swiperefreshlayout.widget.SwipeRefreshLayout>
''')

# MainActivity.kt
with open(os.path.join(package_path, 'MainActivity.kt'), 'w') as f:
    f.write(f'''package {package_name}

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.webkit.*
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

class MainActivity : AppCompatActivity() {{

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: ProgressBar
    private lateinit var offlineLayout: LinearLayout
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {{ result ->
        if (fileChooserCallback != null) {{
            val results = WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data)
            fileChooserCallback?.onReceiveValue(results)
            fileChooserCallback = null
        }}
    }}

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        swipeRefresh = findViewById(R.id.swipeRefreshLayout)
        progressBar = findViewById(R.id.progressBar)
        offlineLayout = findViewById(R.id.offlineLayout)
        val retryBtn: Button = findViewById(R.id.retryBtn)

        val targetUrl = "{web_url}"

        webView.settings.apply {{
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            useWideViewPort = true
            loadWithOverviewMode = true
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            userAgentString = userAgentString + " UCDNativeApp/1.0"
        }}

        webView.webViewClient = object : WebViewClient() {{
            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {{
                super.onPageStarted(view, url, favicon)
                progressBar.visibility = View.VISIBLE
                offlineLayout.visibility = View.GONE
            }}

            override fun onPageFinished(view: WebView?, url: String?) {{
                super.onPageFinished(view, url)
                progressBar.visibility = View.GONE
                swipeRefresh.isRefreshing = false
            }}

            override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {{
                super.onReceivedError(view, request, error)
                if (request?.isForMainFrame == true) {{
                    offlineLayout.visibility = View.VISIBLE
                }}
            }}
        }}

        webView.webChromeClient = object : WebChromeClient() {{
            override fun onProgressChanged(view: WebView?, newProgress: Int) {{
                super.onProgressChanged(view, newProgress)
                progressBar.progress = newProgress
                if (newProgress >= 100) {{
                    progressBar.visibility = View.GONE
                }}
            }}

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {{
                fileChooserCallback?.onReceiveValue(null)
                fileChooserCallback = filePathCallback
                val intent = fileChooserParams?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT).apply {{
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = "*/*"
                }}
                try {{
                    filePickerLauncher.launch(intent)
                }} catch (e: Exception) {{
                    fileChooserCallback = null
                    return false
                }}
                return true
            }}
        }}

        swipeRefresh.setOnRefreshListener {{
            webView.reload()
        }}

        retryBtn.setOnClickListener {{
            offlineLayout.visibility = View.GONE
            webView.loadUrl(targetUrl)
        }}

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {{
            override fun handleOnBackPressed() {{
                if (webView.canGoBack()) {{
                    webView.goBack()
                }} else {{
                    finish()
                }}
            }}
        }})

        webView.loadUrl(targetUrl)
    }}
}}
''')

# Download official gradlew script
os.system('gradle wrapper --gradle-version 8.2')
if not os.path.exists(os.path.join(project_dir, 'gradlew')):
    # Create standard gradlew unix script
    with open(os.path.join(project_dir, 'gradlew'), 'w') as f:
        f.write('''#!/bin/sh
exec gradle "$@"
''')
    os.chmod(os.path.join(project_dir, 'gradlew'), 0o755)

print("Project generated successfully!")
