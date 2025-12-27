import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'dart:async';
import 'dart:typed_data';
import 'dart:math' as math;
import 'package:image/image.dart' as img;
import 'light_sync_native_camera.dart';
import '../../theme/app_theme.dart';

/// Module B: Light-Sync Challenge
/// Physics-based verification using screen flash and camera capture
/// Improved with adaptive thresholds and normalized ratio descriptors
class LightSyncVerifier extends StatefulWidget {
  const LightSyncVerifier({super.key});

  @override
  State<LightSyncVerifier> createState() => _LightSyncVerifierState();
}

class _LightSyncVerifierState extends State<LightSyncVerifier> {
  static const Duration _flashDelay = Duration(milliseconds: 350);
  static const Duration _interFrameDelay = Duration(milliseconds: 100);
  static const Duration _betweenRoundsDelay = Duration(milliseconds: 150);
  static const int _challengeRounds = 3;
  static const int _framesPerPhase = 2;

  // Relaxed base thresholds - will be adapted based on ambient conditions
  static const double _baseMinChannelDelta = 1.8;
  static const double _baseMinLumaDelta = 0.8;
  static const double _baseDominanceThreshold = 1.05;
  static const double _baseDominanceMargin = 0.3;
  static const double _minBackgroundDelta = 0.5;
  static const double _minAmbientLuma = 10.0;
  static const double _maxAmbientLuma = 220.0;
  static const double _maxSaturationRatio = 0.25;

  // Normalized ratio thresholds (SpecDiff-style)
  static const double _minNormalizedRatio = 0.08;
  static const double _minSpatialDifferential = 0.15;

  CameraController? _controller;
  final LightSyncNativeCamera _nativeCamera = LightSyncNativeCamera();
  bool _useNativePreview = false;
  int? _nativeTextureId;
  Size? _nativePreviewSize;
  bool _isInitialized = false;
  bool _isProcessing = false;
  Color _overlayColor = Colors.transparent;
  String _status = 'Initializing camera...';
  double _progress = 0.0;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final nativeOpen = await _nativeCamera.open(useFront: true);
      if (nativeOpen != null && nativeOpen['success'] == true) {
        final textureId = nativeOpen['textureId'];
        final width = nativeOpen['width'];
        final height = nativeOpen['height'];
        if (textureId is int || textureId is num) {
          _nativeTextureId = (textureId as num).toInt();
        }
        if (width is int && height is int && width > 0 && height > 0) {
          _nativePreviewSize = Size(width.toDouble(), height.toDouble());
        }
        if (_nativeTextureId != null) {
          setState(() {
            _useNativePreview = true;
            _isInitialized = true;
            _status = 'Camera ready. Tap to start challenge.';
          });
          return;
        }
        await _nativeCamera.close();
      }

      final cameras = await availableCameras();
      final frontCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _controller = CameraController(
        frontCamera,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await _controller!.initialize();

      if (mounted) {
        setState(() {
          _isInitialized = true;
          _status = 'Camera ready. Tap to start challenge.';
        });
      }
    } catch (e) {
      setState(() {
        _status = 'Camera initialization failed: $e';
      });
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    _nativeCamera.close();
    super.dispose();
  }

