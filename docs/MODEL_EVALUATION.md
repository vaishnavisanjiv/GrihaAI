# Model evaluation

The training script chooses a checkpoint using validation mean intersection
over union (mIoU). The separate evaluator reports metrics on the held-out test
split:

- pixel accuracy;
- mIoU across classes present in the evaluated split;
- per-class IoU;
- per-class and macro precision, recall, F1, and Dice;
- the full confusion matrix (rows are ground-truth classes; columns are
  predicted classes);
- sample and pixel counts, checkpoint epoch, device, and evaluation time.
- checkpoint SHA-256 and qualitative original/ground-truth/prediction overlays
  for the lowest per-plan test mIoU examples.

The JSON result is written to
`data/processed/cubicasa/test_metrics.json`. The test split must not be used
for checkpoint selection. Review per-class metrics and skipped annotations;
pixel accuracy alone can overstate performance when background dominates.
Overlays are saved to `data/processed/cubicasa/qualitative/`; pass
`--overlay-count 0` to the evaluator to skip generating them.

Generated checkpoints and test metrics are excluded from Git and may not be
available in another checkout. The current local smoke checkpoint scored 7.3%
held-out mIoU and 29.4% pixel accuracy; these results are inadequate for
reliable plan interpretation. These segmentation metrics do not validate room
adjacency or building-code compliance. BuildGuard currently has no verified,
versioned NBC or local-authority rule catalog; its plan reports therefore
mark code checks `NOT_ASSESSED` and must not be submitted as compliance
evidence.
