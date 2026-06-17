"""
HydroSovereign AI Engine (HSAE) v6.8.0 — Major Scientific Revision
====================================================================
Satellite-driven transboundary water-law analysis under UNWC 1997.

v6.8.0 is a major scientific revision. The index engine is rebuilt to be
provenance-bound: every index computes only from documented observations
and returns INSUFFICIENT_DATA when real data are absent, rather than a
fabricated value. The treaty classifier is genuinely trained on the TFDD
database with an honest model card, and model validation now rejects any
benchmark that shares the model's own forcing.

The previous heuristic formulas remain available, deprecated, in
`hydrosovereign.indices_legacy` (emitting DeprecationWarning) and will be
removed in v7.0.0. See README and CHANGELOG for the migration guide.

Author:  Seifeldin M.G. Alkhedir
ORCID:   0000-0003-0821-2991
DOI:     10.5281/zenodo.19180160
License: GPL-3.0
"""

__version__ = "6.8.1"
__author__ = "Seifeldin M.G. Alkhedir"
__email__ = "saifeldinkhedir@gmail.com"
__orcid__ = "0000-0003-0821-2991"
__doi__ = "10.5281/zenodo.19180160"
__license__ = "GPL-3.0"
__plugin_id__ = "5040"
__qgis_ver__ = "6.0.14"

# ── Primary API: provenance-bound engine (v6.8.0+) ────────────────
from .provenance import (
    DataPoint, DataQuality, ProvenancedResult,
    InsufficientDataError, INSUFFICIENT_DATA,
)
from .ingestion import DataRegistry, ContributionRecord, RejectedContribution
from .indices import (
    compute_tdi, compute_hifd, compute_atdi,
    hifd_for_basin, tdi_for_basin, atdi_for_basin,
    compute_awgi, awgi_sensitivity, classify_risk,
    compute_afsf, compute_ahlb, compute_asi, compute_atci,
    correlation_matrix,
)
from .legal import get_triggered_articles, get_legal_assessment
from .treaty_classifier import TreatyClassifier, MODEL_CARD
from .validation import validate_model_skill

__all__ = [
    # provenance foundation
    "DataPoint", "DataQuality", "ProvenancedResult",
    "InsufficientDataError", "INSUFFICIENT_DATA",
    "DataRegistry", "ContributionRecord", "RejectedContribution",
    # provenance-bound indices
    "compute_tdi", "compute_hifd", "compute_atdi",
    "hifd_for_basin", "tdi_for_basin", "atdi_for_basin",
    "compute_awgi", "awgi_sensitivity", "classify_risk",
    "compute_afsf", "compute_ahlb", "compute_asi", "compute_atci",
    "correlation_matrix",
    # legal + model + validation
    "get_triggered_articles", "get_legal_assessment",
    "TreatyClassifier", "MODEL_CARD",
    "validate_model_skill",
]

# Note: legacy heuristic indices are intentionally NOT re-exported here.
# Import them explicitly from hydrosovereign.indices_legacy if needed
# (they emit DeprecationWarning and will be removed in v7.0.0).