  Future<void> _startChallenge() async {
    if (_isProcessing || !_isInitialized) return;

    setState(() {
      _isProcessing = true;
      _status = 'Locking camera exposure...';
      _progress = 0.1;
    });

    final useNativeCamera = _useNativePreview;

    try {
      if (!useNativeCamera) {
        await _lockCameraSettings();
      }

      // Wait for exposure to stabilize
      await Future.delayed(const Duration(milliseconds: 400));

      final darkFrames = <Uint8List?>[];
      final redFrames = <Uint8List?>[];
      final blueFrames = <Uint8List?>[];

      final totalSteps = _challengeRounds * 3;
      var step = 0;

      for (var round = 1; round <= _challengeRounds; round++) {
        setState(() {
          _status = 'Round $round/$_challengeRounds: Capturing dark frame...';
          _progress = (++step) / totalSteps;
        });
        setState(() => _overlayColor = Colors.black);
        await Future.delayed(_flashDelay);
        darkFrames.add(await _captureStableFrame(useNativeCamera));

        setState(() {
          _status = 'Round $round/$_challengeRounds: Capturing red flash...';
          _progress = (++step) / totalSteps;
        });
        setState(() => _overlayColor = Colors.red);
        await Future.delayed(_flashDelay);
        redFrames.add(await _captureStableFrame(useNativeCamera));

        setState(() {
          _status = 'Round $round/$_challengeRounds: Capturing blue flash...';
          _progress = (++step) / totalSteps;
        });
        setState(() => _overlayColor = Colors.blue);
        await Future.delayed(_flashDelay);
        blueFrames.add(await _captureStableFrame(useNativeCamera));

        if (round < _challengeRounds) {
          setState(() => _overlayColor = Colors.transparent);
          await Future.delayed(_betweenRoundsDelay);
        }
      }

      setState(() {
        _overlayColor = Colors.transparent;
        _status = 'Analyzing reflection patterns...';
        _progress = 0.92;
      });

      // Analyze the captured frames
      final result = await _analyzeFrames(darkFrames, redFrames, blueFrames);

      setState(() {
        _progress = 1.0;
        _status = result['pass'] == true
            ? 'Challenge passed!'
            : (result['error'] ?? 'Challenge failed');
      });

      await Future.delayed(const Duration(milliseconds: 500));

      if (mounted) {
        Navigator.pop(context, result);
      }
    } catch (e) {
      setState(() {
        _status = 'Challenge error: $e';
        _isProcessing = false;
        _overlayColor = Colors.transparent;
      });
    }
  }

  Future<void> _lockCameraSettings() async {
    if (_controller == null) return;

    try {
      // Keep screen flash off and settle exposure before locking.
      await _controller!.setFlashMode(FlashMode.off);
    } catch (e) {
      debugPrint('Flash mode warning: $e');
    }

    try {
      await _controller!.setFocusMode(FocusMode.auto);
    } catch (e) {
      debugPrint('Focus mode warning: $e');
    }

    try {
      await _controller!.setExposureMode(ExposureMode.auto);
    } catch (e) {
      debugPrint('Exposure mode warning: $e');
    }

    try {
      await _controller!.setExposureOffset(0.0);
    } catch (e) {
      debugPrint('Exposure offset warning: $e');
    }

    await Future.delayed(const Duration(milliseconds: 600));

    try {
      await _controller!.setExposureMode(ExposureMode.locked);
    } catch (e) {
      debugPrint('Exposure lock warning: $e');
    }

    try {
      await _controller!.setFocusMode(FocusMode.locked);
    } catch (e) {
      // Some devices may not support all lock modes.
      debugPrint('Focus lock warning: $e');
    }
  }

  Future<Uint8List?> _captureFrame() async {
    if (_controller == null || !_controller!.value.isInitialized) {
      return null;
    }

    try {
      final XFile file = await _controller!.takePicture();
      return await file.readAsBytes();
    } catch (e) {
      debugPrint('Capture error: $e');
      return null;
    }
  }

  Future<Uint8List?> _captureStableFrame(bool useNativeCamera) async {
    Uint8List? latest;
    for (var i = 0; i < _framesPerPhase; i++) {
      latest = useNativeCamera
          ? await _nativeCamera.captureFrame()
          : await _captureFrame();
      if (latest == null) {
        return null;
      }
      if (i < _framesPerPhase - 1) {
        await Future.delayed(_interFrameDelay);
      }
    }
    return latest;
  }

