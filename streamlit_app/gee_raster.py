"""
gee_raster.py — GEE Live Raster Layers in QGIS
================================================
Fetches and displays live satellite rasters via GEE:
  - Sentinel-2 NDWI (water index)
  - Sentinel-1 SAR (flood mapping)
  - GPM IMERG (precipitation)
  - MODIS LST (land surface temperature)
  - MODIS NDVI (vegetation)

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
import os, json, tempfile
from typing import Optional, Dict

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QLabel, QProgressDialog, QMessageBox, QCheckBox
)
from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsRasterLayer, QgsProject, QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer, QgsRasterShader
)

GEE_LAYERS = {
    "💧 NDWI (Sentinel-2 Water Index)": {
        "collection": "COPERNICUS/S2_SR_HARMONIZED",
        "bands": ["B3", "B8"],
        "op": "ndwi",
        "vis": {"min": -0.5, "max": 0.5, "palette": ["brown", "white", "blue"]},
        "desc": "Normalised Difference Water Index — water = positive values",
    },
    "📡 SAR Backscatter (Sentinel-1)": {
        "collection": "COPERNICUS/S1_GRD",
        "bands": ["VV"],
        "op": "mean",
        "vis": {"min": -25, "max": 0, "palette": ["black", "gray", "white"]},
        "desc": "SAR VV backscatter — flooded areas appear dark",
    },
    "🌧️ Precipitation (GPM IMERG)": {
        "collection": "NASA/GPM_L3/IMERG_V07",
        "bands": ["precipitation"],
        "op": "mean",
        "vis": {"min": 0, "max": 20, "palette": ["white", "cyan", "blue", "darkblue"]},
        "desc": "Mean daily precipitation (mm/day)",
    },
    "🌡️ Land Surface Temp (MODIS)": {
        "collection": "MODIS/061/MOD11A2",
        "bands": ["LST_Day_1km"],
        "op": "mean",
        "vis": {"min": 13000, "max": 16500, "palette": ["blue", "green", "yellow", "red"]},
        "desc": "MODIS LST (×50 − 273.15 = °C)",
    },
    "🌿 NDVI (MODIS Vegetation)": {
        "collection": "MODIS/061/MOD13A2",
        "bands": ["NDVI"],
        "op": "mean",
        "vis": {"min": -2000, "max": 9000, "palette": ["brown", "yellow", "green", "darkgreen"]},
        "desc": "Normalised Difference Vegetation Index",
    },
}

DATE_RANGES = {
    "Last 30 days":  ("2025-12-01", "2025-12-31"),
    "2025 full year":("2025-01-01", "2025-12-31"),
    "2024 full year":("2024-01-01", "2024-12-31"),
    "2023 full year":("2023-01-01", "2023-12-31"),
    "2022 full year":("2022-01-01", "2022-12-31"),
    "2020-2025":     ("2020-01-01", "2025-12-31"),
}


def _init_gee() -> bool:
    try:
        import ee
        try:
            ee.Initialize(project="zinc-arc-484714-j8")
            return True
        except Exception:
            ee.Authenticate()
            ee.Initialize(project="zinc-arc-484714-j8")
            return True
    except Exception as e:
        return False


def fetch_gee_tile_url(layer_name: str, basin_cfg: Dict,
                        date_range: tuple) -> Optional[str]:
    """Get a GEE tile URL for display in QGIS."""
    if not _init_gee():
        return None
    try:
        import ee
        cfg = GEE_LAYERS[layer_name]
        bbox = basin_cfg.get("bbox", [-180, -90, 180, 90])
        aoi = ee.Geometry.Rectangle(bbox)
        start, end = date_range

        col = (ee.ImageCollection(cfg["collection"])
               .filterBounds(aoi)
               .filterDate(start, end))

        if cfg["op"] == "ndwi":
            img = col.select(cfg["bands"]).median()
            img = img.normalizedDifference(cfg["bands"]).rename("result")
        elif cfg["op"] == "mean":
            img = col.select(cfg["bands"][0]).mean()
        else:
            img = col.select(cfg["bands"][0]).median()

        img = img.clip(aoi)
        vis = cfg["vis"]
        tile_url = img.getMapId(vis)["tile_fetcher"].url_format
        return tile_url

    except Exception as e:
        return None


def add_gee_raster_to_qgis(iface, tile_url: str, layer_name: str,
                             basin_name: str) -> bool:
    """Add GEE tile URL as XYZ raster layer in QGIS."""
    try:
        url_param = (
            f"type=xyz"
            f"&url={tile_url}"
            f"&zmax=14&zmin=1"
            f"&crs=EPSG:3857"
        )
        full_name = f"🛰️ {layer_name} — {basin_name}"
        layer = QgsRasterLayer(url_param, full_name, "wms")

        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            iface.messageBar().pushSuccess(
                "HSAE GEE",
                f"✅ {layer_name} loaded for {basin_name}"
            )
            return True
        else:
            return False
    except Exception as e:
        return False


class GEERasterDialog(QDialog):
    """Dialog for selecting and loading GEE raster layers."""

    def __init__(self, iface, basins: list, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.basins = basins
        self.setWindowTitle("🛰️ HSAE GEE Live Raster")
        self.setMinimumWidth(500)
        self.setStyleSheet("background:#1a1a2e;color:#eee;")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        hdr = QLabel("🛰️ GEE Live Satellite Raster")
        hdr.setStyleSheet("color:#00d4ff;font-size:16px;font-weight:bold;")
        layout.addWidget(hdr)

        sub = QLabel("Fetch live imagery from Google Earth Engine into QGIS")
        sub.setStyleSheet("color:#888;font-size:12px;")
        layout.addWidget(sub)

        combo_style = """
            QComboBox{background:#0d1b2a;color:#eee;border:1px solid #334;
                      border-radius:4px;padding:5px 10px;}
            QComboBox QAbstractItemView{background:#0d1b2a;color:#eee;
                                        selection-background-color:#0f3460;}
        """

        # Layer selector
        layout.addWidget(QLabel("Satellite Layer:"))
        self.layer_combo = QComboBox()
        self.layer_combo.addItems(list(GEE_LAYERS.keys()))
        self.layer_combo.setStyleSheet(combo_style)
        self.layer_combo.currentTextChanged.connect(self._update_desc)
        layout.addWidget(self.layer_combo)

        # Description
        self.desc_lbl = QLabel()
        self.desc_lbl.setStyleSheet("color:#888;font-size:11px;padding:4px;")
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)

        # Basin selector
        layout.addWidget(QLabel("Basin / Area of Interest:"))
        self.basin_combo = QComboBox()
        self.basin_combo.addItem("🌍 Global (All Basins)")
        self.basin_combo.addItems([b["name"] for b in self.basins])
        self.basin_combo.setStyleSheet(combo_style)
        layout.addWidget(self.basin_combo)

        # Date range
        layout.addWidget(QLabel("Date Range:"))
        self.date_combo = QComboBox()
        self.date_combo.addItems(list(DATE_RANGES.keys()))
        self.date_combo.setCurrentText("2025 full year")
        self.date_combo.setStyleSheet(combo_style)
        layout.addWidget(self.date_combo)

        # Note
        note = QLabel(
            "⚠️ Requires GEE authentication.\n"
            "Run '🛰️ GEE Status' first to verify connection."
        )
        note.setStyleSheet("color:#f39c12;font-size:11px;background:#0d1b2a;"
                           "border-radius:6px;padding:8px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        load_btn = QPushButton("🛰️ Load Raster")
        load_btn.clicked.connect(self._load_raster)
        load_btn.setStyleSheet(
            "QPushButton{background:#0f3460;color:#00d4ff;border:1px solid #00d4ff44;"
            "border-radius:6px;padding:8px 24px;font-weight:bold;font-size:13px;}"
            "QPushButton:hover{background:#16498a;}"
        )

        close_btn = QPushButton("✖ Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(
            "QPushButton{background:#2c3e50;color:#eee;border-radius:6px;padding:8px 16px;}"
        )

        btn_row.addWidget(close_btn)
        btn_row.addWidget(load_btn)
        layout.addLayout(btn_row)

        self._update_desc(self.layer_combo.currentText())

    def _update_desc(self, name: str):
        desc = GEE_LAYERS.get(name, {}).get("desc", "")
        self.desc_lbl.setText(f"ℹ️ {desc}")

    def _load_raster(self):
        layer_name = self.layer_combo.currentText()
        basin_name = self.basin_combo.currentText()
        date_key = self.date_combo.currentText()
        date_range = DATE_RANGES[date_key]

        if basin_name == "🌍 Global (All Basins)":
            basin_cfg = {"bbox": [-180, -60, 180, 75]}
        else:
            basin = next((b for b in self.basins if b["name"] == basin_name), None)
            basin_cfg = basin or {"bbox": [-180, -60, 180, 75]}

        progress = QProgressDialog("Fetching GEE raster...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        tile_url = fetch_gee_tile_url(layer_name, basin_cfg, date_range)
        progress.close()

        if tile_url:
            ok = add_gee_raster_to_qgis(self.iface, tile_url, layer_name, basin_name)
            if not ok:
                QMessageBox.warning(self, "GEE", "Layer loaded but could not be displayed. Check QGIS logs.")
        else:
            QMessageBox.warning(
                self, "GEE Not Available",
                "❌ Could not fetch GEE raster.\n\n"
                "Possible reasons:\n"
                "• GEE not authenticated\n"
                "• earthengine-api not installed\n"
                "• No imagery for this area/date\n\n"
                "Run: pip install earthengine-api\n"
                "Then: earthengine authenticate"
            )

# ── GEE Authentication Helper ─────────────────────────────────────────────────

GEE_SETUP_GUIDE = """
HSAE GEE Setup (one-time):
  1. pip install earthengine-api
  2. earthengine authenticate        # opens browser
  3. earthengine set_project zinc-arc-484714-j8
  
Or in Python:
  import ee
  ee.Authenticate()
  ee.Initialize(project="zinc-arc-484714-j8")
  
Then run HSAE_GEE_AllBasins.js in https://code.earthengine.google.com
to export S1-SAR + GPM-IMERG + MODIS-MOD16 for all 50 basins (2011-2025).
"""

def check_gee_auth() -> dict:
    """
    Check GEE authentication status without crashing.
    
    Returns
    -------
    dict: {authenticated: bool, project: str, error: str, setup_guide: str}
    """
    try:
        import ee
        try:
            ee.Initialize(project="zinc-arc-484714-j8")
            info = ee.String("HSAE GEE OK").getInfo()
            return {
                "authenticated": True,
                "project":       "zinc-arc-484714-j8",
                "error":         None,
                "setup_guide":   None,
            }
        except Exception as e:
            return {
                "authenticated": False,
                "project":       None,
                "error":         str(e),
                "setup_guide":   GEE_SETUP_GUIDE,
            }
    except ImportError:
        return {
            "authenticated": False,
            "project":       None,
            "error":         "earthengine-api not installed (pip install earthengine-api)",
            "setup_guide":   GEE_SETUP_GUIDE,
        }


def get_basin_gee_stats(
    display_id: str,
    sensor: str = "S1_SAR",
    year: int = 2023,
) -> dict:
    """
    Get GEE statistics for a basin using basin display_id.
    
    Sensors: "S1_SAR" | "GPM_IMERG" | "MODIS_MOD16" | "NDWI"
    
    Returns real values if GEE authenticated, else returns synthetic.
    
    Usage
    -----
    stats = get_basin_gee_stats("blue_nile_gerd", sensor="GPM_IMERG", year=2023)
    """
    from basin_registry import get_basin_info
    import math, random
    
    info = get_basin_info(display_id)
    auth = check_gee_auth()
    
    if auth["authenticated"]:
        try:
            import ee
            from basin_registry import get_basin_info
            binfo = get_basin_info(display_id) or {}
            lat = binfo.get("lat", 0)
            lon = binfo.get("lon", 0)
            # 1° buffer around basin centroid
            point = ee.Geometry.Point([lon, lat])
            region = point.buffer(100000)  # 100 km radius

            sensor_config = {
                "S1_SAR": {
                    "collection": "COPERNICUS/S1_GRD",
                    "band": "VV",
                    "filter": ee.Filter.eq("instrumentMode", "IW"),
                    "unit": "dB",
                    "name": "SAR Backscatter VV",
                    "doi": "10.1016/j.rse.2017.06.031",
                },
                "GPM_IMERG": {
                    "collection": "NASA/GPM_L3/IMERG_V06",
                    "band": "precipitationCal",
                    "filter": None,
                    "scale": 365.0 * 24.0,  # mm/hr → mm/yr
                    "unit": "mm/yr",
                    "name": "Annual Precipitation (GPM IMERG v6)",
                    "doi": "10.1175/JHM-D-18-0080.1",
                },
                "MODIS_MOD16": {
                    "collection": "MODIS/006/MOD16A2",
                    "band": "ET",
                    "filter": None,
                    "scale": 0.1,  # 0.1 mm/8day → mm, sum annually
                    "unit": "mm/yr",
                    "name": "Actual ET (MOD16A2)",
                    "doi": "10.5067/MODIS/MOD16A2.006",
                },
                "NDWI": {
                    "collection": "MODIS/006/MOD09A1",
                    "band": None,  # computed from B4 and B2
                    "unit": "index",
                    "name": "NDWI (MODIS MOD09A1)",
                    "doi": "10.5067/MODIS/MOD09A1.006",
                },
            }
            cfg = sensor_config.get(sensor, {})
            if not cfg:
                raise ValueError(f"Unknown sensor: {sensor}")

            col = ee.ImageCollection(cfg["collection"])
            if cfg.get("filter"):
                col = col.filter(cfg["filter"])
            col = col.filterDate(f"{year}-01-01", f"{year}-12-31")
            col = col.filterBounds(region)

            if sensor == "NDWI":
                img = col.median()
                b4  = img.select("sur_refl_b04")  # Green
                b2  = img.select("sur_refl_b02")  # NIR
                ndwi = b4.subtract(b2).divide(b4.add(b2)).rename("NDWI")
                mean_dict = ndwi.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=region, scale=500, maxPixels=1e9
                ).getInfo()
                mean_val = round(mean_dict.get("NDWI", 0), 4)
            elif sensor == "GPM_IMERG":
                img = col.select(cfg["band"]).sum()
                mean_dict = img.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=region, scale=11132, maxPixels=1e9
                ).getInfo()
                mean_val = round((mean_dict.get(cfg["band"], 0) or 0) * cfg.get("scale", 1), 1)
            elif sensor == "MODIS_MOD16":
                img = col.select(cfg["band"]).sum()
                mean_dict = img.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=region, scale=500, maxPixels=1e9
                ).getInfo()
                mean_val = round((mean_dict.get(cfg["band"], 0) or 0) * cfg.get("scale", 0.1), 1)
            else:  # S1_SAR
                img = col.select(cfg["band"]).mean()
                mean_dict = img.reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=region, scale=10, maxPixels=1e9
                ).getInfo()
                mean_val = round(mean_dict.get(cfg["band"], -12.0) or -12.0, 2)

            return {
                "basin_id":    display_id,
                "sensor":      sensor,
                "year":        year,
                "mean":        mean_val,
                "unit":        cfg["unit"],
                "sensor_name": cfg["name"],
                "source":      f"Google Earth Engine — {cfg['collection']}",
                "doi":         cfg.get("doi", ""),
                "status":      "real_gee",
                "lat_centroid": lat,
                "lon_centroid": lon,
            }
        except Exception as e:
            pass  # fall through to synthetic
    
    # Synthetic fallback
    rng = random.Random(hash(display_id + sensor + str(year)) % 2**32)
    sensor_vals = {
        "S1_SAR":     {"mean": round(rng.uniform(-15, -8), 2),  "unit": "dB",       "name": "SAR Backscatter"},
        "GPM_IMERG":  {"mean": round(rng.uniform(50, 2000), 1), "unit": "mm/yr",    "name": "Annual Precipitation"},
        "MODIS_MOD16":{"mean": round(rng.uniform(200, 1200), 1),"unit": "mm/yr",    "name": "Actual Evapotranspiration"},
        "NDWI":       {"mean": round(rng.uniform(-0.3, 0.6), 3),"unit": "index",    "name": "Water Index"},
    }
    sv = sensor_vals.get(sensor, {"mean": 0, "unit": "", "name": sensor})
    
    return {
        "basin_id":   display_id,
        "sensor":     sensor,
        "year":       year,
        "mean":       sv["mean"],
        "unit":       sv["unit"],
        "sensor_name":sv["name"],
        "source":     f"Synthetic (GEE not authenticated) — {GEE_SETUP_GUIDE.split(chr(10))[0]}",
        "status":     "synthetic",
    }
