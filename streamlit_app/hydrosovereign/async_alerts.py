"""
async_alerts.py — HSAE v6.2.0 Asynchronous Alert Monitor
==========================================================
Asyncio-based concurrent monitoring of multiple basins simultaneously.
Addresses Gemini review: "Implement asyncio for alerts to monitor
hundreds of basins simultaneously without performance bottlenecks."

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
import asyncio
import logging
from typing import List, Optional, Callable

from .indices_legacy import compute_atdi, compute_hifd
from .alerts  import check_atdi_alert, AlertLevel

logger = logging.getLogger(__name__)


class AsyncAlertMonitor:
    """
    Concurrent basin alert monitor using asyncio.

    Monitors multiple basins simultaneously without blocking.
    Suitable for real-time dashboards and Telegram bot integration.

    Parameters
    ----------
    callback : callable, optional
        Async function called when alert fires: callback(basin_name, result).
    min_level : AlertLevel
        Minimum alert level to fire callback. Default = ALERT.
    poll_interval : float
        Seconds between polls. Default = 3600 (1 hour).

    Examples
    --------
    >>> async def my_callback(name, result):
    ...     print(f"ALERT: {name} — {result['alert_level']}")
    >>>
    >>> monitor = AsyncAlertMonitor(callback=my_callback, min_level=AlertLevel.WARNING)
    >>> basins = [{"name":"Blue Nile","runoff_c":0.38,"cap_bcm":74,"n_countries":3,"dispute_level":4}]
    >>> asyncio.run(monitor.run_once(basins))
    """

    def __init__(
        self,
        callback: Optional[Callable] = None,
        min_level: AlertLevel = AlertLevel.ALERT,
        poll_interval: float = 3600.0,
    ):
        self.callback      = callback
        self.min_level     = min_level
        self.poll_interval = poll_interval
        self._results      = {}
        self._running      = False

    async def _check_basin(self, basin: dict) -> dict:
        """Check a single basin asynchronously."""
        await asyncio.sleep(0)  # yield to event loop
        name = basin.get("name", "unknown")
        try:
            rc   = float(basin.get("runoff_c", 0.3))
            cap  = float(basin.get("cap_bcm", basin.get("cap", 10)))
            nc   = int(basin.get("n_countries", 2))
            disp = int(basin.get("dispute_level", 0))
            atdi = compute_atdi(rc, cap, nc, disp)
            hifd = compute_hifd(rc, cap, nc, disp)
            level = check_atdi_alert(atdi)
            result = {
                "basin":       name,
                "atdi":        atdi,
                "hifd":        hifd,
                "alert_level": level.value,
                "triggered":   self._level_gte(level, self.min_level),
            }
            if result["triggered"] and self.callback:
                await self.callback(name, result)
            logger.debug("Basin %s: ATDI=%.1f level=%s", name, atdi, level.value)
            return result
        except Exception as e:
            logger.error("Error checking basin %s: %s", name, e)
            return {"basin": name, "error": str(e)}

    def _level_gte(self, a: AlertLevel, b: AlertLevel) -> bool:
        order = [AlertLevel.INFO, AlertLevel.ALERT, AlertLevel.WARNING, AlertLevel.CRITICAL]
        return order.index(a) >= order.index(b)

    async def run_once(self, basins: list) -> list:
        """
        Check all basins concurrently (single pass).

        Parameters
        ----------
        basins : list of dict
            Basin dicts with: name, runoff_c, cap_bcm, n_countries, dispute_level.

        Returns
        -------
        list of result dicts, one per basin.
        """
        tasks   = [self._check_basin(b) for b in basins]
        results = await asyncio.gather(*tasks)
        self._results = {r["basin"]: r for r in results if "error" not in r}
        triggered = [r for r in results if r.get("triggered")]
        logger.info("AsyncAlertMonitor: %d/%d basins triggered", len(triggered), len(basins))
        return list(results)

    async def run_continuous(self, basins: list, max_polls: int = 0):
        """
        Continuously poll basins (production use).

        Parameters
        ----------
        basins : list of dict
        max_polls : int
            Maximum number of poll cycles. 0 = unlimited.
        """
        self._running = True
        polls = 0
        logger.info("AsyncAlertMonitor started: %d basins, interval=%.0fs", len(basins), self.poll_interval)
        while self._running:
            await self.run_once(basins)
            polls += 1
            if max_polls and polls >= max_polls:
                break
            await asyncio.sleep(self.poll_interval)
        logger.info("AsyncAlertMonitor stopped after %d polls", polls)

    def stop(self):
        """Stop continuous monitoring."""
        self._running = False

    @property
    def last_results(self) -> dict:
        """Most recent results per basin."""
        return self._results.copy()

    def __repr__(self):
        return (f"AsyncAlertMonitor(min_level={self.min_level.value}, "
                f"interval={self.poll_interval}s, n_cached={len(self._results)})")
