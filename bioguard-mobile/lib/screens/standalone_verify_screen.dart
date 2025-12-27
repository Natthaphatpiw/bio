import 'package:flutter/material.dart';
import 'dart:async';
import '../modules/environment_shield/security_checker.dart';
import '../modules/light_sync/light_sync_verifier.dart';
import '../modules/face_liveness/liveness_screen.dart';
import '../services/local_storage_service.dart';
import 'result_screen.dart';
import '../theme/app_theme.dart';

/// Standalone verification screen that runs selected modules locally
/// without requiring a server session
class StandaloneVerifyScreen extends StatefulWidget {
  final bool enableModuleA;
  final bool enableModuleB;
  final bool enableModuleC;

  const StandaloneVerifyScreen({
    super.key,
    required this.enableModuleA,
    required this.enableModuleB,
    required this.enableModuleC,
  });

  @override
  State<StandaloneVerifyScreen> createState() => _StandaloneVerifyScreenState();
}

class _StandaloneVerifyScreenState extends State<StandaloneVerifyScreen> {
  // Current step tracking
  int _currentStep = 0;
  bool _isProcessing = false;
  String _statusMessage = 'Preparing verification...';

  // Results for each module
  Map<String, dynamic>? _moduleAResult;
  Map<String, dynamic>? _moduleBResult;
  Map<String, dynamic>? _moduleCResult;

  // Step status
  String _moduleAStatus = 'pending';
  String _moduleBStatus = 'pending';
  String _moduleCStatus = 'pending';

  @override
  void initState() {
    super.initState();
    _startVerificationFlow();
  }

  Future<void> _startVerificationFlow() async {
    setState(() => _isProcessing = true);

    await Future.delayed(const Duration(milliseconds: 500));

    // Run Module A if enabled
    if (widget.enableModuleA) {
      await _runModuleA();
    } else {
      setState(() => _moduleAStatus = 'skipped');
    }

    if (!mounted) return;

    // Run Module B if enabled
    if (widget.enableModuleB) {
      await _runModuleB();
    } else {
      setState(() => _moduleBStatus = 'skipped');
    }

    if (!mounted) return;

    // Run Module C if enabled
    if (widget.enableModuleC) {
      await _runModuleC();
    } else {
      setState(() => _moduleCStatus = 'skipped');
    }

    if (!mounted) return;

    // All modules complete - save and show results
    await _saveAndShowResults();
  }

  Future<void> _runModuleA() async {
    setState(() {
      _currentStep = 1;
      _moduleAStatus = 'running';
      _statusMessage = 'Checking device security...';
    });

    try {
      _moduleAResult = await SecurityChecker.checkEnvironment();

      setState(() {
        _moduleAStatus = _moduleAResult!['isSafe'] == true ? 'passed' : 'failed';
      });

      await Future.delayed(const Duration(milliseconds: 500));
    } catch (e) {
      setState(() {
        _moduleAStatus = 'failed';
        _moduleAResult = {'isSafe': false, 'error': e.toString()};
      });
    }
  }

  Future<void> _runModuleB() async {
    setState(() {
      _currentStep = 2;
      _moduleBStatus = 'running';
      _statusMessage = 'Preparing Light-Sync challenge...';
    });

    await Future.delayed(const Duration(milliseconds: 300));

    if (!mounted) return;

    // Navigate to Light-Sync screen
    final result = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(
        builder: (context) => const LightSyncVerifier(),
      ),
    );

    _moduleBResult = result ?? {'pass': false, 'error': 'Cancelled'};

    setState(() {
      _moduleBStatus = _moduleBResult!['pass'] == true ? 'passed' : 'failed';
    });

