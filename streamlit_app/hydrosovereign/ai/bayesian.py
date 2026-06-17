"""
hydrosovereign/ai/bayesian.py — Bayesian Uncertainty Quantification
====================================================================
Monte Carlo (n=500) + Sobol sensitivity analysis for AWSI indices.

Author:  Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
import numpy as np
from typing import Dict, Tuple


class BayesianUncertainty:
    """Monte Carlo uncertainty quantification for AWSI indices.

    Produces 95% credible intervals and Sobol first-order
    sensitivity indices for ATDI, AHIFD, and ATCI.

    Parameters
    ----------
    n_samples : int   — Monte Carlo samples (default 500)
    seed      : int   — Random seed for reproducibility

    Examples
    --------
    >>> bu = BayesianUncertainty(n_samples=500)
    >>> r  = bu.estimate(runoff_c=0.38, cap_bcm=74.0,
    ...                  n_countries=3, dispute_level=4)
    >>> print(r["atdi"]["mean"], r["atdi"]["ci95"])
    43.6  (40.1, 47.2)
    """

    def __init__(self, n_samples:int=500, seed:int=42) -> None:
        self.n_samples = n_samples
        self.rng       = np.random.default_rng(seed)

    def estimate(self, runoff_c:float, cap_bcm:float,
                 n_countries:int, dispute_level:int) -> Dict[str, Dict]:
        """Run Monte Carlo estimation.

        Returns
        -------
        dict — atdi, ahifd, atci each with
               {mean, std, p5, p95, ci95}
        """
        from hydrosovereign.indices import (compute_atdi,
                                             compute_ahifd,
                                             compute_atci)
        atdi_s, ahifd_s, atci_s = [], [], []
        for _ in range(self.n_samples):
            rc = max(0.05, min(0.95, runoff_c + self.rng.normal(0, 0.03)))
            cb = max(0.1,  cap_bcm  + self.rng.normal(0, cap_bcm * 0.08))
            nc = max(2, int(round(n_countries + self.rng.normal(0, 0.2))))
            dl = max(1, min(4, int(round(dispute_level + self.rng.normal(0, 0.3)))))
            atdi_s.append(compute_atdi(rc, cb, nc, dl))
            ahifd_s.append(compute_ahifd(rc, cb, nc, dl))
            atci_s.append(compute_atci(rc, cb, nc, dl))
        return {"atdi":  self._stats(atdi_s),
                "ahifd": self._stats(ahifd_s),
                "atci":  self._stats(atci_s)}

    def _stats(self, s:list) -> Dict:
        a = np.array(s)
        return {"mean": round(float(a.mean()),2),
                "std":  round(float(a.std()), 2),
                "p5":   round(float(np.percentile(a,  5)),2),
                "p95":  round(float(np.percentile(a, 95)),2),
                "ci95": (round(float(np.percentile(a,  2.5)),2),
                         round(float(np.percentile(a, 97.5)),2))}

    def sobol_sensitivity(self, runoff_c:float, cap_bcm:float,
                          n_countries:int, dispute_level:int) -> Dict[str,float]:
        """First-order Sobol sensitivity indices for ATDI.

        Returns
        -------
        dict — sensitivity of runoff_c, cap_bcm,
               n_countries, dispute_level (sum=1.0)
        """
        from hydrosovereign.indices import compute_atdi
        base = compute_atdi(runoff_c, cap_bcm, n_countries, dispute_level)
        specs = {"runoff_c":(runoff_c,0.05), "cap_bcm":(cap_bcm,cap_bcm*0.1),
                 "n_countries":(n_countries,0.3), "dispute_level":(dispute_level,0.3)}
        sens = {}
        for pname,(pval,pstd) in specs.items():
            ds = []
            for _ in range(200):
                kw = dict(runoff_c=runoff_c,cap_bcm=cap_bcm,
                          n_countries=n_countries,dispute_level=dispute_level)
                pert = float(pval) + self.rng.normal(0, pstd)
                if pname in ("n_countries","dispute_level"):
                    pert = int(max(1, round(pert)))
                kw[pname] = pert
                try:    ds.append((compute_atdi(**kw) - base)**2)
                except: pass
            sens[pname] = float(np.mean(ds)) if ds else 0.0
        total = sum(sens.values()) or 1
        return {k: round(v/total,3) for k,v in sens.items()}
