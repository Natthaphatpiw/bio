"""
BioGuard AI Service - MiniFASNetV2 Liveness Detection

This service provides an API endpoint for face liveness detection
using the MiniFASNetV2 ONNX model.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import base64
import cv2
from inference import LivenessDetector

app = FastAPI(
    title="BioGuard AI Engine",
    description="Face Liveness Detection API using MiniFASNetV2",
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

# Initialize the liveness detector
detector = LivenessDetector()


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
        "model": "MiniFASNetV2",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model_loaded": detector.is_loaded(),
        "model_path": detector.model_path
    }


@app.post("/v1/verify-liveness", response_model=LivenessResponse)
async def verify_liveness(request: LivenessRequest):
    """
    Verify if the face in the image is real or a spoof.

    Args:
        request: Contains base64 encoded image

    Returns:
        LivenessResponse with verification result
    """
    try:
        # Decode base64 image
        image = decode_base64_image(request.image_base64)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        # Run liveness detection
        result = detector.predict(image)

        return LivenessResponse(
            is_real=result["is_real"],
            confidence=result["confidence"],
            threshold=result["threshold"],
            message="Real face detected" if result["is_real"] else "Spoof detected",
            details={
                "raw_score": result.get("raw_score", 0),
                "processing_time_ms": result.get("processing_time_ms", 0)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/v1/batch-verify")
async def batch_verify(images: list[LivenessRequest]):
    """
    Verify multiple images in batch.
    Useful for multi-frame verification.
    """
    results = []

    for i, request in enumerate(images):
        try:
            image = decode_base64_image(request.image_base64)
            if image is not None:
                result = detector.predict(image)
                results.append({
                    "index": i,
                    "is_real": result["is_real"],
                    "confidence": result["confidence"]
                })
            else:
                results.append({
                    "index": i,
                    "error": "Invalid image"
                })
        except Exception as e:
            results.append({
                "index": i,
                "error": str(e)
            })

    # Calculate aggregate result
    valid_results = [r for r in results if "is_real" in r]
    if valid_results:
        avg_confidence = sum(r["confidence"] for r in valid_results) / len(valid_results)
        all_real = all(r["is_real"] for r in valid_results)
    else:
        avg_confidence = 0
        all_real = False

    return {
        "aggregate": {
            "is_real": all_real,
            "avg_confidence": avg_confidence,
            "frames_analyzed": len(valid_results)
        },
        "individual_results": results
    }


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
