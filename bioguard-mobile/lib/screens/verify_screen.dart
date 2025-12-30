import 'package:flutter/material.dart';
import 'dart:async';
import '../modules/environment_shield/security_checker.dart';
import '../modules/light_sync/light_sync_verifier.dart';
import '../modules/face_liveness/liveness_screen.dart';
import '../services/api_service.dart';
import '../services/agent_service.dart';
import '../theme/app_theme.dart';

enum VerificationStep {
  initializing,
  environmentCheck,
  lightSync,
  faceLiveness,
  submitting,
  agentDecision,
  completed,
  stepUp,
  hold,
  blocked,
  failed,
}

class VerifyScreen extends StatefulWidget {
  final String sessionId;
  final String eventType;
  final bool useAgentMode;

  const VerifyScreen({
    super.key,
    required this.sessionId,
    this.eventType = 'EKYC',
    this.useAgentMode = true,
  });

  @override
  State<VerifyScreen> createState() => _VerifyScreenState();
}

class _VerifyScreenState extends State<VerifyScreen> {
  VerificationStep _currentStep = VerificationStep.initializing;
  Map<String, dynamic> _results = {};
  String _errorMessage = '';
  String _userMessage = '';

  // Module results
  Map<String, dynamic>? _environmentResult;
  Map<String, dynamic>? _lightSyncResult;
  Map<String, dynamic>? _faceLivenessResult;

  // Agent decision
  AgentDecision? _agentDecision;

  @override
  void initState() {
    super.initState();
    _startVerification();
  }

  Future<void> _startVerification() async {
    await Future.delayed(const Duration(milliseconds: 500));

    // Step 1: Environment Check (Module A)
    setState(() => _currentStep = VerificationStep.environmentCheck);
    _environmentResult = await SecurityChecker.checkEnvironment();

    // In agent mode, don't fail immediately - let agent decide
    if (!widget.useAgentMode && _environmentResult!['isSafe'] != true) {
      setState(() {
        _currentStep = VerificationStep.failed;
        _errorMessage = _buildEnvironmentFailureMessage(_environmentResult!);
      });
      return;
    }

    await Future.delayed(const Duration(milliseconds: 800));

    // Step 2: Light-Sync Challenge (Module B)
    setState(() => _currentStep = VerificationStep.lightSync);

    if (!mounted) return;

    final lightSyncResult = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(
        builder: (context) => const LightSyncVerifier(),
      ),
    );

    // In agent mode, collect result even if failed
    _lightSyncResult = lightSyncResult ?? {'pass': false, 'score': 0.0};

    if (!widget.useAgentMode && (lightSyncResult == null || lightSyncResult['pass'] != true)) {
      setState(() {
        _currentStep = VerificationStep.failed;
        _errorMessage = 'Light-Sync verification failed';
      });
      return;
    }

    await Future.delayed(const Duration(milliseconds: 500));

    // Step 3: Face Liveness (Module C)
    setState(() => _currentStep = VerificationStep.faceLiveness);

    if (!mounted) return;

