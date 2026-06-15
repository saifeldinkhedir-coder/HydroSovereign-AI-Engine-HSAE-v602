"""Tests for the 4 rebuilt indices: AFSF, AHLB, ASI, ATCI."""
import pytest
from hydrosovereign_hsae.provenance import DataPoint, DataQuality, INSUFFICIENT_DATA
from hydrosovereign_hsae.indices import (
    compute_afsf, compute_ahlb, compute_asi, compute_atci,
)


def _dp(variable, value, source="GRDC", ref="https://grdc.bafg.de/",
        quality=DataQuality.OBSERVED):
    return DataPoint(value=value, variable=variable, unit="m3/s",
                     source=source, source_ref=ref,
                     date_start="2010-01-01", date_end="2020-12-31",
                     quality=quality)


class TestAFSF:
    def test_computes_from_independent_observations(self):
        obs = _dp("anomaly_obs", 0.8, source="Satellite obs", ref="r1")
        nat = _dp("anomaly_nat", 0.3, source="Pre-dam baseline", ref="r2")
        rng = _dp("range", 1.0, source="Computed range", ref="r3")
        r = compute_afsf(obs, nat, rng)
        assert r.ok
        assert r.value == 0.5  # |0.8-0.3|/1.0

    def test_rejects_shared_source(self):
        obs = _dp("anomaly_obs", 0.8)
        nat = _dp("anomaly_nat", 0.3)  # same source+ref
        rng = _dp("range", 1.0, source="r", ref="r3")
        r = compute_afsf(obs, nat, rng)
        assert r.status == INSUFFICIENT_DATA

    def test_estimate_rejected(self):
        obs = _dp("anomaly_obs", 0.8, source="s1", ref="r1",
                  quality=DataQuality.ESTIMATE)
        nat = _dp("anomaly_nat", 0.3, source="s2", ref="r2")
        rng = _dp("range", 1.0, source="s3", ref="r3")
        assert compute_afsf(obs, nat, rng).status == INSUFFICIENT_DATA


class TestAHLB:
    def test_computes_nse_from_paired_series(self):
        sim = [_dp("q_sim", v, source="HBV", ref="rsim") for v in (10, 12, 11, 13)]
        obs = [_dp("q_obs", v, source="gauge", ref="robs") for v in (10, 11, 12, 13)]
        r = compute_ahlb(sim, obs)
        assert r.ok
        assert 0.0 <= r.value <= 1.0
        assert "NSE" in r.detail

    def test_length_mismatch_insufficient(self):
        sim = [_dp("q_sim", 10, source="HBV", ref="rsim")]
        obs = [_dp("q_obs", v, source="gauge", ref="robs") for v in (10, 11)]
        assert compute_ahlb(sim, obs).status == INSUFFICIENT_DATA

    def test_empty_insufficient(self):
        assert compute_ahlb([], []).status == INSUFFICIENT_DATA


class TestASI:
    def test_weights_sum_to_one(self):
        from hydrosovereign_hsae.indices import ASI_DEFAULT_WEIGHTS
        assert abs(sum(ASI_DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9

    def test_normalised_and_normative(self):
        out = compute_asi(0.6, 0.5, 0.4)
        assert 0.0 <= out["score"] <= 1.0
        assert out["kind"] == "normative-composite"
        for v in out["factors"].values():
            assert 0.0 <= v <= 1.0

    def test_bad_weights_rejected(self):
        with pytest.raises(ValueError):
            compute_asi(0.6, 0.5, 0.4,
                        weights={"equity": 0.5, "cooperation": 0.2,
                                 "data_sharing": 0.1})


class TestATCI:
    def test_weights_sum_to_one(self):
        from hydrosovereign_hsae.indices import ATCI_DEFAULT_WEIGHTS
        assert abs(sum(ATCI_DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9

    def test_score_100_scale(self):
        out = compute_atci(0.6, 0.6, 0.5, 0.8, 1.0)
        assert 0.0 <= out["score_100"] <= 100.0
        assert out["kind"] == "normative-composite"

    def test_responds_to_inputs(self):
        low = compute_atci(0.1, 0.1, 0.1, 0.1, 0.0)["score_100"]
        high = compute_atci(0.9, 0.9, 0.9, 0.9, 1.0)["score_100"]
        assert high > low

    def test_bad_weights_rejected(self):
        with pytest.raises(ValueError):
            compute_atci(0.6, 0.6, 0.5, 0.8, 1.0,
                         weights={"no_harm": 0.5})
