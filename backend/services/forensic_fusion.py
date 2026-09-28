"""
ADIS Forensic Fusion & Assessment Layer
Combines findings from multiple sub-detectors and forensic indicators without blind confidence averaging.
Resolves detector disagreements and enforces non-definitive probabilistic assessments.
"""

from datetime import datetime, timezone


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

    fake_detectors = [d for d in detector_results if d.get("classification") == "FAKE"]
    real_detectors = [d for d in detector_results if d.get("classification") == "REAL"]

    disagreement_warning = None
    detector_agreement = True

    # Conflict Resolution Logic:
    # If independent detectors yield opposing verdicts with confidence >= 0.55
    if fake_detectors and real_detectors:
        fake_max_conf = max(d.get("confidence", 0.0) for d in fake_detectors)
        real_max_conf = max(d.get("confidence", 0.0) for d in real_detectors)

        if fake_max_conf >= 0.55 and real_max_conf >= 0.55:
            detector_agreement = False
            primary_classification = "INCONCLUSIVE"
            primary_confidence = round(max(fake_max_conf, real_max_conf), 4)
            disagreement_warning = (
                f"Detector disagreement detected ({fake_detectors[0].get('detector_name', 'Detector A')}: FAKE {int(fake_max_conf*100)}% vs "
                f"{real_detectors[0].get('detector_name', 'Detector B')}: REAL {int(real_max_conf*100)}%). Manual expert review recommended."
            )
        elif fake_max_conf > real_max_conf:
            primary_classification = "FAKE"
            primary_confidence = fake_max_conf
        else:
            primary_classification = "REAL"
            primary_confidence = real_max_conf

    elif fake_detectors:
        primary_classification = "FAKE"
        primary_confidence = max(d.get("confidence", 0.0) for d in fake_detectors)

    elif real_detectors:
        primary_classification = "REAL"
        primary_confidence = max(d.get("confidence", 0.0) for d in real_detectors)

    else:
        primary_classification = "INCONCLUSIVE"
        confidences = [d.get("confidence", 0.0) for d in detector_results]
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


