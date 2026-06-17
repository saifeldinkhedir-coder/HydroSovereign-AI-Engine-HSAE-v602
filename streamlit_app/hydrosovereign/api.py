"""
api.py — HSAE v6.2.0 Unified High-Level API
=============================================
Single-call basin analysis as recommended by ChatGPT review:
  "Add a clear entry point: analyze_basin(data)"

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
import logging
from typing import Optional, Dict

from .indices  import compute_all_indices
from .legal    import get_legal_assessment
from .alerts   import check_atdi_alert, check_hifd_alert, AlertLevel
from .basins   import BasinRegistry, BASINS_26

logger = logging.getLogger(__name__)


def analyze_basin(
    name: Optional[str] = None,
    runoff_c: Optional[float] = None,
    cap_bcm: Optional[float] = None,
    n_countries: Optional[int] = None,
    dispute_level: Optional[int] = None,
    area_km2: Optional[float] = None,
    wqi_measurements: Optional[Dict] = None,
    include_negotiation: bool = True,
    include_legal: bool = True,
) -> dict:
    """
    Full basin analysis in one call — HSAE unified entry point.

    Provide either basin name (auto-loads parameters) or all parameters manually.

    Parameters
    ----------
    name : str, optional
        Basin name from registry (e.g. "Blue Nile (GERD)"). Auto-fills parameters.
    runoff_c : float, optional
        Runoff coefficient 0–1. Required if name not given.
    cap_bcm : float, optional
        Dam storage capacity BCM.
    n_countries : int, optional
        Number of riparian states.
    dispute_level : int, optional
        TFDD/ICOW dispute level 0–4.
    area_km2 : float, optional
        Catchment area km². Used for conflict sensitivity.
    wqi_measurements : dict, optional
        Physicochemical measurements for WQI (ph, do, bod, turbidity...).
    include_negotiation : bool
        Include Negotiation AI prediction. Default = True.
    include_legal : bool
        Include UNWC legal assessment. Default = True.

    Returns
    -------
    dict
        Complete basin analysis:
        - indices  : atdi, hifd, wqi, ci, nse, kge
        - alerts   : atdi_alert, hifd_alert
        - legal    : articles, recommendation, pathway
        - ai       : negotiation result
        - metadata : basin name, parameters used

    Examples
    --------
    >>> # From registry
    >>> result = analyze_basin("Blue Nile (GERD)")
    >>> print(result["indices"]["atdi"])    # ~53.5
    >>> print(result["ai"]["p_success"])    # ~0.37
    >>> print(result["alerts"]["atdi_alert"])  # ALERT

    >>> # Manual parameters
    >>> result = analyze_basin(runoff_c=0.38, cap_bcm=74, n_countries=3, dispute_level=4)
    """
    # Load from registry if name given
    if name is not None:
        reg = BasinRegistry()
        basin = reg.get(name)
        runoff_c    = runoff_c    or float(basin.get("runoff_c", 0.3))
        cap_bcm     = cap_bcm    or float(basin.get("cap", basin.get("cap_bcm", 10)))
        n_countries = n_countries or (len(basin["country"]) if isinstance(basin.get("country"),list) else int(basin.get("n_countries",2)))
        dispute_level = dispute_level if dispute_level is not None else int(basin.get("dispute_level",0))
        area_km2    = area_km2    or float(basin.get("eff_cat_km2", basin.get("area_km2",100000)))
    else:
        if any(v is None for v in [runoff_c, cap_bcm, n_countries, dispute_level]):
            raise ValueError("Provide basin name or all of: runoff_c, cap_bcm, n_countries, dispute_level")
        area_km2 = area_km2 or 100000.0

    # Core indices
    indices = compute_all_indices(runoff_c, cap_bcm, n_countries, dispute_level,
                                   wqi_measurements=wqi_measurements)

    # Alerts
    atdi_alert = check_atdi_alert(indices["atdi"])
    hifd_alert = check_hifd_alert(indices["hifd"])

    result = {
        "indices": indices,
        "alerts": {
            "atdi_alert": atdi_alert.value,
            "hifd_alert": hifd_alert.value,
            "overall":    ("CRITICAL" if AlertLevel.CRITICAL in (atdi_alert,hifd_alert)
                           else "WARNING" if AlertLevel.WARNING in (atdi_alert,hifd_alert)
                           else "ALERT"   if AlertLevel.ALERT   in (atdi_alert,hifd_alert)
                           else "INFO"),
        },
        "legal":    None,
        "ai":       None,
        "metadata": {
            "name":          name or "custom",
            "runoff_c":      runoff_c,
            "cap_bcm":       cap_bcm,
            "n_countries":   n_countries,
            "dispute_level": dispute_level,
            "area_km2":      area_km2,
            "package_version": "6.2.0",
        }
    }

    if include_legal:
        result["legal"] = get_legal_assessment(
            indices["atdi"], indices["hifd"], dispute_level, n_countries)

    if include_negotiation:
        try:
            from .ai.negotiation import NegotiationAI
            ai = NegotiationAI()
        except ImportError:
            class NegotiationAI:
                def predict(self, atdi, hifd, n_countries, dispute_level):
                    stress = (0.4*atdi + 0.3*hifd + 0.15*(dispute_level/5)*100 + 0.15*min(n_countries/6,1)*100)
                    p = max(0.05, min(0.95, 1.0 - stress/100))
                    strat = "PCA Arbitration" if (dispute_level>=4 or atdi>60) else ("Joint Technical Commission" if (dispute_level>=3 or atdi>40) else "Bilateral Negotiation")
                    risk  = ("CRITICAL" if atdi >= 60
                             else "HIGH" if atdi >= 40
                             else "MODERATE" if atdi >= 25 else "LOW")
                    return {"p_success":round(p,2),"strategy":strat,"un_path":"Art.33→PCA" if risk in ("HIGH","CRITICAL") else "Art.8→JTC","risk":risk}
            ai = NegotiationAI()
        result["ai"] = ai.predict(indices["atdi"], indices["hifd"],
                                   n_countries, dispute_level)

    logger.info("analyze_basin(%s): ATDI=%.1f HIFD=%.1f CI=%.3f alert=%s",
                name or "custom", indices["atdi"], indices["hifd"],
                indices["ci"], result["alerts"]["overall"])
    return result


def analyze_all_basins(include_ai: bool = False) -> list:
    """
    Analyze all 26 registered transboundary basins.

    Parameters
    ----------
    include_ai : bool
        Include NegotiationAI for each basin (slower). Default = False.

    Returns
    -------
    list of dict, sorted by conflict index descending.

    Examples
    --------
    >>> results = analyze_all_basins()
    >>> for r in results[:5]:
    ...     print(r["metadata"]["name"], r["indices"]["atdi"])
    """
    results = []
    for basin in BASINS_26:
        try:
            r = analyze_basin(
                name               = basin["name"],
                include_negotiation= include_ai,
                include_legal      = True,
            )
            results.append(r)
        except Exception as e:
            logger.warning("analyze_basin failed for %s: %s", basin.get("name","?"), e)
    return sorted(results, key=lambda x: x["indices"]["ci"], reverse=True)
