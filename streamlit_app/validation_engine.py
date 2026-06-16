"""
validation_engine.py — HSAE v7.0 Hydrological Validation Engine
================================================================
Adapted from hsae_validation.py. Pure Python computation, no Streamlit.

Provides:
  1. NSE / KGE / PBIAS / RMSE / R² skill metrics
  2. Rating system (Moriasi et al. 2007)
  3. GRDC-compatible CSV ingestion (auto column detection, Arabic+English)
  4. Flow Duration Curve (FDC) data
  5. Seasonal monthly aggregates
  6. Taylor Diagram coordinates (portable)
  7. HTML validation report generator

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
Ref: Moriasi et al. (2007) Trans. ASABE 50(3):885–900
"""
from __future__ import annotations
import math
import csv
import io
import datetime
from typing import Dict, List, Optional, Tuple

# ── Skill Metrics ─────────────────────────────────────────────────────────────

def nse(obs: List[float], sim: List[float]) -> float:
    """Nash-Sutcliffe Efficiency [-∞, 1]. 1 = perfect."""
    n = min(len(obs), len(sim))
    obs_mean = sum(obs[:n]) / n
    ss_res = sum((o - s)**2 for o, s in zip(obs[:n], sim[:n]))
    ss_tot = sum((o - obs_mean)**2 for o in obs[:n])
    return 1.0 - ss_res / max(ss_tot, 1e-12)


def kge(obs: List[float], sim: List[float]) -> float:
    """Kling-Gupta Efficiency [-∞, 1]. 1 = perfect."""
    n = min(len(obs), len(sim))
    o, s = obs[:n], sim[:n]
    o_mean = sum(o) / n
    s_mean = sum(s) / n
    # Pearson r
    num = sum((oi - o_mean) * (si - s_mean) for oi, si in zip(o, s))
    denom_o = math.sqrt(sum((oi - o_mean)**2 for oi in o))
    denom_s = math.sqrt(sum((si - s_mean)**2 for si in s))
    r = num / max(denom_o * denom_s, 1e-12)
    alpha = (denom_s / n**0.5) / max(denom_o / n**0.5, 1e-12)
    beta  = s_mean / max(o_mean, 1e-12)
    return 1.0 - math.sqrt((r - 1)**2 + (alpha - 1)**2 + (beta - 1)**2)


def pbias(obs: List[float], sim: List[float]) -> float:
    """Percent bias (%). 0 = perfect, ±10% = acceptable."""
    n = min(len(obs), len(sim))
    return 100.0 * sum(s - o for o, s in zip(obs[:n], sim[:n])) / max(sum(obs[:n]), 1e-12)


def rmse(obs: List[float], sim: List[float]) -> float:
    n = min(len(obs), len(sim))
    return math.sqrt(sum((o - s)**2 for o, s in zip(obs[:n], sim[:n])) / max(n, 1))


def r2(obs: List[float], sim: List[float]) -> float:
    n = min(len(obs), len(sim))
    o_mean = sum(obs[:n]) / n
    s_mean = sum(sim[:n]) / n
    num    = sum((oi - o_mean) * (si - s_mean) for oi, si in zip(obs[:n], sim[:n]))
    denom  = math.sqrt(
        sum((oi - o_mean)**2 for oi in obs[:n]) *
        sum((si - s_mean)**2 for si in sim[:n])
    )
    r = num / max(denom, 1e-12)
    return r ** 2


def compute_all_scores(obs: List[float], sim: List[float]) -> Dict[str, float]:
    return {
        "NSE":   round(nse(obs, sim), 4),
        "KGE":   round(kge(obs, sim), 4),
        "R2":    round(r2(obs, sim), 4),
        "RMSE":  round(rmse(obs, sim), 6),
        "PBIAS": round(pbias(obs, sim), 2),
    }


