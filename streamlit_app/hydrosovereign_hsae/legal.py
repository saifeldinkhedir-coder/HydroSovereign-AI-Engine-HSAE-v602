"""
legal.py — HSAE UN Watercourses Convention 1997 Legal Engine
====================================================================
Automated UNWC Article triggering and legal assessment.

SINGLE SOURCE OF TRUTH for article-trigger logic. Both the QGIS plugin
and indices.triggered_articles() delegate here so every surface returns
the same articles for the same indices.

Threshold model (unified with the legal risk tiers in indices.classify_risk):
    CRITICAL  ATDI >= 60   -> Art.33 dispute settlement zone
    HIGH      ATDI >= 40   -> Art.7 No Significant Harm triggered
    MODERATE  ATDI >= 25   -> Art.5 equitable-use attention
    Env.flow  AHIFD >= 25  -> Art.20 ecosystem protection
    Emergency ATDI >= 70   -> Art.35 emergency notification

Baseline duties (Art.5 ERU, Art.9 Data Sharing) apply continuously to
every shared watercourse and are always returned.

Author: Seifeldin M.G. Alkhedir - ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
from typing import List
from .indices import classify_risk  # noqa: F401  (re-export)

# Unified thresholds (percent)
ART7_NSH_THRESHOLD = 40.0          # ATDI - No Significant Harm
ART20_ENVFLOW_THRESHOLD = 25.0     # AHIFD - ecosystem / environmental flow
ART33_DISPUTE_THRESHOLD = 60.0     # ATDI - dispute settlement (= CRITICAL tier)
ART35_EMERGENCY_THRESHOLD = 70.0   # ATDI - emergency notification


def check_art7_nsh(atdi: float) -> bool:
    """Art.7 - No Significant Harm. Triggered when ATDI >= 40%."""
    return atdi >= ART7_NSH_THRESHOLD


def check_art20_envflow(ahifd: float) -> bool:
    """Art.20 - Protection of Ecosystems. Triggered when AHIFD >= 25%."""
    return ahifd >= ART20_ENVFLOW_THRESHOLD


def check_art33_dispute(atdi: float) -> bool:
    """Art.33 - Settlement of Disputes. Triggered when ATDI >= 60%
    (the CRITICAL legal tier)."""
    return atdi >= ART33_DISPUTE_THRESHOLD


def check_art35_emergency(atdi: float) -> bool:
    """Art.35 - Emergency Situations. Triggered when ATDI >= 70%."""
    return atdi >= ART35_EMERGENCY_THRESHOLD


def get_triggered_articles(atdi: float, ahifd: float) -> List[str]:
    """
    Return all UNWC 1997 articles triggered by basin indices.

    Art.5 (Equitable & Reasonable Utilisation) and Art.9 (Regular Data
    Exchange) are baseline duties returned for every basin. The remaining
    articles are conditional on the indices crossing their thresholds.

    Parameters
    ----------
    atdi : float
        ATDI percentage (5-95).
    ahifd : float
        AHIFD percentage (3-80).

    Returns
    -------
    list of str
        Triggered UNWC articles, baseline first.

    Examples
    --------
    >>> get_triggered_articles(43.6, 19.7)
    ['Art.5 ERU', 'Art.9 Data Sharing', 'Art.7 NSH']
    """
    arts = ["Art.5 ERU", "Art.9 Data Sharing"]
    if check_art7_nsh(atdi):
        arts.append("Art.7 NSH")
    if check_art20_envflow(ahifd):
        arts.append("Art.20 Env.Flow")
    if check_art33_dispute(atdi):
        arts.append("Art.33 Dispute")
    if check_art35_emergency(atdi):
        arts.append("Art.35 Emergency")
    return arts


def get_legal_assessment(atdi: float, ahifd: float,
                         dispute_level: int, n_countries: int) -> dict:
    """
    Full legal assessment under UNWC 1997.

    Returns triggered articles, recommended action, and the escalation
    pathway. Pathway bands are aligned with the unified thresholds:
        ATDI >= 70  -> Art.35 emergency
        ATDI >= 60  -> Art.33 dispute settlement (PCA/ICJ)
        ATDI >= 40  -> Art.24 Joint Technical Committee + Art.8 exchange
        else        -> Art.9 regular data exchange
    """
    articles = get_triggered_articles(atdi, ahifd)

    if atdi >= ART35_EMERGENCY_THRESHOLD:
        recommendation = "Emergency notification under Art.35 UNWC required"
        pathway = "ICJ Emergency Relief + Art.35"
    elif atdi >= ART33_DISPUTE_THRESHOLD:
        recommendation = "Formal dispute resolution under Art.33 UNWC"
        pathway = "PCA Arbitration or ICJ"
    elif atdi >= ART7_NSH_THRESHOLD:
        recommendation = "Joint Technical Committee under Art.24 UNWC"
        pathway = "Art.8 Information Exchange + Art.24 JMO"
    else:
        recommendation = "Regular data exchange under Art.9 UNWC"
        pathway = "Art.9 Regular Exchange"

    return {
        "articles":        articles,
        "n_articles":      len(articles),
        "recommendation":  recommendation,
        "pathway":         pathway,
        "risk":            classify_risk(atdi),
        "art7_nsh":        check_art7_nsh(atdi),
        "art20_envflow":   check_art20_envflow(ahifd),
        "art33_dispute":   check_art33_dispute(atdi),
        "art35_emergency": check_art35_emergency(atdi),
    }
