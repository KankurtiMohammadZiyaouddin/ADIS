"""
ADIS EfficientNet Image Deepfake Sub-Detector
Wraps dima806/deepfake_vs_real_image_detection under the BaseDetector interface.

FALLBACK TRANSPARENCY:
When the HuggingFace model is unavailable, a spatial edge-variance heuristic is used.
The fallback is disclosed explicitly via: method="heuristic", is_ai_model=False, fallback_used=True
Results from the heuristic path must NEVER be presented as equivalent to model inference.
"""

from pathlib import Path
import sys
from PIL import Image, ImageStat, ImageFilter

SERVICES_DIR = Path(__file__).resolve().parents[1]
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from base_detector import BaseDetector

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
            print(f"[EfficientNetImageDetector] Loading model {_MODEL_ID}...")
            _pipeline = hf_pipeline(
                "image-classification",
                model=_MODEL_ID,
                device=-1,          # CPU inference
                top_k=None,
            )
        except Exception as err:
            print(f"[EfficientNetImageDetector] Model unavailable ({err}). Heuristic fallback will be used and disclosed.")
            _MODEL_LOAD_FAILED = True
            _pipeline = None
    return _pipeline


class EfficientNetImageDetector(BaseDetector):
    """
    Sub-detector wrapping PyTorch EfficientNet image classifier.
    Falls back to a spatial edge-variance heuristic if the model cannot be loaded.
    The fallback is explicitly disclosed in the result schema.
    """

    def __init__(self):
        super().__init__(
            detector_name="EfficientNet Deepfake Detector",
            model_name=_MODEL_ID,
            framework="PyTorch / HuggingFace Transformers",
            model_version="1.0.0",
            method="machine_learning",
            is_ai_model=True,
        )

    def run_detection(self, media_path: str) -> tuple:
        with Image.open(media_path) as img:
            pil_image = img.convert("RGB")
            edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_variance = float(edge_stat.var[0]) if edge_stat.var else 0.0

        pipe = _get_pipeline()
        prob_fake = 0.5
        prob_real = 0.5
        using_fallback = False

        if pipe:
            try:
                preds = pipe(pil_image)
                for p in preds:
                    lbl = p["label"].upper()
                    s = float(p["score"])
                    if "FAKE" in lbl or "SYNTHETIC" in lbl or "LABEL_0" in lbl:
                        prob_fake = s
                    elif "REAL" in lbl or "AUTHENTIC" in lbl or "LABEL_1" in lbl:
                        prob_real = s
            except Exception as infer_err:
                print(f"[EfficientNetImageDetector] Inference failed: {infer_err} — heuristic fallback active.")
                using_fallback = True

        if not pipe or using_fallback:
            # Heuristic: spatial edge-variance proxy (NOT a trained model)
            norm_var = min(1.0, max(0.05, edge_variance / 2000.0))
            prob_fake = round(0.40 + (norm_var * 0.45), 4)
            prob_real = round(1.0 - prob_fake, 4)

        if prob_fake >= 0.55:
            classification = "FAKE"
            confidence = prob_fake
        elif prob_real >= 0.55:
            classification = "REAL"
            confidence = prob_real
        else:
            classification = "INCONCLUSIVE"
            confidence = max(prob_fake, prob_real)

        is_heuristic = (not pipe or using_fallback)

        metadata = {
            "prob_fake": round(prob_fake, 4),
            "prob_real": round(prob_real, 4),
            "edge_variance": round(edge_variance, 2),
            "inference_backend": "Hugging Face Transformers (CPU)" if not is_heuristic else "Spatial Edge-Variance Heuristic (AI model unavailable)",
            "heuristic_warning": (
                "⚠ Heuristic analysis was used because the trained AI model was unavailable. "
                "This result should not be interpreted as equivalent to model inference."
            ) if is_heuristic else None,
            # Signal to BaseDetector.detect() that fallback was used
            "_fallback_used": is_heuristic,
        }

        return classification, confidence, metadata
