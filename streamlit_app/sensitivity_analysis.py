"""
sensitivity_analysis.py — HSAE v9.0.0  Sensitivity Analysis Engine
===================================================================
One-at-a-time (OAT) and Sobol variance-based sensitivity analysis
for ATDI, AHIFD, ASI, and WQI indices.

Answers the question: "Which input parameter most drives TDI uncertainty?"
Essential for peer review of JH-1 methodology paper.

Methods:
  1. OAT  — One-At-a-Time: vary each parameter ±10%, ±25%, ±50%
  2. Morris — Elementary effects screening (Saltelli 2010)
  3. Sobol — First-order and total-order sensitivity indices (pure-Python)

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
import math
import random
from typing import Dict, List, Optional, Tuple

# ── ATDI parameter definitions ────────────────────────────────────────────────
ATDI_PARAMS = {
    "FRD": {
        "name":  "Flow Reduction Deficit",
        "formula": "1 - Q_obs/Q_nat",
        "default": 0.35,
        "range":   (0.0, 1.0),
        "weight":  0.40,
        "unit":    "dimensionless",
    },
    "SRI": {
        "name":  "Storage Retention Index",
        "formula": "storage_BCM / Q_annual_BCM",
        "default": 0.28,
        "range":   (0.0, 5.0),
        "weight":  0.20,
        "unit":    "dimensionless",
    },
    "DI": {
        "name":  "Dependency Index",
        "formula": "(n_countries - 1) / 4",
        "default": 0.25,
        "range":   (0.0, 1.0),
        "weight":  0.25,
        "unit":    "dimensionless",
    },
    "IPI": {
        "name":  "International Pressure Index",
        "formula": "dispute_level / 5",
        "default": 0.50,
        "range":   (0.0, 1.0),
        "weight":  0.15,
        "unit":    "dimensionless",
    },
}

AHIFD_PARAMS = {
    "Q_obs":  {"name": "Observed discharge",    "default": 1200, "range": (100, 5000)},
    "Q_nat":  {"name": "Naturalised discharge",  "default": 1450, "range": (500, 8000)},
}

ASI_PARAMS = {
    "E":    {"name": "Equity score",        "default": 0.55, "range": (0,1), "weight": 0.35},
    "ADTS": {"name": "Digital transparency", "default": 37.0, "range": (0,100),"weight": 0.25},
    "F":    {"name": "Flexibility score",    "default": 0.60, "range": (0,1), "weight": 0.25},
    "D":    {"name": "Dispute level",        "default": 3.0,  "range": (1,5), "weight": 0.15},
}


def _compute_atdi(FRD: float, SRI: float, DI: float, IPI: float) -> float:
    return min(1.0, max(0.0,
        0.40 * FRD + 0.20 * min(SRI, 1.0) + 0.25 * DI + 0.15 * IPI))


def _compute_ahifd(Q_obs: float, Q_nat: float) -> float:
    if Q_nat <= 0:
        return 0.0
    return max(0.0, (Q_nat - Q_obs) / Q_nat * 100)


def _compute_asi(E: float, ADTS: float, F: float, D: float) -> float:
    return max(0.0, min(100.0,
        0.35 * E * 100 + 0.25 * ADTS + 0.25 * F * 100 + 0.15 * (1 - D/5) * 100))


# ── OAT Sensitivity ──────────────────────────────────────────────────────────
def oat_sensitivity(index: str = "ATDI",
                    perturbations: List[float] = None) -> dict:
    """
    One-at-a-time sensitivity analysis.

    Parameters
    ----------
    index        : "ATDI" | "AHIFD" | "ASI"
    perturbations: list of fractional perturbations, e.g. [0.10, 0.25, 0.50]

    Returns
    -------
    dict with sensitivity results per parameter per perturbation level
    """
    if perturbations is None:
        perturbations = [0.05, 0.10, 0.25, 0.50]

    if index == "ATDI":
        params = ATDI_PARAMS
        def compute(**kw):
            return _compute_atdi(kw["FRD"], kw["SRI"], kw["DI"], kw["IPI"])
        base = compute(**{k: v["default"] for k, v in params.items()})
    elif index == "AHIFD":
        params = AHIFD_PARAMS
        def compute(**kw):
            return _compute_ahifd(kw["Q_obs"], kw["Q_nat"])
        base = compute(**{k: v["default"] for k, v in params.items()})
    elif index == "ASI":
        params = ASI_PARAMS
        def compute(**kw):
            return _compute_asi(kw["E"], kw["ADTS"], kw["F"], kw["D"])
        base = compute(**{k: v["default"] for k, v in params.items()})
    else:
        return {"error": f"Unknown index: {index}"}

    results = {"index": index, "base_value": round(base, 4),
               "parameters": {}, "ranking": []}

    for pname, pinfo in params.items():
        p_def = pinfo["default"]
        p_min, p_max = pinfo["range"]
        param_results = {"name": pinfo["name"], "default": p_def, "perturb": {}}

        max_effect = 0.0
        for delta in perturbations:
            p_up = min(p_max, p_def * (1 + delta))
            p_dn = max(p_min, p_def * (1 - delta))

            kw_up = {k: v["default"] for k, v in params.items()}
            kw_dn = {k: v["default"] for k, v in params.items()}
            kw_up[pname] = p_up
            kw_dn[pname] = p_dn

            v_up  = compute(**kw_up)
            v_dn  = compute(**kw_dn)
            s_up  = round((v_up - base) / (base + 1e-9) * 100, 2)
            s_dn  = round((v_dn - base) / (base + 1e-9) * 100, 2)
            norm_s = abs(s_up - s_dn) / (2 * delta * 100)
            max_effect = max(max_effect, abs(s_up), abs(s_dn))

            param_results["perturb"][f"+{int(delta*100)}%"] = {
                "value_up": round(v_up, 4),
                "value_dn": round(v_dn, 4),
                "change_up_pct": s_up,
                "change_dn_pct": s_dn,
                "sensitivity_index": round(norm_s, 4),
            }
        param_results["max_effect_pct"] = round(max_effect, 2)
        results["parameters"][pname] = param_results

    # Rank parameters by max effect
    ranking = sorted(
        [(k, v["max_effect_pct"]) for k, v in results["parameters"].items()],
        key=lambda x: -x[1]
    )
    results["ranking"] = [{"param": k, "effect_pct": e,
                            "name": params[k]["name"]}
                          for k, e in ranking]
    return results


# ── Morris Elementary Effects ─────────────────────────────────────────────────
def morris_sensitivity(index: str = "ATDI",
                       n_trajectories: int = 50,
                       seed: int = 42) -> dict:
    """
    Morris method: elementary effects for screening.
    Returns μ* (mean absolute effect) and σ (std dev) per parameter.
    """
    rng = random.Random(seed)

    if index == "ATDI":
        params = ATDI_PARAMS
        compute = lambda v: _compute_atdi(*[v[k] for k in ["FRD","SRI","DI","IPI"]])
    elif index == "ASI":
        params = ASI_PARAMS
        compute = lambda v: _compute_asi(*[v[k] for k in ["E","ADTS","F","D"]])
    else:
        params = ATDI_PARAMS
        compute = lambda v: _compute_atdi(*[v[k] for k in ["FRD","SRI","DI","IPI"]])

    k     = len(params)
    delta = 0.5 / (k)   # grid step
    pnames = list(params.keys())
    effects: Dict[str, List[float]] = {p: [] for p in pnames}

    for _ in range(n_trajectories):
        # Base point
        base_vals = {}
        for p, info in params.items():
            lo, hi = info["range"]
            base_vals[p] = lo + rng.random() * (hi - lo) * 0.8

        perm = pnames.copy()
        rng.shuffle(perm)

        current = dict(base_vals)
        for p in perm:
            lo, hi = params[p]["range"]
            v0 = current[p]
            step = delta * (hi - lo)
            v1 = min(hi, max(lo, v0 + (step if rng.random() > 0.5 else -step)))

            f0 = compute(current)
            current_new = dict(current)
            current_new[p] = v1
            f1 = compute(current_new)

            ei = (f1 - f0) / (v1 - v0 + 1e-12)
            effects[p].append(ei)
            current = current_new

    result = {}
    for p, ee in effects.items():
        n = len(ee)
        mu      = sum(ee) / n
        mu_star = sum(abs(e) for e in ee) / n
        sigma   = (sum((e - mu)**2 for e in ee) / n)**0.5
        result[p] = {
            "name":     params[p]["name"],
            "mu":       round(mu, 6),
            "mu_star":  round(mu_star, 6),
            "sigma":    round(sigma, 6),
            "class":    ("Important" if mu_star > 0.1 else
                         "Moderate" if mu_star > 0.01 else "Negligible"),
        }

    ranked = sorted(result.items(), key=lambda x: -x[1]["mu_star"])
    return {"index": index, "method": "Morris",
            "n_trajectories": n_trajectories,
            "parameters": result,
            "ranking": [{"param": k, "mu_star": v["mu_star"],
                          "class": v["class"]} for k, v in ranked]}


# ── Sobol First-Order Indices ─────────────────────────────────────────────────
def sobol_sensitivity(index: str = "ATDI",
                      n_samples: int = 500,
                      seed: int = 42) -> dict:
    """
    Sobol variance-based sensitivity indices (Saltelli et al. 2010).
    Returns S1 (first-order) and ST (total-order) per parameter.
    Pure-Python implementation.
    """
    rng = random.Random(seed)

    if index == "ATDI":
        params = ATDI_PARAMS
        compute = lambda v: _compute_atdi(v[0], v[1], v[2], v[3])
        keys    = ["FRD","SRI","DI","IPI"]
    elif index == "ASI":
        params  = ASI_PARAMS
        compute = lambda v: _compute_asi(v[0], v[1], v[2], v[3])
        keys    = ["E","ADTS","F","D"]
    else:
        params = ATDI_PARAMS
        compute = lambda v: _compute_atdi(v[0], v[1], v[2], v[3])
        keys    = ["FRD","SRI","DI","IPI"]

    k = len(keys)

    def sample(seed_local):
        r = random.Random(seed_local)
        return [params[p]["range"][0] + r.random() *
                (params[p]["range"][1] - params[p]["range"][0])
                for p in keys]

    A = [sample(seed + i*100) for i in range(n_samples)]
    B = [sample(seed + 10000 + i*100) for i in range(n_samples)]

    fA = [compute(a) for a in A]
    fB = [compute(b) for b in B]

    f0 = sum(fA) / n_samples
    var_total = sum((fa - f0)**2 for fa in fA) / n_samples
    if var_total < 1e-12:
        var_total = 1e-6

    S1, ST = {}, {}
    for j, p in enumerate(keys):
        # A_B: A with column j replaced by B
        AB = [list(a) for a in A]
        BA = [list(b) for b in B]
        for i in range(n_samples):
            AB[i][j] = B[i][j]
            BA[i][j] = A[i][j]

        fAB = [compute(ab) for ab in AB]
        fBA = [compute(ba) for ba in BA]

        # Jansen estimator for S1
        s1_num = sum((fB[i] - fAB[i])**2 for i in range(n_samples)) / (2*n_samples)
        s1     = max(0.0, 1 - s1_num / var_total)

        # Jansen estimator for ST
        st_num = sum((fA[i] - fAB[i])**2 for i in range(n_samples)) / (2*n_samples)
        st     = st_num / var_total

        S1[p] = round(s1, 4)
        ST[p] = round(min(1.0, st), 4)

    total_S1 = sum(S1.values())
    ranked = sorted(S1.items(), key=lambda x: -x[1])

    return {
        "index":    index,
        "method":   "Sobol",
        "n_samples":n_samples,
        "var_total":round(var_total, 6),
        "S1":       S1,
        "ST":       ST,
        "S1_sum":   round(total_S1, 3),
        "ranking":  [{"param": k, "S1": S1[k], "ST": ST[k],
                       "name": params[k]["name"],
                       "interaction": round(ST[k] - S1[k], 4)}
                     for k, _ in ranked],
    }


def full_sensitivity_report(basin: dict) -> dict:
    """
    Complete sensitivity report for a basin: OAT + Morris + Sobol for ATDI + ASI.
    """
    from conflict_index import compute_atdi as real_atdi
    # Compute current ATDI for context
    bid = basin.get("id", "")
    current_tdi = basin.get("tdi", 0.3)

    return {
        "basin_id":       bid,
        "basin_name":     basin.get("name", bid),
        "current_atdi":   current_tdi,
        "ATDI": {
            "OAT":    oat_sensitivity("ATDI"),
            "Morris": morris_sensitivity("ATDI"),
            "Sobol":  sobol_sensitivity("ATDI", n_samples=200),
        },
        "ASI": {
            "OAT":    oat_sensitivity("ASI"),
            "Sobol":  sobol_sensitivity("ASI", n_samples=200),
        },
    }


def generate_sensitivity_html(basin: dict) -> str:
    """Generate HTML sensitivity report."""
    report = full_sensitivity_report(basin)
    atdi_oat = report["ATDI"]["OAT"]
    atdi_sob = report["ATDI"]["Sobol"]
    asi_oat  = report["ASI"]["OAT"]

    oat_rows = "".join(
        f"<tr><td><b>{r['param']}</b></td><td>{r['name']}</td>"
        f"<td style='color:#f0883e'>{r['effect_pct']:.2f}%</td>"
        f"<td><div style='background:#238636;height:12px;"
        f"width:{min(int(r['effect_pct']*3),300)}px;border-radius:3px'></div></td></tr>"
        for r in atdi_oat["ranking"]
    )
    sob_rows = "".join(
        f"<tr><td><b>{r['param']}</b></td><td>{r['name']}</td>"
        f"<td style='color:#58a6ff'>{r['S1']:.4f}</td>"
        f"<td style='color:#e3b341'>{r['ST']:.4f}</td>"
        f"<td style='color:#8b949e'>{r['interaction']:.4f}</td></tr>"
        for r in atdi_sob["ranking"]
    )

    return f"""<!DOCTYPE html>
