# Dataset and generated data

The model pipeline uses **CubiCasa5K**, a floor-plan dataset with dense SVG
annotations. The archive is approximately 5.47 GB and is not included in this
repository. Download it from the
[official Zenodo record](https://doi.org/10.5281/zenodo.2613548). The dataset
license is **CC BY-NC-SA 4.0**; review the terms before training or sharing
derived data or model weights.

## Local layout

- `raw/cubicasa5k.zip`: verified archive (ignored by Git).
- `raw/cubicasa5k/`: extracted source annotation and image files (ignored).
- `processed/cubicasa/`: prepared images/masks, manifests, splits, and metrics
  (ignored).

To download with the provided script from the repository root:

```powershell
.\backend\venv\Scripts\python.exe scripts\download_dataset.py --download
```

After the download completes, extract it. This verifies and reuses an existing
archive; it does not download it again:

```powershell
.\backend\venv\Scripts\python.exe scripts\download_dataset.py --extract
```

If downloaded elsewhere, copy the complete archive to `data/raw/cubicasa5k.zip`
and run the extraction command above. The script verifies the archive's
published checksum and reuses it without re-downloading. Then run preparation,
split validation, training, and held-out evaluation as shown in the root
README. Do not commit the archive, extracted dataset, prepared data, or trained
checkpoint.
