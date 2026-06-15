"""
indices_v2.py — HSAE Rebuilt Indices (data-driven, provenance-bound)
====================================================================
Rebuilt water-sovereignty indices that compute ONLY from independent,
provenance-verified observations supplied through the ingestion
registry. When the required observed data are absent, each function
returns an INSUFFICIENT_DATA ProvenancedResult — it never fabricates
a value from hard-coded constants.

This is the corrected replacement for the legacy indices.py. It is
built alongside the old code (not replacing it yet) so the new
behaviour can be verified before the legacy path is retired.

Key corrections vs. the legacy implementation
----------------------------------------------
1. HIFD takes Q_obs and Q_nat as INDEPENDENT inputs, so Q_nat does not
   algebraically cancel. Legacy built Q_obs = Q_nat*(1-tdi), which
   reduced HIFD to a renamed constant (tdi).
2. TDI is computed from observed inflow/outflow, not read from a table.
3. No index mixes incommensurable units behind undocumented constants.
   Each index is dimensionless-by-construction and documented.
4. Absent data -> INSUFFICIENT_DATA, never a placeholder number.

Author: Seifeldin M.G. Alkhedir - ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations

from .provenance import (
    DataPoint, ProvenancedResult, insufficient, require_legal_grade,
)
from .ingestion import DataRegistry


# ── TDI — Transparency / flow Deficit Index ───────────────────────
def compute_tdi(inflow: DataPoint, outflow: DataPoint) -> ProvenancedResult:
    """
    Transparency Deficit Index from observed adjusted inflow (I_adj) and
    observed downstream discharge (Q_obs):

        TDI = clip( (I_adj - Q_obs) / (I_adj + eps), 0, 1 )

    Both inputs must be observation-grade. Returns INSUFFICIENT_DATA
    otherwise. (Paper Eq. 1.)
    """
    gate = require_legal_grade("TDI", inflow, outflow)
    if gate is not None:
        return gate
    eps = 1e-9
    i_adj, q_obs = float(inflow.value), float(outflow.value)
    if i_adj <= 0:
        return insufficient("TDI", "inflow must be positive",
                            [inflow, outflow])
    tdi = (i_adj - q_obs) / (i_adj + eps)
    tdi = max(0.0, min(1.0, tdi))
    return ProvenancedResult(
        metric="TDI", value=round(tdi, 4), status="OK",
        inputs=[inflow, outflow],
        method="Eq.1: clip((I_adj - Q_obs)/(I_adj+eps), 0, 1)",
    )


# ── HIFD — Human-Induced Flow Deficit ─────────────────────────────
def compute_hifd(q_nat: DataPoint, q_obs: DataPoint) -> ProvenancedResult:
    """
    Human-Induced Flow Deficit from INDEPENDENT naturalised flow (Q_nat)
    and observed downstream flow (Q_obs):

        HIFD = (Q_nat - Q_obs) / Q_nat * 100

    Q_nat and Q_obs must come from independent observation-grade sources
    (e.g. pre-dam record vs. post-dam gauge). If Q_obs were derived from
    Q_nat, the metric would collapse to a constant — which is exactly the
    legacy bug this rebuild fixes. (Paper Eq. 6.)
    """
    gate = require_legal_grade("HIFD", q_nat, q_obs)
    if gate is not None:
        return gate
    qn, qo = float(q_nat.value), float(q_obs.value)
    if qn <= 0:
        return insufficient("HIFD", "Q_nat must be positive", [q_nat, q_obs])
    # Guard against the legacy degeneracy: identical source_ref for both
    # independent quantities is a red flag for non-independence.
    if (q_nat.source_ref == q_obs.source_ref
            and q_nat.source == q_obs.source):
        return insufficient(
            "HIFD",
            "Q_nat and Q_obs share an identical source; independent "
            "observations are required (legacy self-cancellation guard)",
            [q_nat, q_obs])
    hifd = (qn - qo) / qn * 100.0
    hifd = max(0.0, min(100.0, hifd))
    return ProvenancedResult(
        metric="HIFD", value=round(hifd, 1), status="OK",
        inputs=[q_nat, q_obs],
        method="Eq.6: (Q_nat - Q_obs)/Q_nat * 100",
    )


# ── Registry-driven convenience wrappers ──────────────────────────
def hifd_for_basin(reg: DataRegistry, basin_id: str) -> ProvenancedResult:
    """
    Compute HIFD for a basin using whatever observation-grade Q_nat and
    Q_obs are present in the registry. Returns INSUFFICIENT_DATA if
    either is missing — no fabrication.
    """
    q_nat = reg.get(basin_id, "Q_nat", legal_grade_only=True)
    q_obs = reg.get(basin_id, "Q_obs", legal_grade_only=True)
    if q_nat is None or q_obs is None:
        missing = [v for v, dp in (("Q_nat", q_nat), ("Q_obs", q_obs))
                   if dp is None]
        return insufficient(
            "HIFD",
            f"basin '{basin_id}' lacks observation-grade {', '.join(missing)}")
    return compute_hifd(q_nat, q_obs)


def tdi_for_basin(reg: DataRegistry, basin_id: str) -> ProvenancedResult:
    """TDI for a basin from registry observations, else INSUFFICIENT_DATA."""
    i_adj = reg.get(basin_id, "I_adj", legal_grade_only=True)
    q_obs = reg.get(basin_id, "Q_obs", legal_grade_only=True)
    if i_adj is None or q_obs is None:
        missing = [v for v, dp in (("I_adj", i_adj), ("Q_obs", q_obs))
                   if dp is None]
        return insufficient(
            "TDI",
            f"basin '{basin_id}' lacks observation-grade {', '.join(missing)}")
    return compute_tdi(i_adj, q_obs)


# ══════════════════════════════════════════════════════════════════
#  ATDI — empirical transparency-deficit measure (Option A)
#  Pure hydrological measure: mean of per-period TDI from observed
#  inflow/outflow. No constants, no unit mixing. Matches paper Eq.1+2.
# ══════════════════════════════════════════════════════════════════
def compute_atdi(inflow_series: "list[DataPoint]",
                 outflow_series: "list[DataPoint]") -> ProvenancedResult:
    """
    ATDI = mean(TDI) * 100 over matched observed inflow/outflow periods.

    Each period's TDI uses Eq.1; ATDI is their mean x 100 (Eq.2). Every
    input must be observation-grade and the two series must be the same
    length (paired by period). Returns INSUFFICIENT_DATA otherwise.

    This is an EMPIRICAL measure: it reports what the observed data say,
    with no governance constants. (Option A.)
    """
    if not inflow_series or not outflow_series:
        return insufficient("ATDI", "empty inflow or outflow series")
    if len(inflow_series) != len(outflow_series):
        return insufficient(
            "ATDI",
            f"series length mismatch: {len(inflow_series)} inflow vs "
            f"{len(outflow_series)} outflow periods")

    tdis = []
    inputs = []
    for i, (i_adj, q_obs) in enumerate(zip(inflow_series, outflow_series)):
        per = compute_tdi(i_adj, q_obs)
        if not per.ok:
            return insufficient(
                "ATDI",
                f"period {i}: {per.detail}",
                inflow_series + outflow_series)
        tdis.append(per.value)
        inputs.extend([i_adj, q_obs])

    atdi = sum(tdis) / len(tdis) * 100.0
    return ProvenancedResult(
        metric="ATDI", value=round(atdi, 1), status="OK",
        inputs=inputs,
        method="Eq.2: mean(TDI)*100 over observed inflow/outflow periods",
        detail=f"averaged over {len(tdis)} observed periods",
    )


def atdi_for_basin(reg: DataRegistry, basin_id: str) -> ProvenancedResult:
    """
    ATDI for a basin from registry time series. Expects paired
    'I_adj_series' / 'Q_obs_series' variables (one DataPoint per period).
    Returns INSUFFICIENT_DATA if either series is absent.
    """
    inflow = [r.data_point for r in reg.records(basin_id)
              if r.data_point.variable == "I_adj"
              and r.data_point.is_legal_grade()]
    outflow = [r.data_point for r in reg.records(basin_id)
               if r.data_point.variable == "Q_obs"
               and r.data_point.is_legal_grade()]
    if not inflow or not outflow:
        missing = [v for v, s in (("I_adj", inflow), ("Q_obs", outflow))
                   if not s]
        return insufficient(
            "ATDI",
            f"basin '{basin_id}' lacks observation-grade {', '.join(missing)} "
            f"series")
    return compute_atdi(inflow, outflow)


# ══════════════════════════════════════════════════════════════════
#  AWGI — Alkhedir Water Governance Index (Option B)
#  Explicit composite of NORMALISED factors with JUSTIFIED, published,
#  sensitivity-testable weights. A normative risk index, kept separate
#  from the empirical ATDI so the two are never conflated.
# ══════════════════════════════════════════════════════════════════

# Default weights. Each is documented and the set sums to 1.0. These are
# the published defaults; callers may override and run sensitivity tests.
AWGI_DEFAULT_WEIGHTS = {
    "transparency": 0.40,   # weight of observed transparency deficit
    "dispute":      0.30,   # weight of institutional dispute level
    "multiplicity": 0.15,   # weight of number of riparian states
    "regulation":   0.15,   # weight of flow-regulation intensity
}

# Normalisation references (documented, not hidden in the formula).
AWGI_DISPUTE_MAX = 5.0      # dispute level is ordinal 0..5 (TFDD-style)
AWGI_COUNTRIES_REF = 10.0   # riparian count normalised against 10 states


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_awgi(transparency_deficit: float,
                 dispute_level: float,
                 n_countries: int,
                 regulation_intensity: float,
                 weights: "dict | None" = None) -> dict:
    """
    Alkhedir Water Governance Index — explicit normalised composite.

    Parameters (all placed on a common [0,1] scale before weighting)
    ----------
    transparency_deficit : float
        Observed transparency deficit in [0,1] (e.g. ATDI/100). EMPIRICAL.
    dispute_level : float
        Institutional dispute level, ordinal 0..AWGI_DISPUTE_MAX. NORMATIVE.
    n_countries : int
        Number of riparian states (>=1). Normalised vs AWGI_COUNTRIES_REF.
    regulation_intensity : float
        Flow-regulation intensity in [0,1] (e.g. storage / annual flow,
        capped at 1). EMPIRICAL.
    weights : dict, optional
        Override AWGI_DEFAULT_WEIGHTS to run sensitivity analysis.

    Returns
    -------
    dict with the score, the normalised factors, and the weights used —
    so the computation is fully transparent and reproducible.

    Notes
    -----
    Unlike the legacy ATDI, every term here is dimensionless in [0,1]
    BEFORE weighting, the weights are explicit and sum to 1, and they can
    be overridden for sensitivity testing. This is a NORMATIVE risk index
    and must not be reported as an empirical measurement.
    """
    w = dict(AWGI_DEFAULT_WEIGHTS if weights is None else weights)
    wsum = sum(w.values())
    if abs(wsum - 1.0) > 1e-6:
        raise ValueError(f"AWGI weights must sum to 1.0 (got {wsum})")

    factors = {
        "transparency": _clip01(transparency_deficit),
        "dispute":      _clip01(dispute_level / AWGI_DISPUTE_MAX),
        "multiplicity": _clip01((n_countries - 1) / (AWGI_COUNTRIES_REF - 1)),
        "regulation":   _clip01(regulation_intensity),
    }
    score = sum(w[k] * factors[k] for k in factors)
    return {
        "metric": "AWGI",
        "score": round(score, 4),
        "score_pct": round(score * 100, 1),
        "factors": {k: round(v, 4) for k, v in factors.items()},
        "weights": w,
        "kind": "normative-composite",
        "note": "Normative risk index; not an empirical measurement.",
    }


def awgi_sensitivity(transparency_deficit: float, dispute_level: float,
                     n_countries: int, regulation_intensity: float,
                     perturbation: float = 0.10) -> dict:
    """
    Simple one-at-a-time sensitivity check: perturb each weight by
    +/-perturbation (renormalising the rest) and report the resulting
    spread in the AWGI score. Lets reviewers see how weight choices
    affect the outcome.
    """
    base = compute_awgi(transparency_deficit, dispute_level,
                        n_countries, regulation_intensity)["score"]
    spread = {}
    for key in AWGI_DEFAULT_WEIGHTS:
        scores = []
        for delta in (-perturbation, perturbation):
            w = dict(AWGI_DEFAULT_WEIGHTS)
            w[key] = _clip01(w[key] + delta)
            # renormalise others proportionally
            others = sum(v for k, v in w.items() if k != key)
            target_others = 1.0 - w[key]
            if others > 0:
                for k in w:
                    if k != key:
                        w[k] = w[k] / others * target_others
            scores.append(compute_awgi(transparency_deficit, dispute_level,
                                       n_countries, regulation_intensity,
                                       weights=w)["score"])
        spread[key] = round(max(scores) - min(scores), 4)
    return {
        "base_score": base,
        "weight_sensitivity": spread,
        "max_sensitivity": max(spread.values()) if spread else 0.0,
    }


# ── Risk classification (operates on an already-computed ATDI value) ──
# These are the legal-tier thresholds. classify_risk does NOT compute
# ATDI; it only labels a value that was computed empirically upstream.
RISK_CRITICAL = 60.0   # ATDI >= 60  -> Art.33 dispute zone
RISK_HIGH = 40.0       # ATDI >= 40  -> Art.7 No Significant Harm
RISK_MODERATE = 25.0   # ATDI >= 25  -> Art.5 equitable-use attention


def classify_risk(atdi: float) -> str:
    """
    Classify an ALREADY-COMPUTED ATDI percentage into a legal risk tier.

    This is a labelling function only — it never fabricates ATDI. Callers
    must pass an ATDI produced empirically (compute_atdi) from observed
    data, or handle INSUFFICIENT_DATA before calling.
    """
    if atdi is None:
        raise ValueError("classify_risk requires a computed ATDI value")
    if atdi >= RISK_CRITICAL:
        return "CRITICAL"
    if atdi >= RISK_HIGH:
        return "HIGH"
    if atdi >= RISK_MODERATE:
        return "MODERATE"
    return "LOW"


# ══════════════════════════════════════════════════════════════════
#  AFSF — Alkhedir Forensic Signal Factor (EMPIRICAL)
#  Separates human-induced from natural signal using TWO independent
#  observed anomaly series. Returns INSUFFICIENT_DATA without them.
# ══════════════════════════════════════════════════════════════════
def compute_afsf(observed_anomaly: DataPoint,
                 natural_anomaly: DataPoint,
                 signal_range: DataPoint) -> ProvenancedResult:
    """
    Forensic Signal Factor = |observed_anomaly - natural_anomaly| / range,
    clipped to [0,1]. Measures how far the observed signal departs from the
    natural-baseline signal, normalised by the signal range.

    All three inputs must be observation-grade and independent (the
    observed and natural anomalies must not share a source). Returns
    INSUFFICIENT_DATA otherwise. EMPIRICAL measure.
    """
    gate = require_legal_grade(
        "AFSF", observed_anomaly, natural_anomaly, signal_range)
    if gate is not None:
        return gate
    if (observed_anomaly.source == natural_anomaly.source
            and observed_anomaly.source_ref == natural_anomaly.source_ref):
        return insufficient(
            "AFSF",
            "observed and natural anomalies share an identical source; "
            "independent series are required",
            [observed_anomaly, natural_anomaly, signal_range])
    rng = float(signal_range.value)
    if rng <= 0:
        return insufficient("AFSF", "signal range must be positive",
                            [observed_anomaly, natural_anomaly, signal_range])
    afsf = abs(float(observed_anomaly.value)
               - float(natural_anomaly.value)) / rng
    afsf = max(0.0, min(1.0, afsf))
    return ProvenancedResult(
        metric="AFSF", value=round(afsf, 3), status="OK",
        inputs=[observed_anomaly, natural_anomaly, signal_range],
        method="|observed_anomaly - natural_anomaly| / range, clipped [0,1]",
    )


# ══════════════════════════════════════════════════════════════════
#  AHLB — Alkhedir HBV-Legal Bridge (EMPIRICAL / interpretive)
#  Translates real HBV-96 model skill (sim vs obs) into a documented
#  legal-confidence score. Requires genuine paired sim/obs series.
# ══════════════════════════════════════════════════════════════════
def compute_ahlb(q_sim_series: "list[DataPoint]",
                 q_obs_series: "list[DataPoint]") -> ProvenancedResult:
    """
    HBV-Legal Bridge. Computes the Nash-Sutcliffe Efficiency (NSE) between
    a genuine HBV-96 simulated series and an independent observed series,
    then maps NSE to a [0,1] legal-confidence score:

        AHLB = clip(NSE, 0, 1)

    This expresses how much legal weight the modelled hydrology can bear:
    high model skill -> higher confidence that modelled deficits reflect
    reality. Requires real paired series of equal length; observed series
    must be observation-grade. INSUFFICIENT_DATA otherwise. The score is
    interpretive and must be reported with its NSE.
    """
    if not q_sim_series or not q_obs_series:
        return insufficient("AHLB", "empty simulated or observed series")
    if len(q_sim_series) != len(q_obs_series):
        return insufficient(
            "AHLB",
            f"series length mismatch: {len(q_sim_series)} sim vs "
            f"{len(q_obs_series)} obs")
    # observed series must be observation-grade
    gate = require_legal_grade("AHLB", *q_obs_series)
    if gate is not None:
        return gate

    sim = [float(p.value) for p in q_sim_series]
    obs = [float(p.value) for p in q_obs_series]
    mean_obs = sum(obs) / len(obs)
    denom = sum((o - mean_obs) ** 2 for o in obs)
    if denom == 0:
        return insufficient(
            "AHLB", "observed variance is zero; NSE undefined",
            q_sim_series + q_obs_series)
    numer = sum((s - o) ** 2 for s, o in zip(sim, obs))
    nse = 1.0 - numer / denom
    ahlb = max(0.0, min(1.0, nse))
    return ProvenancedResult(
        metric="AHLB", value=round(ahlb, 3), status="OK",
        inputs=list(q_obs_series),
        method="clip(NSE(sim,obs), 0, 1)",
        detail=f"NSE={round(nse, 3)} over {len(obs)} paired periods",
    )


# ══════════════════════════════════════════════════════════════════
#  ASI — Alkhedir Sovereignty Index (NORMATIVE composite)
#  Explicit normalised composite of governance-balance factors. Like
#  AWGI: factors in [0,1], justified weights summing to 1, sensitivity.
# ══════════════════════════════════════════════════════════════════
ASI_DEFAULT_WEIGHTS = {
    "equity":       0.40,   # equitable-utilisation balance (higher = fairer)
    "cooperation":  0.35,   # institutional cooperation level
    "data_sharing": 0.25,   # transparency / data-exchange practice
}


def compute_asi(equity_balance: float,
                cooperation_level: float,
                data_sharing_level: float,
                weights: "dict | None" = None) -> dict:
    """
    Alkhedir Sovereignty Index — explicit normalised governance composite.

    All inputs in [0,1]; higher ASI = healthier shared-sovereignty balance
    (the inverse sense of a risk index). Weights are explicit, sum to 1,
    and overridable for sensitivity testing. NORMATIVE — not an empirical
    measurement.
    """
    w = dict(ASI_DEFAULT_WEIGHTS if weights is None else weights)
    if abs(sum(w.values()) - 1.0) > 1e-6:
        raise ValueError(f"ASI weights must sum to 1.0 (got {sum(w.values())})")
    factors = {
        "equity":       _clip01(equity_balance),
        "cooperation":  _clip01(cooperation_level),
        "data_sharing": _clip01(data_sharing_level),
    }
    score = sum(w[k] * factors[k] for k in factors)
    return {
        "metric": "ASI",
        "score": round(score, 4),
        "factors": {k: round(v, 4) for k, v in factors.items()},
        "weights": w,
        "kind": "normative-composite",
        "note": "Normative governance index; higher = healthier balance. "
                "Not an empirical measurement.",
    }


# ══════════════════════════════════════════════════════════════════
#  ATCI — Alkhedir Treaty Compliance Index (NORMATIVE composite)
#  Explicit 0-100 composite summarising compliance posture across the
#  relevant UNWC articles. Transparent inputs, justified weights.
# ══════════════════════════════════════════════════════════════════
ATCI_DEFAULT_WEIGHTS = {
    "no_harm":       0.30,   # Art.7 posture (1 - transparency_deficit)
    "equitable_use": 0.25,   # Art.5 posture (ASI)
    "data_exchange": 0.20,   # Art.9 posture (data-sharing)
    "eco_flow":      0.15,   # Art.20 posture (1 - flow_deficit)
    "dispute_mech":  0.10,   # Art.33 posture (has dispute mechanism)
}


def compute_atci(no_harm_posture: float,
                 equitable_use_posture: float,
                 data_exchange_posture: float,
                 eco_flow_posture: float,
                 dispute_mech_posture: float,
                 weights: "dict | None" = None) -> dict:
    """
    Alkhedir Treaty Compliance Index — explicit 0-100 composite of
    per-article compliance postures (each in [0,1], higher = better
    compliance). Weights explicit, sum to 1, overridable. NORMATIVE.

    Returns a 0-100 headline (score_100) plus the factor/weight breakdown
    so the composite is fully transparent and reproducible.
    """
    w = dict(ATCI_DEFAULT_WEIGHTS if weights is None else weights)
    if abs(sum(w.values()) - 1.0) > 1e-6:
        raise ValueError(
            f"ATCI weights must sum to 1.0 (got {sum(w.values())})")
    factors = {
        "no_harm":       _clip01(no_harm_posture),
        "equitable_use": _clip01(equitable_use_posture),
        "data_exchange": _clip01(data_exchange_posture),
        "eco_flow":      _clip01(eco_flow_posture),
        "dispute_mech":  _clip01(dispute_mech_posture),
    }
    score = sum(w[k] * factors[k] for k in factors)
    return {
        "metric": "ATCI",
        "score": round(score, 4),
        "score_100": round(score * 100, 1),
        "factors": {k: round(v, 4) for k, v in factors.items()},
        "weights": w,
        "kind": "normative-composite",
        "note": "Normative compliance composite (0-100); higher = better "
                "compliance posture. Not an empirical measurement.",
    }
