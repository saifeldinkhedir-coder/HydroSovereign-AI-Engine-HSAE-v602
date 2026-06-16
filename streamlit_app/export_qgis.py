"""
export_qgis.py — HSAE v6.01
Export basin data and analysis results to QGIS-compatible formats.
Produces GeoJSON, Shapefile-ready CSV, and styled QGIS project file.
"""
from __future__ import annotations
import json, io
from typing import Optional
import pandas as pd
import numpy as np


def basins_to_geojson(basins: dict, df: Optional[pd.DataFrame] = None) -> str:
    """
    Convert GLOBAL_BASINS dict to GeoJSON with ATDI/TDI computed from df.
    Ready to drag-and-drop into QGIS.
    """
    features = []
    for name, b in basins.items():
        # Compute ATDI from df if available
        atdi_pct = 0.0
        if df is not None and len(df) > 0:
            try:
                from hsae_tdi import compute_atdi
                i_in  = df["Inflow_BCM"].values  if "Inflow_BCM"  in df.columns else np.ones(len(df))
                q_out = df["Outflow_BCM"].values  if "Outflow_BCM" in df.columns else np.zeros(len(df))
                et_pm = df["Evap_PM_BCM"].values  if "Evap_PM_BCM" in df.columns else None
                et_mod= df["Evap_BCM"].values     if "Evap_BCM"    in df.columns else None
                atdi_pct = compute_atdi(i_in, q_out, et_pm, et_mod)
            except Exception:
                atdi_pct = 0.0

        # Legal status
        if atdi_pct >= 85:   legal = "EMERGENCY — Art.33"
        elif atdi_pct >= 70: legal = "CRITICAL — Art.12"
        elif atdi_pct >= 55: legal = "CONCERN — Art.9"
        elif atdi_pct >= 40: legal = "VIOLATION — Art.7"
        elif atdi_pct >= 25: legal = "REVIEW — Art.5"
        else:                legal = "COMPLIANT"

        # ATF risk colour for QGIS
        if atdi_pct >= 85:   colour = "#7f1d1d"
        elif atdi_pct >= 70: colour = "#ef4444"
        elif atdi_pct >= 55: colour = "#f97316"
        elif atdi_pct >= 40: colour = "#eab308"
        elif atdi_pct >= 25: colour = "#84cc16"
        else:                colour = "#22c55e"

        lon = float(b.get("lon", 0))
        lat = float(b.get("lat", 0))
        bbox = b.get("bbox", [lon-2, lat-2, lon+2, lat+2])

        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "id":            b.get("id", ""),
                "name":          name,
                "region":        b.get("region", ""),
                "continent":     b.get("continent", ""),
                "country":       " / ".join(b.get("country", [])) if isinstance(b.get("country"), list) else str(b.get("country", "")),
                "river":         b.get("river", ""),
                "dam":           b.get("dam", ""),
                "cap_BCM":       float(b.get("cap", 0)),
                "head_m":        float(b.get("head", 0)),
                "area_km2":      float(b.get("area_max", 0)),
                "treaty":        b.get("treaty", ""),
                "legal_arts":    b.get("legal_arts", ""),
                "ATDI_pct":      round(atdi_pct, 2),
                "legal_status":  legal,
                "qgis_colour":   colour,
                "grdc_id":       b.get("grdc_id", ""),
                "context":       b.get("context", ""),
                "bbox_wkt":      f"POLYGON(({bbox[0]} {bbox[1]},{bbox[2]} {bbox[1]},{bbox[2]} {bbox[3]},{bbox[0]} {bbox[3]},{bbox[0]} {bbox[1]}))",
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "name": "HSAE_v601_Basins",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features
    }
    return json.dumps(geojson, ensure_ascii=False, indent=2)


def df_to_qgis_csv(df: pd.DataFrame, basin: dict) -> str:
    """
    Export simulation DataFrame as QGIS-compatible CSV with coordinates.
    """
    out = df.copy()
    out["basin_name"] = basin.get("name", "")
    out["basin_id"]   = basin.get("id", "")
    out["lat"]        = float(basin.get("lat", 0))
    out["lon"]        = float(basin.get("lon", 0))
    if "Date" in out.columns:
        out["Date"] = pd.to_datetime(out["Date"]).dt.strftime("%Y-%m-%d")
    return out.to_csv(index=False)


