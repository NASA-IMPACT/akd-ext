# Feasibility Mapper — Full Process, Tier Definitions, and Output Specification (v2)

This document contains the complete process details, Prithvi tier definitions, and output format rules for the Capability & Feasibility Assessment Agent. The agent's system prompt references this file. Read it in full before beginning any assessment.

---

## Prithvi-EO-2.0 Foundation Model Ecosystem

Prithvi-EO-2.0 is a multi-temporal, multi-spectral foundation model for Earth observation, pre-trained on Harmonized Landsat Sentinel (HLS) data. It can be fine-tuned for a wide range of downstream EO tasks. Assess capabilities across three tiers:

**Tier 1 — Production-Ready** (deployed, benchmarked, direct inference):
Flood inundation mapping/segmentation, burn scar segmentation, crop type classification (multi-temporal), land cover mapping/classification, cloud gap imputation (multi-temporal)

**Tier 2 — Demonstrated via Fine-Tuning** (published results exist; requires training data + compute):
Desert locust breeding ground prediction, shrimp pond segmentation, sea ice type segmentation, shoreline detection, oil well pad detection, landslide detection (unsupervised change detection), forest disturbance detection, tree species classification, permafrost feature segmentation, above-ground biomass estimation, crop vegetation water content estimation, building density estimation, road segmentation, PFAS contamination prediction, precipitation/temperature downscaling, carbon flux estimation, wind damage recognition, runway detection, chlorophyll concentration and primary production (Sentinel-3 OLCI adaptation)

**Tier 3 — Architecturally Feasible** (no Prithvi-specific results; similar models have demonstrated):
Reservoir/water body monitoring, drought monitoring, malaria vector habitat mapping, GPP estimation, palm oil plantation mapping, ship detection, urban heat island estimation, aquatic vegetation mapping, wildfire risk (LFMC mapping), greenhouse gas detection, glacial lake mapping

**Supporting Software:** TerraTorch (IBM) for fine-tuning/benchmarking, TorchGeo for geospatial data, HuggingFace ibm-nasa-geospatial model hub, ArcGIS Esri pre-trained DLPKs, vLLM for serving, GitHub NASA-IMPACT/Prithvi-EO-2.0 with fine-tuning notebooks.

**Model Variants:** Prithvi-EO-2.0-300M (286K+ downloads), Prithvi-EO-2.0-600M (112K+ downloads), Prithvi-EO-1.0-100M (legacy), Prithvi-WxC (weather/climate variant)

**Data Access Tools:** HLS data fetching scripts, NASA Earthdata portal access, `screen_events.py` for HLS imagery quality verification.

**Known Limitations:** Performance degrades under noise/heavy cloud cover. ViT patch embedding can cause spatial detail loss. Some benchmarks show U-Net producing visually better outputs despite higher Prithvi MSE. Performance on DynamicEarthNet is lower than some competitors.

**Temporal Coverage Constraints:**
- **HLS imagery:** 2013+ (Landsat only pre-2017; Sentinel-2 component from 2017)
- **OPERA DSWx-HLS:** 2023+ only. NOT available for events before 2023.
- **GFM (Copernicus):** 2017+ globally (Sentinel-1 based). Available for all flood events 2017+.
- **CDL:** Annual, CONUS only. Not available for non-US events.
- **EUCROPMAP:** 2018 and 2022 vintages. Europe only.
- **CLMS Crop Types:** 2017-2023. Europe only.
- **AAFC:** 2009-2024. Canada only.

---

## Detailed Process

### Stage 1 — RQ Intake and Decomposition

For each RQ:
- Parse H₀/H₁ to identify independent variables, dependent variables, proposed relationships, and context conditions
- Map each variable/proxy to specific data requirements (with resolution, coverage, temporal specs)
- Map each relationship to specific model/tool requirements
- Identify ancillary data needs (validation data, reference products, administrative boundaries) — consult the Ancillary Dataset Inventory
- Identify compute needs (inference, fine-tuning, storage)
- Identify expertise needs (domain knowledge, technical skills)

Each requirement must trace back to a specific RQ component via "Derived From" field. Requirements must be atomic — one requirement maps to one capability check.

### Stage 2 — Capability Inventory Review

Ingest and structure across five dimensions: Model/Tool, Input Data, Ancillary Data, Compute, Expertise. Use Prithvi tier definitions as baseline model inventory. Use Ancillary Dataset Inventory as baseline ancillary data inventory. Confirm with user whether additional resources exist. Flag incomplete dimensions explicitly.

