# Workflow Spec Builder — Full Process, Step Definitions, and Output Specification (v2)

This document contains the complete 7-stage process, step field definitions, data acquisition rules, validation rules, output format, and **pipeline config YAML schema** for the Experiment Workflow Designer agent. The agent's system prompt references this file. Read it in full before beginning any workflow design.

---

## Detailed Process

### Stage 1 — Handoff Package Review

Ingest the handoff package from the Feasibility Mapper. Verify your understanding by confirming:
- RQ text, H₀/H₁, variables, and context constraints
- Every requirement in the feasibility matrix and its status
- Confirmed tools with versions and access points
- Confirmed data sources with endpoints
- Compute resources available
- Risks, assumptions, and outstanding action items

If you detect any inconsistency (e.g., a requirement marked Available but no tool listed), flag it immediately. Pause for human confirmation: "Is my understanding correct and complete?"

### Stage 2 — Experiment Design

Design the overall analytical approach before any step-level detail:
- Identify the analytical goal: what must the experiment produce to test H₀ vs H₁?
- Select the primary modeling approach based on confirmed tools (Tier 1/2/3 or Non-Prithvi)
- Trace the data flow: raw inputs → transformations → model outputs → analysis → results
- Sketch the validation strategy: what metrics, what ground truth, what constitutes success
- Identify decision points that become human checkpoints or unresolved decisions
- Assess complexity: straightforward (8–12 steps) vs complex (15–20+ steps)
- **Identify events needed: how many, what regions, what hazard types**

Produce the Experiment Design Narrative (500–1000 words) covering: study objective, approach and justification, key data sources, modeling approach, validation strategy, assumptions, expected outcomes under H₁ vs H₀. Pause for human approval before proceeding.

### Stage 3 — Event Specification & Screening (NEW)

Before workflow decomposition, confirm the study events:

**3a. Collect event parameters** — for each event, confirm:
- Event ID (user-assigned or from catalog)
- Region (US / Europe / Canada / Other — determines baseline products)
- Bounding box [west, south, east, north] in EPSG:4326
- Hazard date (flood date, fire date)
- Hazard type (flood / burn)

**3b. Screen crop dates** — for each event:
- Run `screen_crop_dates.py` or manually confirm 3 pre-hazard HLS dates
- Requirements: ≥70% clear pixels, ≥70-day gaps, excludes cloud/shadow/snow
- Dates labeled T1 (early), T2 (mid), T3 (late)
- Prefer Sentinel-2 (HLSS30) over Landsat (HLSL30) for crop classification

**3c. Verify flood/burn HLS availability** — confirm HLS overpass on or near hazard date:
- Search both HLSS30 and HLSL30 for exact date
- If neither available, select nearest pass (document deviation)

**3d. Determine baseline products per region:**

| Region | Flood Baseline | Crop Baseline | NDVI Source |
|--------|---------------|---------------|-------------|
| US (CONUS) | OPERA DSWx-HLS + GFM | USDA CDL | MOD13A1 + VNP13A1 |
| Europe | OPERA DSWx-HLS + GFM | EUCROPMAP + CLMS | MOD13A1 + VNP13A1 |
| Canada | OPERA DSWx-HLS + GFM | AAFC Annual Crop | MOD13A1 + VNP13A1 |
| Other | OPERA DSWx-HLS + GFM | (none available) | MOD13A1 + VNP13A1 |

GFM is ALWAYS downloaded for flood events regardless of region (Sentinel-1 based, 2017+).

Pause for human review of events and dates.

### Stage 4 — Workflow Decomposition

Break the approved design into atomic, ordered workflow steps (same as previous Stage 3):

1. List all confirmed data sources → create one Data Acquisition step per dataset
2. Identify preprocessing needs → create Preprocessing steps
3. Define model execution steps → Model Inference (Tier 1) or Fine-Tuning sequence
4. Define analysis steps → statistical operations, aggregations, hypothesis testing
5. Define validation steps → ground truth acquisition, metric computation
6. Define output generation steps → maps, tables, figures
7. Assign dependencies and check for circular dependencies
8. Verify completeness: every R-ID covered
9. Verify ordering: every input exists as a prior output

**Each step: 13 fields** (Step ID, Name, Type, Serves Requirement, Inputs, Outputs, Tool/Method, Parameters, Dependencies, Parallelizable, Duration, Failure Modes, Human Checkpoint).

### Stage 5 — Data Acquisition Planning

Same as previous Stage 4. Per dataset: 11 fields.

**US-only datasets (skip for non-US events):** CDL, NLCD, USDA NASS, GridMET
**Global datasets:** MOD13A1, VNP13A1, OPERA DSWx, NASA DEM
**Europe-only:** EUCROPMAP, CLMS Crop Types
**Canada-only:** AAFC Annual Crop Inventory

### Stage 6 — Validation Planning

Same as previous Stage 5. Include NDVI severity comparison when applicable.

### Stage 7 — Final Compilation + Config YAML Generation (UPDATED)

Compile the complete workflow specification with **10 sections** in fixed order:

