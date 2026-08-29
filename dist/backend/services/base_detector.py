"""
ADIS Base Detector Interface
Abstract base class for all forensic sub-detectors across Image, Audio, and Video modalities.
"""

from abc import ABC, abstractmethod
import time


class BaseDetector(ABC):
    """
    Abstract Base Class for all forensic detectors.
    Ensures every sub-detector returns a standardized result dictionary.
    """

    def __init__(self, detector_name: str, model_name: str, model_version: str = "1.0.0"):
        self.detector_name = detector_name
        self.model_name = model_name
        self.model_version = model_version

    @abstractmethod
    def run_detection(self, media_path: str) -> dict:
        """
        Execute sub-detector logic on the media file.
        Must return tuple: (classification: str, confidence: float, metadata: dict)
        """
        pass

    def detect(self, media_path: str) -> dict:
        """
        Public execution wrapper measuring processing time and validating standardized schema.
        """
        start_time = time.perf_counter()
        try:
            classification, confidence, metadata = self.run_detection(media_path)
        except Exception as err:
            classification = "INCONCLUSIVE"
            confidence = 0.0
            metadata = {"error": str(err), "status": "failed"}

        end_time = time.perf_counter()
        processing_time_ms = int((end_time - start_time) * 1000)

        # Enforce supported classifications: FAKE, REAL, INCONCLUSIVE
        classification = classification.upper()
        if classification not in {"FAKE", "REAL", "INCONCLUSIVE"}:
            classification = "INCONCLUSIVE"

        return {
            "detector_name": self.detector_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "classification": classification,
            "confidence": round(float(confidence), 4),
            "processing_time_ms": processing_time_ms,
            "metadata": metadata or {}
        }
