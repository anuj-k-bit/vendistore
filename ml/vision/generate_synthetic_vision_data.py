#!/usr/bin/env python3
"""
IntelliVend Computer Vision - Synthetic Slot Image Generator
Renders 150 synthetic vending machine slot camera images (320x320 px) across 3 fill levels:
- `EMPTY` (0 items)
- `HALF` (1–3 items)
- `FULL` (4–6 items)

Outputs image PNG files to `ml/vision/dataset/images/` and annotations to `ml/vision/dataset/annotations.json`.
"""

import os
import json
import random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageEnhance
from pathlib import Path

DATASET_DIR = Path(__file__).parent / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

ITEM_COLORS = [
    {"name": "Nitro Cold Brew Can", "body": (20, 20, 25), "accent": (0, 210, 240), "type": "can"},
    {"name": "Matcha Tea Bottle", "body": (40, 140, 60), "accent": (230, 245, 230), "type": "bottle"},
    {"name": "Electrolyte Drink", "body": (10, 100, 220), "accent": (255, 255, 255), "type": "bottle"},
    {"name": "Dark Chocolate Bar", "body": (45, 25, 15), "accent": (212, 175, 55), "type": "box"},
    {"name": "Protein Crunch Bar", "body": (15, 45, 100), "accent": (240, 110, 20), "type": "box"},
    {"name": "Detox Green Juice", "body": (25, 120, 45), "accent": (180, 230, 80), "type": "bottle"},
    {"name": "Mango Kombucha", "body": (180, 90, 20), "accent": (250, 200, 40), "type": "bottle"}
]

def render_slot_background(width=320, height=320):
    """Renders metallic vending machine slot shelf background with guide rails."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Dark metallic back panel gradient
    for y in range(height):
        intensity = int(18 + (y / height) * 22)
        img[y, :] = (intensity, intensity + 4, intensity + 8)

    # Shelf rails (vertical guide lines)
    rail_color = (60, 70, 85)
    cv2.line(img, (50, 0), (50, height), rail_color, 3)
    cv2.line(img, (width - 50, 0), (width - 50, height), rail_color, 3)

    # Bottom shelf surface (horizontal bar)
    shelf_y = int(height * 0.78)
    cv2.rectangle(img, (0, shelf_y), (width, height), (35, 42, 52), -1)
    cv2.line(img, (0, shelf_y), (width, shelf_y), (100, 115, 130), 2)

    # Top LED shadow gradient
    highlight_strip = np.full((1, width, 3), [120, 140, 160], dtype=np.uint8)
    for y in range(40):
        alpha = (40 - y) / 40.0 * 0.4
        img[y:y+1, :] = cv2.addWeighted(img[y:y+1, :], 1.0 - alpha, highlight_strip, alpha, 0)

    return img

def render_item(base_img, item_info, center_x, center_y, scale=1.0):
    """Renders a 3D-styled beverage can / box item on the shelf image."""
    h, w, _ = base_img.shape
    item_type = item_info["type"]
    body_color = item_info["body"]
    accent_color = item_info["accent"]

    # Base item dimensions
    if item_type == "box":
        item_w = int(45 * scale)
        item_h = int(85 * scale)
    else: # Can / Bottle
        item_w = int(38 * scale)
        item_h = int(95 * scale)

    x1 = int(center_x - item_w // 2)
    y1 = int(center_y - item_h // 2)
    x2 = x1 + item_w
    y2 = y1 + item_h

    # Ensure bounds inside canvas
    x1, y1 = max(5, x1), max(5, y1)
    x2, y2 = min(w - 5, x2), min(h - 5, y2)

    if x2 <= x1 or y2 <= y1:
        return base_img, None

    # Draw main body
    cv2.rectangle(base_img, (x1, y1), (x2, y2), body_color, -1)

    # Draw label accent band
    accent_y1 = int(y1 + (y2 - y1) * 0.3)
    accent_y2 = int(y1 + (y2 - y1) * 0.6)
    cv2.rectangle(base_img, (x1 + 2, accent_y1), (x2 - 2, accent_y2), accent_color, -1)

    # Draw metallic highlight on left side
    highlight_w = max(2, int((x2 - x1) * 0.15))
    cv2.rectangle(base_img, (x1 + 2, y1 + 2), (x1 + 2 + highlight_w, y2 - 2), (220, 230, 240), -1)

    # Outer border shadow
    cv2.rectangle(base_img, (x1, y1), (x2, y2), (15, 20, 25), 2)

    bbox = [x1, y1, x2, y2]
    return base_img, bbox

def generate_dataset(num_samples_per_category=50, random_seed=42):
    random.seed(random_seed)
    np.random.seed(random_seed)

    annotations = []

    categories = [
        {"fill_level": "EMPTY", "min_items": 0, "max_items": 0},
        {"fill_level": "HALF",  "min_items": 1, "max_items": 3},
        {"fill_level": "FULL",  "min_items": 4, "max_items": 6}
    ]

    image_counter = 0

    for cat in categories:
        fill_level = cat["fill_level"]

        for i in range(num_samples_per_category):
            image_counter += 1
            filename = f"slot_{image_counter:04d}_{fill_level.lower()}.png"
            image_path = IMAGES_DIR / filename

            canvas = render_slot_background(320, 320)
            item_count = random.randint(cat["min_items"], cat["max_items"])
            bboxes = []

            if item_count > 0:
                shelf_base_y = 220
                x_positions = np.linspace(80, 240, item_count).astype(int)

                for idx in range(item_count):
                    cx = int(x_positions[idx] + random.randint(-10, 10))
                    cy = int(shelf_base_y - (idx * 8) + random.randint(-4, 4))
                    scale = 0.85 + (idx * 0.05) + random.uniform(-0.03, 0.03)

                    item_info = random.choice(ITEM_COLORS)
                    canvas, bbox = render_item(canvas, item_info, cx, cy, scale)

                    if bbox:
                        bboxes.append({
                            "label": item_info["name"],
                            "type": item_info["type"],
                            "bbox": bbox
                        })

            # Add subtle noise
            noise = np.random.normal(0, 3, canvas.shape).astype(np.int16)
            canvas = np.clip(canvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)

            cv2.imwrite(str(image_path), canvas)

            annotations.append({
                "image_id": image_counter,
                "filename": filename,
                "filepath": str(image_path),
                "fill_level": fill_level,
                "item_count_estimate": len(bboxes),
                "bboxes": bboxes
            })

    # Save annotations JSON
    annotations_path = DATASET_DIR / "annotations.json"
    with open(annotations_path, "w", encoding="utf-8") as f:
        json.dump(annotations, f, indent=2)

    print(f"✅ Generated {len(annotations)} synthetic slot images across EMPTY, HALF, and FULL categories.")
    print(f"📁 Saved images to: {IMAGES_DIR}")
    print(f"📄 Saved annotations to: {annotations_path}")
    return annotations

if __name__ == "__main__":
    generate_dataset()