def render_export_qgis_section(df, basin, basins_dict):
    """Streamlit section: Export to QGIS — 5 layers ranked by usefulness."""
    import streamlit as st

    st.markdown("---")
    st.markdown("### 🗺️ Export to QGIS")
    st.caption("5 layers — ranked by usefulness for mapping and publication")

    # ── LAYER 1: UNWC Legal Compliance Polygons (MOST USEFUL) ──────────
    st.markdown("#### ⭐ Layer 1 — UNWC Legal Compliance Map *(Most useful)*")
    st.caption("Basin polygons coloured by legal status: COMPLIANT → EMERGENCY · Directly usable in papers")
    try:
        legal_str = atdi_legal_layer(basins_dict, df)
        _fc1 = json.loads(legal_str)
        c1a, c1b = st.columns([2,1])
        with c1a:
            st.download_button("⬇️ Download UNWC_Compliance.geojson",
                data=legal_str, file_name="HSAE_UNWC_Compliance.geojson",
                mime="application/geo+json", key="dl_legal", use_container_width=True)
        with c1b:
            statuses = [f["properties"]["legal_status"] for f in _fc1["features"]]
            from collections import Counter
            for s, c in Counter(statuses).most_common():
                colour = {"EMERGENCY":"🔴","CRITICAL":"🟠","CONCERN":"🟡",
                          "VIOLATION":"🟡","REVIEW":"🟢","COMPLIANT":"🟢"}.get(s,"⚪")
                st.write(f"{colour} {s}: {c}")
    except Exception as e:
        st.error(f"{e}")

    st.markdown("---")

    # ── LAYER 2: Basin Boundary Polygons ───────────────────────────────
    st.markdown("#### ⭐ Layer 2 — Basin Boundary Polygons")
    st.caption("Bounding box polygons for all 26 basins · More useful than points for spatial analysis")
    try:
        bbox_str = basins_to_bbox_polygons(basins_dict, df)
        _fc2 = json.loads(bbox_str)
        st.download_button("⬇️ Download BasinBoundaries.geojson",
            data=bbox_str, file_name="HSAE_BasinBoundaries.geojson",
            mime="application/geo+json", key="dl_bbox", use_container_width=True)
        st.success(f"✅ {len(_fc2['features'])} basin polygons · ATDI + treaty + country attributes")
    except Exception as e:
        st.error(f"{e}")

    st.markdown("---")

    # ── LAYER 3: Basin Points with ATDI ────────────────────────────────
    st.markdown("#### Layer 3 — Basin Centroids (Points + ATDI)")
    st.caption("26 centroid points · all attributes · for labels and symbology")
    try:
        pts_str = basins_to_geojson(basins_dict, df)
        _fc3 = json.loads(pts_str)
        st.download_button("⬇️ Download BasinCentroids.geojson",
            data=pts_str, file_name="HSAE_BasinCentroids.geojson",
            mime="application/geo+json", key="dl_pts", use_container_width=True)
        st.success(f"✅ {len(_fc3['features'])} points")
    except Exception as e:
        st.error(f"{e}")

    st.markdown("---")

    # ── LAYER 4: Monthly Time Series (Temporal Layer) ──────────────────
    st.markdown("#### Layer 4 — Monthly Time Series *(Temporal)*")
    st.caption("Monthly aggregated simulation · use QGIS Temporal Controller to animate · NOT all 365 rows")
    if df is not None and len(df) > 0:
        try:
            monthly_str = simulation_to_points_geojson(df, basin)
            _fc4 = json.loads(monthly_str)
            st.download_button("⬇️ Download Monthly_TimeSeries.geojson",
                data=monthly_str,
                file_name=f"HSAE_{basin.get('id','basin')}_Monthly.geojson",
                mime="application/geo+json", key="dl_monthly", use_container_width=True)
            st.success(f"✅ {len(_fc4['features'])} months · Volume + Inflow + NDWI + TDI per month")
            st.info("💡 In QGIS: Layer Properties → Temporal → Field: date → animate with Temporal Controller")
        except Exception as e:
            st.error(f"{e}")
    else:
        st.info("▶️ Run v430 engine for basin-specific monthly data")

    st.markdown("---")

    # ── LAYER 5: CSV with coordinates ──────────────────────────────────
    st.markdown("#### Layer 5 — Full Time Series CSV")
    st.caption("All 365 daily rows with lat/lon — import as spreadsheet layer in QGIS")
    if df is not None and len(df) > 0:
        try:
            csv_str = df_to_qgis_csv(df, basin)
            st.download_button("⬇️ Download TimeSeries.csv",
                data=csv_str,
                file_name=f"HSAE_{basin.get('id','basin')}_daily.csv",
                mime="text/csv", key="dl_csv", use_container_width=True)
            st.success(f"✅ {len(df):,} daily rows · {len(df.columns)} variables")
        except Exception as e:
            st.error(f"{e}")
    else:
        st.info("▶️ Run v430 engine first")

    # ── QGIS Plugin instructions ────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔧 QGIS Plugin Installation")
    st.info("""**Recommended workflow:**
1. Install QGIS Plugin: `Plugins → Manage → Install from ZIP → hsae_qgis_v601.zip`
2. Click **Load Basin Registry** → all 26 basins load with ATDI colours
3. Download Layer 1 above → drag onto QGIS for legal compliance overlay
4. Use **Processing Toolbox → HydroSovereign → Calculate ATDI** with your own data
5. Export result as Shapefile for publication figures""")


