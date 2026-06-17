"""
forecast.py — HSAE v6.4.0 Multi-Feature Discharge Forecasting
==============================================================
LinearForecast : Ridge Regression baseline (numpy-only)
LSTMForecast   : True PyTorch LSTM — supports up to 5 input features:
                 P (precipitation), T (temperature), SM (soil moisture),
                 TWS (GRACE-FO terrestrial water storage), ET0 (evapotranspiration)
                 Tensors: (batch, seq_len, n_features)

As recommended by Gemini v6.4.0:
  "A PyTorch LSTM processing (batch, seq_len, 4_features) will yield
   vastly superior discharge forecasts compared to just P and T."

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
import logging
import numpy as np
from typing import Union, List, Optional, Dict

logger = logging.getLogger(__name__)

_FEATURES_DEFAULT = ["P", "T"]
_FEATURES_FULL    = ["P", "T", "SM", "TWS", "ET0"]


class LinearForecast:
    """Ridge Regression discharge forecaster (numpy-only baseline).

    Examples
    --------
    >>> m = LinearForecast(lookback=30, horizon=7)
    >>> m.fit(P, T, area_km2=174000)
    >>> fc = m.predict(P[-30:], T[-30:])
    """

    def __init__(self, lookback=30, horizon=7, lam=0.01):
        self.lookback=lookback; self.horizon=horizon; self.lam=lam; self._fitted=False

    def fit(self, P, T, Q_obs=None, area_km2=174000, runoff_c=0.38, **kwargs):
        P=np.asarray(P,float); T=np.asarray(T,float); n=len(P)
        if Q_obs is None:
            from ..models.hbv import HBVModel
            Q_obs = HBVModel(area_km2=area_km2, runoff_c=runoff_c).simulate(P, T)["Q_sim"]
        Q_obs=np.asarray(Q_obs,float)
        self._Pm,self._Ps=P.mean(),max(P.std(),1e-6)
        self._Tm,self._Ts=T.mean(),max(T.std(),1e-6)
        self._Qm,self._Qs=Q_obs.mean(),max(Q_obs.std(),1e-6)
        Pn=(P-self._Pm)/self._Ps; Tn=(T-self._Tm)/self._Ts; Qn=(Q_obs-self._Qm)/self._Qs
        X,y=[],[]
        for i in range(self.lookback, n-self.horizon):
            X.append(np.column_stack([Pn[i-self.lookback:i],Tn[i-self.lookback:i]]).flatten())
            y.append(Qn[i:i+self.horizon].mean())
        X=np.array(X); y=np.array(y)
        self._w=np.linalg.lstsq(X.T@X+self.lam*np.eye(X.shape[1]),X.T@y,rcond=None)[0]
        yp=X@self._w
        self._r2=float(1-np.sum((y-yp)**2)/(np.sum((y-y.mean())**2)+1e-9))
        self._fitted=True
        logger.info("LinearForecast fitted R²=%.3f",self._r2)
        return self

    def predict(self, P_recent, T_recent):
        if not self._fitted: raise RuntimeError("Call fit() first")
        Pn=(np.asarray(P_recent,float)[-self.lookback:]-self._Pm)/self._Ps
        Tn=(np.asarray(T_recent,float)[-self.lookback:]-self._Tm)/self._Ts
        Qm=float(np.column_stack([Pn,Tn]).flatten()@self._w)*self._Qs+self._Qm
        Q_fc=np.array([max(0,Qm*(1+0.02*(i-self.horizon//2))) for i in range(self.horizon)])
        unc=max(5.,18*(1-self._r2)); delta=Q_fc*unc/100
        return {"Q_forecast":np.round(Q_fc,2),"Q_upper":np.round(Q_fc+delta,2),
                "Q_lower":np.round(np.maximum(0,Q_fc-delta),2),
                "horizon_days":self.horizon,"r2_train":round(self._r2,3),
                "uncertainty_pct":round(unc,1),"model":"LinearForecast(Ridge)",
                "n_features":2}

    def __repr__(self):
        return (f"LinearForecast(lb={self.lookback},R²={self._r2:.3f})"
                if self._fitted else f"LinearForecast(lb={self.lookback},not fitted)")


class LSTMForecast:
    """
    Multi-feature PyTorch LSTM discharge forecaster.

    Supports up to 5 input features:
      - P   : precipitation (mm/day)         — required
      - T   : temperature (°C)               — required
      - SM  : soil moisture (m³/m³, SMAP)    — optional
      - TWS : water storage anomaly (cm, GRACE-FO) — optional
      - ET0 : reference ET (mm/day)          — optional

    Architecture: Input(n_feat) → LSTM(hidden, layers) → Linear(horizon)
    Tensors:      (batch, seq_len, n_features)

    Parameters
    ----------
    lookback : int
        Sequence length (days). Default = 30.
    horizon : int
        Forecast horizon (days). Default = 7.
    hidden_size : int
        LSTM hidden state size. Default = 64.
    n_layers : int
        Stacked LSTM layers. Default = 2.
    features : list, optional
        Feature names. Default = ["P","T"].
        Full set: ["P","T","SM","TWS","ET0"]

    Examples
    --------
    >>> # Standard 2-feature LSTM
    >>> model = LSTMForecast(lookback=30, horizon=7)
    >>> model.fit(P, T, area_km2=174000, epochs=50)
    >>> fc = model.predict(P[-30:], T[-30:])

    >>> # Multi-feature LSTM with GEE data
    >>> from hydrosovereign.data import fetch_basin_forcing
    >>> data = fetch_basin_forcing("Blue Nile (GERD)", years=3)
    >>> model = LSTMForecast(features=["P","T","SM","ET0"])
    >>> model.fit_multi(data, area_km2=174000, epochs=50)
    >>> fc = model.predict_multi(data, lookback=30)
    >>> print(fc["model"])   # LSTM(4_features, hidden=64, PyTorch)
    """

    def __init__(self, lookback=30, horizon=7, hidden_size=64, n_layers=2,
                 dropout=0.2, random_seed=42, features=None):
        self.lookback    = lookback
        self.horizon     = horizon
        self.hidden_size = hidden_size
        self.n_layers    = n_layers
        self.dropout     = dropout
        self.random_seed = random_seed
        self.features    = features or ["P","T"]
        self._n_feat     = len(self.features)
        self._fitted     = False
        self._net        = None

    def _build_net(self, n_features: int):
        import torch.nn as nn, torch

        class _HydroLSTM(nn.Module):
            def __init__(s, inp, hid, lay, hor, drop):
                super().__init__()
                s.lstm = nn.LSTM(inp, hid, lay, batch_first=True,
                                 dropout=drop if lay>1 else 0.)
                s.drop = nn.Dropout(drop)
                s.fc   = nn.Linear(hid, hor)

            def forward(s, x):
                # x: (batch, seq_len, n_features)
                out, _ = s.lstm(x)
                return s.fc(s.drop(out[:, -1, :]))  # (batch, horizon)

        torch.manual_seed(self.random_seed)
        return _HydroLSTM(n_features, self.hidden_size, self.n_layers,
                          self.horizon, self.dropout)

    def _make_X_array(self, arrays: Dict[str, np.ndarray]) -> np.ndarray:
        """Stack feature arrays into (n, seq_len, n_feat) tensor."""
        cols = []
        for feat in self.features:
            arr = np.asarray(arrays.get(feat, np.zeros(len(next(iter(arrays.values()))))), float)
            cols.append(arr)
        return np.column_stack(cols)  # (n_days, n_features)

    def fit(self, P, T, Q_obs=None, area_km2=174000, runoff_c=0.38,
            epochs=50, lr=1e-3, batch_size=32, **kwargs):
        """Standard 2-feature fit (P, T). See fit_multi() for GEE data."""
        return self.fit_multi(
            {"P": np.asarray(P, float), "T": np.asarray(T, float)},
            Q_obs=Q_obs, area_km2=area_km2, runoff_c=runoff_c,
            epochs=epochs, lr=lr, batch_size=batch_size,
        )

    def fit_multi(self, feature_arrays: Dict[str, np.ndarray],
                  Q_obs=None, area_km2=174000, runoff_c=0.38,
                  epochs=50, lr=1e-3, batch_size=32):
        """
        Fit LSTM with multiple input features (data fusion).

        Parameters
        ----------
        feature_arrays : dict
            Must contain at minimum "P" and "T". Optionally:
            "SM" (SMAP soil moisture), "TWS" (GRACE-FO), "ET0".
        Q_obs : array-like, optional
            Observed discharge. If None, HBV-96 simulation used.
        area_km2 : float
            Catchment area for HBV fallback.
        epochs : int
            Training epochs. Default = 50.

        Examples
        --------
        >>> from hydrosovereign.data import fetch_basin_forcing
        >>> data = fetch_basin_forcing("Blue Nile (GERD)", years=3)
        >>> model = LSTMForecast(features=["P","T","SM","ET0"])
        >>> model.fit_multi(data, area_km2=174000, epochs=30)
        >>> fc = model.predict_multi(data)
        """
        P = np.asarray(feature_arrays.get("P", []), float)
        T = np.asarray(feature_arrays.get("T", []), float)
        n = len(P)

        # Update features to match what's actually available
        available = ["P","T"] + [f for f in ["SM","TWS","ET0"]
                                   if f in feature_arrays and
                                   len(feature_arrays[f]) == n and
                                   not all(v is None for v in feature_arrays[f])]
        self.features = available
        self._n_feat  = len(available)
        logger.info("LSTMForecast: using %d features: %s", self._n_feat, available)

        try:
            import torch, torch.nn as nn, torch.optim as optim
            self._use_torch = True
        except ImportError:
            logger.warning("PyTorch not available — falling back to LinearForecast")
            lf = LinearForecast(self.lookback, self.horizon)
            lf.fit(P, T, Q_obs=Q_obs)
            self.__dict__.update({k: v for k, v in lf.__dict__.items()})
            self._fallback = True; self._fitted = True; return self

        self._fallback = False

        if Q_obs is None:
            from ..models.hbv import HBVModel
            Q_obs = HBVModel(area_km2=area_km2, runoff_c=runoff_c).simulate(P, T)["Q_sim"]
        Q_obs = np.asarray(Q_obs, float)

        # Normalize each feature
        self._scalers = {}
        feat_matrix = np.zeros((n, self._n_feat))
        for j, feat in enumerate(self.features):
            arr = np.asarray(feature_arrays.get(feat, np.zeros(n)), float)
            # Fill None values with mean
            arr = np.where(np.isnan(arr.astype(float)), np.nanmean(arr) if np.any(~np.isnan(arr)) else 0.0, arr)
            m, s = arr.mean(), max(arr.std(), 1e-6)
            self._scalers[feat] = (m, s)
            feat_matrix[:, j] = (arr - m) / s

        self._Qm, self._Qs = Q_obs.mean(), max(Q_obs.std(), 1e-6)
        Qn = (Q_obs - self._Qm) / self._Qs

        # Build 3D sequences: (N, lookback, n_features)
        X_seq, y_seq = [], []
        for i in range(self.lookback, n - self.horizon):
            X_seq.append(feat_matrix[i-self.lookback:i, :])  # (lookback, n_feat)
            y_seq.append(Qn[i:i+self.horizon].mean())

        X_t = torch.FloatTensor(np.array(X_seq))        # (N, lookback, n_feat)
        y_t = torch.FloatTensor(np.array(y_seq)).unsqueeze(1)

        self._net = self._build_net(self._n_feat)
        opt   = optim.Adam(self._net.parameters(), lr=lr)
        sched = optim.lr_scheduler.ReduceLROnPlateau(opt, patience=5, factor=0.5)
        crit  = nn.HuberLoss()
        N = len(X_t); best = float("inf")

        for ep in range(epochs):
            self._net.train()
            idx = torch.randperm(N); ep_loss = 0.0
            for i in range(0, N, batch_size):
                bX = X_t[idx[i:i+batch_size]]; by = y_t[idx[i:i+batch_size]]
                opt.zero_grad()
                loss = crit(self._net(bX).mean(dim=1, keepdim=True), by)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self._net.parameters(), 1.0)
                opt.step(); ep_loss += loss.item()
            ep_loss /= max(1, N // batch_size)
            sched.step(ep_loss)
            if ep_loss < best: best = ep_loss

        self._net.eval()
        with torch.no_grad():
            yp = self._net(X_t).mean(dim=1).numpy()
        yr = y_t.squeeze().numpy()
        self._r2 = float(1 - np.sum((yr-yp)**2) / (np.sum((yr-yr.mean())**2) + 1e-9))
        self._best_loss = best
        self._fitted = True
        logger.info("LSTMForecast fitted: n_feat=%d R²=%.3f loss=%.4f",
                    self._n_feat, self._r2, best)
        return self

    def predict(self, P_recent, T_recent):
        """Standard 2-feature prediction."""
        return self.predict_multi({
            "P": np.asarray(P_recent, float),
            "T": np.asarray(T_recent, float),
        })

    def predict_multi(self, recent_arrays: Dict[str, np.ndarray]) -> dict:
        """
        Forecast with multi-feature input.

        Parameters
        ----------
        recent_arrays : dict
            Recent values for each feature (last `lookback` days).
            Keys matching self.features.

        Returns
        -------
        dict
            Q_forecast, Q_upper, Q_lower, model, n_features, r2_train.
        """
        if not self._fitted: raise RuntimeError("Call fit() or fit_multi() first")
        if getattr(self, "_fallback", False):
            P = np.asarray(recent_arrays.get("P", []), float)
            T = np.asarray(recent_arrays.get("T", []), float)
            return LinearForecast.predict(self, P, T)

        import torch
        self._net.eval()

        # Build feature matrix for recent window
        feat_mat = np.zeros((self.lookback, self._n_feat))
        for j, feat in enumerate(self.features):
            arr = np.asarray(recent_arrays.get(feat, np.zeros(self.lookback)), float)[-self.lookback:]
            m, s = self._scalers.get(feat, (0., 1.))
            feat_mat[:, j] = (arr - m) / s

        seq = torch.FloatTensor(feat_mat[np.newaxis, :, :])  # (1, lb, n_feat)
        with torch.no_grad():
            pred = self._net(seq).squeeze().numpy()

        Q_fc  = np.maximum(0, pred * self._Qs + self._Qm)
        unc   = max(5., 15. * (1 - self._r2))
        delta = Q_fc * unc / 100

        return {
            "Q_forecast":    np.round(Q_fc, 2),
            "Q_upper":       np.round(Q_fc + delta, 2),
            "Q_lower":       np.round(np.maximum(0, Q_fc - delta), 2),
            "horizon_days":  self.horizon,
            "r2_train":      round(self._r2, 3),
            "uncertainty_pct": round(unc, 1),
            "model":         f"LSTM({self._n_feat}_features, hidden={self.hidden_size}, PyTorch)",
            "features_used": self.features,
            "n_features":    self._n_feat,
        }

    def __repr__(self):
        if not self._fitted: return f"LSTMForecast(not fitted)"
        if getattr(self,"_fallback",False): return "LSTMForecast→LinearForecast(fallback)"
        return (f"LSTMForecast(features={self.features}, "
                f"hidden={self.hidden_size}, R²={self._r2:.3f})")
