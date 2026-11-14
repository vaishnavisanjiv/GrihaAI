# BuildGuard AI - project handoff

## Project in one paragraph

BuildGuard AI is an academic prototype for reviewing uploaded architectural
floor plans. It combines a Next.js web app, a FastAPI API, local persistence,
and a compact PyTorch U-Net segmentation pipeline trained from CubiCasa5K.
The intended flow is to create a project, upload a plan, inspect preliminary
detected geometry, and download a report. It is **not** a code-compliance
approval system: all code checks are `NOT_ASSESSED`, model geometry is
unverified, and the currently evaluated checkpoint is too inaccurate for
reliable interpretation.

## Current implementation

### Product workflow

- Account registration and login; protected API routes use bearer JWTs.
- Create, list, view, update, and delete user-owned projects.
- Upload and process floor plans; documented supported formats are PNG, JPG,
  WEBP, and PDF. PDF conversion requires Poppler on the backend `PATH`.
- Calibrate drawing scale using two image coordinates and a known real-world
  distance.
- Start a model analysis, then view the analysis summary, detected rooms and
  elements, findings, and recommendations.
- Record a `plausible`, `not_plausible`, or `uncertain` review decision on a
  spatial relationship candidate. This records user feedback only; it does
  not verify connectivity or remove the professional-review caveat.
- Retrieve JSON reports and download PDF reports.
- Ask questions through an in-app assistant. Its responses are local,
  keyword-based guidance, not responses from an external LLM.

### Analysis and data pipeline

- The project includes data download, SVG annotation preparation, deterministic
  train/validation/test splitting, split validation, model training, and
  held-out evaluation scripts under `scripts/`. A dataset statistics report
  summarizes labels, dimensions, split distribution, and recorded exclusions.
- Dataset preparation now writes source dimensions and structured skip reasons.
  Training reads only train/validation samples; it uses AdamW, validation-mIoU
  checkpoint selection, learning-rate scheduling, early stopping, gradient
  clipping, and CUDA mixed precision when available.
- Completed analyses persist the checkpoint SHA-256 together with architecture
  and epoch, and expose it in the analysis summary/UI and reports. The loader
  checks that the checkpoint file did not change during loading.
- Evaluation now reports per-class precision, recall, F1, Dice, a confusion
  matrix, a checkpoint SHA-256, and lowest per-plan test-IoU overlays.
- The baseline is a compact U-Net predicting 13 semantic labels, including
  background, walls, broad room categories, doors, and windows.
- Predicted components are converted to room/element records and polygon-like
  geometry. Metric measurements depend on user calibration.
- Shapely/STRtree and NetworkX derive conservative room-adjacency and
  door-proximity candidates from predicted polygons; candidates expose
  pixel-distance evidence, uncalibrated score, and required-review flags.
  They are not verified connectivity or egress paths.
- Reports and spatial candidates are available in the analysis summary API
  and UI, but geometry, adjacency, and rule outcomes are not validated
  building-plan interpretations.
- Spatial candidate review decisions are owner-scoped and store the reviewer
  ID and timestamp in an append-only review table; the analysis summary returns
  the review history for each candidate.
- The rule engine deliberately returns `NOT_ASSESSED`; there is no verified,
  versioned NBC or local-authority rule catalog.

## Technology

| Area | Stack |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4 |
| UI and client-side libraries | Axios, React Dropzone, Recharts, Lucide React |
| Backend/API | Python, FastAPI, Uvicorn, Pydantic |
| Persistence | SQLAlchemy, SQLite by default; PostgreSQL can be configured |
| Authentication | JWT bearer tokens, password hashing via Passlib/bcrypt |
| Image/geometry/reporting | Pillow, OpenCV, NumPy, scikit-image, Shapely, NetworkX, ReportLab |
| PDF input | `pdf2image` and external Poppler |
| ML | PyTorch; CubiCasa5K dataset and SVG annotations |
| Tests | Pytest backend suite; frontend ESLint and Next.js build scripts |

No external AI-provider credentials or external database are needed for the
documented local SQLite development setup.

## Maturity and verified status

Do not express project completion as a single percentage: the web/API
foundation is substantially present, while the core model and compliance
claims are not ready for dependable use.

- The documented local dataset preparation yielded 4,992 image/mask pairs;
  eight annotations were skipped because they had no supported room polygons.
- Inspection of all eight skipped annotations confirmed that each source SVG
  contains no `Space` groups; the corresponding source images are present.
  These exclusions are not missed room polygons under the current label
  mapping.
- The documented deterministic split is 3,494 train, 749 validation, and 749
  test samples; the dataset validator passed.
- The generated local statistics report shows `railing` has zero labeled
  pixels; its checkpoint output slot is retained for schema compatibility but
  is no longer exposed as a detected room. The dataset has now been
  regenerated; original image dimensions are recorded for every prepared
  sample.
- The evaluated checkpoint was selected at epoch 1 after a small CPU smoke run
  limited to 100 training and 20 validation samples.
- The saved held-out test result is **7.3% mean IoU** and **29.4% pixel
  accuracy** over 749 test samples. This is inadequate for reliable room or
  element detection.
- Backend tests, changed-page lint, and the frontend production build are being
  rerun after the provenance and review-history changes. Before these changes,
  44 backend tests passed and the frontend build and changed-page lint passed.
  Full-project ESLint still reports
  the existing issue in the unchanged `AppShell.tsx` effect
  (`react-hooks/set-state-in-effect`).
