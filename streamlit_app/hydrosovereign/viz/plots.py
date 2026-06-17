"""
viz/plots.py — HSAE Visualization Plots
=========================================
Risk plots, discharge time series, ATDI/HIFD charts.

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
import numpy as np
from typing import Optional, List, Union


def _check_plotly():
    try:
        import plotly.graph_objects as go
        return go
    except ImportError:
        raise ImportError(
            "Plotly is required for visualization.\n"
            "Install with: pip install hydrosovereign[viz]"
        )


def plot_basin_risk(
    basin_name: str,
    atdi: float,
    hifd: float,
    ci: float,
    p_negotiation: float,
    wqi: float = 60.0,
    show: bool = True,
) -> "plotly.graph_objects.Figure":
    """
    Plot comprehensive basin risk dashboard.

    Creates a 4-panel figure: ATDI gauge, HIFD gauge,
    Conflict Index bar, Negotiation probability.

    Parameters
    ----------
    basin_name : str
        Basin display name.
    atdi : float
        ATDI percentage (5–95).
    hifd : float
        HIFD percentage (5–80).
    ci : float
        Conflict Index (0–1).
    p_negotiation : float
        Negotiation success probability (0.20–0.90).
    wqi : float
        Water Quality Index (0–100). Default = 60.
    show : bool
        Whether to call fig.show(). Default = True.

    Returns
    -------
    plotly.graph_objects.Figure

    Examples
    --------
    >>> fig = plot_basin_risk("Blue Nile (GERD)", 49.2, 33.4, 0.61, 0.37)
    """
    go = _check_plotly()
    from plotly.subplots import make_subplots

    # Color mapping
    def atdi_color(v):
        if v >= 70: return "#f85149"
        if v >= 55: return "#f0883e"
        if v >= 40: return "#e3b341"
        return "#3fb950"

    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type":"indicator"},{"type":"indicator"}],
               [{"type":"indicator"},{"type":"indicator"}]],
        subplot_titles=["ATDI — Transparency Deficit",
                        "HIFD — Flow Deficit",
                        "Conflict Index",
                        "P(Negotiation Success)"],
    )

    # ATDI gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=atdi,
        number={"suffix":"%","font":{"size":24}},
        delta={"reference":40,"valueformat":".1f"},
        gauge={
            "axis":{"range":[0,100],"tickwidth":1},
            "bar":{"color":atdi_color(atdi)},
            "steps":[
                {"range":[0,40],  "color":"rgba(63,185,80,0.2)"},
                {"range":[40,55], "color":"rgba(227,179,65,0.2)"},
                {"range":[55,70], "color":"rgba(240,136,62,0.2)"},
                {"range":[70,100],"color":"rgba(248,81,73,0.2)"},
            ],
            "threshold":{"line":{"color":"white","width":2},"value":40},
        },
    ), row=1, col=1)

    # HIFD gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=hifd,
        number={"suffix":"%","font":{"size":24}},
        gauge={
            "axis":{"range":[0,80]},
            "bar":{"color":atdi_color(hifd)},
            "steps":[
                {"range":[0,25], "color":"rgba(63,185,80,0.2)"},
                {"range":[25,50],"color":"rgba(240,136,62,0.2)"},
                {"range":[50,80],"color":"rgba(248,81,73,0.2)"},
            ],
            "threshold":{"line":{"color":"white","width":2},"value":25},
        },
    ), row=1, col=2)

    # Conflict Index
    ci_color = "#f85149" if ci>=0.6 else "#f0883e" if ci>=0.4 else "#e3b341" if ci>=0.25 else "#3fb950"
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=round(ci*100, 1),
        number={"suffix":"%","font":{"size":24}},
        gauge={
            "axis":{"range":[0,100]},
            "bar":{"color":ci_color},
        },
    ), row=2, col=1)

    # Negotiation probability
    neg_color = "#3fb950" if p_negotiation>=0.65 else "#e3b341" if p_negotiation>=0.45 else "#f85149"
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=round(p_negotiation*100, 1),
        number={"suffix":"%","font":{"size":24}},
        gauge={
            "axis":{"range":[0,100]},
            "bar":{"color":neg_color},
        },
    ), row=2, col=2)

    fig.update_layout(
        title={
            "text": f"🌊 {basin_name} — HSAE Risk Dashboard",
            "x": 0.5,
            "font": {"size": 18, "color": "#58a6ff"},
        },
        paper_bgcolor="#0d1117",
        font={"color":"#e6edf3","family":"Arial"},
        height=500,
    )

    if show:
        fig.show()
    return fig


def plot_discharge(
    dates,
    Q_sim: Union[np.ndarray, List],
    Q_obs: Optional[Union[np.ndarray, List]] = None,
    Q_forecast: Optional[Union[np.ndarray, List]] = None,
    basin_name: str = "Basin",
    nse: Optional[float] = None,
    kge: Optional[float] = None,
    show: bool = True,
) -> "plotly.graph_objects.Figure":
    """
    Plot discharge time series: simulated vs observed vs forecast.

    Parameters
    ----------
    dates : array-like
        Date array (datetime or strings).
    Q_sim : array-like
        Simulated discharge (m³/s).
    Q_obs : array-like, optional
        Observed discharge (m³/s).
    Q_forecast : array-like, optional
        Forecasted discharge (m³/s).
    basin_name : str
        Basin name for title.
    nse, kge : float, optional
        Model performance metrics for subtitle.
    show : bool
        Call fig.show(). Default = True.

    Returns
    -------
    plotly.graph_objects.Figure

    Examples
    --------
    >>> import pandas as pd
    >>> dates = pd.date_range("2025-01-01", periods=365)
    >>> fig = plot_discharge(dates, Q_sim, Q_obs, nse=0.63, kge=0.74)
    """
    go = _check_plotly()

    fig = go.Figure()

    # Simulated
    fig.add_trace(go.Scatter(
        x=dates, y=Q_sim, name="HBV-96 Simulated",
        line=dict(color="#3fb950", width=2),
        fill="tozeroy", fillcolor="rgba(63,185,80,0.08)",
    ))

    # Observed
    if Q_obs is not None:
        fig.add_trace(go.Scatter(
            x=dates, y=Q_obs, name="Observed (GRDC)",
            line=dict(color="#58a6ff", width=2, dash="dot"),
            mode="lines+markers", marker=dict(size=3),
        ))

    # Forecast
    if Q_forecast is not None:
        n_fc = len(Q_forecast)
        fig.add_trace(go.Scatter(
            x=list(range(n_fc)), y=Q_forecast,
            name="LSTM Forecast", line=dict(color="#f0883e", width=2),
        ))

    subtitle = ""
    if nse is not None:
        subtitle = f"NSE={nse:.3f} · KGE={kge:.3f}" if kge else f"NSE={nse:.3f}"

    fig.update_layout(
        title=dict(
            text=f"🌊 {basin_name} — Discharge<br><sup>{subtitle}</sup>",
            x=0.5, font=dict(size=16, color="#58a6ff")),
        xaxis_title="Date",
        yaxis_title="Discharge (m³/s)",
        template="plotly_dark",
        height=420,
        hovermode="x unified",
        legend=dict(orientation="h", y=1.02),
    )
    if show:
        fig.show()
    return fig


def plot_atdi_hifd(
    basins: list,
    show: bool = True,
) -> "plotly.graph_objects.Figure":
    """
    Scatter plot: ATDI vs HIFD for all basins.

    Parameters
    ----------
    basins : list of dict
        Each dict: name, atdi, hifd, dispute_level.
    show : bool

    Returns
    -------
    plotly.graph_objects.Figure

    Examples
    --------
    >>> from hydrosovereign.basins import BASINS_26
    >>> from hydrosovereign.indices import compute_atdi, compute_hifd
    >>> basins_with_indices = [
    ...     {**b,
    ...      "atdi": compute_atdi(b["runoff_c"], b["cap"], len(b["country"]), b["dispute_level"]),
    ...      "hifd": compute_hifd(b["runoff_c"], b["cap"], len(b["country"]), b["dispute_level"])}
    ...     for b in BASINS_26
    ... ]
    >>> fig = plot_atdi_hifd(basins_with_indices)
    """
    go = _check_plotly()

    names  = [b["name"] for b in basins]
    atdis  = [b.get("atdi", 30) for b in basins]
    hifds  = [b.get("hifd", 15) for b in basins]
    disps  = [int(b.get("dispute_level", 0)) for b in basins]

    colors = ["#f85149" if d>=4 else "#f0883e" if d>=3
              else "#e3b341" if d>=2 else "#3fb950" for d in disps]
    sizes  = [10 + d*4 for d in disps]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=atdis, y=hifds, mode="markers+text",
        text=[n.split("–")[0].strip() for n in names],
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(color=colors, size=sizes, opacity=0.85,
                    line=dict(color="white", width=1)),
        hovertemplate="<b>%{text}</b><br>ATDI=%{x:.1f}%<br>HIFD=%{y:.1f}%<extra></extra>",
    ))

    # Threshold lines
    fig.add_hline(y=25, line_dash="dot", line_color="#e3b341",
                  annotation_text="Art.20 (25%)", annotation_position="right")
    fig.add_vline(x=40, line_dash="dot", line_color="#f0883e",
                  annotation_text="Art.7 (40%)")
    fig.add_vline(x=55, line_dash="dash", line_color="#f85149",
                  annotation_text="Art.33 (55%)")

    fig.update_layout(
        title=dict(text="🌍 ATDI vs HIFD — 26 Transboundary Basins",
                   x=0.5, font=dict(size=16, color="#58a6ff")),
        xaxis_title="ATDI (%)", yaxis_title="HIFD (%)",
        template="plotly_dark", height=520,
        xaxis=dict(range=[0, 100]), yaxis=dict(range=[0, 85]),
    )
    if show:
        fig.show()
    return fig


def plot_negotiation_radar(
    basin_name: str,
    atdi: float,
    hifd: float,
    ci: float,
    p_success: float,
    wqi: float,
    has_treaty: bool = False,
    show: bool = True,
) -> "plotly.graph_objects.Figure":
    """Radar chart of basin risk dimensions."""
    go = _check_plotly()

    categories = ["ATDI Risk", "HIFD Risk", "Conflict",
                  "Neg. Difficulty", "Water Quality (inv)", "Treaty Gap"]
    values = [
        atdi / 95,
        hifd / 80,
        ci,
        1 - p_success,
        1 - wqi / 100,
        0.0 if has_treaty else 0.7,
    ]
    values_pct = [round(v * 100, 1) for v in values]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_pct + [values_pct[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(248,81,73,0.25)",
        line=dict(color="#f85149", width=2),
        name=basin_name,
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(range=[0, 100], ticksuffix="%")),
        title=dict(text=f"🌊 {basin_name} — Risk Radar",
                   x=0.5, font=dict(color="#58a6ff")),
        template="plotly_dark", height=450,
    )
    if show:
        fig.show()
    return fig


def plot_conflict_heatmap(
    basins: list,
    show: bool = True,
) -> "plotly.graph_objects.Figure":
    """Heatmap: conflict index across all basins by continent."""
    go = _check_plotly()

    continents = list(dict.fromkeys(b.get("continent","?") for b in basins))
    basin_names= [b["name"].split("–")[0].strip() for b in basins]
    ci_values  = [b.get("ci", 0.3) for b in basins]

    fig = go.Figure(go.Bar(
        x=ci_values,
        y=basin_names,
        orientation="h",
        marker=dict(
            color=ci_values,
            colorscale=[[0,"#3fb950"],[0.4,"#e3b341"],
                        [0.6,"#f0883e"],[1,"#f85149"]],
            cmin=0, cmax=1,
            showscale=True,
            colorbar=dict(title="CI"),
        ),
        hovertemplate="<b>%{y}</b><br>CI = %{x:.3f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="⚡ Conflict Index — All 26 Basins",
                   x=0.5, font=dict(color="#58a6ff")),
        xaxis_title="Conflict Index (0–1)",
        template="plotly_dark",
        height=700,
        margin=dict(l=200),
    )
    if show:
        fig.show()
    return fig
