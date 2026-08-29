# ADIS Forensic Suite — Multi-Model AI Deepfake & Synthetic Image Detection

A complete digital forensic application featuring real-time **AI Deepfake & Synthetic Image Detection** powered by a **Python FastAPI backend** and a **Vite + React frontend**.

---

## 🚀 Multi-Detector Architecture

The Image Forensics pipeline orchestrates three specialized deepfake detection models:

1. **UniversalFakeDetect (CVPR 2023)**:
   - **Paper**: *"Towards Universal Fake Image Detectors that Generalize Across Generative Models"* (Ojha et al., CVPR 2023).
   - **Backbone**: CLIP ViT-L/14 Vision Transformer + Linear Classifier (`pretrained_weights/fc_weights.pth`).
   - **Scope**: General AI-generated image detection across generative models (GANs, Diffusion models, Midjourney, Stable Diffusion, DALL-E, landscapes, art, photos, and faces). Does **NOT** require face detection.
   
2. **HongguLiu Deepfake-Detection (XceptionNet)**:
   - **Repository**: [HongguLiu/Deepfake-Detection](https://github.com/HongguLiu/Deepfake-Detection)
   - **Backbone**: XceptionNet (FaceForensics++ benchmark; `FF++_c23.pth` / `FF++_c40.pth`).
   - **Scope**: Deepfake face forgery detection.

3. **Face-X-Ray Detector (CVPR 2020)**:
   - **Repository**: [wkq-wukaiqi/Face-X-Ray](https://github.com/wkq-wukaiqi/Face-X-Ray)
   - **Scope**: Face manipulation boundary detection & pixel-level X-ray heatmap overlay generation.

---

## 📦 Directory & File Structure

```
ADIS/
├── backend/
│   ├── app.py                     # FastAPI application entrypoint & API routes (/api/health, /api/predict)
│   ├── requirements.txt           # Backend dependencies (fastapi, uvicorn, torch, torchvision, opencv-python, numpy)
│   ├── .env.example               # Environment variables configuration
│   ├── detector/                  # Face-X-Ray model architecture & boundary evaluation
│   │   ├── DeepFakeMask.py
│   │   ├── dataset.py
│   │   ├── evaluate.py
│   │   └── utils.py
│   ├── detectors/
│   │   ├── honggu_xception/       # XceptionNet model package
│   │   │   ├── xception.py
│   │   │   └── preprocessing.py
│   │   └── universal_fake_detect/ # UniversalFakeDetect (CLIP ViT-L/14) package
│   │       ├── model.py
│   │       └── preprocessing.py
│   ├── models/
│   │   ├── checkpoints/           # Model weight files: FF++_c23.pth, face_xray.pth
│   │   └── universal_fake_detect/ # Pretrained weight file: fc_weights.pth
│   ├── services/
│   │   ├── prediction.py          # Multi-model prediction service manager
│   │   ├── face_detection.py      # OpenCV Haar Cascade & face cropping
│   │   └── preprocessing.py       # Image resizing & tensor normalization
│   ├── uploads/                   # Temporary file upload storage
│   └── results/                   # Generated boundary heatmap images
├── src/
│   ├── components/                # Shared navigation & layout shell
│   ├── pages/                     # ImageForensicsPage.jsx (Connected to FastAPI backend)
│   └── App.jsx                    # React Router configuration
```

---

## 🤖 Pretrained Model Checkpoint Setup

The backend loads model weights from the following paths:

1. **UniversalFakeDetect (`fc_weights.pth`)**:
   - **Placement**: `backend/models/universal_fake_detect/fc_weights.pth` (or `backend/models/checkpoints/fc_weights.pth`)
   - **Source**: [WisconsinAIVision/UniversalFakeDetect Repository](https://github.com/WisconsinAIVision/UniversalFakeDetect)

2. **HongguLiu XceptionNet (`FF++_c23.pth` / `FF++_c40.pth`)**:
   - **Placement**: `backend/models/checkpoints/FF++_c23.pth`
   - **Source**: [HongguLiu/Deepfake-Detection Repository](https://github.com/HongguLiu/Deepfake-Detection)

3. **Face-X-Ray (`face_xray.pth`)**:
   - **Placement**: `backend/models/checkpoints/face_xray.pth`
   - **Source**: [wkq-wukaiqi/Face-X-Ray Repository](https://github.com/wkq-wukaiqi/Face-X-Ray)

---

## 🛰️ API Endpoints

### 1. Health Check
`GET /api/health`

**Response:**
```json
{
  "status": "ok",
  "universal_fake_detect_loaded": true,
  "xception_loaded": true,
  "face_xray_loaded": true,
  "device": "cpu"
}
```

### 2. Multi-Detector Image Prediction
`POST /api/predict` (Accepts `multipart/form-data` with `image` and optional `detector` parameter)

**Response:**
```json
{
  "success": true,
  "prediction": "AI_GENERATED",
  "confidence": 94.72,
  "face_detected": true,
  "message": "All available detectors classified this image as likely manipulated/AI-generated.",
  "heatmap_url": "/results/heatmap_a1b2c3d4e5.png",
  "results": {
    "universal_fake_detect": {
      "detector": "UniversalFakeDetect",
      "architecture": "CLIP:ViT-L/14",
      "prediction": "AI_GENERATED",
      "confidence": 94.72
    },
    "xception": {
      "detector": "XceptionNet (FaceForensics++)",
      "checkpoint": "FF++_c23.pth",
      "prediction": "FAKE",
      "confidence": 91.34
    },
    "face_xray": {
      "detector": "Face-X-Ray",
      "prediction": "FAKE",
      "confidence": 89.51
    }
  }
}
```

---

## ⚡ How to Run

### 1. Start FastAPI Backend
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start backend service
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start Frontend App
```bash
# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

Open `http://localhost:5173/image-forensics` in your browser.

---

## 📜 Research Attribution & Licenses

- **UniversalFakeDetect**: [MIT License]. Citation: Ojha et al., *"Towards Universal Fake Image Detectors that Generalize Across Generative Models"*, CVPR 2023. Repository: `WisconsinAIVision/UniversalFakeDetect`.
- **HongguLiu/Deepfake-Detection**: [Apache-2.0 License]. FaceForensics++ benchmark implementation by Honggu Liu.
- **Face-X-Ray**: Li et al., *"Face X-Ray for More General Face Forgery Detection"*, CVPR 2020.