  Future<Map<String, dynamic>> _analyzeFrames(
    List<Uint8List?> darkFrames,
    List<Uint8List?> redFrames,
    List<Uint8List?> blueFrames,
  ) async {
    final totalRounds = [
      darkFrames.length,
      redFrames.length,
      blueFrames.length,
    ].reduce((value, element) => value < element ? value : element);

    if (totalRounds == 0) {
      return {'pass': false, 'error': 'Failed to capture frames'};
    }

    try {
      final redDiffs = <Map<String, double>>[];
      final blueDiffs = <Map<String, double>>[];
      final redBgDiffs = <Map<String, double>>[];
      final blueBgDiffs = <Map<String, double>>[];
      final ambientLumas = <double>[];
      final saturationRatios = <double>[];
      final normalizedRedRatios = <double>[];
      final normalizedBlueRatios = <double>[];
      final spatialDifferentials = <double>[];

      for (var i = 0; i < totalRounds; i++) {
        final darkBytes = darkFrames[i];
        final redBytes = redFrames[i];
        final blueBytes = blueFrames[i];

        if (darkBytes == null || redBytes == null || blueBytes == null) {
          continue;
        }

        final darkImg = img.decodeImage(darkBytes);
        final redImg = img.decodeImage(redBytes);
        final blueImg = img.decodeImage(blueBytes);

        if (darkImg == null || redImg == null || blueImg == null) {
          continue;
        }

        final redCenter = _calculateColorDifference(darkImg, redImg);
        final blueCenter = _calculateColorDifference(darkImg, blueImg);
        final redBackground = _calculateBackgroundDifference(darkImg, redImg);
        final blueBackground = _calculateBackgroundDifference(darkImg, blueImg);

        ambientLumas.add(redCenter['baseLuma'] ?? 0);
        saturationRatios.add(
          _maxValue(
            redCenter['saturationRatio'] ?? 0,
            blueCenter['saturationRatio'] ?? 0,
          ),
        );

        // Calculate normalized ratio (SpecDiff-style)
        final redNormalized = _calculateNormalizedRatio(
          redCenter['redChannel']!,
          redCenter['greenChannel']!,
          redCenter['blueChannel']!,
        );
        final blueNormalized = _calculateNormalizedRatio(
          blueCenter['blueChannel']!,
          blueCenter['greenChannel']!,
          blueCenter['redChannel']!,
        );
        normalizedRedRatios.add(redNormalized);
        normalizedBlueRatios.add(blueNormalized);

        // Calculate spatial differential (face vs background)
        final redSpatial = _calculateSpatialDifferential(
          redCenter['lumaDelta']!,
          redBackground['lumaDelta']!,
        );
        final blueSpatial = _calculateSpatialDifferential(
          blueCenter['lumaDelta']!,
          blueBackground['lumaDelta']!,
        );
        spatialDifferentials.add((redSpatial + blueSpatial) / 2);

        redDiffs.add(redCenter);
        blueDiffs.add(blueCenter);
        redBgDiffs.add(redBackground);
        blueBgDiffs.add(blueBackground);
      }

      if (redDiffs.isEmpty || blueDiffs.isEmpty) {
        return {'pass': false, 'error': 'Failed to decode images'};
      }

      final validRounds = redDiffs.length;
      final ambientMedian = _median(ambientLumas);

      // Check ambient light conditions
      if (ambientMedian > _maxAmbientLuma) {
        return {
          'pass': false,
          'error': 'Ambient light too strong. Please move to a shaded area.',
        };
      }
      if (ambientMedian < _minAmbientLuma) {
        return {
          'pass': false,
          'error': 'Too dark. Please increase ambient light.',
        };
      }

      final saturationPeak = saturationRatios.isEmpty
          ? 0.0
          : saturationRatios.reduce(_maxValue);
      if (saturationPeak > _maxSaturationRatio) {
        return {
          'pass': false,
          'error': 'Overexposed capture. Move the phone slightly farther away.',
        };
      }

      // Calculate adaptive thresholds based on ambient conditions
      final adaptiveThresholds = _calculateAdaptiveThresholds(ambientMedian);
      final minChannelDelta = adaptiveThresholds['channelDelta']!;
      final minLumaDelta = adaptiveThresholds['lumaDelta']!;
      final dominanceThreshold = adaptiveThresholds['dominance']!;
      final dominanceMargin = adaptiveThresholds['margin']!;

      // Re-evaluate each round with adaptive thresholds
      var roundsPassed = 0;
      for (var i = 0; i < validRounds; i++) {
        final redCenter = redDiffs[i];
        final blueCenter = blueDiffs[i];
        final redBackground = redBgDiffs[i];
        final blueBackground = blueBgDiffs[i];

        final redDominance = _dominanceRatio(
          expected: redCenter['redChannel']!,
          otherA: redCenter['greenChannel']!,
          otherB: redCenter['blueChannel']!,
        );
        final blueDominance = _dominanceRatio(
          expected: blueCenter['blueChannel']!,
          otherA: blueCenter['greenChannel']!,
          otherB: blueCenter['redChannel']!,
        );
        final redMargin = redCenter['redChannel']! -
            _maxValue(redCenter['greenChannel']!, redCenter['blueChannel']!);
        final blueMargin = blueCenter['blueChannel']! -
            _maxValue(blueCenter['greenChannel']!, blueCenter['redChannel']!);

        // Multi-criteria evaluation with OR logic for flexibility
        final redChannelOk = redCenter['redChannel']! > minChannelDelta;
        final redLumaOk = redCenter['lumaDelta']! > minLumaDelta;
        final redSpatialOk = redCenter['lumaDelta']! >
            (redBackground['lumaDelta']! + _minBackgroundDelta);
        final redDominanceOk = redDominance > dominanceThreshold ||
            redMargin > dominanceMargin;
        final redNormalizedOk = normalizedRedRatios[i] > _minNormalizedRatio;

        final blueChannelOk = blueCenter['blueChannel']! > minChannelDelta;
        final blueLumaOk = blueCenter['lumaDelta']! > minLumaDelta;
        final blueSpatialOk = blueCenter['lumaDelta']! >
            (blueBackground['lumaDelta']! + _minBackgroundDelta);
        final blueDominanceOk = blueDominance > dominanceThreshold ||
            blueMargin > dominanceMargin;
        final blueNormalizedOk = normalizedBlueRatios[i] > _minNormalizedRatio;

        // Flexible pass criteria: need to pass majority of checks
        final redChecks = [redChannelOk, redLumaOk, redSpatialOk, redDominanceOk, redNormalizedOk];
        final blueChecks = [blueChannelOk, blueLumaOk, blueSpatialOk, blueDominanceOk, blueNormalizedOk];

        final redPassCount = redChecks.where((c) => c).length;
        final bluePassCount = blueChecks.where((c) => c).length;

        // Pass if at least 3 out of 5 criteria are met for each color
        if (redPassCount >= 3 && bluePassCount >= 3) {
          roundsPassed++;
        }
      }

      final redDiff = _aggregateDiff(redDiffs);
      final blueDiff = _aggregateDiff(blueDiffs);

      final redDominance = _dominanceRatio(
        expected: redDiff['redChannel']!,
        otherA: redDiff['greenChannel']!,
        otherB: redDiff['blueChannel']!,
      );
      final blueDominance = _dominanceRatio(
        expected: blueDiff['blueChannel']!,
        otherA: blueDiff['greenChannel']!,
        otherB: blueDiff['redChannel']!,
      );

      final avgNormalizedRed = _median(normalizedRedRatios);
      final avgNormalizedBlue = _median(normalizedBlueRatios);
      final avgSpatialDiff = _median(spatialDifferentials);

      // Relaxed pass requirement: need to pass at least half the rounds
      final requiredPasses = _requiredPassCount(validRounds);
      var passed = roundsPassed >= requiredPasses;

      // Additional fallback: if normalized ratios and spatial differential are good,
      // allow pass even with fewer round passes
      if (!passed && roundsPassed >= 1) {
        final normalizedOk = avgNormalizedRed > _minNormalizedRatio &&
            avgNormalizedBlue > _minNormalizedRatio;
        final spatialOk = avgSpatialDiff > _minSpatialDifferential;
        final dominanceOk = redDominance > 1.02 && blueDominance > 1.02;

        if (normalizedOk && spatialOk && dominanceOk) {
          passed = true;
        }
      }

      var confidence = _calculateConfidence(
        redDiff: redDiff,
        blueDiff: blueDiff,
        redDominance: redDominance,
        blueDominance: blueDominance,
      );

      // Boost confidence with normalized ratios
      final normalizedBoost = ((avgNormalizedRed + avgNormalizedBlue) / 2 * 0.3)
          .clamp(0.0, 0.15);
      confidence = (confidence + normalizedBoost).clamp(0.0, 0.99);
      confidence *= (roundsPassed / validRounds).clamp(0.5, 1.0).toDouble();

      return {
        'pass': passed,
        'confidence': confidence,
        'redDiff': redDiff,
        'blueDiff': blueDiff,
        'analysis': {
          'roundsTotal': validRounds,
          'roundsPassed': roundsPassed,
          'ambientLuma': ambientMedian,
          'saturationPeak': saturationPeak,
          'redDominance': redDominance,
          'blueDominance': blueDominance,
          'normalizedRedRatio': avgNormalizedRed,
          'normalizedBlueRatio': avgNormalizedBlue,
          'spatialDifferential': avgSpatialDiff,
          'adaptiveThresholds': adaptiveThresholds,
        }
      };
    } catch (e) {
      return {'pass': false, 'error': 'Analysis failed: $e'};
    }
  }

