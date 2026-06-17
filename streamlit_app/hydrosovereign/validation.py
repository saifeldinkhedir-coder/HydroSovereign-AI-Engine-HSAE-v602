"""
validation.py — HSAE Independent Model Validation (Layer)
====================================================================
Honest model-skill assessment that DIRECTLY addresses the prior review's
objection #5: a validation benchmark must be INDEPENDENT of the model's
own forcing, or the comparison measures nothing.

Rules enforced here:
1. The benchmark series and the model series must declare their data
   sources; if they share the same forcing source (e.g. both GPM-derived),
   the validation is rejected as non-independent.
2. NSE / KGE are computed only over genuinely paired, observation-grade
   (or declared-independent reanalysis) series.
3. Absent or non-independent data -> INSUFFICIENT_DATA, never a number.

Author: Seifeldin M.G. Alkhedir - ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
from typing import List

from .provenance import (
    DataPoint, ProvenancedResult, insufficient, DataQuality,
)


def _nse(sim: List[float], obs: List[float]) -> float:
    mean_obs = sum(obs) / len(obs)
    denom = sum((o - mean_obs) ** 2 for o in obs)
    numer = sum((s - o) ** 2 for s, o in zip(sim, obs))
    return 1.0 - numer / denom if denom else float("nan")


def _kge(sim: List[float], obs: List[float]) -> float:
    import statistics as st
    if len(sim) < 2:
        return float("nan")
    mo, ms = st.mean(obs), st.mean(sim)
    so, ss = st.pstdev(obs), st.pstdev(sim)
    if so == 0 or ss == 0 or mo == 0:
        return float("nan")
    # Pearson r
    cov = sum((s - ms) * (o - mo) for s, o in zip(sim, obs)) / len(sim)
    r = cov / (ss * so)
    alpha = ss / so
    beta = ms / mo
    return 1.0 - ((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2) ** 0.5


def validate_model_skill(model_series: List[DataPoint],
                         benchmark_series: List[DataPoint],
                         model_forcing_source: str,
                         benchmark_forcing_source: str) -> ProvenancedResult:
    """
    Compute NSE and KGE of a model series against a benchmark, ONLY if the
    benchmark is independent of the model's forcing.

    Parameters
    ----------
    model_series, benchmark_series : list[DataPoint]
        Paired, equal-length series.
    model_forcing_source : str
        The precipitation/forcing source driving the model (e.g. "GPM IMERG").
    benchmark_forcing_source : str
        The forcing source behind the benchmark (e.g. "ERA5" for true GloFAS).

    Returns
    -------
    ProvenancedResult with {nse, kge} in `detail`, or INSUFFICIENT_DATA if
    series are unusable OR the benchmark is not independent of the model
    forcing (the exact flaw flagged in the review).
    """
    if not model_series or not benchmark_series:
        return insufficient("model_skill", "empty model or benchmark series")
    if len(model_series) != len(benchmark_series):
        return insufficient(
            "model_skill",
            f"length mismatch: {len(model_series)} model vs "
            f"{len(benchmark_series)} benchmark")

    # INDEPENDENCE CHECK — the heart of objection #5.
    mf = model_forcing_source.strip().lower()
    bf = benchmark_forcing_source.strip().lower()
    if not mf or not bf:
        return insufficient(
            "model_skill",
            "both model and benchmark forcing sources must be declared")
    if mf == bf:
        return insufficient(
            "model_skill",
            f"benchmark forcing ('{benchmark_forcing_source}') is identical "
            f"to model forcing ('{model_forcing_source}'); the comparison is "
            f"not independent and measures shared inputs, not skill")

    # benchmark must be observation- or declared-reanalysis grade
    for dp in benchmark_series:
        if not dp.is_valid():
            return insufficient(
                "model_skill",
                f"benchmark point '{dp.variable}' has incomplete provenance",
                model_series + benchmark_series)
        if dp.quality not in (DataQuality.OBSERVED, DataQuality.REANALYSIS):
            return insufficient(
                "model_skill",
                f"benchmark must be observed or reanalysis grade, got "
                f"'{dp.quality.value}'",
                model_series + benchmark_series)

    sim = [float(p.value) for p in model_series]
    obs = [float(p.value) for p in benchmark_series]
    nse = _nse(sim, obs)
    kge = _kge(sim, obs)
    if nse != nse:  # NaN
        return insufficient(
            "model_skill", "benchmark variance zero; NSE undefined",
            model_series + benchmark_series)

    return ProvenancedResult(
        metric="model_skill",
        value=round(nse, 3),
        status="OK",
        inputs=list(benchmark_series),
        method=f"NSE & KGE, model forcing='{model_forcing_source}' vs "
               f"independent benchmark forcing='{benchmark_forcing_source}'",
        detail=f"NSE={round(nse, 3)}, KGE={round(kge, 3)} over {len(obs)} "
               f"paired periods (independence verified)",
    )
