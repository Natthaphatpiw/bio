import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// Model for verification record
class VerificationRecord {
  final String id;
  final DateTime timestamp;
  final String overallStatus; // 'PASSED' or 'FAILED'

  final bool moduleAEnabled;
  final bool moduleBEnabled;
  final bool moduleCEnabled;

  final Map<String, dynamic>? moduleAResult;
  final Map<String, dynamic>? moduleBResult;
  final Map<String, dynamic>? moduleCResult;

  VerificationRecord({
    required this.id,
    required this.timestamp,
    required this.overallStatus,
    required this.moduleAEnabled,
    required this.moduleBEnabled,
    required this.moduleCEnabled,
    this.moduleAResult,
    this.moduleBResult,
    this.moduleCResult,
  });

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'timestamp': timestamp.toIso8601String(),
      'overallStatus': overallStatus,
      'moduleAEnabled': moduleAEnabled,
      'moduleBEnabled': moduleBEnabled,
      'moduleCEnabled': moduleCEnabled,
      'moduleAResult': moduleAResult,
      'moduleBResult': moduleBResult,
      'moduleCResult': moduleCResult,
    };
  }

  /// Create from JSON
  factory VerificationRecord.fromJson(Map<String, dynamic> json) {
    return VerificationRecord(
      id: json['id'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      overallStatus: json['overallStatus'] as String,
      moduleAEnabled: json['moduleAEnabled'] as bool,
      moduleBEnabled: json['moduleBEnabled'] as bool,
      moduleCEnabled: json['moduleCEnabled'] as bool,
      moduleAResult: json['moduleAResult'] as Map<String, dynamic>?,
      moduleBResult: json['moduleBResult'] as Map<String, dynamic>?,
      moduleCResult: json['moduleCResult'] as Map<String, dynamic>?,
    );
  }
}

/// Service for managing local storage operations
class LocalStorageService {
  static const String _historyKey = 'verification_history';
  static const int _maxHistoryItems = 50; // Keep last 50 records

  /// Save a verification record to history
  static Future<void> saveVerificationRecord(VerificationRecord record) async {
    try {
      final prefs = await SharedPreferences.getInstance();

      // Get existing history
      final historyJson = prefs.getStringList(_historyKey) ?? [];

      // Convert record to JSON string
      final recordJson = jsonEncode(record.toJson());

      // Add new record at the beginning
      historyJson.insert(0, recordJson);

      // Keep only the last N items
      if (historyJson.length > _maxHistoryItems) {
        historyJson.removeRange(_maxHistoryItems, historyJson.length);
      }

      // Save back
      await prefs.setStringList(_historyKey, historyJson);
    } catch (e) {
      print('Error saving verification record: $e');
    }
  }

  /// Get all verification history
  static Future<List<VerificationRecord>> getVerificationHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final historyJson = prefs.getStringList(_historyKey) ?? [];

      return historyJson.map((jsonString) {
        final json = jsonDecode(jsonString) as Map<String, dynamic>;
        return VerificationRecord.fromJson(json);
      }).toList();
    } catch (e) {
      print('Error loading verification history: $e');
      return [];
    }
  }

  /// Get a specific record by ID
  static Future<VerificationRecord?> getRecordById(String id) async {
    final history = await getVerificationHistory();
    try {
      return history.firstWhere((record) => record.id == id);
    } catch (e) {
      return null;
    }
  }

  /// Delete a specific record
  static Future<void> deleteRecord(String id) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final historyJson = prefs.getStringList(_historyKey) ?? [];

      historyJson.removeWhere((jsonString) {
        final json = jsonDecode(jsonString) as Map<String, dynamic>;
        return json['id'] == id;
      });

      await prefs.setStringList(_historyKey, historyJson);
    } catch (e) {
      print('Error deleting record: $e');
    }
  }

  /// Clear all history
  static Future<void> clearHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_historyKey);
    } catch (e) {
      print('Error clearing history: $e');
    }
  }

  /// Get statistics
  static Future<Map<String, int>> getStatistics() async {
    final history = await getVerificationHistory();

    int passed = 0;
    int failed = 0;

    for (final record in history) {
      if (record.overallStatus == 'PASSED') {
        passed++;
      } else {
        failed++;
      }
    }

    return {
      'total': history.length,
      'passed': passed,
      'failed': failed,
    };
  }
}
