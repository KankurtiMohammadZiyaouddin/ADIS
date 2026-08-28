import sys
import os
import time
import soundfile as sf
import numpy as np
import requests
import multiprocessing
import uvicorn
from pathlib import Path

# Setup sys.path to find main and services
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# URL settings
API_BASE = "http://127.0.0.1:8000"
HEALTH_URL = f"{API_BASE}/api/health"
ANALYZE_URL = f"{API_BASE}/api/audio/analyze"


def run_server():
    # Import inside process to avoid import conflicts
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def test_api():
    print("=== STARTING API VERIFICATION TESTS ===")

    # 1. Health check
    try:
        r = requests.get(HEALTH_URL)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        assert r.json() == {"status": "healthy"}, f"Expected healthy status, got {r.json()}"
        print("[PASS] Test 1: Health Check GET /api/health")
    except Exception as e:
        print(f"[FAIL] Test 1: Health Check failed: {e}")
        return False

    # Create test folder
    test_files_dir = Path("temp_test_files")
    test_files_dir.mkdir(exist_ok=True)

    try:
        # 2. Correct Audio File Upload & Inference
        wav_path = test_files_dir / "valid_test.wav"
        # Generate 1 second of random noise at 16kHz mono
        data = np.random.uniform(-0.1, 0.1, 16000).astype(np.float32)
        sf.write(str(wav_path), data, 16000)

        print("Uploading valid WAV file for analysis...")
        with open(wav_path, "rb") as f:
            r = requests.post(ANALYZE_URL, files={"audio_file": (wav_path.name, f, "audio/wav")})

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        res = r.json()
        assert res["success"] is True, f"Expected success: true, got {res}"
        assert "evidence" in res
        assert "analysis" in res
        assert "forensic" in res
        assert "analysis_id" in res["forensic"]
        assert res["evidence"]["filename"] == wav_path.name
        assert res["evidence"]["file_size_bytes"] == wav_path.stat().st_size
        assert "sha256" in res["evidence"]
        assert res["evidence"]["sample_rate"] == 16000
        assert res["evidence"]["channels"] == 1
        assert res["analysis"]["classification"] in ["FAKE", "REAL"]
        assert "confidence" in res["analysis"]
        assert res["analysis"]["model"] == "Deepfake-YamNet"
        assert res["analysis"]["model_version"] == "1.0.0"
        assert "processing_time_ms" in res["analysis"]
        assert res["forensic"]["evidence_integrity"] == "SHA-256 calculated"
        assert res["forensic"]["temporary_file_cleanup"] is True
        print(f"[PASS] Test 2: Valid WAV analysis. Result: {res['analysis']['classification']}, Score: {res['analysis']['confidence']}")

        # 3. Invalid file extension test
        txt_path = test_files_dir / "invalid_test.txt"
        with open(txt_path, "w") as f:
            f.write("This is not audio content.")

        with open(txt_path, "rb") as f:
            r = requests.post(ANALYZE_URL, files={"audio_file": (txt_path.name, f, "text/plain")})

        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        res = r.json()
        assert res["success"] is False
        assert res["error"]["code"] == "INVALID_AUDIO_FORMAT"
        print("[PASS] Test 3: Invalid extension validation")

        # 4. Oversized file test
        large_path = test_files_dir / "oversized.wav"
        # 11MB file
        with open(large_path, "wb") as f:
            f.write(b"\0" * (11 * 1024 * 1024))

        with open(large_path, "rb") as f:
            r = requests.post(ANALYZE_URL, files={"audio_file": (large_path.name, f, "audio/wav")})

        assert r.status_code == 413, f"Expected 413, got {r.status_code}"
        res = r.json()
        assert res["success"] is False
        assert res["error"]["code"] == "FILE_TOO_LARGE"
        print("[PASS] Test 4: Oversized file validation (10MB limit)")

        # 5. Unprocessable audio file test (valid extension but corrupt content)
        corrupt_path = test_files_dir / "corrupt.wav"
        with open(corrupt_path, "w") as f:
            f.write("corrupt header content")

        with open(corrupt_path, "rb") as f:
            r = requests.post(ANALYZE_URL, files={"audio_file": (corrupt_path.name, f, "audio/wav")})

        assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        res = r.json()
        assert res["success"] is False
        assert res["error"]["code"] == "UNPROCESSABLE_AUDIO"
        print("[PASS] Test 5: Unprocessable/corrupt audio decoding exception handling")

        # 6. Missing upload file field
        r = requests.post(ANALYZE_URL)
        assert r.status_code == 422, f"Expected 422, got {r.status_code}"
        print("[PASS] Test 6: Missing upload file validation (FastAPI validation error)")

        # 7. Empty filename validation
        r = requests.post(ANALYZE_URL, files={"audio_file": ("", b"\0\0\0\0", "audio/wav")})
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        res = r.json()
        assert res["success"] is False
        assert res["error"]["code"] == "MISSING_FILENAME"
        print("[PASS] Test 7: Empty/missing filename validation")

        # 8. Response schema & validation constraints
        with open(wav_path, "rb") as f:
            r = requests.post(ANALYZE_URL, files={"audio_file": (wav_path.name, f, "audio/wav")})
        assert r.status_code == 200
        res = r.json()
        assert isinstance(res["evidence"]["sha256"], str) and len(res["evidence"]["sha256"]) == 64, "Invalid SHA-256 length"
        assert res["analysis"]["classification"] in ["FAKE", "REAL"], "Invalid classification value"
        assert 0.0 <= res["analysis"]["confidence"] <= 1.0, "Confidence score out of boundary [0, 1]"
        assert "file_size_bytes" in res["evidence"]
        assert "duration_seconds" in res["evidence"]
        assert "sample_rate" in res["evidence"]
        assert "channels" in res["evidence"]
        assert "processing_time_ms" in res["analysis"]
        assert "model" in res["analysis"]
        assert "model_version" in res["analysis"]
        assert "analysis_id" in res["forensic"]
        print("[PASS] Test 8: Response schema and property validation check")

        print("=== ALL API TESTS PASSED SUCCESSFULLY ===")
        return True

    except Exception as e:
        print(f"[FAIL] Test execution encountered an error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup test files
        for item in test_files_dir.iterdir():
            try:
                item.unlink()
            except Exception:
                pass
        try:
            test_files_dir.rmdir()
        except Exception:
            pass


if __name__ == "__main__":
    # Start server process
    server_proc = multiprocessing.Process(target=run_server)
    server_proc.start()

    # Wait for server to warm up (load TF model)
    print("Waiting for backend server and TensorFlow to initialize...")
    max_retries = 90
    for i in range(max_retries):
        try:
            r = requests.get(HEALTH_URL, timeout=1)
            if r.status_code == 200:
                print(f"Backend ready after {i} seconds.")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
        if i % 10 == 0 and i > 0:
            print(f"Still waiting for server... ({i}s)")
    else:
        print("Server failed to start within 90 seconds.")
        server_proc.terminate()
        server_proc.join()
        sys.exit(1)

    success = False
    try:
        success = test_api()
    finally:
        print("Terminating server process...")
        server_proc.terminate()
        server_proc.join()

    if not success:
        sys.exit(1)
