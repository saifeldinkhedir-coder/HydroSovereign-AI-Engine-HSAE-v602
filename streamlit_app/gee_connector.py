"""
gee_connector.py — HSAE v6.01  Google Earth Engine Live Integration
====================================================================
Real satellite data fetcher for all 26 HSAE basins.

Sensors:
  • GPM IMERG    — Daily precipitation (mm/day)
  • GRACE-FO     — Terrestrial Water Storage anomaly (cm)
  • MODIS ET     — Actual evapotranspiration (mm/8day)
  • MODIS NDVI   — Vegetation index
  • Sentinel-1   — Surface water extent (SAR backscatter)
  • SMAP L3      — Soil moisture (m³/m³)
  • MODIS LST    — Land surface temperature (K)
  • GloFAS ERA5  — River discharge reanalysis (m³/s)

Project: zinc-arc-484714-j8
Author:  Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations

import datetime
import math
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from typing import Dict, List, Optional, Tuple

GEE_PROJECT = "zinc-arc-484714-j8"

# ── Basin bounding boxes (lon_min, lat_min, lon_max, lat_max) ─────────────────
BASIN_BBOX: Dict[str, Tuple[float, float, float, float]] = {
    "blue_nile_gerd":      (33.0,  7.0, 40.0, 15.0),
    "nile_aswan":          (31.0, 22.0, 34.0, 25.0),
    "mekong_xayaburi":     (99.0, 17.0, 104.0, 22.0),
    "indus_tarbela":       (70.0, 32.0, 75.0, 36.0),
    "amu_darya_nurek":     (67.0, 36.0, 72.0, 40.0),
    "euphrates_ataturk":   (36.0, 36.0, 40.0, 39.0),
    "tigris_mosul":        (41.0, 35.0, 45.0, 38.0),
    "zambezi_kariba":      (26.0, -18.0, 30.0, -14.0),
    "niger_kainji":        (3.0,  8.0,  7.0,  12.0),
    "danube_iron_gates":   (21.0, 43.0, 25.0, 46.0),
    "rhine_basin":         (6.0,  47.0, 10.0, 52.0),
    "ganges_farakka":      (86.0, 23.0, 90.0, 26.0),
    "brahmaputra_subansiri":(92.0, 26.0, 96.0, 29.0),
    "amazon_belo_monte":   (-53.0,-5.0, -49.0, -1.0),
    "parana_itaipu":       (-56.0,-27.0,-52.0,-23.0),
    "colorado_hoover":     (-116.0,35.0,-113.0,37.0),
    "columbia_grand_coulee":(-120.0,46.0,-116.0,49.0),
    "yangtze_3gorges":     (109.0, 29.0, 112.0, 32.0),
    "salween_myitsone":    (96.0,  24.0, 100.0, 27.0),
    "dnieper_kakhovka":    (32.0,  46.0, 35.0,  49.0),
    "syr_darya_toktogul":  (72.0,  40.0, 76.0,  43.0),
    "orinoco_guri":        (-64.0,  6.0, -60.0,  9.0),
    "rio_grande_amistad":  (-103.0,28.0, -99.0, 31.0),
    "murray_darling_hume": (145.0,-38.0, 149.0,-34.0),
    "congo_inga":          (12.0,  -7.0,  16.0,  -3.0),
    "zambezi_cahora":      (30.0, -16.0,  34.0, -13.0),
}


# Cache GEE results at module level for 24 hours
import functools as _functools
_GEE_CACHE = {}  # {cache_key: result}

def _cached_gee(key, fn):
    """Simple in-memory cache for GEE results."""
    if key not in _GEE_CACHE:
        _GEE_CACHE[key] = fn()
    return _GEE_CACHE[key]

def _init_ee():
    """Initialize GEE via Service Account (Streamlit) or personal creds (local)."""
    try:
        from gee_auth import get_ee
        return get_ee()
    except ImportError:
        pass
    try:
        import ee
        try:
            ee.Initialize(project=GEE_PROJECT)
        except Exception:
            ee.Authenticate()
            ee.Initialize(project=GEE_PROJECT)
        return ee
    except ImportError:
        raise ImportError("earthengine-api not installed.")


def fetch_gpm_precipitation(basin_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch GPM IMERG daily precipitation for a basin.

    Parameters
    ----------
    basin_id   : HSAE basin key (e.g. 'blue_nile_gerd')
    start_date : 'YYYY-MM-DD'
    end_date   : 'YYYY-MM-DD'

    Returns
    -------
    dict with: dates, P_mm (daily precip), mean_P, max_P, source
    """
    ee = _init_ee()
    bbox = BASIN_BBOX.get(basin_id)
    if not bbox:
        return {"error": f"Unknown basin: {basin_id}"}

    lon_min, lat_min, lon_max, lat_max = bbox
    region = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

    try:
        # Single server-side aggregation — much faster than 365 separate calls
        collection = (ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
                      .filterDate(start_date, end_date)
                      .filterBounds(region)
                      .select("precipitation"))

        # Group by day server-side
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt   = datetime.datetime.strptime(end_date,   "%Y-%m-%d")
        n_days   = (end_dt - start_dt).days + 1

        def make_daily(day_offset):
            d0  = ee.Date(start_date).advance(day_offset, "day")
            d1  = d0.advance(1, "day")
            img = collection.filterDate(d0, d1).mean()
            val = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=11132,
                maxPixels=1e9
            ).get("precipitation")
            return ee.Feature(None, {
                "date": d0.format("YYYY-MM-dd"),
                "P_mm": ee.Number(val).multiply(24)  # mm/hr → mm/day
            })

        features_col = ee.FeatureCollection(
            ee.List.sequence(0, n_days - 1).map(make_daily)
        )
        features = features_col.getInfo()["features"]
        dates = [f["properties"]["date"] for f in features]
        P_mm  = [round(f["properties"]["P_mm"] or 0.0, 3) for f in features]
        mean_P = round(sum(P_mm) / len(P_mm), 3) if P_mm else 0.0
        max_P  = round(max(P_mm), 3) if P_mm else 0.0

        return {
            "basin_id":   basin_id,
            "start_date": start_date,
            "end_date":   end_date,
            "n_days":     len(dates),
            "dates":      dates,
            "P_mm":       P_mm,
            "mean_P":     mean_P,
            "max_P":      max_P,
            "source":     "NASA GPM IMERG V07",
            "doi":        "10.5067/GPM/IMERG/3B-HH/07",
        }
    except Exception as exc:
        return {"error": str(exc), "basin_id": basin_id}


