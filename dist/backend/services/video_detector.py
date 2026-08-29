"""
ADIS Video Forensic Detector
Uses dima806/deepfake_vs_real_image_detection (EfficientNet) from Hugging Face.
Analyzes video frame-by-frame for AI-generated / deepfake content.
Works for both face-swap deepfakes AND fully synthetic AI video (Runway, Sora, etc.)
"""

from pathlib import Path
import hashlib
import time
import uuid
import sys

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Lazy-load the HuggingFace pipeline so the model is only downloaded once
# and reused for all subsequent requests.
# ---------------------------------------------------------------------------
_pipeline = None
_MODEL_ID = "dima806/deepfake_vs_real_image_detection"


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline as hf_pipeline
        print(f"[VideoDetector] Loading model {_MODEL_ID} (first-run download may take a minute)...")
        _pipeline = hf_pipeline(
            "image-classification",
            model=_MODEL_ID,
            device=-1,          # CPU inference
            top_k=None,         # return all class scores
        )
        print("[VideoDetector] Model loaded and ready.")
    return _pipeline


# ---------------------------------------------------------------------------
# Core analysis function
# ---------------------------------------------------------------------------

def analyze_video(video_path: str) -> dict:
    """
    Run deepfake/AI-generation detection on a video file.

    Pipeline:
      1. Open with OpenCV, extract duration + resolution metadata
      2. Sample up to 15 evenly-spaced frames across the video
      3. Run the HuggingFace image classifier on each frame
      4. Aggregate frame-level results → single FAKE / REAL verdict + confidence

    Returns a structured forensic dict that matches the FastAPI response schema.
    """

    # ------------------------------------------------------------------
    # 1. SHA-256 hash & file size
    # ------------------------------------------------------------------
    sha256_hash = hashlib.sha256()
    file_size_bytes = Path(video_path).stat().st_size
    with open(video_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256_hash.update(chunk)
    sha256 = sha256_hash.hexdigest()

    # ------------------------------------------------------------------
    # 2. Open video with OpenCV
    # ------------------------------------------------------------------
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Unable to open video file. It may be corrupt or use an unsupported codec.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_s   = total_frames / fps if fps > 0 else 0.0
    resolution   = f"{width}x{height}"

    # ------------------------------------------------------------------
    # 3. Sample up to 15 evenly-spaced frames (skip first/last 2% to
    #    avoid black fade-in/out frames)
    # ------------------------------------------------------------------
    MAX_FRAMES = 15
    margin      = max(1, int(total_frames * 0.02))
    usable_start = margin
    usable_end   = max(usable_start + 1, total_frames - margin)

    if usable_end - usable_start < MAX_FRAMES:
        sample_indices = list(range(usable_start, usable_end))
    else:
        step = (usable_end - usable_start) / MAX_FRAMES
        sample_indices = [int(usable_start + i * step) for i in range(MAX_FRAMES)]

    frames_rgb = []
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame_bgr = cap.read()
        if ret and frame_bgr is not None:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            frames_rgb.append((idx, frame_rgb))
    cap.release()

    if not frames_rgb:
        raise ValueError("Could not extract any frames from the video. The file may be corrupt.")

    # ------------------------------------------------------------------
    # 4. Run the classifier on each frame
    # ------------------------------------------------------------------
    pipe = _get_pipeline()
    start_time = time.perf_counter()

    frame_results = []
    for frame_idx, frame_rgb in frames_rgb:
        timestamp_s = round(frame_idx / fps, 2)
        # HuggingFace pipeline accepts numpy arrays (H, W, 3) uint8
        preds = pipe(frame_rgb)  # returns list of {label, score}

        # Normalize label names — model uses "Fake" / "Real" labels
        score_fake = 0.0
        score_real = 0.0
        for p in preds:
            lbl = p["label"].strip().lower()
            if "fake" in lbl or "ai" in lbl or "deepfake" in lbl or "generated" in lbl:
                score_fake = max(score_fake, p["score"])
            elif "real" in lbl or "authentic" in lbl or "genuine" in lbl:
                score_real = max(score_real, p["score"])

        # If both are 0 (unexpected labels), default to max score as fake
        if score_fake == 0.0 and score_real == 0.0:
            score_fake = max(p["score"] for p in preds)
            score_real = 1.0 - score_fake

        verdict = "FAKE" if score_fake > score_real else "REAL"
        confidence = score_fake if verdict == "FAKE" else score_real

        frame_results.append({
            "frame_index": frame_idx,
            "timestamp_s": timestamp_s,
            "verdict": verdict,
            "confidence": round(confidence, 4),
            "score_fake": round(score_fake, 4),
            "score_real": round(score_real, 4),
        })

    end_time = time.perf_counter()
    processing_time_ms = int((end_time - start_time) * 1000)

    # ------------------------------------------------------------------
    # 5. Aggregate: weighted vote (middle frames weighted 1.5×)
    # ------------------------------------------------------------------
    n = len(frame_results)
    total_weight = 0.0
    weighted_fake_score = 0.0

    for i, fr in enumerate(frame_results):
        # Frames in the middle 40% of the video get 1.5× weight
        rel_pos = i / max(n - 1, 1)
        weight = 1.5 if 0.3 <= rel_pos <= 0.7 else 1.0
        weighted_fake_score += fr["score_fake"] * weight
        total_weight += weight

    avg_fake_score = weighted_fake_score / total_weight
    avg_real_score = 1.0 - avg_fake_score

    final_verdict = "FAKE" if avg_fake_score > 0.5 else "REAL"
    final_confidence = avg_fake_score if final_verdict == "FAKE" else avg_real_score

    frames_fake = sum(1 for fr in frame_results if fr["verdict"] == "FAKE")
    frames_real = n - frames_fake

    return {
        "sha256":              sha256,
        "file_size_bytes":     file_size_bytes,
        "duration_seconds":    round(duration_s, 2),
        "resolution":          resolution,
        "fps":                 round(fps, 2),
        "frame_count":         n,
        "classification":      final_verdict,
        "confidence":          round(final_confidence, 4),
        "frames_fake":         frames_fake,
        "frames_real":         frames_real,
        "frame_results":       frame_results,
        "processing_time_ms":  processing_time_ms,
        "analysis_id":         str(uuid.uuid4()),
        "model":               "EfficientNet-DeepfakeDetector",
        "model_version":       _MODEL_ID,
    }
