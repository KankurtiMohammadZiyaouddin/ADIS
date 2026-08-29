import sys
import os
import time
from pathlib import Path
import soundfile as sf
import numpy as np
import cv2
from PIL import Image, ImageDraw
import requests

# Setup sys.path to find main and services
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

API_BASE = "http://127.0.0.1:8000"
HEALTH_URL = f"{API_BASE}/api/health"
IMAGE_ANALYZE_URL = f"{API_BASE}/api/image/analyze"
AUDIO_ANALYZE_URL = f"{API_BASE}/api/audio/analyze"
VIDEO_ANALYZE_URL = f"{API_BASE}/api/video/analyze"
HISTORY_URL = f"{API_BASE}/api/history"


def test_api():
    print("=== STARTING COMPREHENSIVE MULTIMODAL API SUITE TESTS ===")

    # 1. Health check
    try:
        r = requests.get(HEALTH_URL)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        res = r.json()
        assert res["status"] == "healthy"
        assert res["database"] == "connected"
        print("[PASS] Test 1: Health Check GET /api/health")
    except Exception as e:
        print(f"[FAIL] Test 1: Health Check failed: {e}")
        return False

    test_files_dir = Path("temp_test_files")
    test_files_dir.mkdir(exist_ok=True)

    try:
        # -------------------------------------------------------------------
        # IMAGE TESTS
        # -------------------------------------------------------------------
        img_path = test_files_dir / "valid_image.png"
        img = Image.new("RGB", (300, 300), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((10, 10), "ADIS Forensic Test Image", fill=(255, 255, 0))
        img.save(img_path)

        with open(img_path, "rb") as f:
            r = requests.post(IMAGE_ANALYZE_URL, files={"image_file": (img_path.name, f, "image/png")})
        assert r.status_code == 200, f"Expected 200 for image, got {r.status_code}: {r.text}"
        res = r.json()
        assert res["success"] is True
        assert res["media_type"] == "image"
        assert res["classification"] in ["FAKE", "REAL", "INCONCLUSIVE"]
        assert "sha256" in res
        assert "file_size_bytes" in res
        assert "confidence" in res
        assert "processing_time_ms" in res["processing"]
        print(f"[PASS] Test 2: Valid Image Analysis -> Verdict: {res['classification']}, Confidence: {res['confidence']}")

        # Invalid Image Extension
        invalid_img_path = test_files_dir / "invalid.txt"
        with open(invalid_img_path, "w") as f:
            f.write("not an image")
        with open(invalid_img_path, "rb") as f:
            r = requests.post(IMAGE_ANALYZE_URL, files={"image_file": (invalid_img_path.name, f, "text/plain")})
        assert r.status_code == 400
        print("[PASS] Test 3: Invalid Image Extension Validation")

        # Corrupt Image Content
        corrupt_img = test_files_dir / "corrupt.jpg"
        with open(corrupt_img, "wb") as f:
            f.write(b"corrupt image header data")
        with open(corrupt_img, "rb") as f:
            r = requests.post(IMAGE_ANALYZE_URL, files={"image_file": (corrupt_img.name, f, "image/jpeg")})
        assert r.status_code == 422
        print("[PASS] Test 4: Corrupt Image Handling")

        # -------------------------------------------------------------------
        # AUDIO TESTS
        # -------------------------------------------------------------------
        wav_path = test_files_dir / "valid_audio.wav"
        data = np.random.uniform(-0.1, 0.1, 16000).astype(np.float32)
        sf.write(str(wav_path), data, 16000)

        with open(wav_path, "rb") as f:
            r = requests.post(AUDIO_ANALYZE_URL, files={"audio_file": (wav_path.name, f, "audio/wav")})
        assert r.status_code == 200, f"Expected 200 for audio, got {r.status_code}: {r.text}"
        res = r.json()
        assert res["success"] is True
        assert res["media_type"] == "audio"
        assert res["classification"] in ["FAKE", "REAL", "INCONCLUSIVE"]
        assert len(res["sha256"]) == 64
        print(f"[PASS] Test 5: Valid Audio Analysis -> Verdict: {res['classification']}, Confidence: {res['confidence']}")

        # Invalid Audio Format
        with open(invalid_img_path, "rb") as f:
            r = requests.post(AUDIO_ANALYZE_URL, files={"audio_file": (invalid_img_path.name, f, "text/plain")})
        assert r.status_code == 400
        print("[PASS] Test 6: Invalid Audio Extension Validation")

        # -------------------------------------------------------------------
        # TEMPORAL VIDEO TESTS
        # -------------------------------------------------------------------
        video_path = test_files_dir / "valid_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 10.0, (128, 128))
        for i in range(20):
            frame = np.full((128, 128, 3), (i * 12) % 256, dtype=np.uint8)
            out.write(frame)
        out.release()

        with open(video_path, "rb") as f:
            r = requests.post(VIDEO_ANALYZE_URL, files={"video_file": (video_path.name, f, "video/mp4")})
        assert r.status_code == 200, f"Expected 200 for video, got {r.status_code}: {r.text}"
        res = r.json()
        assert res["success"] is True
        assert res["media_type"] == "video"
        assert "temporal_analysis" in res.get("analysis", {})
        print(f"[PASS] Test 7: Temporal Video Analysis -> Verdict: {res['classification']}, Continuity: {res['analysis']['temporal_analysis'].get('sequence_continuity')}")

        # Invalid Video Format
        with open(invalid_img_path, "rb") as f:
            r = requests.post(VIDEO_ANALYZE_URL, files={"video_file": (invalid_img_path.name, f, "text/plain")})
        assert r.status_code == 400
        print("[PASS] Test 8: Invalid Video Extension Validation")

        # -------------------------------------------------------------------
        # SQLITE HISTORY & COLLABORATION TEST
        # -------------------------------------------------------------------
        r = requests.get(HISTORY_URL)
        assert r.status_code == 200
        res = r.json()
        assert res["success"] is True
        assert res["count"] >= 3
        print(f"[PASS] Test 9: SQLite History Persistence -> {res['count']} Records Retrieved")

        print("=== ALL API SUITE VERIFICATION TESTS PASSED SUCCESSFULLY ===")
        return True

    finally:
        # Cleanup test folder
        for file in test_files_dir.glob("*"):
            try:
                file.unlink()
            except Exception:
                pass
        try:
            test_files_dir.rmdir()
        except Exception:
            pass


if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