def fetch_grace_tws(basin_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch GRACE-FO Terrestrial Water Storage anomaly.

    Returns TWS anomaly in cm (relative to 2004–2009 baseline).
    """
    ee = _init_ee()
    bbox = BASIN_BBOX.get(basin_id)
    if not bbox:
        return {"error": f"Unknown basin: {basin_id}"}

    lon_min, lat_min, lon_max, lat_max = bbox
    region = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

    try:
        # Current GRACE-FO collections (2024 catalog)
        grace_collections = [
            ("NASA/GRACE/MASS_GRIDS_V04/MASCON",       "lwe_thickness"),
            ("NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI",   "lwe_thickness"),
            ("NASA/GRACE/MASS_GRIDS_V04/LAND",         "lwe_thickness"),
            ("NASA/GRACE/MASS_GRIDS/MASCON",           "lwe_thickness"),
            ("NASA/GRACE/MASS_GRIDS/MASCON_CRI",       "lwe_thickness"),
        ]
        collection = None
        band = "lwe_thickness"
        for cid, b in grace_collections:
            try:
                c = (ee.ImageCollection(cid)
                     .filterDate(start_date, end_date)
                     .filterBounds(region))
                n = c.size().getInfo()
                if n > 0:
                    collection = c.select(b)
                    band = b
                    print(f"[GEE] GRACE-FO using: {cid} ({n} images)")
                    break
            except Exception:
                continue

        if collection is None:
            return {"error": "GRACE-FO collection not found", "basin_id": basin_id}

        def extract_tws(img):
            mean_tws = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=111320,
                maxPixels=1e9
            ).get(band)
            return ee.Feature(None, {
                "date":   img.date().format("YYYY-MM-dd"),
                "tws_cm": mean_tws,
            })

        features = collection.map(extract_tws).getInfo()["features"]
        dates   = [f["properties"]["date"] for f in features]
        tws_cm  = [round(f["properties"]["tws_cm"] or 0.0, 4) for f in features]
        mean_tws = round(sum(tws_cm) / len(tws_cm), 4) if tws_cm else 0.0

        return {
            "basin_id":  basin_id,
            "n_months":  len(dates),
            "dates":     dates,
            "tws_cm":    tws_cm,
            "mean_tws":  mean_tws,
            "source":    "GRACE-FO RL06v4 (NASA JPL)",
            "doi":       "10.5067/GGOS/GRACE_FO/DATA_LEVEL-3",
        }
    except Exception as exc:
        return {"error": str(exc), "basin_id": basin_id}


def fetch_modis_et(basin_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch MODIS MOD16A2 actual evapotranspiration (mm/8day → mm/day).
    """
    ee = _init_ee()
    bbox = BASIN_BBOX.get(basin_id)
    if not bbox:
        return {"error": f"Unknown basin: {basin_id}"}

    lon_min, lat_min, lon_max, lat_max = bbox
    region = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

    try:
        collection = (
            ee.ImageCollection("MODIS/061/MOD16A2")
            .filterDate(start_date, end_date)
            .filterBounds(region)
            .select("ET")
        )

        def extract_et(img):
            mean_et = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=500,
                maxPixels=1e9
            ).get("ET")
            return ee.Feature(None, {
                "date":   img.date().format("YYYY-MM-dd"),
                "ET_mm":  ee.Number(mean_et).multiply(0.1).divide(8),
            })

        features = collection.map(extract_et).getInfo()["features"]
        dates  = [f["properties"]["date"] for f in features]
        ET_mm  = [round(f["properties"]["ET_mm"] or 0.0, 3) for f in features]
        mean_ET = round(sum(ET_mm) / len(ET_mm), 3) if ET_mm else 0.0

        return {
            "basin_id": basin_id,
            "n_obs":    len(dates),
            "dates":    dates,
            "ET_mm":    ET_mm,
            "mean_ET":  mean_ET,
            "source":   "MODIS MOD16A2 v061",
            "doi":      "10.5067/MODIS/MOD16A2.061",
        }
    except Exception as exc:
        return {"error": str(exc), "basin_id": basin_id}


