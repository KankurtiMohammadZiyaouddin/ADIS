from pathlib import Path
import shutil
import tempfile

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.audio_detector import analyze_audio


app = FastAPI(
    title="ADIS Forensic Suite API",
    version="1.0.0",
    description="Audio forensic analysis API for ADIS",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "ADIS backend is running",
        "service": "ADIS Forensic Suite API",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
    }


ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit


@app.post("/api/audio/analyze")
async def audio_analyze(audio_file: UploadFile = File(...)):
    # 1. Validate filename
    if not audio_file.filename:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "MISSING_FILENAME",
                    "message": "No filename was provided in the upload."
                }
            }
        )

    # 2. Validate file extension
    suffix = Path(audio_file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_AUDIO_FORMAT",
                    "message": f"Unsupported file extension: '{suffix}'. Supported formats are: WAV, MP3, M4A, FLAC, OGG."
                }
            }
        )

    # 3. Validate file size
    try:
        audio_file.file.seek(0, 2)
        file_size = audio_file.file.tell()
        audio_file.file.seek(0)
    except Exception as exc:
        print(f"Failed to query file size: {exc}")
        file_size = 0

    if file_size > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=413,
            content={
                "success": False,
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds the 10MB limit. Uploaded size: {file_size} bytes."
                }
            }
        )

    temp_path = None

    try:
        # 4. Save to a safe temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            shutil.copyfileobj(audio_file.file, temp_file)

        # 5. Run audio forensic analysis
        result = analyze_audio(str(temp_path))

        # 6. Package in official Forensic Response Format
        response_data = {
            "success": True,
            "evidence": {
                "filename": audio_file.filename,
                "file_size_bytes": result["file_size_bytes"],
                "sha256": result["sha256"],
                "duration_seconds": result["duration_seconds"],
                "sample_rate": result["sample_rate"],
                "channels": result["channels"]
            },
            "analysis": {
                "classification": result["classification"],
                "confidence": result["confidence"],
                "model": "Deepfake-YamNet",
                "model_version": "1.0.0",
                "processing_time_ms": result["processing_time_ms"]
            },
            "forensic": {
                "analysis_id": result["analysis_id"],
                "evidence_integrity": "SHA-256 calculated",
                "temporary_file_cleanup": True
            }
        }

        return response_data

    except ValueError as val_err:
        print(f"Validation error during audio processing: {val_err}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "UNPROCESSABLE_AUDIO",
                    "message": str(val_err)
                }
            }
        )
    except Exception as exc:
        print(f"Unexpected server error during audio analysis: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred during audio forensic analysis."
                }
            }
        )

    finally:
        # 7. Clean up the temporary file
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as clean_exc:
                print(f"Failed to clean up temporary file {temp_path}: {clean_exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
    )
