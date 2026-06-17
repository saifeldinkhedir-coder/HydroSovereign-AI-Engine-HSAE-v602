# conflict_index.py — HSAE v10.0 (QGIS dialogs removed)

"""
conflict_index.py — HSAE v6.0 Conflict Index & ICJ Precedents (QGIS Edition)
==============================================================================
Adapted from hsae_legal.py. No Streamlit dependency.

Components:
  1. Conflict Index (0-100) — composite of TDI, countries, dispute level
  2. ICJ/PCA Precedents Database (6 cases)
  3. Auto-Protest Draft (Article 12, UN 1997)
  4. UN 1997 Article Auto-Mapper
  5. Bilingual Report (EN/AR)

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
from typing import Dict, List, Optional

# ── ICJ Precedents Database ───────────────────────────────────────────────────

ICJ_CASES: List[Dict] = [
    {
        "id": "ICJ-1997-HNG-SVK",
        "title": "Gabcikovo-Nagymaros (Hungary v. Slovakia)",
        "year": 1997, "river": "Danube",
        "articles": ["Art.5", "Art.7", "Art.20"],
        "hifd_threshold": 50.0,
        "holding_en": (
            "Both states have obligations for equitable use. "
            "Unilateral diversion without notification breaches "
            "customary international water law."
        ),
        "holding_ar": (
            "لكلا الدولتين التزامات بالاستخدام المنصف. "
            "يُعدّ تحويل مجرى النهر بشكل أحادي دون إخطار "
            "انتهاكاً للقانون الدولي العرفي للمياه."
        ),
        "keywords": ["diversion", "unilateral", "notification", "equitable"],
        "url": "https://www.icj-cij.org/case/92",
    },
    {
        "id": "ICJ-2010-ARG-URY",
        "title": "Pulp Mills — Uruguay River (Argentina v. Uruguay)",
        "year": 2010, "river": "Uruguay",
        "articles": ["Art.9", "Art.20"],
        "hifd_threshold": 0.0,
        "holding_en": (
            "States must notify co-riparians before constructing works "
            "likely to affect shared watercourses. "
            "Environmental impact assessment is obligatory."
        ),
        "holding_ar": (
            "يجب على الدول إخطار الدول المشاطئة قبل إنشاء أعمال "
            "قد تؤثر على المجاري المائية المشتركة. "
            "تقييم الأثر البيئي إلزامي."
        ),
        "keywords": ["notification", "EIA", "environmental", "construction"],
        "url": "https://www.icj-cij.org/case/135",
    },
    {
        "id": "PCA-2013-IND-PAK",
        "title": "Kishenganga Arbitration (India v. Pakistan)",
        "year": 2013, "river": "Indus / Kishenganga",
        "articles": ["Art.5", "Art.7"],
        "hifd_threshold": 45.0,
        "holding_en": (
            "Minimum environmental flow obligations must be maintained. "
            "Hydropower projects on shared rivers must preserve "
            "downstream ecological integrity."
        ),
        "holding_ar": (
            "يجب الحفاظ على الحد الأدنى من التدفق البيئي. "
            "مشاريع الطاقة الكهرومائية على الأنهار المشتركة يجب "
            "أن تحافظ على سلامة النظام البيئي للمصب."
        ),
        "keywords": ["minimum flow", "hydropower", "downstream", "ecology"],
        "url": "https://pca-cpa.org/en/cases/59/",
    },
    {
        "id": "ICJ-2018-CRI-NIC",
        "title": "Certain Activities (Costa Rica v. Nicaragua)",
        "year": 2018, "river": "San Juan",
        "articles": ["Art.7", "Art.20"],
        "hifd_threshold": 0.0,
        "holding_en": (
            "Environmental damage to shared watercourses gives rise "
            "to reparation obligations. "
            "Satellite imagery accepted as valid legal evidence."
        ),
        "holding_ar": (
            "يُولِّد الضرر البيئي للمجاري المائية المشتركة التزامات بالتعويض. "
            "قُبلت صور الأقمار الصناعية كدليل قانوني صالح."
        ),
        "keywords": ["satellite", "evidence", "reparation", "environment"],
        "url": "https://www.icj-cij.org/case/150",
    },
    {
        "id": "UNSC-2020-ETH-SDN-EGY",
        "title": "GERD Negotiation Framework (Ethiopia–Sudan–Egypt)",
        "year": 2020, "river": "Blue Nile",
        "articles": ["Art.5", "Art.7", "Art.9", "Art.12"],
        "hifd_threshold": 40.0,
        "holding_en": (
            "Ongoing dispute under UNSC Resolution 2519 (2020). "
            "No binding agreement; equity and data transparency "
            "remain central to tripartite negotiations."
        ),
        "holding_ar": (
            "نزاع مستمر بموجب قرار مجلس الأمن 2519 (2020). "
            "لم يُتوصَّل إلى اتفاق ملزم؛ تبقى العدالة وشفافية البيانات "
            "محور المفاوضات الثلاثية."
        ),
        "keywords": ["gerd", "nile", "ethiopia", "egypt", "equity"],
        "url": "https://www.un.org/securitycouncil/content/s2020-657",
    },
    {
        "id": "ICJ-2022-KAZ-UZB",
        "title": "Aral Sea Basin Water Allocation (ICWC Framework)",
        "year": 2022, "river": "Amu Darya / Syr Darya",
        "articles": ["Art.5", "Art.9", "Art.33"],
        "hifd_threshold": 55.0,
        "holding_en": (
            "ICWC framework requires proportional allocation among 5 states. "
            "Climate-driven scarcity heightens Art. 33 dispute resolution obligations."
        ),
        "holding_ar": (
            "يستلزم إطار ICWC التوزيع النسبي بين 5 دول. "
            "تُعزز الشُّح المناخي التزامات التسوية بموجب المادة 33."
        ),
        "keywords": ["aral", "central asia", "allocation", "scarcity"],
        "url": "https://www.icwc-aral.uz/",
    },
]

# ── UN 1997 Articles ──────────────────────────────────────────────────────────

UN_ARTICLES = {
    "Art.5":  {
        "title": "Equitable and Reasonable Utilization",
        "text":  "Watercourse States shall use an international watercourse in an "
                 "equitable and reasonable manner.",
        "threshold_pct": 40.0,
        "color": "#f39c12",
    },
    "Art.6":  {
        "title": "Factors relevant to equitable utilization",
        "text":  "Factors include geographic, hydrological, climatic, ecological "
                 "and other factors of a natural character.",
        "threshold_pct": 0.0,
        "color": "#f39c12",
    },
    "Art.7":  {
        "title": "Obligation not to cause significant harm",
        "text":  "Watercourse States shall take all appropriate measures to prevent "
                 "the causing of significant harm to other watercourse States.",
        "threshold_pct": 55.0,
        "color": "#e67e22",
    },
    "Art.8":  {
        "title": "General obligation to cooperate",
        "text":  "Watercourse States shall cooperate on the basis of sovereign "
                 "equality, territorial integrity and mutual benefit.",
        "threshold_pct": 0.0,
        "color": "#3498db",
    },
    "Art.9":  {
        "title": "Regular exchange of data and information",
        "text":  "Watercourse States shall on a regular basis exchange readily "
                 "available data and information on the condition of the watercourse.",
        "threshold_pct": 0.0,
        "color": "#9b59b6",
    },
    "Art.10": {
        "title": "Relationship between different uses",
        "text":  "In the absence of agreement, no use of an international watercourse "
                 "enjoys inherent priority over other uses.",
        "threshold_pct": 0.0,
        "color": "#1abc9c",
    },
    "Art.12": {
        "title": "Notification concerning planned measures",
        "text":  "Watercourse States shall provide timely notification of planned "
                 "measures which may have a significant adverse effect.",
        "threshold_pct": 60.0,
        "color": "#e74c3c",
    },
    "Art.20": {
        "title": "Protection and preservation of ecosystems",
        "text":  "Watercourse States shall protect and preserve the ecosystems of "
                 "international watercourses.",
        "threshold_pct": 0.0,
        "color": "#2ecc71",
    },
    "Art.33": {
        "title": "Settlement of disputes",
        "text":  "Any dispute may be submitted to arbitration or to the ICJ "
                 "in accordance with international law.",
        "threshold_pct": 70.0,
        "color": "#c0392b",
    },
}

# ── Conflict Index ────────────────────────────────────────────────────────────

def compute_conflict_index(basin: dict) -> Dict:
    """
    Composite Conflict Index (0-100).

    Components:
      - TDI score          (40%)  — hydrological tension
      - Country count      (20%)  — more states → higher conflict
      - Dispute level      (25%)  — encoded from dispute_level field
      - UN articles count  (15%)  — more articles triggered → higher risk

    Returns: score, level, triggered_articles, relevant_cases, legal_summary
    """
    tdi           = float(basin.get("tdi", 0.30))
    n_countries   = int(basin.get("n_countries", 2))
    dispute_level = basin.get("dispute_level", basin.get("tdi_risk", "MEDIUM"))
    un_articles   = basin.get("un_articles", [])

    # Component scores
    tdi_score  = tdi * 100.0 * 0.40

    # Country count: 1 country=0, 2=30, 3=60, 4+=100
    ctry_map   = {1: 0, 2: 30, 3: 60, 4: 80, 5: 90}
    ctry_score = ctry_map.get(min(n_countries, 5), 100) * 0.20

    # Dispute level
    dispute_map = {"MINIMAL": 0, "LOW": 25, "MEDIUM": 55, "HIGH": 90, "CRITICAL": 100}
    disp_score  = dispute_map.get(dispute_level.upper(), 50) * 0.25

    # UN articles
    art_score   = min(len(un_articles) / 9.0, 1.0) * 100.0 * 0.15

    total = tdi_score + ctry_score + disp_score + art_score

    # Conflict level
    if total >= 70:   level = "CRITICAL"
    elif total >= 50: level = "HIGH"
    elif total >= 30: level = "MEDIUM"
    elif total >= 15: level = "LOW"
    else:             level = "MINIMAL"

    # Triggered UN articles
    triggered = []
    hifd_proxy = tdi * 100.0  # use TDI as AHIFD proxy
    for art_id, art in UN_ARTICLES.items():
        if art_id in un_articles or hifd_proxy >= art["threshold_pct"]:
            triggered.append({
                "article": art_id,
                "title":   art["title"],
                "color":   art["color"],
            })

    # Relevant ICJ cases
    relevant_cases = find_relevant_cases(tdi, basin)

    # Legal summary
    art5  = hifd_proxy > 40
    art7  = hifd_proxy > 55
    art12 = hifd_proxy > 60
    art33 = hifd_proxy > 70

    legal_summary = []
    if art5:  legal_summary.append("Art.5 — Equitable utilization under question")
    if art7:  legal_summary.append("Art.7 — Significant harm threshold exceeded")
    if art12: legal_summary.append("Art.12 — Notification obligations apply")
    if art33: legal_summary.append("Art.33 — Dispute resolution recommended")

    return {
        "basin":          basin.get("name", "?"),
        "conflict_score": round(total, 1),
        "level":          level,
        "components": {
            "tdi_score":     round(tdi_score, 1),
            "country_score": round(ctry_score, 1),
            "dispute_score": round(disp_score, 1),
            "article_score": round(art_score, 1),
        },
        "triggered_articles": triggered,
        "relevant_cases":     relevant_cases,
        "legal_summary":      legal_summary,
        "hifd_proxy_pct":     round(hifd_proxy, 1),
        "n_countries":        n_countries,
    }


def find_relevant_cases(tdi: float, basin: dict) -> List[Dict]:
    """Find ICJ cases relevant to this basin's conflict profile."""
    basin_name = basin.get("name", "").lower()
    articles   = basin.get("un_articles", [])
    hifd       = tdi * 100.0
    relevant   = []

    for case in ICJ_CASES:
        score = 0
        # HIFD threshold match
        if hifd >= case["hifd_threshold"]:
            score += 3
        # Article overlap
        for art in case["articles"]:
            if art in articles:
                score += 2
        # Keyword match
        for kw in case["keywords"]:
            if kw in basin_name:
                score += 1
        if score >= 2:
            relevant.append({**case, "relevance_score": score})

    return sorted(relevant, key=lambda x: -x["relevance_score"])[:3]