  /// Calculate adaptive thresholds based on ambient light conditions
  Map<String, double> _calculateAdaptiveThresholds(double ambientLuma) {
    // Scale thresholds based on ambient light
    // Lower ambient = lower thresholds (harder to get strong reflection)
    // Higher ambient = slightly higher thresholds (more noise)
    final ambientFactor = (ambientLuma / 100.0).clamp(0.3, 1.5);

    // Inverse relationship for channel delta - lower ambient needs lower threshold
    final channelMultiplier = 1.0 / math.sqrt(ambientFactor.clamp(0.5, 1.2));

    return {
      'channelDelta': _baseMinChannelDelta * channelMultiplier,
      'lumaDelta': _baseMinLumaDelta * channelMultiplier,
      'dominance': _baseDominanceThreshold,
      'margin': _baseDominanceMargin * channelMultiplier,
    };
  }

  /// Calculate normalized ratio (SpecDiff-style physics-based descriptor)
  double _calculateNormalizedRatio(
    double expected,
    double other1,
    double other2,
  ) {
    final total = expected + other1 + other2 + 0.001; // Avoid division by zero
    final expectedRatio = expected / total;
    final otherRatio = (other1 + other2) / (2 * total);
    return (expectedRatio - otherRatio).clamp(-1.0, 1.0);
  }

