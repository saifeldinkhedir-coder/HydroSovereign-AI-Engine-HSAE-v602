# Response to Reviewers — SOFTX-D-26-00442

**Manuscript:** HydroSovereign AI Engine (HSAE): An Open-Source Satellite and
AI Platform for Transboundary Water Sovereignty Analysis
**Author:** Seifeldin M.G. Alkhedir (ORCID 0000-0003-0821-2991)

This document responds point-by-point to every comment from both reviewers.
The software was not merely revised — the legally-relevant computation was
**rebuilt** on a provenance-bound engine. Each response states the change and
where it can be verified.

Repositories (both updated and consistent):
- `hydrosovereign` (PyPI 6.8.1) — engine for the v601 project
- `hydrosovereign-hsae` (PyPI 6.7.3) — clean engine for the v602 project
- Both Streamlit apps now use the same clean engine and the four quoted
  defect files are fixed.

---

## Reviewer #2 — the five structural problems (highest priority)

### Problem 1 — "The GERD verdict is hardcoded."
**Resolved.** `case_study_gerd.py` no longer renders any hardcoded verdict.
The `ATDI = 0.72` metric, the static `NSE = 0.78 SATISFACTORY` validation
table, and the `VIOLATED` article rows have all been removed. The page is now
an explicitly-labelled **illustrative scenario** that (a) computes HIFD from
the provenance engine only when observation-grade `Q_nat`/`Q_obs` are
supplied, (b) otherwise returns `INSUFFICIENT_DATA`, and (c) states plainly
that no public observed discharge exists for the Blue Nile at GERD, so **no
skill score and no legal verdict are claimed**. The page now issues no legal
adjudication; it defers interpretation to qualified water-law experts.

### Problem 2 — "The indices are unvalidated ad hoc expressions."
**Resolved.** The arbitrary `ATDI = 10 + min(cap/8.5,11) + 4.8·dispute + …`
expression is gone. ATDI is now computed strictly as the manuscript's own
equations define it: `TDI = clip[(I_adj − Q_obs)/(I_adj+ε), 0, 1]` (Eq.1) and
`ATDI = mean(TDI)·100` (Eq.2), from provenance-verified observed inflow/outflow
`DataPoint`s. The indices are explicitly partitioned into **empirical**
(TDI, ATDI, HIFD, AFSF, AHLB — computed from data) and **normative composites**
(ASI, ATCI, AWGI — with explicit, documented weights and a published
sensitivity analysis). AFSF is no longer a re-weighting of ATDI/AHIFD; it is
computed independently from observed/natural anomaly. A `correlation_matrix`
function discloses inter-index redundancy honestly rather than asserting
independence. Verifiable in `hydrosovereign/indices.py`.

### Problem 3 — "HIFD is actually a constant."
**Resolved.** The synthetic `q_obs = q_nat·(1−TDI)` construction (which made
HIFD algebraically identical to a hand-entered TDI) has been removed from
`hbv_model.py`. `compute_ahifd` now returns `INSUFFICIENT_DATA` unless
**independent** observation-grade `Q_obs` is supplied; it never fabricates the
deficit. In the engine, `compute_hifd` takes independent `Q_nat` and `Q_obs`
and includes a guard that rejects the computation when both share a data
source. HIFD now genuinely varies with the observed flow.

### Problem 4 — "The trained AI is untrained."
**Resolved.** The hand-coded `0.70 − (atdi/100)·0.30 − …` "GBM" formula is no
longer presented as a trained model. The platform now ships a **genuinely
trained** `TreatyClassifier` (scikit-learn GradientBoosting) fit to the TFDD
treaties database, with an honest model card:
- task: binary classification — does a treaty include a conflict-resolution mechanism;
- n labelled treaties used: 429; split: 75/25 stratified, random_state=42;
- test F1 = 0.569, ROC-AUC = 0.629, 5-fold CV F1 = 0.504 ± 0.062,
  majority-baseline F1 = 0.000.

Crucially, the model card states what the model does **not** claim: it does not
predict negotiation success/failure (not learnable from a database of concluded
treaties). The `random.uniform()` "calibrated uncertainty band" in
`ai_forecast.py` has been replaced with a deterministic, horizon-dependent
spread that is explicitly labelled **not a calibrated confidence interval**,
and the `SimpleRF/MLP/GBM` classes are relabelled as heuristic rules, NOT
trained models.

### Problem 5 — "The validation benchmark is neither independent nor the cited product."
**Resolved.** The `GPM × runoff_c × area` series in `precompute_gee_daily.py`
is no longer mislabelled "GloFAS ERA5 v4." It is named a **GPM-derived runoff
proxy** and tagged `is_independent_benchmark = False`, so it can never be used
as an independent reanalysis benchmark. The engine's `validate_model_skill`
**rejects** any benchmark that shares the model's forcing (returning
`INSUFFICIENT_DATA`) and only reports NSE/KGE against a genuinely independent
benchmark. The SMAP and GloFAS loaders explicitly distinguish "real API" from
"synthetic demo" in their `source` field, so synthetic series never appear
under a bare real-dataset DOI as though measured.

