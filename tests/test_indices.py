"""Tests for rebuilt, provenance-bound indices (indices_v2)."""
import pytest
from hydrosovereign_hsae.provenance import DataPoint, DataQuality, INSUFFICIENT_DATA
from hydrosovereign_hsae.ingestion import DataRegistry
from hydrosovereign_hsae.indices import (
    compute_tdi, compute_hifd, hifd_for_basin, tdi_for_basin, compute_atdi,
)


def _dp(variable, value, source="GRDC st.1577100",
        ref="https://grdc.bafg.de/", quality=DataQuality.OBSERVED,
        ds="2010-01-01", de="2020-12-31"):
    return DataPoint(value=value, variable=variable, unit="m3/s",
                     source=source, source_ref=ref,
                     date_start=ds, date_end=de, quality=quality)


class TestHIFDIndependence:
    """The central fix: HIFD must NOT collapse to a constant."""

    def test_hifd_varies_with_independent_inputs(self):
        # two independent observed sources
        q_nat = _dp("Q_nat", 1580.0, source="Pre-dam record",
                    ref="https://grdc.bafg.de/predam")
        q_obs = _dp("Q_obs", 1248.0, source="Post-dam gauge",
                    ref="https://grdc.bafg.de/postdam")
        r = compute_hifd(q_nat, q_obs)
        assert r.ok
        assert r.value == round((1580.0 - 1248.0) / 1580.0 * 100, 1)  # 21.0
        # change ONLY q_obs -> result must change (proves no cancellation)
        q_obs2 = _dp("Q_obs", 1000.0, source="Post-dam gauge 2",
                     ref="https://grdc.bafg.de/postdam2")
        r2 = compute_hifd(q_nat, q_obs2)
        assert r2.value != r.value
        assert r2.value == round((1580.0 - 1000.0) / 1580.0 * 100, 1)  # 36.7

    def test_hifd_rejects_shared_source(self):
        # legacy degeneracy guard: same source for both -> not independent
        q_nat = _dp("Q_nat", 1580.0)
        q_obs = _dp("Q_obs", 1248.0)  # identical source + ref
        r = compute_hifd(q_nat, q_obs)
        assert r.status == INSUFFICIENT_DATA
        assert "independent" in r.detail.lower()


class TestInsufficientData:
    def test_hifd_missing_qobs(self):
        q_nat = _dp("Q_nat", 1580.0, source="Pre-dam", ref="r1")
        bad = _dp("Q_obs", 1248.0, quality=DataQuality.ESTIMATE,
                  source="model", ref="r2")
        r = compute_hifd(q_nat, bad)
        assert r.status == INSUFFICIENT_DATA  # estimate not legal-grade

    def test_tdi_requires_observed(self):
        i_adj = _dp("I_adj", 1700.0, quality=DataQuality.SATELLITE,
                    source="GPM", ref="r1")
        q_obs = _dp("Q_obs", 1248.0, source="gauge", ref="r2")
        r = compute_tdi(i_adj, q_obs)
        assert r.status == INSUFFICIENT_DATA  # satellite not legal-grade


class TestTDI:
    def test_tdi_computed_from_observations(self):
        i_adj = _dp("I_adj", 1700.0, source="Observed inflow", ref="r1")
        q_obs = _dp("Q_obs", 1248.0, source="Observed outflow", ref="r2")
        r = compute_tdi(i_adj, q_obs)
        assert r.ok
        assert 0.0 <= r.value <= 1.0
        assert r.value == round((1700.0 - 1248.0) / (1700.0 + 1e-9), 4)


