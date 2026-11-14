# Dataset

The current segmentation training pipeline targets **CubiCasa5K**, a dataset
of 5,000 floor plans with SVG polygon annotations. Its official archive is
approximately 5.47 GB: <https://doi.org/10.5281/zenodo.2613548>.

The dataset license is CC BY-NC-SA 4.0. Review it before downloading,
training, or sharing derived data or weights. Dataset files and model
checkpoints are excluded from Git.

The preparation script expects a `model.svg` beside one of `F1_scaled.png`,
`F1_original.png`, or `F1.png`. It rasterizes a compact set of semantic labels
to 512×512 masks. It records source image dimensions and image/mask provenance
in the manifest. Unsupported/malformed annotations and missing input images
are listed with reasons in `preparation_report.json` and
`prepare_errors.txt`; inspect them and the prepared-plan count before training.

Run `scripts/dataset_statistics.py` after preparing and validating the splits.
It writes `dataset_statistics.json` with per-class pixel frequencies, per-plan
class presence, image/mask dimensions, split statistics, and known exclusions.

The current local report shows the reserved `railing` class has no labeled
pixels. It remains in the checkpoint output schema for compatibility but is
not exposed as an inferred room class. The regenerated manifest now records
original dimensions for all 4,992 prepared plans.

In the current local extraction, preparation produced 4,992 image/mask pairs
and skipped eight annotations that had no supported room polygons. The
3,494/749/749 train/validation/test split passed validation. A CPU
smoke-trained checkpoint has been evaluated locally, with 7.3% held-out mean
IoU and 29.4% pixel accuracy; it is not reliable for plan interpretation.
These generated data, checkpoints, and metrics are ignored by Git and may not
exist in another checkout. Follow [data/README.md](../data/README.md) for
download and extraction, then the training commands in the root README.
