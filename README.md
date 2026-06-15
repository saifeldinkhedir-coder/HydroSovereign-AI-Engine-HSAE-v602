# HydroSovereign AI Engine (HSAE) — v6.0.2

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)]()
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)]()

A **provenance-bound, data-driven rebuild** of the HydroSovereign AI Engine for
transboundary water analysis under the UN Watercourses Convention (1997).

This is a clean parallel edition (`hydrosovereign-hsae`) that runs alongside the
legacy `hydrosovereign` package without replacing it.

## What is different in this edition

This rebuild was undertaken to put every result on a defensible scientific footing:

1. **No fabricated numbers.** Every index computes only from provenance-verified
   observations. When required observed data are absent, the engine returns
   `INSUFFICIENT_DATA` — it never substitutes a hard-coded constant.
2. **Indices match their definitions.** `HIFD` takes independent `Q_nat` and
   `Q_obs`, so it cannot algebraically collapse to a constant. `ATDI` is the
   empirical mean of per-period TDI from observed inflow/outflow.
3. **Empirical vs. normative are separated.** `ATDI` (empirical, hydrological)
   is distinct from `AWGI` (an explicit, normalised, sensitivity-tested
   governance composite). They are never conflated.
4. **The model is genuinely trained.** `TreatyClassifier` is a real
   gradient-boosting model trained on the TFDD treaties database, with an
   honest model card (F1, ROC-AUC, cross-validation, baseline). It classifies a
   documented treaty property — not negotiation success/failure.

## Install

```bash
pip install hydrosovereign-hsae
```

## Quick start — data with provenance

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
```

## Data sources

- **TFDD International Freshwater Treaties Database** (Oregon State University) —
  used to train the treaty-feature classifier.
- **GRDC** observed discharge — for legally-relevant index computation
  (contributed through the open registry).

## Honesty statement

Modest model skill and `INSUFFICIENT_DATA` results are reported as-is. The
engine is designed so that an absence of data produces an explicit non-result
rather than a misleading number.

---
*hydrosovereign-hsae v6.7.3 · GPL-3.0 · Seifeldin M.G. Alkhedir · ORCID 0000-0003-0821-2991*
