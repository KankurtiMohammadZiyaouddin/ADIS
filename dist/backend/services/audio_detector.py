from pathlib import Path
import sys

# Add the Deepfake-YamNet API directory to Python's import path.
YAMNET_API = (
    Path(__file__).resolve().parents[3]
    / "external"
    / "Deepfake-YamNet"
    / "API"
)

if str(YAMNET_API) not in sys.path:
    sys.path.insert(0, str(YAMNET_API))

from app.src.deepfake import deepfake_model, load_wav_16k_mono
import hashlib
import time
import uuid
import soundfile as sf
import tensorflow as tf


def analyze_audio(audio_path: str) -> dict:
    """
    Run the existing Deepfake-YamNet detector and return a structured forensic result.
    """
    # 1. Hashing (SHA-256) of the original file
    sha256_hash = hashlib.sha256()
    with open(audio_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    sha256 = sha256_hash.hexdigest()

    # 2. File size
    file_size_bytes = Path(audio_path).stat().st_size

    # 3. Audio characteristics (duration, sample rate, channels) using soundfile info
    try:
        info = sf.info(audio_path)
        duration_seconds = info.duration
        original_sample_rate = info.samplerate
        channels = info.channels
    except Exception:
        # Fallback if soundfile fails to parse the file structure
        duration_seconds = 0.0
        original_sample_rate = 16000
        channels = 1

    # 4. Measure processing/inference time
    start_time = time.perf_counter()

    testing_wav_data = load_wav_16k_mono(audio_path)
    if testing_wav_data is None:
        raise ValueError("The file could not be loaded as audio (unsupported or corrupt).")

    # Run inference using the TensorFlow SavedModel loaded in the deepfake module
    try:
        infer = deepfake_model.signatures['serving_default']
        input_tensor = tf.convert_to_tensor(testing_wav_data, dtype=tf.float32)
        output = infer(input_tensor)
        predictions = output['output_0']
        pred_numpy = predictions.numpy()
        p_fake = float(pred_numpy[0])
        p_real = float(pred_numpy[1])
    except Exception as e:
        raise RuntimeError(f"Model inference failed: {str(e)}")

    end_time = time.perf_counter()
    processing_time_ms = int((end_time - start_time) * 1000)

    # Classify based on highest probability
    if p_fake > p_real:
        classification = "FAKE"
        is_deepfake = True
        confidence = p_fake
    else:
        classification = "REAL"
        is_deepfake = False
        confidence = p_real

    # Generate a unique analysis ID
    analysis_id = str(uuid.uuid4())

    return {
        "sha256": sha256,
        "file_size_bytes": file_size_bytes,
        "duration_seconds": round(duration_seconds, 2),
        "sample_rate": original_sample_rate,
        "channels": channels,
        "classification": classification,
        "confidence": round(confidence, 4),
        "processing_time_ms": processing_time_ms,
        "analysis_id": analysis_id
    }