def rating(val: float, metric: str) -> Tuple[str, str]:
    """(label, hex_color). Thresholds: Moriasi et al. 2007."""
    THRESHOLDS = {
        "NSE":   [(0.75,"✅ Excellent","#10b981"),(0.65,"✅ Good","#22c55e"),
                  (0.50,"⚠️ Satisfactory","#f59e0b"),(-999,"❌ Unsatisfactory","#ef4444")],
        "KGE":   [(0.75,"✅ Excellent","#10b981"),(0.60,"✅ Good","#22c55e"),
                  (0.40,"⚠️ Satisfactory","#f59e0b"),(-999,"❌ Unsatisfactory","#ef4444")],
        "R2":    [(0.90,"✅ Excellent","#10b981"),(0.75,"✅ Good","#22c55e"),
                  (0.50,"⚠️ Satisfactory","#f59e0b"),(-999,"❌ Unsatisfactory","#ef4444")],
        "PBIAS": "special",
    }
    if metric == "PBIAS":
        a = abs(val)
        if a <= 5:   return "✅ Excellent","#10b981"
        if a <= 10:  return "✅ Good","#22c55e"
        if a <= 25:  return "⚠️ Satisfactory","#f59e0b"
        return "❌ Unsatisfactory","#ef4444"
    for thresh, lbl, col in THRESHOLDS.get(metric, []):
        if val >= thresh:
            return lbl, col
    return "❓ Unknown","#6b7280"


# ── CSV Ingestion (GRDC-compatible) ───────────────────────────────────────────

_DATE_ALIASES  = ["date","Date","DATE","datetime","time","timestamp","تاريخ","يوم"]
_Q_ALIASES     = ["discharge","flow","q","Q","streamflow","runoff","inflow","Inflow",
                   "Inflow_obs","q_m3s","discharge_m3s","Flow_m3s","الجريان","تصريف","تدفق"]
_VOL_ALIASES   = ["volume","Volume","storage","Storage","Volume_obs","vol_bcm",
                   "storage_bcm","حجم","تخزين"]
_LEVEL_ALIASES = ["level","Level","stage","Stage","water_level","Level_obs","مستوى","منسوب"]
_RAIN_ALIASES  = ["rain","Rain","rainfall","Rainfall","precip","precipitation",
                   "Rain_obs","GPM_Rain_mm","أمطار","هطول"]
_ET_ALIASES    = ["et","ET","evap","evapotranspiration","ET_mm","evap_mm",
                   "MODIS_ET","التبخر","تبخر_نتح"]


def _detect_col(headers: List[str], aliases: List[str]) -> Optional[str]:
    for a in aliases:
        if a in headers:
            return a
    # Case-insensitive fallback
    hl = [h.lower() for h in headers]
    for a in aliases:
        if a.lower() in hl:
            return headers[hl.index(a.lower())]
    return None


