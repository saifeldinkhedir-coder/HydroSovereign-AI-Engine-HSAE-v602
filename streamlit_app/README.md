# HydroSovereign AI Engine (HSAE) — Live Platform (v6.0.14)

[![Streamlit](https://img.shields.io/badge/Streamlit-live-FF4B4B?logo=streamlit&logoColor=white)](https://hydrosovereign-ai-engine-hsae-v602-pysmdygmxj9xn6rpv8lmim.streamlit.app/)
[![Engine](https://img.shields.io/badge/engine-hydrosovereign%206.8.1-3775A9?logo=pypi&logoColor=white)](https://pypi.org/project/hydrosovereign/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](../LICENSE)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0003--0821--2991-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0000-0003-0821-2991)

The interactive web platform for the **HydroSovereign AI Engine** — automated,
satellite-driven assessment of transboundary water-law compliance under the
**UN Watercourses Convention (1997)**, built on the provenance-bound HSAE
engine. This edition is the scientifically-revised parallel project (v602).

> **Design rule.** No result is presented as a measurement unless it follows
> from documented observations. Where the required observed data are absent,
> the engine returns `INSUFFICIENT_DATA` rather than a fabricated value. Pages
> driven by modelled or synthetic series are clearly labelled
> **scenario / illustrative**.

---

## Table of contents

1. [What this platform does](#what-this-platform-does)
2. [Live deployment](#live-deployment)
3. [Run locally](#run-locally)
4. [Deploy your own on Streamlit Cloud](#deploy-your-own-on-streamlit-cloud)
5. [Page guide (30 modules)](#page-guide)
6. [The engine underneath](#the-engine-underneath)
7. [Scientific-integrity design](#scientific-integrity-design)
8. [Data sources](#data-sources)
9. [Project layout](#project-layout)
10. [Troubleshooting](#troubleshooting)
11. [Citation](#citation)

---

## What this platform does

HSAE links **live satellite observation** to **international water-law triggers**
for 26 globally-contested transboundary river basins. In one interface it:

- ingests satellite and reanalysis data (GPM, GRACE-FO, SMAP, Sentinel-1/2,
  GloFAS/ERA5, Open-Meteo, Microsoft Planetary Computer);
- runs the **HBV-96** rainfall-runoff model with SCE-UA calibration and an
  EnKF digital-twin mode;
- computes the **AWSI** family of indices (TDI, ATDI, HIFD, AFSF, AHLB, ASI,
  ATCI, AWGI) — empirical indices from observed series, normative composites
  with explicit weights;
- maps results to **UNWC 1997** articles (5, 7, 9, 20, 33, 35);
- classifies treaty properties with a **genuinely trained** TFDD model;
- exports reports (HTML / Excel / JSON dossier / GeoJSON) and QGIS layers.

---

## Live deployment

**App:** https://hydrosovereign-ai-engine-hsae-v602-pysmdygmxj9xn6rpv8lmim.streamlit.app/

The live app redeploys automatically on every push to `main`. To force a
refresh, open the app's **Manage app -> Reboot** in the Streamlit Cloud console.

---

## Run locally

```bash
git clone https://github.com/saifeldinkhedir-coder/HydroSovereign-AI-Engine-HSAE-v602.git
cd HydroSovereign-AI-Engine-HSAE-v602/streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Python 3.10-3.12 is recommended (the live app is pinned to 3.12 via
`runtime.txt`). The clean engine ships **both** as a bundled local package
(`streamlit_app/hydrosovereign/`, including the trained TFDD model) and as
a PyPI dependency, so the app runs even offline from PyPI.

---

## Deploy your own on Streamlit Cloud

1. Sign in at <https://share.streamlit.io> with GitHub.
2. **Create app -> Deploy a public app from GitHub.**
3. Fill in exactly:

   | Field | Value |
   |-------|-------|
   | Repository | `saifeldinkhedir-coder/HydroSovereign-AI-Engine-HSAE-v602` |
   | Branch | `main` |
   | **Main file path** | `streamlit_app/app.py` |

4. **Deploy.** Dependencies install from `streamlit_app/requirements.txt`;
   Python is pinned by `streamlit_app/runtime.txt` (`3.12`).

The heavy, optional satellite packages (`planetary-computer`, `rioxarray`,
`pystac-client`) are **intentionally not** in `requirements.txt`; they are
imported lazily inside `try/except` at runtime so a build failure in them can
never block the whole install. Direct GEE mode additionally needs your own
Earth Engine service-account credentials.

---

## Page guide

The sidebar groups 30 modules. Core analysis pages:

| Page | Purpose |
|------|---------|
| Intro | Overview, basin picker, honesty statement |
| v430 - Hybrid DSS | Decision-support: water balance -> indices -> legal verdict |
| v990 - Legal Nexus | UNWC article-by-article nexus for the active basin |
| Science - Water Balance | TDI water-balance from inflow/outflow/ET series |
| Legal - Treaty Engine | UNWC trigger logic and article mapping |
| Validation - GRDC | Skill scores (NSE/KGE/RMSE/R2) vs. **independent** benchmarks |
| HBV - Catchment Model | HBV-96 rainfall-runoff simulation |
| Operations Room | Multi-basin situational dashboard |
| Groundwater & Irrigation | Abstraction / irrigation balance |
| Water Quality | WQI and quality indicators |
| Audit Trail | SHA-256 provenance/audit chain |

Data & intelligence pages:

| Page | Purpose |
|------|---------|
| Real Data - APIs | Open-Meteo, GloFAS, USGS, GRACE-FO fetchers |
| AI - ML Engine | Ensemble (RF + MLP + GBM), anomaly detection, forecast |
| Climate - SSP Scenarios | SSP1-2.6 / 2-4.5 / 3-7.0 / 5-8.5 projections |
| GRACE-FO - Water Storage | Terrestrial water-storage anomalies |
| SMAP - Soil Moisture | Soil-moisture retrievals |
| GloFAS - 30-Day Forecast | Flood/forecast outlook |
| TDI - ATDI - AFSF Engine | The transparency-deficit index engine, step by step |
| HBV Calibration | SCE-UA parameter calibration |
| Uncertainty Analysis | Bayesian/uncertainty bounds |
| Sensitivity Analysis | Sobol / weight sensitivity |
| Sediment Transport | Sediment-flux estimation |
| Planetary Computer | Microsoft PC STAC sensor (optional) |

Legal, export & ops pages:

| Page | Purpose |
|------|---------|
| Treaty Diff - Compliance | Treaty text/provision comparison |
| Negotiation AI | **TFDD-trained treaty-feature classifier** (see below) |
| ICJ Dossier - Evidence | Evidence-dossier compiler |
| Alerts - Telegram | Alert thresholds / scheduler template |
| DevOps - CI/CD | Deployment notes and API template |
| Database - History | SQLite run history and cache |
| Export - Reports | HTML / Excel / JSON dossier export |
| Export to QGIS | GeoJSON / QGIS-layer export |
| Upload Real Data | Bring your own observed discharge |

---

## The engine underneath

The platform calls **`hydrosovereign` 6.8.1** for all
legally-relevant computation:

```python
from hydrosovereign import (
    DataPoint, DataQuality, DataRegistry,
    hifd_for_basin, compute_atdi, compute_awgi, classify_risk,
    TreatyClassifier, MODEL_CARD, validate_model_skill,
)
```

| Index | Kind | Inputs |
|-------|------|--------|
| `compute_tdi` / `compute_atdi` | empirical | observed inflow/outflow series |
| `compute_hifd` | empirical | independent observed `Q_nat`, `Q_obs` |
| `compute_afsf` | empirical | observed / natural anomaly, range |
| `compute_ahlb` | empirical | paired `q_sim`, `q_obs` (NSE) |
| `compute_asi` / `compute_atci` / `compute_awgi` | normative | declared weights + sensitivity |
| `correlation_matrix` | disclosure | cross-basin index values |

---

## Scientific-integrity design

This edition was rebuilt in response to external peer review. The platform
makes each fix visible:

1. **No fabricated results (objection #1).** A global banner labels modelled or
   synthetic series as *scenario / illustrative*; legally-relevant indices come
   only from provenance-verified observations or return `INSUFFICIENT_DATA`.
2. **Indices match their definitions (objection #2).** Empirical indices
   (TDI/ATDI/HIFD/AFSF/AHLB) are separated from normative composites
   (ASI/ATCI/AWGI) whose weights are explicit and sensitivity-tested.
3. **HIFD cannot collapse to a constant (objection #3).** It takes independent
   `Q_nat` and `Q_obs`; a shared data source is rejected.
4. **The model is genuinely trained (objection #4).** The **Negotiation AI**
   page uses `TreatyClassifier`, a GradientBoosting model trained on the TFDD
   treaties database (429 labelled treaties) with an honest model card
   (F1 ~ 0.57, ROC-AUC ~ 0.63, 5-fold CV, majority baseline). It classifies a
   documented treaty property (presence of a conflict-resolution mechanism) --
   **not** negotiation success/failure, which is not learnable from a database
   of concluded treaties.
5. **Validation is independent (objection #5).** The Validation page requires a
   benchmark that does **not** share the model's own forcing; a benchmark
   derived from the same precipitation is flagged as invalid for skill scoring.

---

## Data sources

- **TFDD International Freshwater Treaties Database** (Oregon State University) --
  trains the treaty-feature classifier.
- **GRDC** observed discharge -- for provenance-bound, legally-relevant indices.
- **GPM IMERG, GRACE-FO, SMAP, Sentinel-1/2, GloFAS/ERA5, Open-Meteo,
  Microsoft Planetary Computer** -- satellite / reanalysis forcings.

Bundled sample data lives in `streamlit_app/data/` (Nile GPM rainfall, SAR,
pre-computed GEE snapshots, the TFDD training CSV).

---

## Project layout

```
streamlit_app/
|- app.py                     # router + sidebar (30 pages)
|- requirements.txt           # startup-only deps (heavy optional ones omitted)
|- runtime.txt                # 3.12 (Streamlit Cloud Python pin)
|- negotiation_ai.py          # TFDD-trained classifier page (honest)
|- hsae_*.py                  # page modules (science, legal, hbv, ...)
|- gee_*.py / *_loader.py     # satellite/reanalysis connectors
|- hydrosovereign/            # bundled clean engine 6.8.1 + trained model
|- data/                      # sample datasets
```

---

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `ModuleNotFoundError` for a heavy package | It is optional and lazily imported; the page degrades gracefully. Do not add it to `requirements.txt` (it can abort the whole Cloud install). |
| App builds but a satellite page shows "demo/scenario" | Direct GEE / Planetary Computer needs your own credentials; without them the app uses bundled sample or ERA5-pattern data, clearly labelled. |
| Deploy fails right after install | Check the Cloud logs; ensure **Main file path** is `streamlit_app/app.py` and `runtime.txt` reads `3.12` (not `python-3.12`). |
| Edits not showing live | Streamlit Cloud redeploys on push; use **Manage app -> Reboot** to force it. |

---

## Citation

```bibtex
@software{alkhedir2026hsae,
  author    = {Alkhedir, Seifeldin M.G.},
  title     = {{HydroSovereign AI Engine (HSAE): provenance-bound transboundary
               water-law analysis}},
  year      = {2026},
  version   = {6.0.14},
  publisher = {PyPI + QGIS Plugin Repository + Streamlit},
  url       = {https://pypi.org/project/hydrosovereign/},
  orcid     = {0000-0003-0821-2991}
}
```

---

*HSAE live platform - v6.0.14 - engine `hydrosovereign` 6.8.1 - GPL-3.0 -
Seifeldin M.G. Alkhedir - University of Khartoum - ORCID 0000-0003-0821-2991*
