"""
ADIS Error Level Analysis (ELA) Sub-Module
Performs Error Level Analysis to detect JPEG re-compression discrepancies and digital editing boundaries.

IMPORTANT:
ELA is a separate forensic indicator for digital image compression anomalies.
It is explicitly NOT definitive proof of AI generation or deepfake synthesis.
"""

from pathlib import Path
import tempfile
import io
import numpy as np
from PIL import Image, ImageChops, ImageEnhance


class ELAAnalyzer:
    """
    Error Level Analysis (ELA) forensic compression indicator module.
    """

    def __init__(self, quality: int = 90, scale_factor: float = 15.0):
        self.quality = quality
        self.scale_factor = scale_factor

    def analyze(self, image_path: str) -> dict:
        """
        Perform ELA analysis on an image file.

        Returns:
          {
            "indicator_name": "Error Level Analysis (ELA)",
            "ela_anomaly_score": float (0.0 to 1.0),
            "compression_variance": float,
            "compression_anomaly": "LOW" | "MODERATE" | "HIGH",
            "is_definitive_ai_proof": False,
            "description": str
          }
        """
        try:
            with Image.open(image_path) as original:
                original_rgb = original.convert("RGB")

                # Resave image into memory buffer at 90% quality
                buffer = io.BytesIO()
                original_rgb.save(buffer, format="JPEG", quality=self.quality)
                buffer.seek(0)
                resaved_rgb = Image.open(buffer).convert("RGB")

                # Compute difference map
                diff = ImageChops.difference(original_rgb, resaved_rgb)
                
                # Enhance difference image for visual inspection metrics
                extrema = diff.getextrema()
                max_diff = max([ex[1] for ex in extrema]) if extrema else 1
                scale = 255.0 / (max_diff + 1e-5)
                
                enhanced_diff = ImageEnhance.Brightness(diff).enhance(scale)
                
                diff_np = np.array(diff, dtype=np.float32)
                variance = float(np.var(diff_np))
                mean_diff = float(np.mean(diff_np))

                # Normalize ELA score
                norm_score = round(min(1.0, max(0.0, variance / 500.0)), 4)

                if norm_score >= 0.65:
                    anomaly_level = "HIGH"
                elif norm_score >= 0.35:
                    anomaly_level = "MODERATE"
                else:
                    anomaly_level = "LOW"

                return {
                    "indicator_name": "Error Level Analysis (ELA)",
                    "ela_anomaly_score": norm_score,
                    "compression_variance": round(variance, 2),
                    "mean_error_delta": round(mean_diff, 2),
                    "compression_anomaly": anomaly_level,
                    "is_definitive_ai_proof": False,
                    "notice": "ELA measures JPEG compression error level variance. Editing anomalies or multiple saves can trigger elevated ELA scores without AI generation."
                }

        except Exception as err:
            return {
                "indicator_name": "Error Level Analysis (ELA)",
                "ela_anomaly_score": 0.0,
                "compression_variance": 0.0,
                "compression_anomaly": "UNAVAILABLE",
                "is_definitive_ai_proof": False,
                "error": str(err)
            }