  /// Calculate spatial differential between face and background response
  double _calculateSpatialDifferential(
    double faceResponse,
    double backgroundResponse,
  ) {
    final total = faceResponse + backgroundResponse + 0.001;
    return ((faceResponse - backgroundResponse) / total).clamp(-1.0, 1.0);
  }

  Map<String, double> _calculateColorDifference(
    img.Image baseFrame,
    img.Image flashFrame,
  ) {
    // Center ROI (face area) - 20% of width.
    final roiSize = (baseFrame.width * 0.2).toInt();
    final left = (baseFrame.width ~/ 2) - roiSize ~/ 2;
    final top = (baseFrame.height ~/ 2) - roiSize ~/ 2;
    return _calculateColorDifferenceInBox(
      baseFrame,
      flashFrame,
      left,
      top,
      roiSize,
      roiSize,
    );
  }

  Map<String, double> _calculateBackgroundDifference(
    img.Image baseFrame,
    img.Image flashFrame,
  ) {
    final roiSize = (baseFrame.width * 0.18).toInt();
    final lefts = [0, baseFrame.width - roiSize];
    final tops = [0, baseFrame.height - roiSize];
    final diffs = <Map<String, double>>[];

    for (final left in lefts) {
      for (final top in tops) {
        diffs.add(
          _calculateColorDifferenceInBox(
            baseFrame,
            flashFrame,
            left,
            top,
            roiSize,
            roiSize,
          ),
        );
      }
    }

    return _aggregateDiff(diffs);
  }

