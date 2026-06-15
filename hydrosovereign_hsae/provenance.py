"""
provenance.py — HSAE Data Provenance Layer
====================================================================
Foundational data-integrity layer. Every numeric value entering an
index computation MUST carry verifiable provenance. Values without a
documented source are rejected, and computations that lack the
required observed data return INSUFFICIENT_DATA rather than a
fabricated number.

This directly addresses the core scientific objection that results
must derive from real, documented data — not hard-coded constants.

Author: Seifeldin M.G. Alkhedir - ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any
import datetime as _dt


class DataQuality(str, Enum):
    """Quality tier of a data point, in descending order of evidential weight."""
    OBSERVED = "observed"        # direct gauge / station measurement
    REANALYSIS = "reanalysis"    # model-based reanalysis (e.g. GloFAS-ERA5)
    SATELLITE = "satellite"      # satellite-derived product (e.g. GPM IMERG)
    ESTIMATE = "estimate"        # derived/approximate; NOT valid for legal use
    UNKNOWN = "unknown"          # provenance not established -> rejected


# Quality tiers that are acceptable for a legally-relevant computation.
# Estimates and unknowns are explicitly excluded.
LEGAL_GRADE_QUALITY = frozenset({DataQuality.OBSERVED})

# Quality tiers acceptable for model validation (a reanalysis proxy is
# acceptable for skill assessment only if independent of the model forcing;
# that independence is checked separately, not here).
VALIDATION_GRADE_QUALITY = frozenset({DataQuality.OBSERVED, DataQuality.REANALYSIS})


class InsufficientDataError(ValueError):
    """Raised when a computation is attempted without adequately-sourced data."""


# Sentinel returned (rather than raised) by non-strict callers.
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class DataPoint:
    """
    A single numeric value bound to its provenance.

    A DataPoint is only considered usable when it has a real numeric
    value, a named source, a source reference (URL/DOI), a date range,
    and a quality flag that is not UNKNOWN. Anything less is rejected
    by `validate()`.
    """
    value: float
    variable: str                 # e.g. "Q_obs", "Q_nat", "precip"
    unit: str                     # e.g. "m3/s", "mm/day", "BCM"
    source: str                   # e.g. "GRDC station 1577100"
    source_ref: str               # URL or DOI documenting the source
    date_start: str               # ISO date "YYYY-MM-DD"
    date_end: str                 # ISO date "YYYY-MM-DD"
    quality: DataQuality = DataQuality.UNKNOWN
    retrieved_at: str = field(
        default_factory=lambda: _dt.date.today().isoformat()
    )
    notes: str = ""

    def is_valid(self) -> bool:
        """True only if every provenance requirement is met."""
        try:
            self.validate()
            return True
        except InsufficientDataError:
            return False

    def validate(self) -> "DataPoint":
        """Raise InsufficientDataError if provenance is incomplete."""
        if self.value is None or not isinstance(self.value, (int, float)):
            raise InsufficientDataError(
                f"{self.variable}: no numeric value")
        if self.quality == DataQuality.UNKNOWN:
            raise InsufficientDataError(
                f"{self.variable}: quality flag is UNKNOWN")
        for fname in ("source", "source_ref", "date_start", "date_end", "unit"):
            if not str(getattr(self, fname)).strip():
                raise InsufficientDataError(
                    f"{self.variable}: missing required field '{fname}'")
        return self

    def is_legal_grade(self) -> bool:
        """True if this point may back a legally-relevant computation."""
        return self.is_valid() and self.quality in LEGAL_GRADE_QUALITY

    def citation(self) -> str:
        """Human-readable provenance string for output transparency."""
        return (f"{self.value} {self.unit} ({self.variable}) "
                f"[{self.quality.value}] "
                f"source: {self.source}, {self.date_start}..{self.date_end}, "
                f"ref: {self.source_ref}")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["quality"] = self.quality.value
        return d


@dataclass
class ProvenancedResult:
    """
    An index/metric result that carries the provenance of every input,
    or an explicit INSUFFICIENT_DATA status when it could not be
    computed from adequately-sourced data.
    """
    metric: str
    value: Optional[float]
    status: str                   # "OK" or INSUFFICIENT_DATA
    inputs: List[DataPoint] = field(default_factory=list)
    method: str = ""              # equation / reference used
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "OK" and self.value is not None

    def provenance(self) -> List[str]:
        """List the citation of every input that fed this result."""
        return [dp.citation() for dp in self.inputs]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "value": self.value,
            "status": self.status,
            "method": self.method,
            "detail": self.detail,
            "inputs": [dp.to_dict() for dp in self.inputs],
        }


def insufficient(metric: str, detail: str,
                 partial_inputs: Optional[List[DataPoint]] = None
                 ) -> ProvenancedResult:
    """Construct an INSUFFICIENT_DATA result (no fabricated value)."""
    return ProvenancedResult(
        metric=metric, value=None, status=INSUFFICIENT_DATA,
        inputs=list(partial_inputs or []), detail=detail,
    )


def require_legal_grade(metric: str, *points: DataPoint) -> Optional[ProvenancedResult]:
    """
    Gate before a legally-relevant computation. Returns an
    INSUFFICIENT_DATA ProvenancedResult if any required input is
    missing or not observation-grade; returns None if all inputs pass
    (meaning the caller may proceed to compute).
    """
    for dp in points:
        if not dp.is_valid():
            return insufficient(
                metric,
                f"input '{dp.variable}' has incomplete provenance",
                list(points))
        if not dp.is_legal_grade():
            return insufficient(
                metric,
                f"input '{dp.variable}' is '{dp.quality.value}', "
                f"not observation-grade; legal computation requires "
                f"observed data",
                list(points))
    return None
