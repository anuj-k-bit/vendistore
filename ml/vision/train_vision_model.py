#!/usr/bin/env python3
"""
IntelliVend Computer Vision - Lightweight Slot Fill & Item Count Detector Training
Trains a multi-task PyTorch CNN to detect slot fill levels (`EMPTY`, `HALF`, `FULL`) and estimate item counts.
Saves model weights to `ml/vision/models/slot_detector.pth`.
"""

import os
import json
import random
import numpy as np
import cv2
from pathlib import Path
from PIL import Image

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms

from generate_synthetic_vision_data import generate_dataset

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
ANNOTATIONS_PATH = Path(__file__).parent / "dataset" / "annotations.json"

FILL_LEVEL_MAP = {"EMPTY": 0, "HALF": 1, "FULL": 2}
FILL_LEVEL_INV = {0: "EMPTY", 1: "HALF", 2: "FULL"}

class SlotDataset(Dataset):
    def __init__(self, annotations, transform=None):
        self.annotations = annotations
        self.transform = transform

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        item = self.annotations[idx]
        img_path = item["filepath"]

        image = Image.open(img_path).convert("RGB")
        fill_label = FILL_LEVEL_MAP[item["fill_level"]]
        count_label = float(item["item_count_estimate"])

        if self.transform:
            image = self.transform(image)

        return image, fill_label, count_label

class LightweightSlotDetector(nn.Module):
    """Lightweight 4-layer CNN feature extractor with dual classification & regression heads."""
    def __init__(self, num_classes=3):
        super(LightweightSlotDetector, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1), # 112x112
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # 56x56

            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1), # 28x28
            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1), # 14x14
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)) # 1x1
        )

        self.classifier = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, num_classes)
        )

        self.count_regressor = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        feat = self.features(x)
        feat_flat = feat.view(feat.size(0), -1)
        fill_logits = self.classifier(feat_flat)
        count_pred = self.count_regressor(feat_flat)
        return fill_logits, count_pred

def train_model(epochs=15, batch_size=16, lr=0.001):
    print("=" * 70)
    print("🧠 INTELLIVEND COMPUTER VISION DETECTOR TRAINING (PyTorch)")
    print("=" * 70)

    if not ANNOTATIONS_PATH.exists():
        annotations = generate_dataset()
    else:
        with open(ANNOTATIONS_PATH, "r", encoding="utf-8") as f:
            annotations = json.load(f)

    # Train / Val Split
    random.seed(42)
    random.shuffle(annotations)
    split_idx = int(len(annotations) * 0.8)
    train_anns = annotations[:split_idx]
    val_anns = annotations[split_idx:]

    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = SlotDataset(train_anns, transform=transform)
    val_dataset = SlotDataset(val_anns, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LightweightSlotDetector(num_classes=3).to(device)

    criterion_cls = nn.CrossEntropyLoss()
    criterion_reg = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    print(f"📦 Training Dataset Size: {len(train_anns)} | Validation Size: {len(val_anns)}")
    print(f"⚙️ Training Device: {device} | Epochs: {epochs} | Batch Size: {batch_size}\n")

    for epoch in range(1, epochs + 1):
        model.train()
        running_cls_loss = 0.0
        running_reg_loss = 0.0

        for imgs, fill_labels, count_labels in train_loader:
            imgs = imgs.to(device)
            fill_labels = fill_labels.to(device)
            count_labels = count_labels.float().to(device).unsqueeze(1)

            optimizer.zero_grad()
            fill_logits, count_preds = model(imgs)

            loss_cls = criterion_cls(fill_logits, fill_labels)
            loss_reg = criterion_reg(count_preds, count_labels)
            total_loss = loss_cls + 0.5 * loss_reg

            total_loss.backward()
            optimizer.step()

            running_cls_loss += loss_cls.item() * imgs.size(0)
            running_reg_loss += loss_reg.item() * imgs.size(0)

        # Validation phase
        model.eval()
        correct_fill = 0
        total_val = 0

        with torch.no_grad():
            for imgs, fill_labels, count_labels in val_loader:
                imgs = imgs.to(device)
                fill_labels = fill_labels.to(device)
                fill_logits, _ = model(imgs)
                preds = torch.argmax(fill_logits, dim=1)
                correct_fill += (preds == fill_labels).sum().item()
                total_val += fill_labels.size(0)

        val_acc = (correct_fill / total_val) * 100.0 if total_val > 0 else 0
        if epoch % 3 == 0 or epoch == epochs:
            print(f"Epoch [{epoch:02d}/{epochs:02d}] - Cls Loss: {running_cls_loss/len(train_anns):.4f} | Reg Loss: {running_reg_loss/len(train_anns):.4f} | Val Fill Accuracy: {val_acc:.1f}%")

    # Export Trained Weights
    model_save_path = MODELS_DIR / "slot_detector.pth"
    config_save_path = MODELS_DIR / "model_config.json"

    torch.save(model.state_dict(), model_save_path)

    config_data = {
        "num_classes": 3,
        "input_size": [128, 128],
        "fill_level_map": FILL_LEVEL_INV,
        "training_accuracy": round(val_acc, 2),
        "epochs": epochs
    }

    with open(config_save_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ Training Complete! Model Checkpoint saved to: {model_save_path}")
    print(f"📄 Config Metadata saved to: {config_save_path}")
    print("=" * 70)

    return model, config_data

if __name__ == "__main__":
    train_model()
