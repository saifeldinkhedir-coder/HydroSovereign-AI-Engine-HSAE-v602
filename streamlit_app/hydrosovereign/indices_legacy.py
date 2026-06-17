"""
indices_legacy.py — DEPRECATED heuristic indices (pre-6.8.0)
====================================================================
WARNING: These are the original heuristic index formulas. They combine
incommensurable quantities with undocumented constants and were found
to be scientifically unvalidated (see the 6.8.0 scientific revision).

They are retained ONLY for backward compatibility and emit a
DeprecationWarning. They will be REMOVED in v7.0.0.

Use the provenance-based indices in `hydrosovereign.indices` instead,
which compute from documented observations and return INSUFFICIENT_DATA
when real data are absent.
"""

from __future__ import annotations

import warnings as _warnings

_warnings.warn(
    "hydrosovereign.indices_legacy contains unvalidated heuristic "
    "formulas and is deprecated; use hydrosovereign.indices (provenance-"
    "based) instead. Legacy module will be removed in v7.0.0.",
    DeprecationWarning, stacklevel=2,
)

import numpy as np
import logging
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def _validate(runoff_c: float, cap_bcm: float,
              n_countries: int, dispute_level: int) -> None:
    """Validate AWSI inputs; raise ValueError on out-of-range values."""
    if not (0.0 < float(runoff_c) <= 1.0):
        raise ValueError(f"runoff_c must be in (0, 1], got {runoff_c}")
    if float(cap_bcm) < 0:
        raise ValueError(f"cap_bcm must be >= 0, got {cap_bcm}")
    if int(n_countries) < 1:
        raise ValueError(f"n_countries must be >= 1, got {n_countries}")
    if not (0 <= int(dispute_level) <= 4):
        raise ValueError(f"dispute_level must be in [0, 4], got {dispute_level}")

# ── ATDI ──────────────────────────────────────────────────
def compute_atdi(runoff_c:float, cap_bcm:float,
                 n_countries:int, dispute_level:int) -> float:
    """Alkhedir Transparency Deficit Index (ATDI).

    Art. 7 UNWC triggered when ATDI >= 40%.
    Validated: Blue Nile GERD → 43.5%.

    Parameters
    ----------
    runoff_c      : float  — Basin runoff coefficient (0-1)
    cap_bcm       : float  — Dam storage capacity (BCM)
    n_countries   : int    — Number of riparian countries
    dispute_level : int    — Geopolitical dispute intensity (1-4)

    Returns
    -------
    float — ATDI percentage (5-95)
    """
    _validate(runoff_c, cap_bcm, n_countries, dispute_level)
    base    = 10.0
    cap_    = min(float(cap_bcm) / 8.5, 11.0)
    state   = float(dispute_level) * 4.8
    multi   = (float(n_countries) - 2) * 2.0
    deficit = (1.0 - float(runoff_c)) * 6.0
    return round(min(95.0, max(5.0, base + cap_ + state + multi + deficit)), 1)


# ── AHIFD ─────────────────────────────────────────────────
def compute_ahifd(runoff_c:float, cap_bcm:float,
                  n_countries:int, dispute_level:int) -> float:
    """Alkhedir Human-Induced Flow Deficit (AHIFD).

    Quantifies fraction of natural downstream flow withheld.
    Validated: Blue Nile GERD → 20.0%.

    Returns
    -------
    float — AHIFD percentage (3-80)
    """
    _validate(runoff_c, cap_bcm, n_countries, dispute_level)
    base    = 3.0
    cap_    = min(float(cap_bcm) / 18.0, 6.0)
    deficit = (1.0 - float(runoff_c)) * 5.0
    state   = float(dispute_level) * 2.0
    multi   = (float(n_countries) - 2) * 1.5
    return round(min(80.0, max(3.0, base + cap_ + deficit + state + multi)), 1)


