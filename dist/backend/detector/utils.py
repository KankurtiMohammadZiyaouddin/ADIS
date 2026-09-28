import os
import torch
import cv2
import numpy as np

def get_device():
    """Returns 'cuda' if GPU available, otherwise 'cpu'."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_checkpoint(model, checkpoint_path, device=None):
    """
    Safely loads pretrained checkpoint into Face-X-Ray model.
    """
    if device is None:
        device = get_device()
        
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint file not found at: {checkpoint_path}")
        
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    elif isinstance(checkpoint, dict) and "model" in checkpoint:
        state_dict = checkpoint["model"]
    else:
        state_dict = checkpoint
        
    model.load_state_dict(state_dict, strict=False)
    model.to(device)
    model.eval()
    return model

def generate_heatmap_overlay(original_bgr, mask):
    """
    Generates a color-mapped Face-X-Ray heatmap overlay image.
    
    Parameters:
    - original_bgr: numpy array (H, W, 3) BGR image
    - mask: numpy array (H, W) float values in [0, 1]
    
    Returns:
    - overlay_bgr: numpy array (H, W, 3) BGR image of original image with colormapped X-Ray heatmap
    """
    if mask.shape[:2] != original_bgr.shape[:2]:
        mask = cv2.resize(mask, (original_bgr.shape[1], original_bgr.shape[0]))
        
    # Scale mask to uint8 [0, 255]
    mask_uint8 = np.uint8(255 * np.clip(mask, 0, 1))
    
    # Apply JET colormap for thermal/heat rendering
    heatmap = cv2.applyColorMap(mask_uint8, cv2.COLORMAP_JET)
    
    # Blend original image and heatmap
    overlay = cv2.addWeighted(original_bgr, 0.5, heatmap, 0.5, 0)
    return overlay
