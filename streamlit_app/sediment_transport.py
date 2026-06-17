"""
sediment_transport.py — HSAE v10.0 Sediment Transport Module
=============================================================
Sediment load estimation, trap efficiency, and downstream impact
assessment for transboundary reservoirs.

Key methods:
  1. MUSLE (Modified Universal Soil Loss Equation) — annual sediment yield
  2. Trap efficiency — Brune (1953) curve + Churchill (1948)
  3. Reservoir sedimentation life — Batuca & Jordaan (2000)
  4. Downstream channel degradation index (DCDI)
  5. GERD-specific sediment balance (Blue Nile observed data)

References:
  - Williams (1975) MUSLE: USDA ARS-S-40
  - Brune (1953) ASCE Trans. 118:1587-1633
  - Churchill (1948) TN 2168, U.S. Corps of Engineers
  - Batuca & Jordaan (2000) ISBN:90-5809-052-3

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# ══════════════════════════════════════════════════════════════════════════════
# Data containers
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class SedimentResult:
    """Complete sediment transport assessment for one reservoir."""
    basin_id:          str
    annual_yield_Mtyr: float     # Mt/yr from catchment
    trap_efficiency:   float     # fraction (0-1) trapped in reservoir
    sediment_in_Mt:    float     # Mt/yr entering reservoir
    sediment_trapped:  float     # Mt/yr trapped
    sediment_passing:  float     # Mt/yr passing downstream
    storage_loss_pct_yr: float   # % of storage lost per year
    reservoir_life_yr: float     # estimated full-trap life (years)
    dcdi:              float     # downstream channel degradation index (0-1)
    art20_flag:        bool      # UN Art.20 ecosystem violation flag
    art7_flag:         bool      # UN Art.7 no-harm violation flag
    notes:             List[str]

    def to_dict(self) -> Dict:
        return {
            "basin_id":           self.basin_id,
            "annual_yield_Mt_yr": round(self.annual_yield_Mtyr, 2),
            "trap_efficiency_pct":round(self.trap_efficiency*100, 1),
            "sediment_in_Mt_yr":  round(self.sediment_in_Mt, 2),
            "sediment_trapped_Mt":round(self.sediment_trapped, 2),
            "sediment_passing_Mt":round(self.sediment_passing, 2),
            "storage_loss_pct_yr":round(self.storage_loss_pct_yr, 3),
            "reservoir_life_yr":  round(self.reservoir_life_yr, 0),
            "DCDI":               round(self.dcdi, 3),
            "art20_flag":         self.art20_flag,
            "art7_flag":          self.art7_flag,
            "notes":              self.notes,
        }


# ══════════════════════════════════════════════════════════════════════════════
# Observed sediment loads for key basins (literature-derived)
# ══════════════════════════════════════════════════════════════════════════════
OBSERVED_SEDIMENT: Dict[str, Dict] = {
    "GERD_ETH": {
        "annual_load_Mt_yr": 140.0,   # Betrie et al. (2011) doi:10.1002/hyp.8060
        "source": "Betrie et al. (2011) Hydrological Processes",
        "doi":    "10.1002/hyp.8060",
        "notes":  "Blue Nile at Sudan border; highly variable 50-300 Mt/yr",
    },
    "ROSEIRES_SDN": {
        "annual_load_Mt_yr": 110.0,   # downstream of GERD, post-trap
        "source": "GRDC + Sudan MoWR",
        "doi":    "10.1016/j.jhydrol.2015.03.061",
        "notes":  "Load reduced after GERD trapping",
    },
    "ASWAN_EGY": {
        "annual_load_Mt_yr": 2.0,     # post-High Aswan Dam; very low
        "source": "Milliman & Farnsworth (2011) ISBN:9780521879873",
        "doi":    "10.1017/CBO9780511781247",
        "notes":  "High Aswan traps >98% of Nile sediment",
    },
    "YANGTZE_3GORGES_CHN": {
        "annual_load_Mt_yr": 170.0,
        "source": "Yang et al. (2015) doi:10.1002/2014GL062012",
        "doi":    "10.1002/2014GL062012",
        "notes":  "Reduced from 500 Mt/yr pre-TGD to ~170 post-TGD",
    },
    "TARBELA_PAK": {
        "annual_load_Mt_yr": 200.0,
        "source": "Walling (2008) doi:10.1007/978-1-4020-5371-2_7",
        "doi":    "10.1007/978-1-4020-5371-2_7",
        "notes":  "Upper Indus; severe sedimentation reducing storage",
    },
    "KARIBA_ZMB": {
        "annual_load_Mt_yr": 15.0,
        "source": "Halcrow (2002) Kariba Dam Sedimentation Study",
        "doi":    None,
        "notes":  "Zambezi at Kariba; moderate sediment load",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. Annual sediment yield — MUSLE
# ══════════════════════════════════════════════════════════════════════════════
def musle_sediment_yield(
    peak_runoff_m3s: float,
    runoff_volume_mm: float,
    area_km2: float,
    k_factor: float = 0.30,    # USLE erodibility (t·ha·h / ha·MJ·mm)
    ls_factor: float = 2.0,    # slope-length factor
    c_factor: float = 0.25,    # cover management factor
    p_factor: float = 1.0,     # support practice factor
) -> float:
    """
    Modified Universal Soil Loss Equation (Williams 1975).
    Sed (t) = 11.8 × (Q · qp)^0.56 × K × LS × C × P

    Parameters
    ----------
    peak_runoff_m3s  : peak surface runoff rate (m³/s)
    runoff_volume_mm : runoff volume per event (mm over area_km2)
    area_km2         : watershed area
    k_factor         : soil erodibility factor
    ls_factor        : slope-length factor
    c_factor         : cover management factor
    p_factor         : support practice factor

    Returns
    -------
    Sediment yield in tonnes per event
    """
    q_vol = runoff_volume_mm * area_km2 * 1000  # m³ per event
    qp    = peak_runoff_m3s
    sed   = 11.8 * (q_vol * qp)**0.56 * k_factor * ls_factor * c_factor * p_factor
    return max(0.0, sed)


def annual_sediment_yield_Mt(
    annual_runoff_mm: float,
    peak_q_m3s: float,
    area_km2: float,
    k_factor: float = 0.30,
    ls_factor: float = 2.0,
    c_factor: float = 0.25,
    n_events: int = 20,   # number of significant runoff events per year
) -> float:
    """Estimate annual sediment yield in Megatonnes."""
    event_runoff = annual_runoff_mm / n_events
    sed_per_event = musle_sediment_yield(
        peak_q_m3s, event_runoff, area_km2, k_factor, ls_factor, c_factor
    )
    annual_t = sed_per_event * n_events
    return annual_t / 1e6   # t → Mt


# ══════════════════════════════════════════════════════════════════════════════
# 2. Trap efficiency
# ══════════════════════════════════════════════════════════════════════════════
def brune_trap_efficiency(
    capacity_BCM: float,
    annual_inflow_BCM: float,
) -> float:
    """
    Brune (1953) trap efficiency curve.
    TE = 1 - 0.05 / (C/I + 0.05)

    where C/I is the capacity-inflow ratio.

    Reference: Brune (1953) ASCE Transactions 118:1587-1633

    Parameters
    ----------
    capacity_BCM      : reservoir storage capacity (BCM)
    annual_inflow_BCM : mean annual inflow (BCM/yr)

    Returns
    -------
    Trap efficiency fraction (0–1)
    """
    if annual_inflow_BCM <= 0:
        return 0.95   # default high TE for large reservoirs
    ci = capacity_BCM / annual_inflow_BCM
    # Brune median curve
    te = 1.0 - 0.05 / (ci + 0.05)
    return max(0.0, min(1.0, te))


def churchill_trap_efficiency(
    capacity_m3: float,
    mean_daily_flow_m3s: float,
) -> float:
    """
    Churchill (1948) sedimentation index method.
    SI = V / (T × Q)  where V=volume, T=period, Q=mean flow

    Reference: Churchill (1948) TN 2168, U.S. Army Corps of Engineers
    """
    T = 86400  # 1 day in seconds
    if mean_daily_flow_m3s <= 0:
        return 0.90
    si = capacity_m3 / (T * mean_daily_flow_m3s)
    # Empirical Churchill curve (simplified)
    te = 1.0 - math.exp(-0.41 * si**0.41)
    return max(0.0, min(1.0, te))


# ══════════════════════════════════════════════════════════════════════════════
# 3. Reservoir life estimation
# ══════════════════════════════════════════════════════════════════════════════
def reservoir_life_estimate(
    capacity_BCM: float,
    annual_yield_Mt: float,
    trap_efficiency: float,
    bulk_density_t_m3: float = 1.2,
    acceptable_loss_pct: float = 50.0,
) -> Tuple[float, float]:
    """
    Estimate reservoir sedimentation life.

    Reference: Batuca & Jordaan (2000) Silting and Desilting of Reservoirs

    Returns
    -------
    (storage_loss_pct_yr, years_to_loss) tuple
    """
    if capacity_BCM <= 0 or annual_yield_Mt <= 0:
        return 0.0, float("inf")

    # Sediment volume trapped per year (m³/yr)
    trapped_t_yr = annual_yield_Mt * 1e6 * trap_efficiency
    trapped_m3_yr = trapped_t_yr / bulk_density_t_m3

    # Capacity in m³
    capacity_m3 = capacity_BCM * 1e9

    # Annual storage loss (%)
    loss_pct_yr = (trapped_m3_yr / capacity_m3) * 100

    # Years to reach acceptable_loss_pct
    if loss_pct_yr > 0:
        years = acceptable_loss_pct / loss_pct_yr
    else:
        years = float("inf")

    return round(loss_pct_yr, 4), round(years, 0)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Downstream channel degradation index (DCDI)
# ══════════════════════════════════════════════════════════════════════════════
def downstream_degradation_index(
    sediment_pre_dam_Mt: float,
    sediment_post_dam_Mt: float,
    years_operation: float,
    river_length_km: float,
) -> float:
    """
    Downstream Channel Degradation Index (DCDI) — HSAE indicator.
    Quantifies relative change in sediment supply to downstream channel.

    DCDI = 1 - (post/pre) × exp(-years/T_adjust)
    where T_adjust = river_length_km / 10 (years for channel to adjust)

    DCDI > 0.5 → significant degradation (UN Art.20 concern)
    DCDI > 0.7 → severe degradation (Art.7 no-harm violation likely)
    """
    if sediment_pre_dam_Mt <= 0:
        return 0.0
    ratio        = sediment_post_dam_Mt / sediment_pre_dam_Mt
    t_adjust     = max(5.0, river_length_km / 10.0)
    decay        = math.exp(-years_operation / t_adjust)
    dcdi         = (1.0 - ratio) * (1.0 - decay * 0.3)
    return max(0.0, min(1.0, round(dcdi, 3)))


# ══════════════════════════════════════════════════════════════════════════════
# 5. Full basin sediment assessment
# ══════════════════════════════════════════════════════════════════════════════
def assess_sediment(
    basin: Dict,
    years_operation: float = 10.0,
    downstream_length_km: float = 500.0,
) -> SedimentResult:
    """
    Complete sediment assessment for a basin.
    Uses observed data where available, MUSLE estimates otherwise.
    """
    basin_id = basin.get("id", basin.get("_v9_id", "UNKNOWN"))
    notes    = []

    # Get observed or estimated sediment load
    if basin_id in OBSERVED_SEDIMENT:
        obs  = OBSERVED_SEDIMENT[basin_id]
        load = obs["annual_load_Mt_yr"]
        notes.append(f"Observed load from: {obs['source']}")
    else:
        # Estimate from basin parameters
        area   = basin.get("eff_cat_km2", 50000)
        runoff = basin.get("runoff_c", 0.3) * 800   # ~800mm mean annual P
        peak_q = (basin.get("cap", 10) * 1e9 / (30*86400))**0.5  # rough estimate
        load   = annual_sediment_yield_Mt(runoff, peak_q, area)
        notes.append(f"MUSLE estimate (Williams 1975); area={area:,.0f} km²")

    cap    = basin.get("cap", 10.0)   # BCM
    inflow = cap * 0.8                # rough C/I ~ 0.8

    # Trap efficiency
    te_brune   = brune_trap_efficiency(cap, inflow)
    te         = te_brune
    notes.append(f"Brune (1953) trap efficiency: {te*100:.1f}%")

    # Trapped and passing sediment
    trapped  = load * te
    passing  = load * (1 - te)

    # Reservoir life
    loss_pct_yr, life_yr = reservoir_life_estimate(cap, load, te)

    # Downstream degradation
    # Pre-dam load from natural estimate, post = what passes
    pre_dam  = OBSERVED_SEDIMENT.get(basin_id, {}).get("annual_load_Mt_yr", load)
    dcdi     = downstream_degradation_index(pre_dam, passing, years_operation,
                                            downstream_length_km)

    # Legal flags
    art20 = dcdi > 0.5
    art7  = dcdi > 0.7 or loss_pct_yr > 1.0

    if art20:
        notes.append("⚠️ DCDI > 0.5 → UN Art.20 (ecosystem protection) concern")
    if art7:
        notes.append("🔴 DCDI > 0.7 or storage loss > 1%/yr → Art.7 no-harm risk")
    if life_yr < 100:
        notes.append(f"⚠️ Reservoir operational life < 100 years ({life_yr:.0f} yr)")

    return SedimentResult(
        basin_id=basin_id,
        annual_yield_Mtyr=round(load, 2),
        trap_efficiency=round(te, 3),
        sediment_in_Mt=round(load, 2),
        sediment_trapped=round(trapped, 2),
        sediment_passing=round(passing, 2),
        storage_loss_pct_yr=round(loss_pct_yr, 4),
        reservoir_life_yr=life_yr,
        dcdi=round(dcdi, 3),
        art20_flag=art20,
        art7_flag=art7,
        notes=notes,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 6. Streamlit render helper
# ══════════════════════════════════════════════════════════════════════════════
def render_sediment_page(basin: Dict) -> None:
    """Render sediment transport assessment as a Streamlit page."""
    try:
        import streamlit as st
        import plotly.graph_objects as go
    except ImportError:
        return

    st.header("🪨 Sediment Transport & Reservoir Sedimentation")
    st.caption(
        "MUSLE (Williams 1975) · Brune (1953) trap efficiency · "
        "DCDI downstream degradation · UN Art.7/20 legal flags"
    )

    basin_id = basin.get("id", basin.get("_v9_id", "unknown"))

    # Show observed data if available
    if basin_id in OBSERVED_SEDIMENT:
        obs = OBSERVED_SEDIMENT[basin_id]
        st.success(
            f"✅ **Observed sediment data available**  \n"
            f"Load: {obs['annual_load_Mt_yr']} Mt/yr  \n"
            f"Source: *{obs['source']}*  \n"
            f"DOI: `{obs.get('doi','—')}`"
        )

    # Controls
    c1, c2, c3 = st.columns(3)
    years_op  = c1.slider("Years of operation", 1, 100, 10)
    ds_length = c2.slider("Downstream length (km)", 50, 3000, 500)

    if st.button("▶ Run Sediment Assessment", type="primary"):
        with st.spinner("Computing sediment transport..."):
            result = assess_sediment(basin,
                                     years_operation=years_op,
                                     downstream_length_km=ds_length)

        # Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Annual Load",     f"{result.annual_yield_Mtyr:.1f} Mt/yr")
        m2.metric("Trap Efficiency", f"{result.trap_efficiency*100:.1f}%")
        m3.metric("Trapped",         f"{result.sediment_trapped:.1f} Mt/yr")
        m4.metric("Reservoir Life",  f"{result.reservoir_life_yr:.0f} yr")
        m5.metric("DCDI",            f"{result.dcdi:.3f}")

        # Legal flags
        st.subheader("⚖️ Legal Implications")
        col_a, col_b = st.columns(2)
        if result.art7_flag:
            col_a.error("🔴 UN Art.7 (No Significant Harm) — violation likely")
        else:
            col_a.success("✅ UN Art.7 — within acceptable bounds")
        if result.art20_flag:
            col_b.warning("⚠️ UN Art.20 (Ecosystem) — monitoring required")
        else:
            col_b.success("✅ UN Art.20 — ecosystem impact acceptable")

        # Sedimentation curve
        years = list(range(0, int(result.reservoir_life_yr * 1.2) + 1, 5))
        capacity_remaining = [
            max(0, 100 - result.storage_loss_pct_yr * y) for y in years
        ]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=capacity_remaining,
            fill="tozeroy", line=dict(color="#f97316"),
            name="Storage remaining (%)"
        ))
        fig.add_hline(y=50, line_dash="dot", line_color="#f85149",
                      annotation_text="50% threshold")
        fig.update_layout(
            template="plotly_dark", height=350,
            title="Reservoir Storage Loss Over Time",
            xaxis_title="Years of operation",
            yaxis_title="Storage remaining (%)",
            yaxis_range=[0, 105]
        )
        st.plotly_chart(fig, width='stretch')

        # Notes
        st.subheader("📋 Assessment Notes")
        for note in result.notes:
            st.markdown(f"- {note}")

        # Export
        st.download_button(
            "⬇️ Download Sediment Report (JSON)",
            data=__import__("json").dumps(result.to_dict(), indent=2),
            file_name=f"sediment_{basin_id}.json",
            mime="application/json"
        )
    else:
        st.info("Configure parameters above and click **Run Sediment Assessment**.")

    with st.expander("📚 Key References"):
        st.markdown("""
- **Williams (1975)** MUSLE: USDA ARS-S-40 (sediment yield estimation)
- **Brune (1953)** Trap efficiency: *ASCE Transactions* 118:1587–1633
- **Batuca & Jordaan (2000)** *Silting and Desilting of Reservoirs* ISBN:90-5809-052-3
- **Betrie et al. (2011)** Blue Nile sediment: *Hydrological Processes* doi:10.1002/hyp.8060
- **UN 1997** Art.7 (no significant harm) · Art.20 (ecosystem protection)
""")