def compute_hifd(runoff_c:float, cap_bcm:float,
                 n_countries:int, dispute_level:int) -> float:
    """Backward compatibility alias for compute_ahifd()."""
    return compute_ahifd(runoff_c=runoff_c, cap_bcm=cap_bcm,
                         n_countries=n_countries, dispute_level=dispute_level)


# ── AFSF ──────────────────────────────────────────────────
def compute_afsf(runoff_c:float, cap_bcm:float,
                 n_countries:int, dispute_level:int) -> float:
    """Alkhedir Forensic Signal Factor (AFSF).

    Separates anthropogenic from natural anomalies.
    Art. 9 UNWC triggered when AFSF >= 0.50.

    Returns
    -------
    float — AFSF score (0.0-1.0)
    """
    atdi  = compute_atdi(runoff_c, cap_bcm, n_countries, dispute_level)
    ahifd = compute_ahifd(runoff_c, cap_bcm, n_countries, dispute_level)
    return round(min(1.0, max(0.0,
        (atdi / 100) * 0.6 + (ahifd / 80) * 0.4)), 3)


# ── AHLB ──────────────────────────────────────────────────
def compute_ahlb(runoff_c:float, cap_bcm:float,
                 n_countries:int, dispute_level:int,
                 q_sim:Optional[np.ndarray]=None,
                 q_obs:Optional[np.ndarray]=None) -> float:
    """Alkhedir HBV-Legal Bridge (AHLB).

    First published mechanism translating HBV-96 outputs
    directly to UNWC Arts. 5, 6, 7 legal triggers.

    Returns
    -------
    float — AHLB score (0.0-1.0). >= 0.4 triggers Art. 7.
    """
    atdi = compute_atdi(runoff_c, cap_bcm, n_countries, dispute_level)
    if q_sim is not None and q_obs is not None:
        qs = np.asarray(q_sim, float)
        qo = np.asarray(q_obs, float)
        n  = min(len(qs), len(qo))
        if qo[:n].mean() > 0:
            dev = abs(qs[:n].mean() - qo[:n].mean()) / qo[:n].mean()
            return round(min(1.0, atdi/100 * 0.7 + dev * 0.3), 3)
    return round(atdi / 100, 3)


# ── ASI ───────────────────────────────────────────────────
def compute_asi(runoff_c:float, cap_bcm:float,
                n_countries:int, dispute_level:int) -> float:
    """Alkhedir Sovereignty Index (ASI).

    Measures water governance balance.
    Art. 5 UNWC triggered when ASI < 0.50.

    Returns
    -------
    float — ASI score (0.05-0.95). Higher = more equitable.
    """
    atdi  = compute_atdi(runoff_c, cap_bcm, n_countries, dispute_level)
    ahifd = compute_ahifd(runoff_c, cap_bcm, n_countries, dispute_level)
    return round(max(0.05, min(0.95,
        1.0 - (atdi/100 * 0.6 + ahifd/80 * 0.4))), 3)


# ── ATCI ──────────────────────────────────────────────────
def compute_atci(runoff_c:float, cap_bcm:float,
                 n_countries:int, dispute_level:int) -> float:
    """Alkhedir Treaty Compliance Index (ATCI).

    Simultaneous assessment of all UNWC obligations:
    Arts. 5, 7, 9, 11, 17, 33.
    Validated: Blue Nile GERD → 70/100.

    Returns
    -------
    float — ATCI score (20-95). Higher = better compliance.
    """
    atdi  = compute_atdi(runoff_c, cap_bcm, n_countries, dispute_level)
    ahifd = compute_ahifd(runoff_c, cap_bcm, n_countries, dispute_level)
    return round(min(95.0, max(20.0,
        100.0 - atdi * 0.5 - ahifd * 0.4)), 1)


