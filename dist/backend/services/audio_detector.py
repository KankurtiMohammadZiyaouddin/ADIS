"""
ADIS Audio Forensic Detector Orchestrator
Orchestrates audio sub-detectors (YAMNet) and passes outputs to the forensic fusion assessment layer.
"""

from pathlib import Path
import hashlib
import time
import uuid
import soundfile as sf

from services.audio_detectors.yamnet_detector import YamnetAudioDetector
from services.forensic_fusion import fuse_detector_results


def analyze_audio(audio_path: str) -> dict:
    """
    Run modular audio sub-detectors and return fused forensic assessment.
    """
    start_time = time.time()

    # 1. Evidence hashing & metadata
    sha256_hash = hashlib.sha256()
    with open(audio_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    sha256 = sha256_hash.hexdigest()

    file_size_bytes = Path(audio_path).stat().st_size

    try:
        info = sf.info(audio_path)
        duration_seconds = info.duration
        sample_rate = info.samplerate
        channels = info.channels
    except Exception:
        duration_seconds = 0.0
        sample_rate = 16000
        channels = 1

    # 2. Sub-detectors execution
    yamnet = YamnetAudioDetector()
    yamnet_res = yamnet.detect(audio_path)

    detector_list = [yamnet_res]

    # 3. Forensic Fusion
    fusion = fuse_detector_results("audio", detector_list)

    processing_time_ms = int((time.time() - start_time) * 1000)
    analysis_id = f"AUD-ANALYSIS-{uuid.uuid4().hex[:8].upper()}"

    return {
        "analysis_id": analysis_id,
        "media_type": "audio",
        "file_size_bytes": file_size_bytes,
        "sha256": sha256,
        "duration_seconds": round(duration_seconds, 2),
        "sample_rate": sample_rate,
        "channels": channels,
        "classification": fusion["primary_classification"],
        "confidence": fusion["primary_confidence"],
        "detector_agreement": fusion["detector_agreement"],
        "disagreement_warning": fusion["disagreement_warning"],
        "detectors": fusion["detectors"],
        "model": "YAMNet Audio Detector",
        "model_version": "1.0.0",
        "processing_time_ms": processing_time_ms,
        "disclaimer": fusion["disclaimer"]
    }