# ── Auto-Protest Draft (Article 12) ──────────────────────────────────────────

def generate_protest_draft(basin: dict, lang: str = "en") -> str:
    """
    Generate auto-protest letter draft under UN 1997 Article 12.
    lang: 'en' or 'ar'
    """
    name         = basin.get("name", "?")
    cup          = basin.get("country_up", "Upstream State")
    cdn          = basin.get("country_dn", "Downstream State")
    dam          = basin.get("dam", "upstream dam")
    tdi          = float(basin.get("tdi", 0.40))
    hifd         = round(tdi * 100, 1)
    storage      = basin.get("storage_bcm", "N/A")
    un_arts      = ", ".join(basin.get("un_articles", ["Art.5", "Art.7"]))

    if lang == "ar":
        return f"""
═══════════════════════════════════════════════════════
مسودة احتجاج رسمي — إطار اتفاقية الأمم المتحدة لعام 1997
═══════════════════════════════════════════════════════

الموضوع: انتهاك المادة 12 من اتفاقية الأمم المتحدة للمجاري المائية الدولية (1997)
الحوض: {name}

إلى:
حكومة {cup}

من:
حكومة {cdn}

نشير إلى الإجراءات المتعلقة بـ {dam} التي تؤثر سلباً على حقوق دولة المصب في المياه.

وفقاً لتقييم HSAE، يبلغ عجز التدفق الناجم عن الإجراءات البشرية (AHIFD) نسبة {hifd}%،
وهو ما يتجاوز العتبات القانونية المحددة في:
  - المادة 5: الاستخدام المنصف والمعقول (العتبة: 40%)
  - المادة 7: الالتزام بعدم التسبب في ضرر جسيم (العتبة: 55%)
  - المادة 12: الإخطار بالتدابير المخططة

الوضع الراهن (السعة التخزينية: {storage} مليار م³) يستدعي:
1. الإخطار الفوري وفق أحكام المادة 12
2. فتح مفاوضات تشاورية وفق أحكام المادة 9
3. تقديم دراسة تقييم الأثر البيئي

المواد المنتهكة: {un_arts}

هذه المسودة مُولَّدة آلياً بواسطة HSAE v6.0.
ORCID: 0000-0003-0821-2991 — د. سيف الدين محمد جلال الدين القدير
═══════════════════════════════════════════════════════
""".strip()
    else:
        return f"""
═══════════════════════════════════════════════════════
OFFICIAL PROTEST DRAFT — UN 1997 WATERCOURSES CONVENTION
═══════════════════════════════════════════════════════

Re: Violation of Article 12, UN Convention on the Law of the Non-Navigational
    Uses of International Watercourses (1997)
Basin: {name}

To:   Government of {cup}
From: Government of {cdn}

We draw your attention to operations at {dam} which materially affect the
downstream riparian rights of {cdn}.

Per HSAE v6.0 assessment, the Alkhedir Human-Induced Flow Deficit (AHIFD)
stands at {hifd}%, exceeding legal thresholds under:
  - Art. 5  (equitable utilization threshold: 40%)
  - Art. 7  (significant harm threshold: 55%)
  - Art. 12 (notification obligation for planned measures)

Current conditions (storage: {storage} BCM) demand:
  1. Immediate notification per Art. 12 requirements
  2. Opening of consultations per Art. 9 data-sharing provisions
  3. Submission of Environmental Impact Assessment

Applicable Articles: {un_arts}

This draft is auto-generated by HSAE v6.0 AI Engine.
Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
═══════════════════════════════════════════════════════
""".strip()