def load_obs_csv(csv_text: str) -> Dict[str, List]:
    """
    Parse GRDC-compatible CSV text.
    Returns dict with keys: Date, Q_obs (optional), V_obs, L_obs, R_obs, ET_obs
    Values are lists of [date_str, float].
    """
    lines = [l for l in csv_text.splitlines() if l.strip() and not l.startswith("#")]
    if not lines:
        raise ValueError("Empty CSV")

    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    rows   = list(reader)
    if not rows:
        raise ValueError("No data rows")

    headers = list(rows[0].keys())
    date_col = _detect_col(headers, _DATE_ALIASES)
    if not date_col:
        raise ValueError("No date column. Rename to 'Date'.")

    result: Dict[str, List] = {"Date": []}
    q_col   = _detect_col(headers, _Q_ALIASES)
    v_col   = _detect_col(headers, _VOL_ALIASES)
    l_col   = _detect_col(headers, _LEVEL_ALIASES)
    r_col   = _detect_col(headers, _RAIN_ALIASES)
    et_col  = _detect_col(headers, _ET_ALIASES)

    if q_col:  result["Q_obs"]  = []
    if v_col:  result["V_obs"]  = []
    if l_col:  result["L_obs"]  = []
    if r_col:  result["R_obs"]  = []
    if et_col: result["ET_obs"] = []

    q_values_raw = []

    for row in rows:
        result["Date"].append(row[date_col].strip())
        if q_col:
            try:
                q_values_raw.append(float(row[q_col]))
            except (ValueError, TypeError):
                q_values_raw.append(None)
        if v_col:
            try:
                result["V_obs"].append(float(row[v_col]))
            except Exception:
                result["V_obs"].append(None)
        if l_col:
            try:
                result["L_obs"].append(float(row[l_col]))
            except Exception:
                result["L_obs"].append(None)
        if r_col:
            try:
                result["R_obs"].append(float(row[r_col]))
            except Exception:
                result["R_obs"].append(None)
        if et_col:
            try:
                result["ET_obs"].append(float(row[et_col]))
            except Exception:
                result["ET_obs"].append(None)

    # Auto-convert m³/s → BCM/day
    if q_col and q_values_raw:
        valid = [v for v in q_values_raw if v is not None]
        if valid and max(valid) > 500:  # clearly m³/s
            q_values_raw = [v * 86400 / 1e9 if v is not None else None for v in q_values_raw]
        result["Q_obs"] = q_values_raw

    return result


# ── Flow Duration Curve ───────────────────────────────────────────────────────

def fdc(values: List[float]) -> Tuple[List[float], List[float]]:
    """Return (exceedance_pct, sorted_values) for FDC plot."""
    clean  = sorted([v for v in values if v is not None], reverse=True)
    n      = len(clean)
    if n == 0:
        return [], []
    exc    = [i / (n - 1) * 100 for i in range(n)]
    return exc, clean


# ── Seasonal Monthly Means ────────────────────────────────────────────────────

def monthly_means(dates: List[str], values: List[float]) -> Dict[int, float]:
    """Returns {month_1-12: mean_value}."""
    monthly: Dict[int, List[float]] = {m: [] for m in range(1, 13)}
    for d, v in zip(dates, values):
        if v is None:
            continue
        try:
            month = int(str(d)[5:7])
            if 1 <= month <= 12:
                monthly[month].append(v)
        except Exception:
            pass
    return {m: (sum(v) / len(v) if v else 0.0) for m, v in monthly.items()}


# ── Taylor Diagram Data ───────────────────────────────────────────────────────

def taylor_stats(obs: List[float], sim: List[float]) -> Dict[str, float]:
    """Returns Taylor diagram statistics."""
    n      = min(len(obs), len(sim))
    o, s   = [x for x in obs[:n] if x is not None], [x for x in sim[:n] if x is not None]
    n2     = min(len(o), len(s))
    o, s   = o[:n2], s[:n2]
    if n2 < 2:
        return {}
    o_mean = sum(o) / n2
    s_mean = sum(s) / n2
    o_std  = math.sqrt(sum((x - o_mean)**2 for x in o) / n2)
    s_std  = math.sqrt(sum((x - s_mean)**2 for x in s) / n2)
    num    = sum((oi - o_mean) * (si - s_mean) for oi, si in zip(o, s))
    r      = num / max(o_std * s_std * n2, 1e-12)
    crmse  = math.sqrt(sum(((si - s_mean) - (oi - o_mean))**2 for oi, si in zip(o, s)) / n2)
    theta  = math.acos(max(-1.0, min(1.0, r)))
    return {
        "r":           round(r, 4),
        "o_std":       round(o_std, 6),
        "s_std":       round(s_std, 6),
        "std_ratio":   round(s_std / max(o_std, 1e-12), 4),
        "cRMSE":       round(crmse, 6),
        "theta_rad":   round(theta, 4),
        # Cartesian coordinates for plotting
        "x_sim":       round(s_std * math.cos(theta), 6),
        "y_sim":       round(s_std * math.sin(theta), 6),
        "x_ref":       round(o_std, 6),
        "y_ref":       0.0,
    }


