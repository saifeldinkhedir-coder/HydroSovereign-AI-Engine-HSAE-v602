"""
basins.py — HSAE v6.01 Basin Registry
======================================
26 transboundary river basins with geopolitical, physical,
and legal data. Source: TFDD, ICOW, GRDC, FAO AQUASTAT.

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
from typing import Optional


BASINS_26 = [
    # ── Africa ──────────────────────────────────────────────────────────────
    {"id":"GERD_ETH",   "name":"Blue Nile (GERD)",          "river":"Blue Nile",    "dam":"Grand Ethiopian Renaissance Dam","continent":"Africa",      "country":["Ethiopia","Sudan","Egypt"],        "lat":10.53,"lon":35.09,"runoff_c":0.38,"cap":74.0,  "eff_cat_km2":174000,  "dispute_level":4,"treaty":"UN1997",             "legal_arts":"Arts. 5, 7, 12, 20","context":"Largest dam in Africa; GERD dispute Ethiopia/Egypt/Sudan"},
    {"id":"ROSE_SDN",   "name":"Nile – Roseires Dam",        "river":"Blue Nile",    "dam":"Roseires Dam",                   "continent":"Africa",      "country":["Sudan","Ethiopia"],                "lat":11.85,"lon":34.38,"runoff_c":0.35,"cap":3.0,   "eff_cat_km2":160000,  "dispute_level":2,"treaty":"NileAgreement1959","legal_arts":"Arts. 5, 6",        "context":"Second major dam on Blue Nile; Sudan/Ethiopia"},
    {"id":"ASWAN_EGY",  "name":"Nile – High Aswan Dam",      "river":"Nile",         "dam":"Aswan High Dam",                 "continent":"Africa",      "country":["Egypt","Sudan"],                   "lat":23.97,"lon":32.88,"runoff_c":0.10,"cap":162.0, "eff_cat_km2":2900000, "dispute_level":3,"treaty":"NileAgreement1959","legal_arts":"Arts. 5, 6, 7",     "context":"Controls entire Nile flow; 1959 Egypt-Sudan agreement"},
    {"id":"KRIB_ZMB",   "name":"Zambezi – Kariba Dam",       "river":"Zambezi",      "dam":"Kariba Dam",                     "continent":"Africa",      "country":["Zambia","Zimbabwe"],               "lat":-16.52,"lon":28.77,"runoff_c":0.15,"cap":180.0,"eff_cat_km2":663000,  "dispute_level":2,"treaty":"ZambeziAction",  "legal_arts":"Arts. 5, 8",        "context":"Largest reservoir by volume; Zambia-Zimbabwe cooperation"},
    {"id":"INGA_DRC",   "name":"Congo – Inga Dam",            "river":"Congo",        "dam":"Inga Dam",                       "continent":"Africa",      "country":["DRC","Congo","Angola"],            "lat":-5.52, "lon":13.61,"runoff_c":0.35,"cap":0.5,  "eff_cat_km2":3730000, "dispute_level":1,"treaty":"Congo_CICOS",     "legal_arts":"Arts. 5, 9",        "context":"World largest hydropower potential; DRC dominates"},
    {"id":"KAIN_NIG",   "name":"Niger – Kainji Dam",          "river":"Niger",        "dam":"Kainji Dam",                     "continent":"Africa",      "country":["Nigeria","Niger","Mali","Guinea"], "lat":10.40,"lon":4.57, "runoff_c":0.20,"cap":15.0, "eff_cat_km2":2200000, "dispute_level":2,"treaty":"NigerBasinAuthority","legal_arts":"Arts. 5, 7",      "context":"Niger Basin Authority established 1980; multi-state"},
    # ── Middle East ──────────────────────────────────────────────────────────
    {"id":"ATAT_TUR",   "name":"Euphrates – Atatürk Dam",    "river":"Euphrates",    "dam":"Atatürk Dam",                    "continent":"Middle East", "country":["Turkey","Syria","Iraq"],           "lat":37.48,"lon":38.35,"runoff_c":0.18,"cap":48.7, "eff_cat_km2":444000,  "dispute_level":4,"treaty":"UN1997",             "legal_arts":"Arts. 5, 7, 33",    "context":"Turkey controls headwaters; major dispute Syria/Iraq"},
    {"id":"MOUS_IRQ",   "name":"Tigris – Mosul Dam",          "river":"Tigris",       "dam":"Mosul Dam",                      "continent":"Middle East", "country":["Iraq","Turkey"],                   "lat":36.34,"lon":43.14,"runoff_c":0.22,"cap":11.1, "eff_cat_km2":375000,  "dispute_level":3,"treaty":"UN1997",             "legal_arts":"Arts. 5, 7",        "context":"Mosul Dam risk; Iraq/Turkey tension"},
    # ── Central Asia ─────────────────────────────────────────────────────────
    {"id":"NURE_TJK",   "name":"Amu Darya – Nurek Dam",      "river":"Amu Darya",    "dam":"Nurek Dam",                      "continent":"Central Asia","country":["Tajikistan","Uzbekistan","Turkmenistan","Afghanistan"],"lat":38.37,"lon":69.32,"runoff_c":0.25,"cap":10.5,"eff_cat_km2":309000,"dispute_level":3,"treaty":"AralSeaAgreement","legal_arts":"Arts. 5, 7, 20","context":"Central Asia water crisis; Aral Sea desiccation"},
    {"id":"TOKT_KGZ",   "name":"Syr Darya – Toktogul Dam",   "river":"Syr Darya",    "dam":"Toktogul Dam",                   "continent":"Central Asia","country":["Kyrgyzstan","Uzbekistan","Kazakhstan","Tajikistan"],"lat":41.79,"lon":72.79,"runoff_c":0.15,"cap":19.5,"eff_cat_km2":219000,"dispute_level":4,"treaty":"AralSeaAgreement","legal_arts":"Arts. 5, 7, 20","context":"Energy vs irrigation conflict; Kyrgyzstan upstream"},
    # ── Asia ────────────────────────────────────────────────────────────────
    {"id":"XAYA_LAO",   "name":"Mekong – Xayaburi Dam",      "river":"Mekong",       "dam":"Xayaburi Dam",                   "continent":"Asia",        "country":["China","Myanmar","Laos","Thailand","Cambodia","Vietnam"],"lat":19.05,"lon":101.70,"runoff_c":0.42,"cap":7.4,"eff_cat_km2":795000,"dispute_level":3,"treaty":"MekongAgreement1995","legal_arts":"Arts. 5, 7, 9","context":"Chinese dams block sediment; MRC manages lower basin"},
    {"id":"3GOR_CHN",   "name":"Yangtze – Three Gorges Dam", "river":"Yangtze",      "dam":"Three Gorges Dam",               "continent":"Asia",        "country":["China"],                           "lat":30.82,"lon":111.00,"runoff_c":0.50,"cap":39.3,"eff_cat_km2":1000000,"dispute_level":1,"treaty":"Domestic",          "legal_arts":"N/A",               "context":"World largest hydroelectric dam; domestic China"},
    {"id":"TARB_PAK",   "name":"Indus – Tarbela Dam",         "river":"Indus",        "dam":"Tarbela Dam",                    "continent":"Asia",        "country":["Pakistan","India"],                "lat":34.07,"lon":72.68,"runoff_c":0.32,"cap":13.7, "eff_cat_km2":363000,  "dispute_level":3,"treaty":"IndusWatersTreaty1960","legal_arts":"Arts. I–VIII IWT","context":"World largest earth-filled dam; Indus Waters Treaty 1960"},
    {"id":"SUBA_IND",   "name":"Brahmaputra – Subansiri Dam","river":"Brahmaputra",  "dam":"Subansiri Dam",                  "continent":"Asia",        "country":["China","India","Bangladesh"],      "lat":27.52,"lon":94.42,"runoff_c":0.55,"cap":1.37,  "eff_cat_km2":651000,  "dispute_level":3,"treaty":"UN1997",             "legal_arts":"Arts. 5, 7",        "context":"China-India tension; China dams on Yarlung Tsangpo"},
    {"id":"FARK_IND",   "name":"Ganges – Farakka Barrage",   "river":"Ganges",       "dam":"Farakka Barrage",                "continent":"Asia",        "country":["India","Bangladesh"],              "lat":24.81,"lon":87.91,"runoff_c":0.45,"cap":0.26,  "eff_cat_km2":1000000, "dispute_level":3,"treaty":"GangesTreaty1996",  "legal_arts":"Ganges Treaty 1996","context":"Bangladesh affected by dry season diversions"},
    {"id":"MYIT_MMR",   "name":"Salween – Myitsone Dam",      "river":"Salween",      "dam":"Myitsone Dam",                   "continent":"Asia",        "country":["China","Myanmar","Thailand"],      "lat":25.54,"lon":97.46,"runoff_c":0.38,"cap":3.7, "eff_cat_km2":324000,  "dispute_level":2,"treaty":"UN1997",             "legal_arts":"Arts. 5, 7",        "context":"Myanmar dam suspended 2011; China investment dispute"},
    # ── Americas ────────────────────────────────────────────────────────────
    {"id":"BELO_BRA",   "name":"Amazon – Belo Monte Dam",    "river":"Amazon",       "dam":"Belo Monte Dam",                 "continent":"Americas",    "country":["Brazil"],                          "lat":-3.14, "lon":-51.38,"runoff_c":0.65,"cap":11.2, "eff_cat_km2":4600000,"dispute_level":1,"treaty":"Domestic",          "legal_arts":"Arts. 5, 20",       "context":"World 3rd largest dam; impacts indigenous communities"},
    {"id":"ITAI_BRA",   "name":"Paraná – Itaipu Dam",         "river":"Paraná",       "dam":"Itaipu Dam",                     "continent":"Americas",    "country":["Brazil","Paraguay"],               "lat":-25.41,"lon":-54.59,"runoff_c":0.55,"cap":29.0,"eff_cat_km2":820000,  "dispute_level":1,"treaty":"ItaipuTreaty1973", "legal_arts":"Itaipu Treaty 1973","context":"World 2nd largest hydropower; Brazil-Paraguay treaty 1973"},
    {"id":"GURI_VEN",   "name":"Orinoco – Guri Dam",          "river":"Orinoco",      "dam":"Guri Dam",                       "continent":"Americas",    "country":["Venezuela","Colombia"],            "lat":7.77,  "lon":-62.99,"runoff_c":0.60,"cap":135.0,"eff_cat_km2":640000,  "dispute_level":2,"treaty":"UN1997",             "legal_arts":"Arts. 5, 9",        "context":"Venezuela national power; Guri reservoir critical"},
    {"id":"HOOV_USA",   "name":"Colorado – Hoover Dam",       "river":"Colorado",     "dam":"Hoover Dam",                     "continent":"Americas",    "country":["USA","Mexico"],                    "lat":36.02,"lon":-114.74,"runoff_c":0.12,"cap":35.2,"eff_cat_km2":629000,  "dispute_level":2,"treaty":"ColoradoCompact1922","legal_arts":"Colorado Compact 1922; Treaty 1944","context":"Over-allocated river; US-Mexico 1944 treaty deficit"},
    {"id":"GCOU_USA",   "name":"Columbia – Grand Coulee Dam", "river":"Columbia",     "dam":"Grand Coulee Dam",               "continent":"Americas",    "country":["USA","Canada"],                    "lat":47.96,"lon":-118.98,"runoff_c":0.42,"cap":11.8,"eff_cat_km2":668000,  "dispute_level":1,"treaty":"ColumbiaRiverTreaty1964","legal_arts":"Columbia River Treaty 1964","context":"Columbia River Treaty 1964; US-Canada cooperation"},
    {"id":"AMIS_USA",   "name":"Rio Grande – Amistad Dam",    "river":"Rio Grande",   "dam":"Amistad Dam",                    "continent":"Americas",    "country":["USA","Mexico"],                    "lat":29.45,"lon":-101.07,"runoff_c":0.08,"cap":7.5,"eff_cat_km2":470000,   "dispute_level":2,"treaty":"Treaty1944",         "legal_arts":"Treaty 1944",       "context":"US-Mexico 1944 water treaty; deficit under climate change"},
    # ── Europe ──────────────────────────────────────────────────────────────
    {"id":"IRON_ROM",   "name":"Danube – Iron Gates I",       "river":"Danube",       "dam":"Iron Gates I",                   "continent":"Europe",      "country":["Germany","Austria","Slovakia","Hungary","Croatia","Serbia","Romania","Bulgaria","Ukraine"],"lat":44.68,"lon":22.52,"runoff_c":0.38,"cap":2.4,"eff_cat_km2":817000,"dispute_level":1,"treaty":"DanubeConvention1994","legal_arts":"Danube Convention 1994","context":"EU-managed; ICPDR coordinates 19 countries"},
    {"id":"RHIN_DEU",   "name":"Rhine – Basin",               "river":"Rhine",        "dam":"Multiple weirs",                 "continent":"Europe",      "country":["Switzerland","Germany","France","Netherlands"],"lat":50.93,"lon":6.96,"runoff_c":0.42,"cap":0.5,"eff_cat_km2":185000,  "dispute_level":1,"treaty":"RhineConvention1999","legal_arts":"Rhine Convention 1999","context":"Model multi-state governance; Rhine Convention 1999"},
    {"id":"KAKH_UKR",   "name":"Dnieper – Kakhovka Dam",      "river":"Dnieper",      "dam":"Kakhovka Dam",                   "continent":"Europe",      "country":["Russia","Belarus","Ukraine"],      "lat":47.36,"lon":33.40,"runoff_c":0.28,"cap":18.2, "eff_cat_km2":504000,  "dispute_level":3,"treaty":"UN1997",             "legal_arts":"Arts. 5, 7, 33, 35","context":"Kakhovka Dam destroyed June 2023 (war); Ukraine/Russia"},
    # ── Oceania ─────────────────────────────────────────────────────────────
    {"id":"HUME_AUS",   "name":"Murray-Darling – Hume Dam",  "river":"Murray-Darling","dam":"Hume Dam",                      "continent":"Oceania",     "country":["Australia"],                       "lat":-36.10,"lon":147.03,"runoff_c":0.12,"cap":3.0,"eff_cat_km2":1061000,  "dispute_level":1,"treaty":"WaterAct2007",       "legal_arts":"Water Act 2007",    "context":"Australia national water reform; Murray-Darling Basin Plan"},
]


class BasinRegistry:
    """
    Registry for all 26 HSAE transboundary river basins.

    Examples
    --------
    >>> reg = BasinRegistry()
    >>> basin = reg.get("Blue Nile (GERD)")
    >>> print(basin["runoff_c"])   # 0.38
    >>> print(basin["cap"])        # 74.0
    >>> africa = reg.filter_by_continent("Africa")
    >>> print(len(africa))         # 6
    """

    def __init__(self):
        self._basins = {b["name"]: b for b in BASINS_26}
        self._by_id  = {b["id"]: b for b in BASINS_26}

    def get(self, name: str) -> dict:
        """Get basin by name."""
        if name not in self._basins:
            raise KeyError(f"Basin '{name}' not found. Use list_basins() to see all.")
        return self._basins[name].copy()

    def get_by_id(self, basin_id: str) -> dict:
        """Get basin by ID (e.g. 'GERD_ETH')."""
        if basin_id not in self._by_id:
            raise KeyError(f"Basin ID '{basin_id}' not found.")
        return self._by_id[basin_id].copy()

    def list_names(self) -> list:
        """List all basin names."""
        return list(self._basins.keys())

    def filter_by_continent(self, continent: str) -> list:
        """Filter basins by continent."""
        return [b.copy() for b in BASINS_26
                if b.get("continent","").lower() == continent.lower()]

    def filter_by_dispute(self, min_level: int = 3) -> list:
        """Filter basins by minimum dispute level."""
        return [b.copy() for b in BASINS_26
                if int(b.get("dispute_level", 0)) >= min_level]

    def all(self) -> list:
        """Return all 26 basins."""
        return [b.copy() for b in BASINS_26]

    def __len__(self):
        return len(BASINS_26)

    def __repr__(self):
        return f"BasinRegistry(n={len(BASINS_26)} basins)"


def get_basin(name: str) -> dict:
    """Convenience function — get basin by name."""
    return BasinRegistry().get(name)


def list_basins() -> list:
    """Convenience function — list all basin names."""
    return BasinRegistry().list_names()
