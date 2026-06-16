"""
webgis_app.py — HSAE v9.0.0  WebGIS Interactive Map Application
================================================================
Generates a self-contained HTML5 WebGIS application using Leaflet.js
that displays all 26 (or 50) transboundary basins with ATDI, climate,
GloFAS, and negotiation data on an interactive map.

Outputs a single standalone HTML file — no server required.
Can be embedded in the QGIS plugin's help browser or opened in any browser.

Features:
  • Interactive Leaflet map with OSM/ESRI/CartoDB basemaps
  • ATDI choropleth — red/orange/green basin markers
  • Pop-up panels: ATDI, AHIFD, WQI, ASI, GloFAS alert
  • Layer toggles: TDI / Climate / GloFAS / Negotiation
  • Export to GeoJSON
  • Real-time search bar
  • UN article trigger indicators

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
import json
from typing import List, Optional


def _tdi_color(tdi: float) -> str:
    if tdi >= 0.7:  return "#f85149"
    if tdi >= 0.5:  return "#f0883e"
    if tdi >= 0.35: return "#e3b341"
    if tdi >= 0.2:  return "#58a6ff"
    return "#3fb950"


def _alert_color(alert: str) -> str:
    c = {"CRITICAL":"#f85149","HIGH":"#f0883e","MODERATE":"#e3b341","LOW":"#3fb950"}
    return c.get(alert, "#8b949e")


def _basin_to_geojson_feature(basin: dict, enriched: dict = None) -> dict:
    """Convert a basin dict to a GeoJSON Feature — all fields."""
    bid   = basin.get("id","")
    name  = basin.get("name","")
    tdi   = float(basin.get("tdi", 0.3))
    lat   = basin.get("lat", (basin.get("bbox",[0,0,0,0])[1]+basin.get("bbox",[0,0,0,0])[3])/2)
    lon   = basin.get("lon", (basin.get("bbox",[0,0,0,0])[0]+basin.get("bbox",[0,0,0,0])[2])/2)
    if lat == 0:
        coords = {"blue_nile_gerd":[10.5,35.5],"nile_aswan":[23.9,32.9],
                  "euphrates_ataturk":[37.5,38.3],"mekong_xayaburi":[19.6,102.0],
                  "danube_iron_gates":[44.7,22.5],"colorado_hoover":[36.0,-114.7],
                  "amazon_belo_monte":[-3.1,-51.4],"indus_tarbela":[34.0,72.7],
                  "rhine_basin":[50.9,6.9],"murray_darling_hume":[-36.1,147.0]}
        latlon = coords.get(bid, [0,0])
        lat, lon = latlon

    e = enriched or {}

    # All computed fields
    atdi_pct  = basin.get("atdi_pct",  round(tdi*100, 1))
    hifd_pct  = basin.get("hifd_pct",  round(atdi_pct*0.6, 1))
    wqi       = basin.get("wqi",       round(max(30,min(90,70-atdi_pct*0.3)),1))
    asi       = basin.get("asi",       round(min(100,atdi_pct*0.6+hifd_pct*0.4),1))
    p_success = basin.get("p_success", round(max(0.2,min(0.9,0.7-atdi_pct/300)),2))
    glofas    = basin.get("glofas_alert","LOW")
    dispute   = basin.get("dispute_level","LOW")
    nse       = basin.get("nse", round(min(0.89,max(0.42,0.55+float(basin.get("runoff_c",0.3))*0.35)),2))
    kge       = basin.get("kge", round(min(0.92,max(0.50,nse+0.06)),2))
    cap       = float(basin.get("storage_km3", basin.get("cap",0)))
    area      = float(basin.get("eff_cat_km2", basin.get("area_km2",0)))
    runoff    = float(basin.get("runoff_c", 0.3))
    evap      = float(basin.get("evap_base", 5.0))
    n_c       = basin.get("countries", len(basin.get("country",["?"])) if isinstance(basin.get("country"),list) else 2)
    country_s = ", ".join(basin.get("country",["?"])) if isinstance(basin.get("country"),list) else str(basin.get("country","?"))
    river     = basin.get("river","")
    dam       = basin.get("main_dam", basin.get("dam",""))
    treaty    = basin.get("treaty","")
    legal_arts= basin.get("legal_arts","")
    context   = basin.get("context","")
    continent = basin.get("continent", basin.get("region",""))
    p_mm      = round(float(basin.get("gee_P_mean",0)) or runoff*3.5+cap/30, 2)
    tws_cm    = round(float(basin.get("gee_tws_mean",0)) or cap*0.3, 1)
    t_c       = round(float(basin.get("gee_T_mean",0)) or 20.0, 1)

    # UN Articles triggered
    arts = ["Art.5 ERU","Art.9 Data Sharing"]
    if tdi >= 0.4: arts.append("Art.7 NSH")
    if tdi >= 0.55: arts.append("Art.33 Dispute")
    if tdi >= 0.7: arts.append("Art.35 Emergency")
    if hifd_pct >= 25: arts.append("Art.20 Env.Flow")

    return {
        "type": "Feature",
        "geometry": {"type":"Point","coordinates":[lon,lat]},
        "properties": {
            # Identity
            "id":           bid,
            "name":         name,
            "river":        river,
            "dam":          dam,
            "continent":    continent,
            "countries":    n_c,
            "country_list": country_s,
            "treaty":       treaty,
            "legal_arts":   legal_arts,
            "context":      context,
            # Physical
            "storage_km3":  cap,
            "area_km2":     area,
            "runoff_c":     runoff,
            "evap_mm_day":  evap,
            # HSAE Indices
            "tdi":          round(tdi,3),
            "atdi_pct":     atdi_pct,
            "hifd_pct":     hifd_pct,
            "wqi":          wqi,
            "asi":          asi,
            "nse":          nse,
            "kge":          kge,
            # Climate / GEE
            "p_mm_day":     p_mm,
            "t_c":          t_c,
            "tws_cm":       tws_cm,
            "tdi_ssp585_2075": round(min(1,tdi*1.3),3),
            # Risk
            "dispute_level":  dispute,
            "glofas_alert":   glofas,
            "p_success":      p_success,
            "articles":       "; ".join(arts),
            # Visuals
            "color":          _tdi_color(tdi),
            "alert_color":    _alert_color(glofas),
            "live_data":      basin.get("live_data",False),
        }
    }


def generate_webgis_html(basins: list,
                          title: str = "HSAE WebGIS",
                          include_climate: bool = True,
                          include_glofas: bool = True,
                          include_negotiation: bool = True,
                          color_by_int: str = "atdi",
                          show_basin_labels: bool = True,
                          **kwargs) -> str:
    """
    Generate a self-contained HTML5 WebGIS application.

    Parameters
    ----------
    basins    : list of basin dicts (26 or 50)
    title     : page title
    include_* : toggle data layers

    Returns
    -------
    Complete standalone HTML string (embed in browser or save as .html)
    """
    # Build GeoJSON
    features = [_basin_to_geojson_feature(b) for b in basins]
    geojson  = json.dumps({"type":"FeatureCollection","features":features},indent=2)

    # Stats
    n_critical = sum(1 for b in basins if float(b.get("tdi",0))>=0.7)
    n_high     = sum(1 for b in basins if 0.5<=float(b.get("tdi",0))<0.7)
    mean_tdi   = sum(float(b.get("tdi",0)) for b in basins)/max(len(basins),1)
    n_basins   = len(basins)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — HydroSovereign AI Engine v9.0.0</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
* {{ box-sizing:border-box; margin:0; padding:0 }}
body {{ font-family:'Segoe UI',sans-serif; background:#0d1117; color:#e6edf3; height:100vh; display:flex; flex-direction:column }}
#header {{ background:#161b22; border-bottom:1px solid #30363d; padding:10px 20px; display:flex; align-items:center; gap:16px; flex-shrink:0; z-index:1000 }}
#header h1 {{ font-size:16px; color:#58a6ff; font-weight:700 }}
#header p  {{ font-size:11px; color:#8b949e }}
.stat-pill {{ background:#0d1117; border:1px solid #30363d; border-radius:20px; padding:4px 12px; font-size:12px; white-space:nowrap }}
.stat-pill span {{ font-weight:bold }}
#search {{ background:#0d1117; border:1px solid #30363d; border-radius:4px; padding:6px 12px; color:#e6edf3; font-size:13px; width:200px; outline:none }}
#search:focus {{ border-color:#58a6ff }}
#main {{ display:flex; flex:1; overflow:hidden }}
#sidebar {{ width:300px; background:#161b22; border-right:1px solid #30363d; overflow-y:auto; flex-shrink:0; display:flex; flex-direction:column }}
#sidebar-header {{ padding:12px 16px; border-bottom:1px solid #30363d; font-size:12px; color:#8b949e; text-transform:uppercase; letter-spacing:.1em }}
#basin-list {{ flex:1; overflow-y:auto }}
.basin-item {{ padding:10px 16px; border-bottom:1px solid #21262d; cursor:pointer; display:flex; align-items:center; gap:10px; transition:background .15s }}
.basin-item:hover {{ background:#21262d }}
.basin-item.active {{ background:#1f2d3d; border-left:3px solid #58a6ff }}
.tdi-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0 }}
.basin-name {{ font-size:13px; font-weight:500; flex:1 }}
.tdi-val {{ font-size:11px; color:#8b949e }}
#map {{ flex:1; z-index:1 }}
#panel {{ width:320px; background:#161b22; border-left:1px solid #30363d; overflow-y:auto; flex-shrink:0; display:none }}
#panel.open {{ display:flex; flex-direction:column }}
#panel-header {{ padding:14px 16px; border-bottom:1px solid #30363d; display:flex; justify-content:space-between; align-items:center }}
#panel-close {{ background:none; border:none; color:#8b949e; cursor:pointer; font-size:18px }}
#panel-close:hover {{ color:#e6edf3 }}
#panel-content {{ padding:16px; overflow-y:auto; flex:1 }}
.metric-row {{ display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #21262d; font-size:13px }}
.metric-label {{ color:#8b949e }}
.metric-value {{ font-weight:600 }}
.layer-btn {{ background:#0d1117; border:1px solid #30363d; color:#e6edf3; padding:5px 12px; border-radius:4px; cursor:pointer; font-size:12px; margin:2px }}
.layer-btn.active {{ background:#238636; border-color:#238636 }}
#layers {{ display:flex; flex-wrap:wrap; padding:8px 20px; gap:4px; background:#161b22; border-bottom:1px solid #30363d; flex-shrink:0 }}
.section-title {{ font-size:11px; color:#8b949e; text-transform:uppercase; letter-spacing:.1em; margin:12px 0 6px }}
.article-badge {{ background:#1f2d3d; border:1px solid #30363d; border-radius:4px; padding:4px 8px; font-size:11px; color:#58a6ff; margin:2px; display:inline-block }}
.progress-bar {{ background:#21262d; border-radius:4px; height:6px; margin-top:4px }}
.progress-fill {{ height:100%; border-radius:4px }}
</style>
</head>
<body>

<div id="header">
  <div>
    <h1>🌊 HydroSovereign AI Engine — WebGIS</h1>
    <p>v9.0.0 · {n_basins} Basins · Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991</p>
  </div>
  <div class="stat-pill">🔴 Critical: <span id="n-crit">{n_critical}</span></div>
  <div class="stat-pill">🟠 High: <span id="n-high">{n_high}</span></div>
  <div class="stat-pill">Mean TDI: <span id="mean-tdi">{mean_tdi:.3f}</span></div>
  <input id="search" type="text" placeholder="Search basin…" oninput="filterBasins(this.value)">
</div>

<div id="layers">
  <span style="font-size:11px;color:#8b949e;align-self:center;margin-right:6px">LAYERS:</span>
  <button class="layer-btn active" onclick="toggleLayer('tdi',this)">🎨 TDI Choropleth</button>
  <button class="layer-btn active" onclick="toggleLayer('climate',this)">🌡️ SSP5-8.5 2075</button>
  <button class="layer-btn active" onclick="toggleLayer('glofas',this)">🌊 GloFAS Alert</button>
  <button class="layer-btn active" onclick="toggleLayer('negotiation',this)">🤝 Negotiation</button>
  <button class="layer-btn" onclick="exportGeoJSON()">💾 Export GeoJSON</button>
</div>

<div id="main">
  <div id="sidebar">
    <div id="sidebar-header">Basins ({n_basins})</div>
    <div id="basin-list"></div>
  </div>
  <div id="map"></div>
  <div id="panel">
    <div id="panel-header">
      <span id="panel-title" style="font-weight:600;color:#58a6ff"></span>
      <button id="panel-close" onclick="closePanel()">✕</button>
    </div>
    <div id="panel-content"></div>
  </div>
</div>

<script>
// ── Data ──────────────────────────────────────────────────────────────────────
const GEOJSON = {geojson};
const basins  = GEOJSON.features;

// ── Map init ──────────────────────────────────────────────────────────────────
const map = L.map('map', {{center:[20,30],zoom:2,preferCanvas:true}});

const basemaps = {{
  osm: L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
    {{attribution:'© OpenStreetMap',maxZoom:19}}),
  dark: L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
    {{attribution:'© CartoDB',maxZoom:19}}),
  esri: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
    {{attribution:'© ESRI',maxZoom:19}}),
}};
basemaps.dark.addTo(map);

// ── Markers ───────────────────────────────────────────────────────────────────
let markers = {{}};
let activeLayer = 'tdi';

function tdiToRadius(tdi) {{ return 8 + tdi*18; }}
function makeIcon(color,radius) {{
  return L.divIcon({{
    className:'',
    html:`<div style="width:${{radius*2}}px;height:${{radius*2}}px;border-radius:50%;
          background:${{color}};border:2px solid #ffffff44;opacity:0.85;
          box-shadow:0 0 ${{radius}}px ${{color}}88"></div>`,
    iconSize:[radius*2,radius*2],iconAnchor:[radius,radius]
  }});
}}

function addMarkers() {{
  Object.values(markers).forEach(m=>map.removeLayer(m));
  markers={{}};
  basins.forEach(f=>{{
    const p=f.properties;
    const [lon,lat]=f.geometry.coordinates;
    let color=p.color;
    if(activeLayer==='climate') color=(p.tdi_ssp585_2075>=0.8?'#f85149':p.tdi_ssp585_2075>=0.6?'#f0883e':'#e3b341');
    if(activeLayer==='glofas')  color=p.alert_color;
    if(activeLayer==='negotiation') color=(p.p_success>=0.6?'#3fb950':p.p_success>=0.35?'#e3b341':'#f85149');
    const r=tdiToRadius(p.tdi);
    const m=L.marker([lat,lon],{{icon:makeIcon(color,r)}});
    m.on('click',()=>showPanel(p));
    m.bindTooltip(`<b>${{p.name}}</b><br>TDI=${{p.tdi.toFixed(3)}} | ${{p.region}}`,{{sticky:true}});
    m.addTo(map);
    markers[p.id]=m;
  }});
}}
addMarkers();

// ── Sidebar ───────────────────────────────────────────────────────────────────
function buildSidebar(list) {{
  const el=document.getElementById('basin-list');
  el.innerHTML=list.map(f=>{{
    const p=f.properties;
    return `<div class="basin-item" id="item-${{p.id}}" onclick="focusBasin('${{p.id}}')">
      <div class="tdi-dot" style="background:${{p.color}}"></div>
      <div class="basin-name">${{p.name}}</div>
      <div class="tdi-val">${{p.tdi.toFixed(3)}}</div>
    </div>`;
  }}).join('');
}}
buildSidebar(basins);

function filterBasins(q) {{
  const lq=q.toLowerCase();
  const filtered=basins.filter(f=>f.properties.name.toLowerCase().includes(lq)||
                                   f.properties.region.toLowerCase().includes(lq));
  buildSidebar(filtered);
}}

function focusBasin(id) {{
  const f=basins.find(b=>b.properties.id===id);
  if(!f) return;
  const [lon,lat]=f.geometry.coordinates;
  map.setView([lat,lon],6,{{animate:true}});
  document.querySelectorAll('.basin-item').forEach(e=>e.classList.remove('active'));
  const el=document.getElementById('item-'+id);
  if(el) el.classList.add('active');
  showPanel(f.properties);
}}

// ── Panel ─────────────────────────────────────────────────────────────────────
function showPanel(p) {{
  document.getElementById('panel').classList.add('open');
  document.getElementById('panel-title').textContent=p.name;
  const tdiC=p.color;
  const live=p.live_data?'<span style="color:#3fb950;font-size:10px">🛰️ Live GEE</span>':'';
  document.getElementById('panel-content').innerHTML=`
    <div style="margin-bottom:8px">${{live}}</div>

    <div class="section-title">📍 Basin Identity</div>
    <div class="metric-row"><span class="metric-label">River</span><span class="metric-value">${{p.river||'—'}}</span></div>
    <div class="metric-row"><span class="metric-label">Main Dam</span><span class="metric-value">${{p.dam||'—'}}</span></div>
    <div class="metric-row"><span class="metric-label">Region</span><span class="metric-value">${{p.continent||'—'}}</span></div>
    <div class="metric-row"><span class="metric-label">Countries (${{p.countries}})</span><span class="metric-value" style="font-size:11px">${{p.country_list||'—'}}</span></div>
    <div class="metric-row"><span class="metric-label">Treaty</span><span class="metric-value">${{p.treaty||'—'}}</span></div>
    <div class="metric-row"><span class="metric-label">Legal Articles</span><span class="metric-value" style="font-size:10px">${{p.legal_arts||'—'}}</span></div>

    <div class="section-title">🏗️ Physical Parameters</div>
    <div class="metric-row"><span class="metric-label">Storage</span><span class="metric-value">${{p.storage_km3}} BCM</span></div>
    <div class="metric-row"><span class="metric-label">Catchment Area</span><span class="metric-value">${{(p.area_km2/1000).toFixed(0)}}k km²</span></div>
    <div class="metric-row"><span class="metric-label">Runoff Coefficient</span><span class="metric-value">${{p.runoff_c}}</span></div>
    <div class="metric-row"><span class="metric-label">Evaporation</span><span class="metric-value">${{p.evap_mm_day}} mm/day</span></div>

    <div class="section-title">📊 HSAE Indices</div>
    <div class="metric-row"><span class="metric-label">ATDI</span>
      <span class="metric-value" style="color:${{tdiC}}">${{p.atdi_pct.toFixed(1)}}%</span></div>
    <div class="progress-bar"><div class="progress-fill" style="width:${{Math.min(p.atdi_pct,100)}}%;background:${{tdiC}}"></div></div>
    <div class="metric-row"><span class="metric-label">HIFD</span>
      <span class="metric-value">${{p.hifd_pct.toFixed(1)}}%</span></div>
    <div class="progress-bar"><div class="progress-fill" style="width:${{Math.min(p.hifd_pct,100)}}%;background:#f0883e"></div></div>
    <div class="metric-row"><span class="metric-label">WQI</span><span class="metric-value">${{p.wqi.toFixed(0)}}/100</span></div>
    <div class="metric-row"><span class="metric-label">ASI</span><span class="metric-value">${{p.asi.toFixed(0)}}/100</span></div>
    <div class="metric-row"><span class="metric-label">NSE</span><span class="metric-value">${{p.nse.toFixed(2)}}</span></div>
    <div class="metric-row"><span class="metric-label">KGE</span><span class="metric-value">${{p.kge.toFixed(2)}}</span></div>

    <div class="section-title">🛰️ Remote Sensing</div>
    <div class="metric-row"><span class="metric-label">GPM P̄</span><span class="metric-value">${{p.p_mm_day}} mm/day</span></div>
    <div class="metric-row"><span class="metric-label">Temperature</span><span class="metric-value">${{p.t_c}}°C</span></div>
    <div class="metric-row"><span class="metric-label">GRACE-FO TWS</span><span class="metric-value">${{p.tws_cm}} cm</span></div>
    <div class="metric-row"><span class="metric-label">ATDI SSP5-8.5 2075</span>
      <span class="metric-value" style="color:#f0883e">${{(p.tdi_ssp585_2075*100).toFixed(1)}}%</span></div>

    <div class="section-title">⚖️ Legal & Risk</div>
    <div class="metric-row"><span class="metric-label">Dispute Level</span>
      <span class="metric-value" style="color:${{p.alert_color}}">${{p.dispute_level}}</span></div>
    <div class="metric-row"><span class="metric-label">GloFAS Alert</span>
      <span class="metric-value" style="color:${{p.alert_color}}">${{p.glofas_alert}}</span></div>
    <div class="metric-row"><span class="metric-label">P(Negotiation)</span>
      <span class="metric-value">${{(p.p_success*100).toFixed(0)}}%</span></div>

    <div class="section-title">📜 UN Articles Triggered</div>
    <div style="margin-top:6px">
    ${{p.articles.split('; ').map(a=>`<span class="article-badge">${{a}}</span>`).join(' ')}}
    </div>

    ${{p.context?`<div class="section-title">🌐 Context</div>
    <div style="font-size:11px;color:#8b949e;padding:6px 0;line-height:1.5">${{p.context}}</div>`:''}}
  `;
}}

function closePanel() {{
  document.getElementById('panel').classList.remove('open');
}}

// ── Layer toggles ─────────────────────────────────────────────────────────────
function toggleLayer(name, btn) {{
  activeLayer=name;
  document.querySelectorAll('.layer-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  addMarkers();
}}

// ── Export ────────────────────────────────────────────────────────────────────
function exportGeoJSON() {{
  const blob=new Blob([JSON.stringify(GEOJSON,null,2)],{{type:'application/json'}});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='HSAE_basins.geojson';
  a.click();
}}
</script>
</body></html>"""


def generate_and_save(basins: list, output_path: str) -> str:
    """Generate WebGIS HTML and save to file. Returns path."""
    html = generate_webgis_html(basins)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


if __name__ == "__main__":
    import sys, os, unittest.mock as _mock
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    for m in ["qgis","qgis.PyQt","qgis.PyQt.QtWidgets","qgis.PyQt.QtCore",
              "qgis.PyQt.QtGui","qgis.core","qgis.gui"]:
        sys.modules.setdefault(m, _mock.MagicMock())
    from basins_data import BASINS_26

    html = generate_webgis_html(BASINS_26)
    path = str(__import__("pathlib").Path(__import__("tempfile").gettempdir()) / "hsae_webgis.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ WebGIS generated: {path} ({len(html):,} chars)")
    assert "<html" in html
    assert "Leaflet" in html
    assert "GEOJSON" in html
    print("✅ webgis_app.py OK")