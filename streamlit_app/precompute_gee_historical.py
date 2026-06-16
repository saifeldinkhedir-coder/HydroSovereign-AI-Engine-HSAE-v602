#!/usr/bin/env python3
"""
HSAE v6.01 — Historical GEE Pre-computation Pipeline
======================================================
Generates yearly satellite data summaries for 2015-2024.
Runs monthly via GitHub Actions (not daily — data doesn't change).
Output: data/gee_historical.json

Sources (same 7 as daily pipeline):
  1. GPM IMERG V07      — daily precip → monthly mean (2000-present)
  2. GRACE-FO MASCON    — TWS anomaly (2018-present)
  3. Sentinel-1 GRD     — SAR VV backscatter (2014-present)
  4. Sentinel-2 SR      — NDWI + NDVI (2015-present)
  5. Open-Meteo SMAP    — soil moisture proxy (1940-present)
  6. GloFAS derived     — discharge from GPM (1979-present)
  7. Open-Meteo ERA5    — temperature (1940-present)
"""

import ee, json, os, datetime, time, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Auth ──────────────────────────────────────────────────────────────────────
SA_KEY   = os.environ.get("GEE_SA_KEY_PATH", "hsae-gee-service.json")
SA_EMAIL = "hsae-gee-service@zinc-arc-484714-j8.iam.gserviceaccount.com"
PROJECT  = "zinc-arc-484714-j8"
ee.Initialize(ee.ServiceAccountCredentials(SA_EMAIL, SA_KEY), project=PROJECT)
print(f"✅ GEE authenticated — project: {PROJECT}")

# ── 26 HSAE Basins (same as daily) ───────────────────────────────────────────
BASINS = {
    "GERD_ETH":     {"bbox":[33,8,38,13],    "lat":10.53,"lon":35.09,  "area_km2":174000,  "runoff_c":0.38},
    "ROS_SDN":      {"bbox":[32,9,37,14],    "lat":11.85,"lon":34.38,  "area_km2":325000,  "runoff_c":0.25},
    "ASWAN_EGY":    {"bbox":[30,21,34,25],   "lat":23.97,"lon":32.87,  "area_km2":2900000, "runoff_c":0.10},
    "KARIBA_ZAM":   {"bbox":[26,-19,31,-13], "lat":-16.52,"lon":28.76, "area_km2":663000,  "runoff_c":0.27},
    "INGA_COD":     {"bbox":[11,-7,15,-3],   "lat":-5.52,"lon":13.58,  "area_km2":3700000, "runoff_c":0.35},
    "KAINJI_NGA":   {"bbox":[2,7,8,14],      "lat":10.40,"lon":4.58,   "area_km2":130000,  "runoff_c":0.18},
    "ATATURK_TUR":  {"bbox":[36,36,41,40],   "lat":37.48,"lon":38.32,  "area_km2":444000,  "runoff_c":0.20},
    "MOSUL_IRQ":    {"bbox":[40,34,45,38],   "lat":36.63,"lon":42.82,  "area_km2":54000,   "runoff_c":0.15},
    "NUREK_TJK":    {"bbox":[67,36,72,41],   "lat":38.38,"lon":69.38,  "area_km2":98000,   "runoff_c":0.32},
    "TOKTO_KGZ":    {"bbox":[70,39,76,44],   "lat":41.78,"lon":72.92,  "area_km2":45000,   "runoff_c":0.28},
    "TARB_PAK":     {"bbox":[70,32,75,37],   "lat":34.08,"lon":72.70,  "area_km2":363000,  "runoff_c":0.32},
    "SUBANS_IND":   {"bbox":[92,25,97,30],   "lat":27.18,"lon":94.25,  "area_km2":195000,  "runoff_c":0.55},
    "FARAKKA_IND":  {"bbox":[85,22,90,27],   "lat":24.82,"lon":87.93,  "area_km2":1100000, "runoff_c":0.38},
    "XAYA_LAO":     {"bbox":[99,17,105,22],  "lat":19.17,"lon":101.93, "area_km2":795000,  "runoff_c":0.45},
    "MYIN_MMR":     {"bbox":[95,23,101,28],  "lat":25.47,"lon":97.53,  "area_km2":280000,  "runoff_c":0.38},
    "3GORGES_CHN":  {"bbox":[109,28,113,33], "lat":30.82,"lon":111.00, "area_km2":1000000, "runoff_c":0.40},
    "IRONGATE_EU":  {"bbox":[19,42,25,47],   "lat":44.68,"lon":22.52,  "area_km2":576000,  "runoff_c":0.38},
    "RHINE_EU":     {"bbox":[6,46,11,52],    "lat":47.68,"lon":8.62,   "area_km2":185000,  "runoff_c":0.42},
    "KAKHOVKA_UKR": {"bbox":[30,44,36,50],   "lat":47.10,"lon":33.37,  "area_km2":504000,  "runoff_c":0.20},
    "AMZ_BRA":      {"bbox":[-55,-6,-48,0],  "lat":-3.12,"lon":-51.77, "area_km2":4600000, "runoff_c":0.52},
    "ITAIPU_BR_PY": {"bbox":[-57,-28,-51,-22],"lat":-25.41,"lon":-54.58,"area_km2":820000, "runoff_c":0.47},
    "GURI_VEN":     {"bbox":[-66,5,-60,11],  "lat":7.76,"lon":-63.00,  "area_km2":440000,  "runoff_c":0.48},
    "HOOVER_USA":   {"bbox":[-117,33,-112,38],"lat":36.01,"lon":-114.73,"area_km2":632000, "runoff_c":0.08},
    "COULEE_USA":   {"bbox":[-122,44,-115,50],"lat":47.96,"lon":-118.98,"area_km2":415000, "runoff_c":0.22},
    "AMISTAD_MEX":  {"bbox":[-104,27,-98,32],"lat":29.45,"lon":-101.07,"area_km2":267000,  "runoff_c":0.06},
    "HUME_AUS":     {"bbox":[144,-39,151,-33],"lat":-36.10,"lon":147.03,"area_km2":15000,  "runoff_c":0.12},
}