def basins_to_bbox_polygons(basins: dict, df=None) -> str:
    """
    Export basin bounding boxes as GeoJSON Polygons.
    More useful than points — shows the actual spatial extent.
    """
    features = []
    for name, b in basins.items():
        lon = float(b.get("lon", 0))
        lat = float(b.get("lat", 0))
        bbox = b.get("bbox", [lon-2, lat-2, lon+2, lat+2])
        w, s, e, n = bbox[0], bbox[1], bbox[2], bbox[3]

        # Compute ATDI
        atdi_pct = 0.0
        if df is not None and len(df) > 0:
            try:
                from hsae_tdi import compute_atdi
                i_in  = df["Inflow_BCM"].values  if "Inflow_BCM"  in df.columns else None
                q_out = df["Outflow_BCM"].values  if "Outflow_BCM" in df.columns else None
                if i_in is not None and q_out is not None:
                    atdi_pct = compute_atdi(i_in, q_out)
            except Exception:
                pass

        if atdi_pct >= 85:   colour = "#7f1d1d"; legal = "EMERGENCY"
        elif atdi_pct >= 70: colour = "#ef4444"; legal = "CRITICAL"
        elif atdi_pct >= 55: colour = "#f97316"; legal = "CONCERN"
        elif atdi_pct >= 40: colour = "#eab308"; legal = "VIOLATION"
        elif atdi_pct >= 25: colour = "#84cc16"; legal = "REVIEW"
        else:                colour = "#22c55e"; legal = "COMPLIANT"

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[w,s],[e,s],[e,n],[w,n],[w,s]]]
            },
            "properties": {
                "name":         name,
                "id":           b.get("id",""),
                "river":        b.get("river",""),
                "dam":          b.get("dam",""),
                "country":      " / ".join(b.get("country",[])) if isinstance(b.get("country"), list) else str(b.get("country","")),
                "continent":    b.get("continent",""),
                "region":       b.get("region",""),
                "cap_BCM":      float(b.get("cap",0)),
                "area_km2":     float(b.get("area_max",0)),
                "treaty":       b.get("treaty",""),
                "legal_arts":   b.get("legal_arts",""),
                "ATDI_pct":     round(atdi_pct, 2),
                "legal_status": legal,
                "fill_colour":  colour,
                "fill_opacity": 0.35,
                "context":      b.get("context","")[:120],
            }
        }
        features.append(feature)

    return json.dumps({
        "type": "FeatureCollection",
        "name": "HSAE_BasinBoundaries",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features
    }, ensure_ascii=False, indent=2)


