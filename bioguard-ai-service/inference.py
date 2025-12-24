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
        default_model = os.getenv("MODEL_PATH", "").strip()
        self.model_path = model_path or default_model or os.path.join(
            os.path.dirname(__file__),
            "models",
            "MiniFASNetV1SE.onnx"
        )
        self.session = None
        self.input_name = None
        self.input_size = 80  # MiniFASNetV2 input size
        self.threshold = 0.90  # Confidence threshold for real face
        # Class mapping varies by training/export. Override via env var if needed.
        # We'll also auto-pick a sensible default once we know the output class count.
        self._real_class_index_env = os.getenv("REAL_CLASS_INDEX", "").strip()
        self.real_class_index = int(self._real_class_index_env) if self._real_class_index_env.isdigit() else None
        self.class_count = None

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
            # Determine class count from output shape, if available
            try:
                out_shape = self.session.get_outputs()[0].shape  # e.g. ['batch_size', 3]
                last_dim = out_shape[-1] if out_shape else None
                self.class_count = int(last_dim) if isinstance(last_dim, int) else None
            except Exception:
                self.class_count = None

            # If user didn't explicitly set REAL_CLASS_INDEX, choose a best-effort default:
            # - For 2-class outputs, many exports are [spoof, real] => real=1
            # - For 3-class outputs in this repo's model, "real" is commonly the last index (2)
            if self.real_class_index is None:
                if self.class_count == 2:
                    self.real_class_index = 1
                elif self.class_count == 3:
                    self.real_class_index = 2
                else:
                    self.real_class_index = 1

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

        # IMPORTANT: Many MiniFASNet reference implementations feed OpenCV images directly
        # (BGR channel order) into ToTensor(), which does NOT swap channels.
        # So we keep BGR here to match that pipeline.
        img_float = img_resized.astype(np.float32) / 255.0

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
            # NOTE: Some exports are binary ([spoof, real]) while others are multi-class
            # (e.g. 3-class). Always softmax across the last dim.
            exp_scores = np.exp(raw_output - np.max(raw_output))  # Numerical stability
            softmax_probs = exp_scores / np.sum(exp_scores)

            probs = [float(x) for x in softmax_probs.tolist()]
            predicted_class = int(np.argmax(softmax_probs))

            real_idx = int(self.real_class_index) if self.real_class_index is not None else 1
            if 0 <= real_idx < len(probs):
                real_score = float(probs[real_idx])
            else:
                # Fallback to "most confident" if misconfigured
                real_score = float(probs[predicted_class])

            is_real = real_score > self.threshold

            processing_time = (time.time() - start_time) * 1000

            return {
                "is_real": is_real,
                "confidence": real_score,
                "threshold": self.threshold,
                "class_count": int(len(probs)),
                "real_class_index": real_idx,
                "predicted_class": predicted_class,
                "probs": probs,
                "raw_scores": [float(x) for x in np.asarray(raw_output).tolist()],
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

    def detect_and_crop(self, image: np.ndarray, scale: float = 2.7, pad: bool = True) -> np.ndarray | None:
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

        # Calculate crop bounds (may go out of image)
        x1 = center_x - crop_size // 2
        y1 = center_y - crop_size // 2
        x2 = x1 + crop_size
        y2 = y1 + crop_size

        if not pad:
            x1c = max(0, x1)
            y1c = max(0, y1)
            x2c = min(image.shape[1], x2)
            y2c = min(image.shape[0], y2)
            return image[y1c:y2c, x1c:x2c]

        # Pad image so we can keep the requested crop size (important for 2.7x)
        h_img, w_img = image.shape[:2]
        pad_left = max(0, -x1)
        pad_top = max(0, -y1)
        pad_right = max(0, x2 - w_img)
        pad_bottom = max(0, y2 - h_img)

        if pad_left or pad_top or pad_right or pad_bottom:
            padded = cv2.copyMakeBorder(
                image,
                pad_top,
                pad_bottom,
                pad_left,
                pad_right,
                borderType=cv2.BORDER_REFLECT_101,
            )
        else:
            padded = image

        x1p = x1 + pad_left
        y1p = y1 + pad_top
        x2p = x2 + pad_left
        y2p = y2 + pad_top
        return padded[y1p:y2p, x1p:x2p]

    def detect_and_crop_with_info(self, image: np.ndarray, scale: float = 2.7, pad: bool = True) -> dict:
        """
        Same as detect_and_crop(), but returns debug info for troubleshooting.
        """
        h, w = image.shape[:2]

        info = {
            "input_h": int(h),
            "input_w": int(w),
            "scale": float(scale),
            "method": None,
            "face_detected": False,
            "bbox_xywh": None,
            "crop_xyxy": None,
            "crop_h": None,
            "crop_w": None,
        }

        info["pad"] = bool(pad)

        if self.face_cascade is None:
            cropped = self._center_crop(image, scale)
            ch, cw = cropped.shape[:2]
            info.update(
                method="center_crop_no_cascade",
                crop_h=int(ch),
                crop_w=int(cw),
            )
            return {"cropped": cropped, "info": info}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60)
        )

        if len(faces) == 0:
            cropped = self._center_crop(image, scale)
            ch, cw = cropped.shape[:2]
            info.update(
                method="center_crop_no_face",
                crop_h=int(ch),
                crop_w=int(cw),
            )
            return {"cropped": cropped, "info": info}

        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        info["face_detected"] = True
        info["bbox_xywh"] = [int(x), int(y), int(fw), int(fh)]

        center_x = x + fw // 2
        center_y = y + fh // 2
        crop_size = int(max(fw, fh) * scale)

        # Intended square crop bounds (may go out of image)
        x1 = center_x - crop_size // 2
        y1 = center_y - crop_size // 2
        x2 = x1 + crop_size
        y2 = y1 + crop_size

        # How much padding would be needed?
        pad_left = max(0, -x1)
        pad_top = max(0, -y1)
        pad_right = max(0, x2 - w)
        pad_bottom = max(0, y2 - h)
        info["pad_px"] = [int(pad_left), int(pad_top), int(pad_right), int(pad_bottom)]

        if not pad:
            x1c = max(0, x1)
            y1c = max(0, y1)
            x2c = min(w, x2)
            y2c = min(h, y2)
            info["crop_xyxy"] = [int(x1c), int(y1c), int(x2c), int(y2c)]
            cropped = image[y1c:y2c, x1c:x2c]
            ch, cw = cropped.shape[:2]
            info.update(method="haar_face_crop_clamped", crop_h=int(ch), crop_w=int(cw))
            return {"cropped": cropped, "info": info}

        # Pad and then crop exact crop_size
        if pad_left or pad_top or pad_right or pad_bottom:
            padded = cv2.copyMakeBorder(
                image,
                pad_top,
                pad_bottom,
                pad_left,
                pad_right,
                borderType=cv2.BORDER_REFLECT_101,
            )
        else:
            padded = image

        x1p = x1 + pad_left
        y1p = y1 + pad_top
        x2p = x2 + pad_left
        y2p = y2 + pad_top
        info["crop_xyxy"] = [int(x1p), int(y1p), int(x2p), int(y2p)]

        cropped = padded[y1p:y2p, x1p:x2p]
        ch, cw = cropped.shape[:2]
        info.update(method="haar_face_crop_padded", crop_h=int(ch), crop_w=int(cw))
        return {"cropped": cropped, "info": info}

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
