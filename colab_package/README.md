# BuildGuard AI — Google Colab GPU Training Guide

This directory contains everything pre-packaged to train your model on a high-speed Cloud GPU (NVIDIA T4 / V100 / A100) on Google Colab.

## 📦 Package Contents

1. **`BuildGuardAI_training.zip`** (11 KB): Contains the training and evaluation scripts, and the model definition modules.
2. **`CubiCasa5K_processed.zip`** (723 MB): Contains all 4,992 normalized $512 \times 512$ RGB floor-plan images, indexed masks, and deterministic splits (`train.jsonl`, `val.jsonl`, `test.jsonl`).
3. **`BuildGuardAI_Colab_Training.ipynb`**: Pre-configured Colab notebook with GPU checks, extraction to local NVMe, mixed-precision training, and test evaluation.

---

## 🚀 3 Simple Steps to Train on Google Colab

### Step 1: Upload to Google Drive
Open your [Google Drive](https://drive.google.com/) and create this folder structure:
```
My Drive/
└── BuildGuardAI/
    ├── training/
    │   └── BuildGuardAI_training.zip
    ├── dataset/
    │   └── CubiCasa5K_processed.zip
    └── checkpoints/
```
Upload the two `.zip` files from `BuildGaurdAI\colab_package\` into their respective folders.

### Step 2: Open and Run the Notebook in Google Colab
1. Go to [Google Colab](https://colab.research.google.com/).
2. Click **Upload** and upload `BuildGuardAI_Colab_Training.ipynb` from this folder.
3. In the Colab menu, click **Runtime** → **Change runtime type** → select **T4 GPU** → click **Save**.
4. Run all cells sequentially (**Runtime** → **Run all**).

The training will run on the NVIDIA GPU using Mixed Precision (FP16):
- Training speed: ~1 to 1.5 minutes per epoch (instead of 85+ minutes on local CPU).
- All 20 epochs complete in ~25 minutes.
- Checkpoints are saved automatically after each epoch directly into your Google Drive at `BuildGuardAI/checkpoints/latest_checkpoint.pt`.
- The best model (highest validation mIoU) is saved as `BuildGuardAI/checkpoints/floorplan_unet_gpu_candidate.pt`.

### Step 3: Bring the Model Back to Your Local Machine
Once Colab finishes:
1. Download `floorplan_unet_gpu_candidate.pt` and `gpu_test_metrics.json` from your Google Drive `BuildGuardAI/checkpoints/` folder.
2. Place them into your local project:
   - Put checkpoint in: `BuildGaurdAI\backend\models\floorplan_unet_gpu_candidate.pt`
   - Put metrics in: `BuildGaurdAI\data\processed\cubicasa\gpu_test_metrics.json`
3. If the test metrics improve upon the previous 10.4% mIoU benchmark, rename/replace `backend\models\floorplan_unet.pt` with this new model.
