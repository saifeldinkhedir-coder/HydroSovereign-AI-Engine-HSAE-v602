"""Tests for independent model validation (objection #5)."""
from hydrosovereign_hsae.provenance import DataPoint, DataQuality, INSUFFICIENT_DATA
from hydrosovereign_hsae.validation import validate_model_skill


def _series(var, vals, source, ref, quality=DataQuality.REANALYSIS):
    return [DataPoint(value=v, variable=var, unit="m3/s", source=source,
                      source_ref=ref, date_start="2010-01-01",
                      date_end="2010-12-31", quality=quality) for v in vals]


class TestIndependence:
    def test_rejects_same_forcing(self):
        # THE core check: model GPM-forced, benchmark also GPM-derived
        model = _series("q_sim", [10, 11, 12], "HBV", "r1")
        bench = _series("q_bench", [10, 11, 12], "GPM-derived", "r2")
        r = validate_model_skill(model, bench,
                                 model_forcing_source="GPM IMERG",
                                 benchmark_forcing_source="GPM IMERG")
        assert r.status == INSUFFICIENT_DATA
        assert "not independent" in r.detail.lower()

    def test_accepts_independent_forcing(self):
        # model GPM-forced, benchmark true GloFAS (ERA5-forced) = independent
        model = _series("q_sim", [10, 11, 12, 13], "HBV", "r1")
        bench = _series("q_bench", [10, 11, 12, 13], "GloFAS ECMWF", "r2",
                        quality=DataQuality.REANALYSIS)
        r = validate_model_skill(model, bench,
                                 model_forcing_source="GPM IMERG",
                                 benchmark_forcing_source="ERA5")
        assert r.ok
        assert "NSE" in r.detail and "KGE" in r.detail
        assert "independence verified" in r.detail

    def test_requires_declared_forcing(self):
        model = _series("q_sim", [10, 11], "HBV", "r1")
        bench = _series("q_bench", [10, 11], "X", "r2")
        r = validate_model_skill(model, bench, "", "ERA5")
        assert r.status == INSUFFICIENT_DATA


class TestUsability:
    def test_length_mismatch(self):
        model = _series("q_sim", [10], "HBV", "r1")
        bench = _series("q_bench", [10, 11], "GloFAS", "r2")
        r = validate_model_skill(model, bench, "GPM", "ERA5")
        assert r.status == INSUFFICIENT_DATA

    def test_estimate_benchmark_rejected(self):
        model = _series("q_sim", [10, 11, 12], "HBV", "r1")
        bench = _series("q_bench", [10, 11, 12], "guess", "r2",
                        quality=DataQuality.ESTIMATE)
        r = validate_model_skill(model, bench, "GPM", "ERA5")
        assert r.status == INSUFFICIENT_DATA
