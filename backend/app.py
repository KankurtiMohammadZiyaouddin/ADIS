import os
import sys

# Limit OpenBLAS and OpenMP threads to prevent memory allocation collisions in PyTorch multi-processing on Windows
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

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
    "http://127.0.0.1:3000",
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
    all_loaded = (
        prediction_service.universal_loaded and 
        prediction_service.xception_loaded and 
        prediction_service.face_xray_loaded
    )
    any_loaded = (
        prediction_service.universal_loaded or 
        prediction_service.xception_loaded or 
        prediction_service.face_xray_loaded
    )
    return {
        "status": "ok" if any_loaded else "degraded",
        "backend": "online",
        "model_loaded": any_loaded,
        "all_models_loaded": all_loaded,
        "models": {
            "universal_fake_detect": {
                "loaded": prediction_service.universal_loaded,
                "checkpoint": "models/universal_fake_detect/fc_weights.pth"
            },
            "xceptionnet": {
                "loaded": prediction_service.xception_loaded,
                "checkpoint": f"models/checkpoints/{prediction_service.active_checkpoint_xception}"
            },
            "face_xray": {
                "loaded": prediction_service.face_xray_loaded,
                "checkpoint": "models/checkpoints/face_xray.pth"
            }
        },
        "device": str(prediction_service.device)
    }

@app.post("/api/predict")
def predict_deepfake(
    image: UploadFile = File(...),
    detector: Optional[str] = Form("all")
):
    """
    Multi-Model Image Deepfake & AI-Generated Image Detection Endpoint.
    Accepts multipart/form-data with 'image' field.
    Returns prediction, confidence score, face status, inference time, and heatmap URL.
    """
    if not image or not image.filename:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "analysis_completed": False,
                "error": "No image file provided in request."
            }
        )

    # 1. Extension Validation
    file_ext = os.path.splitext(image.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "analysis_completed": False,
                "error": f"Unsupported file extension '{file_ext}'. Allowed formats: JPG, JPEG, PNG, WEBP."
            }
        )

    # 2. Content Type Validation
    if image.content_type and image.content_type.lower() not in ALLOWED_MIME_TYPES:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "analysis_completed": False,
                "error": f"Invalid MIME type '{image.content_type}'. Allowed types: image/jpeg, image/png, image/webp."
            }
        )

    # 3. Read Bytes & Validate Size
    try:
        contents = image.file.read()
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "analysis_completed": False,
                "error": f"Failed to read uploaded image bytes: {str(e)}"
            }
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "analysis_completed": False,
                "error": f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
            }
        )

    if len(contents) == 0:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "analysis_completed": False,
                "error": "Uploaded image file is empty (0 bytes)."
            }
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
                "analysis_completed": False,
                "error": f"Internal model inference failure: {str(e)}"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
