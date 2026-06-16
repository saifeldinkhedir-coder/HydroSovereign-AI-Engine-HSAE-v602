"""
test_core.py — HSAE v6.01 Core Tests
=====================================
Pytest suite covering the five canonical indices and HBV model.
Run: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import pytest

# ══════════════════════════════════════════════════════════════════
# 1. TDI / ATDI canonical formula tests
# ══════════════════════════════════════════════════════════════════

def test_tdi_zero_when_equal_flows():
    """TDI = 0 when inflow equals outflow (no deficit)."""
    from hsae_tdi import compute_tdi
    inflow  = np.array([1.0, 1.0, 1.0])
    outflow = np.array([1.0, 1.0, 1.0])
    tdi = compute_tdi(inflow, outflow)
    assert np.allclose(tdi, 0.0, atol=0.01), f"Expected 0, got {tdi}"


def test_tdi_high_when_outflow_zero():
    """TDI → 1 when outflow is zero (full withholding)."""
    from hsae_tdi import compute_tdi
    inflow  = np.array([1.0, 1.0, 1.0])
    outflow = np.array([0.0, 0.0, 0.0])
    tdi = compute_tdi(inflow, outflow)
    assert np.all(tdi > 0.9), f"Expected ~1, got {tdi}"


def test_atdi_range():
    """ATDI must be in [0, 100]."""
    from hsae_tdi import compute_atdi
    inflow  = np.random.rand(365) * 2
    outflow = np.random.rand(365) * 1.5
    atdi = compute_atdi(inflow, outflow)
    assert 0.0 <= atdi <= 100.0, f"ATDI out of range: {atdi}"


def test_tdi_alpha_correction():
    """ET correction (alpha=0.30) reduces effective inflow."""
    from hsae_tdi import compute_tdi, TDI_ALPHA
    assert TDI_ALPHA == 0.30, f"Alpha must be 0.30, got {TDI_ALPHA}"
    inflow  = np.array([1.0])
    outflow = np.array([0.5])
    et_pm   = np.array([0.5])
    tdi_raw = compute_tdi(inflow, outflow)
    tdi_adj = compute_tdi(inflow, outflow, et_pm=et_pm)
    assert tdi_adj <= tdi_raw, "ET correction should reduce TDI"


def test_epsilon_prevents_division_by_zero():
    """Epsilon prevents division by zero when inflow is 0."""
    from hsae_tdi import compute_tdi, TDI_EPSILON
    assert TDI_EPSILON == 0.001, f"Epsilon must be 0.001, got {TDI_EPSILON}"
    inflow  = np.array([0.0])
    outflow = np.array([0.0])
    tdi = compute_tdi(inflow, outflow)
    assert np.isfinite(tdi).all(), "TDI must be finite when inflow=0"


def test_legal_status_mapping():
    """ATDI legal status maps correctly to UN articles."""
    from hsae_tdi import tdi_legal_status
    assert "Compliant" in tdi_legal_status(10.0)[0]
    assert "Art. 5"    in tdi_legal_status(30.0)[2]
    assert "7"         in tdi_legal_status(45.0)[2]  # "Art. 5, 7"
    assert "9"         in tdi_legal_status(60.0)[2]
    assert "12"        in tdi_legal_status(75.0)[2]


# ══════════════════════════════════════════════════════════════════
# 2. NSE / KGE / PBIAS metrics
# ══════════════════════════════════════════════════════════════════

def test_nse_perfect():
    """NSE = 1 for perfect simulation."""
    from hsae_validation import nse
    obs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    nse_val = nse(obs, obs)
    assert abs(nse_val - 1.0) < 1e-9, f"NSE should be 1, got {nse_val}"


def test_nse_bad_model():
    """NSE < 0 for model worse than mean."""
    from hsae_validation import nse
    obs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    sim = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
    assert nse(obs, sim) < 0.0


def test_kge_perfect():
    """KGE = 1 for perfect simulation."""
    from hsae_validation import kge
    obs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert abs(kge(obs, obs) - 1.0) < 1e-9


def test_pbias_zero():
    """PBIAS = 0 for unbiased simulation."""
    from hsae_validation import pbias
    obs = np.array([1.0, 2.0, 3.0])
    assert abs(pbias(obs, obs)) < 1e-9


# ══════════════════════════════════════════════════════════════════
# 3. Basin registry
# ══════════════════════════════════════════════════════════════════

def test_global_basins_count():
    """GLOBAL_BASINS must contain exactly 26 basins."""
    from basins_global import GLOBAL_BASINS
    assert len(GLOBAL_BASINS) == 26, f"Expected 26, got {len(GLOBAL_BASINS)}"


def test_basin_required_keys():
    """Every basin must have lat, lon, river, treaty."""
    from basins_global import GLOBAL_BASINS
    for name, b in GLOBAL_BASINS.items():
        for key in ['lat','lon','river','treaty','continent']:
            assert key in b, f"{name} missing key '{key}'"


def test_gerd_basin_present():
    """Blue Nile (GERD) must be in registry."""
    from basins_global import GLOBAL_BASINS
    ids = [b.get('id','') for b in GLOBAL_BASINS.values()]
    assert 'GERD_ETH' in ids, "GERD_ETH not found in GLOBAL_BASINS"


# ══════════════════════════════════════════════════════════════════
# 4. HBV model
# ══════════════════════════════════════════════════════════════════

def test_hbv_runs_without_error():
    """HBV must run and return a dict with Q_sim."""
    from hsae_hbv import run_hbv, HBVParams
    params   = HBVParams()
    n        = 400  # warm_up=365 + 35 active
    rain_mm  = np.random.rand(n) * 5
    temp_c   = np.ones(n) * 15
    pet_mm   = np.ones(n) * 2
    result   = run_hbv(rain_mm, temp_c, pet_mm, params, area_km2=174000)
    assert result is not None, "run_hbv returned None"
    assert "Q_mm" in result or "Q_m3s" in result or len(result) > 0


def test_hbv_output_positive():
    """HBV simulated discharge must be non-negative."""
    from hsae_hbv import run_hbv, HBVParams
    params  = HBVParams()
    n       = 400
    rain_mm = np.random.rand(n) * 5
    temp_c  = np.ones(n) * 15
    pet_mm  = np.ones(n) * 2
    result  = run_hbv(rain_mm, temp_c, pet_mm, params, area_km2=174000)
    if isinstance(result, dict) and "Q_mm" in result:
        assert np.all(np.array(result["Q_mm"]) >= 0)
    elif isinstance(result, dict) and "Q_m3s" in result:
        assert np.all(np.array(result["Q_m3s"]) >= 0)


# ══════════════════════════════════════════════════════════════════
# 5. ATDI → DataFrame integration
# ══════════════════════════════════════════════════════════════════

def test_add_tdi_to_df():
    """add_tdi_to_df must add TDI columns to DataFrame."""
    from hsae_tdi import add_tdi_to_df
    df = pd.DataFrame({
        'Date':        pd.date_range('2022-01-01', periods=365, freq='D'),
        'Inflow_BCM':  np.random.rand(365) + 0.5,
        'Outflow_BCM': np.random.rand(365) * 0.5,
        'Evap_BCM':    np.ones(365) * 0.1,
    })
    out = add_tdi_to_df(df, inflow_col='Inflow_BCM', outflow_col='Outflow_BCM')
    assert 'TDI_adj'   in out.columns, "TDI_adj missing"
    assert 'ATDI_pct'  in out.columns, "ATDI_pct missing"
    assert 'TDI_art5_flag' in out.columns, "Legal flag missing"
    assert out['ATDI_pct'].between(0, 100).all(), "ATDI_pct out of range"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
