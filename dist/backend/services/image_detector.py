"""
ADIS Image Forensic Detector Orchestrator
Orchestrates image sub-detectors (EfficientNet) and non-definitive forensic compression indicators (ELA).
Applies forensic fusion assessment to generate primary verdict and indicators breakdown.
"""

from pathlib import Path
import hashlib
import time
import uuid
from PIL import Image, ImageStat

from services.image_detectors.efficientnet_detector import EfficientNetImageDetector
from services.image_detectors.ela_analyzer import ELAAnalyzer
from services.forensic_fusion import fuse_detector_results


def compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def analyze_image(image_path: str) -> dict:
    """
    Run modular image sub-detectors and ELA forensic analyzer.
    """
    start_time = time.time()

    # 1. SHA-256 & File Size
    sha256_hash = compute_sha256(image_path)
    file_size_bytes = Path(image_path).stat().st_size

    # 2. PIL Metadata Verification
    try:
        with Image.open(image_path) as img:
            img.verify()
        with Image.open(image_path) as img:
            width, height = img.size
            img_format = img.format or "UNKNOWN"
            mode = img.mode
            stat = ImageStat.Stat(img)
            mean_intensity = round(float(sum(stat.mean) / len(stat.mean)), 2) if stat.mean else 0.0
    except Exception as err:
        raise ValueError(f"Failed to decode image file. File may be corrupt or unreadable: {err}")

    # 3. Sub-Detectors & Forensic Indicators
    effnet = EfficientNetImageDetector()
    effnet_res = effnet.detect(image_path)

    ela = ELAAnalyzer(quality=90)
    ela_res = ela.analyze(image_path)

    detector_list = [effnet_res]
    forensic_indicators = [ela_res]

    # 4. Forensic Fusion
    fusion = fuse_detector_results("image", detector_list, forensic_indicators=forensic_indicators)

    processing_time_ms = int((time.time() - start_time) * 1000)
    analysis_id = f"IMG-ANALYSIS-{uuid.uuid4().hex[:8].upper()}"

    return {
        "analysis_id": analysis_id,
        "media_type": "image",
        "file_size_bytes": file_size_bytes,
        "sha256": sha256_hash,
        "resolution": f"{width}x{height}",
        "width": width,
        "height": height,
        "format": img_format,
        "color_mode": mode,
        "mean_intensity": mean_intensity,
        "classification": fusion["primary_classification"],
        "confidence": fusion["primary_confidence"],
        "detector_agreement": fusion["detector_agreement"],
        "disagreement_warning": fusion["disagreement_warning"],
        "detectors": fusion["detectors"],
        "forensic_indicators": fusion["forensic_indicators"],
        "prob_fake": effnet_res["metadata"].get("prob_fake", 0.5),
        "prob_real": effnet_res["metadata"].get("prob_real", 0.5),
        "edge_variance": effnet_res["metadata"].get("edge_variance", 0.0),
        "model": effnet_res["model_name"],
        "model_version": effnet_res["model_version"],
        "processing_time_ms": processing_time_ms,
        "disclaimer": fusion["disclaimer"]
    }
