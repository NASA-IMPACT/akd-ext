# Workflow Spec Config Schema (v2)
# Knowledge file for the Workflow Spec Builder
# Describes the YAML configuration format for pipeline_executor.py

---

## Purpose

The Pipeline Executor (`pipeline_executor.py`) is a config-driven orchestrator that runs the entire Prithvi-EO-2.0 experiment pipeline. It reads a YAML config file and executes 5 phases: event selection → data download → Prithvi inference → baseline preparation → downstream accounting + statistical analysis.

The Workflow Spec Builder MUST generate this YAML config as its final deliverable (Stage 7). The config must be complete and ready to run — no placeholders unless events are pending screening.

---

## YAML Config Schema

```yaml
# ─── RESEARCH QUESTION ───
rq:
  text: "<Full RQ text from Gap Agent>"
  h0: "<Null hypothesis>"
  h1: "<Alternative hypothesis>"

# ─── EVENT SELECTION ───
events:
  # OPTION A: Use pre-built catalog (events known, dates need verification)
  source: flood_catalog | burn_catalog
  catalog_path: "<exact server path to CSV>"
  filters:
    event_ids: [<id1>, <id2>]             # specific event IDs
    # OR filter by attributes:
    state: [<state_code>, ...]            # e.g., [IL, SD, AR]
    min_cropland_pct: <number>            # e.g., 20
    min_area_acres: <number>              # burns only
    year_range: [<start>, <end>]          # e.g., [2020, 2025]
  max_events: <number>

  # OPTION B: User-provided custom events (dates already verified)
  source: custom
  custom_events:
    - event_id: "<unique_id>"             # user-assigned identifier
      name: "<descriptive name>"
      state: "<state or region>"
      hazard_type: flood | burn           # determines which Prithvi model runs
      bbox: [<west>, <south>, <east>, <north>]  # EPSG:4326 decimal degrees
      flood_date: "<YYYY-MM-DD>"          # exact HLS overpass date for flood/burn
      crop_dates:                         # 3 pre-hazard dates, ≥70-day gaps
        - "<YYYY-MM-DD>"                  # T1 (early)
        - "<YYYY-MM-DD>"                  # T2 (mid)
        - "<YYYY-MM-DD>"                  # T3 (late)
      start_date: "<YYYY-MM-DD>"          # same as flood_date for single-date events
      end_date: "<YYYY-MM-DD>"            # same as flood_date for single-date events
  max_events: <number>

  # OPTION C: Pending screening (Workflow Spec Builder output → Phase 0 fills dates)
  # Use this when Workflow Spec Builder generates the config but events need
  # HLS imagery verification via screen_events.py before pipeline execution.
  source: pending_screening
  screening:
    hazard_type: flood | burn
    mode: discover | catalog | manual
    # discover mode — find events by region + year:
    states: [<state_code>, ...]           # or country: <country_name>
    year_range: [<start>, <end>]
    min_cropland_pct: <number>
    # catalog mode — re-verify existing catalog events:
    catalog_path: "<path to CSV>"
    event_ids: [<id1>, <id2>]             # optional: specific IDs to screen
    # manual mode — user provides bbox interactively during Phase 0
    # (no additional fields needed — screen_events.py prompts user)
  max_events: <number>                    # Phase 0 screens this many, user selects top N
  custom_events: []                       # Phase 0 fills this after screening
  # After Phase 0 runs, source changes to "custom" and custom_events is populated

# ─── PRITHVI MODELS ───
prithvi:
  burn: true | false
  flood: true | false
  crop: true | false                      # almost always true for crop-damage RQs
  flood_checkpoint: /rhome/vkolluru/r2o/r2o_flood/Prithvi-EO-2.0-300M-TL-Sen1Floods11/Prithvi-EO-V2-600-Sen1Floods11.pt
  crop_checkpoint: /rhome/vkolluru/r2o/r2o_crop/scripts/best-epoch=117_ep120.ckpt
  burn_checkpoint: /rhome/rshinde/r2o/burnscars/burn_scar_v2/ckpt/mr01eo-workshop.ckpt
  burn_config: /rhome/rshinde/r2o/burnscars/burn_scar_v2/ckpt/mr01eo_config.yaml

# ─── BASELINES (region-aware, auto-selected by executor) ───
baselines:
  flood: opera_dswx | null                # triggers OPERA download + GFM always
  crop: cdl | null                        # CDL for US; executor auto-selects
                                          # EUCROPMAP+CLMS for Europe, AAFC for Canada
  burn: mcd64a1 | null

# ─── ANCILLARY DATASETS (downloaded per event in Phase 1) ───
datasets:
  # US-only datasets (auto-skipped for non-US events):
  - cdl                  # USDA Cropland Data Layer (30m, annual, CONUS)
  - usda_nass            # USDA NASS county yields (tabular, annual, US)
  - gridmet              # GridMET meteorology (4km, daily, CONUS)
  # Global datasets:
  - mod13a1              # MODIS NDVI/EVI (500m, 16-day) — for NDVI severity
  - vnp13a1              # VIIRS NDVI/EVI (500m, 8-day rolling) — for NDVI severity
  - opera_dswx           # OPERA DSWx-HLS (30m, per-overpass)
  # Optional (include based on RQ needs):
  # - nasa_dem           # Copernicus DEM (auto-downloaded by flood postprocessing)
  # - firms              # Active fire detections (for burn events)
  # - mcd64a1            # MODIS burned area (burn baseline)
  # - era5               # ERA5-Land reanalysis (9km, hourly→daily, global)
  # - worldpop           # Population density (1km, annual)
  # - nlcd               # NLCD land cover (30m, CONUS)
  # - mtbs               # MTBS fire perimeters (30m, CONUS)
  # - mod15a2h           # MODIS LAI/FPAR
  # - mod16a2            # MODIS ET/PET
  # - mod17a2h           # MODIS GPP
  # - mcd12q1            # MODIS land cover

# ─── STATISTICAL ANALYSIS ───
analysis:
  comparison:
    - <test_id>                           # see available tests below
  effect_size:
    - <test_id>
  uq:                                     # optional
    - <method_id>
  metrics:                                # optional
    - <suite>
  correction:
    - <method_id>
  alpha: 0.05
  paired: true | false
  # Note: n ≥ 5 events needed for Wilcoxon; n < 5 → descriptive stats only

# ─── GFM CREDENTIALS (required if any flood events exist) ───
gfm:
  jrc_email: "<user_email>"
  jrc_password: "<password>"
  date_range_days: 5                      # search window around flood date

# ─── SERVER PATHS (fixed) ───
paths:
  download_script: /rhome/vkolluru/AKD/CLSW_new/scripts/download_all_datasets.py
  statistical_tests: /rhome/vkolluru/AKD/CLSW_new/statistical_tests
  prithvi_modules: /rhome/vkolluru/AKD/CLSW_new/prithvi
  flood_validation: /rhome/vkolluru/AKD/CLSW_new/scripts/flood_validation_v26.py

# ─── OUTPUT ───
output:
  dir: /rhome/vkolluru/AKD/CLSW_new/output/<rq_short_name>
  maps: true
  figures: true
  tables: true
  report: true
```

