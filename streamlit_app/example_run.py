#!/usr/bin/env python3
"""
example_run.py — HSAE v6.01 Minimal Usage Example
===================================================
Demonstrates the full HSAE pipeline on the Blue Nile (GERD) basin
using built-in simulation (no API keys required).

Usage:
    python example_run.py

Output:
    - ATDI score and legal status
    - NSE / KGE metrics
    - Basin summary table (CSV)

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("HydroSovereign AI Engine (HSAE) v6.01")
print("Minimal Example — Blue Nile (GERD) Basin")
print("=" * 60)

# ── 1. Load basin configuration ────────────────────────────────
from basins_global import GLOBAL_BASINS, ALL_NAMES

basin_name = "Blue Nile (GERD)"
basin = GLOBAL_BASINS.get(basin_name, GLOBAL_BASINS[ALL_NAMES[0]])
print(f"\n✅ Basin:    {basin['name']}")
print(f"   River:    {basin['river']}")
print(f"   Country:  {basin.get('country', ['—'])[0]}")
print(f"   Treaty:   {basin['treaty']}")
print(f"   Capacity: {basin['cap']} BCM")

# ── 2. Generate simulation DataFrame ──────────────────────────
print("\n📊 Generating physics-based simulation (365 days)...")

np.random.seed(42)
dates    = pd.date_range("2022-01-01", periods=365, freq="D")
inflow   = np.maximum(0.3, np.random.exponential(1.2, 365))
outflow  = inflow * np.random.uniform(0.5, 0.85, 365)
evap     = np.ones(365) * 0.15
volume   = np.cumsum(inflow - outflow - evap) * 0.01 + 30
pct_full = np.clip(volume / basin['cap'] * 100, 5, 100)

df = pd.DataFrame({
    "Date":        dates,
    "Inflow_BCM":  inflow,
    "Outflow_BCM": outflow,
    "Evap_BCM":    evap,
    "Volume_BCM":  volume,
    "Pct_Full":    pct_full,
    "Flow_m3s":    outflow * 1e9 / 86400,
})
print(f"   Shape: {df.shape} · Columns: {list(df.columns)}")

# ── 3. Compute ATDI ────────────────────────────────────────────
print("\n⚖️  Computing ATDI (Alkhedir Transparency Deficit Index)...")

from hsae_tdi import compute_atdi, tdi_legal_status, add_tdi_to_df, TDI_ALPHA, TDI_EPSILON
print(f"   Formula: ATDI = clip((I_adj - Q_out) / (I_adj + ε), 0, 1) × 100")
print(f"   α = {TDI_ALPHA} (ET correction) · ε = {TDI_EPSILON} (stabiliser)")

df = add_tdi_to_df(df, inflow_col="Inflow_BCM", outflow_col="Outflow_BCM")
atdi = float(df["ATDI_pct"].mean())
status, colour, articles = tdi_legal_status(atdi)

print(f"\n   ATDI Score:     {atdi:.1f}%")
print(f"   Legal Status:   {status}")
print(f"   UNWC Articles:  {articles}")

art5_days = int(df["TDI_art5_flag"].sum())
art7_days = int(df["TDI_art7_flag"].sum())
print(f"   Art.5 exceedance: {art5_days} days")
print(f"   Art.7 exceedance: {art7_days} days")

# ── 4. NSE / KGE validation (synthetic obs) ───────────────────
print("\n📈 Computing NSE / KGE performance metrics...")

from hsae_validation import nse, kge, pbias
obs_flow = df["Flow_m3s"].values * np.random.normal(1, 0.05, 365)
sim_flow = df["Flow_m3s"].values

nse_val   = nse(obs_flow, sim_flow)
kge_val   = kge(obs_flow, sim_flow)
pbias_val = pbias(obs_flow, sim_flow)

print(f"   NSE:   {nse_val:.3f}  (>0.65 = Good)")
print(f"   KGE:   {kge_val:.3f}  (>0.65 = Good)")
print(f"   PBIAS: {pbias_val:.1f}% (<±10% = Good)")

# ── 5. Export summary CSV ──────────────────────────────────────
out_path = "hsae_example_output.csv"
summary = df[["Date","Inflow_BCM","Outflow_BCM","ATDI_pct",
              "TDI_art5_flag","TDI_art7_flag","Volume_BCM","Pct_Full"]].head(30)
summary.to_csv(out_path, index=False)
print(f"\n💾 Output saved: {out_path} (first 30 rows)")

# ── 6. Final summary ──────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Basin:        {basin_name}")
print(f"ATDI:         {atdi:.1f}%  →  {status}")
print(f"NSE:          {nse_val:.3f}")
print(f"KGE:          {kge_val:.3f}")
print(f"Art.7 days:   {art7_days}/365")
print(f"Output:       {out_path}")
print("\n✅ Example complete. Run 'streamlit run app.py' for full UI.")
