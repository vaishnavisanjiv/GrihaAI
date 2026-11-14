# BuildGuard AI 🛡️
### Intelligent Building Layout Compliance & Architectural Safety Analysis Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Frontend-Next.js%2016-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![PyTorch](https://img.shields.io/badge/Deep%20Learning-PyTorch%20U--Net-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![Standard](https://img.shields.io/badge/Standard-NBC%202016%20Compliant-0284C7)](https://www.bis.gov.in/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Executive Overview

**BuildGuard AI** is an intelligent full-stack architectural analysis platform that automates the screening of 2D floor plans against national building standards. By combining **deep learning computer vision (PyTorch U-Net)**, **computational geometry (OpenCV & Shapely)**, **spatial graph analysis (NetworkX)**, and a **deterministic statutory rule engine**, BuildGuard AI transforms raster architectural drawings into structured, verifiable spatial data.

The system evaluates uploaded drawings against the **National Building Code of India (NBC 2016 Part 3 & Part 4)**, identifying room dimensions, clear corridor widths, partition wall spacing, sanitary clearances, and window ventilation aperture ratios.

---

## ✨ Key Feature Highlights

### 1. 🧠 Deep Learning Semantic Segmentation
* **Architecture:** Custom 13-class PyTorch U-Net with ResNet-style skip connections (`buildguard-unet-v1`).
* **Dataset:** Trained on the **CubiCasa5K** architectural dataset across 20 epochs on NVIDIA GPU via Google Colab.
* **13 Architectural Classes:** Background, Living/Dining, Bedroom, Bathroom/WC, Kitchen, Entry/Hallway, Balcony, Storage, Garage, Other Room, Wall, Door, and Window.
* **Integrity & Provenance:** Checkpoint SHA-256 fingerprint verification on startup guarantees model authenticity.

### 2. 📐 Automated NBC 2016 Compliance Rule Engine
* **Corridor & Passageway Clear Width (Part 3, Clause 4.8 / 12.8):** Measures clear width across all detected circulation routes. Verifies minimum statutory clearance ($\ge 1.00\text{ m}$ for residential units; $\ge 1.25\text{ m}$ for main access corridors).
* **Space Between Opposing Walls & Shafts (Part 3, Clause 4.9 & 8.2):** Computes perpendicular clear spans between partition walls, verifying minimum $1.00\text{ m}$ passage clearance and $\ge 1.20\text{ m}$ for ventilation/light shafts.
* **Habitable Room Dimensions (Part 3, Clause 4.1):** Checks bedrooms and living rooms for minimum clear width ($\ge 2.40\text{ m}$) and carpet area ($\ge 9.50\text{ m}^2$).
* **Kitchen Dimensions & Clearances (Part 3, Clause 4.2):** Validates kitchen width ($\ge 1.80\text{ m}$) and minimum floor area ($\ge 4.50\text{ m}^2$).
* **Sanitary Facility Dimensions (Part 3, Clause 4.4):** Verifies combined bathroom/WC ($\ge 1.80\text{ m}^2$, width $\ge 1.20\text{ m}$) and independent water closet dimensions ($\ge 1.10\text{ m}^2$, width $\ge 0.90\text{ m}$).
* **Doorway Clear Opening Widths (Part 3, Clause 4.7 / 12.7):** Evaluates detected door aperture leaves: main entrance ($\ge 1.00\text{ m}$), habitable rooms ($\ge 0.90\text{ m}$), and bathrooms ($\ge 0.75\text{ m}$).
* **Ventilation & Daylight Aperture Ratio (Part 3, Clause 4.10):** Checks aggregate window glazed area against habitable room floor space ($\ge 10\%$ ratio / 1:10).
* **Staircase & Egress Capacity (Part 3, Clause 4.9):** Validates internal residential stair flight clear width ($\ge 1.00\text{ m}$).

### 3. 📏 Interactive Scale Calibration Modal
* **1-Click Architectural Presets:** Calibrates scale automatically using detected door openings (e.g. Standard Main Door = $1.00\text{ m}$, Room Door = $0.90\text{ m}$, Bath Door = $0.75\text{ m}$).
* **Known Room Dimension:** Select any detected room and input known site measurements in metres.
* **Custom Pixel Ratio:** Specify drawing scale directly in pixels per metre ($px/m$).
* **Instant Dynamic Recalculation:** Updates all room areas ($m^2$), widths, lengths, and re-evaluates all NBC checks immediately without page refresh.

