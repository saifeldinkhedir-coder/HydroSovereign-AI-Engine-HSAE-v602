# HSAE Streamlit Platform (v6.0.14)

The full HydroSovereign AI Engine web platform — comprehensive 30-page
interface with live GEE/satellite integration, on the provenance-bound
engine.

## Scientific-integrity fixes (peer review)
- Global banner: modelled/synthetic series are labelled scenario/
  illustrative — not validated field measurements.
- **Negotiation AI page** now uses the genuinely-trained TFDD treaty
  classifier (`hydrosovereign_hsae.TreatyClassifier`) with an honest
  model card; it classifies a documented treaty property, not
  negotiation success/failure (objection #4).
- **Validation page** requires a benchmark independent of the model's
  forcing; shared-forcing benchmarks are flagged (objection #5).
- Engine (`hsae_tdi.py`) computes TDI/ATDI from inflow/outflow series,
  not heuristic constants.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

*Seifeldin M.G. Alkhedir · ORCID 0000-0003-0821-2991*
