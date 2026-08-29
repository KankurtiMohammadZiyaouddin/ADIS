"""
ADIS Video Forensic Detector Orchestrator
Orchestrates frame-sampled video sub-detectors and passes outputs to the forensic fusion assessment layer.
"""

from pathlib import Path
import hashlib
import time
import uuid

from services.video_detectors.frame_detector import FrameVideoDetector
from services.forensic_fusion import fuse_detector_results


def compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def analyze_video(video_path: str) -> dict:
    """
    Run modular video sub-detectors and return fused forensic assessment.
    """
    start_time = time.time()

    # 1. SHA-256 & File Size
    sha256_hash = compute_sha256(video_path)
    file_size_bytes = Path(video_path).stat().st_size

    # 2. Sub-detector execution
    frame_detector = FrameVideoDetector(sample_frames=15)
    frame_res = frame_detector.detect(video_path)

    detector_list = [frame_res]

    # 3. Forensic Fusion
    fusion = fuse_detector_results("video", detector_list)

    meta = frame_res.get("metadata", {})
    processing_time_ms = int((time.time() - start_time) * 1000)
    analysis_id = f"VID-ANALYSIS-{uuid.uuid4().hex[:8].upper()}"

    return {
        "analysis_id": analysis_id,
        "media_type": "video",
        "file_size_bytes": file_size_bytes,
        "sha256": sha256_hash,
        "duration_seconds": meta.get("duration_seconds", 0.0),
        "resolution": meta.get("resolution", "N/A"),
        "fps": meta.get("fps", 0.0),
        "frame_count": meta.get("frames_analyzed", 0),
        "frames_fake": meta.get("frames_fake", 0),
        "frames_real": meta.get("frames_real", 0),
        "classification": fusion["primary_classification"],
        "confidence": fusion["primary_confidence"],
        "detector_agreement": fusion["detector_agreement"],
        "disagreement_warning": fusion["disagreement_warning"],
        "detectors": fusion["detectors"],
        "model": frame_res["model_name"],
        "model_version": frame_res["model_version"],
        "processing_time_ms": processing_time_ms,
        "frame_results": meta.get("frame_results", []),
        "aggregation_method": meta.get("aggregation_method", "Frame-Sampled Majority Vote"),
        "is_true_temporal_model": meta.get("is_true_temporal_model", False),
        "limitations_note": meta.get("limitations_note", "Frame-sampled spatial detector."),
        "temporal_analysis": {
            "methodology": meta.get("aggregation_method"),
            "temporal_flicker_score": meta.get("temporal_flicker_score", 0.0),
            "is_true_temporal_model": False
        },
        "disclaimer": fusion["disclaimer"]
    }
