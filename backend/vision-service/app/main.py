import os
import io
import time
import json
import logging
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any

import torch
import torch.nn as nn
import torchvision.transforms as transforms

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VisionService")

WORKSPACE_ROOT = Path(__file__).parent.parent.parent.parent
MODEL_PATH = WORKSPACE_ROOT / "ml" / "vision" / "models" / "slot_detector.pth"
CONFIG_PATH = WORKSPACE_ROOT / "ml" / "vision" / "models" / "model_config.json"

FILL_LEVEL_MAP = {0: "EMPTY", 1: "HALF", 2: "FULL"}

class LightweightSlotDetector(nn.Module):
    """Lightweight 4-layer CNN feature extractor with dual classification & regression heads."""
    def __init__(self, num_classes=3):
        super(LightweightSlotDetector, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
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

detector_model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def load_vision_model():
    global detector_model
    if not MODEL_PATH.exists():
        logger.warning(f"Vision model weights not found at {MODEL_PATH}. Training model now...")
        import sys
        sys.path.insert(0, str(WORKSPACE_ROOT / "ml" / "vision"))
        from train_vision_model import train_model
        train_model()

    detector_model = LightweightSlotDetector(num_classes=3).to(device)
    detector_model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    detector_model.eval()
    logger.info(f"Successfully loaded PyTorch Slot Detector from {MODEL_PATH}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_vision_model()
    yield

app = FastAPI(
    title="IntelliVend Computer Vision Detection Microservice",
    version="1.0.0",
    description="Analyzes slot camera images to predict fill level (EMPTY, HALF, FULL), item count estimates, and bounding boxes",
    lifespan=lifespan
)

class BoundingBoxItem(BaseModel):
    label: str
    confidence: float
    bbox: List[int] # [x_min, y_min, x_max, y_max]

class SlotDetectionResponse(BaseModel):
    fill_level: str
    item_count_estimate: int
    confidence: float
    detected_objects: List[BoundingBoxItem]
    inference_time_ms: float

    model_config = ConfigDict(from_attributes=True)

def detect_item_bboxes_opencv(cv_img):
    """Auxiliary visual object contour detector for bounding box localization."""
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 40, 255, cv2.THRESH_BINARY)[1]

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bboxes = []

    for c in contours:
        area = cv2.contourArea(c)
        if area > 800: # Filter small noise
            x, y, w, h = cv2.boundingRect(c)
            # Filter shelf rails
            if w > 20 and h > 30 and w < 280:
                bboxes.append({
                    "label": "vending_item",
                    "confidence": round(float(min(0.99, 0.75 + (area / 10000.0))), 2),
                    "bbox": [int(x), int(y), int(x + w), int(y + h)]
                })

    return bboxes

@app.get("/")
def read_root():
    return {
        "service": "IntelliVend Computer Vision Service",
        "status": "HEALTHY",
        "description": "Upload a slot camera image to POST /detect to analyze fill level and item count.",
        "interactive_docs": "http://localhost:8083/docs",
        "sample_images": "ml/vision/samples/"
    }

@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "vision-service",
        "model_loaded": detector_model is not None
    }

@app.post("/detect", response_model=SlotDetectionResponse)
async def detect_slot_image(file: UploadFile = File(...)):
    """
    Accepts an uploaded slot camera image file and returns fill level, item count estimate, and confidence.
    """
    if not detector_model:
        raise HTTPException(status_code=500, detail="Vision detector model not loaded.")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image (PNG, JPG, JPEG).")

    start_time = time.time()
    try:
        contents = await file.read()
        pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # PyTorch Inference
        tensor_img = transform(pil_img).unsqueeze(0).to(device)

        with torch.no_grad():
            fill_logits, count_pred = detector_model(tensor_img)
            fill_probs = torch.softmax(fill_logits, dim=1)[0]
            pred_class_idx = int(torch.argmax(fill_probs).item())
            fill_level = FILL_LEVEL_MAP[pred_class_idx]
            cls_confidence = float(fill_probs[pred_class_idx].item())

            item_count_float = float(count_pred[0].item())
            item_count_est = max(0, int(round(item_count_float)))

            if fill_level == "EMPTY":
                item_count_est = 0

        # Run OpenCV bounding box extraction
        detected_objects = detect_item_bboxes_opencv(cv_img)
        if fill_level == "EMPTY":
            detected_objects = []

        inference_time_ms = round((time.time() - start_time) * 1000, 2)

        return SlotDetectionResponse(
            fill_level=fill_level,
            item_count_estimate=item_count_est,
            confidence=round(cls_confidence, 3),
            detected_objects=[BoundingBoxItem(**b) for b in detected_objects],
            inference_time_ms=inference_time_ms
        )

    except Exception as e:
        logger.error(f"Error processing image upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze slot image: {e}")
