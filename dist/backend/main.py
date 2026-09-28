import os
import sys
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Limit OpenBLAS and OpenMP threads to prevent memory allocation collisions in PyTorch multi-processing on Windows
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, File, UploadFile, Query, Form, Body, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.audio_detector import analyze_audio
from services.video_detector import analyze_video
from services.image_detector import analyze_image
from services.forensic_fusion import fuse_cross_modal_evidence
import database as db

# Initialize 3-model Image Forensic PredictionService
try:
    from services.prediction import PredictionService
    CHECKPOINT_DIR = str(BASE_DIR / "models" / "checkpoints")
    RESULTS_DIR = str(BASE_DIR / "results")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    prediction_service = PredictionService(checkpoint_dir=CHECKPOINT_DIR, results_dir=RESULTS_DIR)
    print(f"[Main] PredictionService ready: Universal={prediction_service.universal_loaded}, Xception={prediction_service.xception_loaded}, Face-X-Ray={prediction_service.face_xray_loaded}")
except Exception as e:
    print(f"[Main] Warning: Could not initialize PredictionService: {e}")
    prediction_service = None


app = FastAPI(
    title="ADIS Forensic Suite API",
    version="2.2.0",
    description="Modular Multimodal Digital Forensic Analysis API with 3-Model Image Pipeline, YAMNet Audio, Frame-Sampled Video, Cross-Modal Fusion, and Case Management",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount /results static files for heatmap overlays
RESULTS_PATH = BASE_DIR / "results"
os.makedirs(RESULTS_PATH, exist_ok=True)
app.mount("/results", StaticFiles(directory=str(RESULTS_PATH)), name="results")


@app.on_event("startup")
def startup_event():
    db.init_db()


@app.get("/")
def root():
    return {
        "message": "ADIS backend is running with 3-Model Image Pipeline, Audio YAMNet, Video Sampler & Case Management",
        "service": "ADIS Forensic Suite API v2.2",
        "modalities": ["image", "audio", "video", "cross-modal"],
        "database": "SQLite (adis_forensics.db)",
    }


@app.get("/api/health")
def health():
    universal_loaded = bool(prediction_service and prediction_service.universal_loaded)
    xception_loaded = bool(prediction_service and prediction_service.xception_loaded)
    face_xray_loaded = bool(prediction_service and prediction_service.face_xray_loaded)
    all_loaded = universal_loaded and xception_loaded and face_xray_loaded
    any_loaded = universal_loaded or xception_loaded or face_xray_loaded

    return {
        "status": "ok" if any_loaded else "healthy",
        "backend": "online",
        "database": "connected",
        "model_loaded": any_loaded,
        "all_models_loaded": all_loaded,
        "universal_fake_detect_loaded": universal_loaded,
        "xception_loaded": xception_loaded,
        "face_xray_loaded": face_xray_loaded,
        "models": {
            "universal_fake_detect": {
                "loaded": universal_loaded,
                "checkpoint": "models/universal_fake_detect/fc_weights.pth"
            },
            "xceptionnet": {
                "loaded": xception_loaded,
                "checkpoint": "models/checkpoints/FF++_c23.pth"
            },
            "face_xray": {
                "loaded": face_xray_loaded,
                "checkpoint": "models/checkpoints/face_xray.pth"
            },
            "audio_yamnet": {
                "loaded": True,
                "checkpoint": "external/Deepfake-YamNet"
            }
        },
        "services": {
            "image": "ready (3-Model Pipeline: UniversalFakeDetect + XceptionNet + Face-X-Ray)",
            "audio": "ready (YAMNet Sub-Detector)",
            "video": "ready (Frame-Based Sampler)",
            "cross_modal": "ready (Authoritative Forensic Fusion)",
            "cases": "ready (SQLite Database Layer)"
        }
    }


# Limits and Whitelists
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
MAX_IMAGE_SIZE = 25 * 1024 * 1024  # 25MB limit

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB limit

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
MAX_VIDEO_SIZE = 150 * 1024 * 1024  # 150MB limit


def make_standard_envelope(media_type: str, filename: str, result: dict, extra_evidence: dict = None, extra_analysis: dict = None, extra_forensic: dict = None):
    now_iso = datetime.now(timezone.utc).isoformat()
    analysis_id = result.get("analysis_id", f"{media_type.upper()}-{int(datetime.now().timestamp())}")

    model_name = result.get("model", "ADIS-Detector")
    model_version = result.get("model_version", "1.0.0")
    proc_time = result.get("processing_time_ms", 0)

    envelope = {
        "success": True,
        "status": "success",
        "analysis_id": analysis_id,
        "media_type": media_type,
        "filename": filename,
        "sha256": result.get("sha256", ""),
        "file_size_bytes": result.get("file_size_bytes", 0),
        "classification": result.get("classification", "INCONCLUSIVE"),
        "confidence": result.get("confidence", 0.0),
        "detector_agreement": result.get("detector_agreement", True),
        "disagreement_warning": result.get("disagreement_warning"),
        "model": {
            "name": model_name,
            "version": model_version
        },
        "detectors": result.get("detectors", []),
        "forensic_indicators": result.get("forensic_indicators", []),
        "processing": {
            "processing_time_ms": proc_time
        },
        "timestamp": now_iso,
        "disclaimer": result.get("disclaimer", "Probabilistic forensic assessment. Not standalone legal proof.")
    }

    if extra_evidence:
        envelope["evidence"] = {
            "filename": filename,
            "file_size_bytes": result.get("file_size_bytes", 0),
            "sha256": result.get("sha256", ""),
            **extra_evidence
        }
    else:
        envelope["evidence"] = {
            "filename": filename,
            "file_size_bytes": result.get("file_size_bytes", 0),
            "sha256": result.get("sha256", "")
        }

    if extra_analysis:
        envelope["analysis"] = {
            "classification": result.get("classification", "INCONCLUSIVE"),
            "confidence": result.get("confidence", 0.0),
            "model": model_name,
            "model_version": model_version,
            "processing_time_ms": proc_time,
            **extra_analysis
        }
    else:
        envelope["analysis"] = {
            "classification": result.get("classification", "INCONCLUSIVE"),
            "confidence": result.get("confidence", 0.0),
            "model": model_name,
            "model_version": model_version,
            "processing_time_ms": proc_time
        }

    if extra_forensic:
        envelope["forensic"] = extra_forensic

    try:
        db.save_analysis(envelope)
    except Exception as db_err:
        print(f"[Database Error] Could not persist analysis {analysis_id}: {db_err}")

    return envelope


# ---------------------------------------------------------------------------
# 1. 3-MODEL IMAGE PREDICT ENDPOINT (Ahtesham's Pipeline)
# ---------------------------------------------------------------------------
@app.post("/api/predict")
async def predict_deepfake_image(
    image: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    detector: Optional[str] = Form("all")
):
    """
    Multi-Model Image Deepfake & AI-Generated Image Detection Endpoint.
    Runs UniversalFakeDetect, XceptionNet, and Face-X-Ray with Boundary Heatmap generation.
    Accepts 'image', 'image_file', or 'file' for cross-client compatibility.
    """
    target_file = image or image_file or file
    if not target_file or not target_file.filename:
        return JSONResponse(
            status_code=400,
            content={"success": False, "analysis_completed": False, "error": "No image file provided in request."}
        )

    file_ext = Path(target_file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"success": False, "analysis_completed": False, "error": f"Unsupported file extension '{file_ext}'."}
        )

    try:
        contents = await target_file.read()
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "analysis_completed": False, "error": f"Failed to read image bytes: {str(e)}"}
        )

    if len(contents) > MAX_IMAGE_SIZE:
        return JSONResponse(
            status_code=413,
            content={"success": False, "analysis_completed": False, "error": "Image file exceeds size limit."}
        )

    if len(contents) == 0:
        return JSONResponse(
            status_code=400,
            content={"success": False, "analysis_completed": False, "error": "Uploaded image file is empty (0 bytes)."}
        )

    if prediction_service is None:
        return JSONResponse(
            status_code=500,
            content={"success": False, "analysis_completed": False, "error": "Image PredictionService is unavailable."}
        )

    try:
        result = prediction_service.predict_image(
            image_bytes=contents,
            filename=target_file.filename,
            selected_detector=detector
        )

        # Save record to SQLite history
        try:
            db.save_analysis({
                "analysis_id": f"IMG-{int(datetime.now().timestamp())}",
                "media_type": "image",
                "filename": target_file.filename,
                "sha256": result.get("sha256", ""),
                "file_size_bytes": len(contents),
                "classification": result.get("prediction", "INCONCLUSIVE"),
                "confidence": result.get("confidence", 0.0) / 100.0 if result.get("confidence", 0.0) > 1.0 else result.get("confidence", 0.0),
                "model_name": "UniversalFakeDetect + XceptionNet + Face-X-Ray",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload_json": result
            })
        except Exception:
            pass

        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "analysis_completed": False, "error": f"Internal model inference failure: {str(e)}"}
        )