# ── QGIS Dialog ───────────────────────────────────────────────────────────────

    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTextBrowser, QLabel, QPushButton, QComboBox, QFrame
# Compatibility alias for sensitivity_analysis import
def compute_atdi(inputs: dict) -> float:
    '''ATDI = 0.40*FRD + 0.20*SRI + 0.25*DI + 0.15*IPI'''
    return max(0.0, min(1.0,
        0.40*float(inputs.get('frd',0)) + 0.20*float(inputs.get('sri',0)) +
        0.25*float(inputs.get('di',0))  + 0.15*float(inputs.get('ipi',0))
    ))


def _basin_defaults(basin: dict) -> dict:
    """Compute realistic ATDI/HIFD defaults from basin physical parameters."""
    cap     = float(basin.get("cap", 5.0))
    disp    = int(basin.get("dispute_level", 0))
    country = basin.get("country", [])
    n       = len(country) if isinstance(country, list) else 2
    runoff  = float(basin.get("runoff_c", 0.30))
    atdi = min(95.0, max(5.0,
        15.0 + disp * 12.0 + min(cap / 2.0, 20.0) + (n - 2) * 8.0 + (1 - runoff) * 10.0
    ))
    hifd = min(80.0, max(5.0,
        8.0 + min(cap / 3.0, 15.0) + (1 - runoff) * 12.0 + disp * 5.0
    ))
    return {"atdi": round(atdi, 1), "hifd": round(hifd, 1)}


