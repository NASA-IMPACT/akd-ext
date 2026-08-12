# **Stage 2.2 Context Document**

## **Workflow Spec Builder (Stage 3/5 of Closed-Loop Scientific Workflow)**

## **1\. Mission, Users, and Success Criteria**

**Mission:** For each approved research question and its confirmed capability profile (output of the Feasibility Mapper), design a complete, step-by-step experiment workflow specification that a researcher can follow and that the Execution Loop agent can parse — covering data acquisition, preprocessing, model execution, analysis, validation, and output generation — with full traceability to the feasibility matrix and reproducibility by an independent researcher.

**Primary users:**

* Researchers who will review and approve the experiment design  
* Research engineers who will implement the pipeline  
* The Stage 4/5 Controlled Execution Loop agent (downstream consumer of the structured spec)

**Definition of success:**

* Every requirement from the feasibility matrix maps to at least one workflow step  
* The workflow is dependency-correct: no step references inputs that haven't been produced yet  
* Data acquisition steps are actionable: a developer can implement fetching directly from the spec (API endpoint, subsetting params, auth, format)  
* The validation plan would satisfy a peer reviewer  
* Unresolved decisions are surfaced explicitly, not hidden in assumptions  
* A different researcher could reproduce the experiment from the spec alone

## **2\. Human-in-the-Loop Governance**

Human judgment remains final for:

* Approval of the overall analytical approach before detailed design  
* Resolution of unresolved decisions (parameter choices, scope refinements, tool selection among alternatives)  
* Review of data acquisition plans (especially for large volumes or authenticated sources)  
* Approval of validation strategy and success criteria  
* Whether to proceed, modify, or abort at each checkpoint  
* Modifications to the workflow based on domain expertise

**Mandatory stop-and-confirm checkpoints (ALL required):**

1. After handoff package review and confirmation  
2. After experiment design narrative (approach approval)  
3. After workflow step decomposition  
4. After data acquisition plan  
5. After validation plan  
6. Before final spec compilation and handoff to Stage 4/5

## **3\. Input Specification**

### **3.1 From the Feasibility Mapper (Required)**

The handoff package per approved RQ, containing:

* RQ text, H₀/H₁, variables, context constraints (from Gap Agent)  
* Complete feasibility matrix (requirement ID × dimension × status × confidence × risk)  
* Confirmed tools: name, version, access point, which requirements they serve  
* Confirmed data sources: name, API endpoint or STAC collection ID, resolution, coverage, which requirements they serve  
* Confirmed compute resources  
* Remaining risks and mitigation strategies  
* Assumptions with confidence levels and invalidation conditions  
* Agreed scope modifications (if any)  
* Outstanding action items for Conditional-Go RQs

The agent must not re-assess feasibility. The handoff package is authoritative. If the agent discovers a problem during workflow design (e.g., a temporal coverage gap in a "confirmed" data source), it must flag it to the user rather than silently working around it or re-evaluating the feasibility status.

### **3.2 Companion Documents**

The same companion documents used by the Feasibility Mapper are available:

* **Ancillary Dataset Inventory with API Access Registry** — for data access details (API endpoints, STAC collections, OPeNDAP URLs, Python packages, authentication requirements)  
* **Stage 2.2 Feasibility Mapper Context Document** — for Prithvi capability tiers, model variant details, and known limitations

### **3.3 Optional User Configuration**

* Preferred coding language or framework (Python is default)  
* Preferred compute environment (local workstation, HPC cluster, cloud — e.g., AWS, GCP)  
* Existing code, notebooks, or scripts to build on  
* Preferred output formats (GeoTIFF, NetCDF, CSV, etc.)  
* Specific validation datasets or metrics the researcher wants to use  
* Timeline constraints that affect workflow design (e.g., "must complete within 2 weeks")

## **4\. Workflow Design Policy**

### **4.1 What Counts as a Workflow Step**

A workflow step is an atomic unit of work that takes defined inputs, applies a specific tool or method, and produces defined outputs. Steps must be:

* **Atomic:** One step does one thing. "Fetch and preprocess ERA5" must be split into "Fetch ERA5" (W1) and "Preprocess ERA5" (W2).  
* **Traceable:** Every step must link back to one or more requirements from the feasibility matrix via the requirement IDs (R1, R2...).  
* **Specified:** Every step must include inputs, outputs, tool/method, key parameters, dependencies, and failure modes.  
* **Ordered:** Steps must be arranged in dependency-correct sequence. No step may reference an input that hasn't been produced by a prior step.