    await Future.delayed(const Duration(milliseconds: 300));
  }

  Future<void> _runModuleC() async {
    setState(() {
      _currentStep = 3;
      _moduleCStatus = 'running';
      _statusMessage = 'Preparing face liveness check...';
    });

    await Future.delayed(const Duration(milliseconds: 300));

    if (!mounted) return;

    // Navigate to Face Liveness screen
    final result = await Navigator.push<Map<String, dynamic>>(
      context,
      MaterialPageRoute(
        builder: (context) => const LivenessScreen(),
      ),
    );

    _moduleCResult = result ?? {'isReal': false, 'error': 'Cancelled'};

    setState(() {
      _moduleCStatus = _moduleCResult!['isReal'] == true ? 'passed' : 'failed';
    });

    await Future.delayed(const Duration(milliseconds: 300));
  }

  Future<void> _saveAndShowResults() async {
    setState(() {
      _statusMessage = 'Saving results...';
    });

    // Determine overall status
    bool overallPass = true;

    if (widget.enableModuleA && _moduleAResult?['isSafe'] != true) {
      overallPass = false;
    }
    if (widget.enableModuleB && _moduleBResult?['pass'] != true) {
      overallPass = false;
    }
    if (widget.enableModuleC && _moduleCResult?['isReal'] != true) {
      overallPass = false;
    }

    // Create verification record
    final record = VerificationRecord(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      timestamp: DateTime.now(),
      overallStatus: overallPass ? 'PASSED' : 'FAILED',
      moduleAEnabled: widget.enableModuleA,
      moduleBEnabled: widget.enableModuleB,
      moduleCEnabled: widget.enableModuleC,
      moduleAResult: _moduleAResult,
      moduleBResult: _moduleBResult,
      moduleCResult: _moduleCResult,
    );

    // Save to local storage
    await LocalStorageService.saveVerificationRecord(record);

    if (!mounted) return;

    // Navigate to result screen
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => ResultScreen(record: record),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.navy,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              // Header
              Row(
                children: [
                  IconButton(
                    onPressed: () => _showCancelDialog(),
                    icon: const Icon(Icons.close, color: Colors.white),
                  ),
                  const Expanded(
                    child: Text(
                      'Verification in Progress',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                  ),
                  const SizedBox(width: 48),
                ],
              ),

              const SizedBox(height: 40),

              // Progress Indicator
              _buildProgressIndicator(),

              const SizedBox(height: 40),

              // Current Status
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.navySurface,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (_isProcessing)
                      const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(
                            AppColors.deepBlue,
                          ),
                        ),
                      ),
                    const SizedBox(width: 16),
                    Flexible(
                      child: Text(
                        _statusMessage,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 16,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 40),

              // Module Status Cards
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    children: [
                      if (widget.enableModuleA)
                        _buildModuleCard(
                          module: 'A',
                          title: 'Environment Shield',
                          description: 'Root, Emulator & Hook Detection',
                          icon: Icons.security_rounded,
                          color: AppColors.success,
                          status: _moduleAStatus,
                          result: _moduleAResult,
                        ),
                      if (widget.enableModuleB) ...[
                        const SizedBox(height: 16),
                        _buildModuleCard(
                          module: 'B',
                          title: 'Light-Sync Challenge',
                          description: 'Physics-based Reflection Analysis',
                          icon: Icons.flash_on_rounded,
                          color: AppColors.softOrange,
                          status: _moduleBStatus,
                          result: _moduleBResult,
                        ),
                      ],
                      if (widget.enableModuleC) ...[
                        const SizedBox(height: 16),
                        _buildModuleCard(
                          module: 'C',
                          title: 'AI Face Liveness',
                          description: 'MiniFASNet Detection',
                          icon: Icons.face_rounded,
                          color: AppColors.danger,
                          status: _moduleCStatus,
                          result: _moduleCResult,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProgressIndicator() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (widget.enableModuleA) ...[
          _buildStepDot('A', _moduleAStatus),
          if (widget.enableModuleB || widget.enableModuleC)
            _buildConnector(_moduleAStatus == 'passed' || _moduleAStatus == 'failed'),
        ],
        if (widget.enableModuleB) ...[
          _buildStepDot('B', _moduleBStatus),
          if (widget.enableModuleC)
            _buildConnector(_moduleBStatus == 'passed' || _moduleBStatus == 'failed'),
        ],
        if (widget.enableModuleC) _buildStepDot('C', _moduleCStatus),
      ],
    );
  }

  Widget _buildStepDot(String label, String status) {
    Color bgColor;
    Color textColor = Colors.white;
    Widget child;

    switch (status) {
      case 'running':
        bgColor = AppColors.deepBlue;
        child = const SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
          ),
        );
        break;
      case 'passed':
        bgColor = AppColors.success;
        child = const Icon(Icons.check, color: Colors.white, size: 24);
        break;
      case 'failed':
        bgColor = AppColors.danger;
        child = const Icon(Icons.close, color: Colors.white, size: 24);
        break;
      case 'skipped':
        bgColor = AppColors.textMuted;
        child = const Icon(Icons.remove, color: Colors.white, size: 24);
        break;
      default:
        bgColor = AppColors.navySurface;
        textColor = Colors.white54;
        child = Text(
          label,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: textColor,
          ),
        );
    }

    return Container(
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: bgColor,
        shape: BoxShape.circle,
        boxShadow: status == 'running'
            ? [
                BoxShadow(
                  color: bgColor.withOpacity(0.5),
                  blurRadius: 12,
                  spreadRadius: 2,
                ),
              ]
            : null,
      ),
      child: Center(child: child),
    );
  }

  Widget _buildConnector(bool active) {
    return Container(
      width: 40,
      height: 2,
      color: active ? AppColors.success : AppColors.navySurface,
    );
  }

  Widget _buildModuleCard({
    required String module,
    required String title,
    required String description,
    required IconData icon,
    required Color color,
    required String status,
    Map<String, dynamic>? result,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.navySurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: _getStatusColor(status).withOpacity(0.5),
          width: status == 'running' ? 2 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: color, size: 24),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Module $module: $title',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      description,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.white.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ),
              _buildStatusBadge(status),
            ],
          ),

          // Show result details if available
          if (result != null && status != 'running') ...[
            const SizedBox(height: 12),
            const Divider(color: Colors.white12),
            const SizedBox(height: 8),
            _buildResultDetails(module, result),
          ],
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color color;
    String text;
    IconData? icon;

    switch (status) {
      case 'running':
        color = AppColors.deepBlue;
        text = 'Running';
        break;
      case 'passed':
        color = AppColors.success;
        text = 'Passed';
        icon = Icons.check_circle;
        break;
      case 'failed':
        color = AppColors.danger;
        text = 'Failed';
        icon = Icons.cancel;
        break;
      case 'skipped':
        color = AppColors.textMuted;
        text = 'Skipped';
        icon = Icons.remove_circle;
        break;
      default:
        color = AppColors.textMuted;
        text = 'Pending';
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (status == 'running')
            SizedBox(
              width: 12,
              height: 12,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            )
          else if (icon != null)
            Icon(icon, color: color, size: 14),
          const SizedBox(width: 6),
          Text(
            text,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultDetails(String module, Map<String, dynamic> result) {
    List<Widget> details = [];

    if (module == 'A') {
      details = [
        _buildDetailRow('Device Safe', result['isSafe'] == true),
        _buildDetailRow('Root Access', result['root'] != true),
        _buildDetailRow('Emulator', result['emulator'] != true),
        _buildDetailRow('Hook Detection', result['hooking'] != true),
      ];
    } else if (module == 'B') {
      details = [
        _buildDetailRow('Light Response', result['pass'] == true),
        if (result['confidence'] != null)
          _buildDetailRow(
            'Confidence',
            true,
            value: '${(result['confidence'] * 100).toStringAsFixed(0)}%',
          ),
      ];
    } else if (module == 'C') {
      details = [
        _buildDetailRow('Real Face', result['isReal'] == true),
        if (result['confidence'] != null)
          _buildDetailRow(
            'Confidence',
            true,
            value: '${(result['confidence'] * 100).toStringAsFixed(0)}%',
          ),
      ];
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: details,
    );
  }

  Widget _buildDetailRow(String label, bool passed, {String? value}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: (passed ? AppColors.success : AppColors.danger)
            .withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            passed ? Icons.check_circle : Icons.cancel,
            size: 14,
            color: passed ? AppColors.success : AppColors.danger,
          ),
          const SizedBox(width: 6),
          Text(
            value ?? label,
            style: TextStyle(
              fontSize: 12,
              color: passed ? AppColors.success : AppColors.danger,
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'running':
        return AppColors.deepBlue;
      case 'passed':
        return AppColors.success;
      case 'failed':
        return AppColors.danger;
      default:
        return AppColors.textMuted;
    }
  }

  void _showCancelDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.navySurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: const Text(
          'Cancel Verification?',
          style: TextStyle(color: Colors.white),
        ),
        content: const Text(
          'Progress will be lost. Are you sure you want to cancel?',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Continue'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context); // Close dialog
              Navigator.pop(context); // Go back to home
            },
            child: const Text(
              'Cancel',
              style: TextStyle(color: AppColors.danger),
            ),
          ),
        ],
      ),
    );
  }
}
