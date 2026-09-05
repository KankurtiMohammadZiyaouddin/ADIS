from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone

from fastapi import FastAPI, File, UploadFile, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.audio_detector import analyze_audio
from services.video_detector import analyze_video
from services.image_detector import analyze_image
import database as db


app = FastAPI(
    title="ADIS Forensic Suite API",
    version="2.1.0",
    description="Modular Multimodal Forensic Analysis API with Sub-Detectors, ELA Indicators, and Forensic Fusion",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    db.init_db()


@app.get("/")
def root():
    return {
        "message": "ADIS backend is running with Modular Sub-Detector Architecture",
        "service": "ADIS Forensic Suite API v2.1",
        "modalities": ["image", "audio", "video"],
        "database": "SQLite (adis_forensics.db)",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "services": {
            "image": "ready (EfficientNet + ELA Analyzer)",
            "audio": "ready (YAMNet Sub-Detector)",
            "video": "ready (Frame-Based Sampler)",
        }
    }


# Limits and Whitelists
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
MAX_IMAGE_SIZE = 25 * 1024 * 1024  # 25MB limit

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB limit

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
MAX_VIDEO_SIZE = 150 * 1024 * 1024  # 150MB limit


# Helper for standard response top-level fields
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
        "disclaimer": result.get("disclaimer", "Forensic outputs are probabilistic model classifications and do not constitute legal proof."),
        "evidence": {
            "filename": filename,
            "file_size_bytes": result.get("file_size_bytes", 0),
            "sha256": result.get("sha256", ""),
            **(extra_evidence or {})
        },
        "analysis": {
            "classification": result.get("classification", "INCONCLUSIVE"),
            "confidence": result.get("confidence", 0.0),
            "model": model_name,
            "model_version": model_version,
            "processing_time_ms": proc_time,
            **(extra_analysis or {})
        },
        "forensic": {
            "analysis_id": analysis_id,
            "evidence_integrity": "SHA-256 calculated",
            "temporary_file_cleanup": True,
            **(extra_forensic or {})
        }
    }

    # Automatically persist to SQLite database
    try:
        db.save_analysis(envelope)
    except Exception as db_err:
        print(f"Database save warning: {db_err}")

    return envelope


# ---------------------------------------------------------------------------
# REST API: HISTORY & DATABASE COLLABORATION
# ---------------------------------------------------------------------------
@app.get("/api/history")
def get_history_records(limit: int = Query(200, ge=1, le=1000)):
    records = db.get_history(limit=limit)
    return {
        "success": True,
        "count": len(records),
        "history": records
    }


@app.delete("/api/history")
def clear_history_records():
    db.clear_history()
    return {
        "success": True,
        "message": "SQLite history cleared successfully."
    }


@app.get("/api/cases")
def get_cases():
    return {
        "success": True,
        "cases": [
            {
                "case_id": "#4492",
                "title": "Deepfake Executive Audio & Video Investigation",
                "status": "ACTIVE",
                "investigator": "Lead Investigator",
                "evidence_count": 4,
                "created_at": "2026-08-27T10:00:00Z"
            },
            {
                "case_id": "#4493",
                "title": "Image Splicing & ELA Verification",
                "status": "OPEN",
                "investigator": "Analyst Sarah Chen",
                "evidence_count": 2,
                "created_at": "2026-08-28T14:30:00Z"
            }
        ]
    }


