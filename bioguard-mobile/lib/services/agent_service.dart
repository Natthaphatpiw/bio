import 'dart:convert';
import 'package:http/http.dart' as http;

/// Agent Service for communicating with BioGuard AI Agent System
///
/// This service submits all signals to the agent and receives
/// adaptive decisions (ALLOW/STEP_UP/HOLD/BLOCK)
class AgentService {
  // Configure before deployment
  static const String _aiServiceBaseUrl = 'http://40.81.244.202:8000';

  /// Decision types from the AI Agent
  static const String decisionAllow = 'ALLOW';
  static const String decisionStepUp = 'STEP_UP';
  static const String decisionHold = 'HOLD';
  static const String decisionBlock = 'BLOCK';

  /// Submit all verification signals to the AI Agent
  ///
  /// Returns an [AgentDecision] with the adaptive decision
  static Future<AgentDecision> submitSignals({
    required String sessionId,
    required String eventType,
    String merchantId = 'default',
    Map<String, dynamic>? integrity,
    Map<String, dynamic>? lightSync,
    Map<String, dynamic>? liveness,
    Map<String, dynamic>? behavior,
    Map<String, dynamic>? context,
    String? deviceId,
    String? userId,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_aiServiceBaseUrl/v1/sessions/$sessionId/signals'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'event_type': eventType,
          'merchant_id': merchantId,
          'integrity': integrity,
          'lightsync': lightSync,
          'liveness': liveness,
          'behavior': behavior,
          'context': context,
          'device_id': deviceId,
          'user_id': userId,
        }),
      ).timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        return AgentDecision.fromJson(jsonDecode(response.body));
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? 'Agent decision failed');
      }
    } catch (e) {
      print('Agent API Error: $e');
      // Return a fallback decision for demo
      return AgentDecision.fallback(sessionId);
    }
  }

  /// Get the latest decision for a session
  static Future<AgentDecision?> getDecision(String sessionId) async {
    try {
      final response = await http.get(
        Uri.parse('$_aiServiceBaseUrl/v1/sessions/$sessionId/decision'),
        headers: {
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return AgentDecision.fromJson(jsonDecode(response.body));
      } else if (response.statusCode == 404) {
        return null;
      } else {
        throw Exception('Failed to get decision');
      }
    } catch (e) {
      print('Agent API Error: $e');
      return null;
    }
  }

  /// Get session status
  static Future<SessionStatus?> getSessionStatus(String sessionId) async {
    try {
      final response = await http.get(
        Uri.parse('$_aiServiceBaseUrl/v1/sessions/$sessionId/status'),
        headers: {
          'Content-Type': 'application/json',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return SessionStatus.fromJson(jsonDecode(response.body));
      } else if (response.statusCode == 404) {
        return null;
      } else {
        throw Exception('Failed to get session status');
      }
    } catch (e) {
      print('Agent API Error: $e');
      return null;
    }
  }

  /// Build integrity signal payload from environment check result
  static Map<String, dynamic> buildIntegritySignal(Map<String, dynamic> envResult) {
    return {
      'is_emulator': envResult['emulator'] ?? false,
      'is_rooted': envResult['root'] ?? false,
      'is_hooking': envResult['hooking'] ?? false,
      'is_debuggable': envResult['devMode'] ?? false,
      'is_vpn': envResult['vpn'] ?? false,
      'app_signature_valid': envResult['signatureValid'] ?? true,
      'device_binding_valid': envResult['deviceBindingValid'] ?? true,
      'raw_data': envResult,
    };
  }

  /// Build lightsync signal payload from light-sync result
  static Map<String, dynamic> buildLightSyncSignal(Map<String, dynamic> lsResult) {
    return {
      'score': lsResult['score'] ?? 0.0,
      'quality': lsResult['quality'] ?? 'unknown',
      'rounds_passed': lsResult['roundsPassed'] ?? 0,
      'rounds_total': lsResult['roundsTotal'] ?? 3,
      'raw_data': lsResult,
    };
  }

  /// Build liveness signal payload from face liveness result
  static Map<String, dynamic> buildLivenessSignal(Map<String, dynamic> livenessResult) {
    return {
      'score': livenessResult['confidence'] ?? 0.0,
      'quality': livenessResult['quality'] ?? 'unknown',
      'is_real': livenessResult['isReal'] ?? livenessResult['is_real'] ?? false,
      'confidence': livenessResult['confidence'] ?? 0.0,
      'raw_data': livenessResult,
    };
  }

  /// Build transaction context for transfer events
  static Map<String, dynamic> buildTransactionContext({
    double? amount,
    String currency = 'THB',
    String? recipientId,
    String? recipientName,
    bool isNewPayee = false,
    int deviceAgeDays = 0,
    int userAccountAgeDays = 0,
    int transactionCount24h = 0,
  }) {
    return {
      'amount': amount,
      'currency': currency,
      'recipient_id': recipientId,
      'recipient_name': recipientName,
      'is_new_payee': isNewPayee,
      'device_age_days': deviceAgeDays,
      'user_account_age_days': userAccountAgeDays,
      'transaction_count_24h': transactionCount24h,
    };
  }
}

/// Represents the AI Agent's decision
class AgentDecision {
  final String sessionId;
  final String decision;
  final double finalRisk;
  final List<String> reasonCodes;
  final String explanation;
  final NextAction nextAction;
  final String? caseId;
  final bool isDemo;

  AgentDecision({
    required this.sessionId,
    required this.decision,
    required this.finalRisk,
    required this.reasonCodes,
    required this.explanation,
    required this.nextAction,
    this.caseId,
    this.isDemo = false,
  });

  factory AgentDecision.fromJson(Map<String, dynamic> json) {
    return AgentDecision(
      sessionId: json['session_id'] ?? '',
      decision: json['decision'] ?? 'ALLOW',
      finalRisk: (json['final_risk'] ?? 0.0).toDouble(),
      reasonCodes: List<String>.from(json['reason_codes'] ?? []),
      explanation: json['explanation'] ?? '',
      nextAction: NextAction.fromJson(json['next_action'] ?? {}),
      caseId: json['case_id'],
      isDemo: json['demo'] ?? false,
    );
  }

  /// Create a fallback decision for demo/offline mode
  factory AgentDecision.fallback(String sessionId) {
    return AgentDecision(
      sessionId: sessionId,
      decision: AgentService.decisionAllow,
      finalRisk: 0.1,
      reasonCodes: [],
      explanation: 'Demo mode: All checks passed (offline)',
      nextAction: NextAction(
        type: 'none',
        userMessage: 'Verification complete',
        opsMessage: 'Demo session processed',
        timeoutSeconds: 300,
        retryAllowed: true,
      ),
      isDemo: true,
    );
  }

  /// Check if the decision allows the user to proceed
  bool get isAllowed => decision == AgentService.decisionAllow;

  /// Check if step-up verification is required
  bool get requiresStepUp => decision == AgentService.decisionStepUp;

  /// Check if the session is on hold for manual review
  bool get isOnHold => decision == AgentService.decisionHold;

  /// Check if the session is blocked
  bool get isBlocked => decision == AgentService.decisionBlock;

  /// Get a user-friendly status message
  String get userMessage => nextAction.userMessage;

  /// Get the risk level as a human-readable string
  String get riskLevel {
    if (finalRisk < 0.3) return 'Low';
    if (finalRisk < 0.5) return 'Medium';
    if (finalRisk < 0.7) return 'High';
    return 'Critical';
  }
}

/// Represents the next action from the agent
class NextAction {
  final String type;
  final String userMessage;
  final String opsMessage;
  final int timeoutSeconds;
  final bool retryAllowed;

  NextAction({
    required this.type,
    required this.userMessage,
    required this.opsMessage,
    required this.timeoutSeconds,
    required this.retryAllowed,
  });

  factory NextAction.fromJson(Map<String, dynamic> json) {
    return NextAction(
      type: json['type'] ?? 'none',
      userMessage: json['user_message'] ?? 'Verification complete',
      opsMessage: json['ops_message'] ?? 'Session processed',
      timeoutSeconds: json['timeout_seconds'] ?? 300,
      retryAllowed: json['retry_allowed'] ?? true,
    );
  }

  /// Check if retry is available
  bool get canRetry => retryAllowed && type != 'none';

  /// Check if manual review is pending
  bool get isPendingReview => type == 'manual_review';

  /// Check if light-sync retry is requested
  bool get requiresLightSyncRetry => type == 'retry_lightsync';
}

/// Represents the session status
class SessionStatus {
  final String sessionId;
  final String status;
  final bool hasDecision;
  final String? decision;
  final double? finalRisk;
  final String createdAt;

  SessionStatus({
    required this.sessionId,
    required this.status,
    required this.hasDecision,
    this.decision,
    this.finalRisk,
    required this.createdAt,
  });

  factory SessionStatus.fromJson(Map<String, dynamic> json) {
    return SessionStatus(
      sessionId: json['session_id'] ?? '',
      status: json['status'] ?? 'pending',
      hasDecision: json['has_decision'] ?? false,
      decision: json['decision'],
      finalRisk: json['final_risk']?.toDouble(),
      createdAt: json['created_at'] ?? '',
    );
  }

  bool get isCompleted => status == 'completed';
  bool get isPending => status == 'pending';
}
