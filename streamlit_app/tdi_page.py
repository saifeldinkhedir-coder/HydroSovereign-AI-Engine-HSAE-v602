"""
tdi_page.py  ─  HSAE v6.01
============================
Canonical TDI / ATDI / AFSF Interactive Page
Symbols standardized per Alkhedir (2026) RSE-2 canonical definition.

ε = 0.001 BCM/day  ·  α = 0.30  ·  k = 30 days
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Import canonical engine ────────────────────────────────────────────────
try:
    from hsae_tdi import (
        compute_tdi, compute_atdi, compute_afsf,
        compute_forensic_score, add_tdi_to_df,
        tdi_legal_status, tdi_summary,
        TDI_EPSILON, TDI_ALPHA, TDI_ROLL_DAYS,
        TDI_ART5_THR, TDI_ART7_THR, TDI_ART9_THR,
    )
    _HAS_TDI = True
except ImportError:
    _HAS_TDI = False


def render_tdi_page(basin: dict):
    """Render the canonical TDI/ATDI/AFSF page."""

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1A237E,#283593);
                padding:1.2rem 1.6rem;border-radius:10px;margin-bottom:1rem'>
      <h2 style='color:#fff;margin:0;font-size:1.5rem'>
        📐  Canonical TDI · ATDI · AFSF  Index Engine
      </h2>
      <p style='color:#90CAF9;margin:0.3rem 0 0;font-size:0.85rem'>
        Single Source of Truth — Alkhedir (2026) · RSE-2 canonical formulation
      </p>
    </div>
    """, unsafe_allow_html=True)

    if not _HAS_TDI:
        st.error("⚠️ hsae_tdi.py not found. Please ensure it is in the repository root.")
        return

    # ── Canonical Formula Display ─────────────────────────────────────────
    with st.expander("📐 Canonical Formulas & Constants", expanded=True):
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(r"""
**Canonical Formulation (Alkhedir, 2026 — RSE-2)**

$$I_{\text{adj},t} = \max\!\left(0,\; I_{\text{in},t} - \alpha\cdot(ET_{0,t} + ET_{\text{MODIS},t})\right)$$

$$\text{TDI}_t = \max\!\left(0,\; \frac{I_{\text{adj},t} - Q_{\text{out},t}}{I_{\text{adj},t} + \varepsilon}\right) \in [0,1]$$

$$\text{ATDI} = \overline{\text{TDI}} \times 100 \quad [\%]$$

$$\text{AFSF} = \max\!\left(\text{rolling}_k(\text{TDI})\right) \times 100 \quad [\%]$$

$$F_{\text{score}} = \overline{\text{TDI}} \cdot \bigl(1 + \dot{\text{TDI}}\bigr)$$
""")
        with col2:
            st.markdown("**Constants**")
            st.dataframe(pd.DataFrame({
                "Symbol": ["ε", "α", "k", "Art.5 θ", "Art.7 θ", "Art.9 θ"],
                "Value":  [f"{TDI_EPSILON}", f"{TDI_ALPHA}",
                           f"{TDI_ROLL_DAYS} days",
                           f"{TDI_ART5_THR*100:.0f}%",
                           f"{TDI_ART7_THR*100:.0f}%",
                           f"{TDI_ART9_THR*100:.0f}%"],
                "Description": [
                    "Denominator stabiliser (BCM/day)",
                    "ET partitioning coefficient",
                    "AFSF rolling window",
                    "Equitable use threshold",
                    "No significant harm threshold",
                    "Data withholding threshold",
                ],
            }), width='stretch', hide_index=True)

    st.markdown("---")

    # ── Data Input ────────────────────────────────────────────────────────
    st.subheader("📥 Input Data")

    tab1, tab2 = st.tabs(["📡 Use GEE Session Data", "📂 Upload CSV"])

    df_input = None

    with tab1:
        # Try to get data from session state (Direct GEE mode)
        P_mm  = st.session_state.get("P_mm", [])
        T_C   = st.session_state.get("T_C", [])
        tws   = st.session_state.get("tws_cm", [])

        if P_mm:
            n = len(P_mm)
            # Convert P (mm/day) to BCM/day using basin area
            area_km2 = basin.get("eff_cat_km2", 174000)
            P_bcm = [p * area_km2 / 1e6 / 1000 for p in P_mm]

            # Simulated Q_out from session or derive from P
            Q_sim = st.session_state.get("Q_sim", [])
            if not Q_sim:
                # Estimate: Q_out ≈ 40% of P (typical Blue Nile runoff ratio)
                Q_sim = [p * 0.40 for p in P_bcm]

            Q_bcm = [q * area_km2 / 1e6 / 86400 if q < 10000 else q / 1e9 for q in Q_sim]

            dates = pd.date_range("2025-01-01", periods=n, freq="D")
            df_input = pd.DataFrame({
                "Date":        dates,
                "Inflow_BCM":  P_bcm,
                "Outflow_BCM": Q_bcm[:n] if len(Q_bcm) >= n else Q_bcm + [Q_bcm[-1]]*(n-len(Q_bcm)),
            })
            st.success(f"✅ GEE data loaded: {n} days · Basin area: {area_km2:,.0f} km²")
            st.caption(f"P mean = {np.mean(P_mm):.2f} mm/day · Q sim mean = {np.mean(Q_sim):.2f} m³/s")
        else:
            st.info("⚠️ No GEE data in session. Run **Direct GEE** first, or upload CSV below.")

    with tab2:
        st.markdown("""**CSV format required:**
```
Date, Inflow_BCM, Outflow_BCM [, ET0_mm_day, MODIS_ET_mm, Effective_Area]
2025-01-01, 0.45, 0.18
```
All flow columns in **BCM/day** (Billion Cubic Meters per day).""")

        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded:
            try:
                df_up = pd.read_csv(uploaded, parse_dates=["Date"])
                df_up.columns = df_up.columns.str.strip()
                if "Inflow_BCM" in df_up.columns and "Outflow_BCM" in df_up.columns:
                    df_input = df_up
                    st.success(f"✅ Loaded {len(df_up)} rows")
                    st.dataframe(df_up.head(5), width='stretch')
                else:
                    st.error("Missing required columns: Inflow_BCM, Outflow_BCM")
            except Exception as e:
                st.error(f"Parse error: {e}")

    if df_input is None or df_input.empty:
        st.warning("Please load data (GEE session or CSV) to compute TDI.")
        return

    # ── Parameters Override ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚙️ Parameters")
    c1, c2, c3 = st.columns(3)
    eps   = c1.number_input("ε  (denominator stabiliser, BCM/day)",
                            value=TDI_EPSILON, format="%.4f",
                            min_value=1e-6, max_value=0.01, step=0.0001)
    alpha = c2.number_input("α  (ET partitioning coefficient)",
                            value=TDI_ALPHA, format="%.2f",
                            min_value=0.0, max_value=1.0, step=0.01)
    roll  = c3.number_input("k  (AFSF rolling window, days)",
                            value=int(TDI_ROLL_DAYS),
                            min_value=7, max_value=90, step=1)

    # ── Compute ───────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("🔢 Compute TDI · ATDI · AFSF", type="primary",
                 width='stretch'):

        df_result = add_tdi_to_df(
            df_input,
            inflow_col  = "Inflow_BCM",
            outflow_col = "Outflow_BCM",
            et_pm_col   = "ET0_mm_day"   if "ET0_mm_day"   in df_input.columns else "__none__",
            et_mod_col  = "MODIS_ET_mm"  if "MODIS_ET_mm"  in df_input.columns else "__none__",
            area_col    = "Effective_Area" if "Effective_Area" in df_input.columns else "__none__",
        )

        # Override with user params if different from defaults
        I = df_input["Inflow_BCM"].values
        Q = df_input["Outflow_BCM"].values
        tdi_arr = compute_tdi(I, Q, epsilon=eps, alpha=alpha)
        df_result["TDI_adj"]  = tdi_arr
        df_result["ATDI_pct"] = tdi_arr * 100
        df_result["TDI_roll30"] = pd.Series(tdi_arr).rolling(int(roll), min_periods=1).mean().values

        summ = tdi_summary(df_result)
        atdi_val = float(np.nanmean(tdi_arr) * 100)
        afsf_val = float(pd.Series(tdi_arr).rolling(int(roll), min_periods=1).mean().max() * 100)
        status, color, arts = tdi_legal_status(atdi_val)

        # ── Metric Cards ─────────────────────────────────────────────────
        st.subheader("📊 Results")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("ATDI", f"{atdi_val:.1f}%",
                  help="Alkhedir Transparency Deficit Index — annual mean")
        m2.metric("AFSF", f"{afsf_val:.1f}%",
                  help=f"Alkhedir Forensic Signal Factor — {roll}-day peak rolling TDI")
        m3.metric("Art.7 Days",
                  f"{summ.get('art7_days', 0)}",
                  help="Days TDI ≥ 40% (no significant harm threshold)")
        m4.metric("Art.9 Days",
                  f"{summ.get('art9_days', 0)}",
                  help="Days TDI ≥ 55% (data withholding threshold)")
        m5.metric("Legal Status", status.split()[0] + " " + status.split()[1],
                  help=arts)

        # Legal zone banner
        st.markdown(f"""
        <div style='background:{color}22;border-left:5px solid {color};
                    padding:0.8rem 1.2rem;border-radius:6px;margin:0.5rem 0'>
          <b style='color:{color};font-size:1.1rem'>{status}</b><br>
          <span style='color:#555;font-size:0.85rem'>Triggered: {arts}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Chart 1: Daily TDI Time Series ───────────────────────────────
        dates = df_result["Date"] if "Date" in df_result.columns else pd.date_range("2025-01-01", periods=len(tdi_arr), freq="D")
        fig1 = go.Figure()

        # Article zone shading
        fig1.add_hrect(y0=TDI_ART7_THR*100, y1=TDI_ART9_THR*100,
                       fillcolor="#f97316", opacity=0.12, line_width=0,
                       annotation_text="Art. 7 zone", annotation_position="top right")
        fig1.add_hrect(y0=TDI_ART9_THR*100, y1=100,
                       fillcolor="#ef4444", opacity=0.12, line_width=0,
                       annotation_text="Art. 9 zone", annotation_position="top right")
        fig1.add_hrect(y0=TDI_ART5_THR*100, y1=TDI_ART7_THR*100,
                       fillcolor="#eab308", opacity=0.10, line_width=0,
                       annotation_text="Art. 5 zone", annotation_position="top right")

        # Daily TDI
        fig1.add_trace(go.Scatter(
            x=dates, y=df_result["ATDI_pct"],
            mode="lines", name="Daily ATDI (%)",
            line=dict(color="#3B82F6", width=1.2),
        ))
        # Rolling mean
        fig1.add_trace(go.Scatter(
            x=dates, y=df_result["TDI_roll30"] * 100,
            mode="lines", name=f"{roll}-day Rolling Mean",
            line=dict(color="#1D4ED8", width=2.5, dash="dot"),
        ))
        # Annual mean line
        fig1.add_hline(y=atdi_val, line_dash="dash",
                       line_color="#DC2626", line_width=2,
                       annotation_text=f"ATDI = {atdi_val:.1f}%",
                       annotation_position="bottom right")

        # Threshold lines
        for thr, label, col in [
            (TDI_ART5_THR*100, "Art.5 (25%)", "#eab308"),
            (TDI_ART7_THR*100, "Art.7 (40%)", "#f97316"),
            (TDI_ART9_THR*100, "Art.9 (55%)", "#ef4444"),
        ]:
            fig1.add_hline(y=thr, line_dash="dot", line_color=col, line_width=1,
                           annotation_text=label, annotation_position="top left")

        fig1.update_layout(
            title=f"Daily ATDI Time Series — {basin.get('name','Basin')} "
                  f"(ε={eps}, α={alpha})",
            xaxis_title="Date",
            yaxis_title="ATDI (%)",
            yaxis=dict(range=[0, min(100, max(atdi_val*1.8, 70))]),
            legend=dict(orientation="h", y=1.05),
            height=420,
            plot_bgcolor="#F8FAFC",
        )
        st.plotly_chart(fig1, width='stretch')

        # ── Chart 2: Inflow vs Outflow ─────────────────────────────────
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=dates, y=df_input["Inflow_BCM"],
            mode="lines", name="I_adj (Inflow, BCM/day)",
            line=dict(color="#059669", width=1.5),
            fill="tozeroy", fillcolor="rgba(5,150,105,0.08)"
        ))
        fig2.add_trace(go.Scatter(
            x=dates, y=df_input["Outflow_BCM"],
            mode="lines", name="Q_out (Outflow, BCM/day)",
            line=dict(color="#DC2626", width=1.5),
            fill="tozeroy", fillcolor="rgba(220,38,38,0.08)"
        ))
        fig2.update_layout(
            title="Inflow vs Outflow (BCM/day)",
            xaxis_title="Date", yaxis_title="BCM/day",
            height=300, plot_bgcolor="#F8FAFC",
            legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(fig2, width='stretch')

        # ── Monthly ATDI Bar ───────────────────────────────────────────
        try:
            # Build monthly data directly from tdi_arr and dates
            import calendar
            _dates_list = list(pd.to_datetime(dates))
            _monthly_dict = {}
            for _d, _v in zip(_dates_list, tdi_arr * 100):
                _m = _d.month
                _monthly_dict.setdefault(_m, []).append(_v)
            _months_out = sorted(_monthly_dict.keys())
            _month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                            7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
            _mean_vals = [float(pd.Series(_monthly_dict[m]).mean()) for m in _months_out]
            _labels = [_month_names.get(m, str(m)) for m in _months_out]
            _colors = ["#ef4444" if v >= TDI_ART9_THR*100
                       else "#f97316" if v >= TDI_ART7_THR*100
                       else "#eab308" if v >= TDI_ART5_THR*100
                       else "#22c55e" for v in _mean_vals]
        except Exception:
            _labels = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]
            _mean_vals = [atdi_val] * 12
            _colors = ["#f97316"] * 12

        fig3 = go.Figure(go.Bar(
            x=_labels, y=_mean_vals,
            marker_color=_colors,
            text=[f"{v:.1f}%" for v in _mean_vals],
            textposition="outside",
        ))
        fig3.add_hline(y=TDI_ART7_THR*100, line_dash="dash",
                       line_color="#f97316", line_width=2,
                       annotation_text="Art. 7 (40%)")
        fig3.update_layout(
            title="Monthly Mean ATDI (%) — UNWC Zone Classification",
            xaxis_title="Month", yaxis_title="ATDI (%)",
            yaxis=dict(range=[0, max(100, max(_mean_vals)*1.15) if _mean_vals else 100]),
            height=320, plot_bgcolor="#F8FAFC",
        )
        st.plotly_chart(fig3, width='stretch')

        # ── Download ───────────────────────────────────────────────────
        st.markdown("---")
        out_cols = ["Date", "Inflow_BCM", "Outflow_BCM",
                    "TDI_adj", "ATDI_pct", "TDI_roll30",
                    "TDI_art5_flag", "TDI_art7_flag", "TDI_art9_flag"]
        out_df = df_result[[c for c in out_cols if c in df_result.columns]].copy()
        out_df.columns = [
            "Date", "Inflow_BCM", "Outflow_BCM",
            "TDI (0–1)", "ATDI (%)", f"TDI_roll{roll}",
            "Art.5 Flag", "Art.7 Flag", "Art.9 Flag"
        ][:len(out_df.columns)]

        csv_bytes = out_df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download TDI Results CSV",
            csv_bytes,
            f"HSAE_TDI_{basin.get('id','basin')}_eps{eps}_alpha{alpha}.csv",
            "text/csv",
            width='stretch',
        )

        st.caption(
            f"ε = {eps} BCM/day · α = {alpha} · k = {roll} days · "
            f"Canonical formula: Alkhedir (2026) · HSAE v6.01"
        )

    # ── Legal Pathway ──────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚖️ Legal Pathway Assessment")
    _atdi_lp = st.session_state.get("gee_ATDI",
               float(basin.get("gee_ATDI", basin.get("td_index", 0.435))))
    _atdi_lp = _atdi_lp if _atdi_lp > 1 else _atdi_lp * 100

    if _atdi_lp >= TDI_ART9_THR * 100:
        st.error(f"🔴 **Art.9 + Art.7 Zone (ATDI={_atdi_lp:.1f}%)** — "
                 "Data withholding + No significant harm obligations triggered. "
                 "Recommend: ICJ referral under Art.33 UNWC 1997.")
    elif _atdi_lp >= TDI_ART7_THR * 100:
        st.warning(f"🟠 **Art.7 Zone (ATDI={_atdi_lp:.1f}%)** — "
                   "No significant harm obligation triggered. "
                   "Recommend: PCA arbitration or Joint Commission.")
    elif _atdi_lp >= TDI_ART5_THR * 100:
        st.info(f"🟡 **Art.5 Zone (ATDI={_atdi_lp:.1f}%)** — "
                "Equitable utilisation risk. "
                "Recommend: Bilateral negotiation with data sharing.")
    else:
        st.success(f"🟢 **Compliant (ATDI={_atdi_lp:.1f}%)** — "
                   "Within acceptable range. Continue monitoring.")

    st.caption("Legal thresholds: Art.5 ≥ 25% · Art.7 ≥ 40% · Art.9 ≥ 55% "
               "| Per Alkhedir (2026) RSE-2 canonical formulation")
