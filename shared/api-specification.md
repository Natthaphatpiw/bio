# BioGuard Nexus API Specification

## Overview

BioGuard Nexus consists of three main services:

1. **Dashboard API** (Next.js) - Merchant portal and session management
2. **AI Service** (Python/FastAPI) - Face liveness detection
3. **Mobile App** (Flutter) - Security verification agent

---

## Dashboard API Endpoints

### Base URL
```
Production: https://bioguard-dashboard.vercel.app
Local: http://localhost:3000
```

### POST /api/callback

Receives verification results from the mobile app.

**Request:**
```json
{
  "session_id": "uuid",
  "overall_status": "COMPLETED | FAILED",
  "result": {
    "environment": {
      "isSafe": true,
      "devMode": false,
      "usbDebug": false,
      "root": false,
      "emulator": false,
      "hooking": false
    },
    "lightSync": {
      "pass": true,
      "confidence": 0.92,
      "redDiff": { "redChannel": 25.5, "greenChannel": 8.2, "blueChannel": 5.1 },
      "blueDiff": { "redChannel": 4.3, "greenChannel": 7.8, "blueChannel": 28.9 }
    },
    "faceLiveness": {
      "isReal": true,
      "confidence": 0.95
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "status": "COMPLETED",
  "message": "Verification result recorded"
}
```

### GET /api/session/{id}

Get session configuration and status.

**Response:**
```json
{
  "id": "uuid",
  "status": "PENDING",
  "config": {
    "check_emulator": true,
    "light_sync": true,
    "face_liveness": true
  },
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

## AI Service API Endpoints

### Base URL
```
Production: https://bioguard-ai.your-server.com
Local: http://localhost:8000
```

### POST /v1/verify-liveness

Verify if a face image is real or a spoof.

**Request:**
```json
{
  "image_base64": "base64_encoded_image_data"
}
```

**Response:**
```json
{
  "is_real": true,
  "confidence": 0.95,
  "threshold": 0.90,
  "message": "Real face detected",
  "details": {
    "raw_score": 2.34,
    "processing_time_ms": 45.2
  }
}
```

### POST /v1/batch-verify

Verify multiple images for multi-frame analysis.

**Request:**
```json
[
  { "image_base64": "base64_image_1" },
  { "image_base64": "base64_image_2" },
  { "image_base64": "base64_image_3" }
]
```

**Response:**
```json
{
  "aggregate": {
    "is_real": true,
    "avg_confidence": 0.93,
    "frames_analyzed": 3
  },
  "individual_results": [
    { "index": 0, "is_real": true, "confidence": 0.95 },
    { "index": 1, "is_real": true, "confidence": 0.92 },
    { "index": 2, "is_real": true, "confidence": 0.91 }
  ]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_path": "models/MiniFASNetV2.onnx"
}
```

---

## Deep Link Specification

### Custom Scheme
```
bioguard://verify?session_id={SESSION_ID}
```

### Universal Link (HTTPS)
```
https://bioguard-dashboard.vercel.app/verify/{SESSION_ID}
```

### Parameters
- `session_id` (required): UUID of the verification session

---

## Webhook Payload

When a verification is complete and webhook URL is configured:

```json
{
  "event": "verification.completed",
  "session_id": "uuid",
  "status": "COMPLETED | FAILED",
  "result": {
    "environment": { ... },
    "lightSync": { ... },
    "faceLiveness": { ... }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Error Responses

All APIs return errors in this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Common Error Codes
- `INVALID_SESSION` - Session ID not found or expired
- `INVALID_IMAGE` - Cannot decode image data
- `PROCESSING_ERROR` - AI model inference failed
- `RATE_LIMITED` - Too many requests
- `UNAUTHORIZED` - Invalid API key

---

## Security Considerations

1. **Session Expiration**: Sessions expire after 30 minutes
2. **One-time Use**: Each session can only be completed once
3. **Webhook Verification**: Use HMAC signature to verify webhook authenticity
4. **Rate Limiting**: Implement rate limiting on all endpoints
5. **HTTPS Only**: All production traffic must use HTTPS
