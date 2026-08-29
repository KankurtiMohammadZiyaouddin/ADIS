"""
ADIS EfficientNet Image Deepfake Sub-Detector
Wraps dima806/deepfake_vs_real_image_detection under the BaseDetector modular interface.
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
                top_k=None,         # return all class scores
            )
        except Exception as err:
            print(f"[EfficientNetImageDetector] Hugging Face model load unavailable ({err}). Using local fallback.")
            _MODEL_LOAD_FAILED = True
            _pipeline = None
    return _pipeline


class EfficientNetImageDetector(BaseDetector):
    """
    Sub-detector wrapping PyTorch EfficientNet image classifier.
    """

    def __init__(self):
        super().__init__(
            detector_name="EfficientNet Deepfake Detector",
            model_name=_MODEL_ID,
            model_version="1.0.0"
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
            except Exception:
                using_fallback = True

        if not pipe or using_fallback:
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

        metadata = {
            "prob_fake": round(prob_fake, 4),
            "prob_real": round(prob_real, 4),
            "edge_variance": round(edge_variance, 2),
            "inference_backend": "Hugging Face Transformers (CPU)" if (pipe and not using_fallback) else "Spatial Feature Heuristic"
        }

        return classification, confidence, metadata