---

## Reviewer #1 — the seven points

### Point 1 — validation against reanalysis, and Table 2 interpretation.
**Addressed.** Model skill is now only reported against a benchmark
independent of the model forcing; where none exists (Blue Nile/GERD), HSAE
reports **no** skill score rather than a model-to-model figure. The
head-to-head NSE comparison row that conflated functionality with hydrological
accuracy has been removed from the case study. The manuscript's comparison
will separate (a) hydrological accuracy, (b) community adoption, (c) support,
and (d) documentation as distinct axes rather than feature-counting.

### Point 2 — "original indices / no equivalent" and author-name prefixes.
**Addressed.** The novelty claim is withdrawn. The revised manuscript adds a
systematic literature review situating TDI/ATDI relative to established
flow-deficit measures and HIFD relative to naturalised-vs-observed dam-impact
attribution, and frames the indices as **operationalisations** of existing
concepts for a legal-compliance pipeline, not as novel science. The
author-name prefixes (e.g. "Alkhedir … Index") are dropped in favour of neutral
descriptive names, and the GitHub-timestamp priority claim is removed.

### Point 3 — legal thresholds (ATDI ≥ 20% → Art. 7, etc.).
**Addressed.** The numeric thresholds are not stated in the UNWC (1997) and no
longer drive automated "verdicts." They are reframed as **user-configurable
screening flags** for hydrological attention, explicitly **not** legal
determinations, and the software now states that compliance assessment under
the Convention requires qualified international-water-law expertise. The
default values are presented as illustrative screening defaults with that
caveat, pending interdisciplinary collaboration.

### Point 4 — software-quality evidence.
**Addressed.** Beyond "zero syntax errors," the engine ships a real test suite
(66 tests across provenance, ingestion, indices, validation, treaty
classifier), flake8-clean, with the trained model bundled and a documented
model card. Test counts, CV metrics, and a maintainable modular layout are
reported; CI runs lint + tests on push.

### Point 5 — comparison table balance (SWAT+, WEAP, HEC-HMS, HydroSHEDS).
**Addressed.** The comparison is rebalanced to include dimensions where
established tools are stronger — hydrological-model maturity, calibration
robustness, user-community size, training resources, documentation maturity —
alongside HSAE's legal-pipeline features, and notes the current capabilities of
each tool rather than emphasising only HSAE-unique items.

### Point 6 — uncalibrated HBV, "satisfactory," and the "two-minute" claim.
**Addressed.** Because no independent observed benchmark exists for the case
basin, the manuscript no longer describes uncalibrated HBV-96 performance as
"satisfactory" and reports no skill figure there. The SCE-UA calibration path
is documented as available and demonstrated on a gauged basin where independent
observations exist. The "ICJ documents within two minutes" claim (processing
speed, not legal validity) is removed.

### Point 7 — missing ML methodology.
**Addressed.** The only ML component now presented as trained is the
`TreatyClassifier`, reported with full methodology: features, label definition,
data count (429 labelled treaties), train/test split (75/25 stratified,
seed 42), 5-fold cross-validation, and metrics (F1, ROC-AUC, baseline). The RF/
MLP/GBM "ensemble" and EnKF "digital twin" are reframed as transparent
heuristic/illustrative components, not trained models, and labelled as such.

---

## Summary of what changed in code

| File | Defect | Status |
|------|--------|--------|
| `case_study_gerd.py` | hardcoded verdict (P#1) | rebuilt — scenario, no verdict |
| `hbv_model.py` | synthetic Q_obs → constant HIFD (P#3) | INSUFFICIENT_DATA unless real obs |
| `ai_forecast.py` | random "CI"; untrained "models" (P#4) | deterministic band; relabelled heuristic |
| `precompute_gee_daily.py` | GloFAS mislabel (P#5) | GPM-derived proxy, not a benchmark |
| `hydrosovereign/indices.py` | ad hoc ATDI; AFSF re-weight (P#2) | manuscript equations; empirical/normative split |
| `treaty_classifier.py` | untrained "GBM" (P#4, R1-P7) | trained sklearn GBM + model card |
| `validation.py` | shared-forcing benchmark (P#5, R1-P1) | independence guard |

All 62 app modules parse; the app and all 37 pages run with 0 exceptions in a
Streamlit Cloud-identical environment.

*Prepared by Seifeldin M.G. Alkhedir — ORCID 0000-0003-0821-2991*
