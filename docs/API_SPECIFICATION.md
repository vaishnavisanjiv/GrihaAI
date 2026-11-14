# API reference

The live OpenAPI schema is served at `http://localhost:8000/docs`; ReDoc is at
`http://localhost:8000/redoc`. The API prefix is `/api` (not `/api/v1`).

Protected endpoints require `Authorization: Bearer <access_token>`. Register
with JSON `{ "email", "name", "password" }`. Login is form-encoded and accepts
`username` (the email) and `password`.

## Routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | API status and docs path. |
| `GET` | `/api/health/` | Liveness. |
| `GET` | `/api/health/ready` | Database readiness. |
| `POST` | `/api/auth/register` | Create an account. |
| `POST` | `/api/auth/login` | Get a bearer token. |
| `GET` | `/api/auth/me` | Current account. |
| `GET`, `POST` | `/api/projects/` | List or create projects. |
| `GET`, `PUT`, `DELETE` | `/api/projects/{project_id}` | Read, update, or delete an owned project. |
| `GET` | `/api/projects/{project_id}/summary` | Project summary. |
| `GET` | `/api/floor-plans/` | List owned plans. |
| `POST` | `/api/floor-plans/upload` | Multipart upload: `project_id`, `file`. |
| `POST` | `/api/floor-plans/{floor_plan_id}/process` | Create preview and image metadata. |
| `GET` | `/api/floor-plans/{floor_plan_id}` | Plan metadata. |
| `GET` | `/api/floor-plans/{floor_plan_id}/image` | Original uploaded file. |
| `PUT` | `/api/floor-plans/{floor_plan_id}/scale` | Set scale using two pixel points and known millimeters. |
| `POST` | `/api/analysis/{floor_plan_id}/start` | Start trained model analysis; returns `503` if no checkpoint is installed. |
| `GET` | `/api/analysis/{analysis_id}` | Summary, rooms, elements, findings, image dimensions, and model version/checkpoint SHA-256 when available. |
| `GET` | `/api/analysis/{analysis_id}/elements` | Detected elements. |
| `GET` | `/api/analysis/{analysis_id}/rooms` | Detected room components. |
| `GET` | `/api/analysis/{analysis_id}/graph` | Stored spatial candidates, including review history. |
| `PUT` | `/api/analysis/{analysis_id}/graph/{edge_id}/review` | Append an owner’s `plausible`, `not_plausible`, or `uncertain` review decision to the candidate history. Does not verify connectivity. |
| `GET` | `/api/analysis/{analysis_id}/compliance` | Stored rule results. |
| `GET` | `/api/analysis/{analysis_id}/recommendations` | Recommendations for warnings/failures. |
| `GET` | `/api/reports/{analysis_id}` | JSON report. |
| `GET` | `/api/reports/{analysis_id}/download` | PDF report. |
| `POST` | `/api/assistant/{analysis_id}/ask` | Ask a question using local prototype guidance. |

## Manual PowerShell flow

Run after the backend is started. Register once; skip registration for an
existing account.

```powershell
$api = 'http://localhost:8000'
$email = 'you@example.com'
$password = 'replace-with-your-password'

Invoke-RestMethod -Method Post -Uri "$api/api/auth/register" `
  -ContentType 'application/json' `
  -Body (@{ email = $email; name = 'Your Name'; password = $password } | ConvertTo-Json)

$login = Invoke-RestMethod -Method Post -Uri "$api/api/auth/login" `
  -ContentType 'application/x-www-form-urlencoded' `
  -Body @{ username = $email; password = $password }
$headers = @{ Authorization = "Bearer $($login.access_token)" }

$project = Invoke-RestMethod -Method Post -Uri "$api/api/projects/" `
  -Headers $headers -ContentType 'application/json' `
  -Body (@{ name = 'Plan review'; building_type = 'residential'; jurisdiction = 'Your jurisdiction' } | ConvertTo-Json)

$upload = curl.exe -sS -X POST "$api/api/floor-plans/upload" `
  -H "Authorization: Bearer $($login.access_token)" `
  -F "project_id=$($project.id)" -F "file=@C:\path\to\floor-plan.png" |
  ConvertFrom-Json

# Calibrate before analysis when metric room dimensions are needed.
$scale = @{
  x1 = 100; y1 = 100
  x2 = 500; y2 = 100
  known_distance_mm = 4000
} | ConvertTo-Json
Invoke-RestMethod -Method Put `
  -Uri "$api/api/floor-plans/$($upload.id)/scale" `
  -Headers $headers -ContentType 'application/json' -Body $scale

$analysis = Invoke-RestMethod -Method Post `
  -Uri "$api/api/analysis/$($upload.id)/start" -Headers $headers
Invoke-RestMethod -Uri "$api/api/analysis/$($analysis.id)" -Headers $headers
```

Use image coordinates from the original uploaded image. Analysis requires the
trained checkpoint at `backend/models/floorplan_unet.pt`; without it, the start
request returns `503`. Existing uploads can be retried from the upload page
after model installation.

The analysis summary includes `spatial_edges`. These are geometry-derived
`ADJACENT_TO_CANDIDATE` and `PROXIMATE_TO` records, not verified connections
or egress paths. Each record includes `properties_json` with source/target
node types, pixel-distance evidence, an uncalibrated score, and
`review_required: true`. The analysis graph endpoint returns the same
relationship records.
