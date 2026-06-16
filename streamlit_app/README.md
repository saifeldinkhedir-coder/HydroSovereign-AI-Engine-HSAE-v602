# HSAE Streamlit Platform (v6.0.14) — v602

The full HydroSovereign AI Engine web platform (30 pages, GEE/satellite
integration) on the provenance-bound engine.

## Deploy on Streamlit Cloud (same as v601)

1. New app → repository `saifeldinkhedir-coder/HydroSovereign-AI-Engine-HSAE-v602`
2. **Main file path:** `streamlit_app/app.py`
3. Branch: `main`
4. Deploy. Dependencies install from `streamlit_app/requirements.txt`;
   Python pinned by `streamlit_app/runtime.txt` (3.12).

The clean engine (`hydrosovereign_hsae/`, including the trained TFDD
model) is bundled locally **and** listed in requirements, so the app
runs whether or not the PyPI install succeeds.

## Run locally
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

## Scientific-integrity fixes (peer review)
- Global banner: modelled/synthetic series labelled scenario/illustrative.
- Negotiation AI uses the genuinely-trained TFDD classifier (objection #4).
- Validation requires a benchmark independent of model forcing (objection #5).
- Engine computes TDI/ATDI from inflow/outflow series, not constants.

*Seifeldin M.G. Alkhedir · ORCID 0000-0003-0821-2991*