# ---------------------------------------------------------------------------
# 2. IMAGE FORENSIC STANDARDIZED ENDPOINT (EfficientNet + ELA + Multi-Model)
# ---------------------------------------------------------------------------
@app.post("/api/image/analyze")
async def image_analyze(
    image_file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None)
):
    target_file = image_file or image or file
    if not target_file or not target_file.filename or not target_file.filename.strip():
        return JSONResponse(
            status_code=400,
            content={"success": False, "status": "error", "error": {"code": "MISSING_FILENAME", "message": "No filename provided."}}
        )

    suffix = Path(target_file.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"success": False, "status": "error", "error": {"code": "INVALID_FORMAT", "message": f"Unsupported image extension '{suffix}'."}}
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            shutil.copyfileobj(target_file.file, tmp)

        result = analyze_image(str(temp_path))
        return make_standard_envelope("image", target_file.filename, result)
    except ValueError as val_err:
        return JSONResponse(
            status_code=422,
            content={"success": False, "status": "error", "error": {"code": "CORRUPT_IMAGE_DATA", "message": str(val_err)}}
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"success": False, "status": "error", "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)}}
        )
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 3. AUDIO FORENSIC ENDPOINT
# ---------------------------------------------------------------------------
@app.post("/api/audio/analyze")
async def audio_analyze(
    audio_file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None)
):
    target_file = audio_file or audio or file
    if not target_file or not target_file.filename or not target_file.filename.strip():
        return JSONResponse(
            status_code=400,
            content={"success": False, "status": "error", "error": {"code": "MISSING_FILENAME", "message": "No filename was provided."}}
        )

    suffix = Path(target_file.filename).suffix.lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"success": False, "status": "error", "error": {"code": "INVALID_FORMAT", "message": f"Unsupported audio format '{suffix}'."}}
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            shutil.copyfileobj(target_file.file, tmp)

        result = analyze_audio(str(temp_path))
        extra_evidence = {
            "duration_seconds": result.get("duration_seconds", 0.0),
            "sample_rate": result.get("sample_rate", 16000),
            "channels": result.get("channels", 1)
        }
        return make_standard_envelope("audio", target_file.filename, result, extra_evidence)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"success": False, "status": "error", "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)}}
        )
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 4. VIDEO FORENSIC ENDPOINT
# ---------------------------------------------------------------------------
@app.post("/api/video/analyze")
async def video_analyze(
    video_file: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None)
):
    target_file = video_file or video or file
    if not target_file or not target_file.filename or not target_file.filename.strip():
        return JSONResponse(
            status_code=400,
            content={"success": False, "status": "error", "error": {"code": "MISSING_FILENAME", "message": "No filename provided."}}
        )

    suffix = Path(target_file.filename).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"success": False, "status": "error", "error": {"code": "INVALID_FORMAT", "message": f"Unsupported video format '{suffix}'."}}
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            shutil.copyfileobj(target_file.file, tmp)

        result = analyze_video(str(temp_path))
        extra_analysis = {
            "frames_analyzed": result.get("frame_count", 0),
            "frames_fake": result.get("frames_fake", 0),
            "frames_real": result.get("frames_real", 0),
            "is_true_temporal_model": False,
            "aggregation_method": result.get("aggregation_method", "Frame-Sampled Majority Vote")
        }
        extra_evidence = {
            "duration_seconds": result.get("duration_seconds", 0.0),
            "resolution": result.get("resolution", "N/A"),
            "fps": result.get("fps", 0.0)
        }
        extra_forensic = {
            "frame_results": result.get("frame_results", []),
            "temporal_analysis": result.get("temporal_analysis", {})
        }
        return make_standard_envelope("video", target_file.filename, result, extra_evidence, extra_analysis, extra_forensic)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"success": False, "status": "error", "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)}}
        )
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 5. CROSS-MODAL FORENSIC FUSION ENDPOINT
# ---------------------------------------------------------------------------
@app.post("/api/cross-modal/analyze")
async def cross_modal_analyze(request: Request):
    """
    Authoritative backend cross-modal fusion correlating evidence across Image, Audio, and Video.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Invalid JSON body provided for cross-modal analysis."}
        )

    if not isinstance(payload, dict) or not payload:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "NO_MODALITIES_PROVIDED",
                    "message": "Cross-modal payload must contain modality evidence dictionaries (image, audio, and/or video)."
                }
            }
        )

    result = fuse_cross_modal_evidence(payload)
    if not result.get("success"):
        return JSONResponse(status_code=400, content=result)

    return JSONResponse(status_code=200, content=result)


# ---------------------------------------------------------------------------
# 6. HISTORY & DATABASE ENDPOINTS
# ---------------------------------------------------------------------------
@app.get("/api/history")
def get_history(limit: int = Query(default=200, ge=1, le=500)):
    records = db.get_history(limit=limit)
    return {"success": True, "count": len(records), "history": records}


@app.delete("/api/history")
def clear_history():
    deleted_count = db.clear_history()
    return {"success": True, "message": f"Cleared {deleted_count} records", "deleted_count": deleted_count}


# ---------------------------------------------------------------------------
# 7. CASE MANAGEMENT ENDPOINTS (Full SQLite Backing)
# ---------------------------------------------------------------------------

class CaseCreateSchema(BaseModel):
    title: str = Field(..., min_length=2, description="Case title")
    description: Optional[str] = ""
    investigator: Optional[str] = "Active Investigator"
    priority: Optional[str] = "MEDIUM"
    status: Optional[str] = "ACTIVE"
    metadata: Optional[Dict[str, Any]] = None


class CaseUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    investigator: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EvidenceCreateSchema(BaseModel):
    media_type: str = Field(..., description="image, audio, or video")
    filename: str
    sha256: Optional[str] = ""
    file_size_bytes: Optional[int] = 0
    analysis_id: Optional[str] = ""
    verdict: Optional[str] = "INCONCLUSIVE"
    confidence: Optional[float] = 0.0
    metadata: Optional[Dict[str, Any]] = None


@app.get("/api/cases")
def list_cases(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(default=100, ge=1, le=500)
):
    cases = db.get_cases(status=status, priority=priority, limit=limit)
    return {
        "success": True,
        "count": len(cases),
        "cases": cases
    }


@app.post("/api/cases")
def create_case(case_req: CaseCreateSchema):
    new_case = db.create_case(case_req.dict())
    return {
        "success": True,
        "message": "Investigation case created successfully",
        "case": new_case
    }


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    case_item = db.get_case(case_id)
    if not case_item:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    return {
        "success": True,
        "case": case_item
    }


@app.put("/api/cases/{case_id}")
def update_case(case_id: str, update_req: CaseUpdateSchema):
    updated = db.update_case(case_id, update_req.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    return {
        "success": True,
        "message": "Case updated successfully",
        "case": updated
    }


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str):
    deleted = db.delete_case(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    return {
        "success": True,
        "message": f"Case '{case_id}' and all attached evidence deleted successfully."
    }


@app.get("/api/cases/{case_id}/evidence")
def list_case_evidence(case_id: str):
    evidence_list = db.get_case_evidence(case_id)
    return {
        "success": True,
        "case_id": case_id,
        "count": len(evidence_list),
        "evidence": evidence_list
    }


@app.post("/api/cases/{case_id}/evidence")
def attach_evidence_to_case(case_id: str, evidence_req: EvidenceCreateSchema):
    case_item = db.get_case(case_id)
    if not case_item:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")

    new_evidence = db.add_evidence_to_case(case_id, evidence_req.dict())
    return {
        "success": True,
        "message": "Evidence successfully linked to case",
        "evidence": new_evidence
    }