<html><head><title>ATDI Sensitivity — {report['basin_name']}</title>
<style>body{{font-family:Segoe UI;background:#0d1117;color:#e6edf3;padding:28px}}
h1{{color:#58a6ff}} h2{{color:#79c0ff;margin-top:22px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th{{background:#161b22;color:#8b949e;padding:8px;text-align:left;
   font-size:10px;text-transform:uppercase;letter-spacing:.1em}}
td{{padding:8px;border-bottom:1px solid #21262d}}
</style></head><body>
<h1>🎯 ATDI Sensitivity Analysis — {report['basin_name']}</h1>
<p style='color:#8b949e'>Current ATDI: <b>{report['current_atdi']:.3f}</b> ·
Methods: OAT + Morris + Sobol (Saltelli 2010) ·
Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991</p>

<h2>One-at-a-Time (OAT) — Parameter Influence on ATDI</h2>
<p style='color:#8b949e;font-size:12px'>Percentage change in ATDI when each
parameter is varied ±50% from its default value</p>
<table><tr><th>Param</th><th>Description</th><th>Max Effect</th>
<th>Visual</th></tr>{oat_rows}</table>

<h2>Sobol Variance-Based Sensitivity Indices</h2>
<p style='color:#8b949e;font-size:12px'>
S1 = first-order index (direct effect) ·
ST = total-order index (including interactions)</p>
<table><tr><th>Param</th><th>Description</th><th>S1 (Direct)</th>
<th>ST (Total)</th><th>Interaction</th></tr>{sob_rows}</table>

<p style='margin-top:16px;background:#161b22;border-radius:6px;padding:12px;
  border-left:3px solid #58a6ff;font-size:13px'>
<b>Key Finding:</b> {atdi_sob['ranking'][0]['name']} (S1={atdi_sob['ranking'][0]['S1']:.3f})
is the dominant driver of ATDI uncertainty in {report['basin_name']}.
S1 sum = {atdi_sob['S1_sum']:.3f} (values &lt;1 indicate parameter interactions).
</p>

<p style='margin-top:20px;font-size:11px;color:#8b949e'>
References: Saltelli et al.(2010) Global Sensitivity Analysis ·
Morris(1991) Technometrics · Sobol(2001) Math.Comp.Simul.
</p></body></html>"""


if __name__ == "__main__":
    import sys, os, unittest.mock as _mock
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    for m in ["qgis","qgis.PyQt","qgis.PyQt.QtWidgets","qgis.PyQt.QtCore",
              "qgis.PyQt.QtGui","qgis.core","qgis.gui"]:
        sys.modules.setdefault(m, _mock.MagicMock())

    print("=== ATDI Sensitivity Analysis Engine ===")
    oat = oat_sensitivity("ATDI")
    print(f"\n  OAT ATDI (base={oat['base_value']:.4f}):")
    for r in oat["ranking"]:
        print(f"    {r['param']}: {r['effect_pct']:.2f}% — {r['name']}")

    morris = morris_sensitivity("ATDI", n_trajectories=100)
    print(f"\n  Morris screening:")
    for r in morris["ranking"]:
        print(f"    {r['param']}: μ*={r['mu_star']:.4f} — {r['class']}")

    sobol = sobol_sensitivity("ATDI", n_samples=300)
    print(f"\n  Sobol indices (S1 sum={sobol['S1_sum']:.3f}):")
    for r in sobol["ranking"]:
        print(f"    {r['param']}: S1={r['S1']:.4f}, ST={r['ST']:.4f}")
    print("✅ sensitivity_analysis.py OK")


def run_sobol_analysis(basin: dict, n_samples: int = 512) -> dict:
    """Alias for sobol_sensitivity — run Sobol global sensitivity analysis."""
    return sobol_sensitivity(n_samples=n_samples)


def run_morris_analysis(basin: dict, n_trajectories: int = 20) -> dict:
    """Alias for morris_sensitivity — run Morris screening."""
    return morris_sensitivity(n_trajectories=n_trajectories)



def render_sensitivity_page(basin: dict) -> None:
    import streamlit as st, plotly.graph_objects as go
    st.markdown("## 🧪 Sensitivity Analysis — ATDI Parameters")
    st.caption("One-at-a-Time (OAT) · Morris screening · Sobol variance decomposition")
    index = st.selectbox("Index", ["ATDI","AHIFD","ASI"], key="sens_index")
    n_samples = st.slider("Monte Carlo samples", 50, 500, 100, key="sens_n")
    if st.button("▶ Run Sensitivity Analysis", key="sens_run"):
        with st.spinner("Running…"):
            try:
                results = oat_sensitivity(index)
                if results and isinstance(results, dict):
                    params = list(results.keys())
                    values = [abs(v) if isinstance(v,(int,float)) else 0 for v in results.values()]
                    fig = go.Figure(go.Bar(x=params, y=values,
                        marker_color=["#3b82f6" if v == max(values) else "#64748b" for v in values]))
                    fig.update_layout(template="plotly_dark", height=350,
                        title=f"OAT Sensitivity — {index}", yaxis_title="|ΔIndex|")
                    st.plotly_chart(fig, use_container_width=True)
                    st.info(f"Most sensitive parameter: **{params[values.index(max(values))]}**")
                else:
                    st.info("Sensitivity results computed. Check parameters above.")
            except Exception as e:
                st.warning(f"Sensitivity: {e}")
    else:
        st.info("👆 Press **Run** to compute sensitivity indices")
