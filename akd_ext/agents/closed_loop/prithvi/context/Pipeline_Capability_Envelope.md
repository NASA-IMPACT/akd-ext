# Pipeline Capability Envelope (v2)
# Available Infrastructure for the Prithvi-EO-2.0 Closed-Loop Scientific Workflow

---

## Purpose

This document describes the tools, datasets, events, and analysis methods currently implemented and ready to execute. The Gap Agent uses this to tag Pipeline Alignment levels (High / Partial / Low). The Workflow Spec Builder uses this to select appropriate baselines and datasets per region.

**This does NOT restrict what RQs can be proposed.** It only signals "can we run this now?"

---

## 1. Prithvi-EO-2.0 Downstream Models (3 available)

| Model | Task | Input | Output | Status |
|---|---|---|---|---|
| **Flood detection** | Binary segmentation | HLS 6-band (B02,B03,B04,B8A/B05,B11/B06,B12/B07) | Flood / Not-flood mask (30m) | Available (Tier 1) |
| **Burn scar detection** | Binary segmentation | HLS 6-band (same, scaled DN/10000) | Burned / Not-burned mask (30m) | Available (Tier 1) |
| **Crop classification** | Multi-class segmentation | HLS 6-band × 3 temporal frames | 13-class crop map (30m) | Available (Tier 1) |

**What Prithvi CAN detect:** flood extent, burn scars, and crop types from HLS imagery.

**What Prithvi CANNOT detect (without new fine-tuning):** drought stress, vegetation health indices, soil moisture, urban change, deforestation, snow/ice, atmospheric composition, ocean color, building damage, landslide mapping.

### Flood Module Details
- Searches **exact flood date** on both HLSS30 and HLSL30, picks best coverage
- Post-processing: terrain shadow removal (DEM/slope), aerosol correction, vegetation filter
- No date buffer — if no HLS overpass on flood date, reports error

### Crop Module Details
- Requires **3 pre-hazard dates** (early/mid/late) with ≥70-day gaps
- `screen_crop_dates.py` tool finds clean dates (≥70% clear, no snow/ice)
- Handles mixed S30+L30 collections across the 3 dates
- 13 classes: Natural Vegetation, Forest, Corn, Soybeans, Wetlands, Developed/Barren, Open Water, Winter Wheat, Alfalfa, Fallow/Idle, Cotton, Sorghum, Other

---

## 2. Baseline Comparison Products (region-aware)

The executor **auto-detects region** from bbox center coordinates and selects appropriate baselines:

### Flood Baselines (all regions)
| Product | Source | Resolution | Coverage | Notes |
|---|---|---|---|---|
| **OPERA DSWx-HLS** | NASA PODAAC | 30m | Global, 2023+ | Primary flood baseline. Classes: Open Water (1), Partial Water (2) |
| **GFM** | Copernicus/JRC | 20m (Equi7 grid) | Global, 2017+ | Sentinel-1 SAR based. ALWAYS downloaded for flood events. Requires JRC credentials. Equi7 CRS with false easting/northing offsets |

### Crop Baselines (by region)
| Region | Detection Rule | Product | Resolution | Coverage |
|---|---|---|---|---|
| **US (CONUS)** | lon −130 to −60, lat 24-50 | USDA CDL | 30m, annual | CONUS |
| **Europe** | lon −32 to 45, lat 27-72 | JRC EUCROPMAP + CLMS Crop Types | 10m | EU27 (EUCROPMAP: 2018, 2022; CLMS: 2017-2023) |
| **Canada** | lon −141 to −52, lat 41-84 (excluding CONUS) | AAFC Annual Crop Inventory | 30m | Canada (2009-2024) |
| **Other** | — | None available | — | Prithvi crop map used without reference baseline |

### Notes on Crop Baselines
- **CDL** downloaded via CropScape API (EPSG:5070 Albers) or NASS national tiles
- **EUCROPMAP** downloaded via JRC FTP remote windowed read (COG format, EPSG:3035)
- **CLMS** downloaded via WMS GetMap, pixel-aligned to Prithvi prediction grid
- **AAFC** downloaded via ArcGIS ImageServer REST API
- All crop baseline functions are in `prithvi_crop.py` (Cell 11 from notebook)

---

## 3. NDVI Condition Tracking (for severity-weighted damage)

The pipeline computes pre-flood vs post-flood NDVI to measure damage severity:

| Product | Format | Reader | Resolution | Temporal |
|---|---|---|---|---|
| **MOD13A1** | HDF4 (.hdf) | GDAL python (`gdal.Open` → `ReadAsArray`) | 500m | 16-day composite |
| **VNP13A1** | HDF5 (.h5) | h5py (`HDFEOS/GRIDS/.../500 m 16 days NDVI`) | 500m | 8-day rolling |