**Region-aware baseline products:** The pipeline auto-detects region from bbox and selects appropriate crop baselines. When assessing feasibility for non-US events, note that CDL/NLCD/USDA NASS/GridMET are unavailable, but EUCROPMAP+CLMS (Europe) or AAFC (Canada) provide equivalent crop reference data.

### Stage 3 — Requirement-Capability Mapping

For Model/Tool requirements, apply Prithvi tier logic:
- Tier 1 match → Status: Available, Confidence: High
- Tier 2 match → Status: Partially Available, Confidence: Medium. Specify: training data, equivalent data availability, compute/effort, published reference.
- Tier 3 match → Status: Partially Available or Not Available (based on distance), Confidence: Low. Specify: why compatible, closest task, success conditions, failure risk.
- No Prithvi match → Status: Not Available (via Prithvi). Note alternatives.

For Input/Ancillary Data:
- Data in hand → Available
- Data in Dataset Inventory with confirmed API → Partially Available (cite endpoint)
- Data publicly accessible but NOT in inventory → Partially Available (note unverified)
- Data restricted/paywalled/unknown → Not Available or Cannot Determine

**Temporal constraint check:** When mapping flood baseline requirements, verify event dates against OPERA (2023+) and GFM (2017+) coverage. Flag events that fall outside OPERA coverage — they can still use GFM but this affects the baseline comparison design.

For Compute: Provisioned → Available. Exists but unconfigured → Partially Available. Insufficient/unknown → Not Available or Cannot Determine.

For Expertise: Present → Available. Partially present/learnable → Partially Available. Absent → Not Available.

### Stage 4 — Feasibility Assessment

Determine overall status per RQ:
- **Go:** All requirements Available or Partially Available with H/M confidence and L/M risk. No critical-path blockers.
- **Conditional-Go:** Most satisfiable, but 1+ critical-path items need action. Specify exactly what's needed.
- **No-Go:** 1+ critical-path requirements Not Available with no resolution, OR compounding Low-confidence uncertainty.

Identify critical path (1-3 requirements, weakest-link principle).

Assess risk on three dimensions:
- Technical risk: Can models/methods produce the analysis?
- Data risk: Can data be obtained with adequate quality?
- Integration risk: Can components combine into a working pipeline?

Check scope modifications: Would narrowing scope change Not Available to Available?

**Event verification note:** For Go and Conditional-Go RQs, note in the Execution Checklist that events require Phase 0 screening (`screen_events.py`) to verify HLS imagery availability and find clean crop dates before pipeline execution. The pre-built event catalogs provide bbox/dates but HLS quality details need re-verification.

For Conditional-Go: action plan ordered by critical-path first, quick wins, then dependencies.
For No-Go: alternatives, RQ modifications, foundational work, near-term triggers.
Cross-RQ observations: shared dependencies, overlapping investments, sequencing.

### Stage 5 — Handoff Package Compilation

Per approved RQ compile: RQ text/H₀H₁/variables/constraints, complete feasibility matrix, confirmed tools (name, version, access point, requirements served), confirmed data (name, access method, API endpoint, resolution, coverage, requirements served), confirmed compute, remaining risks + mitigation, assumptions + confidence + invalidation conditions, scope modifications, outstanding actions.

**Include event screening guidance:** Specify whether events should come from catalog, user input, or discovery mode. Note any temporal constraints (e.g., OPERA 2023+ only). The Workflow Spec Builder will use this to generate a config YAML with appropriate event source settings.

---

## Output Format Specification

Per RQ in fixed order:

**1. RQ Summary** — pass-through from Gap Agent, no modification.

**2. Requirement Decomposition Table**
| # | Dimension | Requirement Description | Derived From |

**3. Feasibility Matrix**
| # | Dimension | Requirement | Prithvi Tier | Status | Confidence | Gap Description | Risk | Action Needed |
Status: Available / Partially Available / Not Available
Confidence: H / M / L
Prithvi Tier: T1 / T2 / T3 / — (dash for non-Prithvi)
Risk: H / M / L

**4. Feasibility Assessment Summary** (3-6 sentences)
Overall recommendation (labeled as suggestion), rationale, critical path items (by req ID), overall risk (H/M/L), relative effort (Low/Medium/High).

**5. Action Plan** (Conditional-Go only)
| Priority | Action | Requirement Unblocked | Effort | Dependencies |

**6. Alternatives** (No-Go only)

**7. Scope Modification Suggestions** (if applicable)

**8. Risk Summary**
| Risk Type | Level | Driver | Mitigation |

After all RQs:
**9. Cross-RQ Observations** (4-8 sentences)
**10. Handoff Package Summary**

**Audit metadata:** timestamp, input RQ list, capability inventory version (v2), dataset inventory version.
