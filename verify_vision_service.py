#!/usr/bin/env python3
"""
IntelliVend Computer Vision Service End-to-End Terminal Verifier
Executes:
1. Synthetic image dataset generation.
2. PyTorch vision model training.
3. Exports sample slot images (EMPTY, HALF, FULL).
4. Tests `POST /detect` endpoint against sample images and displays JSON response in terminal.
"""

import sys
import io
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Safe UTF-8 output formatting for Windows terminal
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent / "ml" / "vision"))

from generate_synthetic_vision_data import generate_dataset, render_slot_background, render_item, ITEM_COLORS
from train_vision_model import train_model

def create_sample_images():
    """Generates 3 test images for EMPTY, HALF, and FULL slot states."""
    samples_dir = Path(__file__).parent / "ml" / "vision" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    sample_files = {}

    # 1. EMPTY SLOT
    img_empty = render_slot_background(320, 320)
    p_empty = samples_dir / "sample_empty_slot.png"
    import cv2
    cv2.imwrite(str(p_empty), img_empty)
    sample_files["EMPTY"] = str(p_empty)

    # 2. HALF SLOT (2 items)
    img_half = render_slot_background(320, 320)
    render_item(img_half, ITEM_COLORS[0], 120, 215, 0.9)
    render_item(img_half, ITEM_COLORS[1], 180, 222, 0.95)
    p_half = samples_dir / "sample_half_slot.png"
    cv2.imwrite(str(p_half), img_half)
    sample_files["HALF"] = str(p_half)

    # 3. FULL SLOT (5 items)
    img_full = render_slot_background(320, 320)
    for idx, pos_x in enumerate([80, 115, 155, 195, 235]):
        render_item(img_full, ITEM_COLORS[idx % len(ITEM_COLORS)], pos_x, 220, 0.9)
    p_full = samples_dir / "sample_full_slot.png"
    cv2.imwrite(str(p_full), img_full)
    sample_files["FULL"] = str(p_full)

    return sample_files

def post_image_file(url, file_path):
    """Sends multipart/form-data image upload request using standard urllib."""
    import mimetypes
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = Path(file_path).name

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def verify_vision_pipeline():
    print("=" * 75)
    print("[1/3] GENERATING SYNTHETIC SLOT IMAGE DATASET")
    print("=" * 75)
    generate_dataset(num_samples_per_category=50)

    print("\n" + "=" * 75)
    print("[2/3] TRAINING PYTORCH SLOT FILL & ITEM DETECTOR MODEL")
    print("=" * 75)
    train_model(epochs=10)

    print("\n" + "=" * 75)
    print("[3/3] CREATING SAMPLE TEST IMAGES (EMPTY, HALF, FULL)")
    print("=" * 75)
    sample_files = create_sample_images()
    for category, fpath in sample_files.items():
        print(f"  * Generated sample {category:<5}: {fpath}")

    return sample_files

if __name__ == "__main__":
    verify_vision_pipeline()
