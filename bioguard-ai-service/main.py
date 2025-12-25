"""
BioGuard AI Service - Face Anti-Spoofing (PyTorch .pth)

- /demo: UI page (templates + static) for trying the model
- /api/predict: multipart upload endpoint used by /demo
- /v1/verify-liveness: JSON API for mobile clients (base64 image)
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import base64
import io
import os
from typing import Any

import cv2
import numpy as np
from PIL import Image

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name

app = FastAPI(
    title="BioGuard AI Engine",
    description="Face Anti-Spoofing API using MiniFASNetV1SE (.pth)",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)

# Static + templates for /demo
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Model config
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(BASE_DIR, "models", "4_0_0_80x80_MiniFASNetV1SE.pth"))
WORKING_MODELS = [os.path.basename(MODEL_PATH)]

# Initialize predictor + cropper once (fast)
predictor = AntiSpoofPredict(device_id=0)
predictor.load_model(MODEL_PATH)
image_cropper = CropImage()


class LivenessRequest(BaseModel):
    """Request model for liveness verification"""
    image_base64: str


class LivenessResponse(BaseModel):
    """Response model for liveness verification"""
    is_real: bool
    confidence: float
    threshold: float
    message: str
    details: dict = {}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "BioGuard AI Engine",
        "model": os.path.basename(MODEL_PATH),
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_path": MODEL_PATH
    }

def _validate_image(image_bytes: bytes) -> bool:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        return True
    except Exception:
        return False


def _preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Convert image bytes -> OpenCV BGR ndarray (keep original size).
    """
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    img_array = np.array(image)
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    return img_array