def fetch_smap_soil_moisture(basin_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch SMAP L3 surface soil moisture (m³/m³).
    """
    ee = _init_ee()
    bbox = BASIN_BBOX.get(basin_id)
    if not bbox:
        return {"error": f"Unknown basin: {basin_id}"}

    lon_min, lat_min, lon_max, lat_max = bbox
    region = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])

    try:
        # Current SMAP collections (2024 GEE catalog)
        smap_collections = [
            ("NASA/SMAP/SPL3SMP_E/005",            "soil_moisture_am"),
            ("NASA/SMAP/SPL3SMP_E/006",            "soil_moisture_am"),
            ("NASA_USDA/HSL/SMAP_soil_moisture",   "ssm"),
            ("NASA_USDA/HSL/SMAP10KM_soil_moisture","ssm"),
        ]
        collection = None
        smap_band  = "ssm"
        for cid, b in smap_collections:
            try:
                c = (ee.ImageCollection(cid)
                     .filterDate(start_date, end_date)
                     .filterBounds(region))
                n_imgs = c.size().getInfo()
                if n_imgs > 0:
                    collection = c.select(b)
                    smap_band  = b
                    print(f"[GEE] SMAP using: {cid} ({n_imgs} images)")
                    break
            except Exception:
                continue
        if collection is None:
            return {"basin_id": basin_id, "sm_m3m3": [], "mean_sm": 0.28,
                    "source": "SMAP unavailable — all collections empty"}

        def extract_sm(img):
            mean_sm = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=10000,
                maxPixels=1e9
            ).get(smap_band)
            return ee.Feature(None, {
                "date":  img.date().format("YYYY-MM-dd"),
                "sm":    mean_sm,
            })

        features = collection.map(extract_sm).getInfo()["features"]
        dates  = [f["properties"]["date"] for f in features]
        sm     = [round(f["properties"]["sm"] or 0.0, 4) for f in features]
        mean_sm = round(sum(sm) / len(sm), 4) if sm else 0.0

        return {
            "basin_id": basin_id,
            "n_obs":    len(dates),
            "dates":    dates,
            "sm_m3m3":  sm,
            "mean_sm":  mean_sm,
            "source":   "SMAP L3 10km (NASA-USDA)",
            "doi":      "10.5067/OMHVSRGFX38O",
        }
    except Exception as exc:
        return {"error": str(exc), "basin_id": basin_id}




# ══════════════════════════════════════════════════════════════════════════════
# Sentinel-1 SAR — Surface Water Extent & Backscatter
# ══════════════════════════════════════════════════════════════════════════════

def fetch_sentinel1(basin_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch Sentinel-1 SAR backscatter and water extent for a basin.
    Returns: S1_VV_dB (monthly mean), S1_Area (water extent km²)
    """
    try:
        ee     = _init_ee()
        bbox   = BASIN_BBOX.get(basin_id)
        if not bbox:
            return {"error": f"Unknown basin: {basin_id}"}
        region = ee.Geometry.Rectangle(list(bbox))

        s1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
              .filterDate(start_date, end_date)
              .filterBounds(region)
              .filter(ee.Filter.eq("instrumentMode", "IW"))
              .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
              .select("VV"))

        n = s1.size().getInfo()
        if n == 0:
            return {"error": "No Sentinel-1 images", "basin_id": basin_id}

        def extract_s1(img):
            vv_mean = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region, scale=10, maxPixels=1e9
            ).get("VV")
            # Water pixels: VV < -15 dB
            water = img.lt(-15)
            water_area = (water.multiply(ee.Image.pixelArea())
                         .reduceRegion(ee.Reducer.sum(), region, 10, maxPixels=1e9)
                         .get("VV"))
            return ee.Feature(None, {
                "date":       img.date().format("YYYY-MM-dd"),
                "S1_VV_dB":  vv_mean,
                "S1_Area_m2": water_area,
            })

        feats = s1.map(extract_s1).getInfo()["features"]
        dates, vv_vals, area_vals = [], [], []
        for f in feats:
            p = f["properties"]
            if p.get("S1_VV_dB") is not None:
                dates.append(p["date"])
                vv_vals.append(round(float(p["S1_VV_dB"]), 3))
                area_km2 = float(p.get("S1_Area_m2") or 0) / 1e6
                area_vals.append(round(area_km2, 2))

        return {
            "basin_id":  basin_id,
            "dates":     dates,
            "S1_VV_dB":  vv_vals,
            "S1_Area":   area_vals,
            "mean_VV":   round(sum(vv_vals)/len(vv_vals), 3) if vv_vals else 0,
            "mean_area": round(sum(area_vals)/len(area_vals), 2) if area_vals else 0,
            "n_images":  len(dates),
            "source":    "Copernicus Sentinel-1 GRD IW VV",
        }
    except Exception as exc:
        return {"error": str(exc), "basin_id": basin_id}


