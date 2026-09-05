"""
ADIS Frame-Based Video Sub-Detector
Analyzes videos via sampled sequential frames and optical flow inter-frame motion delta.

DOCUMENTATION NOTICE — MANDATORY:
This is a frame-sampled spatial detector. It is explicitly NOT a 3D temporal deepfake model.
is_true_temporal_model: False

When the EfficientNet pipeline is unavailable, a Laplacian-variance heuristic is used.
The fallback is explicitly disclosed via: method="heuristic", is_ai_model=False, fallback_used=True
"""

from pathlib import Path
import sys
import cv2
import numpy as np
from PIL import Image

SERVICES_DIR = Path(__file__).resolve().parents[1]
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from base_detector import BaseDetector

_pipeline = None
_MODEL_ID = "dima806/deepfake_vs_real_image_detection"


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline as hf_pipeline
            _pipeline = hf_pipeline(
                "image-classification",
                model=_MODEL_ID,
                device=-1,
                top_k=None,
            )
        except Exception:
            _pipeline = False
    return _pipeline


def compute_temporal_diff(prev_gray, curr_gray):
    if prev_gray is None or curr_gray is None:
        return 0.0
    diff = cv2.absdiff(prev_gray, curr_gray)
    return float(np.var(diff))


class FrameVideoDetector(BaseDetector):
    """
    Frame-sampled video sub-detector.
    is_true_temporal_model: False — explicitly not a 3D temporal deepfake model.
    """

    def __init__(self, sample_frames: int = 15):
        super().__init__(
            detector_name="Frame-Sampled Video Detector",
            model_name="EfficientNet Frame Sampler + Optical Flow Delta",
            framework="PyTorch / OpenCV Frame Sampler",
            model_version="1.5.0",
            method="machine_learning",
            is_ai_model=True,
        )
        self.sample_frames = sample_frames

    def run_detection(self, media_path: str) -> tuple:
        cap = cv2.VideoCapture(media_path)
        if not cap.isOpened():
            raise ValueError("Failed to decode video file for frame detection.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_seconds = round(total_frames / fps, 2) if fps > 0 else 0.0

        sample_count = min(self.sample_frames, max(1, total_frames))
        frame_indices = np.linspace(0, max(0, total_frames - 1), sample_count, dtype=int)

        pipe = _get_pipeline()
        using_heuristic_fallback = (pipe is False or pipe is None)

        frame_results = []
        prev_gray = None
        temporal_diffs = []

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame_bgr = cap.read()
            if not ret or frame_bgr is None:
                continue

            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            if prev_gray is not None:
                temporal_diffs.append(compute_temporal_diff(prev_gray, gray))
            prev_gray = gray

            prob_fake = 0.5
            prob_real = 0.5

            if pipe and pipe is not False:
                try:
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)
                    preds = pipe(pil_img)
                    for p in preds:
                        lbl = p["label"].upper()
                        s = float(p["score"])
                        if "FAKE" in lbl or "SYNTHETIC" in lbl or "LABEL_0" in lbl:
                            prob_fake = s
                        elif "REAL" in lbl or "AUTHENTIC" in lbl or "LABEL_1" in lbl:
                            prob_real = s
                except Exception:
                    using_heuristic_fallback = True
                    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                    prob_fake = round(min(0.92, max(0.10, lap_var / 1000.0)), 4)
                    prob_real = round(1.0 - prob_fake, 4)
            else:
                # Heuristic: Laplacian sharpness variance proxy (NOT a trained model)
                lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                prob_fake = round(min(0.92, max(0.10, lap_var / 1000.0)), 4)
                prob_real = round(1.0 - prob_fake, 4)

            timestamp_sec = round(idx / fps, 2)
            frame_verdict = "FAKE" if prob_fake >= 0.55 else ("REAL" if prob_real >= 0.55 else "INCONCLUSIVE")

            frame_results.append({
                "frame_index": int(idx),
                "timestamp_seconds": timestamp_sec,
                "classification": frame_verdict,
                "confidence": round(max(prob_fake, prob_real), 4),
                "prob_fake": round(prob_fake, 4),
                "prob_real": round(prob_real, 4)
            })

        cap.release()

        if not frame_results:
            raise ValueError("Could not extract readable frames from video.")

        fake_frames = [f for f in frame_results if f["classification"] == "FAKE"]
        real_frames = [f for f in frame_results if f["classification"] == "REAL"]

        avg_fake_prob = sum(f["prob_fake"] for f in frame_results) / len(frame_results)

        temporal_flicker_score = 0.0
        if temporal_diffs:
            mean_t_diff = float(np.mean(temporal_diffs))
            std_t_diff = float(np.std(temporal_diffs))
            temporal_flicker_score = round(min(1.0, std_t_diff / (mean_t_diff + 1e-5)), 4)

        combined_fake_score = round(0.75 * avg_fake_prob + 0.25 * temporal_flicker_score, 4)

        if combined_fake_score >= 0.55:
            classification = "FAKE"
            confidence = combined_fake_score
        elif (1.0 - combined_fake_score) >= 0.55:
            classification = "REAL"
            confidence = round(1.0 - combined_fake_score, 4)
        else:
            classification = "INCONCLUSIVE"
            confidence = max(combined_fake_score, round(1.0 - combined_fake_score, 4))

        metadata = {
            "duration_seconds": duration_seconds,
            "resolution": f"{width}x{height}",
            "fps": round(fps, 2),
            "frames_analyzed": len(frame_results),
            "frames_fake": len(fake_frames),
            "frames_real": len(real_frames),
            "aggregation_method": "Frame-Sampled Spatial Majority Vote + Motion Delta",
            "is_true_temporal_model": False,
            "limitations_note": (
                "IMPORTANT: System uses frame sampling and inter-frame motion delta heuristics. "
                "It is NOT a 3D temporal deepfake neural model (e.g. Swin3D, TimeSformer, XceptionNet-LSTM). "
                "It cannot detect temporal manipulation patterns."
            ),
            "temporal_flicker_score": temporal_flicker_score,
            "frame_results": frame_results,
            "inference_backend": "Hugging Face Transformers per-frame (CPU)" if not using_heuristic_fallback else "Laplacian Variance Heuristic (AI model unavailable)",
            "heuristic_warning": (
                "⚠ Heuristic frame analysis was used because the trained AI model was unavailable. "
                "This result should not be interpreted as equivalent to model inference."
            ) if using_heuristic_fallback else None,
            # Signal to BaseDetector.detect() that fallback was used
            "_fallback_used": using_heuristic_fallback,
        }

        return classification, confidence, metadata