# ── Risk classification (legal tiers, matches QGIS plugin) ──
def classify_risk(atdi: float) -> str:
    """Classify basin risk by ATDI using UNWC legal thresholds.

    Tiers (aligned with HSAE QGIS plugin v6.0.12):
      CRITICAL >= 60  (Art. 33 dispute-settlement zone)
      HIGH     >= 40  (Art. 7 No Significant Harm triggered)
      MODERATE >= 25  (Art. 5 equitable-use attention)
      LOW      <  25

    Returns
    -------
    str — one of "CRITICAL", "HIGH", "MODERATE", "LOW".
    """
    if atdi >= 60:
        return "CRITICAL"
    if atdi >= 40:
        return "HIGH"
    if atdi >= 25:
        return "MODERATE"
    return "LOW"


def triggered_articles(atdi: float, ahifd: float) -> List[str]:
    """Return the list of UNWC 1997 articles triggered for given indices.

    Unified with legal.get_triggered_articles (single source of truth):
    Art.5 ERU and Art.9 Data Sharing are baseline duties returned for
    every basin; the rest are conditional on the indices.

    Thresholds: Art.7 NSH (ATDI>=40), Art.20 Env.Flow (AHIFD>=25),
    Art.33 Dispute (ATDI>=60), Art.35 Emergency (ATDI>=70).

    Examples
    --------
    >>> triggered_articles(43.6, 19.7)
    ['Art.5 ERU', 'Art.9 Data Sharing', 'Art.7 NSH']
    """
    arts: List[str] = ["Art.5 ERU", "Art.9 Data Sharing"]
    if atdi >= 40:
        arts.append("Art.7 NSH")
    if ahifd >= 25:
        arts.append("Art.20 Env.Flow")
    if atdi >= 60:
        arts.append("Art.33 Dispute")
    if atdi >= 70:
        arts.append("Art.35 Emergency")
    return arts


# ── Conflict Index ─────────────────────────────────────────
def compute_conflict_index(atdi:float, hifd:float,
                           dispute_level:int, n_countries:int) -> float:
    """Composite Conflict Index (CI).

    ``hifd`` accepts both HIFD and AHIFD values.

    Returns
    -------
    float — CI score (0.0-1.0). >= 0.55 = CRITICAL.
    """
    return round(min(1.0, max(0.0,
        0.40 * atdi/100
      + 0.25 * float(dispute_level)/4.0
      + 0.20 * float(hifd)/80.0
      + 0.10 * min(float(n_countries-2)*0.15, 0.1))), 3)


# ── Negotiation probability ────────────────────────────────
def _pneg_value(atdi: float, hifd: float, n_countries: int) -> float:
    """Raw P(successful negotiation) as a float in [0.05, 0.95]."""
    t1 = (atdi / 100) * 0.30
    t2 = (float(hifd) / 80) * 0.20
    t3 = min(0.10, (n_countries - 2) * 0.03)
    return round(max(0.05, min(0.95, 0.70 - t1 - t2 + t3)), 3)


def compute_negotiation_probability(atdi: float, hifd: float,
                                     n_countries: int,
                                     dispute_level: int = 2) -> Dict[str, object]:
    """Negotiation outlook given ATDI and AHIFD/HIFD.

    Returns
    -------
    dict with keys:
      p_success : float  — probability of successful negotiation (0.05-0.95)
      strategy  : str    — recommended negotiation strategy
      un_path   : str    — UNWC procedural pathway
      risk      : str    — CRITICAL / HIGH / MODERATE / LOW (legal tiers)
    """
    p = _pneg_value(atdi, hifd, n_countries)
    risk = classify_risk(atdi)
    if risk in ("CRITICAL", "HIGH"):
        strategy = "PCA Arbitration"
        un_path = "Art.33->PCA"
    elif risk == "MODERATE":
        strategy = "Joint Technical Commission"
        un_path = "Art.8->JTC"
    else:
        strategy = "Bilateral Negotiation"
        un_path = "Art.9 Regular Exchange"
    return {"p_success": p, "strategy": strategy,
            "un_path": un_path, "risk": risk}


