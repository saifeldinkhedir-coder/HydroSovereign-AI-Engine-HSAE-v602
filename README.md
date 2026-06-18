# HydroSovereign AI Engine (HSAE) — v602 (Scientific Rebuild)

[![PyPI](https://img.shields.io/pypi/v/hydrosovereign-hsae?style=for-the-badge&color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/hydrosovereign-hsae/)
[![Python](https://img.shields.io/pypi/pyversions/hydrosovereign-hsae?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/hydrosovereign-hsae/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg?style=for-the-badge)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Live_App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://hydrosovereign-ai-engine-hsae-v602-pysmdygmxj9xn6rpv8lmim.streamlit.app/)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0003--0821--2991-a6ce39?style=for-the-badge&logo=orcid&logoColor=white)](https://orcid.org/0000-0003-0821-2991)

A **provenance-bound, data-driven rebuild** of the HydroSovereign AI Engine for
transboundary water analysis related to the UN Watercourses Convention (1997).
This is the clean parallel edition (`hydrosovereign-hsae`), engineered so that
**no result is reported as a measurement unless it is computed from documented,
observation-grade data** — and where such data are absent, the engine returns
an explicit `INSUFFICIENT_DATA` result rather than a fabricated value.

> **Scope.** HSAE performs transparent hydrological **screening** and **data
> provenance**. It does **not** issue legal verdicts; interpretation of the
> UN Watercourses Convention is reserved to qualified international-water-law
> experts.

---

## 📋 Table of Contents

1. [What is HSAE?](#-what-is-hsae)
2. [What is different in this edition](#-what-is-different-in-this-edition)
3. [Index reference](#-index-reference)
4. [Installation](#-installation)
5. [Quick start — data with provenance](#-quick-start--data-with-provenance)
6. [Trained treaty-feature classifier](#-trained-treaty-feature-classifier)
7. [Independent validation](#-independent-validation)
8. [26-basin coverage](#-26-basin-coverage)
9. [Architecture](#-architecture)
10. [Comparison with alternatives](#-comparison-with-alternatives)
11. [Data sources](#-data-sources)
12. [Live platform & links](#-live-platform--links)
13. [Honesty statement](#-honesty-statement)
14. [Citation](#-citation)

---

## 🌊 What is HSAE?

HSAE assembles multi-sensor satellite Earth observation, the HBV-96
rainfall-runoff model, a trained treaty-feature classifier, and screening
indicators related to the UN Watercourses Convention (1997) across transboundary
river basins. The platform makes the hydrological **evidence layer**
auditable: every datum entering an index carries its source, units, temporal
coverage, and quality grade, and every result is traceable to that data.

This v602 edition exists as a clean parallel package (`hydrosovereign-hsae`)
that runs alongside the fuller legacy package (`hydrosovereign`) without
replacing it. Both carry the same provenance-bound core engine and the same
trained model.

---

## 🔬 What is different in this edition

This rebuild puts every result on a defensible scientific footing:

1. **No fabricated numbers.** Every index computes only from
   provenance-verified observations. When required observed data are absent,
   the engine returns `INSUFFICIENT_DATA` — it never substitutes a hard-coded
   constant.
2. **Indices match their definitions.** `HIFD` takes **independent** `Q_nat`
   and `Q_obs`, so it cannot algebraically collapse to a constant; a shared
   data source is rejected. `ATDI` is the empirical mean of per-period TDI
   from observed inflow/outflow (Eqs. 1–2).
3. **Empirical vs. normative are separated.** Empirical indices (TDI, ATDI,
   HIFD, AFSF, AHLB) are computed from data; normative composites (ASI, ATCI,
   AWGI) carry **explicit, documented weights** and a sensitivity analysis, and
   are labelled as constructs — never conflated with measurements.
4. **The model is genuinely trained.** `TreatyClassifier` is a real
   gradient-boosting model trained on the TFDD treaties database, with an
   honest model card (F1, ROC-AUC, cross-validation, baseline). It classifies a
   documented treaty property — **not** negotiation success/failure.
5. **Validation is independent.** Model skill is reported only against a
   benchmark independent of the model's own (GPM) forcing; a benchmark derived
   from the same precipitation is rejected as uninformative.

These changes were made in response to external peer review of the prior
version (SoftwareX SOFTX-D-26-00442).

---

## 📐 Index reference

| Function | Kind | Inputs |
|----------|------|--------|
| `compute_tdi` | empirical | observed inflow, outflow |
| `compute_atdi` | empirical | observed inflow/outflow series (Eqs. 1–2) |
| `compute_hifd` | empirical | **independent** observed `Q_nat`, `Q_obs` (Eq. 3) |
| `compute_afsf` | empirical | observed/natural anomaly, range |
| `compute_ahlb` | empirical | paired `q_sim`, `q_obs` (NSE) |
| `compute_asi` | normative | equity, cooperation, data-sharing (explicit weights) |
| `compute_atci` | normative | per-article compliance postures (explicit weights) |
| `compute_awgi` | normative | transparency, dispute, riparians, regulation (+ sensitivity) |
| `correlation_matrix` | disclosure | cross-basin index values (honest redundancy disclosure) |
| `validate_model_skill` | validation | model vs. forcing-independent benchmark |

Defining equations (computed strictly from observation-grade data):

```
Eq. 1   TDI_i = clip[ (I_adj,i − Q_obs,i) / (I_adj,i + ε), 0, 1 ]
Eq. 2   ATDI  = mean(TDI_i) × 100%
Eq. 3   HIFD  = (Q_nat − Q_obs) / Q_nat × 100%      (Q_nat, Q_obs independent)
```

---

## ⚙️ Installation

```bash
# From PyPI
pip install hydrosovereign-hsae

# From source
git clone https://github.com/saifeldinkhedir-coder/HydroSovereign-AI-Engine-HSAE-v602.git
cd HydroSovereign-AI-Engine-HSAE-v602
pip install -e .

# With data extras (pandas, openpyxl)
pip install "hydrosovereign-hsae[data]"

# Developer extras (pytest, flake8)
pip install "hydrosovereign-hsae[dev]"
```

Requires Python 3.10–3.12.

---

## 🚀 Quick start — data with provenance

```python
from hydrosovereign_hsae import (
    DataPoint, DataQuality, DataRegistry, hifd_for_basin,
)

reg = DataRegistry()

# Anyone holding real, documented observations can contribute them.
reg.submit("GERD", DataPoint(
    value=1248.0, variable="Q_obs", unit="m3/s",
    source="GRDC station 1577100 (El Diem)",
    source_ref="https://grdc.bafg.de/  (request 78949)",
    date_start="2010-01-01", date_end="2020-12-31",
    quality=DataQuality.OBSERVED), contributor="Researcher A, ORCID ...")

# Without an independent, observed Q_nat this returns INSUFFICIENT_DATA —
# never a fabricated value.
result = hifd_for_basin(reg, "GERD")
print(result.status, result.value)

# ...once an independent observed Q_nat is also submitted, HIFD is computed
# from the real Eq. 3 and carries its full provenance.
```

---

## 🤖 Trained treaty-feature classifier

The single machine-learning component is genuinely trained and honestly
reported. It classifies a documented treaty property — whether a treaty
includes a conflict-resolution mechanism — **not** negotiation success/failure
(which is not learnable from a database of concluded treaties).

| Model-card property | Value |
|---------------------|-------|
| Task | Binary: treaty includes a conflict-resolution mechanism |
| Source | TFDD treaties database |
| Unique treaties | 476 |
| Labelled treaties used | 429 |
| Features | n_signatories, year, basin_treaty_count |
| Model | GradientBoosting (100 trees, max_depth 3) |
| Split | 75/25 stratified, random_state = 42 |
| Test accuracy | 0.593 |
| Test F1 | 0.569 |
| Test ROC-AUC | 0.629 |
| 5-fold CV F1 | 0.504 ± 0.062 |
| Majority-baseline F1 | 0.000 |

```python
from hydrosovereign_hsae import TreatyClassifier, MODEL_CARD
tc = TreatyClassifier()
p = tc.predict_proba(n_signatories=3, year=2015, basin_treaty_count=12)
print(p)  # probability that the treaty includes a conflict-resolution mechanism
```

---

## ✅ Independent validation

```python
from hydrosovereign_hsae.validation import validate_model_skill
# Reports NSE/KGE ONLY against a benchmark independent of the model forcing.
# If the benchmark shares the model's forcing (e.g. a GPM-derived series for a
# GPM-forced model), it returns INSUFFICIENT_DATA instead of a misleading score.
```

For the Blue Nile (GERD) basin no public observed discharge exists, so the
platform reports **no skill score** there. On an independent ERA5-forced
benchmark over a demonstration period the routine reports NSE ≈ 0.60,
KGE ≈ 0.68 — illustrative of the independence check, not a calibrated claim for
any specific basin.

---

## 🌍 26-basin coverage

| Region | Basins |
|--------|--------|
| 🌍 **Africa** | Blue Nile (GERD) · Nile-Roseires · Nile-Aswan · Zambezi-Kariba · Congo-Inga · Niger-Kainji |
| 🌏 **Middle East** | Euphrates-Atatürk · Tigris-Mosul |
| 🌏 **Central Asia** | Amu Darya-Nurek · Syr Darya-Toktogul |
| 🌏 **Asia** | Mekong-Xayaburi · Yangtze-Three Gorges · Indus-Tarbela · Brahmaputra-Subansiri · Ganges-Farakka · Salween-Myitsone |
| 🌎 **Americas** | Amazon-Belo Monte · Paraná-Itaipu · Orinoco-Guri · Colorado-Hoover · Columbia-Coulee · Rio Grande-Amistad |
| 🇪🇺 **Europe** | Danube-Iron Gates · Rhine · Dnieper-Kakhovka |
| 🌏 **Oceania** | Murray-Darling-Hume |

> Index values for these basins are computed only where observation-grade data
> are contributed; otherwise the engine returns `INSUFFICIENT_DATA`. The
> registry seeds carry scenario priors that are explicitly labelled as such and
> are not presented as measured results.

---

## 🏗 Architecture

```
hydrosovereign_hsae/
├── provenance.py        # DataPoint, DataQuality, ProvenancedResult, INSUFFICIENT_DATA
├── ingestion.py         # DataRegistry, ContributionRecord (SHA), audit log
├── indices.py           # TDI/ATDI/HIFD/AFSF/AHLB + ASI/ATCI/AWGI + correlation_matrix
├── validation.py        # validate_model_skill (independence-checked NSE/KGE)
├── treaty_classifier.py # trained TFDD GradientBoosting model + MODEL_CARD
└── models/
    └── tfdd_crm_model.joblib   # bundled trained model
```

The companion Streamlit application (in `streamlit_app/`) provides ~30 pages
spanning data ingestion, HBV-96 modelling, index computation, satellite
loaders (GPM, GRACE-FO, SMAP, Sentinel, GloFAS/ERA5), and reporting, all on the
same provenance-bound engine.

---

## 📊 Comparison with alternatives

The comparison is deliberately balanced: established tools lead on core
modelling and ecosystem maturity, and HSAE does not seek to replace them.

| Dimension | SWAT+ / WEAP / HEC-HMS | HSAE |
|-----------|------------------------|------|
| Hydrological-model maturity | High (decades of use) | Moderate (HBV-96) |
| Calibration robustness | High | SCE-UA available; limited demo |
| User community / support | Large, institutional | Small, emerging |
| Documentation maturity | Extensive | Growing |
| Data-provenance tracking | Limited | Core design feature |
| Transparent UNWC screening | None | Yes (screening, not verdicts) |
| Open source | Mixed | Yes (GPL-3.0) |

A head-to-head hydrological-accuracy comparison is intentionally omitted,
because a fair comparison requires calibration and an independent observed
benchmark that are not available for the demonstration basin.

---

## 📡 Data sources

- **TFDD International Freshwater Treaties Database** (Oregon State University) —
  trains the treaty-feature classifier.
- **GRDC** observed discharge — for provenance-bound, legally-relevant indices
  (contributed through the open registry).
- **GPM IMERG, GRACE-FO, SMAP, Sentinel-1/2, GloFAS/ERA5, Open-Meteo,
  Microsoft Planetary Computer** — satellite/reanalysis forcings. Synthetic or
  pattern-based series (when credentials are absent) are labelled as synthetic
  and never presented under a bare dataset DOI as a retrieval.

---

## 🔗 Live platform & links

| Resource | URL |
|----------|-----|
| 🌐 Live Streamlit App | [HSAE v602](https://hydrosovereign-ai-engine-hsae-v602-pysmdygmxj9xn6rpv8lmim.streamlit.app/) |
| 📦 PyPI (this edition) | [hydrosovereign-hsae](https://pypi.org/project/hydrosovereign-hsae/) |
| 📦 PyPI (full engine) | [hydrosovereign](https://pypi.org/project/hydrosovereign/) |
| 📂 GitHub (this repo) | [HydroSovereign-AI-Engine-HSAE-v602](https://github.com/saifeldinkhedir-coder/HydroSovereign-AI-Engine-HSAE-v602) |
| 🔌 QGIS Plugin (ID 5040) | [plugins.qgis.org/plugins/hsae_qgis/](https://plugins.qgis.org/plugins/hsae_qgis/) |
| 🏛️ Zenodo Archive | [doi.org/10.5281/zenodo.19180160](https://doi.org/10.5281/zenodo.19180160) |
| 🆔 ORCID | [0000-0003-0821-2991](https://orcid.org/0000-0003-0821-2991) |

---

## 🔎 Honesty statement

Modest model skill and `INSUFFICIENT_DATA` results are reported as-is. The
engine is designed so that an absence of data produces an explicit non-result
rather than a misleading number. Screening flags are not legal determinations.
For the Blue Nile (GERD) basin, no public observed discharge exists, so the
platform reports no measured index and no skill score there; it can only
demonstrate the pipeline on explicitly-labelled hypothetical inputs.

---

## 📝 Citation

```bibtex
@software{alkhedir2026hsae_v602,
  author    = {Alkhedir, Seifeldin M.G.},
  title     = {{HydroSovereign AI Engine (HSAE): a provenance-bound platform
               for transboundary water screening}},
  year      = {2026},
  version   = {6.7.3},
  publisher = {PyPI + QGIS Plugin Repository + Streamlit + Zenodo},
  doi       = {10.5281/zenodo.19180160},
  url       = {https://pypi.org/project/hydrosovereign-hsae/},
  orcid     = {0000-0003-0821-2991}
}
```

---

*HSAE v602 · engine `hydrosovereign-hsae` 6.7.3 · GPL-3.0 · Seifeldin M.G.
Alkhedir · University of Khartoum · ORCID 0000-0003-0821-2991*
