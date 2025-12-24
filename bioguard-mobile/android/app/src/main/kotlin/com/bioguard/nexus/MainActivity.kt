package com.bioguard.nexus

import android.os.Build
import android.os.Bundle
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.BufferedReader
import java.io.FileReader

class MainActivity: FlutterActivity() {
    private val CHANNEL = "com.bioguard.nexus/security"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            if (call.method == "checkEnvironment") {
                val securityReport = performSecurityCheck()
                result.success(securityReport)
            } else {
                result.notImplemented()
            }
        }
    }

    private fun performSecurityCheck(): Map<String, Any> {
        val isDevMode = isDeveloperModeEnabled()
        val isDebugger = isDebuggerConnected()
        val isRooted = isRooted()
        val isEmulator = isEmulator()
        val isHooked = isFridaDetected()

        val isSafe = !(isDevMode || isDebugger || isRooted || isEmulator || isHooked)

        return mapOf(
            "isSafe" to isSafe,
            "devMode" to isDevMode,
            "usbDebug" to isDebugger,
            "root" to isRooted,
            "emulator" to isEmulator,
            "hooking" to isHooked
        )
    }

    // --- 1. Developer Mode & USB Debugging Check ---
    private fun isDeveloperModeEnabled(): Boolean {
        return try {
            val devOptions = Settings.Global.getInt(
                contentResolver,
                Settings.Global.DEVELOPMENT_SETTINGS_ENABLED,
                0
            )
            devOptions == 1
        } catch (e: Exception) {
            false
        }
    }

    private fun isDebuggerConnected(): Boolean {
        return try {
            val adb = Settings.Global.getInt(
                contentResolver,
                Settings.Global.ADB_ENABLED,
                0
            )
            adb == 1
        } catch (e: Exception) {
            false
        }
    }

    // --- 2. Root Detection ---
    private fun isRooted(): Boolean {
        val paths = arrayOf(
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su",
            "/su/bin/su"
        )

        for (path in paths) {
            try {
                if (File(path).exists()) return true
            } catch (e: Exception) {
                // Permission denied, continue
            }
        }

        // Check for root management apps
        val rootPackages = arrayOf(
            "com.topjohnwu.magisk",
            "eu.chainfire.supersu",
            "com.koushikdutta.superuser",
            "com.noshufou.android.su"
        )

        for (pkg in rootPackages) {
            try {
                packageManager.getPackageInfo(pkg, 0)
                return true
            } catch (e: Exception) {
                // Package not found
            }
        }

        return false
    }

    // --- 3. Emulator Detection ---
    private fun isEmulator(): Boolean {
        return (Build.FINGERPRINT.startsWith("generic")
                || Build.FINGERPRINT.startsWith("unknown")
                || Build.MODEL.contains("google_sdk")
                || Build.MODEL.contains("Emulator")
                || Build.MODEL.contains("Android SDK built for x86")
                || Build.MANUFACTURER.contains("Genymotion")
                || (Build.BRAND.startsWith("generic") && Build.DEVICE.startsWith("generic"))
                || "google_sdk" == Build.PRODUCT
                || Build.HARDWARE.contains("goldfish")
                || Build.HARDWARE.contains("ranchu")
                || Build.PRODUCT.contains("sdk")
                || Build.PRODUCT.contains("emulator")
                || Build.PRODUCT.contains("simulator"))
    }

    // --- 4. Frida/Xposed Hook Detection ---
    private fun isFridaDetected(): Boolean {
        // Check memory maps for Frida
        try {
            val file = File("/proc/self/maps")
            val reader = BufferedReader(FileReader(file))
            var line: String?
            while (reader.readLine().also { line = it } != null) {
                if (line != null) {
                    val lowerLine = line!!.lowercase()
                    if (lowerLine.contains("frida") ||
                        lowerLine.contains("gadget") ||
                        lowerLine.contains("xposed")) {
                        reader.close()
                        return true
                    }
                }
            }
            reader.close()
        } catch (e: Exception) {
            // Cannot read maps
        }

        // Check for Xposed
        try {
            Class.forName("de.robv.android.xposed.XposedBridge")
            return true
        } catch (e: ClassNotFoundException) {
            // Xposed not found
        }

        // Check for Frida server port
        try {
            val socket = java.net.Socket()
            socket.connect(java.net.InetSocketAddress("127.0.0.1", 27042), 100)
            socket.close()
            return true
        } catch (e: Exception) {
            // Port not open
        }

        return false
    }
}
