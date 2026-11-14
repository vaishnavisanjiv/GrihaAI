# BuildGuard AI - Model Weights & Provenance

This directory stores the deep learning semantic segmentation model weights for BuildGuard AI.

## Active Model Checkpoint

- **Model File:** `floorplan_unet.pt`
- **Architecture:** PyTorch U-Net (ResNet-style skip-connection semantic segmentation)
- **Input Resolution:** $512 \times 512$ RGB floor plan images
- **Output Classes (13):**
  - **Background / Void (0)**
  - **Living / Dining (1)**
  - **Bedroom (2)**
  - **Bathroom / WC (3)**
  - **Kitchen (4)**
  - **Entry / Hallway (5)**
  - **Balcony (6)**
  - **Storage / Utility (7)**
  - **Garage (8)**
  - **Other Room (9)**
  - **Wall (10)**
  - **Door (11)**
  - **Window (12)**
- **Training Dataset:** CubiCasa5K (high-quality architectural floor plan subset)
- **Training Epochs:** 20 epochs trained on NVIDIA GPU via Google Colab
- **Model Checkpoint Hash:** Verified SHA-256 fingerprint displayed on analysis reports and technical inspector drawers.

## Training / Retraining Model

You can retrain the model or fine-tune weights on your own dataset using the provided Google Colab notebook:
- **Notebook:** [`colab_package/BuildGuardAI_Colab_Training.ipynb`](../../colab_package/BuildGuardAI_Colab_Training.ipynb)
- **Training Script:** [`scripts/train_floorplan_model.py`](../../scripts/train_floorplan_model.py)