def fuse_cross_modal_evidence(modality_payload: dict) -> dict:
    """
    Authoritative cross-modal forensic fusion correlating evidence across Image, Audio, and Video.
    """
    if not modality_payload:
        return {
            "success": False,
            "error": "No modality evidence items provided for cross-modal analysis.",
            "assessment": "INCONCLUSIVE",
            "assessment_confidence": 0.0,
            "confidence": 0.0,
            "detector_agreement": True,
            "disagreement_warning": "No evidence submitted.",
            "modality_sources": {},
            "modalities": {},
            "fallback_warnings": [],
            "fusion_method": "authoritative_backend_forensic_fusion",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "disclaimer": "All forensic outputs are probabilistic models and do not constitute legal proof."
        }

    sources = {}
    fallback_warnings = []
    fake_modalities = []
    real_modalities = []
    inconclusive_modalities = []

    for mod_name in ["image", "audio", "video"]:
        item = modality_payload.get(mod_name)
        if not item or not isinstance(item, dict):
            continue

        raw_conf = float(item.get("confidence", 0.0))
        norm_conf = raw_conf / 100.0 if raw_conf > 1.0 else raw_conf
        norm_conf = round(min(1.0, max(0.0, norm_conf)), 4)

        cls = str(item.get("classification") or item.get("verdict") or "INCONCLUSIVE").upper()
        if cls not in {"FAKE", "REAL", "INCONCLUSIVE"}:
            cls = "INCONCLUSIVE"

        fallback = bool(item.get("fallback_used") or item.get("simulated"))
        if fallback:
            fallback_warnings.append(f"⚠ {mod_name.capitalize()} evidence used a fallback or heuristic detector.")

        source_info = {
            "classification": cls,
            "confidence": norm_conf,
            "detector_name": item.get("detector_name") or item.get("model_name") or f"{mod_name.capitalize()} Detector",
            "model_name": item.get("model_name") or item.get("model") or "ADIS-Detector",
            "model_version": item.get("model_version", "1.0.0"),
            "framework": item.get("framework", "Unknown"),
            "fallback_used": fallback,
            "filename": item.get("filename", f"{mod_name}_evidence"),
            "sha256": item.get("sha256", ""),
            "timestamp": item.get("timestamp") or datetime.now(timezone.utc).isoformat()
        }
        sources[mod_name] = source_info

        if cls == "FAKE":
            fake_modalities.append((mod_name, source_info))
        elif cls == "REAL":
            real_modalities.append((mod_name, source_info))
        else:
            inconclusive_modalities.append((mod_name, source_info))

    if not sources:
        return {
            "success": False,
            "error": "No valid modalities could be parsed from request.",
            "assessment": "INCONCLUSIVE",
            "assessment_confidence": 0.0,
            "confidence": 0.0,
            "detector_agreement": True,
            "disagreement_warning": "No valid modality evidence found.",
            "modality_sources": {},
            "modalities": {},
            "fallback_warnings": [],
            "fusion_method": "authoritative_backend_forensic_fusion",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "disclaimer": "All forensic outputs are probabilistic models and do not constitute legal proof."
        }

    detector_agreement = True
    disagreement_warning = None

    if fake_modalities and real_modalities:
        fake_max_conf = max(s["confidence"] for _, s in fake_modalities)
        real_max_conf = max(s["confidence"] for _, s in real_modalities)

        if fake_max_conf >= 0.55 and real_max_conf >= 0.55:
            detector_agreement = False
            assessment = "INCONCLUSIVE"
            final_conf = round(max(fake_max_conf, real_max_conf), 4)
            disagreement_warning = (
                f"Modal conflict: {fake_modalities[0][0].capitalize()} indicates FAKE ({int(fake_max_conf*100)}%) while "
                f"{real_modalities[0][0].capitalize()} indicates REAL ({int(real_max_conf*100)}%). Manual multi-modal examination required."
            )
            verdict_title = "MODAL CONFLICT / INCONCLUSIVE"
            summary = "Individual evidence modalities yielded conflicting assessments above significant confidence thresholds."
        elif fake_max_conf > real_max_conf:
            assessment = "FAKE"
            final_conf = fake_max_conf
            verdict_title = "PROBABLE SYNTHETIC MANIPULATION"
            summary = f"Synthetic manipulation detected in {fake_modalities[0][0]} modality with primary confidence {int(final_conf*100)}%."
        else:
            assessment = "REAL"
            final_conf = real_max_conf
            verdict_title = "LIKELY AUTHENTIC RECORDING"
            summary = f"Authenticity validated across {real_modalities[0][0]} modality with primary confidence {int(final_conf*100)}%."

    elif fake_modalities:
        assessment = "FAKE"
        final_conf = max(s["confidence"] for _, s in fake_modalities)
        verdict_title = "SYNTHETIC / DEEPFAKE DETECTED"
        summary = f"Consistent deepfake signals observed across {len(fake_modalities)} analyzed modality/modalities."

    elif real_modalities:
        assessment = "REAL"
        final_conf = max(s["confidence"] for _, s in real_modalities)
        verdict_title = "AUTHENTIC MEDIA CONFIRMED"
        summary = f"Authentic forensic features verified across {len(real_modalities)} analyzed modality/modalities."

    else:
        assessment = "INCONCLUSIVE"
        conf_list = [s["confidence"] for s in sources.values()]
        final_conf = max(conf_list) if conf_list else 0.0
        verdict_title = "INCONCLUSIVE ASSESSMENT"
        summary = "Submitted evidence signals did not exceed authoritative forensic confidence thresholds."

    evidence_breakdown = []
    for mod, s in sources.items():
        status_sym = "⚠" if s["classification"] == "FAKE" else ("✓" if s["classification"] == "REAL" else "•")
        evidence_breakdown.append(
            f"{status_sym} {mod.capitalize()} ({s['detector_name']}): {s['classification']} ({int(s['confidence']*100)}%)"
        )

    return {
        "success": True,
        "assessment": assessment,
        "classification": assessment,
        "assessment_confidence": final_conf,
        "confidence": final_conf,
        "detector_agreement": detector_agreement,
        "disagreement_warning": disagreement_warning,
        "fallback_warnings": fallback_warnings,
        "modality_sources": sources,
        "modalities": sources,
        "verdict_title": verdict_title,
        "summary": summary,
        "evidence_breakdown": evidence_breakdown,
        "fusion_method": "authoritative_backend_forensic_fusion",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Cross-modal forensic outputs are probabilistic indicators. Results must be reviewed by a certified forensic examiner before legal submission."
    }
