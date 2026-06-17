"""
ingestion.py — HSAE Open Data Ingestion Registry (Layer 3)
====================================================================
An open, auditable registry that lets anyone holding real, documented
streamflow (or related) observations contribute them to HSAE. Every
submission must carry full provenance (source, reference, dates,
quality); submissions that fail validation are rejected, never stored.

This realises the design goal: the system does not fabricate data — it
accepts verified observations from any contributor and records exactly
where each value came from, so results are reproducible and auditable.

Built alongside the legacy code (does not replace it yet). Depends only
on the provenance layer.

Author: Seifeldin M.G. Alkhedir - ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import hashlib
import datetime as _dt

from .provenance import (
    DataPoint, DataQuality, InsufficientDataError,
)


@dataclass
class ContributionRecord:
    """An accepted observation plus who contributed it and when."""
    data_point: DataPoint
    basin_id: str
    contributor: str               # name / institution / ORCID
    submitted_at: str = field(
        default_factory=lambda: _dt.datetime.now(_dt.timezone.utc).isoformat())
    record_id: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = self._fingerprint()

    def _fingerprint(self) -> str:
        """Deterministic id from content — enables audit & dedup."""
        dp = self.data_point
        raw = (f"{self.basin_id}|{dp.variable}|{dp.value}|{dp.unit}|"
               f"{dp.source}|{dp.source_ref}|{dp.date_start}|{dp.date_end}|"
               f"{self.contributor}")
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "basin_id": self.basin_id,
            "contributor": self.contributor,
            "submitted_at": self.submitted_at,
            "data_point": self.data_point.to_dict(),
        }


class RejectedContribution(ValueError):
    """Raised when a submission fails provenance validation."""


class DataRegistry:
    """
    In-memory open registry of provenance-verified observations.

    Submissions are validated before storage; anything without complete
    provenance is rejected with a clear reason. The registry can be
    serialised to / loaded from JSON for an auditable on-disk record.
    """

    def __init__(self):
        # basin_id -> variable -> list[ContributionRecord]
        self._store: Dict[str, Dict[str, List[ContributionRecord]]] = {}

    # ── submission ────────────────────────────────────────────────
    def submit(self, basin_id: str, data_point: DataPoint,
               contributor: str) -> ContributionRecord:
        """
        Validate and store one observation. Raises RejectedContribution
        if provenance is incomplete. Never stores an invalid point.
        """
        try:
            data_point.validate()
        except InsufficientDataError as e:
            raise RejectedContribution(
                f"rejected ({basin_id}/{data_point.variable}): {e}") from e
        if not str(contributor).strip():
            raise RejectedContribution("rejected: contributor is required")

        rec = ContributionRecord(
            data_point=data_point, basin_id=basin_id, contributor=contributor)
        basin_store = self._store.setdefault(basin_id, {})
        basin_store.setdefault(data_point.variable, []).append(rec)
        return rec

    # ── retrieval ─────────────────────────────────────────────────
    def get(self, basin_id: str, variable: str,
            legal_grade_only: bool = True) -> Optional[DataPoint]:
        """
        Return the most recent qualifying observation for a basin/variable,
        or None if none exists. With legal_grade_only=True (default), only
        observation-grade points are eligible — so a legal computation
        never silently uses an estimate.
        """
        recs = self._store.get(basin_id, {}).get(variable, [])
        for rec in reversed(recs):  # most recent first
            dp = rec.data_point
            if legal_grade_only and not dp.is_legal_grade():
                continue
            if not legal_grade_only and not dp.is_valid():
                continue
            return dp
        return None

    def has_legal_grade(self, basin_id: str, *variables: str) -> bool:
        """True only if every named variable has an observation-grade value."""
        return all(self.get(basin_id, v, legal_grade_only=True) is not None
                   for v in variables)

    def records(self, basin_id: Optional[str] = None) -> List[ContributionRecord]:
        """All contribution records (optionally for one basin)."""
        out: List[ContributionRecord] = []
        basins = [basin_id] if basin_id else list(self._store)
        for b in basins:
            for var_recs in self._store.get(b, {}).values():
                out.extend(var_recs)
        return out

    # ── audit / persistence ───────────────────────────────────────
    def audit_log(self) -> List[dict]:
        """Full auditable list of every accepted contribution."""
        return [r.to_dict() for r in self.records()]

    def to_json(self) -> str:
        return json.dumps(self.audit_log(), indent=2, ensure_ascii=False)

    def load_json(self, text: str) -> int:
        """
        Load records from JSON. Each is re-validated on load; invalid
        records are skipped (never silently trusted). Returns count loaded.
        """
        loaded = 0
        for item in json.loads(text):
            dpd = item["data_point"]
            try:
                dp = DataPoint(
                    value=dpd["value"], variable=dpd["variable"],
                    unit=dpd["unit"], source=dpd["source"],
                    source_ref=dpd["source_ref"],
                    date_start=dpd["date_start"], date_end=dpd["date_end"],
                    quality=DataQuality(dpd["quality"]),
                    retrieved_at=dpd.get("retrieved_at", ""),
                    notes=dpd.get("notes", ""),
                )
                self.submit(item["basin_id"], dp, item["contributor"])
                loaded += 1
            except (RejectedContribution, KeyError, ValueError):
                continue
        return loaded
