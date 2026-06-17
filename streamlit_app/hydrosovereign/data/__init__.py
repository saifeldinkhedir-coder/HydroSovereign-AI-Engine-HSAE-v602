"""hydrosovereign.data — Datasets and Live Data Fetchers."""
from pathlib import Path
from .fetchers import (
    fetch_openmeteo,
    fetch_openmeteo_forecast,
    fetch_basin_forcing,
    fetch_gee_basin,
    fetch_sentinel2_wqi,
    check_connectivity,
)
DATA_DIR = Path(__file__).parent
__all__ = [
    "fetch_openmeteo",
    "fetch_openmeteo_forecast",
    "fetch_basin_forcing",
    "fetch_gee_basin",
    "fetch_sentinel2_wqi",
    "check_connectivity",
    "DATA_DIR",
]
