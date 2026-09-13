import cv2
import numpy as np
import torch

class HongguXceptionPreprocessor:
    """
    Image Preprocessing Pipeline for HongguLiu XceptionNet model (FaceForensics++ benchmark).
    """
    def __init__(self, target_size=(299, 299)):
        self.target_size = target_size
        # Mean and Std for Xception model normalized to [-1, 1]
        self.mean = torch.tensor([0.5, 0.5, 0.5]).view(3, 1, 1)
        self.std = torch.tensor([0.5, 0.5, 0.5]).view(3, 1, 1)

    def preprocess(self, face_bgr):
        """
        Preprocesses a BGR face crop for Xception model:
        1. BGR -> RGB conversion
        2. Resize to (299, 299)
        3. Convert to FloatTensor in [0, 1] range
        4. Normalize with mean=0.5, std=0.5 -> [-1, 1] range
        5. Add batch dimension -> (1, 3, 299, 299)
        """
        if face_bgr is None or face_bgr.size == 0:
            raise ValueError("Empty or invalid face crop provided for Xception preprocessing.")

        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        resized_rgb = cv2.resize(rgb, self.target_size, interpolation=cv2.INTER_CUBIC)

        tensor = torch.from_numpy(resized_rgb).permute(2, 0, 1).float() / 255.0
        tensor = (tensor - self.mean) / self.std
        tensor = tensor.unsqueeze(0)

        return tensor, resized_rgb
