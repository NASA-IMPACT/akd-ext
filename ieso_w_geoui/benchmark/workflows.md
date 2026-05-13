# Benchmark Workflows — GeoUI Protocol vs. VLM Baseline

Candidate iterative-analysis workflows for the schema-vs-VLM token-efficiency
benchmark. Each workflow is a fixed sequence of 5 turns; the same five user
utterances are run, in order, against both the GeoUI-schema agent and the
VLM-baseline agent. Success is judged by **state-field equivalence**: the
agent-produced URL is parsed into a `GeoIntent`, and the structural fields
listed under "Expected state" must match.

Edit the workflows below to add new scenarios or refine turns; the benchmark
runner reads from this catalogue (or its codified twin in `workflows.py`).

## Constraints

- **Turn count:** 5 per workflow.
- **Capability budget:** core + `geoui:compare` + `geoui:chart` +
  `geoui:raster-styling`. No polar projections, animation, multi-pane, or
  sub-daily scrubbing.
- **Excluded from judging:** bounding-box-style spatial fields
  (`viewport.bbox`, `chart:area`) — they vary too much across plausibly-correct
  framings to be useful as pass/fail signals. Tokens are still counted on the
  bbox-changing turns; only the strict equivalence check is skipped.
- **Auto-injected layers ignored:** Worldview's permalink tool always
  prepends a base reflectance layer and appends `Coastlines_15m` /
  `Reference_Features_15m`. The judge will strip those before comparison.

---

## Workflow A — California wildfire smoke tracking *(recommended primary)*

Event-driven scenario exercising all three extensions in five turns. Compare →
zoom → chart → restyle is intuitive for any audience and the layer ids are
already known in the codebase.

| # | User utterance | Expected state (highlights) |
|---|---|---|
| 1 | "Show aerosol optical depth over California on September 15, 2025." | layers: `MODIS_Aqua_Aerosol`; time: `2025-09-15` |
| 2 | "Compare it to the previous day." | compare on; B-side layers include `MODIS_Aqua_Aerosol`; compare time: `2025-09-14`; mode: `swipe` |
| 3 | "Zoom in on the San Francisco Bay Area." | *(no judgeable state change — viewport.bbox excluded; see note)* |
| 4 | "Plot a time series of AOD over that area for the month around the event." | chart on; chart layer: `MODIS_Aqua_Aerosol`; chart time: `2025-09-01`…`2025-09-30` |
| 5 | "Adjust the colour scale to emphasise high AOD values, 0 to 2." | raster-styling on aerosol layer: `min=0`, `max=2`, `squash=true` |

**Extensions exercised:** compare (T2), chart (T4), raster-styling (T5).

**T3 note.** Because viewport.bbox is excluded, turn 3 has no strict judgeable
change. It still incurs tokens and tests state-preservation (compare must
remain on). Two options if a stronger T3 is wanted:

- **Option 1 (accept as-is):** the turn exercises the agent and incurs tokens;
  the only check is "compare from T2 must still be on."
- **Option 2 (substitute):** replace with *"Switch to the morning MODIS Terra
  sensor instead of Aqua"* → expected: `MODIS_Terra_Aerosol` replaces
  `MODIS_Aqua_Aerosol` in layers. Keeps the iterative-refinement narrative
  and makes the turn judgeable.

---

## Workflow B — Saharan dust transport over the Atlantic

Longitudinal time-series scenario. Heavier on time-stepping; chart-with-range-
refinement at the end. Worldview-iconic.

| # | User utterance | Expected state (highlights) |
|---|---|---|
| 1 | "Show Saharan dust optical depth over the tropical Atlantic on June 15, 2023." | layers: `MODIS_Aqua_Aerosol`; time: `2023-06-15` |
| 2 | "Step forward three days." | time: `2023-06-18` |
| 3 | "Compare this date with the same date last week." | compare on; compare time: `2023-06-11` |
| 4 | "Chart the daily mean AOD over the Cabo Verde region for June 2023." | chart on; chart layer: `MODIS_Aqua_Aerosol`; chart time: `2023-06-01`…`2023-06-30` |
| 5 | "Narrow the chart's date range to the second half of June." | chart time: `2023-06-15`…`2023-06-30` |

**Extensions exercised:** compare (T3), chart (T4–T5).
**Every turn has a non-spatial judgeable change.**

---

## Workflow C — Lake Erie algal bloom drill-down

Multi-layer + opacity emphasis; year-over-year compare. Less iconic but
exercises layer-stack semantics more than A or B.

| # | User utterance | Expected state (highlights) |
|---|---|---|
| 1 | "Show chlorophyll concentration over Lake Erie in late August 2024." | layers: chlorophyll layer id (TBD from Worldview catalogue); time ≈ `2024-08-25` |
| 2 | "Add VIIRS true-colour imagery so I can see clouds." | layers include `VIIRS_SNPP_CorrectedReflectance_TrueColor` |
| 3 | "Make the chlorophyll layer 60% opaque so I can see both." | chlorophyll layer opacity: `0.6` |
| 4 | "Chart the mean chlorophyll in the western basin for August 2024." | chart on; chart layer: chlorophyll layer; chart time: `2024-08-01`…`2024-08-31` |
| 5 | "Compare this scene to the same week last year." | compare on; compare time ≈ `2023-08-25` |

**Extensions exercised:** chart (T4), compare (T5).
**Caveat:** the exact chlorophyll layer id needs lookup against Worldview's
GIBS catalogue before this is shippable. A and B use ids already present in
`akd_ext/tools/worldview/permalink.py` (`BASE_LAYERS`).

---

## Recommended starting set

- **Headline:** Workflow A (one hero chart on the poster).
- **Supporting datapoint** (if time permits): Workflow B — strengthens the
  claim across scenario shapes (event-driven vs. longitudinal).
- **In reserve:** Workflow C — pull in if layer-stack/opacity emphasis is
  desired, after resolving the chlorophyll layer-id lookup.

## How to edit this file

- **Tweak an utterance:** edit the corresponding cell in the table; the
  benchmark runs against whatever's here.
- **Tighten or relax an expected state:** edit the "Expected state" cell —
  fields listed are checked, fields omitted are not.
- **Add a new workflow:** copy a workflow section, give it a new letter (D,
  E, …), keep it inside the capability budget.
- **Remove a workflow:** delete its section.
- After edits, re-run the benchmark; results are versioned alongside the
  workflow file (see `results/` once it exists).