# Historical years to cover
YEARS = list(range(2015, 2025))  # 2015-2024

def sg(v):
    try: return float(v) if v is not None else 0.0
    except: return 0.0


def fetch_year_gpm(region, yr):
    """GPM IMERG V07 monthly for a full year."""
    col = (ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
           .filterDate(f"{yr}-01-01", f"{yr+1}-01-01")
           .filterBounds(region).select("precipitation"))
    def mo(m):
        m  = ee.Number(m).add(1)
        d0 = ee.Date.fromYMD(yr, m, 1); d1 = d0.advance(1,"month")
        c  = col.filterDate(d0, d1)
        img= ee.Image(ee.Algorithms.If(c.size().gt(0), c.mean(), ee.Image.constant(0)))
        val= img.reduceRegion(ee.Reducer.mean(), region, 11132, maxPixels=1e9)
        return ee.Feature(None, {"m": d0.format("YYYY-MM"),
                                 "P": ee.Number(val.get("precipitation",0)).multiply(24)})
    feats = ee.FeatureCollection(ee.List.sequence(0,11).map(mo)).getInfo()["features"]
    vals  = [sg(f["properties"]["P"]) for f in feats]
    months= [f["properties"]["m"] for f in feats]
    return {"months":months,"P_mm_day":vals,
            "mean_P":round(sum(vals)/max(len(vals),1),3),
            "source":"NASA/GPM_L3/IMERG_V07","n_months":len(vals),"error":None}


