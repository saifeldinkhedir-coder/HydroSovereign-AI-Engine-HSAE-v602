"""
arabic_ui.py — HSAE v10.0 Arabic/English Bilingual Interface
=============================================================
Provides RTL Arabic support for all HSAE Streamlit pages.
Includes:
  - Complete translation dictionary (AR/EN)
  - RTL CSS injection
  - Arabic metric labels
  - Bilingual SITREP generator
  - Arabic legal text for UN 1997 articles

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
from typing import Dict, Optional

# ══════════════════════════════════════════════════════════════════════════════
# Translation dictionary
# ══════════════════════════════════════════════════════════════════════════════
TRANSLATIONS: Dict[str, Dict[str, str]] = {

    # ── Navigation ──────────────────────────────────────────────────────────
    "Intro":                    {"ar": "مقدمة",                  "en": "Intro"},
    "Dashboard":                {"ar": "لوحة التحكم",            "en": "Dashboard"},
    "Hybrid DSS":               {"ar": "نظام الدعم الهجين",      "en": "Hybrid DSS"},
    "Legal Nexus":              {"ar": "الرابط القانوني",        "en": "Legal Nexus"},
    "Water Balance":            {"ar": "الموازنة المائية",       "en": "Water Balance"},
    "HBV Model":                {"ar": "نموذج HBV",              "en": "HBV Model"},
    "Groundwater":              {"ar": "المياه الجوفية",         "en": "Groundwater"},
    "Water Quality":            {"ar": "جودة المياه",            "en": "Water Quality"},
    "Validation":               {"ar": "التحقق والمعايرة",       "en": "Validation"},
    "GRACE-FO":                 {"ar": "الإجمالي المائي (GRACE)","en": "GRACE-FO TWS"},
    "SMAP":                     {"ar": "رطوبة التربة (SMAP)",    "en": "SMAP Soil Moisture"},
    "GloFAS":                   {"ar": "توقعات GloFAS",          "en": "GloFAS Forecast"},
    "AI Ensemble":              {"ar": "التجميع الذكاء الاصطناعي","en": "AI Ensemble"},
    "Digital Twin":             {"ar": "التوأم الرقمي",          "en": "Digital Twin"},
    "Sensitivity":              {"ar": "تحليل الحساسية",         "en": "Sensitivity Analysis"},
    "Climate":                  {"ar": "سيناريوهات المناخ",      "en": "Climate SSP"},
    "Treaty Engine":            {"ar": "محرك المعاهدات",         "en": "Treaty Engine"},
    "Treaty Diff":              {"ar": "فحص الامتثال للمعاهدات", "en": "Treaty Diff"},
    "Negotiation AI":           {"ar": "الذكاء التفاوضي",        "en": "Negotiation AI"},
    "ICJ Dossier":              {"ar": "ملف المحكمة الدولية",    "en": "ICJ Dossier"},
    "Global Rankings":          {"ar": "التصنيف العالمي",        "en": "Global Rankings"},
    "Run Analysis":             {"ar": "تشغيل التحليل الكامل",   "en": "Run Analysis"},
    "Benchmark":                {"ar": "المقارنة المرجعية",       "en": "Benchmark"},
    "WebGIS":                   {"ar": "خريطة GIS التفاعلية",    "en": "WebGIS"},
    "GRDC Manager":             {"ar": "مدير بيانات GRDC",       "en": "GRDC Manager"},
    "Case Study":               {"ar": "دراسة الحالة — سد النهضة","en": "Case Study GERD"},
    "Alerts":                   {"ar": "التنبيهات",              "en": "Alerts"},
    "Operations Room":          {"ar": "غرفة العمليات",          "en": "Operations Room"},
    "Audit Trail":              {"ar": "سجل التدقيق",            "en": "Audit Trail"},
    "DevOps":                   {"ar": "الحوسبة السحابية",       "en": "DevOps"},
    "API Status":               {"ar": "حالة API",               "en": "API Status"},
    "Sediment":                 {"ar": "الرواسب والترسيب",       "en": "Sediment Transport"},
    "Uncertainty":              {"ar": "عدم اليقين",             "en": "Uncertainty Analysis"},

    # ── Indices ─────────────────────────────────────────────────────────────
    "ATDI":   {"ar": "مؤشر التبعية العابرة للحدود (ATDI)",  "en": "ATDI"},
    "AHIFD":  {"ar": "مؤشر عجز التدفق الهيدرولوجي (AHIFD)","en": "AHIFD"},
    "ATCI":   {"ar": "مؤشر الامتثال للمعاهدات (ATCI)",      "en": "ATCI"},
    "NSE":    {"ar": "معامل كفاءة ناش-ساتكليف",             "en": "NSE"},
    "KGE":    {"ar": "كفاءة كلينج-غوبتا",                   "en": "KGE"},
    "WQI":    {"ar": "مؤشر جودة المياه",                    "en": "WQI"},
    "DCDI":   {"ar": "مؤشر تدهور المجرى المائي",            "en": "DCDI"},

    # ── Units & labels ────────────────────────────────────────────────────
    "BCM":    {"ar": "مليار متر مكعب",   "en": "BCM"},
    "Mt/yr":  {"ar": "مليون طن / سنة",   "en": "Mt/yr"},
    "m³/s":   {"ar": "متر مكعب / ثانية", "en": "m³/s"},
    "mm/day": {"ar": "ملم / يوم",         "en": "mm/day"},
    "°C":     {"ar": "درجة مئوية",        "en": "°C"},

    # ── Actions ──────────────────────────────────────────────────────────
    "Run Analysis":   {"ar": "تشغيل التحليل", "en": "Run Analysis"},
    "Download":       {"ar": "تحميل",          "en": "Download"},
    "Upload":         {"ar": "رفع ملف",        "en": "Upload"},
    "Export":         {"ar": "تصدير",          "en": "Export"},
    "Refresh":        {"ar": "تحديث",          "en": "Refresh"},
    "Reset":          {"ar": "إعادة ضبط",      "en": "Reset"},

    # ── Status messages ──────────────────────────────────────────────────
    "Loading...":     {"ar": "جارٍ التحميل...",     "en": "Loading..."},
    "Complete":       {"ar": "اكتمل",               "en": "Complete"},
    "Error":          {"ar": "خطأ",                  "en": "Error"},
    "Warning":        {"ar": "تحذير",               "en": "Warning"},
    "No data":        {"ar": "لا توجد بيانات",       "en": "No data"},

    # ── UN 1997 Articles ─────────────────────────────────────────────────
    "Art.5":  {"ar": "المادة 5: الانتفاع المنصف والمعقول",         "en": "Art.5: Equitable Utilization"},
    "Art.7":  {"ar": "المادة 7: عدم الإضرار الجسيم",               "en": "Art.7: No Significant Harm"},
    "Art.9":  {"ar": "المادة 9: تبادل البيانات والمعلومات",         "en": "Art.9: Data Exchange"},
    "Art.12": {"ar": "المادة 12: الإخطار المسبق",                   "en": "Art.12: Prior Notification"},
    "Art.20": {"ar": "المادة 20: حماية النظم البيئية",              "en": "Art.20: Ecosystem Protection"},
    "Art.33": {"ar": "المادة 33: تسوية النزاعات",                   "en": "Art.33: Dispute Settlement"},
}


# ══════════════════════════════════════════════════════════════════════════════
# Translation function
# ══════════════════════════════════════════════════════════════════════════════
def t(key: str, lang: str = "en") -> str:
    """Translate a key to Arabic or English."""
    lang = lang.lower()
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(lang, key)
    return key


def t_unit(value: float, unit_key: str, lang: str = "en") -> str:
    """Format a value with a translated unit."""
    unit = t(unit_key, lang)
    return f"{value:,.2f} {unit}"


# ══════════════════════════════════════════════════════════════════════════════
# RTL CSS injection for Streamlit
# ══════════════════════════════════════════════════════════════════════════════
RTL_CSS = """
<style>
/* Arabic RTL support for HSAE */
.arabic-text {
    direction: rtl;
    text-align: right;
    font-family: 'Amiri', 'Cairo', 'Tahoma', Arial, sans-serif;
    font-size: 1.05rem;
    line-height: 1.8;
}
.bilingual-card {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin: 0.5rem 0;
}
.lang-ar {
    direction: rtl;
    text-align: right;
    border-right: 3px solid #10b981;
    padding-right: 0.8rem;
    font-family: 'Cairo', Tahoma, sans-serif;
    color: #34d399;
}
.lang-en {
    direction: ltr;
    text-align: left;
    border-left: 3px solid #3b82f6;
    padding-left: 0.8rem;
    color: #60a5fa;
}
/* Arabic metric cards */
.metric-ar .metric-value { font-size: 1.8rem; font-weight: 700; }
.metric-ar .metric-label { direction: rtl; font-size: 0.85rem; color: #94a3b8; }
</style>
"""

def inject_rtl_css():
    """Inject RTL CSS into Streamlit page."""
    try:
        import streamlit as st
        st.markdown(RTL_CSS, unsafe_allow_html=True)
    except ImportError:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Bilingual metric display
# ══════════════════════════════════════════════════════════════════════════════
def bilingual_metric(label_en: str, label_ar: str, value: str,
                     delta: Optional[str] = None, lang: str = "en"):
    """Display a metric with bilingual label."""
    try:
        import streamlit as st
        label = label_ar if lang == "ar" else label_en
        if delta:
            st.metric(label, value, delta)
        else:
            st.metric(label, value)
    except ImportError:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Bilingual SITREP generator
# ══════════════════════════════════════════════════════════════════════════════
def generate_bilingual_sitrep(
    basin_name: str,
    atdi: float,
    ahifd_pct: float,
    atci: float,
    nse: float,
    n_violations: int,
    alerts: list,
) -> Dict[str, str]:
    """
    Generate a bilingual (EN + AR) Situation Report (SITREP).
    Extends the v6 OpsRoom SITREP with Arabic translation.
    """
    from datetime import datetime
    ts  = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    ts_ar = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Risk level
    if atdi > 0.70:
        risk_en = "🔴 HIGH"
        risk_ar = "🔴 عالٍ"
    elif atdi > 0.45:
        risk_en = "🟡 MODERATE"
        risk_ar = "🟡 متوسط"
    else:
        risk_en = "🟢 LOW"
        risk_ar = "🟢 منخفض"

    alerts_en = "\n".join(f"  • {a}" for a in alerts[:5]) if alerts else "  • None"
    alerts_ar = "\n".join(f"  • {a}" for a in alerts[:5]) if alerts else "  • لا توجد تنبيهات"

    sitrep_en = f"""
╔══════════════════════════════════════════════════════════════╗
║  HSAE DAILY SITUATION REPORT (SITREP) — ENGLISH             ║
╟──────────────────────────────────────────────────────────────╢
║  Basin  : {basin_name:<50} ║
║  Date   : {ts:<50} ║
╠══════════════════════════════════════════════════════════════╣
║  KEY INDICES                                                  ║
║  ─────────────────────────────────────────────────────────── ║
║  ATDI  (Dependency Index)  : {atdi:.3f}  [{risk_en:<10}]          ║
║  AHIFD (Flow Deficit)      : {ahifd_pct:.1f}%                      ║
║  ATCI  (Treaty Compliance) : {atci:.1f}/100                      ║
║  NSE   (Model Performance) : {nse:.3f}                         ║
║  Legal Violations          : {n_violations} article(s)              ║
╠══════════════════════════════════════════════════════════════╣
║  ACTIVE ALERTS                                               ║
{alerts_en}
╚══════════════════════════════════════════════════════════════╝
"""

    sitrep_ar = f"""
╔══════════════════════════════════════════════════════════════╗
║  التقرير اليومي للحالة (SITREP) — نظام HSAE v10.0           ║
╟──────────────────────────────────────────────────────────────╢
║  الحوض  : {basin_name[:48]:<48} ║
║  التاريخ: {ts_ar:<50} ║
╠══════════════════════════════════════════════════════════════╣
║  المؤشرات الرئيسية                                           ║
║  ─────────────────────────────────────────────────────────── ║
║  ATDI  (مؤشر التبعية)      : {atdi:.3f}  [{risk_ar}]          ║
║  AHIFD (عجز التدفق)        : {ahifd_pct:.1f}%                      ║
║  ATCI  (الامتثال القانوني) : {atci:.1f}/100                      ║
║  NSE   (أداء النموذج)      : {nse:.3f}                         ║
║  الانتهاكات القانونية      : {n_violations} مادة                     ║
╠══════════════════════════════════════════════════════════════╣
║  التنبيهات النشطة                                            ║
{alerts_ar}
╚══════════════════════════════════════════════════════════════╝
"""

    return {"en": sitrep_en.strip(), "ar": sitrep_ar.strip()}


# ══════════════════════════════════════════════════════════════════════════════
# Language selector widget
# ══════════════════════════════════════════════════════════════════════════════
def language_selector() -> str:
    """Streamlit language selector. Returns 'en' or 'ar'."""
    try:
        import streamlit as st
        lang = st.session_state.get("ui_language", "en")
        col1, col2 = st.columns([3, 1])
        with col2:
            selected = st.selectbox(
                "🌐 Language / اللغة",
                options=["English", "العربية"],
                index=0 if lang == "en" else 1,
                key="lang_selector",
                label_visibility="collapsed",
            )
        new_lang = "ar" if selected == "العربية" else "en"
        st.session_state["ui_language"] = new_lang
        if new_lang == "ar":
            inject_rtl_css()
        return new_lang
    except ImportError:
        return "en"


# ══════════════════════════════════════════════════════════════════════════════
# Arabic legal text for UN 1997
# ══════════════════════════════════════════════════════════════════════════════
UN1997_AR: Dict[str, str] = {
    "Art.5":  ("تستخدم دول المجرى المائي مجرى المياه الدولي الواقع في إقليمها استخداماً "
               "منصفاً ومعقولاً. ويجوز لها الانتفاع به على وجه الخصوص ووضعه موضع التنفيذ "
               "بقصد تحقيق الاستخدام الأمثل والاستدامة الكافية له، مع مراعاة مصالح دول "
               "المجرى المائي المعنية الأخرى."),
    "Art.7":  ("تتخذ دول المجرى المائي، عند استخدام مجرى مياه دولي داخل أراضيها، كافة "
               "الاحتياطات الملائمة لمنع إلحاق ضرر جسيم بدول المجرى المائي الأخرى."),
    "Art.9":  ("تتبادل دول المجرى المائي بصفة منتظمة البيانات والمعلومات المتعلقة بحالة "
               "مجرى المياه، ولا سيما البيانات ذات الطابع الهيدرولوجي والمناخي."),
    "Art.12": ("قبل أن تضع دولة مجرى المائي تدابير مقترحة موضع التنفيذ تكون قابلة لإحداث "
               "أثر ضار بليغ في دول مجرى المائي الأخرى، تقدم إخطاراً إلى تلك الدول."),
    "Art.20": ("تحمي دول المجرى المائي وتصون النظم الإيكولوجية للمجاري الدولية وتمنع "
               "الإخلال بها."),
    "Art.33": ("إذا نشأ خلاف بين دولتين أو أكثر من دول المجرى المائي بشأن تفسير هذه "
               "الاتفاقية أو تطبيقها، تلتمس تلك الدول تسوية ذلك الخلاف بالوسائل السلمية."),
}


def get_article_text_ar(article: str) -> str:
    """Get Arabic text for a UN 1997 article."""
    return UN1997_AR.get(article, f"النص العربي للمادة {article} غير متاح.")


# ══════════════════════════════════════════════════════════════════════════════
# Bilingual card HTML
# ══════════════════════════════════════════════════════════════════════════════
def bilingual_card_html(text_en: str, text_ar: str, title: str = "") -> str:
    """Generate an HTML card with side-by-side English and Arabic."""
    title_html = f"<h4 style='color:#10b981;margin:0 0 .5rem 0'>{title}</h4>" if title else ""
    return f"""
<div style='background:#161b22;border:1px solid #30363d;border-radius:10px;padding:1rem;margin:.5rem 0;'>
  {title_html}
  <div style='display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;'>
    <div style='direction:ltr;text-align:left;border-left:3px solid #3b82f6;padding-left:.8rem;color:#93c5fd;font-size:.9rem;line-height:1.7;'>
      {text_en}
    </div>
    <div style='direction:rtl;text-align:right;border-right:3px solid #10b981;padding-right:.8rem;color:#6ee7b7;font-family:Tahoma,sans-serif;font-size:.9rem;line-height:1.9;'>
      {text_ar}
    </div>
  </div>
</div>
"""
