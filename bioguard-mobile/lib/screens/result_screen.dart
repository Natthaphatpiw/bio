import 'package:flutter/material.dart';
import '../services/local_storage_service.dart';
import '../theme/app_theme.dart';

/// Screen to display verification results
class ResultScreen extends StatelessWidget {
  final VerificationRecord record;

  const ResultScreen({super.key, required this.record});

  @override
  Widget build(BuildContext context) {
    final bool isPassed = record.overallStatus == 'PASSED';

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              const SizedBox(height: 20),

              // Result Icon
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  color: (isPassed
                          ? AppColors.success
                          : AppColors.danger)
                      .withOpacity(0.2),
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: isPassed
                        ? AppColors.success
                        : AppColors.danger,
                    width: 3,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: (isPassed
                              ? AppColors.success
                              : AppColors.danger)
                          .withOpacity(0.3),
                      blurRadius: 30,
                      spreadRadius: 5,
                    ),
                  ],
                ),
                child: Icon(
                  isPassed ? Icons.check_circle_rounded : Icons.cancel_rounded,
                  size: 64,
                  color: isPassed
                      ? AppColors.success
                      : AppColors.danger,
                ),
              ),

              const SizedBox(height: 24),

              // Result Title
              Text(
                isPassed ? 'Verification Passed' : 'Verification Failed',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: isPassed
                      ? AppColors.success
                      : AppColors.danger,
                ),
              ),

              const SizedBox(height: 8),

              // Timestamp
              Text(
                _formatDateTime(record.timestamp),
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.textMuted,
                ),
              ),

              const SizedBox(height: 32),

              // Summary Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.border,
                  ),
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildSummaryItem(
                          'Modules',
                          _getModulesCount(),
                          Icons.widgets_rounded,
                        ),
                        _buildSummaryItem(
                          'Passed',
                          _getPassedCount(),
                          Icons.check_circle_outline,
                        ),
                        _buildSummaryItem(
                          'Failed',
                          _getFailedCount(),
                          Icons.highlight_off,
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Module Results
              const Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Module Results',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Module A Result
              if (record.moduleAEnabled)
                _buildModuleResultCard(
                  module: 'A',
                  title: 'Environment Shield',
                  icon: Icons.security_rounded,
                  color: AppColors.success,
                  result: record.moduleAResult,
                  isPassed: record.moduleAResult?['isSafe'] == true,
                ),

              // Module B Result
              if (record.moduleBEnabled) ...[
                const SizedBox(height: 12),
                _buildModuleResultCard(
                  module: 'B',
                  title: 'Light-Sync Challenge',
                  icon: Icons.flash_on_rounded,
                  color: AppColors.softOrange,
                  result: record.moduleBResult,
                  isPassed: record.moduleBResult?['pass'] == true,
                ),
              ],

              // Module C Result
              if (record.moduleCEnabled) ...[
                const SizedBox(height: 12),
                _buildModuleResultCard(
                  module: 'C',
                  title: 'AI Face Liveness',
                  icon: Icons.face_rounded,
                  color: AppColors.deepBlue,
                  result: record.moduleCResult,
                  isPassed: record.moduleCResult?['isReal'] == true,
                ),
              ],

              const SizedBox(height: 32),

              // Record ID
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.border),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.fingerprint,
                      size: 16,
                      color: AppColors.textMuted,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Record ID: ${record.id}',
                      style: TextStyle(
                        fontSize: 12,
                        fontFamily: 'monospace',
                        color: AppColors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Done Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: () {
                    // Pop until home
                    Navigator.of(context).popUntil((route) => route.isFirst);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.deepBlue,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text(
                    'Done',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Verify Again Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: OutlinedButton(
                  onPressed: () {
                    Navigator.of(context).popUntil((route) => route.isFirst);
                  },
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.deepBlue,
                    side: const BorderSide(color: AppColors.border),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text(
                    'Verify Again',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSummaryItem(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(
          icon,
          color: AppColors.deepBlue,
          size: 24,
        ),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: AppColors.textMuted,
          ),
        ),
      ],
    );
  }

  Widget _buildModuleResultCard({
    required String module,
    required String title,
    required IconData icon,
    required Color color,
    required Map<String, dynamic>? result,
    required bool isPassed,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isPassed
              ? AppColors.success.withOpacity(0.3)
              : AppColors.danger.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: color, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Module $module',
                      style: TextStyle(
                        fontSize: 12,
                        color: AppColors.textMuted,
                      ),
                    ),
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
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
                  color: (isPassed
                          ? AppColors.success
                          : AppColors.danger)
                      .withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isPassed ? Icons.check_circle : Icons.cancel,
                      size: 16,
                      color: isPassed
                          ? AppColors.success
                          : AppColors.danger,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      isPassed ? 'Passed' : 'Failed',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: isPassed
                            ? AppColors.success
                            : AppColors.danger,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // Details
          if (result != null) ...[
            const SizedBox(height: 12),
            const Divider(color: AppColors.border),
            const SizedBox(height: 12),
            _buildDetails(module, result),
          ],
        ],
      ),
    );
  }

  Widget _buildDetails(String module, Map<String, dynamic> result) {
    if (module == 'A') {
      return Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          _buildDetailChip('Root', result['root'] != true),
          _buildDetailChip('Emulator', result['emulator'] != true),
          _buildDetailChip('USB Debug', result['usbDebug'] != true),
          _buildDetailChip('Hooking', result['hooking'] != true),
          _buildDetailChip('Dev Mode', result['devMode'] != true),
        ],
      );
    } else if (module == 'B') {
      return Row(
        children: [
          Expanded(
            child: _buildMetric(
              'Confidence',
              result['confidence'] != null
                  ? '${(result['confidence'] * 100).toStringAsFixed(1)}%'
                  : 'N/A',
              result['pass'] == true,
            ),
          ),
        ],
      );
    } else if (module == 'C') {
      return Row(
        children: [
          Expanded(
            child: _buildMetric(
              'Confidence',
              result['confidence'] != null
                  ? '${(result['confidence'] * 100).toStringAsFixed(1)}%'
                  : 'N/A',
              result['isReal'] == true,
            ),
          ),
        ],
      );
    }
    return const SizedBox.shrink();
  }

  Widget _buildDetailChip(String label, bool passed) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: (passed ? AppColors.success : AppColors.danger)
            .withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: (passed ? AppColors.success : AppColors.danger)
              .withOpacity(0.3),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            passed ? Icons.check : Icons.close,
            size: 14,
            color: passed ? AppColors.success : AppColors.danger,
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: passed ? AppColors.success : AppColors.danger,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetric(String label, String value, bool passed) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: AppColors.textMuted,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: passed ? AppColors.success : AppColors.danger,
            ),
          ),
        ],
      ),
    );
  }

  String _formatDateTime(DateTime dt) {
    return '${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  String _getModulesCount() {
    int count = 0;
    if (record.moduleAEnabled) count++;
    if (record.moduleBEnabled) count++;
    if (record.moduleCEnabled) count++;
    return count.toString();
  }

  String _getPassedCount() {
    int count = 0;
    if (record.moduleAEnabled && record.moduleAResult?['isSafe'] == true) count++;
    if (record.moduleBEnabled && record.moduleBResult?['pass'] == true) count++;
    if (record.moduleCEnabled && record.moduleCResult?['isReal'] == true) count++;
    return count.toString();
  }

  String _getFailedCount() {
    int total = int.parse(_getModulesCount());
    int passed = int.parse(_getPassedCount());
    return (total - passed).toString();
  }
}