### 4. 🗺️ Spatial Overlay Board & Vector Visualization
* **4 View Modes:** Composite Overlay, Rooms Only, Architectural Elements Only, and Original Plan.
* **Interactive Controls:** Smooth canvas pan, zoom ($50\% - 300\%$), fullscreen toggle, centroid labels, and opacity slider.
* **Interactive Class Legend:** Per-class toggle to show/hide specific room categories or structural elements.

### 5. 🕸️ Spatial Relationship Graph (NetworkX)
* Computes geometric adjacency (under $1.5\text{ px}$ separation) and proximity relationships.
* **Human-in-the-Loop Audit Trail:** Review candidates with *Seems Plausible*, *Seems Incorrect*, or *Unsure* decisions stored persistently in the database.

### 6. 📄 Professional Architectural ReportLab PDF Export
* Generates multi-page vector PDF reports embedding high-resolution plan visualizations, executive summary metric cards, room area schedules, element tables, and the statutory compliance matrix.

### 7. 🤖 Grounded Context-Aware AI Assistant
* Built-in assistant answers real questions (e.g., *"Is corridor width correct?"*, *"Is the space between two walls compliant?"*) using live database records and statutory NBC 2016 clauses.

---

## 🏗️ System Architecture & Tech Stack

```text
BuildGuard AI Architecture
┌────────────────────────────────────────────────────────┐
│               Next.js 16 (React 19) Frontend            │
│    App Router · Tailwind CSS · Lucide Icons · Axios    │
└───────────────────────────┬────────────────────────────┘
                            │ REST API / JWT Auth
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Python Backend                │
│    Uvicorn · Asynchronous Task Runner · Pydantic v2    │
└──────┬────────────────────┬────────────────────┬───────┘
       │                    │                    │
┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼───────┐
│ PyTorch U-Net│     │OpenCV/Shapely│     │  Rule Engine │
│Segmentation │      │CV Contours  │      │  (NBC 2016)  │
│  (13 Classes)│     │Spatial Graph│      │PASS/FAIL/WARN│
└─────────────┘      └─────────────┘      └──────────────┘
```

| Layer | Technologies | Purpose |
|:---|:---|:---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS | Modern dashboard, interactive canvas viewer, review hub |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn | Async background analysis, RESTful endpoints, JWT auth |
| **Computer Vision** | OpenCV, NumPy, Shapely, Pillow | Image pre-processing, morphological closing, polygon extraction |
| **Deep Learning** | PyTorch, torchvision, Albumentations | 13-class semantic segmentation U-Net trained on CubiCasa5K |
| **Graph Analysis** | NetworkX | Room adjacency and spatial topology candidate generation |
| **Database** | SQLite / SQLAlchemy ORM (PostgreSQL ready) | Persistent storage for users, projects, plans, and audits |
| **PDF Generation** | ReportLab | Publication-quality multi-page architectural review reports |

---

## 📁 Repository Directory Structure

```text
BuildGaurdAI/
├── backend/
│   ├── app/
│   │   ├── api/                 # Route handlers (auth, floor_plans, analysis, reports, assistant)
│   │   ├── core/                # Configuration, database setup, JWT security
│   │   ├── models/              # SQLAlchemy database models (User, Project, Room, Compliance)
│   │   ├── schemas/             # Pydantic validation schemas
│   │   └── services/            # Model inference, CV parser, rule engine, spatial graph
│   ├── models/
│   │   ├── floorplan_unet.pt    # Active PyTorch 13-class trained model weights (~24.9 MB)
│   │   └── README.md            # Weights provenance and architecture notes
│   ├── tests/                   # Pytest automated test suite (51 unit & integration tests)
│   ├── requirements.txt         # Core backend dependencies
│   ├── requirements-ml.txt      # PyTorch, torchvision, opencv dependencies
│   └── Dockerfile               # Production container image definition
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages (login, dashboard, upload, analysis)
│   │   ├── components/
│   │   │   ├── analysis/        # Dashboard components (Header, Viewer, Rooms, Compliance)
│   │   │   └── ui/              # Reusable UI primitives (Card, Button, Badge)
│   │   └── lib/                 # Axios API client with automatic JWT token injection
│   ├── package.json             # Frontend dependencies & scripts
│   └── tsconfig.json            # TypeScript configuration
├── colab_package/
│   ├── BuildGuardAI_Colab_Training.ipynb  # GPU training notebook for Google Colab
│   └── README.md                # Cloud training instructions
├── docs/                        # Architecture, API specifications, and handoff documentation
├── sample_plans/                # 5 diverse real-world test floor plans from CubiCasa5K
├── scripts/                     # Dataset download, preparation, and training utilities
├── .gitignore                   # Comprehensive repository ignore rules
├── docker-compose.yml           # Multi-container local orchestration
└── README.md                    # Project documentation
```