# ── NSE ───────────────────────────────────────────────────
def compute_nse(q_obs:Union[np.ndarray,List[float]],
                q_sim:Union[np.ndarray,List[float]]) -> float:
    """Nash-Sutcliffe Efficiency (NSE).

    Returns
    -------
    float — NSE (-inf to 1.0). >= 0.5 = satisfactory.
    """
    obs = np.asarray(q_obs, float).ravel()
    sim = np.asarray(q_sim, float).ravel()
    if len(obs) != len(sim):
        raise ValueError(f"length mismatch: obs={len(obs)}, sim={len(sim)}")
    denom = np.sum((obs - obs.mean())**2)
    if denom < 1e-10:
        raise ValueError("zero variance in observations; NSE undefined")
    return round(float(1.0 - np.sum((obs - sim)**2) / denom), 3)


# ── KGE ───────────────────────────────────────────────────
def compute_kge(q_obs:Union[np.ndarray,List[float]],
                q_sim:Union[np.ndarray,List[float]]) -> float:
    """Kling-Gupta Efficiency (KGE).

    Returns
    -------
    float — KGE (-inf to 1.0). >= 0.5 = satisfactory.
    """
    obs = np.asarray(q_obs, float).ravel()
    sim = np.asarray(q_sim, float).ravel()
    if len(obs) != len(sim):
        raise ValueError(f"length mismatch: obs={len(obs)}, sim={len(sim)}")
    if obs.std() < 1e-10 or sim.std() < 1e-10:
        return 0.0
    r     = float(np.corrcoef(obs, sim)[0, 1])
    beta  = sim.mean() / (obs.mean() + 1e-10)
    gamma = (sim.std() / (sim.mean() + 1e-10)) / (obs.std() / (obs.mean() + 1e-10))
    return round(float(1.0 - ((r-1)**2 + (beta-1)**2 + (gamma-1)**2)**0.5), 3)


# ── WQI ───────────────────────────────────────────────────
def compute_wqi(measurements:Optional[Dict]=None) -> float:
    """Water Quality Index (WQI)."""
    if measurements is None:
        return 65.0
    return round(max(0.0, min(100.0,
        float(measurements.get("wqi", measurements.get("score", 65.0))))), 1)



# ── All at once ────────────────────────────────────────────
def compute_all_indices(runoff_c:float, cap_bcm:float,
                        n_countries:int, dispute_level:int,
                        q_obs:Optional[np.ndarray]=None,
                        q_sim:Optional[np.ndarray]=None,
                        wqi_measurements:Optional[Dict]=None,
                        ) -> Dict[str, float]:
    """Compute all six AWSI indices in a single call.

    Returns
    -------
    dict
        atdi, ahifd, afsf, ahlb, asi, atci,
        ci, p_negotiation, wqi
        (+ nse, kge if q_obs and q_sim provided)
    """
    atdi  = compute_atdi(runoff_c, cap_bcm, n_countries, dispute_level)
    ahifd = compute_ahifd(runoff_c, cap_bcm, n_countries, dispute_level)
    result: Dict[str, float] = {
        "atdi":          atdi,
        "ahifd":         ahifd,
        "afsf":  compute_afsf(runoff_c, cap_bcm, n_countries, dispute_level),
        "ahlb":  compute_ahlb(runoff_c, cap_bcm, n_countries, dispute_level,
                              q_sim=q_sim, q_obs=q_obs),
        "asi":   compute_asi(runoff_c, cap_bcm, n_countries, dispute_level),
        "atci":  compute_atci(runoff_c, cap_bcm, n_countries, dispute_level),
        "ci":    compute_conflict_index(atdi=atdi, hifd=ahifd,
                     dispute_level=dispute_level, n_countries=n_countries),
        "p_negotiation": _pneg_value(atdi, ahifd, n_countries),
        "wqi":   compute_wqi(wqi_measurements),
        "risk":  classify_risk(atdi),
        "articles": triggered_articles(atdi, ahifd),
    }
    if q_obs is not None and q_sim is not None:
        qo = np.asarray(q_obs, float).ravel()
        qs = np.asarray(q_sim, float).ravel()
        result["nse"] = compute_nse(qo, qs)
        result["kge"] = compute_kge(qo, qs)
    return result
