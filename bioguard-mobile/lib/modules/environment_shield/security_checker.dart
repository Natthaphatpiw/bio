import 'package:flutter/services.dart';
import 'dart:io';

/// Module A: Environment Shield
/// Checks device security status using native Android APIs
class SecurityChecker {
  static const MethodChannel _channel =
      MethodChannel('com.bioguard.nexus/security');

  /// Performs comprehensive security check
  /// Returns a map with security status for each check
  static Future<Map<String, dynamic>> checkEnvironment() async {
    if (!Platform.isAndroid) {
      // For iOS or other platforms, return mock safe result
      return {
        'isSafe': true,
        'devMode': false,
        'usbDebug': false,
        'root': false,
        'emulator': false,
        'hooking': false,
        'platform': Platform.operatingSystem,
      };
    }

    try {
      final result = await _channel.invokeMethod('checkEnvironment');
      return Map<String, dynamic>.from(result);
    } on PlatformException catch (e) {
      // If native check fails, perform basic Dart-based checks
      return _performDartBasedChecks();
    } on MissingPluginException {
      // Channel not available, use fallback
      return _performDartBasedChecks();
    }
  }

  /// Fallback security checks using pure Dart
  static Map<String, dynamic> _performDartBasedChecks() {
    bool isEmulator = _checkEmulatorDart();
    bool isRooted = _checkRootDart();

    return {
      'isSafe': !isEmulator && !isRooted,
      'devMode': false, // Cannot check from Dart
      'usbDebug': false, // Cannot check from Dart
      'root': isRooted,
      'emulator': isEmulator,
      'hooking': false, // Cannot check from Dart
      'fallback': true,
    };
  }

  /// Basic emulator detection using Dart
  static bool _checkEmulatorDart() {
    // Check for common emulator indicators
    final emulatorIndicators = [
      'sdk_gphone',
      'emulator',
      'android sdk',
      'goldfish',
      'ranchu',
    ];

    final deviceInfo = Platform.operatingSystemVersion.toLowerCase();
    for (var indicator in emulatorIndicators) {
      if (deviceInfo.contains(indicator)) {
        return true;
      }
    }
    return false;
  }

  /// Basic root detection using Dart
  static bool _checkRootDart() {
    if (!Platform.isAndroid) return false;

    final suPaths = [
      '/system/bin/su',
      '/system/xbin/su',
      '/sbin/su',
      '/data/local/xbin/su',
      '/data/local/bin/su',
    ];

    for (var path in suPaths) {
      try {
        if (File(path).existsSync()) {
          return true;
        }
      } catch (e) {
        // Permission denied - continue checking
      }
    }
    return false;
  }
}