    final faceLivenessResult = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(
        builder: (context) => const LivenessScreen(),
      ),
    );

    // In agent mode, collect result even if failed
    _faceLivenessResult = faceLivenessResult ?? {'isReal': false, 'confidence': 0.0};

    if (!widget.useAgentMode && (faceLivenessResult == null || faceLivenessResult['isReal'] != true)) {
      setState(() {
        _currentStep = VerificationStep.failed;
        _errorMessage = 'Face liveness verification failed';
      });
      return;
    }

    // Step 4: Submit to Agent or Legacy API
    setState(() => _currentStep = VerificationStep.submitting);

    _results = {
      'environment': _environmentResult,
      'lightSync': _lightSyncResult,
      'faceLiveness': _faceLivenessResult,
    };

    if (widget.useAgentMode) {
      await _submitToAgent();
    } else {
      await _submitToLegacyApi();
    }
  }

  Future<void> _submitToAgent() async {
    setState(() => _currentStep = VerificationStep.agentDecision);

    try {
      // Build signal payloads for agent
      final integritySignal = AgentService.buildIntegritySignal(_environmentResult!);
      final lightSyncSignal = AgentService.buildLightSyncSignal(_lightSyncResult!);
      final livenessSignal = AgentService.buildLivenessSignal(_faceLivenessResult!);

      // Submit to agent
      _agentDecision = await AgentService.submitSignals(
        sessionId: widget.sessionId,
        eventType: widget.eventType,
        integrity: integritySignal,
        lightSync: lightSyncSignal,
        liveness: livenessSignal,
      );

      // Handle agent decision
      _handleAgentDecision(_agentDecision!);
    } catch (e) {
      setState(() {
        _currentStep = VerificationStep.failed;
        _errorMessage = 'Agent decision failed: $e';
      });
    }
  }

  void _handleAgentDecision(AgentDecision decision) {
    setState(() {
      _userMessage = decision.userMessage;

      switch (decision.decision) {
        case AgentService.decisionAllow:
          _currentStep = VerificationStep.completed;
          break;
        case AgentService.decisionStepUp:
          _currentStep = VerificationStep.stepUp;
          _errorMessage = decision.explanation;
          break;
        case AgentService.decisionHold:
          _currentStep = VerificationStep.hold;
          _errorMessage = decision.explanation;
          break;
        case AgentService.decisionBlock:
          _currentStep = VerificationStep.blocked;
          _errorMessage = decision.explanation;
          break;
        default:
          _currentStep = VerificationStep.completed;
      }
    });
  }

  Future<void> _submitToLegacyApi() async {
    try {
      await ApiService.submitVerificationResult(
        sessionId: widget.sessionId,
        result: _results,
        overallStatus: 'COMPLETED',
      );
      setState(() => _currentStep = VerificationStep.completed);
    } catch (e) {
      // For demo, still show completed
      setState(() => _currentStep = VerificationStep.completed);
    }
  }

  Future<void> _retryLightSync() async {
    setState(() => _currentStep = VerificationStep.lightSync);

    if (!mounted) return;

    final lightSyncResult = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(
        builder: (context) => const LightSyncVerifier(),
      ),
    );

    _lightSyncResult = lightSyncResult ?? {'pass': false, 'score': 0.0};

    // Re-submit to agent
    await _submitToAgent();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              // Header
              Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close, color: AppColors.textPrimary),
                  ),
                  const Expanded(
                    child: Text(
                      'Verification',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                  // Agent mode indicator
                  if (widget.useAgentMode)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.deepBlue.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.smart_toy, size: 16, color: AppColors.deepBlue),
                          const SizedBox(width: 4),
                          Text(
                            'AI',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: AppColors.deepBlue,
                            ),
                          ),
                        ],
                      ),
                    )
                  else
                    const SizedBox(width: 48),
                ],
              ),
              const SizedBox(height: 16),

              // Session ID
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.border),
                ),
                child: Text(
                  'Session: ${widget.sessionId}',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppColors.textMuted,
                    fontFamily: 'monospace',
                  ),
                ),
              ),

              const Spacer(),

              // Status Display
              _buildStatusDisplay(),

              const SizedBox(height: 24),

              // Agent Decision Details (if available)
              if (_agentDecision != null && _currentStep != VerificationStep.agentDecision)
                _buildAgentDecisionCard(),

              const SizedBox(height: 24),

              // Progress Steps
              _buildProgressSteps(),

              const Spacer(),

              // Action Buttons
              _buildActionButtons(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAgentDecisionCard() {
    final decision = _agentDecision!;
    Color riskColor;

    if (decision.finalRisk < 0.3) {
      riskColor = AppColors.success;
    } else if (decision.finalRisk < 0.5) {
      riskColor = AppColors.softOrange;
    } else if (decision.finalRisk < 0.7) {
      riskColor = Colors.orange;
    } else {
      riskColor = AppColors.danger;
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.analytics, size: 20, color: AppColors.deepBlue),
              const SizedBox(width: 8),
              Text(
                'AI Analysis',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: riskColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  'Risk: ${(decision.finalRisk * 100).toStringAsFixed(0)}%',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: riskColor,
                  ),
                ),
              ),
            ],
          ),
          if (decision.reasonCodes.isNotEmpty) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: decision.reasonCodes.map((code) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.border,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    code,
                    style: TextStyle(
                      fontSize: 10,
                      fontFamily: 'monospace',
                      color: AppColors.textMuted,
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
          if (decision.caseId != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.folder_open, size: 16, color: AppColors.softOrange),
                const SizedBox(width: 4),
                Text(
                  'Case: ${decision.caseId}',
                  style: TextStyle(
                    fontSize: 11,
                    fontFamily: 'monospace',
                    color: AppColors.softOrange,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    switch (_currentStep) {
      case VerificationStep.completed:
        return SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: () => Navigator.pop(context, {'success': true, 'decision': _agentDecision}),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.success,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
            child: const Text(
              'Verification Complete',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
          ),
        );

      case VerificationStep.stepUp:
        return Column(
          children: [
            if (_agentDecision?.nextAction.requiresLightSyncRetry ?? false)
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _retryLightSync,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.softOrange,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text(
                    'Retry Light-Sync',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: OutlinedButton(
                onPressed: () => Navigator.pop(context, {'success': false, 'decision': _agentDecision}),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.textMuted,
                  side: BorderSide(color: AppColors.border),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: const Text('Cancel'),
              ),
            ),
          ],
        );

      case VerificationStep.hold:
        return SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: () => Navigator.pop(context, {'success': false, 'decision': _agentDecision, 'pending_review': true}),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.softOrange,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
            child: const Text(
              'Pending Review',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
          ),
        );

      case VerificationStep.blocked:
      case VerificationStep.failed:
        return SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton(
            onPressed: () => Navigator.pop(context, {'success': false, 'decision': _agentDecision}),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.danger,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
            child: Text(
              _currentStep == VerificationStep.blocked ? 'Session Blocked' : 'Try Again',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
          ),
        );

      default:
        return const SizedBox.shrink();
    }
  }

  Widget _buildStatusDisplay() {
    IconData icon;
    Color color;
    String title;
    String subtitle;

    switch (_currentStep) {
      case VerificationStep.initializing:
        icon = Icons.hourglass_empty;
        color = AppColors.deepBlue;
        title = 'Initializing';
        subtitle = 'Preparing verification modules...';
        break;
      case VerificationStep.environmentCheck:
        icon = Icons.security;
        color = AppColors.deepBlue;
        title = 'Environment Check';
        subtitle = 'Scanning device security...';
        break;
      case VerificationStep.lightSync:
        icon = Icons.flash_on;
        color = AppColors.softOrange;
        title = 'Light-Sync Challenge';
        subtitle = 'Verifying physical presence...';
        break;
      case VerificationStep.faceLiveness:
        icon = Icons.face;
        color = AppColors.blue;
        title = 'Face Liveness';
        subtitle = 'AI verification in progress...';
        break;
      case VerificationStep.submitting:
        icon = Icons.cloud_upload;
        color = AppColors.deepBlue;
        title = 'Submitting';
        subtitle = 'Sending results to server...';
        break;
      case VerificationStep.agentDecision:
        icon = Icons.smart_toy;
        color = AppColors.deepBlue;
        title = 'AI Agent';
        subtitle = 'Making adaptive decision...';
        break;
      case VerificationStep.completed:
        icon = Icons.check_circle;
        color = AppColors.success;
        title = 'Verified!';
        subtitle = _userMessage.isNotEmpty ? _userMessage : 'All checks passed successfully';
        break;
      case VerificationStep.stepUp:
        icon = Icons.warning_amber;
        color = AppColors.softOrange;
        title = 'Additional Verification';
        subtitle = _userMessage.isNotEmpty ? _userMessage : 'Please complete additional steps';
        break;
      case VerificationStep.hold:
        icon = Icons.pause_circle;
        color = AppColors.softOrange;
        title = 'Under Review';
        subtitle = _userMessage.isNotEmpty ? _userMessage : 'Your verification is being reviewed';
        break;
      case VerificationStep.blocked:
        icon = Icons.block;
        color = AppColors.danger;
        title = 'Blocked';
        subtitle = _userMessage.isNotEmpty ? _userMessage : 'Verification cannot proceed';
        break;
      case VerificationStep.failed:
        icon = Icons.error;
        color = AppColors.danger;
        title = 'Verification Failed';
        subtitle = _errorMessage;
        break;
    }

    return Column(
      children: [
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
            border: Border.all(
              color: color.withOpacity(0.3),
              width: 2,
            ),
          ),
          child: Icon(icon, size: 60, color: color),
        ),
        const SizedBox(height: 24),
        Text(
          title,
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 8),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Text(
            subtitle,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: AppColors.textMuted,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildProgressSteps() {
    final isAgentMode = widget.useAgentMode;

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildStepIndicator(
          'A',
          _currentStep.index > VerificationStep.environmentCheck.index,
          _currentStep == VerificationStep.environmentCheck,
        ),
        _buildStepConnector(
          _currentStep.index > VerificationStep.environmentCheck.index,
        ),
        _buildStepIndicator(
          'B',
          _currentStep.index > VerificationStep.lightSync.index,
          _currentStep == VerificationStep.lightSync,
        ),
        _buildStepConnector(
          _currentStep.index > VerificationStep.lightSync.index,
        ),
        _buildStepIndicator(
          'C',
          _currentStep.index > VerificationStep.faceLiveness.index,
          _currentStep == VerificationStep.faceLiveness,
        ),
        if (isAgentMode) ...[
          _buildStepConnector(
            _currentStep.index > VerificationStep.faceLiveness.index,
          ),
          _buildStepIndicator(
            'AI',
            _currentStep.index > VerificationStep.agentDecision.index,
            _currentStep == VerificationStep.agentDecision ||
                _currentStep == VerificationStep.submitting,
            isAgent: true,
          ),
        ],
      ],
    );
  }

  Widget _buildStepIndicator(String label, bool completed, bool active, {bool isAgent = false}) {
    Color bgColor;
    Color textColor;

    if (completed) {
      bgColor = AppColors.success;
      textColor = Colors.white;
    } else if (active) {
      bgColor = isAgent ? AppColors.deepBlue : AppColors.deepBlue;
      textColor = Colors.white;
    } else {
      bgColor = AppColors.border;
      textColor = AppColors.textMuted;
    }

    return Container(
      width: isAgent ? 56 : 48,
      height: 48,
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: isAgent ? BorderRadius.circular(24) : null,
        shape: isAgent ? BoxShape.rectangle : BoxShape.circle,
      ),
      child: Center(
        child: completed
            ? const Icon(Icons.check, color: Colors.white, size: 24)
            : isAgent
                ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.smart_toy, color: textColor, size: 18),
                    ],
                  )
                : Text(
                    label,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: textColor,
                    ),
                  ),
      ),
    );
  }

  Widget _buildStepConnector(bool completed) {
    return Container(
      width: 40,
      height: 2,
      color: completed ? AppColors.success : AppColors.border,
    );
  }

  String _buildEnvironmentFailureMessage(Map<String, dynamic> result) {
    final reasons = <String>[];
    if (result['devMode'] == true) reasons.add('Developer options enabled');
    if (result['usbDebug'] == true) reasons.add('USB debugging enabled');
    if (result['root'] == true) reasons.add('Root access detected');
    if (result['emulator'] == true) reasons.add('Emulator detected');
    if (result['hooking'] == true) reasons.add('Hooking framework detected');

    if (reasons.isEmpty) {
      return 'Device security check failed';
    }

    return 'Device security check failed: ${reasons.join(', ')}';
  }
}
