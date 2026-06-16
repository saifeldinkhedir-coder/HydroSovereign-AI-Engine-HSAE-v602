"""
HSAE v6.01 — Fast GEE Real Data Reader
=======================================
Reads from pre-computed data/gee_realtime.json
Response time: < 0.1 seconds (no GEE connection needed)

Usage in app.py:
    from gee_realtime_reader import get_basin_data, get_all_basins
    data = get_basin_data("blue_nile_gerd")
"""

import json
import os
import datetime
from pathlib import Path

REALTIME_PATH = Path("data/gee_realtime.json")

def get_all_basins() -> dict:
    """Load full pre-computed dataset."""
    if not REALTIME_PATH.exists():
        return {"error": "data/gee_realtime.json not found. Run precompute_gee_daily.py first."}
    with open(REALTIME_PATH) as f:
        return json.load(f)

def get_basin_data(basin_id: str) -> dict:
    """
    Get real satellite data for a basin — instant, no GEE call.

    Returns dict with:
        gpm.P_mm_day     : list[float]  monthly precipitation mm/day
        gpm.mean_P       : float        annual mean
        grace.tws_cm     : list[float]  monthly TWS anomaly cm
        grace.mean_tws   : float
        glofas.Q_m3s     : list[float]  monthly discharge m3/s
        glofas.mean_Q    : float
        smap.sm_m3m3     : list[float]  soil moisture
        temperature.T_C  : list[float]  monthly temperature °C
        data_age_hours   : float        hours since last update
    """
    all_data = get_all_basins()
    if "error" in all_data:
        return all_data

    basins = all_data.get("basins", {})
    if basin_id not in basins:
        available = list(basins.keys())
        return {
            "error": f"Basin '{basin_id}' not found.",
            "available_basins": available
        }

    data = basins[basin_id].copy()

    # Add data age
    computed_at = all_data.get("computed_at", "")
    if computed_at:
        age = datetime.datetime.utcnow() - datetime.datetime.fromisoformat(computed_at)
        data["data_age_hours"] = round(age.total_seconds() / 3600, 1)
        data["computed_at"]    = computed_at

    return data

def get_data_status() -> dict:
    """Quick status check for Streamlit sidebar."""
    all_data = get_all_basins()
    if "error" in all_data:
        return {"ok": False, "message": all_data["error"]}

    computed_at = all_data.get("computed_at", "")
    age_h = 0
    if computed_at:
        age = datetime.datetime.utcnow() - datetime.datetime.fromisoformat(computed_at)
        age_h = age.total_seconds() / 3600

    return {
        "ok":           True,
        "computed_at":  computed_at,
        "age_hours":    round(age_h, 1),
        "n_basins":     all_data.get("n_basins", 0),
        "date_range":   all_data.get("date_range", {}),
        "fresh":        age_h < 25   # updated within 25 hours
    }


if __name__ == "__main__":
    status = get_data_status()
    print(f"Status: {status}")
    if status["ok"]:
        data = get_basin_data("blue_nile_gerd")
        print(f"GPM mean: {data.get('gpm',{}).get('mean_P')} mm/day")
        print(f"GRACE mean: {data.get('grace',{}).get('mean_tws')} cm")
        print(f"GloFAS mean: {data.get('glofas',{}).get('mean_Q')} m3/s")
        print(f"Data age: {data.get('data_age_hours')} hours")
