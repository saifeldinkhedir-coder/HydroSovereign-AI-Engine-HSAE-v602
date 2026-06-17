"""
hydrosovereign/ai/conflict.py — ConflictIndex
==============================================
Composite conflict assessment for transboundary basins.

Author:  Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
from typing import Dict, List


class ConflictIndex:
    """Composite Conflict Index (CI) for a transboundary basin.

    Examples
    --------
    >>> ci = ConflictIndex(atdi=43.5, ahifd=20.0, dispute_level=4, n_countries=3)
    >>> print(ci.score)    # 0.44
    >>> print(ci.level)    # HIGH
    >>> print(ci.articles) # ['Art. 7', 'Art. 9', 'Art. 5']
    """

    THRESHOLDS = {"CRITICAL": 0.55, "HIGH": 0.40,
                  "MEDIUM":   0.25, "LOW":  0.0}

    def __init__(self, atdi:float, ahifd:float=0.0,
                 dispute_level:int=2, n_countries:int=3,
                 hifd:float=0.0) -> None:
        self.atdi          = atdi
        self.ahifd         = ahifd if ahifd > 0 else hifd
        self.dispute_level = dispute_level
        self.n_countries   = n_countries
        self.score         = self._compute()
        self.level         = self._classify()
        self.articles      = self._articles()

    def _compute(self) -> float:
        return round(min(1.0, max(0.0,
            0.40 * self.atdi / 100
          + 0.25 * self.dispute_level / 4.0
          + 0.20 * self.ahifd / 80.0
          + 0.10 * min((self.n_countries - 2) * 0.15, 0.1))), 3)

    def _classify(self) -> str:
        for level, thr in self.THRESHOLDS.items():
            if self.score >= thr:
                return level
        return "LOW"

    def _articles(self) -> List[str]:
        arts: List[str] = []
        if self.atdi  >= 40: arts.append("Art. 7")
        if self.ahifd >= 15: arts.append("Art. 9")
        if self.dispute_level >= 3: arts.append("Art. 33")
        if self.atdi  >= 25: arts.append("Art. 5")
        return arts

    def to_dict(self) -> Dict:
        return {"score": self.score, "level": self.level,
                "articles": self.articles,
                "atdi": self.atdi, "ahifd": self.ahifd}

    def __repr__(self) -> str:
        return f"ConflictIndex(score={self.score:.3f}, level={self.level})"