def atdi_legal_layer(basins: dict, df=None) -> str:
    """
    UNWC 1997 compliance layer — each basin polygon coloured by legal status.
    Most useful layer for the legal/diplomacy papers.
    """
    import json as _json
    features = []
    for name, b in basins.items():
        lon = float(b.get("lon", 0))
        lat = float(b.get("lat", 0))
        bbox = b.get("bbox", [lon-2, lat-2, lon+2, lat+2])
        w, s, e, n = bbox[0], bbox[1], bbox[2], bbox[3]

        tdi = float(b.get("tdi", 0.5))
        atdi = tdi * 100

        arts = []
        if atdi >= 25: arts.append("Art.5")
        if atdi >= 40: arts.append("Art.7")
        if atdi >= 55: arts.append("Art.9")
        if atdi >= 70: arts.append("Art.12")
        if atdi >= 85: arts.append("Art.33")

        if atdi >= 85:   status = "EMERGENCY"; colour = "#7f1d1d"
        elif atdi >= 70: status = "CRITICAL";  colour = "#ef4444"
        elif atdi >= 55: status = "CONCERN";   colour = "#f97316"
        elif atdi >= 40: status = "VIOLATION"; colour = "#eab308"
        elif atdi >= 25: status = "REVIEW";    colour = "#84cc16"
        else:            status = "COMPLIANT"; colour = "#22c55e"

        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon",
                         "coordinates": [[[w,s],[e,s],[e,n],[w,n],[w,s]]]},
            "properties": {
                "name":            name,
                "ATDI_pct":        round(atdi, 2),
                "legal_status":    status,
                "violated_arts":   ", ".join(arts) or "None",
                "treaty":          b.get("treaty",""),
                "upstream":        b.get("country",[""])[0] if isinstance(b.get("country"), list) else "",
                "downstream":      b.get("country",["",""])[1] if isinstance(b.get("country"), list) and len(b.get("country", [])) > 1 else "",
                "fill_colour":     colour,
                "recommended":     ("ICJ Referral" if atdi>=85 else
                                    "ITLOS Measures" if atdi>=70 else
                                    "PCA Arbitration" if atdi>=55 else
                                    "Bilateral Talks" if atdi>=25 else "Monitoring"),
            }
        })

    return json.dumps({
        "type": "FeatureCollection",
        "name": "HSAE_UNWC_Compliance",
        "features": features
    }, ensure_ascii=False, indent=2)


def simulation_to_points_geojson(df, basin: dict) -> str:
    """
    Export monthly-aggregated simulation as time-stamped GeoJSON points.
    Each point = one month · ATDI + flow + storage for that month.
    This is what makes sense spatially — not 365 identical-location rows.
    """
    if df is None or len(df) == 0:
        return json.dumps({"type":"FeatureCollection","features":[]})

    lon = float(basin.get("lon", 0))
    lat = float(basin.get("lat", 0))

    # Monthly aggregation
    _df = df.copy()
    if "Date" in _df.columns:
        _df["Date"] = pd.to_datetime(_df["Date"])
        monthly = _df.resample("ME", on="Date").mean(numeric_only=True).reset_index()
    else:
        monthly = _df.copy()

    features = []
    for _, row in monthly.iterrows():
        props = {
            "basin_name":  basin.get("name",""),
            "basin_id":    basin.get("id",""),
            "date":        row["Date"].strftime("%Y-%m") if "Date" in row else "",
        }
        for col in ["Volume_BCM","Inflow_BCM","Outflow_BCM","Pct_Full",
                    "Flow_m3s","TD_Deficit","S2_NDWI","GPM_Rain_mm"]:
            if col in row:
                props[col] = round(float(row[col]), 4) if not pd.isna(row[col]) else 0.0
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props
        })

    return json.dumps({
        "type": "FeatureCollection",
        "name": f"HSAE_{basin.get('id','basin')}_Monthly",
        "features": features
    }, ensure_ascii=False, indent=2)
