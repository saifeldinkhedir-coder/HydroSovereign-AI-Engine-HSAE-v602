"""
climate_engine.py — HSAE v8.0.0  Climate Scenario Engine
=========================================================
IPCC AR6 SSP projections for all 26 transboundary basins, 2026–2100.

Scenarios implemented:
  SSP1-2.6  — Low emissions, sustainability pathway
  SSP2-4.5  — Intermediate emissions
  SSP3-7.0  — High emissions, regional rivalry
  SSP5-8.5  — Very high emissions, fossil-fuelled development

Outputs per basin:
  • ΔP   — Precipitation change (%)
  • ΔT   — Temperature change (°C)
  • ΔET  — Evapotranspiration change (%)
  • ΔQ   — Runoff change (%)
  • ΔStorage — Reservoir storage change (%)
  • TDI_projected — Projected ATDI under each SSP
  • Conflict_risk  — Projected conflict risk tier
  • People_affected — Millions affected by water stress

Scientific basis:
  IPCC AR6 WGI Chapter 4, 8, 11 — Regional Climate Projections
  Schewe et al. (2014) Nature CC — Multi-model global water scarcity
  Munia et al. (2020) Earth's Future — Transboundary water dependence

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
import math
from typing import Dict, List, Optional, Tuple

# ── IPCC AR6 Regional Delta Tables ───────────────────────────────────────────
# Source: IPCC AR6 WGI Table Atlas 4.1 + Chapter 8
# Format: {region: {ssp: {decade: (delta_P_pct, delta_T_C)}}}

AR6_REGIONAL_DELTAS = {
    # ── Africa ──────────────────────────────────────────────────────────────
    "East Africa": {
        "SSP1-2.6": {2030: (2, 0.8), 2050: (3, 1.4), 2070: (4, 1.7), 2100: (5, 1.9)},
        "SSP2-4.5": {2030: (1, 1.0), 2050: (2, 1.8), 2070: (3, 2.4), 2100: (4, 2.8)},
        "SSP3-7.0": {2030: (0, 1.1), 2050: (-2, 2.2), 2070: (-5, 3.4), 2100: (-8, 4.5)},
        "SSP5-8.5": {2030: (0, 1.2), 2050: (-3, 2.6), 2070: (-8, 4.2), 2100: (-15, 5.8)},
    },
    "West Africa": {
        "SSP1-2.6": {2030: (-1, 0.9), 2050: (-2, 1.5), 2070: (-2, 1.8), 2100: (-3, 2.0)},
        "SSP2-4.5": {2030: (-2, 1.1), 2050: (-4, 2.0), 2070: (-6, 2.7), 2100: (-8, 3.2)},
        "SSP3-7.0": {2030: (-2, 1.2), 2050: (-6, 2.5), 2070: (-10, 3.8), 2100: (-15, 5.0)},
        "SSP5-8.5": {2030: (-3, 1.3), 2050: (-8, 3.0), 2070: (-14, 4.8), 2100: (-20, 6.5)},
    },
    "Southern Africa": {
        "SSP1-2.6": {2030: (-2, 0.9), 2050: (-3, 1.6), 2070: (-4, 2.0), 2100: (-4, 2.2)},
        "SSP2-4.5": {2030: (-3, 1.2), 2050: (-6, 2.2), 2070: (-8, 3.0), 2100: (-10, 3.6)},
        "SSP3-7.0": {2030: (-3, 1.3), 2050: (-8, 2.8), 2070: (-13, 4.4), 2100: (-18, 5.8)},
        "SSP5-8.5": {2030: (-4, 1.5), 2050: (-10, 3.4), 2070: (-16, 5.5), 2100: (-25, 7.5)},
    },
    # ── Middle East ──────────────────────────────────────────────────────────
    "Middle East": {
        "SSP1-2.6": {2030: (-3, 1.0), 2050: (-5, 1.7), 2070: (-6, 2.1), 2100: (-7, 2.3)},
        "SSP2-4.5": {2030: (-4, 1.3), 2050: (-7, 2.3), 2070: (-10, 3.2), 2100: (-12, 3.8)},
        "SSP3-7.0": {2030: (-4, 1.4), 2050: (-9, 2.9), 2070: (-14, 4.6), 2100: (-20, 6.0)},
        "SSP5-8.5": {2030: (-5, 1.6), 2050: (-11, 3.5), 2070: (-18, 5.8), 2100: (-28, 8.0)},
    },
    # ── Central Asia ─────────────────────────────────────────────────────────
    "Central Asia": {
        "SSP1-2.6": {2030: (-1, 1.0), 2050: (-2, 1.8), 2070: (-3, 2.2), 2100: (-3, 2.5)},
        "SSP2-4.5": {2030: (-2, 1.3), 2050: (-4, 2.4), 2070: (-5, 3.3), 2100: (-7, 3.9)},
        "SSP3-7.0": {2030: (-2, 1.4), 2050: (-5, 3.0), 2070: (-8, 4.7), 2100: (-12, 6.2)},
        "SSP5-8.5": {2030: (-3, 1.6), 2050: (-7, 3.6), 2070: (-12, 6.0), 2100: (-18, 8.3)},
    },
    # ── South Asia ───────────────────────────────────────────────────────────
    "South Asia": {
        "SSP1-2.6": {2030: (3, 0.8), 2050: (4, 1.4), 2070: (5, 1.7), 2100: (6, 1.9)},
        "SSP2-4.5": {2030: (2, 1.0), 2050: (4, 1.9), 2070: (5, 2.6), 2100: (7, 3.1)},
        "SSP3-7.0": {2030: (2, 1.1), 2050: (3, 2.4), 2070: (5, 3.8), 2100: (7, 5.0)},
        "SSP5-8.5": {2030: (2, 1.3), 2050: (3, 2.9), 2070: (5, 4.8), 2100: (8, 6.6)},
    },
    # ── Southeast / East Asia ────────────────────────────────────────────────
    "Southeast Asia": {
        "SSP1-2.6": {2030: (2, 0.7), 2050: (3, 1.2), 2070: (4, 1.5), 2100: (5, 1.7)},
        "SSP2-4.5": {2030: (1, 0.9), 2050: (3, 1.7), 2070: (4, 2.3), 2100: (6, 2.8)},
        "SSP3-7.0": {2030: (1, 1.0), 2050: (2, 2.1), 2070: (3, 3.4), 2100: (5, 4.5)},
        "SSP5-8.5": {2030: (2, 1.1), 2050: (3, 2.5), 2070: (4, 4.3), 2100: (6, 5.9)},
    },
    # ── Americas ─────────────────────────────────────────────────────────────
    "North America": {
        "SSP1-2.6": {2030: (1, 0.7), 2050: (1, 1.2), 2070: (2, 1.5), 2100: (2, 1.7)},
        "SSP2-4.5": {2030: (0, 0.9), 2050: (1, 1.7), 2070: (1, 2.3), 2100: (2, 2.8)},
        "SSP3-7.0": {2030: (-1, 1.0), 2050: (-2, 2.1), 2070: (-3, 3.3), 2100: (-5, 4.4)},
        "SSP5-8.5": {2030: (-1, 1.1), 2050: (-3, 2.5), 2070: (-5, 4.2), 2100: (-8, 5.8)},
    },
    "South America": {
        "SSP1-2.6": {2030: (-1, 0.8), 2050: (-2, 1.4), 2070: (-3, 1.7), 2100: (-3, 1.9)},
        "SSP2-4.5": {2030: (-2, 1.0), 2050: (-3, 1.8), 2070: (-5, 2.5), 2100: (-6, 3.0)},
        "SSP3-7.0": {2030: (-2, 1.1), 2050: (-5, 2.3), 2070: (-8, 3.6), 2100: (-12, 4.8)},
        "SSP5-8.5": {2030: (-3, 1.2), 2050: (-6, 2.8), 2070: (-10, 4.5), 2100: (-16, 6.2)},
    },
    # ── Europe ───────────────────────────────────────────────────────────────
    "Europe": {
        "SSP1-2.6": {2030: (1, 0.6), 2050: (1, 1.1), 2070: (2, 1.3), 2100: (2, 1.5)},
        "SSP2-4.5": {2030: (0, 0.8), 2050: (1, 1.5), 2070: (1, 2.0), 2100: (1, 2.5)},
        "SSP3-7.0": {2030: (-1, 0.9), 2050: (-2, 1.9), 2070: (-4, 3.0), 2100: (-6, 4.0)},
        "SSP5-8.5": {2030: (-1, 1.0), 2050: (-3, 2.3), 2070: (-5, 3.7), 2100: (-9, 5.2)},
    },
    # ── Oceania ──────────────────────────────────────────────────────────────
    "Oceania": {
        "SSP1-2.6": {2030: (-2, 0.7), 2050: (-3, 1.2), 2070: (-4, 1.5), 2100: (-4, 1.7)},
        "SSP2-4.5": {2030: (-3, 0.9), 2050: (-5, 1.7), 2070: (-7, 2.3), 2100: (-8, 2.8)},
        "SSP3-7.0": {2030: (-3, 1.0), 2050: (-6, 2.1), 2070: (-10, 3.3), 2100: (-14, 4.4)},
        "SSP5-8.5": {2030: (-4, 1.1), 2050: (-8, 2.6), 2070: (-13, 4.2), 2100: (-20, 5.8)},
    },
}

# ── Basin → AR6 Region Mapping ────────────────────────────────────────────────
BASIN_AR6_REGION = {
    "blue_nile_gerd":       "East Africa",
    "nile_roseires":        "East Africa",
    "nile_aswan":           "East Africa",
    "zambezi_kariba":       "Southern Africa",
    "congo_inga":           "West Africa",
    "niger_kainji":         "West Africa",
    "euphrates_ataturk":    "Middle East",
    "tigris_mosul":         "Middle East",
    "amu_darya_nurek":      "Central Asia",
    "syr_darya_toktogul":   "Central Asia",
    "mekong_xayaburi":      "Southeast Asia",
    "yangtze_3gorges":      "Southeast Asia",
    "indus_tarbela":        "South Asia",
    "brahmaputra_subansiri":"South Asia",
    "ganges_farakka":       "South Asia",
    "salween_myitsone":     "Southeast Asia",
    "amazon_belo_monte":    "South America",
    "parana_itaipu":        "South America",
    "orinoco_guri":         "South America",
    "colorado_hoover":      "North America",
    "columbia_grand_coulee":"North America",
    "rio_grande_amistad":   "North America",
    "danube_iron_gates":    "Europe",
    "rhine_basin":          "Europe",
    "dnieper_kakhovka":     "Europe",
    "murray_darling_hume":  "Oceania",
}

# ── Basin population served (millions) ───────────────────────────────────────
BASIN_POPULATION_M = {
    "blue_nile_gerd": 120,   "nile_roseires": 45,      "nile_aswan": 100,
    "zambezi_kariba": 40,    "congo_inga": 80,          "niger_kainji": 110,
    "euphrates_ataturk": 60, "tigris_mosul": 35,        "amu_darya_nurek": 50,
    "syr_darya_toktogul": 35,"mekong_xayaburi": 70,     "yangtze_3gorges": 450,
    "indus_tarbela": 220,    "brahmaputra_subansiri": 55,"ganges_farakka": 500,
    "salween_myitsone": 10,  "amazon_belo_monte": 25,   "parana_itaipu": 80,
    "orinoco_guri": 30,      "colorado_hoover": 40,     "columbia_grand_coulee": 10,
    "rio_grande_amistad": 12,"danube_iron_gates": 85,   "rhine_basin": 60,
    "dnieper_kakhovka": 35,  "murray_darling_hume": 3,
}

SSPS = ["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
DECADES = [2030, 2050, 2070, 2100]


def _interpolate_decade(data: dict, year: int) -> Tuple[float, float]:
    """Linear interpolation between AR6 decade anchors."""
    decades = sorted(data.keys())
    if year <= decades[0]:
        return data[decades[0]]
    if year >= decades[-1]:
        return data[decades[-1]]
    for i in range(len(decades) - 1):
        y0, y1 = decades[i], decades[i + 1]
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0)
            p0, t0 = data[y0]
            p1, t1 = data[y1]
            return (p0 + t * (p1 - p0), t0 + t * (t1 - t0))
    return data[decades[-1]]


def _delta_ET(delta_T_C: float) -> float:
    """
    Penman-Monteith sensitivity: ~2–3%/°C in arid, ~4–6%/°C in humid.
    Using mid-range 3.5%/°C for global estimate.
    """
    return delta_T_C * 3.5


def _delta_runoff(delta_P_pct: float, delta_ET_pct: float,
                  runoff_ratio: float = 0.35) -> float:
    """
    Budyko framework: ΔQ/Q ≈ (ΔP - ΔET × ET/P) / (Q/P)
    Simplified: elasticity ≈ 2.0 × ΔP - 0.8 × ΔET
    """
    return 2.0 * delta_P_pct - 0.8 * delta_ET_pct


def _delta_storage(delta_runoff_pct: float, delta_T_C: float,
                   current_tdi: float) -> float:
    """
    Reservoir storage change accounting for:
    - Reduced inflow (runoff change)
    - Increased evaporation from reservoir surface (T-driven)
    - Upstream abstraction pressure (TDI-driven)
    evap_loss ≈ 1.5%/°C for large reservoirs (Wurtsbaugh et al. 2017)
    """
    evap_penalty = -delta_T_C * 1.5
    abstraction_penalty = -current_tdi * delta_T_C * 0.5
    return delta_runoff_pct + evap_penalty + abstraction_penalty


def _project_tdi(current_tdi: float, delta_storage_pct: float,
                 delta_runoff_pct: float) -> float:
    """
    Project ATDI change: less storage + less runoff → higher TDI.
    TDI_proj = TDI_current × (1 + |ΔStorage| / 100 × 0.5)
    Clamped to [0, 1].
    """
    storage_factor = abs(min(delta_storage_pct, 0)) / 100.0
    runoff_factor  = abs(min(delta_runoff_pct, 0)) / 100.0
    tdi_increase   = current_tdi * (storage_factor * 0.6 + runoff_factor * 0.4)
    return min(1.0, current_tdi + tdi_increase)


def _conflict_risk(tdi: float, dispute_level: int,
                   delta_storage_pct: float) -> str:
    """Classify projected conflict risk."""
    stress = tdi + dispute_level / 5.0 * 0.2 + abs(min(delta_storage_pct, 0)) / 200.0
    if stress >= 0.85:  return "CRITICAL — ICJ Referral"
    if stress >= 0.70:  return "HIGH — Art.33 Trigger"
    if stress >= 0.50:  return "ELEVATED — Art.7 Watch"
    if stress >= 0.30:  return "MODERATE — Art.5 Monitor"
    return "LOW — Regular Monitoring"


def project_basin(basin: dict, ssp: str, year: int = 2050) -> dict:
    """
    Project climate impacts for a single basin at a given year.

    Parameters
    ----------
    basin : basin dict from basins_data.py
    ssp   : "SSP1-2.6" | "SSP2-4.5" | "SSP3-7.0" | "SSP5-8.5"
    year  : target year (2026–2100)

    Returns
    -------
    dict with all projection metrics
    """
    basin_id = basin.get("id", "unknown")
    ar6_reg  = BASIN_AR6_REGION.get(basin_id, "East Africa")
    region_deltas = AR6_REGIONAL_DELTAS.get(ar6_reg, AR6_REGIONAL_DELTAS["East Africa"])
    ssp_deltas = region_deltas.get(ssp, region_deltas["SSP2-4.5"])

    dP, dT = _interpolate_decade(ssp_deltas, year)
    dET    = _delta_ET(dT)
    dQ     = _delta_runoff(dP, dET)

    current_tdi = float(basin.get("tdi", 0.3))
    dispute_lvl = 3
    if isinstance(basin.get("dispute_level"), (int, float)):
        dispute_lvl = int(basin["dispute_level"])
    elif isinstance(basin.get("dispute_level"), str):
        mapping = {"LOW": 1, "MEDIUM": 2, "MODERATE": 3, "HIGH": 4, "CRITICAL": 5}
        dispute_lvl = mapping.get(basin["dispute_level"].upper(), 3)

    dStorage = _delta_storage(dQ, dT, current_tdi)
    tdi_proj = _project_tdi(current_tdi, dStorage, dQ)
    risk     = _conflict_risk(tdi_proj, dispute_lvl, dStorage)
    pop      = BASIN_POPULATION_M.get(basin_id, 10)
    stress_factor = abs(min(dStorage, 0)) / 100.0
    affected_M    = pop * stress_factor

    return {
        "basin_id":          basin_id,
        "basin_name":        basin.get("name", basin_id),
        "ar6_region":        ar6_reg,
        "ssp":               ssp,
        "year":              year,
        "delta_P_pct":       round(dP, 1),
        "delta_T_C":         round(dT, 2),
        "delta_ET_pct":      round(dET, 1),
        "delta_Q_pct":       round(dQ, 1),
        "delta_storage_pct": round(dStorage, 1),
        "TDI_current":       round(current_tdi, 3),
        "TDI_projected":     round(tdi_proj, 3),
        "TDI_change":        round(tdi_proj - current_tdi, 3),
        "conflict_risk":     risk,
        "pop_million":       pop,
        "affected_million":  round(affected_M, 1),
        "dispute_level":     dispute_lvl,
    }


def project_all_basins(basins: list, ssp: str, year: int = 2050) -> List[dict]:
    """Project all 26 basins for a given SSP + year."""
    return [project_basin(b, ssp, year) for b in basins]


def full_ssp_matrix(basins: list) -> Dict[str, Dict[int, List[dict]]]:
    """
    Full SSP × Decade × Basin matrix.
    Returns {ssp: {decade: [basin_projections]}}
    """
    result = {}
    for ssp in SSPS:
        result[ssp] = {}
        for decade in DECADES:
            result[ssp][decade] = project_all_basins(basins, ssp, decade)
    return result


def critical_basins_by_ssp(basins: list, ssp: str,
                            year: int = 2075,
                            tdi_threshold: float = 0.80) -> List[dict]:
    """Return basins projected to exceed TDI threshold under given SSP."""
    projs = project_all_basins(basins, ssp, year)
    return sorted(
        [p for p in projs if p["TDI_projected"] >= tdi_threshold],
        key=lambda x: x["TDI_projected"], reverse=True
    )


def people_at_risk(basins: list, ssp: str = "SSP5-8.5",
                   year: int = 2075) -> dict:
    """Aggregate people at water stress risk under an SSP scenario."""
    projs = project_all_basins(basins, ssp, year)
    total = sum(p["affected_million"] for p in projs)
    by_region = {}
    for p in projs:
        r = p["ar6_region"]
        by_region[r] = by_region.get(r, 0) + p["affected_million"]
    return {
        "ssp": ssp, "year": year,
        "total_affected_million": round(total, 1),
        "by_region": {k: round(v, 1) for k, v in
                      sorted(by_region.items(), key=lambda x: -x[1])},
        "worst_basins": sorted(projs, key=lambda x: -x["affected_million"])[:5],
    }


def generate_html_report(basins: list, ssp: str = "SSP5-8.5",
                         year: int = 2075) -> str:
    """Generate HTML climate projection report."""
    projs = sorted(project_all_basins(basins, ssp, year),
                   key=lambda x: -x["TDI_projected"])
    risk_agg = people_at_risk(basins, ssp, year)

    rows = ""
    for p in projs:
        color = ("#f85149" if p["TDI_projected"] >= 0.8 else
                 "#f0883e" if p["TDI_projected"] >= 0.6 else
                 "#e3b341" if p["TDI_projected"] >= 0.4 else "#3fb950")
        rows += f"""
        <tr>
          <td><strong>{p['basin_name']}</strong></td>
          <td>{p['ar6_region']}</td>
          <td>{p['delta_P_pct']:+.1f}%</td>
          <td>{p['delta_T_C']:+.2f}°C</td>
          <td>{p['delta_storage_pct']:+.1f}%</td>
          <td style='color:{color}'><strong>{p['TDI_projected']:.3f}</strong></td>
          <td style='color:{color}'>{p['TDI_change']:+.3f}</td>
          <td>{p['conflict_risk']}</td>
          <td>{p['affected_million']:.1f}M</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><title>HSAE Climate Projection {ssp} {year}</title>
