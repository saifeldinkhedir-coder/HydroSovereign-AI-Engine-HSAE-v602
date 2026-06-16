"""
upload_real_data.py — HSAE v6.01 Real Data Upload Page
========================================================
Allows users to upload real discharge data from any source:
- GRDC export format (.txt)
- USGS tab-delimited (.txt)
- Generic CSV (date + discharge columns)
- WaterML2 CSV exports

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import re
from datetime import datetime

# ── Constants ──────────────────────────────────────────────────────────────────
ALPHA   = 0.30
EPSILON = 0.001

def render_upload_real_data():
    st.title("📂 Upload Real Data")
    st.markdown("""
    Upload your own discharge data from **GRDC**, **USGS**, **BfG**, or any 
    CSV source and compute all five HSAE indices instantly.
    """)

    # ── Source selector ────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        source = st.selectbox("Data source format", [
            "GRDC Export (.txt)",
            "USGS Tab-delimited (.txt)",
            "Generic CSV (date + Q)",
            "Custom CSV",
        ])
    with col2:
        basin_name = st.text_input("Basin / Station name", placeholder="e.g. Rhine at Lobith")

    # ── File uploader ──────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload discharge file",
        type=["txt", "csv"],
        help="Max 200MB · Daily or monthly data"
    )

    if uploaded is None:
        st.info("👆 Upload a file to begin analysis")
        _show_format_guide()
        return

    # ── Parse ──────────────────────────────────────────────────────────────────
    df = None
    meta = {}
    try:
        raw = uploaded.read().decode("latin-1")
        if "GRDC" in source:
            df, meta = _parse_grdc(raw)
        elif "USGS" in source:
            df, meta = _parse_usgs(raw)
        else:
            df, meta = _parse_generic_csv(raw)
    except Exception as e:
        st.error(f"❌ Parse error: {e}")
        return

    if df is None or len(df) == 0:
        st.error("❌ No valid discharge data found in file")
        return

    # ── Show metadata ──────────────────────────────────────────────────────────
    st.success(f"✅ Loaded **{len(df):,}** records · {df['date'].min().date()} → {df['date'].max().date()}")

    if meta:
        with st.expander("📋 Station metadata"):
            for k, v in meta.items():
                st.write(f"**{k}:** {v}")

    # ── Data preview ───────────────────────────────────────────────────────────
    with st.expander("🔍 Data preview (first 10 rows)"):
        st.dataframe(df.head(10))

    # ── Quality check ──────────────────────────────────────────────────────────
    st.subheader("📊 Data Quality Check")
    col1, col2, col3, col4 = st.columns(4)
    missing = int(df['Q_m3s'].isna().sum())
    negative = int((df['Q_m3s'] < 0).sum())
    col1.metric("Total records", f"{len(df):,}")
    col2.metric("Missing values", f"{missing}")
    col3.metric("Negative values", f"{negative}")
    col4.metric("Period (years)", f"{(df['date'].max()-df['date'].min()).days/365:.1f}")

    # ── User inputs ────────────────────────────────────────────────────────────
    st.subheader("⚙️ Analysis Settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        upstream_factor = st.slider(
            "Upstream abstraction (%)",
            min_value=0, max_value=80, value=15,
            help="Estimated % of natural flow withheld upstream"
        )
    with col2:
        alpha = st.slider("α (ET correction)", 0.0, 1.0, ALPHA, 0.05)
    with col3:
        treaty = st.selectbox("Treaty framework", [
            "UN Watercourses Convention 1997",
            "Rhine Convention 1999",
            "Nile Basin Initiative",
            "Indus Waters Treaty",
            "Mekong Agreement 1995",
        ])

    if not st.button("🚀 Compute All Indices", type="primary"):
        return

    # ── Clean data ─────────────────────────────────────────────────────────────
    df = df.dropna(subset=['Q_m3s'])
    df = df[df['Q_m3s'] >= 0]
    Q_obs = df['Q_m3s'].values
    doy   = df['date'].dt.dayofyear.values

    # Natural flow estimate
    Q_nat = Q_obs / (1 - upstream_factor/100 + 1e-6)

    # ET proxy (seasonal)
    ET0 = 2.5 + 1.8 * np.sin(2*np.pi*(doy - 80)/365)
    P   = 60  + 20  * np.sin(2*np.pi*(doy-270)/365)

    # BCM conversion
    bcm = 86400 / 1e9
    I_nat = Q_nat  * bcm
    Q_out = Q_obs  * bcm

    # ── 1. ATDI ────────────────────────────────────────────────────────────────
    I_adj = I_nat * (1 - alpha * ET0 / (P + EPSILON))
    TDI   = np.clip((I_adj - Q_out) / (I_adj + EPSILON), 0, 1)
    ATDI  = float(TDI.mean() * 100)

    # ── 2. AHIFD ──────────────────────────────────────────────────────────────
    AHIFD_d = np.clip((Q_nat - Q_obs) / (Q_nat + 1e-3), 0, 1)
    AHIFD   = float(AHIFD_d.mean() * 100)

    # ── 3. AFSF ───────────────────────────────────────────────────────────────
    sigma_obs = pd.Series(Q_obs).rolling(30).std().fillna(0).values
    sigma_nat = pd.Series(Q_nat).rolling(30).std().fillna(0).values
    AFSF_d    = np.clip(1 - sigma_obs/(sigma_nat+1e-3), 0, 1)
    AFSF      = float(AFSF_d.mean() * 100)

    # ── 4. ASI ────────────────────────────────────────────────────────────────
    ASI = 0.40*(ATDI/100) + 0.35*(AHIFD/100) + 0.25*(AFSF/100)
    ASI_pct = ASI * 100

    # ── 5. ATCI ───────────────────────────────────────────────────────────────
    art3  = max(0, 1 - ATDI/100)
    art4  = max(0, 1 - AHIFD/100)
    art5s = 0.90 if ATDI < 30 else 0.65
    art6  = 0.85
    art7  = max(0, 1 - AFSF/100)
    ATCI  = float(np.mean([art3,art4,art5s,art6,art7]) * 100)

    # ── Display results ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏆 HSAE Index Results")

    def _badge(val, thresholds, labels, colors):
        for t, l, c in zip(thresholds, labels, colors):
            if val < t:
                return f":{c}[{l}]"
        return f":{colors[-1]}[{labels[-1]}]"

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("ATDI",  f"{ATDI:.1f}%",  help="Transparency Deficit Index")
    col2.metric("AHIFD", f"{AHIFD:.1f}%", help="Human-Induced Flow Deficit")
    col3.metric("AFSF",  f"{AFSF:.1f}%",  help="Forensic Signal Factor")
    col4.metric("ASI",   f"{ASI_pct:.1f}%",help="Sovereignty Index")
    col5.metric("ATCI",  f"{ATCI:.1f}%",  help="Treaty Compliance Index")

    # UNWC legal status
    st.markdown("### ⚖️ Legal Status — " + treaty)
    art5_days  = int((TDI*100 > 20).sum())
    art7_days  = int((TDI*100 > 40).sum())
    art9_days  = int((TDI*100 > 55).sum())
    art12_days = int((TDI*100 > 70).sum())
    n = len(TDI)

    def _pct(d): return f"{d:,} days ({d/n*100:.1f}%)"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Art. 5 (>20%)", _pct(art5_days),  delta="Equitable use")
    col2.metric("Art. 7 (>40%)", _pct(art7_days),  delta="No-harm rule")
    col3.metric("Art. 9 (>55%)", _pct(art9_days),  delta="Notification")
    col4.metric("Art. 12 (>70%)",_pct(art12_days), delta="Significant harm")

    # Time series chart
    st.markdown("### 📈 ATDI Time Series")
    chart_df = pd.DataFrame({
        "Date": df["date"].values,
        "ATDI (%)": TDI * 100,
        "Q obs (m³/s)": Q_obs,
        "Q natural (m³/s)": Q_nat,
    }).set_index("Date")
    st.line_chart(chart_df[["ATDI (%)"]])

    with st.expander("📊 Discharge comparison"):
        st.line_chart(chart_df[["Q obs (m³/s)", "Q natural (m³/s)"]])

    # ── Export ─────────────────────────────────────────────────────────────────
    st.markdown("### 💾 Export Results")
    result_df = pd.DataFrame({
        "Date":        df["date"].values,
        "Q_obs_m3s":   Q_obs.round(2),
        "Q_nat_m3s":   Q_nat.round(2),
        "TDI_pct":     (TDI*100).round(3),
        "AHIFD_pct":   (AHIFD_d*100).round(3),
        "AFSF_pct":    (AFSF_d*100).round(3),
        "Art5_flag":   (TDI*100 > 20).astype(int),
        "Art7_flag":   (TDI*100 > 40).astype(int),
        "Art9_flag":   (TDI*100 > 55).astype(int),
        "Art12_flag":  (TDI*100 > 70).astype(int),
    })

    summary = {
        "Basin": basin_name or "User upload",
        "ATDI_%": round(ATDI, 2),
        "AHIFD_%": round(AHIFD, 2),
        "AFSF_%": round(AFSF, 2),
        "ASI_%": round(ASI_pct, 2),
        "ATCI_%": round(ATCI, 2),
        "N_records": len(df),
        "Period": f"{df['date'].min().date()} to {df['date'].max().date()}",
        "Treaty": treaty,
    }

    col1, col2 = st.columns(2)
    with col1:
        csv = result_df.to_csv(index=False)
        st.download_button(
            "⬇️ Download daily results CSV",
            csv, f"hsae_{basin_name or 'results'}.csv",
            "text/csv", use_container_width=True
        )
    with col2:
        summary_csv = pd.DataFrame([summary]).to_csv(index=False)
        st.download_button(
            "⬇️ Download summary CSV",
            summary_csv, f"hsae_{basin_name or 'summary'}_summary.csv",
            "text/csv", use_container_width=True
        )


# ── Parsers ────────────────────────────────────────────────────────────────────

def _parse_grdc(raw: str):
    """Parse GRDC Export format."""
    meta = {}
    lines = raw.split('\n')

    for line in lines[:50]:
        for field in ['Station','River','Country','Latitude','Longitude',
                      'Catchment area','Altitude']:
            if line.startswith(f'{field}') and ':' in line:
                meta[field] = line.split(':',1)[1].strip()

    records = []
    for line in lines:
        line = line.strip()
        if re.match(r'\d{4}-\d{2}-\d{2}', line):
            parts = line.split(';')
            if len(parts) >= 3:
                try:
                    q = float(parts[2].strip())
                    if q > -999:
                        records.append({'date': pd.to_datetime(parts[0].strip()),
                                        'Q_m3s': q})
                except: pass

    df = pd.DataFrame(records) if records else pd.DataFrame(columns=['date','Q_m3s'])
    return df, meta


def _parse_usgs(raw: str):
    """Parse USGS tab-delimited format."""
    meta = {}
    lines = raw.split('\n')
    header_line = None
    records = []

    for i, line in enumerate(lines):
        if line.startswith('#'):
            if 'site_no' in line.lower() or 'station' in line.lower():
                meta['Station'] = line.strip('#').strip()
            continue
        if header_line is None and 'agency_cd' in line.lower():
            header_line = line.strip().split('\t')
            continue
        if header_line and not line.startswith('5s'):
            parts = line.strip().split('\t')
            if len(parts) >= len(header_line):
                try:
                    date_idx = next(i for i,h in enumerate(header_line) if 'datetime' in h.lower() or 'date' in h.lower())
                    q_idx    = next(i for i,h in enumerate(header_line) if '_00060' in h or ('00060' in h and not h.endswith('_cd')))
                    records.append({
                        'date':   pd.to_datetime(parts[date_idx]),
                        'Q_m3s':  float(parts[q_idx]) * 0.0283168  # cfs→m³/s
                    })
                except: pass

    df = pd.DataFrame(records) if records else pd.DataFrame(columns=['date','Q_m3s'])
    return df, meta


def _parse_generic_csv(raw: str):
    """Parse any CSV with date + discharge columns."""
    meta = {}
    try:
        df = pd.read_csv(io.StringIO(raw), sep=None, engine='python',
                         comment='#', on_bad_lines='skip')
        df.columns = [c.lower().strip() for c in df.columns]

        # Find date column
        date_col = next((c for c in df.columns if any(k in c for k in
                         ['date','time','day','datum','fecha'])), df.columns[0])
        # Find discharge column
        q_col = next((c for c in df.columns if any(k in c for k in
                      ['q','flow','discharge','abfluss','caudal','streamflow'])),
                     df.columns[1])

        df = df.rename(columns={date_col:'date', q_col:'Q_m3s'})
        df['date']  = pd.to_datetime(df['date'], errors='coerce')
        df['Q_m3s'] = pd.to_numeric(df['Q_m3s'], errors='coerce')
        df = df.dropna(subset=['date','Q_m3s'])
        df = df.sort_values('date').reset_index(drop=True)
        meta['Detected date column']      = date_col
        meta['Detected discharge column'] = q_col
        return df[['date','Q_m3s']], meta
    except Exception as e:
        return pd.DataFrame(columns=['date','Q_m3s']), {'error': str(e)}


def _show_format_guide():
    with st.expander("📖 Supported file formats"):
        st.markdown("""
**GRDC Export (.txt)**
```
Station : El Deim
River   : Blue Nile
1978-01-01; ; 150.0; ...
```

**USGS Tab-delimited (.txt)**
```
agency_cd  site_no  datetime  00060_Mean
USGS       09380000  2020-01-01  1234
```

**Generic CSV**
```
date,Q_m3s
2020-01-01,1234.5
2020-01-02,1290.3
```
Any column names containing 'date' and 'Q' or 'flow' will be detected automatically.
        """)