Sections 1-9 same as before (Narrative, Steps, Data Plan, Validation, Risk, Decisions, Traceability, Directory, Audit).

**Section 10 — Pipeline Config YAML** (NEW): Generate the machine-readable config file. Schema defined below in "Pipeline Config YAML Schema".

---

## Pipeline Config YAML Schema

The config YAML is the primary input to `pipeline_executor.py`. It must follow this exact schema:

```yaml
# ─── RESEARCH QUESTION ───
rq:
  text: "<full RQ text>"
  h0: "<null hypothesis>"
  h1: "<alternative hypothesis>"

# ─── EVENTS ───
# Option A: catalog events
events:
  source: flood_catalog  # or burn_catalog
  catalog_path: /rhome/vkolluru/AKD/CLSW_new/event_database/flood_events_catalog.csv
  filters:
    event_ids: [NOAA_EP_183571]  # specific IDs
    # OR filter by attributes:
    # state: [IL, SD]
    # min_cropland_pct: 20
    # year_range: [2023, 2025]
  max_events: 5

# Option B: custom events
events:
  source: custom
  custom_events:
    - event_id: "SD_SIOUX_2024"
      name: "Descriptive name"
      state: "SD"
      hazard_type: "flood"  # or "burn"
      bbox: [-97.15, 42.50, -96.41, 43.14]  # [west, south, east, north] EPSG:4326
      flood_date: "2024-06-24"  # exact HLS overpass date
      crop_dates: ["2024-02-11", "2024-04-13", "2024-06-16"]  # 3 pre-hazard dates
      start_date: "2024-06-24"
      end_date: "2024-06-24"
    
    - event_id: "SPAIN_VALENCIA_2024"
      name: "Valencia DANA Flood"
      state: "Valencia"
      hazard_type: "flood"
      bbox: [-0.45, 39.15, -0.32, 39.47]
      flood_date: "2024-10-30"
      crop_dates: ["2024-03-05", "2024-05-30", "2024-08-10"]
      start_date: "2024-10-30"
      end_date: "2024-10-30"
  max_events: 10

# ─── PRITHVI MODELS ───
prithvi:
  burn: false       # set true if burn events exist
  flood: true       # set true if flood events exist
  crop: true        # always true for crop-damage RQs
  flood_checkpoint: /rhome/vkolluru/r2o/r2o_flood/Prithvi-EO-2.0-300M-TL-Sen1Floods11/Prithvi-EO-V2-600-Sen1Floods11.pt
  crop_checkpoint: /rhome/vkolluru/r2o/r2o_crop/scripts/best-epoch=117_ep120.ckpt
  # burn_checkpoint: /rhome/rshinde/r2o/burnscars/burn_scar_v2/ckpt/mr01eo-workshop.ckpt
  # burn_config: /rhome/rshinde/r2o/burnscars/burn_scar_v2/configs/config.yaml

# ─── BASELINES (auto-selected by region, these are triggers) ───
baselines:
  flood: opera_dswx   # OPERA + GFM always downloaded
  crop: cdl            # CDL for US, EUCROPMAP+CLMS for Europe, AAFC for Canada

# ─── PHASE 1 DATASETS (downloaded per event) ───
datasets:
  # US events: all of these
  # Non-US events: cdl, nlcd, usda_nass, gridmet auto-skipped
  - cdl              # USDA Cropland Data Layer (US only, annual)
  - mod13a1          # MODIS NDVI (global, 16-day) — for NDVI severity
  - vnp13a1          # VIIRS NDVI (global, 8-day rolling) — for NDVI severity
  - opera_dswx       # OPERA DSWx-HLS (global, per HLS overpass)
  - usda_nass        # USDA NASS county yields (US only, annual)
  - gridmet          # GridMET meteorology (US only, daily)
  # Optional:
  # - nasa_dem       # Copernicus DEM (downloaded by flood postprocessing)
  # - firms          # Active fire detections (for burn events)
  # - mcd64a1        # MODIS burned area (for burn baseline)

# ─── ANALYSIS ───
analysis:
  comparison:
    - wilcoxon_signed_rank   # non-parametric paired test
    - paired_t_test          # parametric paired test
  effect_size:
    - cohens_d               # standardized effect size
  correction:
    - bh_fdr                 # Benjamini-Hochberg for multiple comparisons
  alpha: 0.05
  paired: true
  # Note: n ≥ 5 events needed for Wilcoxon, n ≥ 3 for t-test
  # With n < 5, descriptive statistics are reported instead

# ─── GFM CREDENTIALS (required for flood events) ───
gfm:
  jrc_email: "user@email.com"
  jrc_password: "password"
  date_range_days: 5   # search window around flood date

# ─── PATHS ───
paths:
  download_script: /rhome/vkolluru/AKD/CLSW_new/scripts/download_all_datasets.py
  statistical_tests: /rhome/vkolluru/AKD/CLSW_new/statistical_tests
  prithvi_modules: /rhome/vkolluru/AKD/CLSW_new/prithvi
  flood_validation: /rhome/vkolluru/AKD/CLSW_new/scripts/flood_validation_v26.py

# ─── OUTPUT ───
output:
  dir: /rhome/vkolluru/AKD/CLSW_new/output/rq{N}_{descriptor}
  maps: true
  figures: true
  tables: true
  report: true
```

