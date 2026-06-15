"""Tests for the open data ingestion registry (Layer 3)."""
import pytest
from hydrosovereign_hsae.provenance import DataPoint, DataQuality
from hydrosovereign_hsae.ingestion import (
    DataRegistry, ContributionRecord, RejectedContribution,
)


def _obs(**over):
    base = dict(
        value=1248.0, variable="Q_obs", unit="m3/s",
        source="GRDC station 1577100", source_ref="https://grdc.bafg.de/",
        date_start="2010-01-01", date_end="2020-12-31",
        quality=DataQuality.OBSERVED,
    )
    base.update(over)
    return DataPoint(**base)


class TestSubmission:
    def test_valid_observed_accepted(self):
        reg = DataRegistry()
        rec = reg.submit("GERD", _obs(), "Dr. X (ORCID 0000-...)")
        assert isinstance(rec, ContributionRecord)
        assert rec.record_id  # fingerprint assigned
        assert reg.get("GERD", "Q_obs") is not None

    def test_incomplete_provenance_rejected(self):
        reg = DataRegistry()
        with pytest.raises(RejectedContribution):
            reg.submit("GERD", _obs(source_ref=""), "Dr. X")
        # nothing stored
        assert reg.get("GERD", "Q_obs") is None

    def test_unknown_quality_rejected(self):
        reg = DataRegistry()
        with pytest.raises(RejectedContribution):
            reg.submit("GERD", _obs(quality=DataQuality.UNKNOWN), "Dr. X")

    def test_missing_contributor_rejected(self):
        reg = DataRegistry()
        with pytest.raises(RejectedContribution):
            reg.submit("GERD", _obs(), "")


class TestRetrieval:
    def test_legal_grade_only_skips_estimate(self):
        reg = DataRegistry()
        reg.submit("GERD", _obs(quality=DataQuality.ESTIMATE), "X")
        # estimate is valid-provenance but not legal grade
        assert reg.get("GERD", "Q_obs", legal_grade_only=True) is None
        assert reg.get("GERD", "Q_obs", legal_grade_only=False) is not None

    def test_most_recent_returned(self):
        reg = DataRegistry()
        reg.submit("GERD", _obs(value=1200.0), "X")
        reg.submit("GERD", _obs(value=1248.0), "Y")
        assert reg.get("GERD", "Q_obs").value == 1248.0

    def test_has_legal_grade(self):
        reg = DataRegistry()
        reg.submit("GERD", _obs(variable="Q_obs"), "X")
        assert not reg.has_legal_grade("GERD", "Q_obs", "Q_nat")
        reg.submit("GERD", _obs(variable="Q_nat", value=1580.0), "X")
        assert reg.has_legal_grade("GERD", "Q_obs", "Q_nat")


class TestAuditPersistence:
    def test_audit_log_lists_contributions(self):
        reg = DataRegistry()
        reg.submit("GERD", _obs(), "Contributor A")
        log = reg.audit_log()
        assert len(log) == 1
        assert log[0]["contributor"] == "Contributor A"
        assert log[0]["data_point"]["source"] == "GRDC station 1577100"

    def test_json_roundtrip_revalidates(self):
        reg = DataRegistry()
        reg.submit("GERD", _obs(), "X")
        reg.submit("Nile", _obs(variable="Q_nat", value=2810.0), "Y")
        text = reg.to_json()

        reg2 = DataRegistry()
        n = reg2.load_json(text)
        assert n == 2
        assert reg2.get("GERD", "Q_obs").value == 1248.0

    def test_fingerprint_is_deterministic(self):
        reg = DataRegistry()
        r1 = reg.submit("GERD", _obs(), "Same Person")
        reg2 = DataRegistry()
        r2 = reg2.submit("GERD", _obs(), "Same Person")
        assert r1.record_id == r2.record_id  # same content -> same id
