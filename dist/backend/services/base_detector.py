"""
ADIS Base Detector Interface
Abstract base class for all forensic sub-detectors across Image, Audio, and Video modalities.

Standardized schema MUST include:
  detector_name, model_name, model_version, framework,
  method, is_ai_model, fallback_used,
  classification, confidence, processing_time_ms, metadata
"""

from abc import ABC, abstractmethod
import time


class BaseDetector(ABC):
    """
    Abstract Base Class for all forensic detectors.
    """

    def __init__(
        self,
        detector_name: str,
        model_name: str,
        framework: str = "Unknown",
        model_version: str = "1.0.0",
        method: str = "machine_learning",
        is_ai_model: bool = True,
    ):
        self.detector_name = detector_name
        self.model_name = model_name
        self.framework = framework
        self.model_version = model_version
        self.method = method
        self.is_ai_model = is_ai_model

    @abstractmethod
    def run_detection(self, media_path: str) -> tuple:
        """
        Execute sub-detector logic on the media file.
        Returns: (classification: str, confidence: float, metadata: dict)
        The metadata dict may optionally include:
          "fallback_used": bool
          "inference_backend": str
        """
        pass

    def detect(self, media_path: str) -> dict:
        """
        Public execution wrapper measuring processing time and enforcing the standardized schema.
        """
        start_time = time.perf_counter()
        fallback_used = False
        try:
            classification, confidence, metadata = self.run_detection(media_path)
            fallback_used = bool(metadata.pop("_fallback_used", False))
        except Exception as err:
            classification = "INCONCLUSIVE"
            confidence = 0.0
            metadata = {"error": str(err), "status": "failed"}
            fallback_used = True

        end_time = time.perf_counter()
        processing_time_ms = int((end_time - start_time) * 1000)

        # Enforce supported classifications
        classification = classification.upper()
        if classification not in {"FAKE", "REAL", "INCONCLUSIVE"}:
            classification = "INCONCLUSIVE"

        # Determine effective method and is_ai_model based on fallback
        effective_method = self.method if not fallback_used else "heuristic"
        effective_is_ai_model = self.is_ai_model and not fallback_used

        return {
            "detector_name": self.detector_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "framework": self.framework,
            "method": effective_method,
            "is_ai_model": effective_is_ai_model,
            "fallback_used": fallback_used,
            "classification": classification,
            "confidence": round(float(confidence), 4),
            "processing_time_ms": processing_time_ms,
            "metadata": metadata or {}
        }
