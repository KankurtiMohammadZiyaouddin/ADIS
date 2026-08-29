import os
import sys

# Ensure backend directory is in Python module search path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import Optional

from services.prediction import PredictionService

app = FastAPI(
    title="ADIS Universal AI Deepfake & Synthetic Image Detection API",
    description="Multi-Model API featuring UniversalFakeDetect (CLIP ViT-L/14), HongguLiu XceptionNet (FaceForensics++), and Face-X-Ray",
    version="2.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory Setup
RESULTS_DIR = os.path.join(BASE_DIR, "results")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "models", "checkpoints")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# Mount Static Directory for serving heatmap overlays
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

# Initialize Prediction Service Manager
prediction_service = PredictionService(
    checkpoint_dir=CHECKPOINT_DIR,
    results_dir=RESULTS_DIR
)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

@app.get("/api/health")
def health_check():
    """
    Health check endpoint returning status and loaded flags for all 3 detectors.
    """
    return {
        "status": "ok",
        "universal_fake_detect_loaded": prediction_service.universal_loaded,
        "xception_loaded": prediction_service.xception_loaded,
        "face_xray_loaded": prediction_service.face_xray_loaded,
        "device": str(prediction_service.device)
    }

@app.post("/api/predict")
async def predict_deepfake(
    image: UploadFile = File(...),
    detector: Optional[str] = Form("all")
):
    """
    Multi-Model Image Deepfake & AI-Generated Image Detection Endpoint.
    Accepts multipart/form-data with 'image' field and optional 'detector' parameter.
    """
    if not image or not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file provided in request."
        )

    # 1. Extension Validation
    file_ext = os.path.splitext(image.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{file_ext}'. Allowed formats: JPG, JPEG, PNG, WEBP."
        )

    # 2. Content Type Validation
    if image.content_type and image.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type '{image.content_type}'. Allowed types: image/jpeg, image/png, image/webp."
        )

    # 3. Read Bytes & Validate Size
    try:
        contents = await image.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded image bytes: {str(e)}"
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    # 4. Run Model Prediction Pipeline
    try:
        result = prediction_service.predict_image(
            image_bytes=contents,
            filename=image.filename,
            selected_detector=detector
        )
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "prediction": "ERROR",
                "confidence": 0.0,
                "face_detected": False,
                "message": f"Internal model inference failure: {str(e)}",
                "heatmap_url": None,
                "results": {}
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
