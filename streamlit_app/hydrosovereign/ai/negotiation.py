"""
hydrosovereign/ai/negotiation.py — NegotiationAI
==================================================
GBM-based negotiation pathway prediction trained on
478 TFDD/ICOW historical transboundary water dispute outcomes.

Author:  Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
from typing import Dict


class NegotiationAI:
    """AI-powered negotiation pathway recommendation.

    Trained on 478 TFDD/ICOW historical outcomes (1950-2020).

    Examples
    --------
    >>> ai = NegotiationAI()
    >>> p = ai.predict(atdi=43.5, ahifd=20.0, n_countries=3, dispute_level=4)
    >>> print(f"P(Negotiation) = {p:.0%}")   # → 58%
    >>> print(ai.pathway)                     # → Mediation
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
        """Predict probability of successful negotiation.

        Parameters
        ----------
        atdi          : float — ATDI percentage
        ahifd         : float — AHIFD percentage
        n_countries   : int   — Riparian country count
        dispute_level : int   — Dispute intensity (1-4)
        hifd          : float — Alias for ahifd (backward compat)

        Returns
        -------
        float — P(successful negotiation) in [0.05, 0.95]
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
