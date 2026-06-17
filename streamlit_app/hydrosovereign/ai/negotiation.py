"""
hydrosovereign/ai/negotiation.py — NegotiationAI (DEPRECATED heuristic)
=======================================================================
A transparent, NON-trained heuristic that maps ATDI/AHIFD to an
indicative negotiation-pathway score. It is NOT a trained statistical
model and makes no use of historical training data.

For a genuinely trained, validated model use
``hydrosovereign.TreatyClassifier`` (GradientBoosting trained on the TFDD
treaties database, with an honest model card). That classifier predicts a
documented treaty property (presence of a conflict-resolution mechanism),
not negotiation success — which is not learnable from a database of
concluded treaties.

This module is retained only for backward compatibility and will be
REMOVED in v7.0.0. Importing it raises a DeprecationWarning.

Author:  Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
from typing import Dict
import warnings as _warnings

_warnings.warn(
    "hydrosovereign.ai.negotiation.NegotiationAI is a non-trained heuristic "
    "(not a statistical model) and is deprecated; use "
    "hydrosovereign.TreatyClassifier for the genuinely trained model. "
    "This module will be removed in v7.0.0.",
    DeprecationWarning, stacklevel=2,
)


class NegotiationAI:
    """Transparent heuristic for an indicative negotiation-pathway score.

    NOT a trained model: the score is a fixed, documented linear rule, not
    parameters fit to data. The weights below are declared, not learned.
    For a trained, validated model use ``hydrosovereign.TreatyClassifier``.

    Examples
    --------
    >>> ai = NegotiationAI()
    >>> p = ai.predict(atdi=43.5, ahifd=20.0, n_countries=3, dispute_level=4)
    >>> print(f"heuristic score = {p:.0%}")
    >>> print(ai.pathway)
    """

    PATHWAY_MAP = {
        (0.70, 1.01): ("Direct Negotiation", "Art. 8 Cooperation"),
        (0.50, 0.70): ("Mediation",           "Art. 17 Mediation"),
        (0.30, 0.50): ("PCA Arbitration",     "Art. 33 Dispute"),
        (0.00, 0.30): ("ICJ Referral",        "Art. 33 Dispute"),
    }

    def __init__(self) -> None:
        self.pathway:      str   = ""
        self.article:      str   = ""
        self._last_p:      float = 0.0

    def predict(
        self,
        atdi:          float,
        ahifd:         float = 0.0,
        n_countries:   int   = 3,
        dispute_level: int   = 2,
        hifd:          float = 0.0,
    ) -> float:
        """Heuristic negotiation-pathway score (NOT a trained prediction).

        Computes a transparent, fixed linear score from the inputs. The
        weights are declared (not learned). For a trained model use
        ``hydrosovereign.TreatyClassifier``.

        Parameters
        ----------
        atdi          : float — ATDI percentage
        ahifd         : float — AHIFD percentage
        n_countries   : int   — Riparian country count
        dispute_level : int   — Dispute intensity (1-4)
        hifd          : float — Alias for ahifd (backward compat)

        Returns
        -------
        float — heuristic score in [0.05, 0.95] (NOT a calibrated probability)
        """
        _ahifd = ahifd if ahifd > 0 else hifd
        p = round(max(0.05, min(0.95,
            0.70
            - (atdi  / 100) * 0.30
            - (_ahifd /  80) * 0.20
            + min(0.10, (n_countries - 2) * 0.03)
        )), 3)
        for (lo, hi), (path, art) in self.PATHWAY_MAP.items():
            if lo <= p < hi:
                self.pathway = path
                self.article = art
                break
        self._last_p = p
        return p

    def recommend(
        self,
        atdi: float, ahifd: float = 0.0,
        n_countries: int = 3, dispute_level: int = 2,
    ) -> Dict:
        """Full recommendation dictionary.

        Returns
        -------
        dict — probability, pathway, article, confidence
        """
        p = self.predict(atdi=atdi, ahifd=ahifd,
                         n_countries=n_countries,
                         dispute_level=dispute_level)
        return {"probability": p, "pathway": self.pathway,
                "article": self.article,
                "confidence": "HIGH" if 0.4 < p < 0.75 else "MEDIUM"}

    def __repr__(self) -> str:
        return f"NegotiationAI(p={self._last_p:.3f}, pathway={self.pathway!r})"