def fetch_year_grace(region, yr):
    """GRACE-FO TWS for a given year."""
    for col_id, band in [
        ("NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI","lwe_thickness"),
        ("NASA/GRACE/MASS_GRIDS_V04/MASCON",    "lwe_thickness"),
        ("NASA/GRACE/MASS_GRIDS/MASCON_CRI",    "lwe_thickness"),
    ]:
        try:
            coll = (ee.ImageCollection(col_id)
                    .filterDate(f"{yr}-01-01",f"{yr+1}-01-01")
                    .filterBounds(region).select(band))
            if coll.size().getInfo() == 0: continue
            def ex(img):
                v = img.reduceRegion(ee.Reducer.mean(),region,55000,maxPixels=1e8).get(band)
                return ee.Feature(None,{"d":img.date().format("YYYY-MM"),"t":v})
            feats = coll.map(ex).getInfo()["features"]
            vals  = [(f["properties"]["d"],sg(f["properties"]["t"]))
                     for f in feats if f["properties"].get("t") is not None]
            tws   = [d[1] for d in vals]
            return {"months":[d[0] for d in vals],"tws_cm":tws,
                    "mean_tws":round(sum(tws)/max(len(tws),1),3),
                    "source":col_id,"n_months":len(tws),"error":None}
        except Exception: continue
    return {"error":"GRACE unavailable","tws_cm":[],"mean_tws":0,"months":[],"n_months":0}


def fetch_year_s1(region, yr):
    """Sentinel-1 GRD monthly VV for a year."""
    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
          .filterDate(f"{yr}-01-01",f"{yr+1}-01-01").filterBounds(region)
          .filter(ee.Filter.eq("instrumentMode","IW"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VV"))
          .select("VV"))
    def mo(m):
        m  = ee.Number(m).add(1)
        d0 = ee.Date.fromYMD(yr, m, 1); d1 = d0.advance(1,"month")
        c  = s1.filterDate(d0, d1)
        img= ee.Image(ee.Algorithms.If(c.size().gt(0), c.mean(), ee.Image.constant(-20)))
        val= img.reduceRegion(ee.Reducer.mean(), region, 100, maxPixels=1e9)
        return ee.Feature(None,{"m":d0.format("YYYY-MM"),"VV":val.get("VV",-20)})
    feats = ee.FeatureCollection(ee.List.sequence(0,11).map(mo)).getInfo()["features"]
    vals  = [sg(f["properties"].get("VV",-20)) for f in feats]
    months= [f["properties"]["m"] for f in feats]
    return {"months":months,"VV_dB":vals,"mean_VV":round(sum(vals)/max(len(vals),1),2),
            "source":"COPERNICUS/S1_GRD","n_months":len(vals),"error":None}


def fetch_year_s2(lat, lon, yr):
    """Sentinel-2 SR monthly NDWI+NDVI for a year."""
    point  = ee.Geometry.Point([lon, lat])
    buffer = point.buffer(10000)
    results = []
    for m in range(1, 13):
        d0 = f"{yr}-{m:02d}-01"
        d1 = f"{yr}-{m+1:02d}-01" if m < 12 else f"{yr+1}-01-01"
        try:
            col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                   .filterDate(d0, d1).filterBounds(buffer).select(["B3","B4","B8"]))
            if col.size().getInfo() == 0: continue
            med  = col.median().divide(10000)
            ndwi = med.normalizedDifference(["B3","B8"]).rename("NDWI")
            ndvi = med.normalizedDifference(["B8","B4"]).rename("NDVI")
            raw  = ndwi.addBands(ndvi).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=buffer,
                scale=30, maxPixels=1e7, bestEffort=True).getInfo()
            nw = raw.get("NDWI"); nv = raw.get("NDVI")
            if nw is not None and nw != 0.0:
                results.append((f"{yr}-{m:02d}", float(nw), float(nv) if nv else 0.3))
        except Exception: continue
    if not results:
        return {"error":"No S2 coverage","NDWI":[],"NDVI":[],"mean_NDWI":0,"mean_NDVI":0,
                "months":[],"n_months":0}
    ndwi = [r[1] for r in results]; ndvi = [r[2] for r in results]
    return {"months":[r[0] for r in results],"NDWI":ndwi,"NDVI":ndvi,
            "mean_NDWI":round(sum(ndwi)/len(ndwi),4),"mean_NDVI":round(sum(ndvi)/len(ndvi),4),
            "source":"COPERNICUS/S2_SR_HARMONIZED","n_months":len(results),"error":None}


