"""
ADIS YAMNet Audio Deepfake Sub-Detector
Wraps TensorFlow Deepfake-YamNet SavedModel under the BaseDetector modular interface.
"""

from pathlib import Path
import sys
import soundfile as sf
import tensorflow as tf

# Import base class
SERVICES_DIR = Path(__file__).resolve().parents[1]
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from base_detector import BaseDetector

# Add Deepfake-YamNet API path
YAMNET_API = (
    Path(__file__).resolve().parents[4]
    / "external"
    / "Deepfake-YamNet"
    / "API"
)
if str(YAMNET_API) not in sys.path:
    sys.path.insert(0, str(YAMNET_API))

from app.src.deepfake import deepfake_model, load_wav_16k_mono


class YamnetAudioDetector(BaseDetector):
    """
    Sub-detector wrapping TensorFlow Deepfake-YamNet model.
    """

    def __init__(self):
        super().__init__(
            detector_name="YAMNet Audio Detector",
            model_name="Deepfake-YamNet",
            model_version="1.0.0"
        )

    def run_detection(self, media_path: str) -> tuple:
        testing_wav_data = load_wav_16k_mono(media_path)
        if testing_wav_data is None:
            raise ValueError("Audio file could not be loaded or decoded for YAMNet inference.")

        infer = deepfake_model.signatures['serving_default']
        input_tensor = tf.convert_to_tensor(testing_wav_data, dtype=tf.float32)
        output = infer(input_tensor)
        predictions = output['output_0']
        pred_numpy = predictions.numpy()
        p_fake = float(pred_numpy[0])
        p_real = float(pred_numpy[1])

        if p_fake > p_real:
            classification = "FAKE"
            confidence = p_fake
        else:
            classification = "REAL"
            confidence = p_real

        metadata = {
            "prob_fake": round(p_fake, 4),
            "prob_real": round(p_real, 4),
            "target_sample_rate_hz": 16000,
            "architecture": "MobileNet-YAMNet Spectrogram Classifier"
        }

        return classification, confidence, metadata
