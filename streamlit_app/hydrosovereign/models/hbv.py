"""
models/hbv.py — HBVModel class (OOP wrapper)
==============================================
Object-oriented interface to HBV-96 + SCE-UA calibration.
As requested by ChatGPT review: 'from hydrosovereign.models import HBVModel'

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
import numpy as np
from typing import Union, List, Optional, Dict
from ..hbv import run_hbv96, calibrate_hbv_sceua


class HBVModel:
    """
    HBV-96 Catchment Model — Object-Oriented Interface.

    Physics-based rainfall-runoff model (Bergström, 1992) with
    SCE-UA calibration (Duan et al., 1992).

    Parameters
    ----------
    area_km2 : float
        Catchment area (km²).
    runoff_c : float
        Runoff coefficient (0–1). Default = 0.38.
    params : dict, optional
        HBV-96 parameters. If None, uses physics-based defaults.

    Examples
    --------
    >>> import numpy as np
    >>> model = HBVModel(area_km2=174000, runoff_c=0.38)
    >>> P = np.maximum(0, 2.5*np.sin(np.pi*np.arange(365)/180))
    >>> T = np.full(365, 25.0)
    >>> result = model.simulate(P, T)
    >>> print(f"NSE = {result['nse']:.3f}")
    >>> print(f"Mean Q = {result['Q_sim'].mean():.1f} m³/s")
    """

    def __init__(
        self,
        area_km2: float,
        runoff_c: float = 0.38,
        params: Optional[Dict] = None,
    ):
        if area_km2 <= 0:
            raise ValueError(f"area_km2 must be > 0, got {area_km2}")
        if not 0 < runoff_c <= 1:
            raise ValueError(f"runoff_c must be in (0,1], got {runoff_c}")

        self.area_km2  = area_km2
        self.runoff_c  = runoff_c
        self.params    = params or {}
        self._calibrated = False
        self._nse        = None
        self._kge        = None

    def simulate(
        self,
        P: Union[np.ndarray, List[float]],
        T: Union[np.ndarray, List[float]],
        Q_obs: Optional[Union[np.ndarray, List[float]]] = None,
    ) -> dict:
        """
        Run HBV-96 simulation.

        Parameters
        ----------
        P : array-like
            Daily precipitation (mm/day).
        T : array-like
            Daily temperature (°C).
        Q_obs : array-like, optional
            Observed discharge for NSE/KGE computation.

        Returns
        -------
        dict
            - Q_sim  (ndarray) : simulated discharge (m³/s)
            - SM     (ndarray) : soil moisture (mm)
            - AET    (ndarray) : actual ET (mm/day)
            - nse    (float)   : NSE if Q_obs provided
            - kge    (float)   : KGE if Q_obs provided
            - n_days (int)     : simulation length
        """
        result = run_hbv96(P, T, self.area_km2, self.runoff_c, self.params)

        if Q_obs is not None:
            from ..indices import compute_nse, compute_kge
            Q_obs = np.asarray(Q_obs, dtype=float)
            n     = min(len(Q_obs), len(result["Q_sim"]))
            result["nse"] = compute_nse(Q_obs[:n], result["Q_sim"][:n])
            result["kge"] = compute_kge(Q_obs[:n], result["Q_sim"][:n])
            self._nse = result["nse"]
            self._kge = result["kge"]
        else:
            result["nse"] = None
            result["kge"] = None

        return result

    def calibrate(
        self,
        Q_obs: Union[np.ndarray, List[float]],
        P: Union[np.ndarray, List[float]],
        T: Union[np.ndarray, List[float]],
        n_complexes: int = 5,
        n_per_complex: int = 12,
        max_iter: int = 500,
        random_seed: int = 42,
    ) -> dict:
        """
        Calibrate HBV-96 using SCE-UA algorithm.

        Updates self.params with calibrated values.

        Parameters
        ----------
        Q_obs : array-like
            Observed discharge (m³/s) for calibration.
        P, T : array-like
            Daily forcing data.
        n_complexes : int
            SCE-UA complexes. Default = 5.
        n_per_complex : int
            Points per complex. Default = 12.
        max_iter : int
            Maximum iterations. Default = 500.

        Returns
        -------
        dict
            Calibration results with params, NSE, KGE, n_eval.

        Examples
        --------
        >>> model.calibrate(Q_obs, P, T)
        >>> print(f"Calibrated NSE = {model.nse:.3f}")
        """
        result = calibrate_hbv_sceua(
            Q_obs=Q_obs, P=P, T=T,
            area_km2=self.area_km2,
            runoff_c=self.runoff_c,
            n_complexes=n_complexes,
            n_per_complex=n_per_complex,
            max_iter=max_iter,
            random_seed=random_seed,
        )
        self.params      = result["params"]
        self._calibrated = True
        self._nse        = result["nse"]
        self._kge        = result["kge"]
        return result

    @property
    def nse(self) -> Optional[float]:
        """Most recent NSE value."""
        return self._nse

    @property
    def kge(self) -> Optional[float]:
        """Most recent KGE value."""
        return self._kge

    @property
    def is_calibrated(self) -> bool:
        """Whether calibration has been run."""
        return self._calibrated

    def summary(self) -> str:
        """Print model summary."""
        lines = [
            f"HBVModel Summary",
            f"  Area:     {self.area_km2:,.0f} km²",
            f"  Runoff_c: {self.runoff_c:.2f}",
            f"  Calibrated: {self._calibrated}",
        ]
        if self._nse is not None:
            lines += [f"  NSE: {self._nse:.3f}", f"  KGE: {self._kge:.3f}"]
        if self.params:
            lines.append("  Parameters:")
            for k, v in self.params.items():
                lines.append(f"    {k}: {v:.3f}")
        return "\n".join(lines)

    def __repr__(self):
        cal = f", NSE={self._nse:.3f}" if self._nse else ""
        return (f"HBVModel(area={self.area_km2:.0f}km², "
                f"runoff_c={self.runoff_c:.2f}"
                f"{cal})")
