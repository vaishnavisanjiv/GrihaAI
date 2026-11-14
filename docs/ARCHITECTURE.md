# Architecture

## Runtime

```text
Next.js browser app
       │ REST requests with bearer JWT
       ▼
FastAPI ─── SQLAlchemy ─── SQLite (default) / configured PostgreSQL
   │
   ├── Local uploaded files and PDF previews
   ├── Required PyTorch U-Net checkpoint for plan analysis
   ├── OpenCV connected-component polygons
   ├── Prototype deterministic rule checks
   ├── JSON/PDF reports
   └── Local keyword-based assistant guidance
```

The frontend and backend run as separate development servers. The backend
stores uploaded files under `STORAGE_PATH` (default `backend/storage` when
started from `backend/`) and loads the checkpoint from `CV_MODEL_PATH`
(default `backend/models`).

## Analysis path

1. An authenticated user uploads an image or PDF to a project.
2. `POST /api/analysis/{floor_plan_id}/start` verifies ownership and requires
   `floorplan_unet.pt`.
3. The segmentation model predicts 13 semantic classes. Connected components
   are converted to polygon records; metric measurements are only available
   after user scale calibration.
4. Shapely/STRtree and NetworkX derive conservative, pixel-distance-based
   adjacency and door-proximity candidates from valid predicted polygons.
   Candidates record their geometry evidence, uncalibrated minimum model
   score, and `review_required`; they do not assert room connectivity, door
   association, egress, or path availability.
5. The prototype rule engine stores `NOT_ASSESSED` findings and the API exposes
   results, relationship candidates, and reports.

Analysis currently executes in the request; it is not a background job queue.
If the checkpoint is unavailable, the API returns `503` and does not create
synthetic analysis records.

## Not implemented

There is no external LLM integration, production vector database, verified
code corpus, validated room topology, reliable path/egress analysis, or
jurisdiction-specific compliance engine. Spatial relationship candidates are
unverified because the segmentation model itself has poor measured quality.
See [limitations](LIMITATIONS.md).
