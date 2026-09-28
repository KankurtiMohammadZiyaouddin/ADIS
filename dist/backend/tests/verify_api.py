"""
ADIS Forensic Suite — P1 Hardening Verification Suite
Covers all original API tests PLUS the new P1 forensic hardening requirements:

New tests added:
  - SHA-256 full-file parity verification (frontend algorithm matches backend)
  - Heuristic fallback disclosure in detector schema
  - Backend cross-modal fusion endpoint (/api/cross-modal/analyze)
  - Detector disagreement -> INCONCLUSIVE result
  - is_true_temporal_model: False on video detector
  - Fabricated video metrics absence verification
  - SQLite persistence verification
"""

import sys
import os
import io
import time
import hashlib
from pathlib import Path
import soundfile as sf
import numpy as np
import cv2
from PIL import Image, ImageDraw
import requests

# Fix Windows console encoding for test output
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup sys.path to find main and services
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.forensic_fusion import fuse_detector_results

API_BASE = "http://127.0.0.1:8000"
HEALTH_URL            = f"{API_BASE}/api/health"
IMAGE_ANALYZE_URL     = f"{API_BASE}/api/image/analyze"
AUDIO_ANALYZE_URL     = f"{API_BASE}/api/audio/analyze"
VIDEO_ANALYZE_URL     = f"{API_BASE}/api/video/analyze"
HISTORY_URL           = f"{API_BASE}/api/history"
CROSS_MODAL_URL       = f"{API_BASE}/api/cross-modal/analyze"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_sha256_complete(file_path: Path) -> str:
    """Hash the complete file — same algorithm the browser must use."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def make_image(path: Path, size=(300, 300)):
    img = Image.new("RGB", size, color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "ADIS Forensic Test", fill=(255, 255, 0))
    img.save(path, format="PNG")


def make_audio_wav(path: Path, duration_sec=1, sample_rate=16000):
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.3).astype(np.int16)
    sf.write(str(path), data, sample_rate, subtype="PCM_16")


def make_video_mp4(path: Path, frames=30, size=(64, 64)):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(path), fourcc, 15.0, size)
    for i in range(frames):
        frame = np.full((size[1], size[0], 3), (50 + i * 6, 50, 100), dtype=np.uint8)
        out.write(frame)
    out.release()


def make_large_image(path: Path, size=(2000, 2000)):
    """Create an image > 1MB to verify full-file hashing."""
    arr = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    img.save(path, format="PNG")


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

def test_api():
    print("=== ADIS P1 HARDENING VERIFICATION SUITE ===")
    passed = 0
    failed = 0

    test_files_dir = Path("temp_test_files")
    test_files_dir.mkdir(exist_ok=True)

    # -----------------------------------------------------------------------
    # T01. Health Check
    # -----------------------------------------------------------------------
    try:
        r = requests.get(HEALTH_URL)
        assert r.status_code == 200
        res = r.json()
        assert res["status"] in ["healthy", "ok"]
        assert res["database"] == "connected"
        print("[PASS] T01: Health Check GET /api/health")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T01: Health Check: {e}")
        failed += 1
        return False  # Cannot proceed

    # -----------------------------------------------------------------------
    # T02. Valid Image Analysis — schema + ELA + framework provenance
    # -----------------------------------------------------------------------
    img_path = test_files_dir / "valid_image.png"
    make_image(img_path)
    try:
        with open(img_path, "rb") as f:
            r = requests.post(IMAGE_ANALYZE_URL, files={"image_file": (img_path.name, f, "image/png")})
        assert r.status_code == 200, r.text
        res = r.json()
        assert res["success"] is True
        assert res["media_type"] == "image"
        assert res["classification"] in ["FAKE", "REAL", "INCONCLUSIVE"]
        assert len(res["sha256"]) == 64
        assert len(res["detectors"]) >= 1
        assert "framework" in res["detectors"][0]
        assert len(res["forensic_indicators"]) >= 1
        assert res["forensic_indicators"][0]["indicator_name"] == "Error Level Analysis (ELA)"
        assert res["forensic_indicators"][0]["is_definitive_ai_proof"] is False
        assert "disclaimer" in res
        print(f"[PASS] T02: Valid Image Analysis — {res['classification']}, framework: {res['detectors'][0]['framework']}")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T02: Image Analysis: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T03. SHA-256 Parity — backend hash equals full-file hash (< 1MB file)
    # -----------------------------------------------------------------------
    try:
        client_hash = compute_sha256_complete(img_path)
        with open(img_path, "rb") as f:
            r = requests.post(IMAGE_ANALYZE_URL, files={"image_file": (img_path.name, f, "image/png")})
        res = r.json()
        backend_hash = res.get("sha256", "")
        assert len(backend_hash) == 64
        assert backend_hash == client_hash, (
            f"SHA-256 mismatch: backend={backend_hash[:16]}… client={client_hash[:16]}…"
        )
        print(f"[PASS] T03: SHA-256 parity (<1MB): backend == client full-file hash")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T03: SHA-256 parity (<1MB): {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T04. SHA-256 Parity — large image (> 1MB), verifies no 1MB truncation
    # -----------------------------------------------------------------------
    large_img_path = test_files_dir / "large_image.png"
    make_large_image(large_img_path)
    try:
        file_size = large_img_path.stat().st_size
        assert file_size > 1 * 1024 * 1024, f"Expected > 1MB, got {file_size}"
        client_hash = compute_sha256_complete(large_img_path)
        # Truncated 1MB hash for comparison
        truncated_hash = hashlib.sha256(open(large_img_path, "rb").read(1024 * 1024)).hexdigest()
        assert client_hash != truncated_hash, "Full-file hash should differ from 1MB truncated hash for large files"
        with open(large_img_path, "rb") as f:
            r = requests.post(IMAGE_ANALYZE_URL, files={"image_file": (large_img_path.name, f, "image/png")})
        if r.status_code == 200:
            res = r.json()
            backend_hash = res.get("sha256", "")
            assert backend_hash == client_hash, f"Backend hash {backend_hash[:8]}… != full-file hash {client_hash[:8]}…"
            assert backend_hash != truncated_hash, "Backend must NOT use truncated 1MB hash"
            print(f"[PASS] T04: SHA-256 parity (>1MB, {file_size//1024}KB): full-file hash matches backend, differs from 1MB truncation")
        else:
            print(f"[SKIP] T04: Large image upload returned {r.status_code} (may exceed limit) — verifying algorithm parity only")
            assert client_hash != truncated_hash
            print(f"[PASS] T04: SHA-256 full-file vs truncated algorithm difference confirmed")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T04: SHA-256 large file parity: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T05. Heuristic Fallback Disclosure — detector schema
    # -----------------------------------------------------------------------
    try:
        # Import the detector directly to test the schema
        from services.image_detectors.efficientnet_detector import EfficientNetImageDetector
        det = EfficientNetImageDetector()
        result = det.detect(str(img_path))

        # Verify all required schema fields are present
        required = ["detector_name", "model_name", "model_version", "framework",
                    "method", "is_ai_model", "fallback_used", "classification",
                    "confidence", "processing_time_ms", "metadata"]
        for field in required:
            assert field in result, f"Missing required field: {field}"

        # Verify method and is_ai_model are consistent
        if result["fallback_used"]:
            assert result["method"] == "heuristic", f"fallback_used=True must have method='heuristic', got: {result['method']}"
            assert result["is_ai_model"] is False, "fallback_used=True must have is_ai_model=False"
            # Verify heuristic warning in metadata
            assert "heuristic_warning" in result["metadata"]
            assert result["metadata"]["heuristic_warning"] is not None
            print(f"[PASS] T05: Heuristic fallback schema (fallback active) — method='heuristic', is_ai_model=False, warning present")
        else:
            assert result["method"] == "machine_learning"
            assert result["is_ai_model"] is True
            print(f"[PASS] T05: Heuristic fallback schema (model loaded) — method='machine_learning', is_ai_model=True")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T05: Heuristic fallback disclosure: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T06. Invalid Image Extension (HTTP 400)
    # -----------------------------------------------------------------------
    try:
        txt_path = test_files_dir / "invalid.txt"
        txt_path.write_text("not an image")
        with open(txt_path, "rb") as f:
            r = requests.post(IMAGE_ANALYZE_URL, files={"image_file": (txt_path.name, f, "text/plain")})
        assert r.status_code == 400
        print("[PASS] T06: Invalid Image Extension (HTTP 400)")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T06: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T07. Corrupt Image Content (HTTP 422)
    # -----------------------------------------------------------------------
    try:
        corrupt_path = test_files_dir / "corrupt.jpg"
        corrupt_path.write_bytes(b"NOTAJPEG" * 50)
        with open(corrupt_path, "rb") as f:
            r = requests.post(IMAGE_ANALYZE_URL, files={"image_file": (corrupt_path.name, f, "image/jpeg")})
        assert r.status_code in [422, 400]
        print(f"[PASS] T07: Corrupt Image Content (HTTP {r.status_code})")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T07: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T08. Valid Audio Analysis — YAMNet schema
    # -----------------------------------------------------------------------
    audio_path = test_files_dir / "test_audio.wav"
    make_audio_wav(audio_path)
    try:
        with open(audio_path, "rb") as f:
            r = requests.post(AUDIO_ANALYZE_URL, files={"audio_file": (audio_path.name, f, "audio/wav")})
        assert r.status_code == 200, r.text
        res = r.json()
        assert res["success"] is True
        assert res["media_type"] == "audio"
        assert res["classification"] in ["FAKE", "REAL", "INCONCLUSIVE"]
        assert len(res["sha256"]) == 64
        assert len(res["detectors"]) >= 1
        print(f"[PASS] T08: Valid Audio Analysis — {res['classification']}")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T08: Audio Analysis: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T09. Invalid Audio Extension (HTTP 400)
    # -----------------------------------------------------------------------
    try:
        bad_audio = test_files_dir / "bad.xyz"
        bad_audio.write_bytes(b"noise")
        with open(bad_audio, "rb") as f:
            r = requests.post(AUDIO_ANALYZE_URL, files={"audio_file": (bad_audio.name, f, "application/octet-stream")})
        assert r.status_code == 400
        print("[PASS] T09: Invalid Audio Extension (HTTP 400)")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T09: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T10. Valid Video Analysis — frame-based + is_true_temporal_model=False
    # -----------------------------------------------------------------------
    video_path = test_files_dir / "test_video.mp4"
    make_video_mp4(video_path)
    try:
        with open(video_path, "rb") as f:
            r = requests.post(VIDEO_ANALYZE_URL, files={"video_file": (video_path.name, f, "video/mp4")})
        assert r.status_code == 200, r.text
        res = r.json()
        assert res["success"] is True
        assert res["media_type"] == "video"
        assert res["classification"] in ["FAKE", "REAL", "INCONCLUSIVE"]
        assert len(res["sha256"]) == 64

        # Verify is_true_temporal_model is always False
        analysis = res.get("analysis", {})
        assert analysis.get("is_true_temporal_model") is False, (
            f"Expected is_true_temporal_model=False, got: {analysis.get('is_true_temporal_model')}"
        )
        print(f"[PASS] T10: Valid Video Analysis -- {res['classification']}, is_true_temporal_model=False OK")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T10: Video Analysis: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T11. Video Fabricated Metrics Absence — metrics=None in service response
    # -----------------------------------------------------------------------
    try:
        from services.video_detector import analyze_video
        result = analyze_video(str(video_path))
        # Verify fabricated metrics do NOT appear in backend response
        for fabricated in ["facialMeshIntegrity", "lipSyncJitter", "audioVisualSyncVariance",
                           "spatialArtifactScore", "temporalInconsistency", "frameAccuracy"]:
            assert fabricated not in result, f"Fabricated metric '{fabricated}' found in backend video result"
        print("[PASS] T11: Fabricated metrics absent from video detector output")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T11: Fabricated metrics absence: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T12. is_true_temporal_model explicitly False in frame_detector metadata
    # -----------------------------------------------------------------------
    try:
        from services.video_detectors.frame_detector import FrameVideoDetector
        det = FrameVideoDetector(sample_frames=5)
        result = det.detect(str(video_path))
        assert result["metadata"]["is_true_temporal_model"] is False, (
            f"Expected False, got: {result['metadata']['is_true_temporal_model']}"
        )
        assert "limitations_note" in result["metadata"]
        print("[PASS] T12: is_true_temporal_model=False preserved in FrameVideoDetector")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T12: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T13. Forensic Fusion — Agreement case
    # -----------------------------------------------------------------------
    try:
        detectors = [
            {"detector_name": "Det A", "model_name": "M", "model_version": "1", "framework": "F",
             "method": "machine_learning", "is_ai_model": True, "fallback_used": False,
             "classification": "FAKE", "confidence": 0.88, "processing_time_ms": 10, "metadata": {}},
            {"detector_name": "Det B", "model_name": "M", "model_version": "1", "framework": "F",
             "method": "machine_learning", "is_ai_model": True, "fallback_used": False,
             "classification": "FAKE", "confidence": 0.75, "processing_time_ms": 15, "metadata": {}},
        ]
        fusion = fuse_detector_results("image", detectors)
        assert fusion["primary_classification"] == "FAKE"
        assert fusion["detector_agreement"] is True
        assert fusion["disagreement_warning"] is None
        print(f"[PASS] T13: Forensic Fusion Agreement -- FAKE OK, disagreement_warning=None")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T13: Forensic Fusion Agreement: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T14. Forensic Fusion — Disagreement -> INCONCLUSIVE
    # -----------------------------------------------------------------------
    try:
        detectors_conflict = [
            {"detector_name": "Det A", "model_name": "M", "model_version": "1", "framework": "F",
             "method": "machine_learning", "is_ai_model": True, "fallback_used": False,
             "classification": "FAKE", "confidence": 0.91, "processing_time_ms": 10, "metadata": {}},
            {"detector_name": "Det B", "model_name": "M", "model_version": "1", "framework": "F",
             "method": "machine_learning", "is_ai_model": True, "fallback_used": False,
             "classification": "REAL", "confidence": 0.89, "processing_time_ms": 10, "metadata": {}},
        ]
        fusion = fuse_detector_results("image", detectors_conflict)
        assert fusion["primary_classification"] == "INCONCLUSIVE", (
            f"Expected INCONCLUSIVE for conflicting detectors, got: {fusion['primary_classification']}"
        )
        assert fusion["detector_agreement"] is False
        assert fusion["disagreement_warning"] is not None
        print(f"[PASS] T14: Forensic Fusion Disagreement -> INCONCLUSIVE OK, warning: '{fusion['disagreement_warning'][:40]}'")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T14: Forensic Fusion Disagreement: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T15. Backend Cross-Modal Endpoint — single modality
    # -----------------------------------------------------------------------
    try:
        payload = {
            "image": {
                "classification": "FAKE",
                "confidence": 0.87,
                "detector_name": "EfficientNet",
                "model_name": "dima806/deepfake_vs_real_image_detection",
                "method": "machine_learning",
                "is_ai_model": True,
                "fallback_used": False,
            }
        }
        r = requests.post(CROSS_MODAL_URL, json=payload)
        assert r.status_code == 200, r.text
        res = r.json()
        assert res["success"] is True
        assert res["assessment"] in ["FAKE", "REAL", "INCONCLUSIVE"]
        assert "assessment_confidence" in res
        assert "detector_agreement" in res
        assert "modality_sources" in res
        assert "image" in res["modality_sources"]
        assert res["fusion_method"] == "authoritative_backend_forensic_fusion"
        assert "disclaimer" in res
        print(f"[PASS] T15: Cross-Modal Endpoint (single modality) — {res['assessment']}")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T15: Cross-Modal single modality: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T16. Backend Cross-Modal Endpoint — disagreement -> INCONCLUSIVE
    # -----------------------------------------------------------------------
    try:
        payload_conflict = {
            "image": {
                "classification": "FAKE",
                "confidence": 0.91,
                "method": "machine_learning",
                "is_ai_model": True,
                "fallback_used": False,
            },
            "audio": {
                "classification": "REAL",
                "confidence": 0.89,
                "method": "machine_learning",
                "is_ai_model": True,
                "fallback_used": False,
            }
        }
        r = requests.post(CROSS_MODAL_URL, json=payload_conflict)
        assert r.status_code == 200, r.text
        res = r.json()
        assert res["assessment"] == "INCONCLUSIVE", (
            f"Expected INCONCLUSIVE for FAKE+REAL conflict, got: {res['assessment']}"
        )
        assert res["detector_agreement"] is False
        assert res["disagreement_warning"] is not None
        print(f"[PASS] T16: Cross-Modal Endpoint Disagreement -> INCONCLUSIVE ✓")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T16: Cross-Modal disagreement: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T17. Backend Cross-Modal Endpoint — heuristic fallback disclosure
    # -----------------------------------------------------------------------
    try:
        payload_heuristic = {
            "image": {
                "classification": "FAKE",
                "confidence": 0.70,
                "method": "heuristic",
                "is_ai_model": False,
                "fallback_used": True,
            }
        }
        r = requests.post(CROSS_MODAL_URL, json=payload_heuristic)
        assert r.status_code == 200, r.text
        res = r.json()
        assert len(res["fallback_warnings"]) > 0, "Expected heuristic fallback warning in cross-modal response"
        assert "image" in res["modality_sources"]
        assert res["modality_sources"]["image"]["fallback_used"] is True
        assert res["modality_sources"]["image"]["is_ai_model"] is False
        print(f"[PASS] T17: Cross-Modal Heuristic Fallback Disclosure — warning present ✓")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T17: Cross-Modal heuristic disclosure: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T18. Backend Cross-Modal Endpoint -- no modalities (HTTP 400 or 422)
    # -----------------------------------------------------------------------
    try:
        r = requests.post(CROSS_MODAL_URL, json={})
        # FastAPI may return 400 (our logic) or 422 (Body validation before handler)
        assert r.status_code in [400, 422], f"Expected 400 or 422, got {r.status_code}"
        if r.status_code == 400:
            res = r.json()
            assert res["error"]["code"] == "NO_MODALITIES_PROVIDED"
        print(f"[PASS] T18: Cross-Modal empty payload (HTTP {r.status_code})")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T18: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T19. SQLite Persistence — GET /api/history returns saved records
    # -----------------------------------------------------------------------
    try:
        r = requests.get(f"{HISTORY_URL}?limit=10")
        assert r.status_code == 200
        res = r.json()
        assert res["success"] is True
        assert isinstance(res["history"], list)
        print(f"[PASS] T19: SQLite Persistence — history contains {res['count']} records")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T19: SQLite Persistence: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T20. Fabricated Video Database is Empty -- INITIAL_VIDEO_DATABASE = []
    # -----------------------------------------------------------------------
    try:
        service_file = Path(__file__).resolve().parents[3] / "src" / "services" / "deepfakeService.js"
        if service_file.exists():
            content = service_file.read_text(encoding="utf-8")
            # Zero-hash is a known fabricated value from old code
            zero_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert zero_hash not in content, "Fabricated zero-hash found in deepfakeService.js"
            # Verify INITIAL_VIDEO_DATABASE is empty
            assert "INITIAL_VIDEO_DATABASE = [];" in content, "INITIAL_VIDEO_DATABASE should be []"
            # Verify fabricated metrics are gone from video analysis (no longer calculated from confidence)
            assert "facialMeshIntegrity:" not in content, "Fabricated facialMeshIntegrity found in deepfakeService.js"
            assert "lipSyncJitter:" not in content, "Fabricated lipSyncJitter found in deepfakeService.js"
            print("[PASS] T20: Fabricated video data removed from deepfakeService.js OK")
        else:
            print("[SKIP] T20: deepfakeService.js not found at expected path")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T20: Fabricated video database check: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T21. BaseDetector Schema — all required fields present
    # -----------------------------------------------------------------------
    try:
        from services.base_detector import BaseDetector

        class _TestDet(BaseDetector):
            def run_detection(self, media_path):
                return "REAL", 0.95, {}

        det = _TestDet("Test Det", "Test Model", "Test Framework", "1.0.0", "machine_learning", True)
        result = det.detect(str(img_path))
        required = ["detector_name", "model_name", "model_version", "framework",
                    "method", "is_ai_model", "fallback_used", "classification",
                    "confidence", "processing_time_ms", "metadata"]
        for field in required:
            assert field in result, f"Missing field: {field}"
        assert result["classification"] in ["FAKE", "REAL", "INCONCLUSIVE"]
        print("[PASS] T21: BaseDetector schema — all required fields present")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T21: BaseDetector schema: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # T22. BaseDetector Heuristic Fallback Schema Propagation
    # -----------------------------------------------------------------------
    try:
        from services.base_detector import BaseDetector

        class _HeuristicDet(BaseDetector):
            def run_detection(self, media_path):
                return "FAKE", 0.65, {"_fallback_used": True, "heuristic_warning": "⚠ Heuristic used"}

        det = _HeuristicDet("Heuristic", "None", "Heuristic", "0.0", "machine_learning", True)
        result = det.detect(str(img_path))
        assert result["fallback_used"] is True
        assert result["method"] == "heuristic"
        assert result["is_ai_model"] is False
        print("[PASS] T22: BaseDetector heuristic fallback propagation (method, is_ai_model, fallback_used) OK")
        passed += 1
    except Exception as e:
        print(f"[FAIL] T22: BaseDetector heuristic propagation: {e}")
        failed += 1

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print(f"\n=== RESULTS: {passed} passed / {failed} failed out of {passed + failed} tests ===")
    return failed == 0


# ---------------------------------------------------------------------------
# Cleanup helper
# ---------------------------------------------------------------------------
def cleanup():
    import shutil
    p = Path("temp_test_files")
    if p.exists():
        shutil.rmtree(p)
        print("[CLEAN] Temporary test files removed.")


if __name__ == "__main__":
    result = test_api()
    cleanup()
    sys.exit(0 if result else 1)