  Map<String, double> _calculateColorDifferenceInBox(
    img.Image baseFrame,
    img.Image flashFrame,
    int left,
    int top,
    int width,
    int height,
  ) {
    final clampedLeft = left.clamp(0, baseFrame.width - 1).toInt();
    final clampedTop = top.clamp(0, baseFrame.height - 1).toInt();
    final clampedWidth = _maxInt(1, width);
    final clampedHeight = _maxInt(1, height);

    double sumR = 0, sumG = 0, sumB = 0;
    double baseLuma = 0, flashLuma = 0;
    int saturated = 0;
    int count = 0;

    for (int y = clampedTop; y < clampedTop + clampedHeight; y++) {
      for (int x = clampedLeft; x < clampedLeft + clampedWidth; x++) {
        if (x >= 0 && x < baseFrame.width && y >= 0 && y < baseFrame.height) {
          final basePixel = baseFrame.getPixel(x, y);
          final flashPixel = flashFrame.getPixel(x, y);

          sumR += (flashPixel.r - basePixel.r).abs();
          sumG += (flashPixel.g - basePixel.g).abs();
          sumB += (flashPixel.b - basePixel.b).abs();
          baseLuma += _luma(basePixel.r, basePixel.g, basePixel.b);
          flashLuma += _luma(flashPixel.r, flashPixel.g, flashPixel.b);

          if (flashPixel.r > 250 || flashPixel.g > 250 || flashPixel.b > 250) {
            saturated++;
          }
          count++;
        }
      }
    }

    if (count == 0) count = 1;

    return {
      'redChannel': sumR / count,
      'greenChannel': sumG / count,
      'blueChannel': sumB / count,
      'lumaDelta': (flashLuma / count - baseLuma / count).abs(),
      'baseLuma': baseLuma / count,
      'flashLuma': flashLuma / count,
      'saturationRatio': saturated / count,
    };
  }

  double _luma(num r, num g, num b) {
    return (0.299 * r) + (0.587 * g) + (0.114 * b);
  }

  double _dominanceRatio({
    required double expected,
    required double otherA,
    required double otherB,
  }) {
    final otherAvg = (otherA + otherB) / 2;
    return expected / (otherAvg + 1);
  }

  double _calculateConfidence({
    required Map<String, double> redDiff,
    required Map<String, double> blueDiff,
    required double redDominance,
    required double blueDominance,
  }) {
    final redScore = _scoreForChannel(
      expected: redDiff['redChannel']!,
      lumaDelta: redDiff['lumaDelta']!,
      dominance: redDominance,
    );
    final blueScore = _scoreForChannel(
      expected: blueDiff['blueChannel']!,
      lumaDelta: blueDiff['lumaDelta']!,
      dominance: blueDominance,
    );
    final confidence = (redScore + blueScore) / 2;
    return confidence.clamp(0.0, 0.99).toDouble();
  }

  double _scoreForChannel({
    required double expected,
    required double lumaDelta,
    required double dominance,
  }) {
    final dominanceScore =
        ((dominance - 1.0) / 1.3).clamp(0.0, 1.0).toDouble();
    final signalScore = (expected / 12.0).clamp(0.0, 1.0).toDouble();
    final lumaScore = (lumaDelta / 10.0).clamp(0.0, 1.0).toDouble();
    return (dominanceScore * 0.5) + (signalScore * 0.3) + (lumaScore * 0.2);
  }

