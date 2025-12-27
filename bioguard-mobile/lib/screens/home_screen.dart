import 'package:flutter/material.dart';
import 'standalone_verify_screen.dart';
import 'history_screen.dart';
import 'verify_screen.dart';
import '../theme/app_theme.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // Module selection state
  bool _moduleA = true; // Environment Shield
  bool _moduleB = true; // Light-Sync
  bool _moduleC = true; // Face Liveness
  final TextEditingController _sessionController = TextEditingController();
  String? _sessionError;

  @override
  void dispose() {
    _sessionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(
                          color: AppColors.navy,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: const [
                            BoxShadow(
                              color: Color(0x331E3A8A),
                              blurRadius: 18,
                              offset: Offset(0, 8),
                            ),
                          ],
                        ),
                        child: const Icon(
                          Icons.shield_rounded,
                          size: 30,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: const [
                          Text(
                            'BioGuard Nexus',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Secure Verification Agent',
                            style: TextStyle(
                              fontSize: 12,
                              color: AppColors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  IconButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const HistoryScreen(),
                        ),
                      );
                    },
                    icon: const Icon(
                      Icons.history_rounded,
                      color: AppColors.navy,
                      size: 26,
                    ),
                    tooltip: 'View History',
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Session Entry
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Enter Session',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Paste the Verification URL, Direct App Link, or Session ID.',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppColors.textMuted,
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _sessionController,
                      onChanged: (_) {
                        if (_sessionError != null) {
                          setState(() => _sessionError = null);
                        }
                      },
                      decoration: InputDecoration(
                        hintText: 'bioguard://verify?session_id=...',
                        errorText: _sessionError,
                      ),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton.icon(
                        onPressed: _openSessionFromInput,
                        icon: const Icon(Icons.login_rounded),
                        label: const Text('Open Session'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.deepBlue,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),

              // Module Selection Section
              const Text(
                'Select Verification Modules',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Choose which security checks to perform',
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.textMuted,
                ),
              ),
              const SizedBox(height: 20),

              // Module A - Environment Shield
              _buildModuleToggle(
                icon: Icons.security_rounded,
                title: 'Module A: Environment Shield',
                description: 'Root, Emulator, USB Debug & Hook Detection',
                color: AppColors.success,
                value: _moduleA,
                onChanged: (value) => setState(() => _moduleA = value),
              ),
              const SizedBox(height: 12),

              // Module B - Light-Sync
              _buildModuleToggle(
                icon: Icons.flash_on_rounded,
                title: 'Module B: Light-Sync Challenge',
                description: 'Physics-based Reflection Analysis',
                color: AppColors.softOrange,
                value: _moduleB,
                onChanged: (value) => setState(() => _moduleB = value),
              ),
              const SizedBox(height: 12),

              // Module C - Face Liveness
              _buildModuleToggle(
                icon: Icons.face_rounded,
                title: 'Module C: AI Face Liveness',
                description: 'MiniFASNet Deep Learning Detection',
                color: AppColors.deepBlue,
                value: _moduleC,
                onChanged: (value) => setState(() => _moduleC = value),
              ),

              const SizedBox(height: 32),

              // Selected Modules Summary
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.border,
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.checklist_rounded,
                      color: AppColors.deepBlue,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Selected Modules',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _getSelectedModulesText(),
                            style: TextStyle(
                              fontSize: 13,
                              color: AppColors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.deepBlue.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        '${_getSelectedCount()}/3',
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: AppColors.deepBlue,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // Start Verification Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _canStartVerification()
                      ? () => _startVerification(context)
                      : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.deepBlue,
                    foregroundColor: Colors.white,
                    disabledBackgroundColor: AppColors.border,
                    disabledForegroundColor: AppColors.textMuted,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    elevation: _canStartVerification() ? 8 : 0,
                    shadowColor: AppColors.deepBlue.withOpacity(0.3),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        _canStartVerification()
                            ? Icons.verified_user_rounded
                            : Icons.block_rounded,
                        size: 24,
                      ),
                      const SizedBox(width: 12),
                      Text(
                        _canStartVerification()
                            ? 'Start Verification'
                            : 'Select at least 1 module',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Info Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.deepBlue.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.deepBlue.withOpacity(0.15),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.info_outline_rounded,
                      color: AppColors.deepBlue,
                      size: 24,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'All verification data is processed locally on your device. Results are saved in history.',
                        style: TextStyle(
                          fontSize: 13,
                          color: AppColors.textMuted,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildModuleToggle({
    required IconData icon,
    required String title,
    required String description,
    required Color color,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return GestureDetector(
      onTap: () => onChanged(!value),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: value
              ? color.withOpacity(0.08)
              : AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: value ? color.withOpacity(0.6) : AppColors.border,
            width: 1.5,
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: value
                    ? color.withOpacity(0.15)
                    : AppColors.background,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                icon,
                color: value ? color : AppColors.textMuted,
                size: 24,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: value ? AppColors.textPrimary : AppColors.textMuted,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: TextStyle(
                      fontSize: 12,
                      color: value
                          ? AppColors.textMuted
                          : AppColors.textMuted.withOpacity(0.7),
                    ),
                  ),
                ],
              ),
            ),
            // Toggle Switch
            Switch(
              value: value,
              onChanged: onChanged,
              activeColor: color,
              activeTrackColor: color.withOpacity(0.3),
              inactiveThumbColor: AppColors.textMuted,
              inactiveTrackColor: AppColors.border,
            ),
          ],
        ),
      ),
    );
  }

  void _openSessionFromInput() {
    final sessionId = _extractSessionId(_sessionController.text);
    if (sessionId == null) {
      setState(() {
        _sessionError = 'Invalid link or session ID';
      });
      return;
    }

    setState(() {
      _sessionError = null;
    });

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => VerifyScreen(sessionId: sessionId),
      ),
    );
  }

  String? _extractSessionId(String input) {
    final trimmed = input.trim();
    if (trimmed.isEmpty) return null;

    if (trimmed.contains('session_id=')) {
      final uri = Uri.tryParse(trimmed);
      return uri?.queryParameters['session_id'];
    }

    if (trimmed.contains('/verify/')) {
      final uri = Uri.tryParse(trimmed);
      if (uri != null && uri.pathSegments.isNotEmpty) {
        return uri.pathSegments.last;
      }
    }

    final sessionRegex = RegExp(r'^[0-9a-fA-F-]{32,}$');
    if (sessionRegex.hasMatch(trimmed)) {
      return trimmed;
    }

    return null;
  }

  bool _canStartVerification() {
    return _moduleA || _moduleB || _moduleC;
  }

  int _getSelectedCount() {
    int count = 0;
    if (_moduleA) count++;
    if (_moduleB) count++;
    if (_moduleC) count++;
    return count;
  }

  String _getSelectedModulesText() {
    List<String> selected = [];
    if (_moduleA) selected.add('A');
    if (_moduleB) selected.add('B');
    if (_moduleC) selected.add('C');

    if (selected.isEmpty) return 'None selected';
    return 'Module ${selected.join(', ')}';
  }

  void _startVerification(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => StandaloneVerifyScreen(
          enableModuleA: _moduleA,
          enableModuleB: _moduleB,
          enableModuleC: _moduleC,
        ),
      ),
    );
  }
}
