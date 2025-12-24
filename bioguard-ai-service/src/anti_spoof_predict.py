# -*- coding: utf-8 -*-
"""
Anti-spoof predictor using PyTorch .pth weights.
This follows the structure of the reference code, but uses Haar cascade for bbox
to avoid external caffe model dependencies.
"""

from __future__ import annotations

import os
import cv2
import torch
import numpy as np
import torch.nn.functional as F

from src.model_lib.MiniFASNet import MiniFASNetV1SE
from src.data_io import transform as trans
from src.utility import get_kernel, parse_model_name


class Detection:
    def __init__(self):
        # Use OpenCV haarcascade (bundled with opencv) so the service is self-contained.
        self.detector_confidence = 0.0
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path) if os.path.exists(cascade_path) else None

    def get_bbox(self, img: np.ndarray):
        """
        Returns bbox in [x, y, w, h] (like reference code).
        """
        if self.face_cascade is None:
            raise RuntimeError("Haar cascade not available")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            raise RuntimeError("No face detected")
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return [int(x), int(y), int(w), int(h)]


class AntiSpoofPredict(Detection):
    def __init__(self, device_id: int = 0):
        super().__init__()
        self.device = torch.device(f"cuda:{device_id}" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.kernel_size = None

    def load_model(self, model_path: str):
        model_name = os.path.basename(model_path)
        h_input, w_input, model_type, _ = parse_model_name(model_name)
        self.kernel_size = get_kernel(h_input, w_input)

        if model_type != "MiniFASNetV1SE":
            raise ValueError(f"Only MiniFASNetV1SE is supported by this service, got: {model_type}")

        self.model = MiniFASNetV1SE(conv6_kernel=self.kernel_size).to(self.device)

        state_dict = torch.load(model_path, map_location=self.device)
        first_key = next(iter(state_dict))
        if "module." in first_key:
            from collections import OrderedDict

            new_state_dict = OrderedDict()
            for key, value in state_dict.items():
                new_state_dict[key[7:]] = value
            self.model.load_state_dict(new_state_dict)
        else:
            self.model.load_state_dict(state_dict)

        self.model.eval()
        return None

    def predict(self, img_bgr_80: np.ndarray):
        """
        img_bgr_80: numpy array (H,W,C) in BGR order (OpenCV).
        Returns softmax probabilities shape (1,3)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model(model_path) first.")

        test_transform = trans.Compose([trans.ToTensor()])
        img_tensor = test_transform(img_bgr_80)  # float tensor CHW (0..255)
        img_tensor = img_tensor.unsqueeze(0).to(self.device)

        with torch.no_grad():
            out = self.model.forward(img_tensor)
            probs = F.softmax(out, dim=1).cpu().numpy()
        return probs


