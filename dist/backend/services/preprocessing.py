import cv2
import numpy as np
import torch

class ImagePreprocessingService:
    """
    Image preprocessing and face alignment service required by Face-X-Ray model.
    """
    def __init__(self, target_size=(256, 256)):
        self.target_size = target_size
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        self.std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

    def preprocess_face(self, face_bgr):
        """
        Preprocesses face crop:
        1. BGR -> RGB
        2. Resize to model target resolution (256x256)
        3. Convert to torch Tensor (B, C, H, W)
        4. Normalize using standard ImageNet mean and std
        
        Returns:
        - preprocessed_tensor: torch.Tensor (1, 3, H, W)
        - rgb_resized: numpy array (H, W, 3)
        """
        if face_bgr is None or face_bgr.size == 0:
            raise ValueError("Invalid empty face crop provided for preprocessing.")
            
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        rgb_resized = cv2.resize(rgb, self.target_size, interpolation=cv2.INTER_CUBIC)
        
        # Convert to Tensor (3, H, W) normalized to [0, 1]
        tensor = torch.from_numpy(rgb_resized).permute(2, 0, 1).float() / 255.0
        
        # Normalize
        tensor = (tensor - self.mean) / self.std
        
        # Add Batch dimension -> (1, 3, H, W)
        tensor = tensor.unsqueeze(0)
        
        return tensor, rgb_resized