<style>
body{{font-family:Segoe UI,sans-serif;background:#0d1117;color:#e6edf3;padding:32px}}
h1{{color:#58a6ff}} h2{{color:#79c0ff;margin-top:28px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#161b22;color:#8b949e;padding:10px;text-align:left;
    font-size:10px;letter-spacing:0.1em;text-transform:uppercase}}
td{{padding:9px 10px;border-bottom:1px solid #21262d}}
tr:hover td{{background:#161b22}}
.stat{{display:inline-block;background:#161b22;border:1px solid #30363d;
       border-radius:8px;padding:16px 24px;margin:8px;text-align:center}}
.stat-num{{font-size:2em;font-weight:bold;color:#f0883e}}
.stat-lbl{{font-size:0.75em;color:#8b949e;margin-top:4px}}
</style></head><body>
<h1>🌡️ HSAE Climate Projections — {ssp} · {year}</h1>
<p style='color:#8b949e'>IPCC AR6 WGI regional deltas applied to 26 transboundary basins
 · Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991</p>

<h2>Summary Statistics</h2>
<div class='stat'><div class='stat-num'>{risk_agg['total_affected_million']:.0f}M</div>
<div class='stat-lbl'>People at Risk</div></div>
<div class='stat'><div class='stat-num'>{len(critical_basins_by_ssp(basins,ssp,year))}</div>
<div class='stat-lbl'>Critical Basins (TDI≥0.8)</div></div>
<div class='stat'><div class='stat-num'>{ssp}</div>
<div class='stat-lbl'>Scenario</div></div>
<div class='stat'><div class='stat-num'>{year}</div>
<div class='stat-lbl'>Projection Year</div></div>

<h2>Basin Projections — All 26 Basins</h2>
<table>
<thead><tr>
  <th>Basin</th><th>AR6 Region</th><th>ΔP</th><th>ΔT</th>
  <th>ΔStorage</th><th>TDI Proj.</th><th>ΔTDI</th>
  <th>Conflict Risk</th><th>People</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>

<p style='margin-top:28px;font-size:12px;color:#8b949e'>
Sources: IPCC AR6 WGI Chapter 4, 8, 11 · Schewe et al. (2014) Nature CC ·
Munia et al. (2020) Earth's Future · Wurtsbaugh et al. (2017) Nat. Geosci.
</p>
</body></html>"""


def ssp_comparison_table(basin: dict) -> List[dict]:
    """Compare all 4 SSPs for a single basin across all decades."""
    rows = []
    for ssp in SSPS:
        for decade in DECADES:
            p = project_basin(basin, ssp, decade)
            rows.append(p)
    return rows


# ── Self-test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import unittest.mock as _mock
    for m in ["qgis","qgis.PyQt","qgis.PyQt.QtWidgets","qgis.PyQt.QtCore",
              "qgis.PyQt.QtGui","qgis.core","qgis.gui"]:
        sys.modules.setdefault(m, _mock.MagicMock())
    from basins_data import BASINS_26

    print("=== HSAE Climate Engine ===")
    gerd = next(b for b in BASINS_26 if b["id"] == "blue_nile_gerd")

    print("\n  GERD — SSP5-8.5 Projections:")
    for yr in [2050, 2075, 2100]:
        p = project_basin(gerd, "SSP5-8.5", yr)
        print(f"    {yr}: ΔT={p['delta_T_C']:+.1f}°C "
              f"ΔStorage={p['delta_storage_pct']:+.1f}% "
              f"TDI={p['TDI_projected']:.3f} "
              f"Risk={p['conflict_risk'][:20]}")

    print("\n  People at risk — SSP5-8.5 2075:")
    r = people_at_risk(BASINS_26, "SSP5-8.5", 2075)
    print(f"    Total: {r['total_affected_million']:.0f}M people")
    print(f"    Worst region: {list(r['by_region'].items())[0]}")

    print("\n  Critical basins (TDI≥0.8) — SSP5-8.5 2075:")
    crit = critical_basins_by_ssp(BASINS_26, "SSP5-8.5", 2075)
    for c in crit[:3]:
        print(f"    {c['basin_name']}: TDI={c['TDI_projected']:.3f}")

    html = generate_html_report(BASINS_26, "SSP5-8.5", 2075)
    with open(str(__import__("pathlib").Path(__import__("tempfile").gettempdir()) / "hsae_climate_report.html"), "w") as f:
        f.write(html)
    print(f"\n  HTML report: /tmp/hsae_climate_report.html ({len(html):,} chars)")
    print("✅ climate_engine.py OK")


def project_climate(basin: dict, ssp: str = "SSP2-4.5",
                    horizon: int = 2050) -> dict:
    """Alias for project_basin — project climate impacts on a basin."""
    return project_basin(basin, ssp=ssp, year=horizon)


def compute_ssp_flow(basin: dict, ssp: str = "SSP2-4.5",
                     year: int = 2050) -> dict:
    """Compute SSP-projected flow deficit for a basin."""
    result = project_basin(basin, ssp=ssp, year=year)
    return {
        "basin_id":       basin.get("id", "unknown"),
        "ssp":            ssp,
        "year":           year,
        "delta_flow_pct": result.get("delta_storage_pct", 0.0),
        "projected_tdi":  result.get("tdi_projected", 0.0),
        "conflict_risk":  result.get("conflict_risk", "Low"),
    }



# ── SSP Scenario registry (IPCC AR6) ──────────────────────────────────────────
SSP_SCENARIOS = {
    "SSP1-2.6": {"label": "SSP1-2.6 — Low emissions",   "temp_2100": 1.8, "color": "#22c55e"},
    "SSP2-4.5": {"label": "SSP2-4.5 — Intermediate",    "temp_2100": 2.7, "color": "#eab308"},
    "SSP3-7.0": {"label": "SSP3-7.0 — High emissions",  "temp_2100": 3.6, "color": "#f97316"},
    "SSP5-8.5": {"label": "SSP5-8.5 — Very high",       "temp_2100": 4.4, "color": "#ef4444"},
}

IPCC_AR6_PARAMS = {
    "SSP1-2.6": {"delta_T_2050": 1.0, "delta_P_pct": 2.0,  "delta_ET_pct": 3.0},
    "SSP2-4.5": {"delta_T_2050": 1.5, "delta_P_pct": -2.0, "delta_ET_pct": 5.0},
    "SSP3-7.0": {"delta_T_2050": 2.0, "delta_P_pct": -5.0, "delta_ET_pct": 8.0},
    "SSP5-8.5": {"delta_T_2050": 2.5, "delta_P_pct": -8.0, "delta_ET_pct": 11.0},
}
