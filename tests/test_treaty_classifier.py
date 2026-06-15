"""Tests for the honest TFDD treaty-feature classifier."""
from hydrosovereign_hsae.treaty_classifier import TreatyClassifier, MODEL_CARD


class TestModelCard:
    def test_card_documents_real_source(self):
        assert "TFDD" in MODEL_CARD["source"]
        assert MODEL_CARD["n_labelled_used"] == 429  # real post-filter count

    def test_card_is_honest_about_task(self):
        # must NOT claim negotiation-outcome prediction
        assert "property" in MODEL_CARD["honest_note"].lower()
        assert "not negotiation" in MODEL_CARD["honest_note"].lower()

    def test_metrics_present(self):
        for k in ("test_f1", "test_roc_auc", "cv5_f1_mean",
                  "baseline_majority_f1"):
            assert k in MODEL_CARD


class TestTrainedModel:
    def test_model_available(self):
        assert TreatyClassifier().is_available

    def test_prediction_is_real_probability(self):
        tc = TreatyClassifier()
        p = tc.predict_proba(n_signatories=3, year=2015,
                             basin_treaty_count=12)
        assert 0.0 <= p <= 1.0

    def test_prediction_varies_with_input(self):
        tc = TreatyClassifier()
        p1 = tc.predict_proba(2, 1900, 1)
        p2 = tc.predict_proba(8, 2020, 30)
        # a real trained model responds to inputs
        assert p1 != p2

    def test_predict_returns_binary(self):
        tc = TreatyClassifier()
        assert tc.predict(3, 2015, 12) in (0, 1)
