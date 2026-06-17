"""
hydrosovereign.viz — Visualization Module
==========================================
Basin risk maps, discharge plots, ATDI dashboards.

As recommended by ChatGPT review:
  'You are missing: Maps, Plots, GIS outputs.
   Add module visualization/maps.py, visualization/plots.py'

Requires: pip install hydrosovereign[viz]

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from .plots import (
    plot_basin_risk,
    plot_discharge,
    plot_atdi_hifd,
    plot_negotiation_radar,
    plot_conflict_heatmap,
)
from .maps import (
    map_global_basins,
    map_risk_choropleth,
)

__all__ = [
    "plot_basin_risk",
    "plot_discharge",
    "plot_atdi_hifd",
    "plot_negotiation_radar",
    "plot_conflict_heatmap",
    "map_global_basins",
    "map_risk_choropleth",
]
