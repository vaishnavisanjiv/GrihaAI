from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageOps
from torch import nn
from torch.nn import functional as F

IMAGE_SIZE = 512
NUM_CLASSES = 13
CLASS_NAMES = (
    "background",
    "wall",
    "kitchen",
    "living_dining",
    "bedroom",
    "bathroom",
    "entry",
    "railing",
    "storage",
    "garage",
    "other_room",
    "door",
    "window",
)
ROOM_LABELS = {
    2: "Kitchen",
    3: "Living / Dining",
    4: "Bedroom",
    5: "Bathroom",
    6: "Entry / Hallway",
    8: "Storage",
    9: "Garage",
    10: "Other room",
}
# Class 7 is reserved in the checkpoint schema but has no labeled pixels in
# the validated local dataset, so inference does not report it as a detection.
UNSUPPORTED_CLASS_IDS = frozenset({7})
ELEMENT_LABELS = {1: "wall", 11: "door", 12: "window"}


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return self.layers(value)


class FloorPlanUNet(nn.Module):
    def __init__(self, num_classes: int = NUM_CLASSES) -> None:
        super().__init__()
        self.encoder1 = ConvBlock(3, 32)
        self.encoder2 = ConvBlock(32, 64)
        self.encoder3 = ConvBlock(64, 128)
        self.encoder4 = ConvBlock(128, 256)
        self.bottleneck = ConvBlock(256, 384)
        self.decoder4 = ConvBlock(384 + 256, 256)
        self.decoder3 = ConvBlock(256 + 128, 128)
        self.decoder2 = ConvBlock(128 + 64, 64)
        self.decoder1 = ConvBlock(64 + 32, 32)
        self.classifier = nn.Conv2d(32, num_classes, kernel_size=1)
        self.pool = nn.MaxPool2d(kernel_size=2)

    def _decode(self, value: torch.Tensor, skip: torch.Tensor, block: ConvBlock) -> torch.Tensor:
        value = F.interpolate(value, size=skip.shape[-2:], mode="bilinear", align_corners=False)
        return block(torch.cat((value, skip), dim=1))

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        skip1 = self.encoder1(value)
        skip2 = self.encoder2(self.pool(skip1))
        skip3 = self.encoder3(self.pool(skip2))
        skip4 = self.encoder4(self.pool(skip3))
        value = self.bottleneck(self.pool(skip4))
        value = self._decode(value, skip4, self.decoder4)
        value = self._decode(value, skip3, self.decoder3)
        value = self._decode(value, skip2, self.decoder2)
        value = self._decode(value, skip1, self.decoder1)
        return self.classifier(value)


def load_checkpoint(checkpoint_path: Path, device: torch.device) -> tuple[FloorPlanUNet, dict[str, Any]]:
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    if checkpoint.get("architecture") != "buildguard-unet-v1":
        raise ValueError("Unsupported floor-plan model architecture")
    if checkpoint.get("image_size") != IMAGE_SIZE:
        raise ValueError(f"Model checkpoint must use {IMAGE_SIZE}x{IMAGE_SIZE} training inputs")
    if checkpoint.get("class_names") != list(CLASS_NAMES):
        raise ValueError("Model checkpoint labels do not match the supported CubiCasa5K label map")
    model = FloorPlanUNet(num_classes=len(CLASS_NAMES)).to(device)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, checkpoint


def predict_image(model: FloorPlanUNet, image_path: Path, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        original_size = image.size
        resized = image.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
        image_array = np.asarray(resized, dtype=np.float32) / 255.0

    tensor = torch.from_numpy(image_array.transpose(2, 0, 1)).unsqueeze(0).to(device)
    with torch.inference_mode():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=1)
        probabilities = F.interpolate(
            probabilities,
            size=(original_size[1], original_size[0]),
            mode="bilinear",
            align_corners=False,
        )[0]
    probability_array = probabilities.cpu().numpy()
    labels = probability_array.argmax(axis=0).astype(np.uint8)
    confidence = probability_array.max(axis=0).astype(np.float32)
    return labels, confidence
