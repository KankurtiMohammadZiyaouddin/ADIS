import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvBlock(nn.Module):
    """Basic convolutional block with BatchNorm and ReLU activation."""
    def __init__(self, in_channels, out_channels, kernel_size=3, padding=1):
        super(ConvBlock, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=padding, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=kernel_size, padding=padding, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.conv(x)

class FaceXRayDetector(nn.Module):
    """
    Face-X-Ray Model Architecture for Face Forgery Boundary Detection.
    
    Reference:
    'Face X-Ray for More General Face Forgery Detection' (Li et al., CVPR 2020)
    
    Predicts:
    1. Face X-Ray mask: (B, 1, H, W) - blending boundary map (0 = real background, >0 = boundary artifact).
    2. Classification score: (B, 1) - Overall forgery probability.
    """
    def __init__(self, in_channels=3, base_filters=64):
        super(FaceXRayDetector, self).__init__()
        
        # Encoder (Feature Extractor)
        self.enc1 = ConvBlock(in_channels, base_filters)
        self.pool1 = nn.MaxPool2d(2, 2)
        
        self.enc2 = ConvBlock(base_filters, base_filters * 2)
        self.pool2 = nn.MaxPool2d(2, 2)
        
        self.enc3 = ConvBlock(base_filters * 2, base_filters * 4)
        self.pool3 = nn.MaxPool2d(2, 2)
        
        self.enc4 = ConvBlock(base_filters * 4, base_filters * 8)
        self.pool4 = nn.MaxPool2d(2, 2)
        
        # Bottleneck
        self.bottleneck = ConvBlock(base_filters * 8, base_filters * 16)
        
        # Decoder (Face X-Ray Boundary Mask Generator)
        self.up4 = nn.ConvTranspose2d(base_filters * 16, base_filters * 8, kernel_size=2, stride=2)
        self.dec4 = ConvBlock(base_filters * 16, base_filters * 8)
        
        self.up3 = nn.ConvTranspose2d(base_filters * 8, base_filters * 4, kernel_size=2, stride=2)
        self.dec3 = ConvBlock(base_filters * 8, base_filters * 4)
        
        self.up2 = nn.ConvTranspose2d(base_filters * 4, base_filters * 2, kernel_size=2, stride=2)
        self.dec2 = ConvBlock(base_filters * 4, base_filters * 2)
        
        self.up1 = nn.ConvTranspose2d(base_filters * 2, base_filters, kernel_size=2, stride=2)
        self.dec1 = ConvBlock(base_filters * 2, base_filters)
        
        # Mask Output Layer (1 channel X-Ray map)
        self.mask_head = nn.Sequential(
            nn.Conv2d(base_filters, 1, kernel_size=1),
            nn.Sigmoid()
        )
        
        # Global Classifier Head (Aggregates features for classification)
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.cls_head = nn.Sequential(
            nn.Linear(base_filters * 16, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # Encoder
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        e4 = self.enc4(self.pool3(e3))
        
        b = self.bottleneck(self.pool4(e4))
        
        # Decoder for X-Ray Mask Prediction
        d4 = self.up4(b)
        d4 = torch.cat([d4, e4], dim=1)
        d4 = self.dec4(d4)
        
        d3 = self.up3(d4)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)
        
        d2 = self.up2(d3)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)
        
        d1 = self.up1(d2)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)
        
        mask = self.mask_head(d1)
        
        # Global Forgery Classification
        pooled = self.global_pool(b).view(b.size(0), -1)
        cls_score = self.cls_head(pooled)
        
        return mask, cls_score
