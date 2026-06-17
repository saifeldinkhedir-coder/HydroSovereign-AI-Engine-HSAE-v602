"""
alerts.py — HSAE v6.01 Alert System
=====================================
4-level alert system for ATDI/HIFD thresholds.

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""

from __future__ import annotations
from enum import Enum


class AlertLevel(Enum):
    INFO     = "INFO"
    ALERT    = "ALERT"
    WARNING  = "WARNING"
    CRITICAL = "CRITICAL"


def check_atdi_alert(atdi: float) -> AlertLevel:
    """
    Return alert level based on ATDI.

    Thresholds:
    - CRITICAL : ATDI >= 70%
    - WARNING  : ATDI >= 55%
    - ALERT    : ATDI >= 40%
    - INFO     : ATDI < 40%
    """
    if atdi >= 70: return AlertLevel.CRITICAL
    if atdi >= 55: return AlertLevel.WARNING
    if atdi >= 40: return AlertLevel.ALERT
    return AlertLevel.INFO


def check_hifd_alert(hifd: float) -> AlertLevel:
    """
    Return alert level based on HIFD.

    Thresholds:
    - CRITICAL : HIFD >= 60%
    - WARNING  : HIFD >= 40%
    - ALERT    : HIFD >= 25%
    - INFO     : HIFD < 25%
    """
    if hifd >= 60: return AlertLevel.CRITICAL
    if hifd >= 40: return AlertLevel.WARNING
    if hifd >= 25: return AlertLevel.ALERT
    return AlertLevel.INFO


def format_alert_message(basin_name: str, atdi: float,
                          hifd: float, level: AlertLevel) -> str:
    """Format alert message for Telegram or logging."""
    emoji = {"CRITICAL":"🔴","WARNING":"🟠","ALERT":"🟡","INFO":"🟢"}[level.value]
    return (
        f"{emoji} HSAE Alert — {level.value}\n"
        f"Basin: {basin_name}\n"
        f"ATDI: {atdi:.1f}% | HIFD: {hifd:.1f}%\n"
        f"UNWC Arts: {', '.join(['Art.5','Art.9'] + (['Art.7'] if atdi>=40 else []) + (['Art.20'] if hifd>=25 else []))}"
    )