def fetch_year_openmeteo(lat, lon, yr):
    """Open-Meteo ERA5 — full year temperature + precipitation + SM."""
    url = (f"https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={lat}&longitude={lon}"
           f"&start_date={yr}-01-01&end_date={yr}-12-31"
           f"&daily=temperature_2m_mean,precipitation_sum,soil_moisture_0_to_7cm_mean"
           f"&timezone=UTC")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.loads(r.read())
            daily = d.get("daily",{}); times = daily.get("time",[])
            out = {}
            for var in ["temperature_2m_mean","precipitation_sum","soil_moisture_0_to_7cm_mean"]:
                vals = daily.get(var,[])
                monthly = {}
                for i, t in enumerate(times):
                    mo = t[:7]; v = vals[i] if i < len(vals) else None
                    if v is not None: monthly.setdefault(mo,[]).append(float(v))
                mos = sorted(monthly)
                out[var] = {"months":mos,
                            "monthly":[round(sum(monthly[m])/len(monthly[m]),4) for m in mos],
                            "mean":round(sum(sum(monthly[m]) for m in mos)/
                                         max(sum(len(monthly[m]) for m in mos),1),4)}
            return out
        except Exception as e:
            if attempt == 3: raise
            time.sleep(5*(attempt+1))


def process_basin_year(basin_id, cfg, yr):
    """Fetch all 7 sources for one basin for one year."""
    t0     = time.time()
    lat    = cfg["lat"]; lon = cfg["lon"]
    rc     = cfg["runoff_c"]; area = cfg["area_km2"]
    region = ee.Geometry.Rectangle(cfg["bbox"])
    result = {"basin_id":basin_id,"year":yr,
              "fetched_at":datetime.datetime.utcnow().isoformat()}

    try:    result["gpm"]      = fetch_year_gpm(region, yr)
    except Exception as e: result["gpm"] = {"error":str(e),"P_mm_day":[],"mean_P":0,"months":[],"n_months":0}

    try:    result["grace"]    = fetch_year_grace(region, yr)
    except Exception as e: result["grace"] = {"error":str(e),"tws_cm":[],"mean_tws":0,"months":[],"n_months":0}

    try:    result["sentinel1"]= fetch_year_s1(region, yr)
    except Exception as e: result["sentinel1"] = {"error":str(e),"VV_dB":[],"mean_VV":-20,"months":[],"n_months":0}

    try:    result["sentinel2"]= fetch_year_s2(lat, lon, yr)
    except Exception as e: result["sentinel2"] = {"error":str(e),"NDWI":[],"NDVI":[],"mean_NDWI":0,"mean_NDVI":0,"months":[],"n_months":0}

    try:
        om  = fetch_year_openmeteo(lat, lon, yr)
        T   = om["temperature_2m_mean"]; P = om["precipitation_sum"]; SM = om["soil_moisture_0_to_7cm_mean"]
        result["temperature"] = {"months":T["months"],"T_C":T["monthly"],"mean_T":T["mean"],
                                  "source":"Open-Meteo ERA5","n_months":len(T["months"]),"error":None}
        result["smap"]        = {"months":SM["months"],"sm_m3m3":SM["monthly"],"mean_sm":SM["mean"],
                                  "source":"Open-Meteo SMAP-proxy","n_months":len(SM["months"]),"error":None}
        if not result["gpm"].get("P_mm_day"):
            result["gpm"] = {"months":P["months"],"P_mm_day":P["monthly"],"mean_P":P["mean"],
                              "source":"Open-Meteo ERA5 backup","n_months":len(P["months"]),"error":None}
    except Exception as e:
        result["temperature"] = {"error":str(e),"T_C":[],"mean_T":25.0,"months":[],"n_months":0}
        result["smap"]        = {"error":str(e),"sm_m3m3":[],"mean_sm":0.2,"months":[],"n_months":0}

    P_vals = result["gpm"].get("P_mm_day",[])
    if P_vals:
        Q = [round(p*rc*area/86.4,1) for p in P_vals]
        result["glofas"] = {"Q_m3s":Q,"mean_Q":round(sum(Q)/max(len(Q),1),1),
                             "source":"Derived: GPM × runoff_c × area",
                             "n_months":len(Q),"months":result["gpm"]["months"],"error":None}
    else:
        result["glofas"] = {"error":"No GPM","Q_m3s":[],"mean_Q":0,"months":[],"n_months":0}

    elapsed = time.time()-t0
    s = {k:("✅" if result.get(k,{}).get("n_months",0)>0 else "❌")
         for k in ["gpm","grace","sentinel1","sentinel2","smap","glofas","temperature"]}
    print(f"  {yr} {basin_id:<18} {s['gpm']}GPM {s['grace']}GRC {s['sentinel1']}S1 "
          f"{s['sentinel2']}S2 {s['smap']}SM {s['glofas']}Q {s['temperature']}T ({elapsed:.0f}s)")
    return basin_id, yr, result


