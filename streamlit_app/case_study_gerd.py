"""
case_study_gerd.py - GERD Illustrative Scenario (HONEST REBUILD)
====================================================================
Addresses peer-review Problem #1 (hardcoded GERD verdict presented as a
finding). This page no longer displays fabricated metrics
(ATDI=0.72, NSE=0.78 SATISFACTORY) as results. Instead it:

  * clearly frames the whole page as an ILLUSTRATIVE SCENARIO using
    published, openly-citable scenario inputs (not measured results);
  * computes indices from the clean provenance engine where observation-
    grade inputs are supplied, and otherwise returns INSUFFICIENT_DATA;
  * never renders a legal "VIOLATED" verdict or a "SATISFACTORY"
    validation row from constants;
  * states explicitly that no public observed discharge exists for the
    Blue Nile at GERD, so no skill score is claimed.

Author: Seifeldin M.G. Alkhedir - ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations


# Published scenario context (openly citable, NOT measured HSAE outputs).
GERD_SCENARIO = {
    "dam": "Grand Ethiopian Renaissance Dam (GERD)",
    "river": "Blue Nile (Abay)",
    "riparians": "Ethiopia (upstream) - Sudan, Egypt (downstream)",
    "storage_capacity_bcm": 74.0,
    "catchment_km2": 311_548,
    "filling_phases": "2020-2024 (Phases I-V)",
    "observed_discharge": "No public observed daily discharge record "
                          "exists for the Blue Nile at GERD (El Diem) for "
                          "the filling period; see note below.",
}


def render_case_study_page(basin: dict) -> None:
    import streamlit as st

    st.markdown("## GERD Illustrative Scenario - Blue Nile")
    st.caption("Grand Ethiopian Renaissance Dam - pipeline demonstration")

    st.error(
        "**Illustrative scenario - not a measured result or a legal "
        "finding.** No public observed daily discharge record exists for "
        "the Blue Nile at GERD during the filling period. This page "
        "demonstrates the HSAE pipeline on **published scenario inputs**; "
        "it does not compute, and must not be read as, an adjudication of "
        "any state's compliance with the UN Watercourses Convention.",
        icon="⚠️")

    st.subheader("Scenario context")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"- **Dam:** {GERD_SCENARIO['dam']}\n"
            f"- **River:** {GERD_SCENARIO['river']}\n"
            f"- **Riparian states:** {GERD_SCENARIO['riparians']}")
    with c2:
        st.markdown(
            f"- **Design storage:** {GERD_SCENARIO['storage_capacity_bcm']} BCM\n"
            f"- **Catchment to GERD:** {GERD_SCENARIO['catchment_km2']:,} km²\n"
            f"- **Filling:** {GERD_SCENARIO['filling_phases']}")

    st.info(GERD_SCENARIO["observed_discharge"], icon="ℹ️")

    st.subheader("Provenance-bound indices")
    st.caption("Indices are computed only from observation-grade inputs you "
               "supply. Without them, the engine returns INSUFFICIENT_DATA "
               "rather than a fabricated number.")

    try:
        from hydrosovereign import (
            DataPoint, DataQuality, DataRegistry, hifd_for_basin,
            compute_hifd,
        )
        engine_ok = True
    except Exception:  # noqa: BLE001
        engine_ok = False

    if not engine_ok:
        st.warning("Clean engine unavailable (install hydrosovereign).")
        return

    st.markdown(
        "To compute a real HIFD for this basin, provide **independent** "
        "observation-grade naturalised flow (Q_nat) and observed downstream "
        "flow (Q_obs). With no such record available for GERD, the honest "
        "output is:")

    reg = DataRegistry()
    result = hifd_for_basin(reg, "GERD")
    st.metric("HIFD (GERD, from observed data)",
              result.value if result.ok else result.status)
    if not result.ok:
        st.caption(result.detail)

    st.subheader("Pipeline demonstration (hypothetical inputs)")
    st.caption("The values below are user-set scenario inputs to illustrate "
               "how the UNWC mapping responds - they are NOT measurements "
               "and carry NO legal weight.")

    demo_q_nat = st.slider("Hypothetical Q_nat (m³/s)", 800, 2500, 1580, 10)
    demo_q_obs = st.slider("Hypothetical Q_obs (m³/s)", 400, 2500, 1248, 10)

    def _dp(var, val):
        return DataPoint(
            value=float(val), variable=var, unit="m³/s",
            source="USER SCENARIO INPUT (hypothetical)",
            source_ref="scenario-only",
            date_start="2020-01-01", date_end="2024-12-31",
            quality=DataQuality.ESTIMATE)

    hyp = compute_hifd(_dp("Q_nat", demo_q_nat), _dp("Q_obs", demo_q_obs))
    if hyp.ok:
        st.metric("Scenario HIFD (hypothetical, illustrative only)",
                  f"{hyp.value}%")
        st.caption(
            "Illustrative only. A scenario HIFD is not evidence of harm and "
            "does not trigger any treaty article. Real attribution requires "
            "observed gauge data and legal-expert interpretation.")
    else:
        st.caption(hyp.detail)

    st.subheader("Model skill")
    st.warning(
        "**No skill score is claimed for this basin.** A valid NSE/KGE "
        "requires an observed benchmark that is independent of the model's "
        "forcing. None is available for the Blue Nile at GERD, so HSAE "
        "reports no validation metric here rather than a misleading one.",
        icon="🚫")

    st.divider()
    st.caption(
        "Legal interpretation of the UN Watercourses Convention is reserved "
        "to qualified international-water-law experts. HSAE provides "
        "hydrological indicators with full provenance; it does not issue "
        "legal verdicts.")
