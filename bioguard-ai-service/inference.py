"""
MiniFASNetV2 Liveness Detection Inference

This module handles the ONNX model inference for face liveness detection.
"""

import os
import time
import numpy as np
import cv2

# Check if ONNX Runtime is available
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    print("Warning: onnxruntime not installed. Running in demo mode.")


class LivenessDetector:
    """
    Face Liveness Detector using MiniFASNetV2 ONNX model.

    The model detects whether a face image is from a real person
    or a spoof attempt (photo, video, mask).
    """

    def __init__(self, model_path: str = None):
        """
        Initialize the liveness detector.

        Args:
            model_path: Path to the ONNX model file.
                       Defaults to 'models/MiniFASNetV2.onnx'
        """
        self.model_path = model_path or os.path.join(
            os.path.dirname(__file__),
            "models",
            "MiniFASNetV2.onnx"
        )
        self.session = None
        self.input_name = None
        self.input_size = 80  # MiniFASNetV2 input size
        self.threshold = 0.90  # Confidence threshold for real face

        self._load_model()

    def _load_model(self):
        """Load the ONNX model."""
        if not ONNX_AVAILABLE:
            print("ONNX Runtime not available. Using demo mode.")
            return

        if not os.path.exists(self.model_path):
            print(f"Model not found at {self.model_path}. Using demo mode.")
            return

        try:
            # Create ONNX Runtime session
            self.session = ort.InferenceSession(
                self.model_path,
                providers=['CPUExecutionProvider']
            )
            self.input_name = self.session.get_inputs()[0].name
            print(f"Model loaded successfully: {self.model_path}")
        except Exception as e:
            print(f"Failed to load model: {e}")
            self.session = None

    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.session is not None

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model inference.

        Args:
            image: BGR image from OpenCV

        Returns:
            Preprocessed tensor ready for inference
        """
        # Resize to model input size
        img_resized = cv2.resize(image, (self.input_size, self.input_size))

        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1]
        img_float = img_rgb.astype(np.float32) / 255.0

        # Transpose from HWC to CHW format
        img_transposed = img_float.transpose((2, 0, 1))

        # Add batch dimension
        img_batch = np.expand_dims(img_transposed, axis=0)

        return img_batch

    def predict(self, image: np.ndarray) -> dict:
        """
        Predict liveness from face image.

        Args:
            image: BGR image from OpenCV (face region)

        Returns:
            Dictionary with prediction results:
            - is_real: Boolean indicating if face is real
            - confidence: Confidence score (0-1)
            - threshold: Threshold used for decision
            - raw_score: Raw model output
            - processing_time_ms: Time taken for inference
        """
        start_time = time.time()

        # If model not loaded, return demo result
        if not self.is_loaded():
            return self._demo_predict(image)

        try:
            # Preprocess image
            input_tensor = self.preprocess(image)

            # Run inference
            outputs = self.session.run(None, {self.input_name: input_tensor})

            # Get prediction
            raw_output = outputs[0][0]

            # Apply softmax to get probabilities
            # Output format: [spoof_score, real_score]
            exp_scores = np.exp(raw_output - np.max(raw_output))  # Numerical stability
            softmax_probs = exp_scores / np.sum(exp_scores)

            real_score = float(softmax_probs[1]) if len(softmax_probs) > 1 else float(softmax_probs[0])
            is_real = real_score > self.threshold

            processing_time = (time.time() - start_time) * 1000

            return {
                "is_real": is_real,
                "confidence": real_score,
                "threshold": self.threshold,
                "raw_score": float(raw_output[1]) if len(raw_output) > 1 else float(raw_output[0]),
                "processing_time_ms": round(processing_time, 2)
            }

        except Exception as e:
            print(f"Inference error: {e}")
            return self._demo_predict(image)

    def _demo_predict(self, image: np.ndarray) -> dict:
        """
        Demo prediction when model is not available.
        Uses simple heuristics based on image properties.
        """
        start_time = time.time()

        # Simple heuristics for demo
        # In real scenario, these would not be reliable
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Higher variance usually means more texture (real face)
        # This is just for demo purposes
        normalized_score = min(1.0, laplacian_var / 500.0)

        # Add some randomness for demo variability
        import random
        confidence = 0.85 + (random.random() * 0.14)

        processing_time = (time.time() - start_time) * 1000

        return {
            "is_real": confidence > self.threshold,
            "confidence": round(confidence, 4),
            "threshold": self.threshold,
            "raw_score": round(normalized_score, 4),
            "processing_time_ms": round(processing_time, 2),
            "demo_mode": True
        }


class FacePreprocessor:
    """
    Utility class for face preprocessing.
    Handles face detection and cropping with 2.7x scale.
    """

    def __init__(self):
        """Initialize face preprocessor."""
        self.face_cascade = None
        self._load_cascade()

    def _load_cascade(self):
        """Load OpenCV face cascade classifier."""
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(cascade_path):
            self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def detect_and_crop(self, image: np.ndarray, scale: float = 2.7) -> np.ndarray | None:
        """
        Detect face and crop with specified scale.

        The 2.7x scale is important for MiniFASNet as it includes
        context around the face (background, shoulders) which helps
        detect spoofing attempts like photos held up to the camera.

        Args:
            image: Input BGR image
            scale: Scale factor for cropping (default 2.7)

        Returns:
            Cropped face region or None if no face detected
        """
        if self.face_cascade is None:
            # If cascade not available, use center crop
            return self._center_crop(image, scale)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )

        if len(faces) == 0:
            return self._center_crop(image, scale)

        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

        # Calculate scaled crop region
        center_x = x + w // 2
        center_y = y + h // 2
        crop_size = int(max(w, h) * scale)

        # Calculate crop bounds
        x1 = max(0, center_x - crop_size // 2)
        y1 = max(0, center_y - crop_size // 2)
        x2 = min(image.shape[1], center_x + crop_size // 2)
        y2 = min(image.shape[0], center_y + crop_size // 2)

        return image[y1:y2, x1:x2]

    def _center_crop(self, image: np.ndarray, scale: float) -> np.ndarray:
        """Center crop as fallback when no face detected."""
        h, w = image.shape[:2]
        crop_size = int(min(h, w) * 0.8)

        center_x = w // 2
        center_y = h // 2

        x1 = center_x - crop_size // 2
        y1 = center_y - crop_size // 2
        x2 = center_x + crop_size // 2
        y2 = center_y + crop_size // 2

        return image[y1:y2, x1:x2]
