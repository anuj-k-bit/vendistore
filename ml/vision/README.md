# IntelliVend Computer Vision Service (`ml/vision`)

## 📌 Overview
The **IntelliVend Vision System** analyzes vending machine slot camera images using a lightweight PyTorch deep learning detector to estimate slot fill levels (`EMPTY`, `HALF`, `FULL`), calculate item count estimates, and output object bounding box locations.

---

## ⚠️ Synthetic Dataset Disclaimer & Real Camera Adaptations

> [!IMPORTANT]
> The current model is trained on a **programmatically generated synthetic visual dataset** (`ml/vision/generate_synthetic_vision_data.py`).
> While synthetic data accelerates prototyping, deploying vision models in production vending hardware requires addressing domain transfer challenges.

### 🎥 What Changes with Real Camera Data?

1. **Glass Door Reflections & Glare**:
   - *Synthetic*: Uniform diffuse lighting without specular glare reflections.
   - *Real Camera*: Reflections of external store lights, sunlight, and people walking by. Real training pipeline requires polarizers, multi-exposure HDR, and specular reflection augmentation.

2. **Occlusion & Deep Spiral Depth**:
   - *Synthetic*: Items rendered in clear linear depth perspective.
   - *Real Camera*: Items at the back of deep spiral coils are heavily occluded by items in front. Requires temporal camera tracking or multi-frame multi-angle camera fusion.

3. **Lighting & LED Shadow Variations**:
   - *Synthetic*: Fixed top-LED shadow gradient.
   - *Real Camera*: LED strip degradation, flickering, and shadows cast by surrounding vending slots. Requires aggressive brightness, contrast, and HSV color jittering during data augmentation.

4. **Wide-Angle Lens Distortion**:
   - *Synthetic*: Orthographic/rectilinear perspective.
   - *Real Camera*: Small fisheye or wide-angle micro-cameras suffer from radial barrel distortion. Requires intrinsic camera matrix calibration (`cv2.undistort`) before inference.

---

## 🚀 Model Architecture & API

- **Backbone**: Lightweight 4-layer Convolutional Neural Network with Adaptive Average Pooling.
- **Task Heads**:
  1. `fill_level`: 3-class Softmax Classification (`EMPTY`, `HALF`, `FULL`).
  2. `item_count`: Continuous Regression Head.
- **REST Endpoint**: `POST /detect` accepting `multipart/form-data` image file upload.