**How it works:**
1. Phase 1 downloads MOD13A1 + VNP13A1 with temporal window: −32 days to +64 days around hazard date
2. Phase 4 reads NDVI subdataset from each file, reprojects to flood grid (MODIS sinusoidal → EPSG:4326)
3. Classifies each date as PRE or POST flood
4. Severity = mean(pre-flood NDVI) − min(post-flood NDVI)
5. Severity-weighted damage = sum(severity × pixel_area) per crop type

**Pipeline A** uses severity-weighted damage. **Pipeline B** uses binary area only. The RQ tests whether adding NDVI condition info improves damage assessment.

---

## 4. Supported Datasets (18 with download automation)

### Tier 1 — Full automation (download_all_datasets.py)

| # | Dataset | Variables | Resolution | Temporal | Coverage | US-only? |
|---|---|---|---|---|---|---|
| 1 | CDL | Crop type | 30m | Annual | CONUS | Yes |
| 2 | NLCD | Land cover | 30m | 2-3 yr | CONUS | Yes |
| 3 | GridMET | Tmax, Tmin, Precip, Wind, etc. | 4km | Daily | CONUS | Yes |
| 4 | USDA NASS | Crop stats (yield, production) | County | Annual | US | Yes |
| 5 | MTBS | Fire perimeters + severity | 30m | Per-fire | CONUS | Yes |
| 6 | MOD13A1 | NDVI, EVI | 500m | 16-day | Global | No |
| 7 | VNP13A1 | VIIRS NDVI, EVI | 500m | 16-day | Global | No |
| 8 | MOD15A2H | LAI, FPAR | 500m | 8-day | Global | No |
| 9 | MOD16A2 | ET, PET | 500m | 8-day | Global | No |
| 10 | MOD17A2H | GPP | 500m | 8-day | Global | No |
| 11 | MOD17A3HGF | NPP | 500m | Annual | Global | No |
| 12 | MCD12Q1 | Land cover (IGBP) | 500m | Annual | Global | No |
| 13 | MCD64A1 | Burned area | 500m | Monthly | Global | No |
| 14 | OPERA DSWx | Surface water | 30m | Per-overpass | Global | No |
| 15 | NASA DEM | Elevation | 30m | Static | Global | No |
| 16 | FIRMS | Active fire | 375m | NRT | Global | No |
| 17 | ERA5-Land | Temp, precip, soil moisture, etc. | 9km | Hourly→daily | Global | No |
| 18 | WorldPop | Population density | 1km | Annual | Global | No |

**US-only datasets are auto-skipped** by the executor for non-US events (detected from bbox center).

### Tier 2 — In inventory but no automation
The full Ancillary Dataset Inventory contains ~92 datasets. Those not in Tier 1 require manual download.

---

## 5. Event Identification & Selection

### Option A: Pre-built Event Database (200 events, CONUS only)

#### Burn Events (100)
- Source: MTBS + FIRMS/VIIRS agricultural burn clusters
- Coverage: CONUS, 2017–2025
- Enrichment: CDL land cover, HLS availability (Fmask-verified)

#### Flood Events (100 episodes)
- Source: NOAA Storm Events Database
- Coverage: CONUS, 2017–2025
- Enrichment: CDL land cover, HLS availability (Fmask-verified)

#### Per event: location (bbox), timing (dates), scale (area/damage), land cover (8 categories), HLS (clean dates with cloud %)

### Option B: User-provided events (any region worldwide)
Users provide bbox + dates for events anywhere HLS imagery is available. The pipeline auto-detects region and selects appropriate baselines:
- **US events:** CDL for crop baseline, OPERA + GFM for flood, NASS for validation
- **European events:** EUCROPMAP + CLMS for crop baseline, OPERA + GFM for flood
- **Canadian events:** AAFC for crop baseline, OPERA + GFM for flood
- **Other regions:** No crop baseline (Prithvi crop map used directly), OPERA + GFM for flood

**Multi-region experiment design is encouraged** — it strengthens RQs by testing across diverse agricultural systems, crop calendars, and flood regimes. Validated examples: US (SD Sioux City flood 2024) + Europe (Spain Valencia DANA flood 2024).

