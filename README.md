# BioGuard Nexus

Advanced Liveness Verification Platform powered by AI & Physics.

## Overview

BioGuard Nexus is a comprehensive security verification system that combines:
- **Environment Shield** - Root, emulator, and hook detection
- **Light-Sync Challenge** - Physics-based reflection analysis
- **AI Face Liveness** - MiniFASNetV2 deep learning model

## Architecture

```
bioguard-nexus/
├── bioguard-mobile/          # Flutter Mobile App
├── bioguard-dashboard/       # Next.js Merchant Dashboard
├── bioguard-ai-service/      # Python AI Service
└── shared/                   # Documentation & Schemas
```

## Quick Start

### 1. Mobile App (Flutter)

```bash
cd bioguard-mobile

# Install dependencies
flutter pub get

# Run on device
flutter run

# Build APK
flutter build apk --release
```

### 2. Dashboard (Next.js)

```bash
cd bioguard-dashboard

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your Supabase credentials

# Run development server
npm run dev

# Build for production
npm run build
```

### 3. AI Service (Python)

```bash
cd bioguard-ai-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add your MiniFASNetV2.onnx model to models/

# Run server
uvicorn main:app --reload
```

## Deployment

### Dashboard (Vercel)

1. Push to GitHub
2. Import project in Vercel
3. Add environment variables
4. Deploy

### AI Service (Docker)

```bash
cd bioguard-ai-service

# Build image
docker build -t bioguard-ai .

# Run container
docker run -p 8000:8000 -v ./models:/app/models bioguard-ai
```

### Mobile App

```bash
cd bioguard-mobile

# Build release APK
flutter build apk --release

# The APK will be at:
# build/app/outputs/flutter-apk/app-release.apk
```

## Configuration

### Supabase Setup

1. Create a new Supabase project
2. Run the SQL from `shared/database-schema.sql`
3. Enable Realtime for `verification_sessions` table
4. Copy project URL and keys to dashboard `.env.local`

### Deep Link Configuration

Android (already configured in AndroidManifest.xml):
```xml
<intent-filter>
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="bioguard" android:host="verify" />
</intent-filter>
```

## API Documentation

See [shared/api-specification.md](shared/api-specification.md) for complete API documentation.

## Tech Stack

- **Mobile**: Flutter (Dart) + Kotlin (Android Native)
- **Dashboard**: Next.js 14 + TypeScript + Tailwind CSS
- **AI Service**: Python + FastAPI + ONNX Runtime
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Vercel + Docker

## Security Features

### Module A: Environment Shield
- Developer Mode detection
- USB Debugging detection
- Root access detection
- Emulator detection
- Frida/Xposed hook detection

### Module B: Light-Sync Challenge
- Screen flash color challenge
- Camera exposure locking
- Differential frame analysis
- Physics-based reflection verification

### Module C: AI Face Liveness
- MiniFASNetV2 deep learning model
- 2.7x scale context analysis
- Multi-scale anti-spoofing
- Photo/Video/Mask detection

### Module D: Platform Integration
- Deep linking for seamless app launch
- Real-time status updates
- Webhook notifications
- Session management

## License

Proprietary - All rights reserved.

## Team

Built for Hackathon 2024
