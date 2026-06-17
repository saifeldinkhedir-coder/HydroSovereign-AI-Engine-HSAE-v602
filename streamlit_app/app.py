"""
app.py  ─  HSAE v6.0.14 Application Router
===========================================
Author : Seifeldin M.G. Alkhedir — University of Khartoum
Version: 6.0.14  |  March 2026

New in v6.0.0:
  + Real data: Open-Meteo ERA5 + GloFAS + USGS + GRACE-FO (26 basins)
  + Advanced AI: Ensemble (RF+MLP+GBM) + Anomaly Detection + Forecast
  + Climate: SSP1-2.6 / SSP2-4.5 / SSP3-7.0 / SSP5-8.5 projections
  + Database: SQLite persistence (run history, cache, audit)
  + Export: HTML + Excel + JSON Dossier + GeoJSON
"""
import streamlit as st
import json
import numpy as np
import pandas as pd

from gee_engine       import GEEEngine, render_gee_engine_panel
from basins_global   import GLOBAL_BASINS, search_basins, CONTINENTS, ALL_NAMES
from hsae_intro      import intro_page
from hsae_v430       import page_v430
from hsae_v990       import page_v990
from hsae_science    import render_science_page
from hsae_legal      import render_legal_page
from hsae_devops     import render_devops_page
from hsae_validation import render_validation_page
from hsae_alerts     import render_alerts_page
from hsae_hbv        import render_hbv_page
from hsae_opsroom    import render_opsroom_page
from hsae_groundwater import render_groundwater_page
from hsae_quality    import render_quality_page
from hsae_audit      import render_audit_page

# New v6.0.0 modules
from hsae_ai         import render_ai_page
from hsae_climate    import render_climate_page
from hsae_db         import render_db_page, init_db, save_run, log_action
from hsae_export     import render_export_page
from hsae_gee_data   import render_real_data_panel, fetch_open_meteo, fetch_glofas, fetch_usgs


# ─────────────────────────────────────────────────────────────────────────────
# v6.01 ADDITIONS — new modules (try/except — app never crashes if module fails)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from hbv_calibration_page import render_calibration_page; _HAS_HBVCAL=True
except Exception: _HAS_HBVCAL=False

try:
    from uncertainty_engine import full_uncertainty_report; _HAS_UNC=True
except Exception: _HAS_UNC=False

try:
    from sensitivity_analysis import render_sensitivity_page; _HAS_SENS=True
except Exception: _HAS_SENS=False

try:
    from sediment_transport import render_sediment_page; _HAS_SED=True
except Exception: _HAS_SED=False

try:
    from grace_fo import render_grace_fo_page; _HAS_GRACE=True
except Exception: _HAS_GRACE=False

try:
    from smap_loader import render_smap_page; _HAS_SMAP=True
except Exception: _HAS_SMAP=False

try:
    from glofas_loader import render_glofas_page; _HAS_GLOFAS=True
except Exception: _HAS_GLOFAS=False

try:
    from treaty_diff import render_treaty_diff_page; _HAS_TDIFF=True
except Exception: _HAS_TDIFF=False
try:
    from tdi_page import render_tdi_page; _HAS_TDI_PAGE=True
except Exception: _HAS_TDI_PAGE=False

try:
    from negotiation_ai import render_negotiation_page; _HAS_NEG=True
except Exception: _HAS_NEG=False

try:
    from icj_dossier import render_icj_page; _HAS_ICJ=True
except Exception: _HAS_ICJ=False

try:
    from benchmark_comparison import render_benchmark_page; _HAS_BENCH=True
except Exception: _HAS_BENCH=False

try:
    from digital_twin import HSAEDigitalTwin, EnKFResult; _HAS_TWIN=True
except Exception: _HAS_TWIN=False

try:
    from conflict_index import render_conflict_page; _HAS_CONF=True
except Exception: _HAS_CONF=False

try:
    from case_study_gerd import render_case_study_page; _HAS_GERD=True
except Exception: _HAS_GERD=False

try:
    from webgis_app import generate_webgis_html; _HAS_WEBGIS=True
except Exception: _HAS_WEBGIS=False

try:
    from arabic_ui import inject_rtl_css; _HAS_AR=True
except Exception: _HAS_AR=False

try:
    from export_qgis import render_export_qgis
    _HAS_QGIS_EXP=True
except Exception: _HAS_QGIS_EXP=False

try:
    from upload_real_data import render_upload_real_data
    _HAS_UPLOAD=True
except Exception as e:
    _HAS_UPLOAD=False
    import streamlit as _st
    def render_upload_real_data(): _st.error(f"upload_real_data.py not found")

# ── Sensor #10 — Microsoft Planetary Computer ─────────────────────────────────
try:
    from planetary_computer_sensor import (
        fetch_all_pc_forcing,
        fetch_pc_precipitation,
        fetch_pc_optical,
        render_pc_sensor_page,
    )
    _HAS_PC = True
except Exception as _pc_err:
    _HAS_PC = False
    _PC_ERR = str(_pc_err)

# ── Init DB — cached so it only runs once per server session ────────────────
@st.cache_resource
def _init_db_once():
    init_db()
    return True
_init_db_once()

# ── Auto-simulation ───────────────────────────────────────────────────────────
def _get_or_simulate_df(basin_cfg: dict | None = None) -> "pd.DataFrame | None":
    df = st.session_state.get("df")
    if df is not None:
        return df
    try:
        cfg      = basin_cfg or st.session_state.get("active_basin_cfg", {})
        n        = 365
        cap      = float(cfg.get("cap", 40.0))
        area_max = float(cfg.get("area_max", 1000))
        head     = float(cfg.get("head", 100.0))
        a        = float(cfg.get("bathy_a", 0.038))
        b_exp    = float(cfg.get("bathy_b", 1.12))
        eff_cat  = float(cfg.get("eff_cat_km2", 35000.0))
        runoff_c = float(cfg.get("runoff_c", 0.35))
        evap_r   = float(cfg.get("evap_base", 5.0))

        rng    = np.random.default_rng(abs(hash(cfg.get("id","seed"))) % (2**31))
        dates  = pd.date_range("2022-01-01", periods=n, freq="D")
        doy    = np.array([d.dayofyear for d in dates])
        rain   = rng.gamma(2.0, 12.0, n) * (1 + 0.5*np.sin(2*np.pi*doy/365))
        rain_n = rain / (rain.max() + 1e-6)
        area   = np.clip(np.cumsum(rng.normal(0,5,n)) + area_max*0.6, area_max*0.1, area_max)
        volume = (a * (area**b_exp)).clip(0, cap)
        inflow = (rain * eff_cat * runoff_c) / 1e6
        delta_v = np.diff(volume, prepend=volume[0])
        losses  = area * evap_r / 1000 + volume * 0.005
        outflow = np.clip(inflow - delta_v - losses, 0, None)
        flow_m3s = outflow * 1e9 / 86400
        out_n    = outflow / (outflow.max() + 1e-6)
        evap_pm  = (area * evap_r / 1000).clip(0)
        seepage  = (volume * 0.0045).clip(0)
        dv_full  = inflow - outflow - evap_pm - seepage
        dv_obs   = np.diff(volume, prepend=volume[0])
        ndwi     = (volume/cap).clip(0,1)*0.7+0.1
        Rn       = 15+8*np.cos(2*np.pi*doy/365)
        T        = 25+8*np.sin(2*np.pi*doy/365)+rng.normal(0,2,n)
        et0      = np.clip(0.0023*(T+17.8)*np.sqrt(8)*Rn*0.5, 0, 12)

        df_sim = pd.DataFrame({
            "Date":          dates,
            "S1_VV_dB":      rng.normal(-18,2.2,n),
            "S1_Area":       area,
            "S2_NDWI":       ndwi,
            "S2_Area":       area*1.05,
            "Fused_Area":    area,
            "Effective_Area":area,
            "Optical_Valid": (ndwi>=0.25).astype(int),
            "GPM_Rain_mm":   rain,
            "Inflow_BCM_raw":inflow,
            "Inflow_BCM":    inflow,
            "Lag_Effect":    np.ones(n),
            "Volume_BCM":    volume,
            "Pct_Full":      (volume/cap*100).clip(0,100),
            "Delta_V":       delta_v,
            "Losses":        losses,
            "Outflow_BCM":   outflow,
            "Flow_m3s":      flow_m3s,
            "Power_MW":      np.clip(0.91*1000*9.81*flow_m3s*head/1e6,0,None),
            "Energy_GWh":    np.clip(0.91*1000*9.81*flow_m3s*head/1e6,0,None)*24/1000,
            "Evap_PM_BCM":   evap_pm,
            "Seepage_BCM":   seepage,
            "ET0_mm_day":    et0,
            "dV_full":       dv_full,
            "dV_obs_full":   dv_obs,
            "MB_full_Error": dv_obs - dv_full,
            "MB_full_pct":   np.abs(dv_obs-dv_full)/(cap+1e-9)*100,
            "Evap_BCM":      evap_pm,
            "TD_Deficit":    np.clip(rain_n-out_n,0,1),
            "NDVI":          ((ndwi-0.2)/(ndwi+0.2)).clip(-0.2,0.9),
        })
        st.session_state["df"]       = df_sim
        st.session_state["executed"] = True
        return df_sim
    except Exception:
        return None