---

## 🚀 Step-by-Step Guide to Run the Project

The application runs as a decoupled full-stack architecture. Open **two terminal windows**:

### Step 1: Start the FastAPI Backend

Open a terminal in the project directory:

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# Install dependencies (only on first setup)
pip install -r requirements.txt
pip install -r requirements-ml.txt

# Start FastAPI server with live reload
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

* **Backend API:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive API Docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **API Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

### Step 2: Start the Next.js Frontend

Open a second terminal window:

```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies (only on first setup)
npm install

# Start Next.js development server
npm run dev
```

* **Web Application:** [http://localhost:3000](http://localhost:3000)

---

### Step 3: Using the Application

1. Open **[http://localhost:3000](http://localhost:3000)** in your browser.
2. **Log In:** Register a new account or sign in with default test credentials:
   * **Email:** `sayaliyadav16@gmail.com`
   * **Password:** `password123`
3. **Upload or Select a Plan:**
   * Go to **Upload Layout**.
   * You can upload your own image (`PNG`, `JPG`, `WEBP`) or click **"Select for Test"** on any of the pre-bundled sample plans.
4. **Run Analysis:**
   * Click **Start Review**.
   * The PyTorch U-Net model runs semantic segmentation in the background while real-time polling tracks status.
5. **View Results & Calibrate Scale:**
   * Inspect the **Spatial Overlay Board** to see rooms, doors, and walls.
   * Click **"Calibrate Scale"** in the header or compliance panel (e.g. choose *Main Entrance Door = 1.00 m*).
   * **Watch the results update instantly:** real corridor widths, wall-to-wall clearances, and room carpet areas will be checked against NBC 2016 norms with clear green **PASS** or red **FAIL** badges.
6. **Export Findings:** Click **Download PDF** to export a multi-page architectural compliance report.

---

## 📥 Sample Test Floor Plans

The repository bundles 5 real-world architectural plans from the CubiCasa5K held-out benchmark split in `sample_plans/`:

| File | Description | Recommended Reference Door |
|:---|:---|:---|
| `01_large_architectural_villa.png` | Multi-room villa with bedrooms, baths & living hall | Main double door ($1.20\text{ m}$) |
| `02_compact_residential_apartment.png` | Compact 1-BHK studio layout with corridor & bath | Entry door ($1.00\text{ m}$) |
| `03_modern_family_home.png` | Suburban home with dining, kitchen & patio | Front entrance ($1.00\text{ m}$) |
| `04_multi_room_duplex.png` | Duplex unit with interior partition walls | Internal room door ($0.90\text{ m}$) |
| `05_two_bedroom_flat.png` | 2-BHK apartment with balconies & kitchen | Living room door ($0.90\text{ m}$) |

---

## 🧪 Testing & Verification

Run backend unit and integration tests:

```powershell
cd backend
python -m pytest tests/test_rule_engine.py tests/test_spatial_service.py -v
```

Run frontend TypeScript typecheck and ESLint:

```powershell
cd frontend
npm run lint
npx tsc --noEmit
```

---

## 🔮 Future Scope & Roadmap

1. **BIM / IFC (Industry Foundation Classes) Ingestion:** Expand beyond 2D raster drawings to ingest 3D IFC and Revit files directly via `ifcopenshell`.
2. **Municipal Development Control Regulation (DCR) Catalogs:** Introduce regional municipal bylaw modules for Indian metropolitan authorities (e.g. BMC Mumbai, BBMP Bengaluru, PMRDA Pune, DDA Delhi).
3. **3D Point Cloud & LiDAR Scan Reconstruction:** Integrate iPhone LiDAR / matterport point clouds to verify ceiling heights and volume compliance.
4. **Generative Layout Optimization:** Recommend layout revisions using constrained diffusion models to auto-widen narrow corridors or reconfigure partition walls to achieve 100% compliance.
5. **Automated Fire Life-Safety (NBC Part 4) Egress Simulation:** Agent-based evacuation simulation computing exact travel distances to external fire escape staircases.

---

## 👥 Authors & Academic Context

* **Project:** B.Tech Final Year Capstone Project
* **Title:** BuildGuard AI – An Intelligent Building Layout Compliance and Safety Analysis Platform
* **Supervision:** Department of Computer Engineering & Information Technology
* **License:** [MIT License](LICENSE)