def _fallback_center_bbox(image_bgr: np.ndarray):
    h, w = image_bgr.shape[:2]
    size = min(w, h)
    cx, cy = w // 2, h // 2
    return [int(cx - size // 2), int(cy - size // 2), int(size), int(size)]


def _predict_face_authenticity(image_bgr: np.ndarray, bbox):
    """
    Implements the same loop style as the reference test.py:
    - parse model name
    - crop via CropImage
    - predict via AntiSpoofPredict
    """
    prediction = np.zeros((1, 3), dtype=np.float32)
    num_models = len(WORKING_MODELS)

    for model_name in WORKING_MODELS:
        h_input, w_input, _model_type, scale = parse_model_name(model_name)
        param: dict[str, Any] = {
            "org_img": image_bgr,
            "bbox": bbox,
            "scale": scale if scale is not None else 1.0,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        if scale is None:
            param["crop"] = False

        cropped_img = image_cropper.crop(**param)
        result = predictor.predict(cropped_img)  # (1,3)
        prediction += result.astype(np.float32)

    label = int(np.argmax(prediction))
    value = float(prediction[0][label] / num_models)

    # label: 0=fake, 1=real, 2=unknown
    is_real = bool(label == 1)
    prob_fake = float(prediction[0][0] / num_models)
    prob_real = float(prediction[0][1] / num_models)
    prob_unknown = float(prediction[0][2] / num_models)

    return {
        "is_real": is_real,
        "confidence": float(value),
        "probabilities": {"real": prob_real, "fake": prob_fake, "unknown": prob_unknown},
        "label": label,
    }


REAL_PROB_THRESHOLD = float(os.getenv("REAL_PROB_THRESHOLD", "0.8"))


def _apply_real_threshold(result: dict) -> dict:
    """
    Tighten decision rule: even if model predicts label==1 (real),
    require prob_real >= REAL_PROB_THRESHOLD to accept as real.
    """
    probs = result.get("probabilities") or {}
    prob_real = float(probs.get("real") or 0.0)
    label = int(result.get("label") if result.get("label") is not None else -1)
    is_real = bool(label == 1 and prob_real >= REAL_PROB_THRESHOLD)

    # Use prob_real as the user-facing confidence for the "real" claim
    result = dict(result)
    result["is_real"] = is_real
    result["confidence"] = prob_real
    result["threshold"] = REAL_PROB_THRESHOLD
    return result


@app.get("/demo", response_class=HTMLResponse)
async def demo(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/predict")
async def api_predict(file: UploadFile = File(...)):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    if not _validate_image(image_bytes):
        raise HTTPException(status_code=400, detail="Invalid image file")

    image_bgr = _preprocess_image(image_bytes)

    try:
        bbox = predictor.get_bbox(image_bgr)
    except Exception:
        bbox = _fallback_center_bbox(image_bgr)

    result = _apply_real_threshold(_predict_face_authenticity(image_bgr, bbox))

    # Base64 images for UI
    pil_image = Image.fromarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    img_str = base64.b64encode(buf.getvalue()).decode()

    # Draw bbox
    image_with_bbox = image_bgr.copy()
    x, y, w, h = bbox
    color = (0, 255, 0) if result["is_real"] else (0, 0, 255)
    cv2.rectangle(image_with_bbox, (x, y), (x + w, y + h), color, 3)
    bbox_pil = Image.fromarray(cv2.cvtColor(image_with_bbox, cv2.COLOR_BGR2RGB))
    buf2 = io.BytesIO()
    bbox_pil.save(buf2, format="JPEG")
    bbox_img_str = base64.b64encode(buf2.getvalue()).decode()

    return {"filename": file.filename, "result": result, "image_data": img_str, "bbox_image_data": bbox_img_str, "bbox": bbox}


@app.post("/v1/verify-liveness", response_model=LivenessResponse)
async def verify_liveness(request: LivenessRequest):
    """
    Mobile API: accepts base64 image, runs .pth anti-spoofing and returns a compact result.
    """
    try:
        image_bgr = decode_base64_image(request.image_base64)
        if image_bgr is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        try:
            bbox = predictor.get_bbox(image_bgr)
        except Exception:
            bbox = _fallback_center_bbox(image_bgr)

        r = _apply_real_threshold(_predict_face_authenticity(image_bgr, bbox))

        return LivenessResponse(
            is_real=bool(r["is_real"]),
            confidence=float(r["confidence"]),
            threshold=float(r["threshold"]),
            message="Real face detected" if r["is_real"] else "Spoof detected",
            details={
                "bbox": bbox,
                "probabilities": r.get("probabilities", {}),
                "label": r.get("label"),
                "model": os.path.basename(MODEL_PATH),
                "real_prob_threshold": float(r["threshold"]),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/v1/batch-verify")
async def batch_verify(images: list[LivenessRequest]):
    results = []
    for i, req in enumerate(images):
        try:
            image_bgr = decode_base64_image(req.image_base64)
            if image_bgr is None:
                results.append({"index": i, "error": "Invalid image"})
                continue
            try:
                bbox = predictor.get_bbox(image_bgr)
            except Exception:
                bbox = _fallback_center_bbox(image_bgr)
            r = _predict_face_authenticity(image_bgr, bbox)
            results.append({"index": i, "is_real": r["is_real"], "confidence": r["confidence"]})
        except Exception as e:
            results.append({"index": i, "error": str(e)})

    valid = [r for r in results if "is_real" in r]
    if valid:
        avg_conf = sum(r["confidence"] for r in valid) / len(valid)
        all_real = all(r["is_real"] for r in valid)
    else:
        avg_conf = 0.0
        all_real = False
    return {"aggregate": {"is_real": all_real, "avg_confidence": avg_conf, "frames_analyzed": len(valid)}, "individual_results": results}


def decode_base64_image(base64_string: str) -> np.ndarray | None:
    """
    Decode a base64 string to an OpenCV image.

    Args:
        base64_string: Base64 encoded image

    Returns:
        OpenCV image (numpy array) or None if decoding fails
    """
    try:
        # Remove data URL prefix if present
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]

        # Decode base64
        img_data = base64.b64decode(base64_string)

        # Convert to numpy array
        nparr = np.frombuffer(img_data, np.uint8)

        # Decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        return img
    except Exception as e:
        print(f"Image decode error: {e}")
        return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