- A full training run was not started: the latest local host check showed
  approximately 0.73 GiB free of 7.33 GiB physical memory and no CUDA GPU.
  This is not sufficient headroom for a 512×512 U-Net full-split CPU run.
- Detection and relationship scores are uncalibrated model probabilities;
  the UI labels them as such and requires review.

### Workspace-only files

At the snapshot date, this workspace contains local model files
(`backend/models/floorplan_unet.pt` and
`backend/models/floorplan_unet.experiment.pt`), prepared dataset files, test
metrics, a SQLite database, and uploaded files. These are runtime/local
artifacts, not portable project guarantees: `.gitignore` excludes model
checkpoints, processed/raw data, the local database, and uploads. The saved
metrics refer specifically to `floorplan_unet.pt`; the separate
`floorplan_unet.experiment.pt` has no verified evaluation result in the
available metrics. Another machine or checkout may not contain either model.

The code returns HTTP `503` when its configured checkpoint is missing. Check
the local `CV_MODEL_PATH` and model artifact before assuming analysis can run.

## Main gaps and constraints

1. **Model quality:** current measured performance is poor; no reliable
   measurements or labels should be inferred from its output.
2. **Compliance:** NBC, Maharashtra UDCPR, PMC, and PCMC rules are not encoded
   or verified. There is no compliance score or approval capability.
3. **Geometry:** predicted components are not a validated vectorization,
   adjacency graph, egress, or pathfinding solution.
4. **Assistant:** guidance is keyword-matched and local; there is no external
   LLM integration or verified-code retrieval corpus.
5. **Execution model:** analysis runs synchronously in the API request rather
   than through a background job queue.
6. **Input dependencies:** PDF processing requires a separately installed
   Poppler executable; scale must be calibrated for meaningful metric values.
7. **Use restrictions:** treat results as preliminary research/prototype
   output, not design approval, professional sign-off, or official submission
   evidence.

## Suggested next work, in priority order

1. **Establish a trustworthy model baseline.** Inspect the refreshed dataset
   statistics and exclusion review, then, when adequate memory or a compatible
   GPU is available, train a candidate checkpoint on the full training split.
   Evaluate it on the held-out test split without using test results for model
   selection. The currently saved reports contain aggregate metrics only;
   failure-case overlays have not been generated in this workspace.
2. **Improve model and geometry validation.** Confirm label mappings, validate
   on plans representative of intended users, and measure room-boundary and
   element quality beyond pixel accuracy.
3. **Validate spatial candidates.** Compare stored adjacency/proximity
   candidates against manually reviewed plans; do not infer connected rooms,
   egress, or safety until a separate validated method supports those claims.
4. **Keep compliance explicitly out of scope until sourced and reviewed.** If
   compliance work is approved, first select the exact authority, occupancy,
   code edition, amendments, and authoritative provisions; obtain qualified
   review before encoding rules or changing `NOT_ASSESSED` to a pass/fail state.
5. **Verify the complete user flow.** Run backend tests and frontend lint/build,
   then manually exercise account -> project -> upload -> calibration ->
   analysis -> report using a real sample plan and the intended checkpoint.
6. **Address product reliability after prototype validation.** Consider
   asynchronous analysis jobs, model/version provenance, review/correction of
   detected rooms/elements, operational logging, and deployment/security
   controls. Spatial-candidate review capture exists but is not a full
   detection-editing workflow.

## Useful project map

- `backend/app/api/`: FastAPI routes for authentication, projects, uploads,
  analysis, health, reports, and assistant queries.
- `backend/app/services/`: business logic, preprocessing, model inference,
  geometry, rule checks, reports, and assistant responses.
- `backend/app/models/` and `backend/app/schemas/`: persisted entities and API
  request/response types.
- `frontend/src/app/`: dashboard, login/register, projects, upload, analysis,
  and settings pages.
- `frontend/src/lib/api.ts`: frontend API client.
- `scripts/`: dataset and model pipeline.
- `backend/tests/`: backend automated tests.
- `docs/`: architecture, API, dataset, evaluation, limitations, and status.

For setup, use the [root README](../README.md). The documentation index is
[docs/README.md](README.md); the detailed source-of-truth status is
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md). The API routes are
listed in [API_SPECIFICATION.md](API_SPECIFICATION.md), and non-goals and
authority-specific caveats are in [LIMITATIONS.md](LIMITATIONS.md).

## Prompt to give another AI

> You are helping with BuildGuard AI, an academic floor-plan analysis
> prototype. Read `README.md`, `docs/PROJECT_HANDOFF.md`,
> `docs/IMPLEMENTATION_STATUS.md`, `docs/ARCHITECTURE.md`, and
> `docs/LIMITATIONS.md` before proposing changes. The stack is Next.js 16 /
> React 19 / TypeScript 5 with a Python FastAPI backend, SQLAlchemy (SQLite by
> default), and a compact PyTorch U-Net trained from CubiCasa5K. The app has
> authentication, projects, floor-plan uploads, scale calibration, preliminary
> segmentation, reports, and local keyword-based assistant guidance. The
> evaluated model scores only 7.3% held-out mean IoU and 29.4% pixel accuracy;
> do not treat detections as reliable. Code rules are all `NOT_ASSESSED`: no
> verified NBC or local-authority catalog, compliance score, approval, or
> certification exists. Local model/data/database/upload files are ignored
> artifacts and may not be present in another checkout. First inspect the
> relevant implementation and tests, distinguish verified behavior from
> planned behavior, and recommend the smallest high-value next step. Never
> invent model metrics, code provisions, or compliance results.
