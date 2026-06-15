"""Tests for the data-provenance foundation layer."""
import pytest
from hydrosovereign_hsae.provenance import (
    DataPoint, DataQuality, ProvenancedResult,
    InsufficientDataError, INSUFFICIENT_DATA,
    insufficient, require_legal_grade,
)


def _good_point(**over):
    base = dict(
        value=1248.0, variable="Q_obs", unit="m3/s",
        source="GRDC station 1577100",
        source_ref="https://grdc.bafg.de/",
        date_start="2010-01-01", date_end="2020-12-31",
        quality=DataQuality.OBSERVED,
    )
    base.update(over)
    return DataPoint(**base)


class TestDataPointValidation:
    def test_complete_observed_point_is_valid(self):
        assert _good_point().is_valid()
        assert _good_point().is_legal_grade()

    def test_unknown_quality_rejected(self):
        dp = _good_point(quality=DataQuality.UNKNOWN)
        assert not dp.is_valid()
        with pytest.raises(InsufficientDataError):
            dp.validate()

    def test_missing_source_ref_rejected(self):
        assert not _good_point(source_ref="").is_valid()

    def test_missing_source_rejected(self):
        assert not _good_point(source="").is_valid()

    def test_missing_dates_rejected(self):
        assert not _good_point(date_start="").is_valid()
        assert not _good_point(date_end="").is_valid()

    def test_estimate_is_valid_but_not_legal_grade(self):
        dp = _good_point(quality=DataQuality.ESTIMATE)
        assert dp.is_valid()            # has provenance
        assert not dp.is_legal_grade()  # but not observation-grade

    def test_reanalysis_not_legal_grade(self):
        dp = _good_point(quality=DataQuality.REANALYSIS)
        assert not dp.is_legal_grade()

    def test_citation_contains_source_and_dates(self):
        c = _good_point().citation()
        assert "GRDC station 1577100" in c
        assert "2010-01-01" in c
        assert "observed" in c


class TestLegalGrade:
    def test_gate_passes_with_observed(self):
        q_obs = _good_point()
        q_nat = _good_point(variable="Q_nat", value=1580.0)
        assert require_legal_grade("HIFD", q_obs, q_nat) is None

    def test_gate_blocks_estimate(self):
        q_obs = _good_point()
        q_nat = _good_point(variable="Q_nat", quality=DataQuality.ESTIMATE)
        r = require_legal_grade("HIFD", q_obs, q_nat)
        assert r is not None
        assert r.status == INSUFFICIENT_DATA
        assert not r.ok

    def test_gate_blocks_incomplete_provenance(self):
        q_obs = _good_point()
        q_nat = _good_point(variable="Q_nat", source_ref="")
        r = require_legal_grade("HIFD", q_obs, q_nat)
        assert r.status == INSUFFICIENT_DATA


class TestProvenancedResult:
    def test_insufficient_has_no_value(self):
        r = insufficient("ATDI", "no observed discharge")
        assert r.value is None
        assert not r.ok
        assert r.status == INSUFFICIENT_DATA

    def test_ok_result_carries_provenance(self):
        dp = _good_point()
        r = ProvenancedResult(metric="HIFD", value=21.0, status="OK",
                              inputs=[dp], method="Eq.6")
        assert r.ok
        assert len(r.provenance()) == 1
        assert "GRDC" in r.provenance()[0]

    def test_to_dict_roundtrip(self):
        dp = _good_point()
        r = ProvenancedResult(metric="HIFD", value=21.0, status="OK",
                              inputs=[dp], method="Eq.6")
        d = r.to_dict()
        assert d["metric"] == "HIFD"
        assert d["inputs"][0]["source"] == "GRDC station 1577100"
        assert d["inputs"][0]["quality"] == "observed"
