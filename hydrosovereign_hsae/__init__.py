"""
HydroSovereign-AI-Engine (HSAE) v6.0.2 — clean, provenance-bound rebuild
========================================================================
A parallel, scientifically-rebuilt edition of HSAE. Every index computes
only from provenance-verified observations; absent data yield
INSUFFICIENT_DATA rather than fabricated numbers. The treaty classifier
is genuinely trained on the TFDD database with honestly-reported metrics.

This package (hydrosovereign-hsae) is independent of the legacy
`hydrosovereign` package; it does not import or depend on it.

Author: Seifeldin M.G. Alkhedir - ORCID: 0000-0003-0821-2991
"""

__version__ = "6.7.3"
__author__ = "Seifeldin M.G. Alkhedir"
__orcid__ = "0000-0003-0821-2991"

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
    "DataPoint", "DataQuality", "ProvenancedResult",
    "InsufficientDataError", "INSUFFICIENT_DATA",
    "DataRegistry", "ContributionRecord", "RejectedContribution",
    "compute_tdi", "compute_hifd", "compute_atdi",
    "hifd_for_basin", "tdi_for_basin", "atdi_for_basin",
    "compute_awgi", "awgi_sensitivity", "classify_risk",
    "compute_asi", "compute_ahlb", "compute_afsf", "compute_atci",
    "correlation_matrix",
    "get_triggered_articles", "get_legal_assessment",
    "TreatyClassifier", "MODEL_CARD",
    "validate_model_skill",
]