---

## Generation Rules

### 1. RQ Section
- Copy `rq.text` verbatim from the Gap Agent's approved RQ
- Copy `rq.h0` and `rq.h1` from the Feasibility Mapper handoff
- Do NOT paraphrase or modify the RQ text

### 2. Events Section
- **source:** "flood_catalog" if flood RQ; "burn_catalog" if burn RQ; "custom" if user provides events or RQ scope doesn't match catalogs
- **catalog_path:** Use exact server paths:
  - Floods: `/rhome/vkolluru/AKD/CLSW_new/event_database/flood_events_catalog.csv`
  - Burns: `/rhome/vkolluru/AKD/CLSW_new/event_database/burn_events_catalog.csv`
- **filters:** Derive from RQ constraints (state, cropland%, year range)
- **max_events:** ≥5 for statistical tests; 2-4 for initial testing; 10+ for production
- **custom_events:** Each event requires:
  - `event_id`: unique identifier (user-assigned)
  - `bbox`: [west, south, east, north] in EPSG:4326
  - `flood_date` or fire date: exact HLS overpass date (not the disaster date if no HLS that day)
  - `crop_dates`: 3 pre-hazard dates with ≥70-day gaps, ≥70% clear pixels
  - If crop dates unknown, note "pending screening" and provide screening command
- **NEVER hardcode specific events** — accept from user or handoff

### 3. Prithvi Section
- Set each model to true/false based on RQ:
  - "flood" or "inundation" → flood: true
  - "burn" or "fire damage" → burn: true
  - "crop" or "cropland" or "agriculture" → crop: true
- Include all checkpoint paths even for disabled models (documentation)
- Paths are fixed — always use the exact values shown

### 4. Baselines Section
- **The executor auto-selects region-appropriate baselines:**
  - US (CONUS): CDL for crop, OPERA + GFM for flood
  - Europe: EUCROPMAP + CLMS for crop, OPERA + GFM for flood
  - Canada: AAFC for crop, OPERA + GFM for flood
- **GFM is ALWAYS downloaded** for flood events regardless of what's in baselines
- Set `baselines.flood: opera_dswx` to trigger flood baseline logic
- Set `baselines.crop: cdl` to trigger crop baseline logic (auto-selects by region)
- Set to null for hazard types not in the RQ