class TestRegistryDriven:
    def test_hifd_for_basin_insufficient_when_empty(self):
        reg = DataRegistry()
        r = hifd_for_basin(reg, "GERD")
        assert r.status == INSUFFICIENT_DATA
        assert "Q_nat" in r.detail and "Q_obs" in r.detail

    def test_hifd_for_basin_computes_with_independent_data(self):
        reg = DataRegistry()
        reg.submit("GERD", _dp("Q_nat", 1580.0, source="Pre-dam",
                               ref="https://grdc.bafg.de/predam"), "A")
        reg.submit("GERD", _dp("Q_obs", 1248.0, source="Post-dam gauge",
                               ref="https://grdc.bafg.de/postdam"), "B")
        r = hifd_for_basin(reg, "GERD")
        assert r.ok
        assert r.value == 21.0
        assert len(r.provenance()) == 2  # carries both sources

    def test_hifd_for_basin_partial_data(self):
        reg = DataRegistry()
        reg.submit("GERD", _dp("Q_nat", 1580.0, source="Pre-dam",
                               ref="r-predam"), "A")
        r = hifd_for_basin(reg, "GERD")  # Q_obs missing
        assert r.status == INSUFFICIENT_DATA
        assert "Q_obs" in r.detail


# ── Option A: empirical ATDI ──────────────────────────────────────
class TestATDIEmpirical:
    def test_atdi_mean_of_tdi(self):
        inflow = [_dp("I_adj", 1700.0, source="in", ref="r-in"),
                  _dp("I_adj", 1600.0, source="in", ref="r-in")]
        outflow = [_dp("Q_obs", 1248.0, source="out", ref="r-out"),
                   _dp("Q_obs", 1200.0, source="out", ref="r-out")]
        r = compute_atdi(inflow, outflow)
        assert r.ok
        # mean of two TDIs * 100, must lie in [0,100]
        assert 0.0 <= r.value <= 100.0

    def test_atdi_series_mismatch_insufficient(self):
        from hydrosovereign_hsae.indices import compute_atdi
        inflow = [_dp("I_adj", 1700.0, source="in", ref="r-in")]
        outflow = [_dp("Q_obs", 1248.0, source="out", ref="r-out"),
                   _dp("Q_obs", 1200.0, source="out", ref="r-out")]
        r = compute_atdi(inflow, outflow)
        assert r.status == INSUFFICIENT_DATA
        assert "mismatch" in r.detail

    def test_atdi_empty_insufficient(self):
        r = compute_atdi([], [])
        assert r.status == INSUFFICIENT_DATA


# ── Option B: composite AWGI ──────────────────────────────────────
class TestAWGIComposite:
    def test_weights_sum_to_one(self):
        from hydrosovereign_hsae.indices import AWGI_DEFAULT_WEIGHTS
        assert abs(sum(AWGI_DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9

    def test_factors_normalised_0_1(self):
        from hydrosovereign_hsae.indices import compute_awgi
        out = compute_awgi(transparency_deficit=0.436, dispute_level=4,
                           n_countries=3, regulation_intensity=0.5)
        for k, v in out["factors"].items():
            assert 0.0 <= v <= 1.0, f"{k}={v} out of [0,1]"
        assert 0.0 <= out["score"] <= 1.0

    def test_bad_weights_rejected(self):
        from hydrosovereign_hsae.indices import compute_awgi
        with pytest.raises(ValueError):
            compute_awgi(0.4, 4, 3, 0.5,
                         weights={"transparency": 0.5, "dispute": 0.2,
                                  "multiplicity": 0.1, "regulation": 0.1})

    def test_score_responds_to_inputs(self):
        from hydrosovereign_hsae.indices import compute_awgi
        low = compute_awgi(0.1, 1, 2, 0.1)["score"]
        high = compute_awgi(0.9, 5, 9, 0.9)["score"]
        assert high > low

    def test_sensitivity_runs(self):
        from hydrosovereign_hsae.indices import awgi_sensitivity
        s = awgi_sensitivity(0.436, 4, 3, 0.5)
        assert "weight_sensitivity" in s
        assert s["max_sensitivity"] >= 0.0

    def test_awgi_marked_normative(self):
        from hydrosovereign_hsae.indices import compute_awgi
        out = compute_awgi(0.4, 4, 3, 0.5)
        assert out["kind"] == "normative-composite"
        assert "not an empirical" in out["note"].lower()
