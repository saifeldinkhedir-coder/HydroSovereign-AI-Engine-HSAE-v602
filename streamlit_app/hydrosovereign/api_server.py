"""
api_server.py — HSAE v6.5.0 FastAPI REST Service
==================================================
Production REST API for hydrosovereign.

Install: pip install hydrosovereign[api]
Run:     uvicorn hydrosovereign.api_server:app --host 0.0.0.0 --port 8000
Docs:    http://localhost:8000/docs

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False


import logging
from typing import Optional, List, Dict
from datetime import date

logger = logging.getLogger(__name__)

if not _FASTAPI_AVAILABLE:
    raise ImportError(
        "FastAPI required: pip install hydrosovereign[api]\n"
        "  pip install fastapi uvicorn"
    )


# ── Pydantic models ───────────────────────────────────────────────────────────

class BasinRequest(BaseModel):
    name: Optional[str] = Field(None, example="Blue Nile (GERD)")
    runoff_c: Optional[float] = Field(None, ge=0.01, le=1.0, example=0.38)
    cap_bcm: Optional[float]  = Field(None, ge=0.0,  example=74.0)
    n_countries: Optional[int]= Field(None, ge=1,    example=3)
    dispute_level: Optional[int]=Field(None,ge=0,le=4,example=4)
    include_ai: bool    = True
    include_legal: bool = True

class WQIRequest(BaseModel):
    ph:        Optional[float] = Field(None, ge=0.0, le=14.0, example=7.2)
    do:        Optional[float] = Field(None, ge=0.0, le=20.0, example=8.5)
    bod:       Optional[float] = Field(None, ge=0.0, example=1.2)
    turbidity: Optional[float] = Field(None, ge=0.0, example=2.0)
    nitrates:  Optional[float] = Field(None, ge=0.0, example=3.0)
    tds:       Optional[float] = Field(None, ge=0.0, example=120.0)
    ec:        Optional[float] = Field(None, ge=0.0, example=250.0)
    atdi: Optional[float] = None
    hifd: Optional[float] = None

class ForecastRequest(BaseModel):
    basin_name: str    = Field(..., example="Blue Nile (GERD)")
    horizon_days: int  = Field(7, ge=1, le=16)
    years_history: int = Field(3, ge=1, le=10)

class NegotiationRequest(BaseModel):
    atdi: float          = Field(..., ge=5,  le=95, example=53.5)
    hifd: float          = Field(..., ge=5,  le=80, example=35.7)
    n_countries: int     = Field(..., ge=1,  le=20, example=3)
    dispute_level: int   = Field(..., ge=0,  le=4,  example=4)
    has_treaty: bool     = False
    gdp_gap: float       = Field(0.0, ge=0, le=1)
    shared_history: float= Field(0.5, ge=0, le=1)


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "HydroSovereign AI Engine API",
    description = (
        "REST API for hydrosovereign v6.5.0 — "
        "Transboundary Water Analysis & Governance\n\n"
        "Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991\n"
        "DOI: 10.5281/zenodo.19180160"
    ),
    version     = "6.5.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    """Package information and available endpoints."""
    return {
        "package":     "hydrosovereign",
        "version":     "6.5.0",
        "author":      "Seifeldin M.G. Alkhedir",
        "orcid":       "0000-0003-0821-2991",
        "doi":         "10.5281/zenodo.19180160",
        "endpoints": {
            "/analyze":      "Full basin analysis",
            "/analyze/all":  "All 26 basins ranked",
            "/basins":       "List registered basins",
            "/indices":      "Compute ATDI/HIFD/CI/WQI",
            "/wqi":          "Water Quality Index (WHO 2017)",
            "/negotiate":    "Negotiation AI prediction",
            "/forecast":     "Discharge forecast",
            "/legal":        "UNWC 1997 legal assessment",
            "/alerts":       "Real-time alert levels",
            "/docs":         "Swagger UI",
        }
    }


@app.post("/analyze", tags=["Analysis"])
def analyze_basin_endpoint(req: BasinRequest):
    """
    Full basin analysis — indices + AI + legal + alerts.

    Provide either `name` (from registry) or all manual parameters.
    """
    from .api import analyze_basin
    try:
        result = analyze_basin(
            name           = req.name,
            runoff_c       = req.runoff_c,
            cap_bcm        = req.cap_bcm,
            n_countries    = req.n_countries,
            dispute_level  = req.dispute_level,
            include_negotiation = req.include_ai,
            include_legal       = req.include_legal,
        )
        return result
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/all", tags=["Analysis"])
def analyze_all_endpoint(include_ai: bool = Query(False)):
    """Analyze all 26 registered basins, sorted by conflict index."""
    from .api import analyze_all_basins
    return analyze_all_basins(include_ai=include_ai)


@app.get("/basins", tags=["Data"])
def list_basins_endpoint(continent: Optional[str] = None, dispute_min: Optional[int] = None):
    """List all 26 registered transboundary basins."""
    from .basins import BasinRegistry
    reg = BasinRegistry()
    if continent:
        return reg.filter_by_continent(continent)
    if dispute_min is not None:
        return reg.filter_by_dispute(min_level=dispute_min)
    return reg.all()


@app.get("/basins/{name}", tags=["Data"])
def get_basin_endpoint(name: str):
    """Get a specific basin by name."""
    from .basins import BasinRegistry
    try:
        return BasinRegistry().get(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Basin not found: {name}")


@app.post("/indices", tags=["Indices"])
def compute_indices_endpoint(
    runoff_c:     float = Query(..., ge=0.01, le=1.0),
    cap_bcm:      float = Query(..., ge=0.0),
    n_countries:  int   = Query(..., ge=1, le=20),
    dispute_level:int   = Query(..., ge=0, le=4),
):
    """Compute ATDI, HIFD, Conflict Index, and Negotiation P for given parameters."""
    from .indices_legacy import compute_all_indices
    try:
        return compute_all_indices(runoff_c, cap_bcm, n_countries, dispute_level)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/wqi", tags=["Indices"])
def compute_wqi_endpoint(req: WQIRequest):
    """
    Water Quality Index — WHO 2017 physicochemical or ATDI/HIFD proxy.

    Supply physicochemical measurements (ph, do, bod, turbidity...) for
    accurate WQI, or use atdi/hifd for proxy estimation.
    """
    from .indices_legacy import compute_wqi
    measurements = {k: v for k, v in {
        "ph": req.ph, "do": req.do, "bod": req.bod,
        "turbidity": req.turbidity, "nitrates": req.nitrates,
        "tds": req.tds, "ec": req.ec,
    }.items() if v is not None}
    try:
        wqi = compute_wqi(
            atdi=req.atdi, hifd=req.hifd,
            measurements=measurements or None,
        )
        return {
            "wqi": wqi,
            "mode": "physicochemical" if measurements else "proxy",
            "interpretation": (
                "Excellent" if wqi > 90 else
                "Good"      if wqi > 70 else
                "Medium"    if wqi > 50 else "Poor"
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/negotiate", tags=["AI"])
def negotiate_endpoint(req: NegotiationRequest):
    """Heuristic negotiation-pathway score (non-trained; see TreatyClassifier)."""
    from .ai.negotiation import NegotiationAI
    ai = NegotiationAI()
    return ai.predict(
        req.atdi, req.hifd, req.n_countries, req.dispute_level,
        req.has_treaty, req.gdp_gap, req.shared_history,
    )


@app.post("/forecast", tags=["AI"])
def forecast_endpoint(req: ForecastRequest):
    """
    7-day discharge forecast using PyTorch LSTM.
    Fetches live Open-Meteo data automatically.
    """
    from .data.fetchers import fetch_basin_forcing, _load_sample_data
    from .ai.forecast import LSTMForecast
    from .basins import BasinRegistry
    import numpy as np

    try:
        basin = BasinRegistry().get(req.basin_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Basin not found: {req.basin_name}")

    try:
        data = fetch_basin_forcing(req.basin_name, years=req.years_history)
    except Exception:
        data = _load_sample_data(req.basin_name)

    P  = np.array(data["P"][:365*req.years_history])
    T  = np.array(data["T"][:365*req.years_history])
    SM = np.array([v or 0.25 for v in (data.get("SM") or [0.25]*len(P))][:len(P)])

    features = ["P","T","SM"] if any(SM > 0) else ["P","T"]
    model = LSTMForecast(features=features, lookback=30, horizon=req.horizon_days,
                         hidden_size=32, n_layers=2)
    model.fit_multi({"P":P,"T":T,"SM":SM}, area_km2=float(basin.get("eff_cat_km2",100000)),
                    runoff_c=float(basin.get("runoff_c",0.3)), epochs=30)
    return model.predict_multi({"P":P[-30:],"T":T[-30:],"SM":SM[-30:]})


@app.get("/legal/{basin_name}", tags=["Legal"])
def legal_endpoint(basin_name: str):
    """UNWC 1997 legal assessment for a registered basin."""
    from .api import analyze_basin
    try:
        result = analyze_basin(basin_name, include_negotiation=False, include_legal=True)
        return result["legal"]
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/alerts/{basin_name}", tags=["Alerts"])
def alerts_endpoint(basin_name: str):
    """Real-time alert levels for a registered basin."""
    from .api import analyze_basin
    try:
        result = analyze_basin(basin_name, include_negotiation=False, include_legal=False)
        return {**result["alerts"], "indices": result["indices"]}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/health", tags=["Info"])
def health():
    """Health check endpoint."""
    return {"status": "healthy", "package": "hydrosovereign", "version": "6.5.0"}
