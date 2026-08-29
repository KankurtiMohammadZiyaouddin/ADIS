import os
import sys
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from detector.DeepFakeMask import FaceXRayDetector
from detectors.honggu_xception.xception import HongguXceptionDetector
from detectors.universal_fake_detect.model import UniversalFakeDetectModel

def initialize_checkpoints():
    checkpoints_dir = os.path.join(BASE_DIR, "models", "checkpoints")
    universal_dir = os.path.join(BASE_DIR, "models", "universal_fake_detect")

    os.makedirs(checkpoints_dir, exist_ok=True)
    os.makedirs(universal_dir, exist_ok=True)

    # 1. Face-X-Ray Checkpoint
    xray_path = os.path.join(checkpoints_dir, "face_xray.pth")
    if not os.path.exists(xray_path):
        model = FaceXRayDetector()
        torch.save({"state_dict": model.state_dict()}, xray_path)
        print(f"[INIT] Initialized Face-X-Ray checkpoint at: {xray_path}")

    # 2. XceptionNet Checkpoint
    xc_path = os.path.join(checkpoints_dir, "FF++_c23.pth")
    if not os.path.exists(xc_path):
        model = HongguXceptionDetector(num_classes=2)
        torch.save({"state_dict": model.state_dict()}, xc_path)
        print(f"[INIT] Initialized XceptionNet checkpoint at: {xc_path}")

    # 3. UniversalFakeDetect Checkpoint
    univ_path = os.path.join(universal_dir, "fc_weights.pth")
    if not os.path.exists(univ_path):
        model = UniversalFakeDetectModel(feature_dim=768)
        torch.save({"state_dict": model.classifier.state_dict()}, univ_path)
        print(f"[INIT] Initialized UniversalFakeDetect checkpoint at: {univ_path}")

if __name__ == "__main__":
    initialize_checkpoints()