### Option C: Screening tools
- `screen_events.py` — Phase 0: discovers events, verifies HLS, finds crop/flood dates, ranks events, updates config
- `screen_crop_dates.py` — finds 3 clean pre-hazard HLS dates (≥70% clear, ≥70-day gaps, no snow/ice)
- `build_event_database.py` — identifies events from MTBS/FIRMS/NOAA for any region
- `download_all_datasets.py` — downloads and previews datasets for any bbox/date

### IMPORTANT: The pre-built catalog covers CONUS only. For non-US events, use Option B (user-provided) or Option C (discovery tools). The pipeline works with ANY bbox and date where HLS imagery is available, regardless of country. When designing experiments, prefer a mix of US and international events for stronger generalizability.

---

## 6. Statistical Analysis Framework (86 tests/metrics)

(Unchanged from v1 — see full list: 32 core tests, 5 causal, 5 UQ, 40 metrics, 4 spatial)

Key note: **n ≥ 5 events** needed for Wilcoxon signed-rank. With n < 5, the executor reports descriptive statistics (mean difference, per-event comparison) instead of p-values.

---

## 7. Pipeline Alignment Rules

### HIGH alignment (immediately executable):
- RQ involves flood extent, burn scar area, or crop classification as primary variables
- RQ uses comparison between Prithvi outputs and baseline products
- RQ uses NDVI condition tracking for severity-weighted damage assessment
- Required datasets are all in Tier 1
- Events from catalog (CONUS) AND/OR user-provided (any region with HLS coverage)
- **Multi-region designs** (US + Europe, US + Canada, etc.) are HIGH alignment because baseline products exist for all major agricultural regions: CDL (US), EUCROPMAP+CLMS (Europe), AAFC (Canada)

### PARTIAL alignment (moderate effort):
- RQ needs Tier 2 dataset (manual download)
- RQ targets regions outside US/Europe/Canada (no crop baseline available)
- RQ needs statistical method not yet implemented but available in scipy/statsmodels
- RQ uses events outside catalog (needs screening)

### LOW alignment (significant development):
- RQ requires new fine-tuning task (drought, deforestation, urban change)
- RQ needs field data, surveys, or restricted datasets
- RQ requires architectures not available
- RQ involves non-EO modalities

---

## 8. Engineering Constraints (confirmed from implementation)

1. **Band ordering:** Explicit lists only. `list(spectral.keys())` produces filesystem-dependent order → 57.5% false-positive flood detection
2. **Burn DN scaling:** Burn model requires raw HLS / 10000 (0-1 reflectance). Flood uses raw DN.
3. **MODIS HDF4:** Must use `gdal.Open()` + `ReadAsArray()`. `rasterio.open()` fails on HDF4.
4. **VIIRS HDF5:** Must use `h5py`. Dataset path: `HDFEOS/GRIDS/VIIRS_Grid_16Day_VI_500m/Data Fields/500 m 16 days NDVI`
5. **GFM Equi7 CRS:** Tiles report fake EPSG codes (27704/27705). Must override with correct aeqd proj4 strings including false easting/northing (NA: x_0=8264722, EU: x_0=5837287)
6. **CropScape bbox:** EPSG:5070 Albers metres, not WGS84
7. **Pixel area for geographic CRS:** Requires `111320 × cos(lat)` conversion
8. **Flood dates:** Exact HLS overpass, no buffer. Search both S30 + L30, pick best coverage.
9. **Crop dates:** 3 pre-hazard, ≥70-day gaps, ≥70% clear after excluding cloud+shadow+snow
10. **NDVI scale factor:** 0.0001 (raw values −2000 to 10000 → −0.2 to 1.0)

---

## 9. Server Paths

| Tool | Path |
|---|---|
| Pipeline executor | `/rhome/vkolluru/AKD/CLSW_new/prithvi/pipeline_executor.py` |
| Prithvi modules | `/rhome/vkolluru/AKD/CLSW_new/prithvi/` |
| Download script | `/rhome/vkolluru/AKD/CLSW_new/scripts/download_all_datasets.py` |
| Flood validation | `/rhome/vkolluru/AKD/CLSW_new/scripts/flood_validation_v26.py` |
| Crop date screening | `/rhome/vkolluru/AKD/CLSW_new/scripts/screen_crop_dates.py` |
| Event database | `/rhome/vkolluru/AKD/CLSW_new/event_database/` |
| Flood catalog | `flood_events_catalog.csv` (100 episodes) |
| Burn catalog | `burn_events_catalog.csv` (100 events) |
| Statistical tests | `/rhome/vkolluru/AKD/CLSW_new/statistical_tests/` |
| Configs | `/rhome/vkolluru/AKD/CLSW_new/configs/` |
| Output | `/rhome/vkolluru/AKD/CLSW_new/output/` |