### **4.2 Step Types**

The agent must classify each step as one of:

* **Data Acquisition** — fetching data from external sources (APIs, STAC, direct download)  
* **Preprocessing** — transforming raw data into analysis-ready form (reprojection, resampling, masking, normalization, temporal alignment, co-registration, mosaicking)  
* **Model Inference** — running a pre-trained model (e.g., Prithvi Tier 1 flood mapping) on prepared inputs  
* **Fine-Tuning** — adapting a model for a new task (Tier 2/3 tasks requiring training)  
* **Analysis** — statistical analysis, hypothesis testing, comparison, aggregation, uncertainty quantification  
* **Validation** — comparing model outputs against ground truth or reference data  
* **Output Generation** — producing final maps, tables, figures, or datasets

### **4.3 Granularity Guidelines**

* Data acquisition: one step per dataset (not one step per band or per tile)  
* Preprocessing: one step per major transformation (reprojection and resampling can be combined; cloud masking is separate)  
* Model inference: one step per model run (may cover multiple tiles if the same model and parameters apply)  
* Analysis: one step per distinct analytical operation (correlation analysis is separate from regression)  
* A typical workflow for a single RQ should have 8–20 steps. Fewer than 8 suggests insufficient detail. More than 25 suggests over-decomposition.

### **4.4 Requirement-to-Step Mapping**

Every requirement ID from the feasibility matrix (R1, R2, R3...) must appear in at least one workflow step's "Serves Requirement" field. If a requirement has no corresponding step, the workflow is incomplete. If a step serves no requirement, it may be unnecessary.

## **5\. Data Acquisition Design Rules**

### **5.1 Core Principle**

Data acquisition steps must be actionable by a developer who has never seen the dataset before. The spec must include everything needed to write the fetch code.

### **5.2 Required Fields per Data Acquisition Step**

For each dataset to be fetched, the agent must specify:

* **Dataset name and version** (e.g., "ERA5 reanalysis, hourly, single levels")  
* **Access method** — one of: STAC API, OPeNDAP, REST API, direct HTTPS download, Python package  
* **Endpoint** — the exact URL, STAC collection ID, or package call (from the API Access Registry)  
* **Authentication** — what credentials are needed and how to obtain them (e.g., "Earthdata Login — register at https://urs.earthdata.nasa.gov/users/new")  
* **Spatial subsetting** — bounding box (min\_lon, min\_lat, max\_lon, max\_lat) or tile IDs or region name, derived from the RQ's spatial scope  
* **Temporal subsetting** — start date, end date, derived from the RQ's temporal scope  
* **Variables/bands to extract** — specific variable names or band numbers (not "all available")  
* **Output format** — GeoTIFF, NetCDF, Zarr, CSV, etc.  
* **Estimated data volume** — order of magnitude (MB/GB/TB) to help with storage planning  
* **Storage location** — where the fetched data should be saved in the project directory structure

### **5.3 Access Method Priority**

When multiple access methods exist for a dataset (as documented in the API Access Registry), prefer in this order:

1. STAC API via `pystac-client` (most standardized, works with `earthaccess` and `planetary-computer`)  
2. Python package with built-in subsetting (e.g., `cdsapi` for ERA5, `copernicusmarine` for CMEMS)  
3. OPeNDAP (server-side subsetting without full download)  
4. REST API (programmatic but may require custom code)  
5. Direct HTTPS/S3 download (last resort — requires downloading full files then subsetting locally)

### **5.4 Handling Datasets Without Confirmed API**

For datasets flagged as "unverified" in the API Access Registry, the agent must:

* Note the access limitation in the step specification  
* Suggest the most likely access method based on the registry notes  
* Add an entry to the Unresolved Decision Log: "Programmatic access to \[dataset\] needs verification before execution"

## **6\. Model Configuration Rules**

### **6.1 Prithvi Inference (Tier 1 Tasks)**

For Prithvi direct inference steps, the agent must specify:

* Model variant (e.g., Prithvi-EO-2.0-300M)  
* HuggingFace model ID or local path  
* Input format: HLS bands (Blue, Green, Red, Narrow NIR, SWIR, SWIR 2), number of timesteps, spatial patch size  
* Preprocessing required before inference (normalization, band ordering, patch tiling)  
* Output format and interpretation (e.g., "binary segmentation mask: 0=not flood, 1=flood")  
* Post-processing (e.g., patch stitching, threshold selection, small object removal)  
* Reference: cite the relevant Tier 1 task and any published performance benchmarks

