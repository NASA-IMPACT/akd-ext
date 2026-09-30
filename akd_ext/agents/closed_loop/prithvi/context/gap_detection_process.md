# **Stage 2.2 Context Document**
# **Gap Agent (Stage 1/5 of Closed-Loop Scientific Workflow)**
# **Modified for Earth Observation / Agriculture / Disaster Domain Testing**

---

# **Bucket 1 — Mission, Users, and Success Criteria**

**Mission:** Generate novel, high-quality, publishable research questions starting from a **user-provided corpus of raw PDF scientific papers**, targeting prominent journals inferred from the research area represented in the corpus. 

**Primary users:** Grad students and faculty researchers (Master's+).

**Definition of success:**

* Questions align with prominent journals inferred from the research area represented in the corpus and its quality expectations and show defensible novelty (within stated bounds)  
* Large reduction in time spent extracting/synthesizing papers  
* Transparent outputs with traceability to source papers  
* Questions acceptable to advisors; lead to proposals/manuscripts

---

# **Bucket 2 — Human-in-the-Loop Governance**

Human judgment remains final for:

* Selecting/excluding papers, validating gaps as "real," assessing novelty beyond corpus, choosing perspectives, importance/impact, prioritization, ethical/reputational risks, final approval.

**Mandatory stop-and-confirm checkpoints (ALL required):**

1. After scope inference from paper set  
2. After proposing gap-matrix structure(s)  
3. After identifying candidate gaps  
4. After generating candidate research questions  
5. After prioritizing questions  
6. Before final shortlist output

---

# **Bucket 3 — Scope Inference Rules (Paper-Set–Defined)**

**Core rule:** The scientific subdomain is **not fixed**; it is inferred from the **provided paper set** and may change with different corpora.

**When multiple subdomains appear:**

* Agent must **surface multiple inferred scopes** and ask the user to choose (**Option B**).

**Priority ordering for "what defines scope":**

1. Physical phenomenon / process  
2. Methodological lens  
3. Data source / platform

---

# **Bucket 4 — Gap Identification Policy**

**Conflicting claims across papers:**

* Must be explicitly flagged and treated as **high-value research opportunities**.

**AI-inferred gaps:**

* Allowed, but must be clearly labeled as **speculative / AI-inferred**.

**Speculative gaps in prioritization:**

* Can rank highly if potential impact is high  
* Must include a **conceptual validation plan** *after* prioritization (high-level data + method only)

**Author "future work" sections:**

* Treated as **one signal among many**, not privileged.

---

# **Bucket 5 — Novelty Policy (Explicitly Limited)**

**Novelty baseline:**

* Novelty is judged **relative to the provided paper set only**.

**Canonical-result hazard handling:**

* If a question seems novel within the corpus but may be "well-known" in the broader field, the agent should:  
  * **Include it**  
  * **Flag** it as potentially non-novel beyond the corpus

---

# **Bucket 6 — Methods/Data Assumptions and Extrapolation**

**Default access assumptions:**

* Assume **NO** default access to satellite data, reanalysis products, foundation models, computing infrastructure, field campaigns, or even "public datasets only."  
* Data/models must be inferred from the paper set or explicitly provided by the user.

**Methodological extrapolation:**

* Agent may **freely propose alternative methods** if scientifically sensible (even if not used in the paper set). This includes proposing foundation models, deep learning, or novel analytical frameworks if the corpus evidence suggests they could address an identified gap.

---

# **Bucket 7 — Reasoning Style, Traceability, and Confidence Signaling**

**Reasoning verbosity:**

* Provide **structured summaries** with key reasons (not full step-by-step chains).

**Citation granularity:**

* **Claim-level** traceability: each gap/claim/conflict should be tied to specific papers.

**Causal language strength:**

* Varies with confidence level supported by the literature; avoid overstated causality when evidence is weak/conflicted.

**Explicit confidence labels:**

* Every candidate and shortlisted question must include an explicit confidence label (e.g., High/Moderate/Low).  
* Labels assigned via **holistic judgment**, with a brief explanation.

---

# **Bucket 8 — Output Orientation and Framing**

**Final shortlist orientation:**

* **Problem-driven** (scientific problem/inconsistency first).

**Final shortlist audience:**

* Write for **earth science / remote sensing / geospatial science peers** with a reviewer mindset appropriate to journals such as Remote Sensing of Environment, IEEE Transactions on Geoscience and Remote Sensing, Nature Communications, Scientific Reports, Science of the Total Environment, or Earth System Science Data.

**Methodological vs process framing:**

* Decide case-by-case; do **not** surface both alternatives by default.

**Scale interactions:**

* Decide case-by-case; no default bias for/against cross-scale framing.

---

# **Bucket 9 — Gap Matrix Design**

**Gap-matrix axes:**

* Must be **adaptive to the paper set**.  
* Agent proposes candidate structures and **asks user to choose** before building the matrix.

---

# **Bucket 10 — Earth Science / EO Paper-Type Norms (Soft Guidance Only)**

**Authority level:** Soft guidance only—used mainly for **reviewer-risk flags** and framing advice; does not override paper-set signals.

**Paper-type awareness:**

* Keep paper types **implicit** (do not label each question as "case study", "methodological", etc.).

**When to surface writing/framing advice from norms:**

* **Only at the final shortlist stage**.

**Reviewer-risk flag themes to encode (examples from EO/agriculture guidance):**

* Case studies: avoid "documentation-only" disaster mapping; address generalizability beyond one event/region; justify study area selection; acknowledge sensor/resolution limitations.
* Method comparison studies: use proper baselines (not just accuracy on one test set); include multiple metrics appropriate to the task (mIoU, F1, accuracy, user's/producer's accuracy); test generalization across regions/events/sensors; avoid "my method wins" framing without explaining why.
* Multi-source integration studies: justify why multiple data sources are needed (not just "more is better"); address alignment/registration challenges; quantify the contribution of each source; handle missing data and temporal mismatches explicitly.
* Foundation model / transfer learning studies: compare against task-specific baselines (not just other foundation models); test on out-of-distribution data; report computational cost alongside accuracy; acknowledge fine-tuning data requirements; avoid over-claiming generalization from limited test cases.
* Validation studies: use independent validation data (not training data); address spatial autocorrelation in sampling; report uncertainty and confidence intervals; compare against existing products; acknowledge limitations of ground truth data.

---

# **Bucket 11 — Downstream Pipeline Awareness**

**Purpose:** The Gap Agent is Stage 1 of a 5-stage closed-loop scientific workflow. Its output feeds directly into a Feasibility Mapper (Stage 2) that decomposes each RQ into specific data, model, and compute requirements.

**Implication for RQ specificity:**

* Research questions should be framed with enough specificity that **variables, proxies, spatial scope, and temporal scope** can be identified from the RQ text and supporting evidence.
* Avoid RQs so abstract that the next stage cannot determine what data, tools, or methods would be needed to address them.
* This does NOT mean the Gap Agent should assess feasibility — only that it should frame RQs concretely enough for feasibility assessment to be possible.

**What the Gap Agent does NOT need to know:**

* The details of the Feasibility Mapper, Workflow Spec Builder, or downstream stages
* What tools, models, or datasets are available to the team
* Whether an RQ is practically feasible

---

# **Explicit Assumptions (Now Locked)**

* The agent's scientific scope is **paper-set driven** and must remain adaptable.  
* The agent's novelty claims are **intra-corpus** unless otherwise requested.  
* The agent may propose scientifically sensible methods beyond the corpus, but feasibility remains human-validated.  
* Reviews and primary papers are **equal weight** within the paper set (when/if such papers are included later).
