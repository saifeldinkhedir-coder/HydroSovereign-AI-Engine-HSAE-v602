"""
fetchers.py — HSAE v6.3.0 Live Data Ingestion Module
======================================================
Connects to real external APIs to fetch hydrological data:
  - Open-Meteo (free, no key) — precipitation, temperature, ET
  - GRDC (Global Runoff Data Centre) — observed discharge
  - NASA POWER (free) — solar radiation, humidity
  - GEE/Copernicus (requires auth) — satellite products

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
import logging
import json
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Union
from pathlib import Path

logger = logging.getLogger(__name__)


def fetch_openmeteo(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    variables: Optional[List[str]] = None,
    timeout: int = 30,
) -> Dict:
    """
    Fetch daily climate data from Open-Meteo ERA5 API (free, no API key).

    Parameters
    ----------
    lat, lon : float
        Basin centroid coordinates.
    start_date : str
        Start date "YYYY-MM-DD".
    end_date : str
        End date "YYYY-MM-DD".
    variables : list, optional
        Variables to fetch. Default:
        ["precipitation_sum","temperature_2m_mean",
         "et0_fao_evapotranspiration","soil_moisture_0_to_7cm_mean"]
    timeout : int
        Request timeout seconds. Default = 30.

    Returns
    -------
    dict
        - dates       : list of date strings
        - P_mm_day    : daily precipitation (mm/day)
        - T_celsius   : daily mean temperature (°C)
        - ET0         : FAO-56 reference ET (mm/day)
        - soil_moisture: volumetric soil moisture (m³/m³)
        - source      : "Open-Meteo ERA5"
        - lat, lon    : coordinates used
        - n_days      : number of days

    Raises
    ------
    ConnectionError
        If the API is unreachable.

    Examples
    --------
    >>> data = fetch_openmeteo(10.53, 35.09, "2024-01-01", "2024-12-31")
    >>> print(f"Mean P = {sum(data['P_mm_day'])/len(data['P_mm_day']):.2f} mm/day")
    """
    try:
        import urllib.request
        import urllib.parse
    except ImportError:
        raise ImportError("urllib is required (standard library)")

    if variables is None:
        variables = [
            "precipitation_sum",
            "temperature_2m_mean",
            "et0_fao_evapotranspiration",
            "soil_moisture_0_to_7cm_mean",
        ]

    params = {
        "latitude":    str(lat),
        "longitude":   str(lon),
        "start_date":  start_date,
        "end_date":    end_date,
        "daily":       ",".join(variables),
        "timezone":    "UTC",
    }

    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(params)
    logger.info("Fetching Open-Meteo: lat=%.2f lon=%.2f %s→%s", lat, lon, start_date, end_date)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "hydrosovereign/6.3.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except Exception as e:
        raise ConnectionError(f"Open-Meteo API request failed: {e}")

    daily   = data.get("daily", {})
    dates   = daily.get("time", [])
    n       = len(dates)

    result = {
        "dates":         dates,
        "P_mm_day":      daily.get("precipitation_sum", [0.0]*n),
        "T_celsius":     daily.get("temperature_2m_mean", [25.0]*n),
        "ET0":           daily.get("et0_fao_evapotranspiration", [None]*n),
        "soil_moisture": daily.get("soil_moisture_0_to_7cm_mean", [None]*n),
        "source":        "Open-Meteo ERA5 (open-meteo.com)",
        "lat":           lat,
        "lon":           lon,
        "n_days":        n,
        "start_date":    start_date,
        "end_date":      end_date,
    }

    logger.info("Open-Meteo: %d days fetched, P_mean=%.2f mm/day",
                n, sum(p or 0 for p in result["P_mm_day"]) / max(1, n))
    return result


def fetch_openmeteo_forecast(
    lat: float,
    lon: float,
    horizon_days: int = 7,
    timeout: int = 20,
) -> Dict:
    """
    Fetch weather forecast from Open-Meteo (free, no key).

    Parameters
    ----------
    lat, lon : float
        Coordinates.
    horizon_days : int
        Forecast horizon (max 16 days). Default = 7.
    timeout : int
        Request timeout. Default = 20.

    Returns
    -------
    dict
        - dates, P_mm_day, T_celsius, ET0
        - source: "Open-Meteo Forecast"

    Examples
    --------
    >>> fc = fetch_openmeteo_forecast(10.53, 35.09, horizon_days=7)
    >>> print(fc["P_mm_day"])   # next 7 days precipitation
    """
    import urllib.request, urllib.parse

    params = {
        "latitude":  str(lat),
        "longitude": str(lon),
        "daily":     "precipitation_sum,temperature_2m_mean,et0_fao_evapotranspiration",
        "timezone":  "UTC",
        "forecast_days": str(min(horizon_days, 16)),
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = json.loads(r.read())
    except Exception as e:
        raise ConnectionError(f"Open-Meteo Forecast API failed: {e}")

    daily = data.get("daily", {})
    return {
        "dates":     daily.get("time", []),
        "P_mm_day":  daily.get("precipitation_sum", []),
        "T_celsius": daily.get("temperature_2m_mean", []),
        "ET0":       daily.get("et0_fao_evapotranspiration", []),
        "source":    "Open-Meteo Forecast (open-meteo.com)",
        "lat": lat, "lon": lon,
    }


def fetch_basin_forcing(
    basin_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    years: int = 5,
) -> Dict:
    """
    Fetch precipitation and temperature for a named basin (from registry).

    Uses basin centroid coordinates from BasinRegistry.
    Data source: Open-Meteo ERA5 (free, no authentication).

    Parameters
    ----------
    basin_name : str
        Basin name from BASINS_26 registry.
    start_date : str, optional
        "YYYY-MM-DD". If None, uses `years` before today.
    end_date : str, optional
        "YYYY-MM-DD". If None, uses yesterday.
    years : int
        Years of data if dates not specified. Default = 5.

    Returns
    -------
    dict
        - basin_name, lat, lon
        - P, T : numpy arrays ready for HBVModel.simulate()
        - source, n_days, dates

    Examples
    --------
    >>> import numpy as np
    >>> from hydrosovereign.models import HBVModel
    >>> data = fetch_basin_forcing("Blue Nile (GERD)", years=3)
    >>> P, T = np.array(data["P"]), np.array(data["T"])
    >>> model = HBVModel(area_km2=174000, runoff_c=0.38)
    >>> result = model.simulate(P, T)
    >>> print(f"NSE = {result['nse']}")
    """
    import numpy as np
    from ..basins import BasinRegistry

    reg   = BasinRegistry()
    basin = reg.get(basin_name)
    lat   = float(basin["lat"])
    lon   = float(basin["lon"])

    if end_date is None:
        end_date = (date.today() - timedelta(days=1)).isoformat()
    if start_date is None:
        start_date = (date.today() - timedelta(days=years*365)).isoformat()

    logger.info("Fetching forcing for %s (%s → %s)", basin_name, start_date, end_date)

    try:
        raw = fetch_openmeteo(lat, lon, start_date, end_date)
        P   = [max(0.0, float(p or 0)) for p in raw["P_mm_day"]]
        T   = [float(t or 25.0)        for t in raw["T_celsius"]]

        # Extract all features for multi-feature LSTM
        SM_raw  = raw.get("soil_moisture", [None]*len(P))
        ET0_raw = raw.get("ET0", [None]*len(P))
        SM  = [float(v) if v is not None else None for v in SM_raw]
        ET0 = [float(v) if v is not None else None for v in ET0_raw]

        return {
            "basin_name":  basin_name,
            "lat":         lat,
            "lon":         lon,
            "start_date":  start_date,
            "end_date":    end_date,
            # Core features
            "P":           P,       # precipitation (mm/day)
            "T":           T,       # temperature (°C)
            "ET0":         ET0,     # evapotranspiration (mm/day)
            "SM":          SM,      # soil moisture (m³/m³)
            # Metadata
            "dates":       raw["dates"],
            "n_days":      len(P),
            "source":      raw["source"],
            "runoff_c":    float(basin.get("runoff_c", 0.3)),
            "cap_bcm":     float(basin.get("cap", 10)),
            "ready_for_lstm": True,  # can pass directly to LSTMForecast.fit_multi()
        }
    except ConnectionError as e:
        logger.warning("Live data unavailable (%s) — loading sample data", e)
        return _load_sample_data(basin_name)


def _load_sample_data(basin_name: str) -> Dict:
    """Fallback: load bundled sample dataset."""
    import numpy as np
    sample_path = Path(__file__).parent / "nile_basin_sample.json"

    if sample_path.exists() and "Nile" in basin_name:
        with open(sample_path) as f:
            raw = json.load(f)
        records = raw["records"]
        return {
            "basin_name": basin_name,
            "lat":        raw["lat"],
            "lon":        raw["lon"],
            "P":          [r["P"] for r in records],
            "T":          [r["T"] for r in records],
            "ET0":        [r.get("ET0") for r in records],
            "SM":         [r.get("SM") for r in records],
            "dates":      [r["date"] for r in records],
            "n_days":     len(records),
            "source":     "HSAE bundled sample (Open-Meteo offline)",
            "runoff_c":   raw.get("runoff_c", 0.38),
            "cap_bcm":    raw.get("cap_bcm", 74.0),
            "ready_for_lstm": True,
        }

    # Generic fallback: synthetic seasonal data
    logger.warning("No sample data for %s — using synthetic seasonal proxy", basin_name)
    n   = 365 * 3
    doy = np.tile(np.arange(1, 366), 3)[:n]
    P   = list(np.maximum(0, 2.0 * np.sin(np.pi * doy / 180) ** 1.3
                          + np.random.default_rng(42).exponential(0.3, n)))
    T   = list(25 + 5 * np.sin(2 * np.pi * doy / 365))
    return {
        "basin_name": basin_name,
        "P": P, "T": T, "n_days": n,
        "source": "HSAE synthetic seasonal proxy",
        "runoff_c": 0.3, "cap_bcm": 10.0,
    }


def fetch_gee_basin(
    lat: float,
    lon: float,
    bbox: List[float],
    start_date: str,
    end_date: str,
    sensors: Optional[List[str]] = None,
    project_id: str = "zinc-arc-484714-j8",
) -> Dict:
    """
    Fetch satellite data from Google Earth Engine (requires earthengine-api).

    Install: pip install hydrosovereign[gee]
    Auth:    earthengine authenticate

    Sensors available:
      - "gpm"      : GPM IMERG V07 precipitation (11 km, daily)
      - "grace"    : GRACE-FO MASCON TWS anomaly (300 km, monthly)
      - "smap"     : SMAP 10km soil moisture
      - "sentinel1": Sentinel-1 SAR flood extent (10 m)
      - "sentinel2": Sentinel-2 NDWI water mask (10 m)
      - "era5"     : ERA5 temperature (25 km, monthly)

    Parameters
    ----------
    lat, lon : float
        Basin centroid.
    bbox : list
        [lon_min, lat_min, lon_max, lat_max].
    start_date : str
        "YYYY-MM-DD".
    end_date : str
        "YYYY-MM-DD".
    sensors : list, optional
        Subset of sensors. Default = ["gpm", "grace", "smap"].
    project_id : str
        GEE project ID. Default = "zinc-arc-484714-j8".

    Returns
    -------
    dict
        One key per sensor with retrieved values.

    Raises
    ------
    ImportError
        If earthengine-api not installed.
    RuntimeError
        If GEE authentication fails.

    Examples
    --------
    >>> data = fetch_gee_basin(
    ...     lat=10.53, lon=35.09,
    ...     bbox=[33.0, 8.0, 37.5, 13.0],
    ...     start_date="2024-01-01", end_date="2024-12-31",
    ...     sensors=["gpm", "grace"],
    ... )
    >>> print(f"Mean P = {data['gpm']['mean_P_mm_day']:.2f} mm/day")
    >>> print(f"TWS    = {data['grace']['mean_tws_cm']:.1f} cm")
    """
    try:
        import ee
    except ImportError:
        raise ImportError(
            "earthengine-api is required for GEE data.\n"
            "Install: pip install hydrosovereign[gee]\n"
            "Authenticate: earthengine authenticate"
        )

    # Initialize GEE
    try:
        ee.Initialize(project=project_id)
    except Exception:
        try:
            ee.Initialize()
        except Exception as e:
            raise RuntimeError(
                f"GEE authentication failed: {e}\n"
                "Run: earthengine authenticate"
            )

    if sensors is None:
        sensors = ["gpm", "grace", "smap"]

    region = ee.Geometry.Rectangle(bbox)
    result = {}

    # GPM IMERG V07 precipitation
    if "gpm" in sensors:
        try:
            gpm = (ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
                   .filterDate(start_date, end_date)
                   .filterBounds(region)
                   .select("precipitation"))
            mean_p = gpm.mean().reduceRegion(
                ee.Reducer.mean(), region, 11132).getInfo()
            result["gpm"] = {
                "mean_P_mm_day": float(list(mean_p.values())[0] or 0),
                "source": "GPM IMERG V07 (NASA)",
                "resolution_km": 11,
            }
            logger.info("GEE GPM: mean_P=%.2f mm/day", result["gpm"]["mean_P_mm_day"])
        except Exception as e:
            logger.warning("GPM fetch failed: %s", e)
            result["gpm"] = {"error": str(e)}

    # GRACE-FO MASCON TWS
    if "grace" in sensors:
        try:
            grace = (ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/LAND")
                     .filterDate(start_date, end_date)
                     .select("lwe_thickness_csr"))
            mean_tws = grace.mean().reduceRegion(
                ee.Reducer.mean(), region, 300000).getInfo()
            result["grace"] = {
                "mean_tws_cm": float(list(mean_tws.values())[0] or 0),
                "source": "GRACE-FO MASCON RL06v4 (NASA)",
                "resolution_km": 300,
            }
            logger.info("GEE GRACE-FO: mean_TWS=%.1f cm", result["grace"]["mean_tws_cm"])
        except Exception as e:
            logger.warning("GRACE fetch failed: %s", e)
            result["grace"] = {"error": str(e)}

    # SMAP soil moisture
    if "smap" in sensors:
        try:
            smap = (ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture")
                    .filterDate(start_date, end_date)
                    .select("ssm"))
            mean_sm = smap.mean().reduceRegion(
                ee.Reducer.mean(), region, 10000).getInfo()
            result["smap"] = {
                "mean_sm_m3m3": float(list(mean_sm.values())[0] or 0),
                "source": "SMAP 10km (NASA)",
                "resolution_km": 10,
            }
            logger.info("GEE SMAP: mean_SM=%.3f m³/m³", result["smap"]["mean_sm_m3m3"])
        except Exception as e:
            logger.warning("SMAP fetch failed: %s", e)
            result["smap"] = {"error": str(e)}

    # Sentinel-1 SAR flood extent
    if "sentinel1" in sensors:
        try:
            s1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
                  .filterDate(start_date, end_date)
                  .filterBounds(region)
                  .filter(ee.Filter.eq("instrumentMode","IW"))
                  .select("VV"))
            flood_area = s1.mean().lt(-15).reduceRegion(
                ee.Reducer.mean(), region, 100).getInfo()
            result["sentinel1"] = {
                "flood_fraction": float(list(flood_area.values())[0] or 0),
                "source": "Sentinel-1 SAR IW (Copernicus)",
                "resolution_m": 10,
            }
        except Exception as e:
            logger.warning("Sentinel-1 fetch failed: %s", e)
            result["sentinel1"] = {"error": str(e)}

    # ERA5 temperature
    if "era5" in sensors:
        try:
            era5 = (ee.ImageCollection("ECMWF/ERA5/MONTHLY")
                    .filterDate(start_date, end_date)
                    .select("mean_2m_air_temperature"))
            mean_t = era5.mean().subtract(273.15).reduceRegion(
                ee.Reducer.mean(), region, 25000).getInfo()
            result["era5"] = {
                "mean_T_celsius": float(list(mean_t.values())[0] or 25.0),
                "source": "ERA5 Monthly (ECMWF via GEE)",
                "resolution_km": 25,
            }
        except Exception as e:
            logger.warning("ERA5 fetch failed: %s", e)
            result["era5"] = {"error": str(e)}

    result["metadata"] = {
        "lat": lat, "lon": lon, "bbox": bbox,
        "start_date": start_date, "end_date": end_date,
        "sensors_requested": sensors,
        "gee_project": project_id,
        "source": "Google Earth Engine",
    }
    return result


def fetch_sentinel2_wqi(
    bbox: List[float],
    start_date: str,
    end_date: str,
    project_id: str = "zinc-arc-484714-j8",
) -> Dict:
    """
    Estimate Water Quality Index using Sentinel-2 spectral indices (GEE).

    Computes remote-sensing WQI proxies:
      - NDWI (B3-B8)/(B3+B8)     : water presence
      - NDTI (B4-B3)/(B4+B3)     : turbidity proxy
      - Chlorophyll-a proxy (B5/B4): trophic state

    Parameters
    ----------
    bbox : list
        [lon_min, lat_min, lon_max, lat_max].
    start_date, end_date : str
        Date range "YYYY-MM-DD".
    project_id : str
        GEE project ID.

    Returns
    -------
    dict
        - ndwi_mean      : water extent index (-1 to 1)
        - ndti_mean      : turbidity proxy (-1 to 1, higher=more turbid)
        - chl_proxy      : chlorophyll proxy (higher=more algae)
        - rs_wqi_score   : remote-sensing WQI estimate (0-100)
        - water_fraction : fraction of basin covered by water

    Raises
    ------
    ImportError
        If earthengine-api not installed.

    Examples
    --------
    >>> wq = fetch_sentinel2_wqi([33,8,37.5,13], "2024-01-01", "2024-12-31")
    >>> print(f"RS-WQI = {wq['rs_wqi_score']:.1f}")
    >>> print(f"Turbidity proxy: {wq['ndti_mean']:.3f}")
    """
    try:
        import ee
    except ImportError:
        raise ImportError("earthengine-api required: pip install hydrosovereign[gee]")

    try:
        ee.Initialize(project=project_id)
    except Exception:
        try:
            ee.Initialize()
        except Exception as e:
            raise RuntimeError(f"GEE authentication failed: {e}")

    region = ee.Geometry.Rectangle(bbox)

    try:
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterDate(start_date, end_date)
              .filterBounds(region)
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

        # NDWI: (B3-B8)/(B3+B8) — positive = water
        ndwi_img  = s2.mean().normalizedDifference(["B3","B8"])
        ndwi_val  = ndwi_img.reduceRegion(ee.Reducer.mean(), region, 20).getInfo()
        ndwi_mean = float(list(ndwi_val.values())[0] or 0)

        # NDTI: (B4-B3)/(B4+B3) — turbidity proxy
        ndti_img  = s2.mean().normalizedDifference(["B4","B3"])
        ndti_val  = ndti_img.reduceRegion(ee.Reducer.mean(), region, 20).getInfo()
        ndti_mean = float(list(ndti_val.values())[0] or 0)

        # Chlorophyll-a proxy: B5/B4
        b5 = s2.mean().select("B5")
        b4 = s2.mean().select("B4")
        chl_img = b5.divide(b4.add(1e-6))
        chl_val = chl_img.reduceRegion(ee.Reducer.mean(), region, 20).getInfo()
        chl_proxy = float(list(chl_val.values())[0] or 1.0)

        # Water fraction: pixels where NDWI > 0
        water_mask = ndwi_img.gt(0)
        wf_val = water_mask.reduceRegion(ee.Reducer.mean(), region, 100).getInfo()
        water_fraction = float(list(wf_val.values())[0] or 0)

        # Composite RS-WQI score (0-100)
        # High NDWI = more water = better; High NDTI = turbid = worse; High chl = algae = worse
        rs_wqi = float(max(0, min(100,
            50
            + (ndwi_mean * 30)       # water presence boost
            - (max(0, ndti_mean) * 40)  # turbidity penalty
            - (max(0, chl_proxy - 1) * 10)  # algae penalty
        )))

        return {
            "ndwi_mean":      round(ndwi_mean, 4),
            "ndti_mean":      round(ndti_mean, 4),
            "chl_proxy":      round(chl_proxy, 4),
            "water_fraction": round(water_fraction, 4),
            "rs_wqi_score":   round(rs_wqi, 1),
            "source":         "Sentinel-2 SR Harmonized (Copernicus/GEE)",
            "interpretation": (
                "EXCELLENT" if rs_wqi > 80 else
                "GOOD" if rs_wqi > 60 else
                "MODERATE" if rs_wqi > 40 else "POOR"
            ),
        }

    except Exception as e:
        logger.warning("Sentinel-2 WQI fetch failed: %s", e)
        return {"error": str(e), "rs_wqi_score": None}


def check_connectivity(timeout: int = 5) -> Dict[str, bool]:
    """
    Check connectivity to all data sources.

    Returns
    -------
    dict
        {"open_meteo": bool, "grdc": bool, "nasa_power": bool}

    Examples
    --------
    >>> status = check_connectivity()
    >>> print(status)
    {'open_meteo': True, 'grdc': False, 'nasa_power': True}
    """
    import urllib.request

    results = {}
    endpoints = {
        "open_meteo":  "https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&daily=temperature_2m_mean&forecast_days=1",
        "nasa_power":  "https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR&community=AG&longitude=0&latitude=0&start=20240101&end=20240102&format=JSON",
    }
    for name, url in endpoints.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "hydrosovereign/6.3.0"})
            with urllib.request.urlopen(req, timeout=timeout):
                results[name] = True
        except Exception:
            results[name] = False

    logger.info("Connectivity: %s", results)
    return results