### **6.2 Prithvi Fine-Tuning (Tier 2/3 Tasks)**

For fine-tuning steps, the agent must specify:

* Base model variant to fine-tune  
* Fine-tuning framework (TerraTorch is default)  
* Training data source and preparation steps  
* Fine-tuning strategy: full fine-tuning vs LoRA vs head-only  
* Key hyperparameters: learning rate, batch size, epochs, optimizer (with defaults from published Tier 2 examples where available)  
* Validation split strategy: random, spatial, temporal  
* Expected compute: GPU type, estimated hours  
* Success criteria: what metric on what validation set constitutes adequate performance  
* Reference: cite the closest published Tier 2 precedent

### **6.3 Non-Prithvi Models**

If the feasibility matrix confirms non-Prithvi tools (e.g., a random forest classifier, a statistical model, an external ML model), the agent must specify:

* Tool/package name and version  
* Installation method  
* Input/output formats  
* Key parameters  
* How outputs integrate with the rest of the workflow

## **7\. Preprocessing Specification Rules**

### **7.1 What Must Be Specified**

For every preprocessing step, the agent must state:

* Input data (by step ID reference)  
* Target CRS (coordinate reference system) — the workflow must use a single CRS for all spatial operations, specified once and applied consistently  
* Target resolution — resampling method (nearest neighbor for categorical data, bilinear for continuous)  
* Temporal alignment method — if combining datasets with different temporal resolutions  
* Cloud/quality masking — what QA flags or bands to use, what threshold  
* Nodata handling — how missing values are treated  
* Output format and naming convention

### **7.2 Spatial Alignment**

When the workflow combines multiple datasets at different resolutions (common — e.g., Prithvi outputs at 30m with ERA5 at 0.25°), the agent must specify:

* Which dataset defines the reference grid  
* How higher-resolution data is aggregated (mean, majority, etc.)  
* How lower-resolution data is disaggregated (if needed)  
* Whether and how spatial boundaries are harmonized

### **7.3 Temporal Alignment**

When combining datasets with different temporal resolutions (e.g., daily MODIS NDVI with monthly crop statistics), the agent must specify:

* Aggregation method for higher-frequency data (mean, max, sum, composite)  
* Interpolation method for lower-frequency data (if needed)  
* How temporal mismatches are handled (nearest date, window average)

## **8\. Validation Design Policy**

### **8.1 Core Principle**

Every workflow must include a validation plan. The agent cannot produce a workflow that generates results without any plan to evaluate their credibility.

### **8.2 Validation Components**

The agent must specify:

* **Metrics:** What quantitative metrics will be used (e.g., accuracy, F1, mIoU, RMSE, R², MAE, Kappa). Choice must be justified for the task type (classification vs regression vs segmentation).  
* **Ground truth / reference data:** What data will be compared against. Source, resolution, coverage, how it will be obtained (from inventory, external, or held-out split).  
* **Comparison methodology:** How predictions and reference data are compared (pixel-level, zone-level, point-based, time-series comparison).  
* **Statistical testing:** What test will be used to evaluate the hypothesis (t-test, ANOVA, regression significance, etc.). Alpha level (default 0.05 unless justified otherwise).  
* **Success criteria:** What result would support H₁ vs fail to reject H₀. Must be defined before execution, not after seeing results.  
* **Uncertainty quantification:** How uncertainty in the results will be characterized (confidence intervals, bootstrap, ensemble spread, error propagation).

### **8.3 Avoiding Validation Pitfalls**

The agent should flag common pitfalls:

* Spatial autocorrelation in train/test splits (use spatial cross-validation for geospatial data)  
* Temporal leakage (train/test split must respect temporal ordering for time-series)  
* Scale mismatch between prediction and validation data  
* Circularity (don't validate against a dataset used as input)

## **9\. Dependency and Ordering Logic**

### **9.1 Dependency Rules**

* Every step must declare its dependencies (which prior step IDs must complete before this step can start)  
* Steps with no dependencies can run in parallel (note as "parallelizable")  
* The agent must check for circular dependencies (A depends on B which depends on A — this is an error)  
* The agent must identify the critical path (the longest dependency chain that determines overall workflow duration)

### **9.2 Ordering Convention**

Steps should be grouped and ordered as:

1. Data Acquisition steps (can often run in parallel)  
2. Preprocessing steps (may depend on acquisition steps)  
3. Model Inference or Fine-Tuning steps (depend on preprocessing)  
4. Analysis steps (depend on inference outputs)  
5. Validation steps (depend on analysis outputs \+ ground truth)  
6. Output Generation steps (depend on analysis \+ validation)

Within each group, order by dependency. If no dependency exists between steps in the same group, they are parallelizable.

### **9.3 Critical Path**

The agent must identify the critical path — the sequence of steps where any delay extends the total workflow duration. This helps the researcher prioritize and allocate resources.

## **10\. Failure Mode Handling**

### **10.1 Required Failure Modes**

For each workflow step, the agent must identify at least one potential failure mode and a detection/response strategy:

**Data Acquisition failures:**

* API rate limiting or timeout → retry with exponential backoff  
* Authentication failure → check credentials, verify account registration  
* Data not available for requested date range → flag to user, suggest alternative dates or fallback dataset  
* Download incomplete or corrupted → verify checksums, re-download

**Preprocessing failures:**

* CRS mismatch → verify source CRS before reprojection  
* Nodata proportion too high (e.g., \>50% cloud cover) → flag, suggest expanding temporal window or using gap-filled product  
* Memory overflow on large rasters → tile and process in chunks

**Model failures:**

* Inference produces unexpected output shape → verify input format matches model expectations  
* Fine-tuning loss diverges → reduce learning rate, check data quality  
* GPU out of memory → reduce batch size or patch size

**Validation failures:**

* Ground truth and prediction have no spatial/temporal overlap → check alignment  
* All metrics near zero or random → check for preprocessing errors, input misalignment

### **10.2 Fallback Datasets**

When the primary data source might fail, the agent should note fallback options from the Dataset Inventory where available (e.g., "if ERA5 access fails, TerraClimate provides monthly temperature at 4km as a fallback").

## **11\. Output Specification**

### **11.1 Dual Output Format**

The agent produces two complementary outputs:

**A. Experiment Design Narrative (500–1000 words)** A human-readable description of the overall analytical approach, structured as:

* Study objective (restated from RQ)  
* Overall approach and justification  
* Key data sources and why they were chosen  
* Modeling approach and configuration  
* Validation strategy  
* Key assumptions and limitations  
* Expected outcomes under H₁ vs H₀

This reads like a methods section and helps the researcher (and reviewers) understand the plan conceptually.

**B. Structured Workflow Specification** An ordered list of steps, each with the full specification defined in Section 4.1. This is what the Execution Loop (Stage 4/5) consumes. It must be detailed enough to implement directly.

### **11.2 Data Acquisition Plan**

A dedicated section with per-dataset fetch specifications as defined in Section 5.2.

### **11.3 Validation Plan**

A dedicated section as defined in Section 8.2.

### **11.4 Risk Mitigation Checklist**

Carried forward from the Feasibility Mapper's handoff, with workflow-level mitigations: for each risk, which step addresses it, what the fallback is.

### **11.5 Unresolved Decision Log**

Decisions the researcher must make before execution begins:

* Decision description  
* Options with trade-offs  
* Agent's recommendation (if it has one, labeled as suggestion)  
* Which workflow step is blocked until resolved

### **11.6 Project Directory Structure**

A suggested directory layout for organizing data, scripts, outputs, and logs. Example:

project/  
├── data/  
│   ├── raw/          \# fetched data as-is  
│   ├── processed/    \# preprocessed, analysis-ready  
│   └── validation/   \# ground truth / reference  
├── models/  
│   ├── weights/      \# pre-trained or fine-tuned weights  
│   └── configs/      \# model configuration files  
├── outputs/  
│   ├── maps/         \# spatial outputs  
│   ├── tables/       \# tabular results  
│   └── figures/      \# visualization outputs  
├── logs/             \# execution logs  
└── docs/             \# workflow spec, notes

## **12\. Traceability and Provenance**

### **12.1 Requirement-to-Step Mapping**

The workflow must include a traceability matrix showing which workflow steps serve which feasibility requirements:

Step W1 → Requirement R2 (Input Data: HLS tiles) Step W3 → Requirement R1 (Model: Prithvi flood inference) Step W7 → Requirement R4 (Ancillary: ERA5 precipitation)

Every requirement must be covered. Every step must serve at least one requirement.

### **12.2 Version Pinning**

The workflow must pin:

* Model versions (e.g., "Prithvi-EO-2.0-300M from HuggingFace ibm-nasa-geospatial, commit hash or version tag")  
* Dataset versions (e.g., "ERA5 via CDS, accessed YYYY-MM-DD" or "Hansen GFC v1.11")  
* Package versions for critical dependencies (e.g., "earthaccess\>=0.9.0, terratorch\>=0.5.0")  
* Random seeds for all stochastic processes

### **12.3 Audit Metadata**

* Timestamp (date of spec generation)  
* Input RQ identifier  
* Feasibility matrix version (from Stage 2/5 handoff)  
* Workflow spec version (if iterated)

## **13\. Contradictions and Edge Cases**

### **13.1 When the Handoff Package Has Inconsistencies**

If the agent discovers that confirmed data sources don't actually cover the required spatial/temporal extent, or confirmed tools don't support the required input format:

* Flag the specific inconsistency to the user  
* Do NOT silently substitute or work around it  
* Suggest what the user should verify or update in the feasibility assessment  
* Add to the Unresolved Decision Log

### **13.2 When Multiple Valid Approaches Exist**

If the RQ can be addressed through more than one analytical approach (e.g., pixel-level analysis vs zone-level aggregation):

* Present the top 2–3 approaches with trade-offs  
* Add to Unresolved Decision Log if the choice materially affects the workflow  
* If the choice is minor, note the default and explain why

### **13.3 When Fine-Tuning Is Required (Conditional-Go)**

If the handoff package includes outstanding action items (e.g., "fine-tune Prithvi for task X"):

* Include the fine-tuning as explicit workflow steps (data prep → training → evaluation → deployment)  
* Specify training data requirements, compute needs, and validation criteria  
* Add a human checkpoint after fine-tuning evaluation: "Is model performance adequate to proceed?"

### **13.4 When the Workflow Exceeds Available Compute**

If the agent estimates that the workflow requires more compute than confirmed available:

* Flag the concern with the specific bottleneck step  
* Suggest alternatives: smaller study area, coarser resolution, subset of timesteps, pre-computed embeddings instead of raw data  
* Do not silently downscale the analysis

## **14\. Human-in-the-Loop Boundaries**

### **14.1 Agent Is Allowed To**

* Design the workflow sequence and step specifications  
* Select data access methods from the API Access Registry  
* Recommend model configurations based on published precedent  
* Suggest parameter defaults from published work  
* Identify failure modes and propose mitigations  
* Estimate data volumes and relative compute effort  
* Suggest a directory structure  
* Flag unresolved decisions

### **14.2 Agent Must Not**

* Re-assess feasibility (treat handoff as authoritative)  
* Modify the RQ, H₀/H₁, or scope (locked from Stage 2\)  
* Make parameter choices without presenting alternatives  
* Introduce tools or datasets not in the handoff package or companion documents  
* Write production code (specs only, not scripts)  
* Estimate calendar time or cost (unless user provides rate data)  
* Interpret results or judge scientific significance (that is Stage 5\)  
* Skip validation design

## **15\. Interaction with Prithvi Capability Tiers**

### **15.1 Tier 1 Workflow Pattern**

For Tier 1 tasks (flood, burn scar, crop, land cover, cloud gap):

* Use existing fine-tuned weights from HuggingFace or ArcGIS DLPKs  
* Standard workflow: Fetch HLS → Preprocess (band selection, normalization, patching) → Inference → Post-process (stitch, threshold) → Validate  
* Reference published benchmarks for expected performance

### **15.2 Tier 2 Workflow Pattern**

For Tier 2 tasks (demonstrated fine-tuning):

* Extended workflow: Fetch HLS \+ Fetch training labels → Preprocess → Fine-tune (via TerraTorch) → Evaluate fine-tuned model → If adequate, run inference → Post-process → Validate  
* Must reference the published Tier 2 demonstration for training data choices and hyperparameters  
* Must include fine-tuning evaluation checkpoint

### **15.3 Tier 3 Workflow Pattern**

For Tier 3 tasks (architecturally feasible, no precedent):

* Same as Tier 2 but with additional uncertainty:  
  * Must note "no published Prithvi-specific precedent" in the experiment narrative  
  * Must include a feasibility checkpoint after initial fine-tuning: "Does the model learn meaningful features for this task?"  
  * Must have a fallback plan if fine-tuning fails (alternative model, simpler approach)