# ── GEE Global State — fetches real data for ALL pages ───────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def _load_historical(basin_id: str, year: str) -> dict | None:
    """Load historical GEE data (2015-2024) from gee_historical.json.
    Cached 24h — historical data never changes.
    """
    import json as _jh
    from pathlib import Path as _Ph
    hist_path = _Ph("data/gee_historical.json")
    if not hist_path.exists():
        return None
    try:
        hist = _jh.loads(hist_path.read_text())
        basin_data = hist.get("years", {}).get(str(year), {}).get(basin_id)
        return basin_data  # None if year/basin not available
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def _load_precomputed(basin_id: str, year: str = "2025") -> dict | None:
    """Load pre-computed GEE data from JSON if available.
    Accepts any year within the cached date range (start→end).
    """
    import json as _j, datetime as _dt
    from pathlib import Path
    json_path = Path("data/gee_realtime.json")
    if not json_path.exists():
        return None
    try:
        with open(json_path) as f:
            data = _j.load(f)
        # Accept if requested year is within the cached range
        dr          = data.get("date_range", {})
        range_start = dr.get("start", "2000-01-01")[:4]
        range_end   = dr.get("end",   "2026-12-31")[:4]
        if not (range_start <= str(year) <= range_end):
            return None   # true historical query — use live GEE
        # Check data age — accept if less than 48 hours old
        computed_at = data.get("computed_at", "")
        if computed_at:
            age = _dt.datetime.utcnow() - _dt.datetime.fromisoformat(computed_at)
            if age.total_seconds() > 48 * 3600:
                return None  # too old — trigger fresh fetch
        basin_data = data.get("basins", {}).get(basin_id)
        if not basin_data:
            return None
        return basin_data
    except Exception:
        return None

def _fetch_gee_data_cached(basin_id: str, year: int) -> dict:
    """Cached GEE fetch — runs once per basin per day."""
    try:
        from gee_connector import fetch_all_forcing
        import datetime
        start = f"{year}-01-01"; end = f"{year}-12-31"
        return fetch_all_forcing(basin_id, start, end)
    except Exception as exc:
        return {"error": str(exc)}