# ---------------------------------------------------------------------------
# 1. IMAGE FORENSIC ENDPOINT
# ---------------------------------------------------------------------------
@app.post("/api/image/analyze")
async def image_analyze(image_file: UploadFile = File(...)):
    if not image_file.filename or not image_file.filename.strip():
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "MISSING_FILENAME",
                    "message": "No filename was provided in the upload."
                }
            }
        )

    suffix = Path(image_file.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "INVALID_IMAGE_FORMAT",
                    "message": f"Unsupported image file extension: '{suffix}'. Supported: JPG, JPEG, PNG, WEBP, BMP, TIFF."
                }
            }
        )

    try:
        image_file.file.seek(0, 2)
        file_size = image_file.file.tell()
        image_file.file.seek(0)
    except Exception:
        file_size = 0

    if file_size == 0:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "EMPTY_FILE",
                    "message": "Uploaded image file is empty (0 bytes)."
                }
            }
        )

    if file_size > MAX_IMAGE_SIZE:
        return JSONResponse(
            status_code=413,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"Image file size exceeds limit (25MB). Uploaded: {file_size} bytes."
                }
            }
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            shutil.copyfileobj(image_file.file, tmp)

        result = analyze_image(str(temp_path))

        extra_evidence = {
            "resolution": result.get("resolution", "N/A"),
            "width": result.get("width", 0),
            "height": result.get("height", 0),
            "format": result.get("format", "N/A"),
            "color_mode": result.get("color_mode", "N/A"),
            "mean_intensity": result.get("mean_intensity", 0.0)
        }
        extra_analysis = {
            "prob_fake": result.get("prob_fake", 0.0),
            "prob_real": result.get("prob_real", 0.0),
            "edge_variance": result.get("edge_variance", 0.0)
        }
        return make_standard_envelope("image", image_file.filename, result, extra_evidence, extra_analysis)

    except ValueError as val_err:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "UNPROCESSABLE_IMAGE",
                    "message": str(val_err)
                }
            }
        )
    except Exception as exc:
        print(f"Unexpected image analysis error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred during image forensic analysis."
                }
            }
        )
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 2. AUDIO FORENSIC ENDPOINT
# ---------------------------------------------------------------------------
@app.post("/api/audio/analyze")
async def audio_analyze(audio_file: UploadFile = File(...)):
    if not audio_file.filename or not audio_file.filename.strip():
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "MISSING_FILENAME",
                    "message": "No filename was provided in the upload."
                }
            }
        )

    suffix = Path(audio_file.filename).suffix.lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "INVALID_AUDIO_FORMAT",
                    "message": f"Unsupported file extension: '{suffix}'. Supported: WAV, MP3, M4A, FLAC, OGG."
                }
            }
        )

    try:
        audio_file.file.seek(0, 2)
        file_size = audio_file.file.tell()
        audio_file.file.seek(0)
    except Exception:
        file_size = 0

    if file_size == 0:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "EMPTY_FILE",
                    "message": "Uploaded audio file is empty (0 bytes)."
                }
            }
        )

    if file_size > MAX_AUDIO_SIZE:
        return JSONResponse(
            status_code=413,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds 10MB limit. Uploaded: {file_size} bytes."
                }
            }
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            shutil.copyfileobj(audio_file.file, tmp)

        result = analyze_audio(str(temp_path))

        extra_evidence = {
            "duration_seconds": result.get("duration_seconds", 0.0),
            "sample_rate": result.get("sample_rate", 0),
            "channels": result.get("channels", 0)
        }
        return make_standard_envelope("audio", audio_file.filename, result, extra_evidence)

    except ValueError as val_err:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "UNPROCESSABLE_AUDIO",
                    "message": str(val_err)
                }
            }
        )
    except Exception as exc:
        print(f"Unexpected audio analysis error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred during audio forensic analysis."
                }
            }
        )
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 3. VIDEO FORENSIC ENDPOINT
# ---------------------------------------------------------------------------
@app.post("/api/video/analyze")
async def video_analyze(video_file: UploadFile = File(...)):
    if not video_file.filename or not video_file.filename.strip():
        return JSONResponse(status_code=400, content={
            "success": False,
            "status": "error",
            "error": {"code": "MISSING_FILENAME", "message": "No filename provided."}
        })

    suffix = Path(video_file.filename).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        return JSONResponse(status_code=400, content={
            "success": False,
            "status": "error",
            "error": {
                "code": "INVALID_VIDEO_FORMAT",
                "message": f"Unsupported format '{suffix}'. Supported: MP4, WebM, MOV, AVI, MKV."
            }
        })

    try:
        video_file.file.seek(0, 2)
        file_size = video_file.file.tell()
        video_file.file.seek(0)
    except Exception:
        file_size = 0

    if file_size == 0:
        return JSONResponse(status_code=400, content={
            "success": False,
            "status": "error",
            "error": {"code": "EMPTY_FILE", "message": "Uploaded video file is empty (0 bytes)."}
        })

    if file_size > MAX_VIDEO_SIZE:
        return JSONResponse(status_code=413, content={
            "success": False,
            "status": "error",
            "error": {
                "code": "FILE_TOO_LARGE",
                "message": f"Video exceeds 150MB limit. Uploaded: {file_size} bytes."
            }
        })

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            shutil.copyfileobj(video_file.file, tmp)

        result = analyze_video(str(temp_path))

        extra_evidence = {
            "duration_seconds": result.get("duration_seconds", 0.0),
            "resolution": result.get("resolution", "N/A"),
            "fps": result.get("fps", 0),
            "frame_count": result.get("frame_count", 0),
        }
        extra_analysis = {
            "methodology": result.get("aggregation_method", "Frame-Sampled Spatial Majority Vote"),
            "is_true_temporal_model": False,
            "frames_analyzed": result.get("frame_count", 0),
            "frames_fake": result.get("frames_fake", 0),
            "frames_real": result.get("frames_real", 0),
            "temporal_analysis": result.get("temporal_analysis", {})
        }
        extra_forensic = {
            "frame_results": result.get("frame_results", []),
            "limitations_note": result.get("limitations_note", "Frame-sampled spatial detector.")
        }

        return make_standard_envelope("video", video_file.filename, result, extra_evidence, extra_analysis, extra_forensic)

    except ValueError as val_err:
        return JSONResponse(status_code=422, content={
            "success": False,
            "status": "error",
            "error": {"code": "UNPROCESSABLE_VIDEO", "message": str(val_err)}
        })
    except Exception as exc:
        print(f"Unexpected video analysis error: {exc}")
        return JSONResponse(status_code=500, content={
            "success": False,
            "status": "error",
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred during video analysis."}
        })
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 4. CROSS-MODAL ANALYSIS ENDPOINT
# ---------------------------------------------------------------------------
@app.post("/api/cross-modal/analyze")
async def cross_modal_analyze(payload: dict = Body(...)):
    """
    Authoritative backend cross-modal fusion.
    Accepts previously-stored analysis records for image, audio, and video
    and runs them through forensic_fusion.py to produce the single source-of-truth verdict.

    Payload schema:
      {
        "image": { "classification": str, "confidence": float, "detector_name": str, ... } | null,
        "audio": { "classification": str, "confidence": float, "detector_name": str, ... } | null,
        "video": { "classification": str, "confidence": float, "detector_name": str, ... } | null
      }
    """
    from services.forensic_fusion import fuse_detector_results
    from datetime import datetime, timezone

    image_rec = payload.get("image")
    audio_rec = payload.get("audio")
    video_rec = payload.get("video")

    if not any([image_rec, audio_rec, video_rec]):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "status": "error",
                "error": {
                    "code": "NO_MODALITIES_PROVIDED",
                    "message": "At least one modality (image, audio, or video) must be provided."
                }
            }
        )

    # Build a standardized detector list from submitted modality records
    detector_list = []
    modality_sources = {}

    MODALITY_ORDER = [("image", image_rec), ("audio", audio_rec), ("video", video_rec)]
    for modality, rec in MODALITY_ORDER:
        if not rec:
            continue
        # Normalize confidence: accept 0-1 float or 0-100 percentage
        raw_conf = float(rec.get("confidence", 0.5))
        if raw_conf > 1.0:
            raw_conf = raw_conf / 100.0
        raw_conf = max(0.0, min(1.0, raw_conf))

        classification = str(rec.get("classification", "INCONCLUSIVE")).upper()
        if classification not in {"FAKE", "REAL", "INCONCLUSIVE"}:
            classification = "INCONCLUSIVE"

        detector_entry = {
            "detector_name": rec.get("detector_name") or rec.get("model") or f"{modality.capitalize()} Detector",
            "model_name": rec.get("model_name") or rec.get("model") or "Unknown",
            "model_version": rec.get("model_version", "1.0.0"),
            "framework": rec.get("framework", "Unknown"),
            "method": rec.get("method", "machine_learning"),
            "is_ai_model": rec.get("is_ai_model", True),
            "fallback_used": rec.get("fallback_used", False),
            "classification": classification,
            "confidence": raw_conf,
            "processing_time_ms": rec.get("processing_time_ms", 0),
            "metadata": {
                "modality": modality,
                "filename": rec.get("filename", "unknown"),
                "sha256": rec.get("sha256"),
                "timestamp": rec.get("timestamp"),
            }
        }
        detector_list.append(detector_entry)
        modality_sources[modality] = {
            "detector_name": detector_entry["detector_name"],
            "classification": classification,
            "confidence": raw_conf,
            "is_ai_model": detector_entry["is_ai_model"],
            "fallback_used": detector_entry["fallback_used"],
            "method": detector_entry["method"],
            "filename": rec.get("filename", "unknown"),
        }

    # Run authoritative backend fusion
    fusion = fuse_detector_results("cross_modal", detector_list)

    # Collect any heuristic fallback warnings
    fallback_warnings = []
    for modality, src in modality_sources.items():
        if src.get("fallback_used"):
            fallback_warnings.append(
                f"⚠ {modality.capitalize()} analysis used a heuristic fallback. "
                f"Results should not be interpreted as equivalent to trained model inference."
            )

    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "status": "success",
        "analysis_id": f"CROSS-MODAL-{int(datetime.now().timestamp())}",
        "timestamp": now_iso,
        "assessment": fusion["primary_classification"],
        "assessment_confidence": fusion["primary_confidence"],
        "detector_agreement": fusion["detector_agreement"],
        "disagreement_warning": fusion["disagreement_warning"],
        "fallback_warnings": fallback_warnings,
        "modality_sources": modality_sources,
        "detectors": fusion["detectors"],
        "forensic_indicators": fusion.get("forensic_indicators", []),
        "disclaimer": fusion["disclaimer"],
        "fusion_method": "authoritative_backend_forensic_fusion",
        "note": (
            "This verdict is produced by the authoritative ADIS backend forensic_fusion.py. "
            "Detectors that strongly disagree will produce an INCONCLUSIVE result. "
            "All outputs are probabilistic and do not constitute legal proof."
        )
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)