  Map<String, double> _aggregateDiff(List<Map<String, double>> diffs) {
    if (diffs.isEmpty) {
      return {
        'redChannel': 0,
        'greenChannel': 0,
        'blueChannel': 0,
        'lumaDelta': 0,
        'baseLuma': 0,
        'flashLuma': 0,
        'saturationRatio': 0,
      };
    }

    double aggregate(List<double> values) => _median(values);

    return {
      'redChannel': aggregate(diffs.map((d) => d['redChannel'] ?? 0).toList()),
      'greenChannel':
          aggregate(diffs.map((d) => d['greenChannel'] ?? 0).toList()),
      'blueChannel': aggregate(diffs.map((d) => d['blueChannel'] ?? 0).toList()),
      'lumaDelta': aggregate(diffs.map((d) => d['lumaDelta'] ?? 0).toList()),
      'baseLuma': aggregate(diffs.map((d) => d['baseLuma'] ?? 0).toList()),
      'flashLuma': aggregate(diffs.map((d) => d['flashLuma'] ?? 0).toList()),
      'saturationRatio':
          aggregate(diffs.map((d) => d['saturationRatio'] ?? 0).toList()),
    };
  }

  double _median(List<double> values) {
    if (values.isEmpty) return 0;
    final sorted = [...values]..sort();
    final mid = sorted.length ~/ 2;
    if (sorted.length.isOdd) {
      return sorted[mid];
    }
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }

  int _requiredPassCount(int rounds) {
    // More lenient: require only 50% of rounds to pass (was 67%)
    if (rounds <= 1) return 1;
    if (rounds == 2) return 1;
    return (rounds * 0.5).ceil();
  }

  double _maxValue(double a, double b) {
    return a > b ? a : b;
  }

  int _maxInt(int a, int b) {
    return a > b ? a : b;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.navy,
      body: Stack(
        children: [
          // Camera Preview
          if (_isInitialized)
            Positioned.fill(
              child: _useNativePreview && _nativeTextureId != null
                  ? _buildNativePreview()
                  : _controller != null
                      ? AspectRatio(
                          aspectRatio: _controller!.value.aspectRatio,
                          child: CameraPreview(_controller!),
                        )
                      : const SizedBox.shrink(),
            ),

          // Color Overlay for flash
          Positioned.fill(
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 50),
              color: _overlayColor,
            ),
          ),

          // Face Oval Guide
          if (!_isProcessing)
            Center(
              child: Container(
                width: 250,
                height: 320,
                decoration: BoxDecoration(
                  border: Border.all(
                    color: Colors.white.withOpacity(0.6),
                    width: 3,
                  ),
                  borderRadius: BorderRadius.circular(150),
                ),
              ),
            ),

          // UI Overlay
          SafeArea(
            child: Column(
              children: [
                // Header
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      IconButton(
                        onPressed: () => Navigator.pop(context, {'pass': false}),
                        icon: const Icon(Icons.close, color: Colors.white),
                      ),
                      const Expanded(
                        child: Text(
                          'Light-Sync Challenge',
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
                ),

                const Spacer(),

                // Status and Progress
                Container(
                  margin: const EdgeInsets.all(24),
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: AppColors.navy.withOpacity(0.78),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Column(
                    children: [
                      if (_isProcessing) ...[
                        LinearProgressIndicator(
                          value: _progress,
                          backgroundColor: Colors.white24,
                          valueColor: const AlwaysStoppedAnimation<Color>(
                            AppColors.softOrange,
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],
                      Text(
                        _status,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 16,
                          color: Colors.white,
                        ),
                      ),
                      if (!_isProcessing && _isInitialized) ...[
                        const SizedBox(height: 16),
                        SizedBox(
                          width: double.infinity,
                          height: 50,
                          child: ElevatedButton(
                            onPressed: _startChallenge,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.softOrange,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                            child: const Text(
                              'Start Challenge',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNativePreview() {
    final size = _nativePreviewSize;
    if (size == null || _nativeTextureId == null) {
      return const SizedBox.shrink();
    }
    return FittedBox(
      fit: BoxFit.cover,
      child: SizedBox(
        width: size.width,
        height: size.height,
        child: Texture(textureId: _nativeTextureId!),
      ),
    );
  }
}
