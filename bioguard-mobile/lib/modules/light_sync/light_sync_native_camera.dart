import 'dart:typed_data';

import 'package:flutter/services.dart';

class LightSyncNativeCamera {
  static const MethodChannel _channel =
      MethodChannel('com.bioguard.nexus/light_sync_camera');

  Future<Map<String, dynamic>?> open({bool useFront = true}) async {
    try {
      final result = await _channel.invokeMethod<Map<dynamic, dynamic>>(
        'open',
        {'lens': useFront ? 'front' : 'back'},
      );
      if (result == null) return null;
      return Map<String, dynamic>.from(result);
    } catch (_) {
      return null;
    }
  }

  Future<Uint8List?> captureFrame() async {
    try {
      final bytes = await _channel.invokeMethod<Uint8List>('captureFrame');
      return bytes;
    } catch (_) {
      return null;
    }
  }

  Future<void> close() async {
    try {
      await _channel.invokeMethod('close');
    } catch (_) {
      // Ignore close errors.
    }
  }
}
