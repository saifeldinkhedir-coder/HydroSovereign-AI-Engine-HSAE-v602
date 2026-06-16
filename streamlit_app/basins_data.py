"""
basins_data.py — HSAE v6.0 Complete Basin Registry
====================================================
26 transboundary basins — ALL fields complete.
Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

BASINS_26 = [
    # ── AFRICA ──────────────────────────────────────────────────────────────
    {"id":"blue_nile_gerd","name":"Blue Nile – GERD","region":"Africa","lat":11.21,"lon":35.09,
     "bbox":[33.0,8.0,38.5,15.0],"tdi":0.72,"country_up":"Ethiopia","country_dn":"Sudan / Egypt",
     "n_countries":3,"dam":"Grand Ethiopian Renaissance Dam (GERD)","storage_bcm":74.0,
     "area_km2":325000,"flow_mcm":50000,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.10","Art.33"],
     "notes":"Most contested dam in Africa; AU-mediated talks ongoing"},

    {"id":"nile_roseires","name":"Nile – Roseires","region":"Africa","lat":11.85,"lon":34.38,
     "bbox":[32.0,9.0,37.0,15.0],"tdi":0.65,"country_up":"Ethiopia","country_dn":"Sudan",
     "n_countries":2,"dam":"Roseires Dam","storage_bcm":3.0,
     "area_km2":187000,"flow_mcm":48000,"dispute_level":"MEDIUM",
     "un_articles":["Art.5","Art.7","Art.9"],"notes":"Blue Nile at Sudan entry; seasonal flood risk"},

    {"id":"nile_aswan","name":"Nile – Aswan","region":"Africa","lat":23.97,"lon":32.88,
     "bbox":[30.0,20.0,36.0,27.0],"tdi":0.68,"country_up":"Sudan / Ethiopia","country_dn":"Egypt",
     "n_countries":3,"dam":"Aswan High Dam","storage_bcm":162.0,
     "area_km2":2870000,"flow_mcm":84000,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.33"],"notes":"1959 Treaty challenged by GERD"},

    {"id":"zambezi_kariba","name":"Zambezi – Kariba","region":"Africa","lat":-16.52,"lon":28.77,
     "bbox":[24.0,-20.0,34.0,-12.0],"tdi":0.45,"country_up":"Zambia","country_dn":"Zimbabwe",
     "n_countries":2,"dam":"Kariba Dam","storage_bcm":180.6,
     "area_km2":1330000,"flow_mcm":98000,"dispute_level":"MEDIUM",
     "un_articles":["Art.5","Art.7","Art.8"],"notes":"World's largest reservoir by volume"},

    {"id":"congo_inga","name":"Congo – Inga","region":"Africa","lat":-5.52,"lon":13.58,
     "bbox":[11.0,-8.0,16.0,-3.0],"tdi":0.22,"country_up":"DRC","country_dn":"DRC / Congo",
     "n_countries":2,"dam":"Inga Falls (proposed Grand Inga)","storage_bcm":45.0,
     "area_km2":3680000,"flow_mcm":1300000,"dispute_level":"LOW",
     "un_articles":["Art.5","Art.6"],"notes":"Highest discharge in Africa"},

    {"id":"niger_kainji","name":"Niger – Kainji","region":"Africa","lat":10.40,"lon":4.57,
     "bbox":[2.0,7.0,8.0,14.0],"tdi":0.38,"country_up":"Guinea / Mali","country_dn":"Nigeria",
     "n_countries":9,"dam":"Kainji Dam","storage_bcm":15.0,
     "area_km2":2090000,"flow_mcm":180000,"dispute_level":"LOW",
     "un_articles":["Art.5","Art.6","Art.7"],"notes":"Niger Basin Authority coordinates 9 states"},

    # ── MIDDLE EAST ──────────────────────────────────────────────────────────
    {"id":"euphrates_ataturk","name":"Euphrates – Atatürk","region":"Middle East","lat":37.48,"lon":38.32,
     "bbox":[36.0,35.0,42.0,40.0],"tdi":0.61,"country_up":"Turkey","country_dn":"Syria / Iraq",
     "n_countries":3,"dam":"Atatürk Dam","storage_bcm":48.7,
     "area_km2":444000,"flow_mcm":31800,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.33"],"notes":"GAP project; Turkey controls 90% headwaters"},

    {"id":"tigris_mosul","name":"Tigris – Mosul","region":"Middle East","lat":36.63,"lon":42.82,
     "bbox":[40.0,33.0,46.0,38.0],"tdi":0.57,"country_up":"Turkey","country_dn":"Iraq / Syria",
     "n_countries":3,"dam":"Mosul Dam","storage_bcm":11.1,
     "area_km2":473000,"flow_mcm":21200,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.10"],"notes":"Dam safety risk; Turkish dams reduce flow"},

    # ── CENTRAL ASIA ─────────────────────────────────────────────────────────
    {"id":"amu_darya_nurek","name":"Amu Darya – Nurek","region":"Central Asia","lat":38.38,"lon":69.42,
     "bbox":[66.0,35.0,72.0,41.0],"tdi":0.63,"country_up":"Tajikistan","country_dn":"Uzbekistan / Turkmenistan",
     "n_countries":5,"dam":"Nurek Dam","storage_bcm":10.5,
     "area_km2":534739,"flow_mcm":79000,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.33"],"notes":"Aral Sea basin; ICWC coordinates allocation"},

    {"id":"syr_darya_toktogul","name":"Syr Darya – Toktogul","region":"Central Asia","lat":41.78,"lon":72.83,
     "bbox":[70.0,38.0,76.0,44.0],"tdi":0.59,"country_up":"Kyrgyzstan","country_dn":"Kazakhstan / Uzbekistan",
     "n_countries":4,"dam":"Toktogul Reservoir","storage_bcm":19.5,
     "area_km2":219000,"flow_mcm":37000,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9"],"notes":"Energy vs irrigation conflict; winter release disputes"},

    # ── ASIA ─────────────────────────────────────────────────────────────────
    {"id":"mekong_xayaburi","name":"Mekong – Xayaburi","region":"Asia","lat":19.16,"lon":101.73,
     "bbox":[98.0,15.0,106.0,23.0],"tdi":0.54,"country_up":"China / Laos","country_dn":"Thailand / Cambodia / Vietnam",
     "n_countries":6,"dam":"Xayaburi Dam","storage_bcm":7.4,
     "area_km2":795000,"flow_mcm":475000,"dispute_level":"MEDIUM",
     "un_articles":["Art.5","Art.7","Art.8","Art.9"],"notes":"MRC coordinates; China dams alter seasonal flow"},

    {"id":"yangtze_3gorges","name":"Yangtze – Three Gorges","region":"Asia","lat":30.82,"lon":111.00,
     "bbox":[108.0,28.0,114.0,33.0],"tdi":0.22,"country_up":"China (upstream)","country_dn":"China (downstream) · reference basin",
     "n_countries":1,"dam":"Three Gorges Dam","storage_bcm":39.3,
     "area_km2":1800000,"flow_mcm":951000,"dispute_level":"MINIMAL",
     "un_articles":["Art.5","Art.6"],"notes":"World's largest hydropower; domestic reference basin"},

    {"id":"indus_tarbela","name":"Indus – Tarbela","region":"Asia","lat":34.08,"lon":72.68,
     "bbox":[70.0,30.0,76.0,36.0],"tdi":0.66,"country_up":"India / China","country_dn":"Pakistan",
     "n_countries":3,"dam":"Tarbela Dam","storage_bcm":11.3,
     "area_km2":1165500,"flow_mcm":207000,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.33"],"notes":"Indus Waters Treaty 1960; India-Pakistan tensions"},

    {"id":"brahmaputra_subansiri","name":"Brahmaputra – Subansiri","region":"Asia","lat":27.50,"lon":94.74,
     "bbox":[88.0,25.0,97.0,30.0],"tdi":0.48,"country_up":"China (Tibet)","country_dn":"India / Bangladesh",
     "n_countries":3,"dam":"Lower Subansiri Project","storage_bcm":1.37,
     "area_km2":651334,"flow_mcm":629000,"dispute_level":"MEDIUM",
     "un_articles":["Art.5","Art.7","Art.9"],"notes":"China dam construction raises India flood concerns"},

    {"id":"ganges_farakka","name":"Ganges – Farakka","region":"Asia","lat":24.80,"lon":87.92,
     "bbox":[85.0,22.0,91.0,27.0],"tdi":0.58,"country_up":"India","country_dn":"Bangladesh",
     "n_countries":2,"dam":"Farakka Barrage","storage_bcm":0.35,
     "area_km2":1087300,"flow_mcm":500000,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.10"],"notes":"1996 Ganges Treaty; Bangladesh dry-season dispute"},

    {"id":"salween_myitsone","name":"Salween – Myitsone","region":"Asia","lat":25.50,"lon":97.50,
     "bbox":[96.0,22.0,100.0,28.0],"tdi":0.41,"country_up":"China","country_dn":"Myanmar / Thailand",
     "n_countries":3,"dam":"Myitsone Dam (suspended)","storage_bcm":19.3,
     "area_km2":271914,"flow_mcm":211000,"dispute_level":"MEDIUM",
     "un_articles":["Art.5","Art.7","Art.8"],"notes":"Myanmar suspended 2011; China pressure continues"},

    # ── AMERICAS ─────────────────────────────────────────────────────────────
    {"id":"amazon_belo_monte","name":"Amazon – Belo Monte","region":"Americas","lat":-3.38,"lon":-51.77,
     "bbox":[-55.0,-6.0,-48.0,-1.0],"tdi":0.18,"country_up":"Brazil / Peru / Colombia","country_dn":"Brazil · reference basin",
     "n_countries":8,"dam":"Belo Monte Dam","storage_bcm":2.5,
     "area_km2":7180000,"flow_mcm":6600000,"dispute_level":"LOW",
     "un_articles":["Art.5","Art.6"],"notes":"World's largest discharge; indigenous rights disputes"},

    {"id":"parana_itaipu","name":"Paraná – Itaipu","region":"Americas","lat":-25.41,"lon":-54.59,
     "bbox":[-57.0,-28.0,-52.0,-22.0],"tdi":0.31,"country_up":"Brazil","country_dn":"Paraguay",
     "n_countries":3,"dam":"Itaipu Dam","storage_bcm":29.0,
     "area_km2":820000,"flow_mcm":685000,"dispute_level":"LOW",
     "un_articles":["Art.5","Art.6","Art.7"],"notes":"Brazil-Paraguay co-owned; 2009 price renegotiation"},

    {"id":"orinoco_guri","name":"Orinoco – Guri","region":"Americas","lat":7.77,"lon":-62.97,
     "bbox":[-66.0,5.0,-60.0,11.0],"tdi":0.27,"country_up":"Colombia","country_dn":"Venezuela",
     "n_countries":2,"dam":"Guri (Simón Bolívar) Dam","storage_bcm":135.0,
     "area_km2":1000000,"flow_mcm":1135000,"dispute_level":"LOW",
     "un_articles":["Art.5","Art.6","Art.7"],"notes":"Venezuela main power source; 2016 drought crisis"},

    {"id":"colorado_hoover","name":"Colorado – Hoover","region":"Americas","lat":36.01,"lon":-114.74,
     "bbox":[-116.0,34.0,-112.0,38.0],"tdi":0.73,"country_up":"USA","country_dn":"Mexico",
     "n_countries":2,"dam":"Hoover Dam","storage_bcm":35.0,
     "area_km2":629100,"flow_mcm":20000,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.33"],"notes":"Lake Mead historic low; 1944 US-Mexico Treaty strained"},

    {"id":"columbia_grand_coulee","name":"Columbia – Grand Coulee","region":"Americas","lat":47.96,"lon":-118.98,
     "bbox":[-121.0,45.0,-116.0,50.0],"tdi":0.33,"country_up":"Canada","country_dn":"USA",
     "n_countries":2,"dam":"Grand Coulee Dam","storage_bcm":11.8,
     "area_km2":668000,"flow_mcm":238000,"dispute_level":"LOW",
     "un_articles":["Art.5","Art.6","Art.7"],"notes":"1964 Columbia River Treaty; US-Canada flood control"},

    {"id":"rio_grande_amistad","name":"Rio Grande – Amistad","region":"Americas","lat":29.44,"lon":-101.07,
     "bbox":[-104.0,27.0,-98.0,32.0],"tdi":0.62,"country_up":"USA","country_dn":"Mexico",
     "n_countries":2,"dam":"Amistad Dam","storage_bcm":4.0,
     "area_km2":870000,"flow_mcm":5100,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9"],"notes":"IBWC administers; chronic water debt disputes"},

    # ── EUROPE ───────────────────────────────────────────────────────────────
    {"id":"danube_iron_gates","name":"Danube – Iron Gates I","region":"Europe","lat":44.67,"lon":22.53,
     "bbox":[20.0,42.0,26.0,47.0],"tdi":0.35,"country_up":"Germany / Austria","country_dn":"Romania / Serbia",
     "n_countries":14,"dam":"Iron Gates I (Đerdap)","storage_bcm":2.4,
     "area_km2":817000,"flow_mcm":206000,"dispute_level":"LOW",
     "un_articles":["Art.5","Art.6","Art.8"],"notes":"ICPDR coordinates 14 countries; EU WFD"},

    {"id":"rhine_basin","name":"Rhine – Basin","region":"Europe","lat":51.45,"lon":6.76,
     "bbox":[5.0,47.0,10.0,53.0],"tdi":0.28,"country_up":"Switzerland","country_dn":"Germany / Netherlands",
     "n_countries":9,"dam":"Rhine Basin (multiple)","storage_bcm":5.2,
     "area_km2":185000,"flow_mcm":70000,"dispute_level":"LOW",
     "un_articles":["Art.5","Art.6","Art.7"],"notes":"ICPR success story; 1986 Sandoz spill led to reform"},

    {"id":"dnieper_kakhovka","name":"Dnieper – Kakhovka","region":"Europe","lat":47.25,"lon":34.00,
     "bbox":[32.0,45.0,37.0,50.0],"tdi":0.71,"country_up":"Russia / Belarus","country_dn":"Ukraine",
     "n_countries":3,"dam":"Kakhovka Dam (destroyed 2023)","storage_bcm":18.2,
     "area_km2":504000,"flow_mcm":53000,"dispute_level":"HIGH",
     "un_articles":["Art.5","Art.7","Art.9","Art.33"],"notes":"Dam destroyed June 2023; war-related ecocide"},

    # ── OCEANIA ──────────────────────────────────────────────────────────────
    {"id":"murray_darling_hume","name":"Murray-Darling – Hume","region":"Oceania","lat":-36.10,"lon":147.03,
     "bbox":[138.0,-38.0,152.0,-25.0],"tdi":0.44,"country_up":"Australia (QLD/NSW/VIC)","country_dn":"Australia (SA) · reference basin",
     "n_countries":1,"dam":"Hume Dam","storage_bcm":3.0,
     "area_km2":1061469,"flow_mcm":23600,"dispute_level":"MEDIUM",
     "un_articles":["Art.5","Art.6","Art.7"],"notes":"Murray-Darling Basin Plan 2012; climate-driven decline"},
]

BASINS_BY_ID     = {b["id"]: b for b in BASINS_26}
BASINS_BY_REGION = {}
for b in BASINS_26:
    BASINS_BY_REGION.setdefault(b["region"], []).append(b)

REGIONS = list(BASINS_BY_REGION.keys())

def get_basin(basin_id): return BASINS_BY_ID.get(basin_id, {})
def get_by_region(region): return BASINS_BY_REGION.get(region, [])
def get_by_risk(risk):
    t = {"MINIMAL":(0,.25),"LOW":(.25,.40),"MEDIUM":(.40,.55),"HIGH":(.55,1.0)}
    lo,hi = t.get(risk,(0,1))
    return [b for b in BASINS_26 if lo <= float(b["tdi"]) < hi]
def atdi(): return sum(float(b["tdi"]) for b in BASINS_26)/len(BASINS_26)*100


# ── 24 Additional Basins (Total: 50) — HSAE v9.0.0 ───────────────────────────
BASINS_ADDITIONAL = [
    {"id":"volta_akosombo","name":"Volta – Akosombo","region":"West Africa",
     "countries":6,"tdi":0.32,"dispute_level":"MODERATE","storage_km3":148,
     "main_dam":"Akosombo","bbox":[-5.5,7.0,1.5,12.0],"area_km2":394100,
     "un_articles":[5,7,9,20],"upstream_dams":3},
    {"id":"limpopo_cahora","name":"Limpopo – Massingir","region":"Southern Africa",
     "countries":4,"tdi":0.38,"dispute_level":"MODERATE","storage_km3":2.8,
     "main_dam":"Massingir","bbox":[25.0,-27.0,35.0,-22.0],"area_km2":415000,
     "un_articles":[5,7,20,21],"upstream_dams":5},
    {"id":"senegal_manantali","name":"Senegal – Manantali","region":"West Africa",
     "countries":3,"tdi":0.27,"dispute_level":"LOW","storage_km3":11.3,
     "main_dam":"Manantali","bbox":[-18.0,11.0,-7.0,17.0],"area_km2":289000,
     "un_articles":[5,8,20],"upstream_dams":2},
    {"id":"okavango_delta","name":"Okavango – Mohembo","region":"Southern Africa",
     "countries":3,"tdi":0.18,"dispute_level":"LOW","storage_km3":0,
     "main_dam":"No major dam","bbox":[18.0,-21.0,25.0,-15.0],"area_km2":721000,
     "un_articles":[5,20,23],"upstream_dams":0},
    {"id":"irrawaddy_myitsone","name":"Irrawaddy – Myitsone","region":"Southeast Asia",
     "countries":2,"tdi":0.28,"dispute_level":"MODERATE","storage_km3":19.6,
     "main_dam":"Myitsone (planned/suspended)","bbox":[94.0,20.0,100.0,29.0],
     "area_km2":404000,"un_articles":[5,7,12,33],"upstream_dams":4},
    {"id":"sittaung_myanmar","name":"Sittaung – Paunglaung","region":"Southeast Asia",
     "countries":1,"tdi":0.20,"dispute_level":"LOW","storage_km3":0.7,
     "main_dam":"Paunglaung","bbox":[96.0,17.0,100.0,20.0],
     "area_km2":36000,"un_articles":[20,21],"upstream_dams":2},
    {"id":"helmand_kajaki","name":"Helmand – Kajaki","region":"Central Asia",
     "countries":2,"tdi":0.51,"dispute_level":"HIGH","storage_km3":2.05,
     "main_dam":"Kajaki","bbox":[61.0,29.0,68.0,35.0],"area_km2":255000,
     "un_articles":[5,7,12,17,33],"upstream_dams":3},
    {"id":"aral_syrdarya","name":"Syr Darya – Toktogul","region":"Central Asia",
     "countries":4,"tdi":0.42,"dispute_level":"HIGH","storage_km3":19.5,
     "main_dam":"Toktogul","bbox":[65.0,37.0,79.0,44.0],"area_km2":219000,
     "un_articles":[5,7,9,17,20],"upstream_dams":7},
    {"id":"jordan_river","name":"Jordan – Deganya","region":"Middle East",
     "countries":4,"tdi":0.72,"dispute_level":"CRITICAL","storage_km3":0.23,
     "main_dam":"Deganya","bbox":[35.0,31.0,39.0,35.0],"area_km2":18300,
     "un_articles":[5,7,12,17,28,33],"upstream_dams":2},
    {"id":"nile_atbara","name":"Atbara – Khashm el Girba","region":"East Africa",
     "countries":2,"tdi":0.40,"dispute_level":"MODERATE","storage_km3":1.3,
     "main_dam":"Khashm el Girba","bbox":[36.5,13.0,38.5,15.0],
     "area_km2":67000,"un_articles":[5,7,9],"upstream_dams":1},
    {"id":"ob_irtysh","name":"Ob-Irtysh – Bukhtarma","region":"Central Asia",
     "countries":3,"tdi":0.22,"dispute_level":"LOW","storage_km3":49.6,
     "main_dam":"Bukhtarma","bbox":[65.0,47.0,88.0,60.0],"area_km2":2972000,
     "un_articles":[5,8,20],"upstream_dams":6},
    {"id":"yenisei_krasnoyarsk","name":"Yenisei – Krasnoyarsk","region":"Central Asia",
     "countries":2,"tdi":0.12,"dispute_level":"LOW","storage_km3":73.3,
     "main_dam":"Krasnoyarsk","bbox":[82.0,52.0,105.0,70.0],"area_km2":2580000,
     "un_articles":[5,20],"upstream_dams":9},
    {"id":"huang_he_xiaolangdi","name":"Yellow River – Xiaolangdi","region":"Southeast Asia",
     "countries":1,"tdi":0.35,"dispute_level":"MODERATE","storage_km3":12.65,
     "main_dam":"Xiaolangdi","bbox":[100.0,33.0,120.0,42.0],"area_km2":752000,
     "un_articles":[5,20,21],"upstream_dams":18},
    {"id":"pearl_river_delta","name":"Pearl River – Tianshengqiao","region":"Southeast Asia",
     "countries":2,"tdi":0.18,"dispute_level":"LOW","storage_km3":10.3,
     "main_dam":"Tianshengqiao","bbox":[103.0,21.0,115.0,25.0],"area_km2":453700,
     "un_articles":[5,8,20,21],"upstream_dams":10},
    {"id":"chao_phraya_bhumibol","name":"Chao Phraya – Bhumibol","region":"Southeast Asia",
     "countries":2,"tdi":0.24,"dispute_level":"LOW","storage_km3":13.5,
     "main_dam":"Bhumibol","bbox":[98.0,13.5,102.0,19.0],"area_km2":177000,
     "un_articles":[5,20,21],"upstream_dams":5},
    {"id":"rio_de_la_plata","name":"Río de la Plata – Yacyretá","region":"South America",
     "countries":2,"tdi":0.15,"dispute_level":"LOW","storage_km3":21.0,
     "main_dam":"Yacyretá","bbox":[-65.0,-35.0,-50.0,-15.0],"area_km2":3100000,
     "un_articles":[5,8,20],"upstream_dams":12},
    {"id":"magdalena_betania","name":"Magdalena – Betania","region":"South America",
     "countries":1,"tdi":0.20,"dispute_level":"LOW","storage_km3":1.97,
     "main_dam":"Betania","bbox":[-78.0,2.0,-73.0,8.0],"area_km2":257438,
     "un_articles":[5,20,21],"upstream_dams":6},
    {"id":"niger_selingue","name":"Niger – Sélingué","region":"West Africa",
     "countries":9,"tdi":0.35,"dispute_level":"MODERATE","storage_km3":2.17,
     "main_dam":"Sélingué","bbox":[-7.0,5.0,14.0,17.0],"area_km2":2090000,
     "un_articles":[5,7,9,20,21],"upstream_dams":8},
    {"id":"columbia_revelstoke","name":"Columbia – Revelstoke","region":"North America",
     "countries":2,"tdi":0.14,"dispute_level":"LOW","storage_km3":1.89,
     "main_dam":"Revelstoke","bbox":[-120.0,46.0,-114.0,52.0],"area_km2":668000,
     "un_articles":[5,8,9],"upstream_dams":12},
    {"id":"fraser_williston","name":"Fraser – Williston","region":"North America",
     "countries":1,"tdi":0.10,"dispute_level":"LOW","storage_km3":74.3,
     "main_dam":"Williston Lake (WAC Bennett)","bbox":[-127.0,49.0,-119.0,57.0],
     "area_km2":232000,"un_articles":[20,21],"upstream_dams":4},
    {"id":"dnestr_dubossary","name":"Dniester – Dubossary","region":"Europe",
     "countries":3,"tdi":0.45,"dispute_level":"HIGH","storage_km3":0.40,
     "main_dam":"Dubossary","bbox":[26.0,45.5,31.0,49.5],"area_km2":72100,
     "un_articles":[5,7,12,17,33],"upstream_dams":3},
    {"id":"ebro_mequinenza","name":"Ebro – Mequinenza","region":"Europe",
     "countries":3,"tdi":0.20,"dispute_level":"LOW","storage_km3":1.53,
     "main_dam":"Mequinenza","bbox":[-4.0,40.0,4.0,44.0],"area_km2":85550,
     "un_articles":[5,8,20,21],"upstream_dams":18},
    {"id":"daugava_plavinas","name":"Daugava – Plāviņas","region":"Europe",
     "countries":3,"tdi":0.15,"dispute_level":"LOW","storage_km3":0.40,
     "main_dam":"Plāviņas","bbox":[24.0,55.0,28.0,58.0],"area_km2":87900,
     "un_articles":[5,8,20],"upstream_dams":4},
    {"id":"tigris_mosul_karun","name":"Karun – Dez","region":"Middle East",
     "countries":2,"tdi":0.35,"dispute_level":"MODERATE","storage_km3":3.30,
     "main_dam":"Dez","bbox":[47.0,30.5,52.0,35.5],"area_km2":66000,
     "un_articles":[5,7,9,20],"upstream_dams":5},
]

# Fix bbox error
for b in BASINS_ADDITIONAL:
    bbox = b.get("bbox",[])
    if isinstance(bbox, list) and len(bbox) == 4:
        pass  # ok
    else:
        b["bbox"] = [0,0,1,1]

# Handle bbox with string inside
import ast
clean_additional = []
for b in BASINS_ADDITIONAL:
    try:
        bbox = b["bbox"]
        if '"' in str(bbox) or "'" in str(bbox):
            b["bbox"] = [0,0,1,1]
        clean_additional.append(b)
    except:
        clean_additional.append(b)

BASINS_ADDITIONAL = clean_additional

# Combined list
BASINS_50 = BASINS_26 + BASINS_ADDITIONAL