# ── Synthetic Demo (noise-perturbed) ─────────────────────────────────────────

def make_synthetic_obs(sim_values: List[float], noise_frac: float = 0.12,
                        seed: int = 99) -> List[float]:
    """Add ±noise_frac Gaussian perturbation to simulate 'observed' data."""
    import random
    rng = random.Random(seed)
    return [max(0.0, v * (1 + rng.gauss(0, noise_frac))) for v in sim_values]


# ── HTML Report Generator ─────────────────────────────────────────────────────

def build_validation_report_html(
    scores:   Dict[str, Dict[str, float]],
    basin:    dict,
    n_days:   int,
    date_min: str,
    date_max: str,
) -> str:
    date_str = datetime.datetime.utcnow().strftime("%d %B %Y, %H:%M UTC")
    rows_html = ""
    for var, sc in scores.items():
        label = "Inflow/Discharge" if var == "inflow" else "Volume/Storage"
        rows_html += f"<tr><td colspan='3'><b>{label}</b></td></tr>"
        for m, v in sc.items():
            lbl, color = rating(v, m)
            rows_html += (f"<tr><td>{m}</td>"
                          f"<td style='color:{color};font-weight:bold;'>{v:.4f}</td>"
                          f"<td style='color:{color};'>{lbl}</td></tr>")

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>HSAE Validation Report — {basin.get('name','?')}</title>
<style>
body{{font-family:Segoe UI,Arial;margin:30px;background:#f8fafc;color:#1e293b;}}
h1{{color:#0f766e;border-bottom:2px solid #0f766e;padding-bottom:8px;}}
h2{{color:#1d4ed8;}} table{{border-collapse:collapse;width:70%;margin:1rem 0;}}
th,td{{border:1px solid #cbd5e1;padding:8px 14px;}}
th{{background:#1e3a5f;color:#fff;}}
.meta{{background:#f0f9ff;border-radius:8px;padding:12px;margin:10px 0;}}
.footer{{color:#94a3b8;font-size:11px;margin-top:24px;border-top:1px solid #e2e8f0;padding-top:12px;}}
</style></head><body>
<h1>📊 HSAE Hydrological Validation Report</h1>
<div class="meta">
  <b>Basin:</b> {basin.get('name','?')} — {basin.get('dam','?')}<br>
  <b>Region:</b> {basin.get('region','?')} | <b>Countries:</b> {basin.get('n_countries','?')}<br>
  <b>Overlap period:</b> {date_min} → {date_max} ({n_days:,} days)<br>
  <b>Generated:</b> {date_str}
</div>
<h2>Skill Scores</h2>
<table>
<tr><th>Metric</th><th>Value</th><th>Rating</th></tr>
{rows_html}
</table>
<h2>Reference Thresholds (Moriasi et al. 2007)</h2>
<table>
<tr><th>Metric</th><th>Excellent</th><th>Good</th><th>Satisfactory</th></tr>
<tr><td>NSE</td><td>&gt;0.75</td><td>&gt;0.65</td><td>&gt;0.50</td></tr>
<tr><td>KGE</td><td>&gt;0.75</td><td>&gt;0.60</td><td>&gt;0.40</td></tr>
<tr><td>PBIAS</td><td>&lt;±5%</td><td>&lt;±10%</td><td>&lt;±25%</td></tr>
</table>
<h2>Legal Significance</h2>
<p>Validation scores (NSE/KGE/PBIAS) establish the reproducibility and
scientific credibility of HSAE simulations. They can be cited in technical
annexes to diplomatic negotiations or arbitral submissions under
Articles 9 (data exchange) and Annex Article 6 (fact-finding) of the
UN 1997 Watercourses Convention.</p>
<div class="footer">
HSAE v7.0.0 QGIS Plugin · Author: Seifeldin M.G. Alkhedir ·
ORCID: 0000-0003-0821-2991 · MIT License
</div></body></html>"""
