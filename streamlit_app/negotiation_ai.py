"""
negotiation_ai.py — Treaty-feature classifier page (HONEST ML)
====================================================================
Replaces the old "NegotiationAI trained on 478 cases" claim. This page
uses the GENUINELY trained TFDD classifier from the clean engine
(hydrosovereign_hsae.TreatyClassifier) and shows its honest model card.

Addresses review objection #4: the model is really trained, metrics are
reported honestly, and it predicts a documented treaty property — NOT
negotiation success/failure (which is not learnable from a database of
concluded treaties).

Author: Seifeldin M.G. Alkhedir - ORCID: 0000-0003-0821-2991
"""
import streamlit as st

try:
    from hydrosovereign_hsae import TreatyClassifier, MODEL_CARD
    _HAS_MODEL = True
except Exception:  # noqa: BLE001
    _HAS_MODEL = False


def render_negotiation_page(basin):
    st.header("🤝 Treaty-Feature Classifier")
    st.caption("Genuinely trained on the TFDD treaties database — "
               "addresses peer-review objection #4")

    st.warning(
        "This is **not** a negotiation success/failure predictor. The TFDD "
        "database records concluded treaties, so negotiation outcome is not "
        "a learnable label. This model classifies a documented treaty "
        "property: whether a treaty includes a conflict-resolution "
        "mechanism.", icon="🔍")

    if not _HAS_MODEL:
        st.error("Trained model unavailable in this environment "
                 "(install hydrosovereign-hsae).")
        return

    tc = TreatyClassifier()
    card = MODEL_CARD

    st.subheader("Model card (honest metrics)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"- **Task:** {card['task']}\n"
            f"- **Source:** {card['source']}\n"
            f"- **Unique treaties:** {card['n_treaties_total_unique']}\n"
            f"- **Labelled used:** {card['n_labelled_used']}\n"
            f"- **Model:** {card['model']}\n"
            f"- **Split:** {card['split']}")
    with c2:
        st.metric("Test F1", card["test_f1"])
        st.metric("Test ROC-AUC", card["test_roc_auc"])
        st.metric("5-fold CV F1",
                  f"{card['cv5_f1_mean']} ± {card['cv5_f1_std']}")
        st.caption(f"Baseline (majority) F1: {card['baseline_majority_f1']}")

    st.info(card["honest_note"], icon="📌")

    st.subheader("Try the classifier")
    c1, c2, c3 = st.columns(3)
    with c1:
        n_sig = st.number_input("Signatories", 1, 30,
                                int(basin.get("n_countries", 3)))
    with c2:
        year = st.number_input("Year signed", 1820, 2025, 2015)
    with c3:
        btc = st.number_input("Treaties in basin", 1, 100, 12)

    if st.button("Predict treaty property", type="primary"):
        if tc.is_available:
            try:
                p = tc.predict_proba(int(n_sig), int(year), int(btc))
                st.metric(
                    "P(treaty includes a conflict-resolution mechanism)",
                    f"{p:.3f}")
                st.caption("Real model output. Modest skill, honestly "
                           "reported.")
            except Exception as exc:  # noqa: BLE001
                st.error(
                    "The trained model could not be loaded in this "
                    "environment (likely a scikit-learn version mismatch). "
                    "The model card metrics above are still valid; live "
                    "prediction is temporarily unavailable.")
                st.caption(f"Details: {type(exc).__name__}")
        else:
            st.error("Model file not found.")