def render_conflict_page(basin: dict) -> None:
    import streamlit as st, plotly.graph_objects as go
    st.markdown("## ⚡ Conflict Index — Risk Assessment")
    st.caption("Composite conflict likelihood · ATDI + Political + Hydrological factors · Updates with basin selection")

    # ── Extract live basin values ──────────────────────────────────────────
    basin_name   = basin.get("name", "Unknown Basin")
    countries    = basin.get("country", ["Unknown"])
    n_countries  = len(countries) if isinstance(countries, list) else 1
    treaty       = basin.get("treaty", "UN1997")
    cap_bcm      = float(basin.get("cap", 10.0))
    area_km2     = float(basin.get("eff_cat_km2", 100000))
    context      = basin.get("context", "")

    # Basin-specific defaults from physical parameters
    _bd       = _basin_defaults(basin)
    _atdi_def = _bd["atdi"]
    _hifd_def = _bd["hifd"]
    _disp_raw    = int(basin.get("dispute_level", 0))
    _disp_labels = ["LOW", "LOW", "MEDIUM", "HIGH", "CRITICAL", "CRITICAL"]
    _disp_def    = _disp_labels[min(_disp_raw, 5)]
    _disp_idx    = ["LOW","MEDIUM","HIGH","CRITICAL"].index(_disp_def) if _disp_def in ["LOW","MEDIUM","HIGH","CRITICAL"] else 1

    # ── Input Controls ────────────────────────────────────────────────────
    st.info(f"🌍 **{basin_name}** · {', '.join(countries) if isinstance(countries,list) else countries} · Treaty: {treaty}")

    # Reset sliders when basin changes
    _bid = basin.get("id", basin.get("name", "default"))
    _prev_bid = st.session_state.get("_conf_basin_id", "")
    if _prev_bid != _bid:
        st.session_state[f"conf_atdi_{_bid}"] = _atdi_def
        st.session_state[f"conf_hifd_{_bid}"] = _hifd_def
        st.session_state["_conf_basin_id"] = _bid

    with st.expander("⚙️ Adjust Parameters", expanded=True):
        c1, c2, c3 = st.columns(3)
        atdi_in    = c1.slider("ATDI (%)", 0.0, 100.0,
                               st.session_state.get(f"conf_atdi_{_bid}", _atdi_def),
                               step=0.5, key=f"conf_atdi_{_bid}",
                               help=f"Basin: {basin_name} · Auto from physical params")
        hifd_in    = c2.slider("HIFD (%)", 0.0, 100.0,
                               st.session_state.get(f"conf_hifd_{_bid}", _hifd_def),
                               step=0.5, key=f"conf_hifd_{_bid}",
                               help="Human-Induced Flow Deficit")
        dispute_in = c3.selectbox("Dispute Level", ["LOW","MEDIUM","HIGH","CRITICAL"],
                                  index=_disp_idx,
                                  key=f"conf_disp_{_bid}",
                                  help="Political dispute intensity — pre-set from basin data")

    # ── Compute Conflict Index ─────────────────────────────────────────────
    _dispute_map = {"LOW": 0.15, "MEDIUM": 0.35, "HIGH": 0.60, "CRITICAL": 0.85}
    _cap_factor  = min(1.0, cap_bcm / 100.0)        # larger dam → higher risk
    _country_fac = min(1.0, (n_countries - 1) * 0.15)  # more countries → higher risk
    _disp_score  = _dispute_map[dispute_in]
    _atdi_score  = atdi_in / 100.0
    _hifd_score  = hifd_in / 100.0
    ci_value     = (0.35 * _atdi_score + 0.25 * _disp_score +
                    0.20 * _hifd_score + 0.12 * _country_fac + 0.08 * _cap_factor)
    ci_value     = max(0.0, min(1.0, ci_value))

    # Try full ML compute
    try:
        basin_live = dict(basin)
        basin_live.update({"gee_ATDI": atdi_in, "td_index": atdi_in/100,
                           "hifd": hifd_in/100, "gee_HIFD": hifd_in,
                           "dispute_level": dispute_in})
        ci_full = compute_conflict_index(basin_live)
        if ci_full and isinstance(ci_full, dict) and "conflict_index" in ci_full:
            ci_value = float(ci_full["conflict_index"])
    except Exception:
        ci_full = {}

    pol_score = round(_disp_score * 0.7 + _country_fac * 0.3, 2)
    hyd_score = round(_atdi_score * 0.6 + _hifd_score * 0.4, 2)
    risk_level = ("🟢 LOW" if ci_value < 0.25 else
                  "🟡 MEDIUM" if ci_value < 0.50 else
                  "🟠 HIGH"   if ci_value < 0.75 else "🔴 CRITICAL")

    # ── Metrics ───────────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Conflict Index",  f"{ci_value*100:.1f}%")
    m2.metric("Risk Level",      risk_level)
    m3.metric("Political Score", f"{pol_score:.2f}")
    m4.metric("Hydro Score",     f"{hyd_score:.2f}")
    m5.metric("Riparian States", str(n_countries))

    # ── Gauge ─────────────────────────────────────────────────────────────
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=ci_value * 100,
        delta={"reference": 50, "relative": False,
               "increasing": {"color": "#ef4444"},
               "decreasing": {"color": "#22c55e"}},
        gauge={"axis":      {"range": [0, 100], "tickcolor": "#E0E0E0"},
               "bar":       {"color": "#ef4444"},
               "bgcolor":   "#1E1E2E",
               "steps":     [{"range": [0,  25], "color": "#14532d"},
                              {"range": [25, 50], "color": "#713f12"},
                              {"range": [50, 75], "color": "#7c2d12"},
                              {"range": [75,100], "color": "#450a0a"}],
               "threshold": {"line": {"color": "#FFD600", "width": 3},
                             "thickness": 0.8, "value": 50}},
        title={"text": f"Conflict Risk — {basin_name}",
               "font": {"color": "#E0E0E0", "size": 13}}))
    fig.update_layout(template="plotly_dark", height=320,
                      paper_bgcolor="#0F1117", font=dict(color="#E0E0E0"))
    st.plotly_chart(fig, width='stretch')

    # ── Context ───────────────────────────────────────────────────────────
    if context:
        st.info(f"🌐 **Basin Context:** {context}")

    # ── ICJ Precedents ────────────────────────────────────────────────────
    try:
        cases = ci_full.get("relevant_cases", []) if ci_full else []
    except Exception:
        cases = []

    if not cases:
        cases = [
            {"case": "Gabčíkovo-Nagymaros (Hungary v. Slovakia)", "year": "1997",
             "relevance": "Equitable utilisation · significant harm doctrine · Art.5 & 7"},
            {"case": "Pulp Mills on the River Uruguay", "year": "2010",
             "relevance": "Environmental impact assessment · notification Art.12"},
            {"case": "Nile Basin Initiative Framework", "year": "2010",
             "relevance": "Multi-state water sharing · direct GERD/Nile precedent"},
        ]

    st.subheader("⚖️ Relevant ICJ/PCA Precedents")
    for c in cases[:3]:
        st.markdown(f"""
<div style='background:#1E2A3A;border-left:4px solid #3B82F6;
            padding:0.7rem 1rem;border-radius:6px;margin:0.4rem 0'>
  <b style='color:#60A5FA'>{c.get("case","—")}</b>
  <span style='color:#94A3B8;font-size:0.8rem;float:right'>{c.get("year","—")}</span><br>
  <span style='color:#CBD5E1;font-size:0.85rem'>{c.get("relevance","—")}</span>
</div>""", unsafe_allow_html=True)

    # ── Legal Assessment ───────────────────────────────────────────────────
    st.markdown("---")
    if ci_value >= 0.75:
        st.error(f"🔴 **Critical Risk ({ci_value*100:.0f}%)** — ICJ referral recommended under Art.33 UNWC 1997.")
    elif ci_value >= 0.50:
        st.warning(f"🟠 **High Risk ({ci_value*100:.0f}%)** — PCA arbitration or UN mediation recommended.")
    elif ci_value >= 0.25:
        st.info(f"🟡 **Medium Risk ({ci_value*100:.0f}%)** — Bilateral negotiation with data sharing recommended.")
    else:
        st.success(f"🟢 **Low Risk ({ci_value*100:.0f}%)** — Continue monitoring via HSAE.")