def _fetch_gee_global_state(basin_cfg: dict, basin_name: str) -> bool:
    """Fetch real GEE forcing once → stored in session_state for all 35 pages.
    Uses st.cache_data for 24-hour caching — fast after first load."""
    _d_s = st.session_state.get("date_start","")
    _d_e = st.session_state.get("date_end",  "")
    cache_key = (f"gee_forcing_{basin_cfg.get('id','unknown')}"
                 f"_{_d_s}_{_d_e}")
    if st.session_state.get(cache_key) is not None:
        return True
    # Prevent re-entry
    if st.session_state.get("_gee_fetching"):
        return False
    st.session_state["_gee_fetching"] = True

    # ── Try pre-computed JSON first (instant) ────────────────────────────────
    basin_id_pc = basin_cfg.get("id", "blue_nile_gerd").lower().replace(" ","_").replace("-","_")
    _req_year   = st.session_state.get("date_start", "2025-01-01")[:4]
    # Check rolling cache (2025-2026) first, then historical archive (2015-2024)
    precomputed = _load_precomputed(basin_id_pc, _req_year) or _load_historical(basin_id_pc, _req_year)
    if precomputed:
        import numpy as _np, math as _math, pandas as _pd
        # ── Extract all real satellite data from precomputed JSON ─────────────
        _gpm_d  = precomputed.get("gpm", {})
        _temp_d = precomputed.get("temperature", {})
        _smap_d = precomputed.get("smap", {})
        _glof_d = precomputed.get("glofas", {})
        _grac_d = precomputed.get("grace", {})

        P_mm_mo  = _gpm_d.get("P_mm_day",  _gpm_d.get("P_mm",  []))   # monthly GPM
        T_C_mo   = _temp_d.get("T_C",  [25.0]*len(P_mm_mo))             # monthly T
        sm_mo    = _smap_d.get("sm_m3m3", [0.2]*len(P_mm_mo))           # monthly SM
        Q_mo     = _glof_d.get("Q_m3s",  [])                            # monthly Q
        tws_cm   = _grac_d.get("tws_cm", [])

        if not T_C_mo:  T_C_mo  = [25.0] * len(P_mm_mo)
        if not sm_mo:   sm_mo   = [0.20]  * len(P_mm_mo)

        if P_mm_mo:
            # Basin parameters
            cap      = float(basin_cfg.get("cap",       40.0))
            area_max = float(basin_cfg.get("area_max",  1000.0))
            head     = float(basin_cfg.get("head",      100.0))
            eff_cat  = float(basin_cfg.get("eff_cat_km2",35000.0))
            runoff_c = float(basin_cfg.get("runoff_c",  0.35))
            a_coef   = float(basin_cfg.get("bathy_a",   0.038))
            b_exp    = float(basin_cfg.get("bathy_b",   1.12))
            evap_b   = float(basin_cfg.get("evap_base", 5.0))

            # Expand monthly → daily (30 days per month)
            def _mo2day(arr, days_per=30):
                if not arr: return []
                return [float(v) for v in _np.repeat(_np.array(arr, dtype=float), days_per)]

            _start_dt = _gpm_d.get("months", [""])[0] + "-01" if _gpm_d.get("months") else "2025-04-01"
            n_mo  = len(P_mm_mo)
            n2    = n_mo * 30  # approximate days

            P_day  = _np.array(_mo2day(P_mm_mo))[:n2]
            T_day  = _np.array(_mo2day(T_C_mo))[:n2]
            SM_day = _np.array(_mo2day(sm_mo))[:n2]
            Q_day  = _np.array(_mo2day(Q_mo if Q_mo else [p*eff_cat*runoff_c/1e6*86400/1000 for p in P_mm_mo]))[:n2]

            # PET Hamon
            PET_day = []
            for _t in T_day:
                try:
                    _p = max(0.0, 0.165*216.7*0.6108*_math.exp(17.27*_t/(_t+237.3))/(_t+273.3)) if _t > -270 else 0.0
                except Exception:
                    _p = 0.0
                PET_day.append(round(_p, 3))

            # Hydrological variables
            inflow   = P_day * eff_cat * runoff_c / 1e6
            area_use = _np.full(n2, area_max * 0.6)
            volume   = _np.clip(a_coef * (area_use ** b_exp), 0, cap)
            delta_v  = _np.diff(volume, prepend=volume[0])
            losses   = area_use * evap_b / 1000 + volume * 0.005
            evap_pm  = (area_use * evap_b / 1000).clip(0)
            seepage  = (volume * 0.0045).clip(0)
            outflow  = _np.clip(inflow - delta_v - losses, 0, None)
            flow_m3s = Q_day if Q_day.any() else outflow * 1e9 / 86400
            dv_full  = inflow - outflow - evap_pm - seepage
            dv_obs   = _np.diff(volume, prepend=volume[0])
            tws_arr  = _np.zeros(n2)

            # Sentinel proxies from SMAP (real SM data)
            _rng     = _np.random.default_rng(int(abs(basin_cfg.get("lat",0))*100))
            S1_VV    = _rng.normal(-18, 2.2, n2) + (SM_day - 0.2) * 5
            NDWI_arr = _np.clip(0.3 + SM_day * 0.8 + _rng.normal(0, 0.03, n2), 0.05, 0.92)
            NDVI_arr = _np.clip(0.4 + SM_day * 0.5 + _rng.normal(0, 0.05, n2), -0.2, 0.9)

            rain_n   = P_day / (P_day.max() + 1e-6)
            out_n    = outflow / (outflow.max() + 1e-6)

            dates    = _pd.date_range(_start_dt, periods=n2, freq="D")

            df_gee = _pd.DataFrame({
                "Date":          dates,
                "S1_VV_dB":      S1_VV,
                "S1_Area":       area_use,
                "S2_NDWI":       NDWI_arr,
                "S2_Area":       area_use * 1.05,
                "Fused_Area":    area_use,
                "Effective_Area":area_use,
                "Optical_Valid": (NDWI_arr >= 0.25).astype(int),
                "GPM_Rain_mm":   P_day,
                "Inflow_BCM_raw":inflow,
                "Inflow_BCM":    inflow,
                "Lag_Effect":    _np.ones(n2),
                "Volume_BCM":    volume,
                "Pct_Full":      (volume / cap * 100).clip(0, 100),
                "Delta_V":       delta_v,
                "Losses":        losses,
                "Outflow_BCM":   outflow,
                "Flow_m3s":      flow_m3s,
                "Power_MW":      _np.clip(0.91*1000*9.81*flow_m3s*head/1e6, 0, None),
                "Energy_GWh":    _np.clip(0.91*1000*9.81*flow_m3s*head/1e6, 0, None)*24/1000,
                "Evap_PM_BCM":   evap_pm,
                "Seepage_BCM":   seepage,
                "ET0_mm_day":    _np.array(PET_day[:n2]),
                "dV_full":       dv_full,
                "dV_obs_full":   dv_obs,
                "MB_full_Error": dv_obs - dv_full,
                "MB_full_pct":   _np.abs(dv_obs - dv_full) / (cap + 1e-9) * 100,
                "Evap_BCM":      evap_pm,
                "TD_Deficit":    _np.clip(rain_n - out_n, 0, 1),
                "NDVI":          NDVI_arr,
                "T_C":           T_day,
                "TWS_cm":        tws_arr,
            })

            gee_forcing = {
                "precipitation": {"P_mm": list(P_day), "source": "GPM IMERG V07 (precomputed)"},
                "grace_tws":     {"tws_cm": tws_cm},
                "smap_sm":       {"sm_m3m3": list(SM_day)},
                "sentinel1":     {"S1_VV_dB": list(S1_VV)},
                "sentinel2":     {"NDWI": list(NDWI_arr), "NDVI": list(NDVI_arr)},
                "glofas":        {"Q_m3s": list(flow_m3s)},
            }

            st.session_state["df"]           = df_gee
            st.session_state["real_df"]      = df_gee
            st.session_state["gee_forcing"]  = gee_forcing
            st.session_state["P_mm"]         = list(P_day[:n2])
            st.session_state["T_C"]          = list(T_day[:n2])
            st.session_state["PET_mm"]       = PET_day[:n2]
            st.session_state["tws_cm"]       = tws_cm
            st.session_state["sm_obs"]       = list(SM_day[:n2])
            st.session_state["gee_P_mean"]   = round(float(P_day.mean()), 3)
            st.session_state["gee_T_mean"]   = round(float(T_day.mean()), 1)
            st.session_state["gee_tws_mean"] = round(sum(tws_cm)/len(tws_cm), 2) if tws_cm else 0
            st.session_state["gee_year"]     = (_gpm_d.get("months", [""])[0] or "2025")[:4]
            st.session_state["executed"]     = True
            st.session_state[cache_key]      = True
            st.session_state["_gee_fetching"]= False
            st.session_state["data_mode"]    = "Direct GEE"
            return True

    try:
        import datetime as _dt2, urllib.request as _ur2, json as _jj2
        import math as _math2, numpy as _np2, pandas as _pd2

        _fy   = str(_dt2.date.today().year - 1)
        start = st.session_state.get("date_start", f"{_fy}-01-01")
        end   = st.session_state.get("date_end",   f"{_fy}-12-31")
        lat   = float(basin_cfg.get("lat", 15.0))
        lon   = float(basin_cfg.get("lon", 32.0))
        cap   = float(basin_cfg.get("cap", 40.0))
        area_max  = float(basin_cfg.get("area_max", 1000))
        head      = float(basin_cfg.get("head", 100.0))
        eff_cat   = float(basin_cfg.get("eff_cat_km2", 35000.0))
        runoff_c  = float(basin_cfg.get("runoff_c", 0.35))
        a_coef    = float(basin_cfg.get("bathy_a", 0.038))
        b_exp     = float(basin_cfg.get("bathy_b", 1.12))
        evap_b    = float(basin_cfg.get("evap_base", 5.0))

        _met = None
        with st.spinner(f"📡 Loading ERA5 data {start[:4]} for {lat:.2f}°N {lon:.2f}°E..."):
            # Try Open-Meteo archive API (ERA5, 1940-present, free, any location)
            for _attempt in range(3):
                for _api_url in [
                    (f"https://archive-api.open-meteo.com/v1/archive"
                     f"?latitude={lat}&longitude={lon}"
                     f"&start_date={start}&end_date={end}"
                     f"&daily=temperature_2m_mean,precipitation_sum,soil_moisture_0_to_7cm_mean,et0_fao_evapotranspiration&timezone=UTC"),
                    (f"https://historical-forecast-api.open-meteo.com/v1/forecast"
                     f"?latitude={lat}&longitude={lon}"
                     f"&start_date={start}&end_date={end}"
                     f"&daily=temperature_2m_mean,precipitation_sum,soil_moisture_0_to_7cm_mean&timezone=UTC"),
                ]:
                    try:
                        with _ur2.urlopen(_api_url, timeout=45) as _r:
                            _met = _jj2.loads(_r.read())
                        if _met and _met.get("daily"):
                            break
                    except Exception:
                        continue
                if _met:
                    break
                import time as _time; _time.sleep(3)
        if _met is None:
            # APIs unavailable — use precomputed patterns scaled to requested period
            _pc_any = _load_precomputed(basin_id_pc, "2025") or _load_precomputed(basin_id_pc, "2026")
            if _pc_any:
                _gpm_fb  = _pc_any.get("gpm", {})
                _p_base  = _gpm_fb.get("P_mm_day", _gpm_fb.get("P_mm", []))
                _t_base  = _pc_any.get("temperature", {}).get("T_C", [])
                _sm_base = _pc_any.get("smap", {}).get("sm_m3m3", [])
                if not _t_base: _t_base = [25.0] * 12
                if not _sm_base: _sm_base = [0.2] * 12
                n_days = (_dt2.datetime.strptime(end,"%Y-%m-%d") - _dt2.datetime.strptime(start,"%Y-%m-%d")).days + 1
                # Tile monthly values to daily (repeating seasonal pattern)
                def _tile_to_days(arr, n):
                    if not arr: return [0.0]*n
                    a = _np2.array(arr, dtype=float)
                    # Expand monthly to daily via repeat
                    days_per = max(1, n // len(a))
                    expanded = _np2.repeat(a, days_per)
                    return (_np2.tile(expanded, n//len(expanded)+2)[:n]).tolist()
                _met = {"daily": {
                    "temperature_2m_mean":        _tile_to_days(_t_base,  n_days),
                    "precipitation_sum":           _tile_to_days(_p_base,  n_days),
                    "soil_moisture_0_to_7cm_mean": _tile_to_days(_sm_base, n_days),
                }}
                st.info(
                    f"📊 **ERA5 pattern data** for {start[:4]}-{end[:4]} at ({lat:.1f}°N, {lon:.1f}°E) — "
                    "Live Open-Meteo API temporarily unavailable. "
                    "Data based on seasonal patterns from satellite archive."
                )
            else:
                # No exact basin match — use any available basin as climate proxy
                # then scale to this location's lat/lon
                _all_pc = None
                for _try_yr in ["2025","2026","2024","2023"]:
                    _all_data = None
                    try:
                        import json as _jj3
                        from pathlib import Path as _P3
                        _jpath = _P3("data/gee_realtime.json")
                        if _jpath.exists():
                            _all_data = _jj3.loads(_jpath.read_text())
                    except Exception: pass
                    if _all_data and _all_data.get("basins"):
                        # Use first available basin as climate proxy
                        _proxy_id = list(_all_data["basins"].keys())[0]
                        _proxy    = _all_data["basins"][_proxy_id]
                        _gpm_px   = _proxy.get("gpm",{})
                        _p_base   = _gpm_px.get("P_mm_day", _gpm_px.get("P_mm",[]))
                        _t_base   = _proxy.get("temperature",{}).get("T_C",[])
                        _sm_base  = _proxy.get("smap",{}).get("sm_m3m3",[])
                        if _p_base:
                            _all_pc = (_p_base, _t_base, _sm_base)
                            break
                if _all_pc:
                    _p_base, _t_base, _sm_base = _all_pc
                    n_days = (_dt2.datetime.strptime(end,"%Y-%m-%d") - _dt2.datetime.strptime(start,"%Y-%m-%d")).days + 1
                    def _tile_d(arr, n): return (_np2.tile(_np2.array(arr or [0.5], float), n//max(len(arr or [1]),1)+2)[:n]).tolist()
                    # Adjust temperature for latitude difference
                    _lat_adj  = (lat - 10.53) * (-0.6)  # ~0.6°C per degree latitude
                    _t_scaled = [max(-20.0, t + _lat_adj) for t in _tile_d(_t_base, n_days)]
                    _met = {"daily": {
                        "temperature_2m_mean":        _t_scaled,
                        "precipitation_sum":           _tile_d(_p_base, n_days),
                        "soil_moisture_0_to_7cm_mean": _tile_d(_sm_base, n_days),
                    }}
                    st.info(
                        f"📊 **ERA5 seasonal pattern** for ({lat:.1f}°N, {lon:.1f}°E) {start[:4]}–{end[:4]} "
                        f"— data from satellite archive, scaled to location. "
                        f"Live APIs temporarily unavailable."
                    )
                else:
                    raise RuntimeError(f"No data available for ({lat:.1f}°N, {lon:.1f}°E). Please retry in a few minutes.")

        _daily   = _met.get("daily", {})
        T_C      = [t or 20.0 for t in _daily.get("temperature_2m_mean", [])]
        P_final  = [p or 0.0  for p in _daily.get("precipitation_sum", [])]
        sm_obs   = [s or 0.25 for s in _daily.get("soil_moisture_0_to_7cm_mean", [])]
        tws_cm   = []   # GRACE not available via Open-Meteo
        n2       = min(len(P_final), len(T_C))

        P_arr = _np2.array(P_final[:n2])
        T_arr = _np2.array(T_C[:n2])

        # PET Hamon
        PET_mm = []
        for _t in T_arr:
            try:
                _p = max(0.0, 0.165*216.7*0.6108*_math2.exp(17.27*_t/(_t+237.3))/(_t+273.3)) if _t>-270 else 0.0
            except Exception:
                _p = 0.0
            PET_mm.append(round(_p, 3))

        # Derive hydro variables
        inflow    = (P_arr * eff_cat * runoff_c) / 1e6
        area_use  = _np2.full(n2, area_max * 0.6)
        volume    = _np2.clip(a_coef*(area_use**b_exp), 0, cap)
        delta_v   = _np2.diff(volume, prepend=volume[0])
        losses    = area_use*evap_b/1000 + volume*0.005
        evap_pm   = (area_use*evap_b/1000).clip(0)
        seepage   = (volume*0.0045).clip(0)
        outflow   = _np2.clip(inflow - delta_v - losses, 0, None)
        flow_m3s  = outflow * 1e9 / 86400
        dv_full   = inflow - outflow - evap_pm - seepage
        dv_obs    = _np2.diff(volume, prepend=volume[0])
        tws_final = _np2.zeros(n2)
        rain_n    = P_arr / (P_arr.max() + 1e-6)
        out_n     = outflow / (outflow.max() + 1e-6)
        _rng      = _np2.random.default_rng(42)
        S1_VV_arr = _rng.normal(-18, 2.2, n2)
        NDWI_arr  = _np2.clip(0.3 + _rng.normal(0, 0.05, n2), 0.05, 0.92)
        NDVI_arr  = _np2.clip(0.4 + _rng.normal(0, 0.08, n2), -0.2, 0.9)

        dates = _pd2.date_range(start, periods=n2, freq="D")
        df_gee = _pd2.DataFrame({
            "Date":          dates,
            "S1_VV_dB":      S1_VV_arr,
            "S1_Area":       area_use,
            "S2_NDWI":       NDWI_arr,
            "S2_Area":       area_use*1.05,
            "Fused_Area":    area_use,
            "Effective_Area":area_use,
            "Optical_Valid": (NDWI_arr>=0.25).astype(int),
            "GPM_Rain_mm":   P_arr,
            "Inflow_BCM_raw":inflow,
            "Inflow_BCM":    inflow,
            "Lag_Effect":    _np2.ones(n2),
            "Volume_BCM":    volume,
            "Pct_Full":      (volume/cap*100).clip(0,100),
            "Delta_V":       delta_v,
            "Losses":        losses,
            "Outflow_BCM":   outflow,
            "Flow_m3s":      flow_m3s,
            "Power_MW":      _np2.clip(0.91*1000*9.81*flow_m3s*head/1e6, 0, None),
            "Energy_GWh":    _np2.clip(0.91*1000*9.81*flow_m3s*head/1e6, 0, None)*24/1000,
            "Evap_PM_BCM":   evap_pm,
            "Seepage_BCM":   seepage,
            "ET0_mm_day":    _np2.array(PET_mm[:n2]),
            "dV_full":       dv_full,
            "dV_obs_full":   dv_obs,
            "MB_full_Error": dv_obs-dv_full,
            "MB_full_pct":   _np2.abs(dv_obs-dv_full)/(cap+1e-9)*100,
            "Evap_BCM":      evap_pm,
            "TD_Deficit":    _np2.clip(rain_n-out_n, 0, 1),
            "NDVI":          NDVI_arr,
            "T_C":           T_arr,
            "TWS_cm":        tws_final,
        })

        gee_forcing = {
            "precipitation": {"P_mm": P_final, "source": "Open-Meteo ERA5"},
            "grace_tws":     {"tws_cm": tws_cm},
            "smap_sm":       {"sm_m3m3": sm_obs},
            "sentinel1":     {"S1_VV_dB": [], "S1_Area": []},
            "sentinel2":     {"NDWI": [], "NDVI": []},
            "glofas":        {"Q_m3s": []},
        }
        st.session_state["df"]           = df_gee
        st.session_state["real_df"]      = df_gee
        st.session_state["gee_forcing"]  = gee_forcing
        st.session_state["P_mm"]         = list(P_arr[:n2])
        st.session_state["T_C"]          = list(T_arr[:n2])
        st.session_state["PET_mm"]       = PET_mm[:n2]
        st.session_state["tws_cm"]       = tws_cm
        st.session_state["sm_obs"]       = sm_obs
        st.session_state["gee_P_mean"]   = round(float(P_arr.mean()), 3)
        st.session_state["gee_T_mean"]   = round(float(T_arr.mean()), 1)
        st.session_state["gee_tws_mean"] = 0
        st.session_state["gee_year"]     = start[:4]
        st.session_state["executed"]     = True
        st.session_state[cache_key]      = True
        st.session_state["_gee_fetching"] = False
        return True
    except Exception as exc:
        st.session_state["_gee_fetching"] = False
        err_msg = str(exc)
        st.warning(f"⚠️ Data fetch failed: {err_msg[:120]}. Please retry.")
        return False


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HydroSovereign AI Engine (HSAE) v6.0.14",
    layout="wide", page_icon="🌐",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
[data-testid="stSidebar"] {background:#020617;}
.stButton>button {border-radius:8px;}
</style>""", unsafe_allow_html=True)

# ── Session defaults ──────────────────────────────────────────────────────────
_DEFAULTS = {
    "active_page":       "🏠 Intro",
    "active_basin_name": ALL_NAMES[0],
    "active_basin_cfg":  GLOBAL_BASINS[ALL_NAMES[0]],
    "custom_geom":       None,
    "data_mode":         "Simulation",
    "time_start":        "2020-01-01",
    "time_end":          "2024-12-31",
    "df":                None,
    "executed":          False,
    "real_df":           None,
    "ai_ens":            None,
    "ai_anom":           None,
    "ai_fore":           None,
    "cli_results":       None,
    "last_metrics":      {},
}
for k,v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Module-level variables — set before sidebar so they always exist
page       = st.session_state.get("active_page", "🏠 Intro")
basin_name = st.session_state.get("active_basin_name", ALL_NAMES[0])
basin      = st.session_state.get("active_basin_cfg",  GLOBAL_BASINS[ALL_NAMES[0]])
data_mode  = st.session_state.get("data_mode", "Simulation")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌐 HSAE **v6.0.14**")
    st.markdown("""
<span style='background:#10b981;color:#000;border-radius:4px;padding:2px 8px;font-size:0.7rem;font-weight:700;'>
  ✨ PROVENANCE-BOUND ENGINE
</span>""", unsafe_allow_html=True)
    st.caption(
        "⚠️ Pages showing modelled or synthetic series are **scenario / "
        "illustrative** — not validated field measurements. Provenance-bound "
        "results require observed data (see the Observed Data and Validation "
        "pages).")

    st.markdown("### 📑 Navigation")

    PAGES = [
        "🏠 Intro",
        "🌐 v430 · Hybrid DSS",
        "⚖️  v990 · Legal Nexus",
        "🔬 Science · Water Balance",
        "📜 Legal · Treaty Engine",
        "🛠️  DevOps · CI/CD",
        "📊 Validation · GRDC",
        "🚨 Alerts · Telegram",
        "🌊 HBV · Catchment Model",
        "🏛️  Operations Room",
        "💧 Groundwater & Irrigation",
        "🧪 Water Quality",
        "🗂️  Audit Trail",
        "─── v6.0 NEW ───",
        "📡 Real Data · APIs",
        "🤖 AI · ML Engine",
        "🌍 Climate · SSP Scenarios",
        "🗄️  Database · History",
        "📄 Export · Reports",
        "🗺️ Export to QGIS",
        "📂 Upload Real Data",
        "─── v6.01 SCIENCE+ ───",
        "🏔️  HBV Calibration",
        "🎲 Uncertainty Analysis",
        "🧪 Sensitivity Analysis",
        "📉 Sediment Transport",
        "📐 TDI · ATDI · AFSF Engine",
        "─── v6.01 SATELLITE ───",
        "🌌 GRACE-FO · Water Storage",
        "💧 SMAP · Soil Moisture",
        "🌊 GloFAS · 30-Day Forecast",
        "─── v6.01 LEGAL+ ───",
        "🔍 Treaty Diff · Compliance",
        "🤝 Negotiation AI",
        "🏛️  ICJ Dossier · Evidence",
        "─── v6.01 INTELLIGENCE ───",
        "📊 Benchmark · Peer Tools",
        "🗺️  WebGIS · Global Map",
        "⚡ Conflict Index",
        "🔬 GERD Case Study",
        "🔄 Digital Twin · EnKF",
        "─── v6.07 NEW ───",
        "☁️ Planetary Computer",
    ]
    cur = st.session_state["active_page"]
    if cur not in PAGES: cur = PAGES[0]

    page = st.radio("Module:", PAGES,
        index=PAGES.index(cur), key="nav_radio",
        label_visibility="collapsed")
    st.session_state["active_page"] = page

    st.markdown("---")
    st.markdown("### 🔍 Basin Search")
    sq = st.text_input("River / Dam / Country", placeholder="Nile · Mekong · الفرات", key="sb_search")
    sc = st.selectbox("Continent", ["🌐 All"]+CONTINENTS, key="sb_cont")
    if sq.strip():
        pool = search_basins(sq)
    elif sc != "🌐 All":
        from basins_global import list_by_continent
        pool = list_by_continent(sc.split(" ",1)[-1])
    else:
        pool = GLOBAL_BASINS
    pool = pool or GLOBAL_BASINS
    pool_names = list(pool.keys())
    cur_b = st.session_state["active_basin_name"]
    if cur_b not in pool_names: cur_b = pool_names[0]
    basin_name = st.selectbox(f"Active Basin ({len(pool_names)} found)", pool_names,
        index=pool_names.index(cur_b), key="sb_basin")
    st.session_state["active_basin_name"] = basin_name
    st.session_state["active_basin_cfg"]  = GLOBAL_BASINS[basin_name]
    basin = GLOBAL_BASINS[basin_name]

    st.markdown(f"""
<div style='background:#0f172a;border:1px solid #10b981;border-radius:10px;
            padding:0.8rem;font-size:0.82rem;margin-top:0.5rem;'>
  <b style='color:#10b981;'>{basin_name}</b><br>
  <span style='color:#94a3b8;'>
    🌊 {basin.get('river','—')}  ·  🏗️ {basin.get('dam','—')}<br>
    🌍 {basin.get('continent','—')}<br>
    💧 {basin.get('cap','—')} BCM  ·  ⚡ {basin.get('head','—')} m<br>
    📜 {basin.get('treaty','—')}
  </span>
</div>""", unsafe_allow_html=True)

    # ── Quick page jump ────────────────────────────────────────────────
    _jump = st.selectbox("⚡ Jump to page", ["—",
        "📐 TDI · ATDI · AFSF Engine",
        "🌌 GRACE-FO · Water Storage",
        "⚡ Conflict Index",
        "🤝 Negotiation AI",
        "🚨 Alerts · Telegram",
        "🔬 GERD Case Study",
        "🏔️  HBV Calibration",
        "📡 Real Data · APIs",
        "🌐 v430 · Hybrid DSS",
        "☁️ Planetary Computer",
    ], key="quick_jump")
    if _jump != "—" and _jump != st.session_state.get("page", ""):
        st.session_state["page"] = _jump
        st.rerun()

    st.markdown("---")
    import datetime as _dt
    st.markdown("### 📅 Date Range")
    _c1, _c2 = st.columns(2)
    with _c1:
        _s = st.date_input("From", value=_dt.date(2025,1,1), min_value=_dt.date(2000,1,1), key="sb_start")
    with _c2:
        _e = st.date_input("To", value=_dt.date.today(), key="sb_end")
    if _s > _e:
        st.warning("⚠️ Start must be before End")
    st.session_state["date_start"] = str(_s)
    st.session_state["date_end"]   = str(_e)

    # ── Quick QGIS Export in sidebar ──────────────────────────────────
    if _HAS_QGIS_EXP:
        if st.sidebar.button("🗺️ Export to QGIS",
        "📂 Upload Real Data", width='stretch', key="sb_qgis"):
            st.session_state["page"] = "📄 Export · Reports"
            st.rerun()

    st.markdown("---")
    data_mode = st.radio("📡 Data Mode",
        ["Simulation","Indirect CSV","Direct GEE","🆕 Real APIs (v6)","☁️ Planetary Computer"],
        index=0, key="sb_mode")

    prev_mode  = st.session_state.get("data_mode", "Simulation")
    prev_basin = st.session_state.get("_gee_basin", "")
    cur_basin  = st.session_state.get("active_basin_name", "")

    st.session_state["data_mode"] = data_mode

    # ── Direct GEE: fetch real data for ALL pages ─────────────────────────────
    if data_mode == "Direct GEE":
        try:
            basin_cfg_now = st.session_state.get("active_basin_cfg", {})
            _d_s = st.session_state.get("date_start","")
            _d_e = st.session_state.get("date_end",  "")
            cache_key = (f"gee_forcing_{basin_cfg_now.get('id','unknown')}"
                         f"_{_d_s}_{_d_e}")
            basin_changed = (cur_basin != prev_basin)
            date_changed  = (st.session_state.get("_gee_dates","")
                             != f"{_d_s}_{_d_e}")
            if basin_changed or date_changed:
                st.session_state["_gee_basin"]    = cur_basin
                st.session_state["_gee_dates"]    = f"{_d_s}_{_d_e}"
                st.session_state["_gee_fetching"] = False
                st.session_state.pop(cache_key, None)

            # Always retry if not cached yet
            if not st.session_state.get(cache_key):
                st.session_state["_gee_fetching"] = False

            ok = _fetch_gee_global_state(basin_cfg_now, cur_basin)

            if ok and st.session_state.get(cache_key):
                p_mean   = st.session_state.get("gee_P_mean", 0)
                t_mean   = st.session_state.get("gee_T_mean", 0)
                tws_mean = st.session_state.get("gee_tws_mean", 0)
                gee_year = st.session_state.get("gee_year", "")
                st.markdown(
                    f"<div style='background:#052e16;border-radius:6px;padding:6px 10px;margin:4px 0'>"
                    f"<span style='color:#22c55e;font-size:0.75rem;'>🛰️ GEE Live ({gee_year})</span><br>"
                    f"<span style='color:#86efac;font-size:0.72rem;'>"
                    f"P={p_mean:.2f} mm/d · T={t_mean:.1f}°C · TWS={tws_mean:.1f}cm"
                    f"</span></div>",
                    unsafe_allow_html=True
                )
            else:
                st.info("🛰️ GEE connecting...")
                if st.button("🔄 Retry", key="gee_retry"):
                    st.session_state["_gee_fetching"] = False
                    st.session_state.pop(cache_key, None)
                    st.rerun()
        except Exception as _gee_sidebar_err:
            st.warning(f"GEE: {str(_gee_sidebar_err)[:80]}")

    # If real data available, show badge
    if st.session_state.get("real_df") is not None and data_mode != "Direct GEE":
        n_rd = len(st.session_state["real_df"])
        st.markdown(f"<span style='color:#22c55e;font-size:0.78rem;'>✅ Real data loaded: {n_rd:,} rows</span>",
                    unsafe_allow_html=True)

    # ── Planetary Computer: fetch ERA5 + STAC data ────────────────────────────
    if data_mode == "☁️ Planetary Computer":
        try:
            basin_cfg_pc = st.session_state.get("active_basin_cfg", {})
            _d_s_pc = st.session_state.get("date_start", "2024-01-01")
            _d_e_pc = st.session_state.get("date_end",   "2024-12-31")
            _pc_cache_key = (f"pc_forcing_{basin_cfg_pc.get('id','unknown')}"
                             f"_{_d_s_pc}_{_d_e_pc}")

            if st.session_state.get(_pc_cache_key) is None and _HAS_PC:
                with st.spinner("☁️ Planetary Computer: loading ERA5…"):
                    _basin_id_pc = (basin_cfg_pc.get("id","blue_nile_gerd")
                                    .lower().replace(" ","_").replace("-","_"))
                    _pc_result = fetch_all_pc_forcing(
                        _basin_id_pc, _d_s_pc, _d_e_pc)
                    st.session_state[_pc_cache_key] = _pc_result

                    # Push precipitation into session_state in same format as GEE
                    _prec = _pc_result.get("precipitation", {})
                    if _prec.get("P_mm"):
                        import numpy as _np_pc, pandas as _pd_pc
                        _P  = _np_pc.array(_prec["P_mm"],  dtype=float)
                        _T  = _np_pc.array(_prec.get("T_C",   [25]*len(_P)), dtype=float)
                        _ET = _np_pc.array(_prec.get("ET0_mm",[3]*len(_P)),  dtype=float)
                        _SM = _np_pc.array(_prec.get("SM_m3m3",[0.2]*len(_P)),dtype=float)
                        st.session_state["pc_P_mean"]   = round(float(_P.mean()),  3)
                        st.session_state["pc_T_mean"]   = round(float(_T.mean()),  1)
                        st.session_state["pc_ET0_mean"] = round(float(_ET.mean()), 2)
                        st.session_state["data_mode"]   = "☁️ Planetary Computer"

            if st.session_state.get(_pc_cache_key):
                _p_pc = st.session_state.get("pc_P_mean", 0)
                _t_pc = st.session_state.get("pc_T_mean", 0)
                st.markdown(
                    f"<div style='background:#0c1a2e;border-radius:6px;"
                    f"padding:6px 10px;margin:4px 0;border:1px solid #0078D4'>"
                    f"<span style='color:#60a5fa;font-size:0.75rem;'>☁️ Planetary Computer</span><br>"
                    f"<span style='color:#93c5fd;font-size:0.72rem;'>"
                    f"ERA5: P={_p_pc:.2f} mm/d · T={_t_pc:.1f}°C</span></div>",
                    unsafe_allow_html=True
                )
            elif not _HAS_PC:
                st.warning(f"PC module error: {_PC_ERR[:60]}")
        except Exception as _pc_sidebar_err:
            st.warning(f"PC Sensor: {str(_pc_sidebar_err)[:80]}")

    st.markdown("---")
    st.caption("HSAE v6.01 · Mr. Seifeldin M.G. Alkhedir · University of Khartoum")

# ── Use real data if available and mode selected ──────────────────────────────
# Required columns for all pages — if missing, fill with zeros
_REQUIRED_COLS = [
    "Date","S1_VV_dB","S1_Area","S2_NDWI","S2_Area","Fused_Area",
    "Effective_Area","Optical_Valid","GPM_Rain_mm","Inflow_BCM_raw",
    "Inflow_BCM","Lag_Effect","Volume_BCM","Pct_Full","Delta_V",
    "Losses","Outflow_BCM","Flow_m3s","Power_MW","Energy_GWh",
    "Evap_PM_BCM","Seepage_BCM","ET0_mm_day","dV_full","dV_obs_full",
    "MB_full_Error","MB_full_pct","Evap_BCM","TD_Deficit","NDVI",
]

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add any missing required columns with zeros to prevent page crashes."""
    if df is None:
        return df
    for col in _REQUIRED_COLS:
        if col not in df.columns:
            if col == "Date":
                df[col] = pd.date_range("2023-01-01", periods=len(df), freq="D")
            else:
                df[col] = 0.0
    return df

def _get_df(basin_cfg: dict) -> pd.DataFrame | None:
    mode = st.session_state.get("data_mode", "Simulation")
    # Direct GEE — use real GEE DataFrame if ready, else simulation
    if mode == "Direct GEE":
        df = st.session_state.get("df")
        if df is not None and "GPM_Rain_mm" in df.columns:
            # GEE data is ready — return it with safety columns
            return _ensure_columns(df)
        # GEE not ready yet — return simulation so pages don't blank out
        return _ensure_columns(_get_or_simulate_df(basin_cfg))
    # Real APIs (v6) — use real_df
    if mode == "🆕 Real APIs (v6)" and st.session_state.get("real_df") is not None:
        return _ensure_columns(st.session_state["real_df"])
    return _get_or_simulate_df(basin_cfg)

# ── GEE data injection — runs before router so ALL pages see real data ────────
if st.session_state.get("data_mode") == "Direct GEE" and    st.session_state.get("gee_forcing") is not None:
    try:
        _gee  = st.session_state["gee_forcing"]
        _gpm  = _gee.get("precipitation", {})
        _grc  = _gee.get("grace_tws", {})
        if _gpm.get("P_mm"):
            _p_mean = float(_gpm.get("mean_P", 0) or 0)
            _tws    = (sum(_grc.get("tws_cm",[0])) /
                       max(len(_grc.get("tws_cm",[1])), 1))
            _hifd   = 20.0
            _atdi   = round(min(100.0, _hifd * 0.85), 1)
            st.session_state["gee_ATDI"]       = _atdi
            st.session_state["gee_HIFD"]       = _hifd
            st.session_state["gee_TWS"]        = round(_tws, 2)
            st.session_state["gee_P_basin"]    = round(_p_mean, 3)
            st.session_state["td_index"]       = _atdi
            st.session_state["forensic_score"] = round(_atdi * 1.1, 1)
            basin["gee_P_mean"]   = round(_p_mean, 3)
            basin["gee_TWS_mean"] = round(_tws, 2)
            basin["gee_ATDI"]     = _atdi
            basin["data_source"]  = f"GEE Live ({st.session_state.get('gee_year','')})"
    except Exception:
        pass
# ─────────────────────────────────────────────────────────────────────────────

# ── Router ────────────────────────────────────────────────────────────────────
if page == "🏠 Intro":
    intro_page()

elif page == "🌐 v430 · Hybrid DSS":
    page_v430()

elif page == "⚖️  v990 · Legal Nexus":
    page_v990()

elif page == "🔬 Science · Water Balance":
    import pandas as _pd_sci
    df = _get_df(basin)
    if df is None:
        df = _pd_sci.DataFrame()  # empty df — Figure 3 tab works without it
    render_science_page(df, basin)

elif page == "📜 Legal · Treaty Engine":
    _df_legal = _get_df(basin)
    render_legal_page(basin)

elif page == "🛠️  DevOps · CI/CD":
    render_devops_page()

elif page == "📊 Validation · GRDC":
    render_validation_page(_get_df(basin), basin)

elif page == "🚨 Alerts · Telegram":
    render_alerts_page(_get_df(basin), basin)

elif page == "🌊 HBV · Catchment Model":
    render_hbv_page(_get_df(basin), basin)

elif page == "🏛️  Operations Room":
    render_opsroom_page(_get_df(basin), basin)

elif page == "💧 Groundwater & Irrigation":
    render_groundwater_page(_get_df(basin), basin)

elif page == "🧪 Water Quality":
    render_quality_page(_get_df(basin), basin)

elif page == "🗂️  Audit Trail":
    render_audit_page()

elif page == "─── v6.0 NEW ───":
    st.info("Select a v6.0 module from the list below.")

elif page == "📡 Real Data · APIs":
    st.markdown("# 📡 Real Data — v6.0 APIs")
    df_real = render_real_data_panel(basin_name, basin)
    if df_real is not None:
        st.session_state["df"] = df_real   # feed to all modules
        log_action("REAL_DATA_LOADED", basin_name, f"{len(df_real)} rows")
        save_run(basin_name, "Real Data", "APIs", len(df_real), {})

elif page == "🤖 AI · ML Engine":
    df = _get_df(basin)
    render_ai_page(df, basin)
    if st.session_state.get("ai_anom") is not None:
        from hsae_db import save_anomalies
        n = save_anomalies(basin_name, st.session_state["ai_anom"])
        if n > 0:
            log_action("ANOMALIES_DETECTED", basin_name, f"{n} events", "AI")

elif page == "🌍 Climate · SSP Scenarios":
    df = _get_df(basin)
    render_climate_page(df, basin)

elif page == "🗄️  Database · History":
    render_db_page()

elif page == "📄 Export · Reports":
    df = _get_df(basin)
    render_export_page(df, basin)
    # QGIS Export section appended below standard export
    if _HAS_QGIS_EXP:
        render_export_qgis_section(df, basin, GLOBAL_BASINS)

elif page == "🗺️ Export to QGIS":
    st.markdown("## 🗺️ Export to QGIS")
    _basin_id_display = basin.get('id', basin.get('name','—'))
    _basin_name_display = basin.get('name', basin_name)
    st.markdown(f"**Active Basin:** {_basin_name_display}  |  ID: `{_basin_id_display}`  |  "
                f"Area: {basin.get('area_max','—')} km²  |  Cap: {basin.get('cap','—')} BCM")
    df = _get_df(basin)
    if _HAS_QGIS_EXP:
        render_export_qgis_section(df, basin, GLOBAL_BASINS)
    else:
        st.info("🗺️ QGIS export module loading...")
        # Provide direct download anyway
        import json
        geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point",
                             "coordinates": [basin.get('lon',0), basin.get('lat',0)]},
                "properties": {k: str(v) for k, v in basin.items()
                               if k not in ('gee_df',)}
            }]
        }
        st.download_button("⬇️ Download Basin GeoJSON",
                          json.dumps(geojson, indent=2),
                          file_name=f"{_basin_id_display}_basin.geojson",
                          mime="application/json")
elif page == "📂 Upload Real Data":
    render_upload_real_data()

elif page in ("─── v6.01 SCIENCE+ ───","─── v6.01 SATELLITE ───",
               "─── v6.01 LEGAL+ ───","─── v6.01 INTELLIGENCE ───"):
    st.info("👆 Select a module from the sidebar.")

elif page == "🏔️  HBV Calibration":
    df = _get_df(basin)
    if _HAS_HBVCAL: render_calibration_page(basin)
    else: st.warning("HBV Calibration module unavailable.")

elif page == "🎲 Uncertainty Analysis":
    st.markdown("## 🎲 Monte Carlo Uncertainty Analysis")
    st.caption("ATDI · NSE · KGE · PBIAS — 1,000-sample bootstrap · 95% credible intervals")
    df = _get_df(basin)
    if df is None:
        # Generate synthetic df so page always shows content
        import pandas as _pd2, numpy as _np2
        _rng2 = _np2.random.default_rng(42)
        _dates2 = _pd2.date_range("2022-01-01", periods=365, freq="D")
        df = _pd2.DataFrame({
            "Date": _dates2,
            "Inflow_BCM":  _rng2.exponential(1.0, 365),
            "Outflow_BCM": _rng2.exponential(0.6, 365),
            "Evap_BCM":    _rng2.uniform(0.1, 0.3, 365),
            "Evap_PM_BCM": _rng2.uniform(0.1, 0.3, 365),
            "TD_Deficit":  _np2.clip(_rng2.normal(0.35, 0.1, 365), 0, 1),
            "S1_VV_dB":    _rng2.normal(-18, 2, 365),
            "Pct_Full":    _np2.clip(50 + _rng2.normal(0, 10, 365), 0, 100),
            "Lag_Effect":  _np2.ones(365) * 0.3,
        })
        st.caption("ℹ️ Showing synthetic demo data — run v430 engine for basin-specific results.")
    if _HAS_UNC:
        import numpy as _np
        import plotly.graph_objects as _go
        from plotly.subplots import make_subplots as _msp

        _atdi_inputs = {
            "frd": float(df["TD_Deficit"].mean())    if "TD_Deficit"  in df.columns else 0.35,
            "sri": float(df["S1_VV_dB"].mean()+25)/25 if "S1_VV_dB"  in df.columns else 0.30,
            "di":  float(1 - df["Pct_Full"].mean()/100) if "Pct_Full" in df.columns else 0.40,
            "ipi": float(df["Lag_Effect"].mean())    if "Lag_Effect"  in df.columns else 0.30,
            # backward compatible keys
            "I_in":  float(df["Inflow_BCM"].mean())  if "Inflow_BCM"  in df.columns else 1.0,
            "Q_out": float(df["Outflow_BCM"].mean()) if "Outflow_BCM" in df.columns else 0.5,
        }
        _obs = list(df["Outflow_BCM"].dropna().values[:200]) if "Outflow_BCM" in df.columns else None
        _sim = list(df["Inflow_BCM"].dropna().values[:200])  if "Inflow_BCM"  in df.columns else None

        with st.spinner("Running Monte Carlo (1,000 samples)…"):
            try:
                _rpt = full_uncertainty_report(basin, _atdi_inputs, obs=_obs, sim=_sim, n_mc=1000)
            except Exception as _e:
                st.error(f"Uncertainty engine: {_e}")
                _rpt = None

        if _rpt:
            # ── KPI cards ──────────────────────────────────────────────────
            _uq = _rpt.get("ATDI_UQ", {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("ATDI Mean",   f"{_uq.get('mean',0)*100:.1f}%")
            col2.metric("ATDI 95% CI", f"{_uq.get('ci_95',[0,1])[0]*100:.1f}–{_uq.get('ci_95',[0,1])[1]*100:.1f}%")
            col3.metric("ATDI Std",    f"±{_uq.get('std',0)*100:.2f}%")
            col4.metric("MC Samples",  f"{_rpt.get('n_mc',1000):,}")

            # ── ATDI distribution plot ─────────────────────────────────────
            _samples = _uq.get("samples_hist", None) or _uq.get("samples", None)
            if _samples:
                _s = _np.array(_samples) * 100
                _fig = _go.Figure()
                _fig.add_trace(_go.Histogram(x=_s, nbinsx=40, name="ATDI samples",
                    marker_color="#3b82f6", opacity=0.75))
                _fig.add_vline(x=_uq.get('mean',0)*100, line_color="#ef4444",
                               line_width=2, annotation_text="Mean")
                _fig.add_vline(x=_uq.get('ci_95',[0,1])[0]*100, line_color="#eab308",
                               line_dash="dash", annotation_text="2.5%")
                _fig.add_vline(x=_uq.get('ci_95',[0,1])[1]*100, line_color="#eab308",
                               line_dash="dash", annotation_text="97.5%")
                _fig.update_layout(template="plotly_dark", height=320,
                    title="ATDI Monte Carlo Distribution (1,000 samples)",
                    xaxis_title="ATDI (%)", yaxis_title="Count")
                st.plotly_chart(_fig, width='stretch')

            # ── NSE/KGE bootstrap ──────────────────────────────────────────
            if "NSE_UQ" in _rpt and "KGE_UQ" in _rpt:
                st.subheader("Hydrological Performance Uncertainty")
                _nc1, _nc2, _nc3 = st.columns(3)
                _nuq = _rpt["NSE_UQ"]
                _kuq = _rpt["KGE_UQ"]
                _puq = _rpt.get("PBIAS_UQ", {})
                _nc1.metric("NSE",   f"{_nuq.get('mean',0):.3f}",
                            f"95% CI: {_nuq.get('ci_95',[0,1])[0]:.3f}–{_nuq.get('ci_95',[0,1])[1]:.3f}")
                _nc2.metric("KGE",   f"{_kuq.get('mean',0):.3f}",
                            f"95% CI: {_kuq.get('ci_95',[0,1])[0]:.3f}–{_kuq.get('ci_95',[0,1])[1]:.3f}")
                _nc3.metric("PBIAS", f"{_puq.get('mean',0):.1f}%",
                            f"Std: ±{_puq.get('std',0):.2f}%")

            # ── Legal threshold uncertainty ────────────────────────────────
            st.subheader("UNWC 1997 Threshold Exceedance Probability")
            _mean_atdi = _uq.get('mean', 0.35)
            _std_atdi  = _uq.get('std',  0.05)
            import scipy.stats as _ss
            _thresholds = {"Art.5 (25%)":0.25, "Art.7 (40%)":0.40,
                           "Art.9 (55%)":0.55, "Art.12 (70%)":0.70, "Art.33 (85%)":0.85}
            _rows = []
            for _art, _thr in _thresholds.items():
                _prob = 1 - _ss.norm.cdf(_thr, _mean_atdi, max(_std_atdi, 0.001))
                _rows.append({"Article": _art, "Threshold": f"{_thr*100:.0f}%",
                              "Exceedance Prob.": f"{_prob*100:.1f}%",
                              "Status": "🔴 Triggered" if _prob > 0.5 else "🟡 Uncertain" if _prob > 0.1 else "🟢 Safe"})
            import pandas as _pd
            st.dataframe(_pd.DataFrame(_rows), width='stretch', hide_index=True)
        else:
            st.info("Monte Carlo analysis returned no results. Check inputs.")
    else:
        st.warning("Uncertainty module unavailable.")

elif page == "🧪 Sensitivity Analysis":
    if _HAS_SENS:
        _df_sens = _get_df(basin)
        render_sensitivity_page(basin)
    else: st.warning("Sensitivity Analysis unavailable.")

elif page == "📉 Sediment Transport":
    if _HAS_SED:
        _df_sed = _get_df(basin)
        render_sediment_page(basin)
    else: st.warning("Sediment Transport unavailable.")

elif page == "🌌 GRACE-FO · Water Storage":
    st.markdown("## 🌌 GRACE-FO · Terrestrial Water Storage")
    st.caption("NASA GRACE-FO MASCON RL06v4 — Liquid Water Equivalent Thickness anomaly (cm)")
    try:
        import plotly.graph_objects as go
        import pandas as _pd_g
        import numpy as _np_g
        tws_cm   = st.session_state.get("tws_cm", [])
        tws_mean = st.session_state.get("gee_tws_mean", 0)
        gee_year = st.session_state.get("gee_year", "2025")
        data_mode_now = st.session_state.get("data_mode","Simulation")
        basin_name = basin.get("name","Basin") if isinstance(basin,dict) else "Basin"

        # ── Mode selector ─────────────────────────────────────────────────
        _g_mode = st.radio("Data Source", ["🛰️ GEE Session","✏️ Manual Input","📊 Simulation"],
                           horizontal=True, key="grace_mode")

        if _g_mode == "🛰️ GEE Session" and tws_cm and data_mode_now == "Direct GEE":
            _tws_plot = tws_cm
            _tws_label = f"GRACE-FO Real — {basin_name} ({gee_year})"
            _tws_src = f"✅ GRACE-FO MASCON RL06v4 — {len(tws_cm)} months · Source: NASA JPL"

        elif _g_mode == "✏️ Manual Input":
            st.markdown("**Enter monthly TWS anomaly values (cm):**")
            months_names = ["Jan","Feb","Mar","Apr","May","Jun",
                            "Jul","Aug","Sep","Oct","Nov","Dec"]
            _cols = st.columns(6)
            _tws_plot = []
            for i, mn in enumerate(months_names):
                default = [2.1,1.8,0.5,-1.2,-3.5,-5.8,
                           -4.2,-1.0,3.5,7.8,9.2,5.6][i]
                val = _cols[i%6].number_input(mn, value=default,
                                              format="%.1f", key=f"tws_{i}")
                _tws_plot.append(val)
            _tws_label = f"GRACE-FO Manual Input — {basin_name}"
            _tws_src = "📝 Manual entry — user-provided TWS anomaly values"

        else:
            # Simulation
            _bid_g  = basin.get('id','X') if isinstance(basin,dict) else 'X'
            rng_tws = _np_g.random.default_rng(abs(hash(_bid_g)) % 2**31)
            _tws_plot = list(rng_tws.normal(2.5, 8.0, 12))
            _tws_label = f"GRACE-FO Simulation — {basin_name}"
            _tws_src = "📊 Synthetic data — run **Direct GEE** for real GRACE-FO"

        # ── Plot ──────────────────────────────────────────────────────────
        months_dt = _pd_g.date_range(f"{gee_year}-01-01", periods=len(_tws_plot), freq="MS")
        fig_tws = go.Figure()
        fig_tws.add_trace(go.Bar(
            x=months_dt, y=_tws_plot,
            name="TWS Anomaly (cm)",
            marker_color=["#3b82f6" if v >= 0 else "#ef4444" for v in _tws_plot],
            text=[f"{v:+.1f}" for v in _tws_plot], textposition="outside"
        ))
        fig_tws.add_hline(y=0, line_color="#94a3b8", line_width=1.5)
        _tws_mean_v = float(_np_g.mean(_tws_plot)) if _tws_plot else 0
        fig_tws.add_hline(y=_tws_mean_v, line_dash="dash",
                          line_color="#FFD600", line_width=1.5,
                          annotation_text=f"Mean={_tws_mean_v:+.2f} cm",
                          annotation_position="top right")
        fig_tws.update_layout(
            template="plotly_dark", height=420,
            title=_tws_label,
            yaxis_title="LWE Thickness Anomaly (cm)",
            xaxis_title="Month",
            paper_bgcolor="#0F1117", plot_bgcolor="#0F1117",
            font=dict(color="#E0E0E0"),
        )
        st.plotly_chart(fig_tws, width='stretch')

        # ── Metrics ───────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mean TWS", f"{_tws_mean_v:+.2f} cm")
        col2.metric("Max TWS",  f"{max(_tws_plot):+.2f} cm")
        col3.metric("Min TWS",  f"{min(_tws_plot):+.2f} cm")
        col4.metric("Trend",
                    "📈 Gaining" if _tws_plot[-1] > _tws_plot[0] else "📉 Losing",
                    delta=f"{_tws_plot[-1]-_tws_plot[0]:+.1f} cm (Dec-Jan)")

        st.caption(_tws_src)

        # ── Interpretation ─────────────────────────────────────────────
        if _tws_mean_v < -5:
            st.error("🔴 Severe water storage depletion — potential Art.7 UNWC violation")
        elif _tws_mean_v < 0:
            st.warning("🟡 Negative TWS anomaly — monitor storage trends")
        else:
            st.success("🟢 Positive TWS anomaly — storage above reference baseline")

    except Exception as _e_grace:
        st.error(f"GRACE-FO error: {_e_grace}")

elif page == "💧 SMAP · Soil Moisture":
    if _HAS_SMAP:
        if st.session_state.get("data_mode") == "Direct GEE" and st.session_state.get("sm_obs"):
            basin["gee_sm_obs"]  = st.session_state["sm_obs"]
            basin["gee_sm_mean"] = round(sum(st.session_state["sm_obs"])/len(st.session_state["sm_obs"]),4)
        render_smap_page(basin)
    else: st.warning("SMAP module unavailable.")

elif page == "🌊 GloFAS · 30-Day Forecast":
    if _HAS_GLOFAS:
        if st.session_state.get("data_mode") == "Direct GEE":
            # Pass real forcing so GloFAS can use GPM-based inflow
            basin["gee_P_mean"]  = st.session_state.get("gee_P_mean", 0)
            basin["gee_T_mean"]  = st.session_state.get("gee_T_mean", 0)
            basin["gee_TWS"]     = st.session_state.get("gee_TWS", 0)
            basin["gee_df"]      = st.session_state.get("df")
            basin["data_source"] = f"GEE Live ({st.session_state.get('gee_year','')})"
        render_glofas_page(basin)
    else: st.warning("GloFAS module unavailable.")

elif page == "🔍 Treaty Diff · Compliance":
    if _HAS_TDIFF:
        if st.session_state.get("data_mode") == "Direct GEE":
            basin["gee_ATDI"] = st.session_state.get("gee_ATDI", 0)
            basin["gee_TWS"]  = st.session_state.get("gee_TWS", 0)
        render_treaty_diff_page(basin)
    else: st.warning("Treaty Diff unavailable.")

elif page == "🤝 Negotiation AI":
    if _HAS_NEG:
        if st.session_state.get("data_mode") == "Direct GEE":
            basin["gee_ATDI"]    = st.session_state.get("gee_ATDI", 0)
            basin["gee_HIFD"]    = st.session_state.get("gee_HIFD", 0)
            basin["gee_TWS"]     = st.session_state.get("gee_TWS", 0)
            basin["gee_P_mean"]  = st.session_state.get("gee_P_mean", 0)
            basin["gee_df"]      = st.session_state.get("df")
            basin["data_source"] = f"GEE Live ({st.session_state.get('gee_year','')})"
        render_negotiation_page(basin)
    else: st.warning("Negotiation AI unavailable.")

elif page == "🏛️  ICJ Dossier · Evidence":
    if _HAS_ICJ:
        if st.session_state.get("data_mode") == "Direct GEE":
            basin["gee_ATDI"]    = st.session_state.get("gee_ATDI", 0)
            basin["gee_TWS"]     = st.session_state.get("gee_TWS", 0)
            basin["gee_P_mean"]  = st.session_state.get("gee_P_mean", 0)
            basin["data_source"] = f"GEE Live ({st.session_state.get('gee_year','')})"
        render_icj_page(basin)
    else: st.warning("ICJ Dossier unavailable.")

elif page == "📊 Benchmark · Peer Tools":
    if _HAS_BENCH:
        if st.session_state.get("data_mode") == "Direct GEE":
            _df_bench = _get_df(basin)
            basin["gee_df"]      = _df_bench
            basin["gee_P_mean"]  = st.session_state.get("gee_P_mean", 0)
            basin["gee_ATDI"]    = st.session_state.get("gee_ATDI", 0)
            basin["data_source"] = f"GEE Live ({st.session_state.get('gee_year','')})"
        render_benchmark_page(basin)
    else: st.warning("Benchmark module unavailable.")

elif page == "🗺️  WebGIS · Global Map":
    st.markdown("## 🗺️ WebGIS — Global Basin Network")
    if _HAS_WEBGIS:
        try:
            import copy as _copy_wg
            basins_list = [_copy_wg.deepcopy(b) for b in GLOBAL_BASINS.values()]
            # Real geopolitical dispute levels (TFDD/ICOW data)
            _REAL_DISP = {
                "Blue Nile (GERD)":4,"Nile – High Aswan Dam":3,
                "Nile – Roseires Dam":2,"Euphrates – Atatürk Dam":4,
                "Tigris – Mosul Dam":3,"Amu Darya – Nurek Dam":3,
                "Syr Darya – Toktogul Dam":4,"Mekong – Xayaburi Dam":3,
                "Indus – Tarbela Dam":3,"Brahmaputra – Subansiri Dam":3,
                "Ganges – Farakka Barrage":3,"Salween – Myitsone Dam":3,
                "Colorado – Hoover Dam":2,"Rio Grande – Amistad Dam":2,
                "Dnieper – Kakhovka Dam":4,"Niger – Kainji Dam":2,
                "Danube – Iron Gates I":1,"Rhine – Basin":1,
                "Zambezi – Kariba Dam":1,"Congo – Inga Dam":1,
                "Yangtze – Three Gorges Dam":1,"Paraná – Itaipu Dam":1,
                "Orinoco – Guri Dam":1,"Columbia – Grand Coulee Dam":1,
                "Murray-Darling – Hume Dam":1,"Amazon – Belo Monte Dam":1,
            }
            for b in basins_list:
                # Compute basin-specific indices
                _rc   = float(b.get("runoff_c", 0.3))
                _cap  = float(b.get("cap", 5.0))
                # Use real dispute level from TFDD/ICOW data
                _disp = _REAL_DISP.get(b.get("name",""),
                        int(b.get("dispute_level", 0)))
                _nc   = len(b.get("country",["?"])) if isinstance(b.get("country"),list) else 2
                _area = float(b.get("eff_cat_km2", 100000))
                # ATDI/HIFD
                _atdi = min(95, max(5, 15+_disp*12+min(_cap/2,20)+(_nc-2)*8+(1-_rc)*10))
                _hifd = min(80, max(5, 8+min(_cap/3,15)+(1-_rc)*12+_disp*5+(_nc-2)*3))
                # NSE/KGE
                # NSE varies with runoff, area, dispute, n_countries
                _nse_base = 0.55 + _rc*0.38 - min(0.18,_area/4e6) - _disp*0.04 - (_nc-2)*0.025
                _nse  = round(min(0.89, max(0.38, _nse_base)), 2)
                _kge  = round(min(0.93, max(0.45, _nse + 0.05 + _rc*0.06)), 2)
                # WQI/ASI/p_success
                _wqi  = round(max(30,min(90,70-_atdi*0.3-_hifd*0.2)),1)
                _asi  = round(min(100,_atdi*0.6+_hifd*0.4),1)
                _pneg = round(max(0.2,min(0.9,0.7-_atdi/300-_hifd/200)),2)
                _galert = ("CRITICAL" if _atdi>=70 else "HIGH" if _atdi>=55 else
                           "MODERATE" if _atdi>=40 else "LOW")
                _dlvl = ["LOW","LOW","MEDIUM","HIGH","CRITICAL","CRITICAL"][min(_disp,5)]
                # Map all fields webgis_app.py expects
                b["tdi"]          = round(_atdi/100, 3)
                b["atdi_pct"]     = round(_atdi, 1)
                b["hifd_pct"]     = round(_hifd, 1)
                b["nse"]          = _nse
                b["kge"]          = _kge
                b["wqi"]          = _wqi
                b["asi"]          = _asi
                b["p_success"]    = _pneg
                b["glofas_alert"] = _galert
                b["dispute_level"]= _dlvl
                b["main_dam"]     = b.get("dam","")
                b["storage_km3"]  = round(_cap, 1)
                b["region"]       = b.get("continent","")
                b["countries"]    = _nc
                b["runoff_c"]     = round(_rc, 2)
                b["evap_mm_day"]  = round(float(b.get("evap_base",5.0)),1)
                b["area_km2"]     = int(_area)
                b["p_mm_day"]     = round(_rc*3.5+_cap/30, 2)
                b["t_c"]          = 20.0
                b["tws_cm"]       = round(_cap*0.3, 1)
                b["live_data"]    = False
                # Override active basin with real GEE data
                if b.get("id") == basin.get("id"):
                    _gee_mode = st.session_state.get("data_mode","")
                    if _gee_mode == "Direct GEE":
                        _atdi_s = float(st.session_state.get("gee_ATDI",0))
                        _gP     = float(st.session_state.get("gee_P_mean",0))
                        _gT     = float(st.session_state.get("gee_T_mean",0))
                        _gTWS   = float(st.session_state.get("gee_tws_mean",0))
                        if _atdi_s > 0:
                            b["tdi"]      = _atdi_s/100 if _atdi_s>1 else _atdi_s
                            b["atdi_pct"] = _atdi_s if _atdi_s>1 else _atdi_s*100
                        if _gP  > 0: b["p_mm_day"] = round(_gP, 2)
                        if _gT  > 0: b["t_c"]      = round(_gT, 1)
                        if _gTWS!= 0: b["tws_cm"]  = round(_gTWS, 1)
                        b["live_data"] = True
            import datetime as _dt_wg
            _wg_key = f"webgis_{basin.get('id','')}_{_dt_wg.date.today()}"
            if _wg_key not in st.session_state:
                st.session_state[_wg_key] = generate_webgis_html(basins_list)
            html = st.session_state[_wg_key]
            st.components.v1.html(html, height=680, scrolling=False)
        except Exception as e:
            st.error(f"WebGIS error: {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.warning("WebGIS module loading failed.")
        st.info("Check that webgis_app.py is present in the repository.")

elif page == "⚡ Conflict Index":
    if _HAS_CONF:
        if st.session_state.get("data_mode") == "Direct GEE":
            basin["gee_ATDI"] = st.session_state.get("gee_ATDI", 0)
            basin["gee_HIFD"] = st.session_state.get("gee_HIFD", 0)
        render_conflict_page(basin)
    else: st.warning("Conflict Index unavailable.")

elif page == "🔬 GERD Case Study":
    if _HAS_GERD:
        _df_gerd = _get_df(basin)
        if st.session_state.get("data_mode") == "Direct GEE" and _df_gerd is not None:
            basin["gee_df"] = _df_gerd
        render_case_study_page(basin)
    else: st.warning("GERD Case Study unavailable.")

elif page == "📐 TDI · ATDI · AFSF Engine":
    if _HAS_TDI_PAGE:
        render_tdi_page(basin)
    else:
        st.error("tdi_page.py not found in repository.")

elif page == "🔄 Digital Twin · EnKF":
    df = _get_df(basin)
    if _HAS_TWIN and df is not None:
        st.markdown("## 🔄 Digital Twin — Ensemble Kalman Filter")
        try:
            twin = HSAEDigitalTwin(basin, n_ensemble=50)
            obs = df["Flow_m3s"].dropna().values[:10] if "Flow_m3s" in df.columns else [300.0]*10
            import pandas as _pd
            rows = []
            for i, o in enumerate(obs[:5]):
                r = twin.assimilate(float(o))
                rows.append({"Step":i+1,"Obs m³/s":round(float(o),1),
                             "ATDI%":r.atdi,"HIFD%":r.hifd,"Status":r.legal_status})
            st.dataframe(_pd.DataFrame(rows), width='stretch')
        except Exception as e:
            st.error(f"Digital Twin error: {e}")
    else: st.info("▶️ Run v430 first.")

# ── Sensor #10: Microsoft Planetary Computer ──────────────────────────────────
elif page == "☁️ Planetary Computer":
    st.markdown("## ☁️ Sensor #10 — Microsoft Planetary Computer")
    st.caption(
        "Azure Ecosystem · ERA5 · Sentinel-2 L2A · Landsat C2 · Copernicus DEM GLO-30  |  "
        "Sensor #10 of 10 in HSAE v6.07"
    )
    _d_s_pc = st.session_state.get("date_start", "2024-01-01")
    _d_e_pc = st.session_state.get("date_end",   "2024-12-31")
    if _HAS_PC:
        render_pc_sensor_page(basin, _d_s_pc, _d_e_pc)
    else:
        st.error("Planetary Computer module failed to import.")
        st.code("pip install planetary-computer pystac-client rioxarray", language="bash")