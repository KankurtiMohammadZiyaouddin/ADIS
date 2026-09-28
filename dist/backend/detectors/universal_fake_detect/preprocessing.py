import cv2
import numpy as np
import torch

class UniversalFakeDetectPreprocessor:
    """
    Preprocessing pipeline for UniversalFakeDetect (CLIP ViT-L/14 architecture).
    Reference:
    'Towards Universal Fake Image Detectors that Generalize Across Generative Models' (CVPR 2023)
    """
    def __init__(self, target_size=(224, 224)):
        self.target_size = target_size
        # OpenAI CLIP normalization parameters
        self.mean = torch.tensor([0.48145466, 0.4578275, 0.40821073]).view(3, 1, 1)
        self.std = torch.tensor([0.26862954, 0.26130258, 0.27577711]).view(3, 1, 1)

    def preprocess(self, image_bgr):
        """
        Preprocesses any BGR image (no face detection required):
        1. BGR -> RGB conversion
        2. Bicubic resize to (224, 224)
        3. Convert to FloatTensor in range [0, 1]
        4. Normalize using CLIP mean and std
        5. Add batch dimension -> (1, 3, 224, 224)
        """
        if image_bgr is None or image_bgr.size == 0:
            raise ValueError("Invalid empty image provided for UniversalFakeDetect preprocessing.")

        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized_rgb = cv2.resize(rgb, self.target_size, interpolation=cv2.INTER_CUBIC)

        tensor = torch.from_numpy(resized_rgb).permute(2, 0, 1).float() / 255.0
        tensor = (tensor - self.mean) / self.std
        tensor = tensor.unsqueeze(0)

        return tensor, resized_rgb
