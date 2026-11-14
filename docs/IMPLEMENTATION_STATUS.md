# Implementation status

## Working

- FastAPI authentication, project and floor-plan upload APIs.
- SQLite by default; PostgreSQL can be configured manually.
- PNG/JPG/WEBP and PDF upload support. PDF conversion requires Poppler.
- User scale calibration from two original-image pixel coordinates and a known
  distance.
- Next.js upload, analysis, report, and assistant screens.
- A compact U-Net training and inference pipeline with CubiCasa5K SVG labels.
- Dataset preparation, seeded train/validation/test splitting, split checking,
  checkpoint selection using validation mIoU, and held-out test reporting.
- Dataset preparation records source image dimensions and writes structured
  exclusion reports. The dataset statistics script reports class frequencies,
  dimensions, split composition, and exclusions.
- Training defaults to the full train/validation splits and uses AdamW,
  validation-based learning-rate scheduling, early stopping, gradient
  clipping, and CUDA-only mixed precision. Evaluation reports per-class
  precision/recall/F1/Dice, a confusion matrix, checkpoint SHA-256, and
  qualitative overlays for the lowest-scoring test samples.
- Analysis derives and stores only conservative, geometry-proximity
  relationship candidates. Each candidate records source/target node types,
  pixel-distance evidence, uncalibrated minimum model score, and a required
  manual-review flag. The analysis summary API and UI expose these candidates
  with explicit non-connectivity/non-egress caveats.
- Analysis owners can record a `plausible`, `not_plausible`, or `uncertain`
  review decision for a spatial candidate. Decisions are append-only and
  auditable by user ID and timestamp; the analysis response returns the review
  history. A review does not mark the relationship as verified.
- Completed model analyses persist the checkpoint SHA-256 with architecture
  and epoch in the existing model-version field. The analysis UI and reports
  expose that provenance; analysis also fails if the checkpoint changes while
  it is being loaded.
- Frontend detection scores are now labeled as uncalibrated model scores,
  rather than calibrated confidence percentages.
- The trainer now displays a per-batch progress bar and atomically updates an
  ignored progress JSON file for monitoring future runs.
- Analysis fails with `503` when the trained model checkpoint is absent.
- The workspace-local checkpoint was produced by a one-epoch CPU smoke
  test limited to 100 training and 20 validation samples. It is not trained
  sufficiently for reliable room or element detections.
- The current rule engine marks code checks `NOT_ASSESSED`; it does not claim
  NBC, Maharashtra UDCPR, PMC, or PCMC compliance. Reports contain no
  compliance score.
- The latest verification after the current review-history and provenance
  changes is in progress. Prior validation passed 44 backend tests, the
  frontend production build, and lint for the modified analysis page.
  Full-project ESLint still reports the existing issue in the unchanged
  `frontend/src/components/AppShell.tsx` effect
  (`react-hooks/set-state-in-effect`).
- The local CubiCasa5K extraction was prepared into 4,992 image/mask pairs;
  eight annotations without supported room polygons were skipped. The
  deterministic split contains 3,494 train, 749 validation, and 749 test
  samples, and the strengthened dataset validator passed. The local
  statistics report shows the reserved `railing` class has zero labeled
  pixels; it is therefore excluded from reported detections. The manifest has
  been regenerated and now records original dimensions for all 4,992 samples.

## Not yet verified or incomplete

- The current checkpoint has a held-out mean IoU of 7.3% and pixel accuracy of
  29.4%. These results are not adequate for reliable plan interpretation; the
  checkpoint must be retrained on the full training split and evaluated before
  relying on detections.
- SVG parsing and label mapping succeeded across the extracted annotations,
  but prediction quality and label correctness still require visual review.
  The full training job has not been run with the improved training controls.
  It remains deferred: the latest Windows host check showed approximately
  0.73 GiB free of 7.33 GiB physical memory and no CUDA GPU. A full 512×512 CPU
  run risks exhausting system memory.
- The eight excluded source SVGs were inspected: none contains a `Space` group,
  so these do not appear recoverable by adjusting polygon traversal. Source
  images are present for all eight.
- The saved evaluation JSONs contain aggregate metrics only. No qualitative
  failure-case overlays have been generated in this workspace; generating the
  lowest-scoring overlays requires evaluating the 749-plan test set again.
- Predicted components are not a validated building-plan vectorization or
  room-adjacency solution. Stored adjacency/proximity entries are candidates,
  not verified relationships, connectivity, or egress paths.
- No verified, versioned NBC/local-authority rule catalog is implemented.
  Code findings remain `NOT_ASSESSED`; they must not be used for design
  approval or official submission. Official source portals identified for
  future work are recorded in [Limitations](LIMITATIONS.md), but no provisions
  have yet been transcribed, legally reviewed, or encoded.
- The assistant uses local keyword-matched guidance; it does not call an
  external LLM or perform building-code retrieval from a verified source.

## Next steps

1. When adequate RAM or a compatible GPU is available, retrain using the full
   training split to a separate candidate checkpoint, then evaluate it on the
   held-out test split without using test results for tuning.
2. Once evaluation is safe, generate and inspect failure-case overlays for
   the candidate model.
3. Validate on plans representative of the intended region and define
   jurisdiction-specific rules before making compliance claims.