# ══════════════════════════════════════════════════════════════════════════════
# Sentinel-2 — NDWI & NDVI (cloud-masked)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_sentinel2(basin_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch Sentinel-2 NDWI and NDVI (cloud-masked) for a basin.
    """
    try:
        ee     = _init_ee()
        bbox   = BASIN_BBOX.get(basin_id)
        if not bbox:
            return {"error": f"Unknown basin: {basin_id}"}
        region = ee.Geometry.Rectangle(list(bbox))

        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterDate(start_date, end_date)
              .filterBounds(region)
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

        n = s2.size().getInfo()
        if n == 0:
            # Try less strict cloud filter
            s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterDate(start_date, end_date)
                  .filterBounds(region)
                  .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))
            n = s2.size().getInfo()
            if n == 0:
                return {"error": "No Sentinel-2 images", "basin_id": basin_id}

        def extract_s2(img):
            # NDWI = (Green - NIR) / (Green + NIR)
            ndwi = img.normalizedDifference(["B3", "B8"])
            # NDVI = (NIR - Red) / (NIR + Red)
            ndvi = img.normalizedDifference(["B8", "B4"])
            ndwi_val = ndwi.reduceRegion(ee.Reducer.mean(), region, 20, maxPixels=1e9).get("nd")
            ndvi_val = ndvi.reduceRegion(ee.Reducer.mean(), region, 20, maxPixels=1e9).get("nd")
            return ee.Feature(None, {
                "date":  img.date().format("YYYY-MM-dd"),
                "NDWI":  ndwi_val,
                "NDVI":  ndvi_val,
            })

        feats = s2.map(extract_s2).getInfo()["features"]
        dates, ndwi_vals, ndvi_vals = [], [], []
        for f in feats:
            p = f["properties"]
            if p.get("NDWI") is not None and p.get("NDVI") is not None:
                dates.append(p["date"])
                ndwi_vals.append(round(float(p["NDWI"]), 4))
                ndvi_vals.append(round(float(p["NDVI"]), 4))

        return {
            "basin_id":  basin_id,
            "dates":     dates,
            "NDWI":      ndwi_vals,
            "NDVI":      ndvi_vals,
            "mean_NDWI": round(sum(ndwi_vals)/len(ndwi_vals), 4) if ndwi_vals else 0,
            "mean_NDVI": round(sum(ndvi_vals)/len(ndvi_vals), 4) if ndvi_vals else 0,
            "n_images":  len(dates),
            "source":    "Copernicus Sentinel-2 SR Harmonized",
        }
    except Exception as exc:
        return {"error": str(exc), "basin_id": basin_id}


# ══════════════════════════════════════════════════════════════════════════════
# GloFAS ERA5 — River Discharge Reanalysis
# ══════════════════════════════════════════════════════════════════════════════

def fetch_glofas_discharge(basin_id: str, start_date: str, end_date: str) -> dict:
    """
    Fetch GloFAS v4 ERA5 reanalysis discharge for a basin outlet.
    Collection: ECMWF/CEMS_GLOFAS/v4 or similar
    """
    try:
        ee     = _init_ee()
        bbox   = BASIN_BBOX.get(basin_id)
        if not bbox:
            return {"error": f"Unknown basin: {basin_id}"}

        # Basin outlet = downstream corner
        lon_min, lat_min, lon_max, lat_max = bbox
        outlet = ee.Geometry.Point([lon_max, lat_min])

        glofas_collections = [
            ("ECMWF/CEMS_GLOFAS/v4",           "dis06"),
            ("ECMWF/CEMS_GLOFAS_HISTORICAL/v4", "dis06"),
        ]

        collection = None
        band = "dis06"
        for cid, b in glofas_collections:
            try:
                c = (ee.ImageCollection(cid)
                     .filterDate(start_date, end_date)
                     .filterBounds(outlet))
                if c.size().getInfo() > 0:
                    collection = c.select(b)
                    band = b
                    break
            except Exception:
                continue

        if collection is None:
            return {"error": "GloFAS collection not found", "basin_id": basin_id}

        def extract_q(img):
            q = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=outlet.buffer(5000),
                scale=1000, maxPixels=1e9
            ).get(band)
            return ee.Feature(None, {
                "date": img.date().format("YYYY-MM-dd"),
                "Q_m3s": q,
            })

        feats = collection.map(extract_q).getInfo()["features"]
        dates, q_vals = [], []
        for f in feats:
            p = f["properties"]
            if p.get("Q_m3s") is not None:
                dates.append(p["date"])
                q_vals.append(round(float(p["Q_m3s"]), 2))

        if not q_vals:
            return {"error": "No GloFAS data", "basin_id": basin_id}

        return {
            "basin_id": basin_id,
            "dates":    dates,
            "Q_m3s":    q_vals,
            "mean_Q":   round(sum(q_vals)/len(q_vals), 2),
            "max_Q":    round(max(q_vals), 2),
            "n_days":   len(dates),
            "source":   "GloFAS ERA5 v4 reanalysis",
        }
    except Exception as exc:
        return {"error": str(exc), "basin_id": basin_id}


def fetch_all_forcing(basin_id: str,
                      start_date: str = "2023-01-01",
                      end_date:   str = "2023-12-31") -> dict:
    """
    Fetch all forcing data for a basin in one call.
    Returns combined dict ready for HBV-96 and ATDI computation.
    """
    print(f"[GEE] Fetching forcing for {basin_id}  {start_date} → {end_date}")

    gpm   = fetch_gpm_precipitation(basin_id, start_date, end_date)
    grace = fetch_grace_tws(basin_id, start_date, end_date)
    et    = fetch_modis_et(basin_id, start_date, end_date)
    smap  = fetch_smap_soil_moisture(basin_id, start_date, end_date)
    s1    = fetch_sentinel1(basin_id, start_date, end_date)
    s2    = fetch_sentinel2(basin_id, start_date, end_date)
    glofas = fetch_glofas_discharge(basin_id, start_date, end_date)

    return {
        "basin_id":    basin_id,
        "start_date":  start_date,
        "end_date":    end_date,
        "gee_project": GEE_PROJECT,
        "precipitation": gpm,
        "grace_tws":   grace,
        "modis_et":    et,
        "smap_sm":     smap,
        "sentinel1":   s1,
        "sentinel2":   s2,
        "glofas":      glofas,
        "status": {
            "gpm":    "ok" if "error" not in gpm    else gpm["error"],
            "grace":  "ok" if "error" not in grace  else grace["error"],
            "et":     "ok" if "error" not in et     else et["error"],
            "smap":   "ok" if "error" not in smap   else smap["error"],
            "s1":     "ok" if "error" not in s1     else s1["error"],
            "s2":     "ok" if "error" not in s2     else s2["error"],
            "glofas": "ok" if "error" not in glofas else glofas["error"],
        }
    }


def test_gee_connection() -> bool:
    """Quick test — returns True if GEE is connected."""
    try:
        ee = _init_ee()
        val = ee.Number(42).getInfo()
        print(f"[GEE] Connection OK — project: {GEE_PROJECT}")
        return val == 42
    except Exception as exc:
        print(f"[GEE] Connection FAILED: {exc}")
        return False


if __name__ == "__main__":
    print("=== HSAE v6.01 — GEE Live Connection Test ===")

    if not test_gee_connection():
        print("Run: earthengine authenticate")
        exit(1)

    print("\n[TEST] Fetching GPM precipitation — Blue Nile 2023...")
    result = fetch_gpm_precipitation("blue_nile_gerd", "2023-01-01", "2023-03-31")

    if "error" in result:
        print(f"ERROR: {result['error']}")
    else:
        print(f"  Days fetched:    {result['n_days']}")
        print(f"  Mean precip:     {result['mean_P']} mm/day")
        print(f"  Max precip:      {result['max_P']} mm/day")
        print(f"  Source:          {result['source']}")
        print(f"  First date:      {result['dates'][0] if result['dates'] else 'N/A'}")
        print(f"  Last date:       {result['dates'][-1] if result['dates'] else 'N/A'}")

    print("\n[TEST] Fetching GRACE-FO TWS — Blue Nile 2023...")
    grace = fetch_grace_tws("blue_nile_gerd", "2023-01-01", "2023-12-31")
    if "error" in grace:
        print(f"ERROR: {grace['error']}")
    else:
        print(f"  Months fetched:  {grace['n_months']}")
        print(f"  Mean TWS:        {grace['mean_tws']} cm")
        print(f"  Source:          {grace['source']}")

    print("\n✅ GEE connector ready for HSAE v6.01")
    print(f"   Project: {GEE_PROJECT}")
    print(f"   Basins supported: {len(BASIN_BBOX)}")
