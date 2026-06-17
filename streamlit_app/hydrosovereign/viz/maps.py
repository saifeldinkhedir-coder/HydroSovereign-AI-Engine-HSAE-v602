"""
viz/maps.py — HSAE Interactive Maps
=====================================
Global basin maps and risk choropleth visualizations.

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
import numpy as np
from typing import Optional, List


def _check_plotly():
    try:
        import plotly.graph_objects as go
        return go
    except ImportError:
        raise ImportError(
            "Plotly required: pip install hydrosovereign[viz]"
        )


def map_global_basins(
    basins: list,
    color_by: str = "atdi",
    show: bool = True,
) -> "plotly.graph_objects.Figure":
    """
    Interactive global map of all transboundary basins.

    Parameters
    ----------
    basins : list of dict
        Each dict must have: name, lat, lon, atdi, hifd, dispute_level.
    color_by : str
        Color coding: 'atdi', 'hifd', 'ci', 'dispute_level'. Default='atdi'.
    show : bool
        Call fig.show(). Default = True.

    Returns
    -------
    plotly.graph_objects.Figure

    Examples
    --------
    >>> from hydrosovereign.basins import BASINS_26
    >>> from hydrosovereign.indices import compute_all_indices
    >>> enriched = []
    >>> for b in BASINS_26:
    ...     idx = compute_all_indices(b['runoff_c'], b['cap'],
    ...                               len(b['country']), b['dispute_level'])
    ...     enriched.append({**b, **idx})
    >>> fig = map_global_basins(enriched, color_by='atdi')
    """
    go = _check_plotly()

    lats    = [float(b.get("lat", 0)) for b in basins]
    lons    = [float(b.get("lon", 0)) for b in basins]
    names   = [b.get("name", "?") for b in basins]
    colors  = [float(b.get(color_by, b.get("atdi", 30))) for b in basins]
    disps   = [int(b.get("dispute_level", 0)) for b in basins]
    sizes   = [10 + d * 4 for d in disps]

    # Hover text
    hovers = []
    for b in basins:
        hovers.append(
            f"<b>{b.get('name','')}</b><br>"
            f"ATDI: {b.get('atdi','-'):.1f}%<br>"
            f"HIFD: {b.get('hifd','-'):.1f}%<br>"
            f"Dispute: {['LOW','LOW','MEDIUM','HIGH','CRITICAL'][min(int(b.get('dispute_level',0)),4)]}<br>"
            f"Countries: {len(b.get('country',[])) if isinstance(b.get('country'),list) else b.get('n_countries',2)}<br>"
            f"Treaty: {b.get('treaty','—')}"
        )

    colorscale = {
        "atdi":         [[0,"#3fb950"],[0.4,"#e3b341"],[0.6,"#f0883e"],[1,"#f85149"]],
        "hifd":         [[0,"#3fb950"],[0.3,"#e3b341"],[0.6,"#f0883e"],[1,"#f85149"]],
        "ci":           [[0,"#3fb950"],[0.4,"#e3b341"],[0.6,"#f0883e"],[1,"#f85149"]],
        "dispute_level":[[0,"#3fb950"],[0.5,"#e3b341"],[0.75,"#f0883e"],[1,"#f85149"]],
    }.get(color_by, [[0,"#3fb950"],[1,"#f85149"]])

    label_map = {"atdi":"ATDI (%)","hifd":"HIFD (%)","ci":"Conflict Index","dispute_level":"Dispute Level"}

    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons,
        text=names,
        hovertext=hovers,
        hoverinfo="text",
        mode="markers+text",
        textposition="top center",
        textfont=dict(size=8, color="white"),
        marker=dict(
            size=sizes,
            color=colors,
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title=label_map.get(color_by, color_by),
                thickness=12,
            ),
            opacity=0.90,
            line=dict(color="white", width=1),
        ),
    ))

    fig.update_geos(
        showland=True, landcolor="#161b22",
        showocean=True, oceancolor="#0d1117",
        showcoastlines=True, coastlinecolor="#30363d",
        showframe=False,
        projection_type="natural earth",
    )

    fig.update_layout(
        title=dict(
            text=f"🌍 HSAE v6.01 — Global Basin Network (colored by {label_map.get(color_by,color_by)})",
            x=0.5, font=dict(size=15, color="#58a6ff"),
        ),
        paper_bgcolor="#0d1117",
        font=dict(color="#e6edf3"),
        height=520,
        margin=dict(l=0, r=0, t=50, b=0),
    )

    if show:
        fig.show()
    return fig


def map_risk_choropleth(
    basins: list,
    metric: str = "ci",
    show: bool = True,
) -> "plotly.graph_objects.Figure":
    """
    Bubble map sized and colored by risk metric.

    Parameters
    ----------
    basins : list of dict
        Basin data with lat, lon, and metric values.
    metric : str
        Risk metric to display: 'ci', 'atdi', 'hifd', 'p_neg'.
    show : bool

    Returns
    -------
    plotly.graph_objects.Figure

    Examples
    --------
    >>> fig = map_risk_choropleth(enriched_basins, metric='ci')
    """
    go = _check_plotly()

    metric_labels = {
        "ci":    "Conflict Index",
        "atdi":  "ATDI (%)",
        "hifd":  "HIFD (%)",
        "p_neg": "P(Negotiation)",
    }

    lats   = [float(b.get("lat", 0)) for b in basins]
    lons   = [float(b.get("lon", 0)) for b in basins]
    names  = [b.get("name","?") for b in basins]
    values = [float(b.get(metric, 0.3)) for b in basins]

    # Scale size by value
    vmin, vmax = min(values), max(values)
    norm       = [(v - vmin) / (vmax - vmin + 1e-9) for v in values]
    sizes      = [8 + n * 24 for n in norm]

    risk_cats  = []
    for v in values:
        if metric in ("ci",):
            cat = "CRITICAL" if v>=0.6 else "HIGH" if v>=0.4 else "MEDIUM" if v>=0.25 else "LOW"
        elif metric == "atdi":
            cat = "CRITICAL" if v>=70 else "HIGH" if v>=55 else "MEDIUM" if v>=40 else "LOW"
        else:
            cat = "—"
        risk_cats.append(cat)

    colors_map = {"CRITICAL":"#f85149","HIGH":"#f0883e","MEDIUM":"#e3b341","LOW":"#3fb950","—":"#58a6ff"}
    colors     = [colors_map[c] for c in risk_cats]

    hovers = [
        f"<b>{n}</b><br>{metric_labels.get(metric,metric)}: {v:.3f}<br>Risk: {r}"
        for n, v, r in zip(names, values, risk_cats)
    ]

    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lat=lats, lon=lons,
        hovertext=hovers, hoverinfo="text",
        mode="markers",
        marker=dict(
            size=sizes, color=colors, opacity=0.85,
            line=dict(color="rgba(255,255,255,0.4)", width=1),
        ),
        text=names,
    ))

    # Legend annotations
    for cat, col in colors_map.items():
        if cat == "—": continue
        fig.add_trace(go.Scattergeo(
            lat=[None], lon=[None], mode="markers",
            marker=dict(size=10, color=col),
            name=cat, showlegend=True,
        ))

    fig.update_geos(
        showland=True, landcolor="#161b22",
        showocean=True, oceancolor="#0d1117",
        showcoastlines=True, coastlinecolor="#30363d",
        projection_type="natural earth",
    )

    fig.update_layout(
        title=dict(
            text=f"🌊 HSAE — {metric_labels.get(metric,metric)} Risk Map",
            x=0.5, font=dict(size=15, color="#58a6ff"),
        ),
        paper_bgcolor="#0d1117",
        font=dict(color="#e6edf3"),
        height=500,
        legend=dict(
            title="Risk Level",
            bgcolor="rgba(22,27,34,0.8)",
            bordercolor="#30363d",
        ),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    if show:
        fig.show()
    return fig