### Config Generation Rules

1. **Event dates must be verified** — crop_dates from screening tool or manual confirmation
2. **flood_date must match an HLS overpass** — exact date, no buffer
3. **bbox must be EPSG:4326** — [west, south, east, north]
4. **US-only datasets auto-skipped** for non-US events by the executor
5. **Baselines auto-selected by region** — config just needs the trigger name
6. **GFM section required** if any flood events exist
7. **burn_checkpoint required** if `prithvi.burn: true`
8. **At least 5 events recommended** for statistical tests; 2 events = descriptive only

---

## Pipeline Execution Phases (what the executor does)

The config drives a 5-phase pipeline:

**Phase 1 — Data Acquisition:** Downloads datasets with temporal windows per type. Annual (CDL, NASS) use event year. Veg time series (MOD13A1, VNP13A1) use −32 to +64 days. Climate (GridMET) uses ±30 days. Event-matched (OPERA) uses exact date.

**Phase 2 — Prithvi Inference:** Runs flood/burn + crop per event. Flood: exact date, both S30+L30, best coverage. Crop: 3 specified dates with collection probing.

**Phase 3 — Baseline Preparation:** Reuses Phase 1 downloads when available. Auto-detects region → downloads appropriate crop baseline. Always downloads GFM for flood events.

**Phase 4 — Downstream Accounting:** Pipeline A (combined): flood × crop × MODIS NDVI severity → severity-weighted damage. Pipeline B (inundation-only): flood × crop → binary area. Baseline: OPERA/GFM × CDL/EUCROPMAP.

**Phase 5 — Analysis:** Statistical tests (if n ≥ 5), descriptive comparison, visualizations (pipeline comparison chart, per-crop breakdown), run report, handoff JSON.

---

## Critical Engineering Constraints

These are confirmed from implementation. The config and workflow spec must respect these:

1. **HLS band ordering — NEVER use glob or dict key order:**
   HLSS30: [B02, B03, B04, B8A, B11, B12]. HLSL30: [B02, B03, B04, B05, B06, B07].

2. **Burn model requires DN/10000 scaling.** Flood model uses raw DN.

3. **MODIS HDF4 files:** Read via `gdal.Open()` + `ReadAsArray()`, not `rasterio.open()`. NDVI subdataset: `500m 16 days NDVI`.

4. **VIIRS HDF5 files:** Read via `h5py`. Path: `HDFEOS/GRIDS/VIIRS_Grid_16Day_VI_500m/Data Fields/500 m 16 days NDVI`.

5. **GFM Equi7 CRS:** Tiles report fake EPSG codes (27704/27705). Must override with correct Equi7 aeqd proj4 strings including false easting/northing offsets (x_0=8264722 for NA, x_0=5837287 for EU).

6. **CropScape API bbox:** Requires EPSG:5070 Albers metres, not WGS84.

7. **Crop dates:** 3 pre-hazard dates with ≥70-day gaps, ≥70% clear pixels, excluding cloud/shadow/snow.

8. **Flood dates:** Exact HLS overpass date. Search both S30 and L30, pick best coverage.

9. **NDVI severity:** Pre-flood mean NDVI vs post-flood min NDVI. Scale factor 0.0001. Valid range −0.2 to 1.0.

10. **Region auto-detection:** Center of bbox determines US/Europe/Canada. US: lon −130 to −60, lat 24-50. Europe: lon −32 to 45, lat 27-72.

---

## Prithvi Tier Workflow Patterns

### Tier 1 (flood, burn scar, crop, land cover, cloud gap):
Use existing fine-tuned weights. Standard workflow: Fetch HLS → Preprocess → Inference → Post-process → Validate.

### Tier 2 (demonstrated fine-tuning):
Extended workflow with fine-tuning evaluation checkpoint.

### Tier 3 (architecturally feasible, no precedent):
Same as Tier 2 with additional uncertainty and fallback plan.

---

## Contradictions and Edge Cases

### When the handoff has inconsistencies:
Flag the specific inconsistency. Do NOT silently substitute. Add to Unresolved Decision Log.

### When multiple valid approaches exist:
Present top 2–3 with trade-offs.

### When fine-tuning is required (Conditional-Go):
Include fine-tuning as explicit steps with human checkpoint.

### When workflow exceeds available compute:
Flag the bottleneck. Suggest alternatives.

---

## Agent Boundaries

### Allowed:
Design workflow, select data access methods, recommend model configs, suggest parameters with alternatives, identify failure modes, estimate data volumes, generate config YAML.

### Must Not:
Re-assess feasibility, modify RQ/H₀H₁, make parameter choices without alternatives, introduce unconfirmed tools/datasets, write production code, interpret results, skip validation.
