"""
ADIS Forensic Fusion & Assessment Layer
Combines findings from multiple sub-detectors and forensic indicators without blind confidence averaging.
Resolves detector disagreements and enforces non-definitive probabilistic assessments.
"""


def fuse_detector_results(media_type: str, detector_results: list, forensic_indicators: list = None) -> dict:
    """
    Assess results from multiple sub-detectors for a single media file.

    Parameters:
      media_type: 'image' | 'audio' | 'video'
      detector_results: list of standardized detector dicts from BaseDetector.detect()
      forensic_indicators: list of non-model forensic signals (e.g. ELA, SHA-256 metadata)

    Returns:
      {
        "primary_classification": "FAKE" | "REAL" | "INCONCLUSIVE",
        "primary_confidence": float,
        "detector_agreement": bool,
        "disagreement_warning": str or None,
        "detectors": list,
        "forensic_indicators": list,
        "disclaimer": str
      }
    """
    if not detector_results:
        return {
            "primary_classification": "INCONCLUSIVE",
            "primary_confidence": 0.0,
            "detector_agreement": True,
            "disagreement_warning": "No detector results available.",
            "detectors": [],
            "forensic_indicators": forensic_indicators or [],
            "disclaimer": "All forensic outputs are probabilistic models and do not constitute legal proof."
        }

    # Filter valid classifications
    classifications = [d["classification"] for d in detector_results]
    confidences = [d["confidence"] for d in detector_results]

    fake_detectors = [d for d in detector_results if d["classification"] == "FAKE"]
    real_detectors = [d for d in detector_results if d["classification"] == "REAL"]

    disagreement_warning = None
    detector_agreement = True

    # 1. Conflict Resolution Logic
    if fake_detectors and real_detectors:
        # Strong disagreement detected between models!
        fake_max_conf = max(d["confidence"] for d in fake_detectors)
        real_max_conf = max(d["confidence"] for d in real_detectors)

        if fake_max_conf >= 0.60 and real_max_conf >= 0.60:
            detector_agreement = False
            primary_classification = "INCONCLUSIVE"
            primary_confidence = round(max(fake_max_conf, real_max_conf), 4)
            disagreement_warning = (
                f"Detector disagreement detected ({fake_detectors[0]['detector_name']}: FAKE {int(fake_max_conf*100)}% vs "
                f"{real_detectors[0]['detector_name']}: REAL {int(real_max_conf*100)}%). Manual expert review recommended."
            )
        elif fake_max_conf > real_max_conf:
            primary_classification = "FAKE"
            primary_confidence = fake_max_conf
        else:
            primary_classification = "REAL"
            primary_confidence = real_max_conf

    elif fake_detectors:
        primary_classification = "FAKE"
        # Use max confidence (highest certainty detector) rather than naive average
        primary_confidence = max(d["confidence"] for d in fake_detectors)

    elif real_detectors:
        primary_classification = "REAL"
        primary_confidence = max(d["confidence"] for d in real_detectors)

    else:
        primary_classification = "INCONCLUSIVE"
        primary_confidence = max(confidences) if confidences else 0.0

    return {
        "primary_classification": primary_classification,
        "primary_confidence": round(primary_confidence, 4),
        "detector_agreement": detector_agreement,
        "disagreement_warning": disagreement_warning,
        "detectors": detector_results,
        "forensic_indicators": forensic_indicators or [],
        "disclaimer": "Forensic classification model outputs are probabilistic indicators. Results must be reviewed by a certified forensic examiner before legal submission."
    }