### 5. Datasets Section
- List ONLY what this RQ needs — not all 18
- **Always include mod13a1 and vnp13a1** for flood×crop RQs (NDVI severity)
- US-only datasets (cdl, nlcd, usda_nass, gridmet) are **auto-skipped** for non-US events
- Common patterns:
  - Flood × crop: [cdl, mod13a1, vnp13a1, opera_dswx, usda_nass, gridmet]
  - Burn × crop: [cdl, mod13a1, vnp13a1, mcd64a1, firms, usda_nass]
  - Temporal analysis: add era5 for climate context
  - Exposure: add worldpop

### 6. Analysis Section
- Use exact test_id strings from the 86-test framework:
  - comparison: wilcoxon_signed_rank, paired_t_test, mann_whitney_u, etc.
  - effect_size: cohens_d, cliffs_delta, eta_squared
  - uq: bootstrap_ci, ensemble_spread
  - metrics: segmentation, classification
  - correction: bh_fdr, bonferroni
- `paired: true` when comparing Pipeline A vs B on same events
- Note: with n < 5 events, executor reports descriptive stats instead of p-values

### 7. GFM Section
- **Required if any flood events exist** (gfm section triggers GFM download)
- User must provide JRC credentials (email + password)
- `date_range_days: 5` is standard (searches ±5 days around flood date)

### 8. Paths Section
- FIXED server paths — always use exact values shown
- `flood_validation` path is required for GFM tile processing

### 9. Output Section
- `dir`: Use descriptive path based on RQ, e.g., `/rhome/vkolluru/AKD/CLSW_new/output/rq2_flood_crop_severity`

---

## What the Executor Does with This Config

**Phase 1 — Data Acquisition:** Downloads datasets per event with temporal windows. Auto-skips US-only datasets for non-US events.

**Phase 2 — Prithvi Inference:** Flood: exact date, searches both HLSS30+HLSL30, picks best coverage. Crop: uses specified crop_dates with collection probing.

**Phase 3 — Baseline Preparation:** Reuses Phase 1 downloads. Auto-detects region from bbox center → downloads appropriate crop baseline (CDL/EUCROPMAP/AAFC). Always downloads GFM + OPERA for flood events. Generates clipped preview PNGs.

**Phase 4 — Downstream Accounting:**
- Pipeline A (combined): flood × crop × MODIS/VIIRS NDVI severity → severity-weighted damage per crop type
- Pipeline B (inundation-only): flood × crop → binary area per crop type (no NDVI condition)
- Baseline reference: OPERA/GFM × CDL/EUCROPMAP → independent area comparison
- Outputs: pipeline_A_combined.csv, pipeline_B_inundation_only.csv, baseline_reference.csv

**Phase 5 — Analysis:** Statistical tests (if n≥5), descriptive comparison, pipeline comparison charts, per-crop breakdown, run report, handoff JSON.

---

## Presentation Rules

When presenting the config YAML to the user in Stage 7:
1. Present as a standalone ```yaml code block
2. After the code block, provide the exact commands:
   ```
   Save as: configs/rq{N}_config.yaml
   Copy executor: cp pipeline_executor.py prithvi_flood.py prithvi_crop.py /rhome/vkolluru/AKD/CLSW_new/prithvi/
   Run: CUDA_VISIBLE_DEVICES=0 python -u prithvi/pipeline_executor.py --config configs/rq{N}_config.yaml
   ```
3. Note that the executor pauses at each phase boundary for human review
4. If crop dates are pending screening, provide the screening command first

---

## Common Config Patterns

### Flood × Crop (with NDVI severity)
```yaml
prithvi: { burn: false, flood: true, crop: true, ... }
baselines: { flood: opera_dswx, crop: cdl, burn: null }
datasets: [cdl, mod13a1, vnp13a1, opera_dswx, usda_nass, gridmet]
gfm: { jrc_email: "...", jrc_password: "...", date_range_days: 5 }
analysis:
  comparison: [wilcoxon_signed_rank, paired_t_test]
  effect_size: [cohens_d]
  correction: [bh_fdr]
  alpha: 0.05
  paired: true
```

### Burn × Crop
```yaml
prithvi: { burn: true, flood: false, crop: true, ... }
baselines: { burn: mcd64a1, flood: null, crop: cdl }
datasets: [cdl, mod13a1, vnp13a1, mcd64a1, firms, usda_nass]
analysis:
  comparison: [wilcoxon_signed_rank]
  effect_size: [cohens_d]
  correction: [bh_fdr]
  alpha: 0.05
  paired: true
```

### Multi-region (US + Europe events)
```yaml
# baselines.crop: cdl triggers auto-selection:
#   US events → CDL
#   Europe events → EUCROPMAP + CLMS
#   Canada events → AAFC
# US-only datasets (cdl, usda_nass, gridmet) auto-skipped for non-US events
datasets: [cdl, mod13a1, vnp13a1, opera_dswx, usda_nass, gridmet]
```
