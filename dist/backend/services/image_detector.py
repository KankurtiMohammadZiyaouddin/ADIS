"""
ADIS Image Forensic Detector
Analyzes uploaded images for AI-generated / deepfake / manipulated content.
Uses PyTorch/Hugging Face model with robust spatial feature extraction fallback.
"""

from pathlib import Path
import hashlib
import time
import uuid
from PIL import Image, ImageStat, ImageFilter


_pipeline = None
_MODEL_ID = "dima806/deepfake_vs_real_image_detection"
_MODEL_LOAD_FAILED = False


def _get_pipeline():
    global _pipeline, _MODEL_LOAD_FAILED
    if _MODEL_LOAD_FAILED:
        return None
    if _pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline
            print(f"[ImageDetector] Attempting to load HuggingFace model {_MODEL_ID}...")
            _pipeline = hf_pipeline(
                "image-classification",
                model=_MODEL_ID,
                device=-1,          # CPU inference
                top_k=None,         # return all class scores
            )
            print("[ImageDetector] HuggingFace model loaded successfully.")
        except Exception as err:
            print(f"[ImageDetector] Network/HF download unavailable ({err}). Using spatial feature extraction.")
            _MODEL_LOAD_FAILED = True
            _pipeline = None
    return _pipeline


def compute_sha256(file_path: str) -> str:
    """Compute raw byte SHA-256 hash of evidence file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def analyze_image(image_path: str) -> dict:
    """
    Run deepfake/AI-generation detection on an image file.

    Pipeline:
      1. Calculate SHA-256 signature and file size.
      2. Verify & load image with PIL to extract width, height, format, mode.
      3. Execute model inference or spatial/frequency analysis.
      4. Return structured forensic dictionary.
    """
    start_time = time.time()

    # 1. SHA-256 & File Size
    sha256_hash = compute_sha256(image_path)
    file_size_bytes = Path(image_path).stat().st_size

    # 2. PIL Image Validation & Feature Extraction
    try:
        with Image.open(image_path) as img:
            img.verify()
        with Image.open(image_path) as img:
            width, height = img.size
            img_format = img.format or "UNKNOWN"
            mode = img.mode
            stat = ImageStat.Stat(img)
            mean_intensity = round(float(sum(stat.mean) / len(stat.mean)), 2) if stat.mean else 0.0
            pil_image = img.convert("RGB")

            # High-pass filter edge analysis for noise/compression artifacts
            edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_variance = float(edge_stat.var[0]) if edge_stat.var else 0.0
    except Exception as err:
        raise ValueError(f"Failed to decode image file. File may be corrupt or unreadable: {err}")

    # 3. Model Inference or Spatial Analysis Heuristic
    pipe = _get_pipeline()
    prob_fake = 0.5
    prob_real = 0.5
    model_name = _MODEL_ID

    if pipe:
        try:
            predictions = pipe(pil_image)
            for pred in predictions:
                label = pred["label"].upper()
                score = float(pred["score"])
                if "FAKE" in label or "SYNTHETIC" in label or "LABEL_0" in label:
                    prob_fake = score
                elif "REAL" in label or "AUTHENTIC" in label or "LABEL_1" in label:
                    prob_real = score
        except Exception as pred_err:
            print(f"[ImageDetector] Pipeline inference exception: {pred_err}")
            pipe = None

    if not pipe:
        # Spatial Feature Extraction & High-Pass Frequency Score
        model_name = "ADIS-Spatial-Detector (Local Feature Extraction)"
        # High edge variance often indicates artificial sharp synthesis or noise artifacts
        norm_var = min(1.0, max(0.05, edge_variance / 2000.0))
        prob_fake = round(0.40 + (norm_var * 0.45), 4)
        prob_real = round(1.0 - prob_fake, 4)

    # Verdict determination
    if prob_fake >= 0.55:
        classification = "FAKE"
        confidence = prob_fake
    elif prob_real >= 0.55:
        classification = "REAL"
        confidence = prob_real
    else:
        classification = "INCONCLUSIVE"
        confidence = max(prob_fake, prob_real)

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
        "edge_variance": round(edge_variance, 2),
        "classification": classification,
        "confidence": round(confidence, 4),
        "prob_fake": round(prob_fake, 4),
        "prob_real": round(prob_real, 4),
        "model": model_name,
        "model_version": "1.0.0",
        "processing_time_ms": processing_time_ms
    }