# ── Main: Load existing + update missing years ────────────────────────────────
hist_path = Path("data/gee_historical.json")
if hist_path.exists():
    existing = json.loads(hist_path.read_text())
    print(f"📂 Loaded existing gee_historical.json: {len(existing.get('years',{}))} years")
else:
    existing = {"schema_version":"1.0","updated_at":"","years":{},"basins_per_year":{}}
    print("📂 Creating new gee_historical.json")

# Only fetch years that are missing or incomplete
todo = []
for yr in YEARS:
    yr_key = str(yr)
    existing_yr = existing.get("years",{}).get(yr_key,{})
    basins_done = len(existing_yr)
    if basins_done < len(BASINS):
        todo.append(yr)
        print(f"  Year {yr}: {basins_done}/{len(BASINS)} basins — will fetch")
    else:
        print(f"  Year {yr}: {basins_done}/{len(BASINS)} basins — already complete ✅")

if not todo:
    print("\n✅ All years complete — nothing to fetch")
else:
    print(f"\n⚡ Fetching {len(todo)} years × {len(BASINS)} basins in parallel (8 workers)...")
    t0_total = time.time()

    tasks = [(bid, cfg, yr) for yr in todo for bid, cfg in BASINS.items()]

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(process_basin_year, bid, cfg, yr): (bid, yr)
                   for bid, cfg, yr in tasks}
        for fut in as_completed(futures):
            bid, yr, res = fut.result()
            yr_key = str(yr)
            if yr_key not in existing["years"]:
                existing["years"][yr_key] = {}
            existing["years"][yr_key][bid] = res

    elapsed_total = time.time()-t0_total
    print(f"\n⚡ Done in {elapsed_total:.0f}s ({elapsed_total/60:.1f} min)")

existing["updated_at"] = datetime.datetime.utcnow().isoformat()
existing["schema_version"] = "1.0"
existing["n_years"] = len(existing["years"])
existing["n_basins"] = len(BASINS)
existing["years_covered"] = sorted(existing["years"].keys())

Path("data").mkdir(exist_ok=True)
hist_path.write_text(json.dumps(existing, indent=2))

print(f"\n✅ Saved data/gee_historical.json")
print(f"   Years: {existing['years_covered']}")
print(f"   Basins per year: {len(BASINS)}")

# Summary
print(f"\n{'='*55}")
for yr_key in sorted(existing["years"].keys()):
    yr_data = existing["years"][yr_key]
    srcs = ["gpm","grace","sentinel1","sentinel2","smap","glofas","temperature"]
    ok_counts = {s: sum(1 for bd in yr_data.values() if bd.get(s,{}).get("n_months",0)>0)
                 for s in srcs}
    icons = {s: "✅" if ok_counts[s]==len(BASINS) else f"⚠️{ok_counts[s]}" for s in srcs}
    print(f"  {yr_key}: {icons['gpm']}GPM {icons['grace']}GRC {icons['sentinel1']}S1 "
          f"{icons['sentinel2']}S2 {icons['smap']}SM {icons['glofas']}Q {icons['temperature']}T")
print(f"{'='*55}")
