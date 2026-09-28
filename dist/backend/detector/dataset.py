import numpy as np
import cv2
import torch
from torch.utils.data import Dataset

class FaceXRayDataset(Dataset):
    """
    Dataset loader helper for Face-X-Ray model validation and processing.
    """
    def __init__(self, image_paths, labels=None, transform=None, img_size=(256, 256)):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
        self.img_size = img_size

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = cv2.imread(img_path)
        if image is None:
            raise ValueError(f"Unable to read image at path: {img_path}")
            
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, self.img_size)
        
        # Normalize image to [0, 1] range and transpose to CHW
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        
        # Apply standard ImageNet normalization
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        image_tensor = (image_tensor - mean) / std

        label = self.labels[idx] if self.labels is not None else 0
        return image_tensor, label
