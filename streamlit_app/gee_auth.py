"""
gee_auth.py — HSAE v6.01  GEE Authentication via Service Account
=================================================================
Supports three authentication modes:
  1. Streamlit Cloud  — reads from st.secrets["gee"]
  2. Local dev        — reads from .streamlit/secrets.toml
  3. Personal creds   — falls back to earthengine authenticate

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
import json
import os
import tempfile

GEE_PROJECT = "zinc-arc-484714-j8"
_initialized = False


def init_gee() -> bool:
    """
    Initialize GEE with Service Account (Streamlit) or personal creds (local).
    Returns True if successful.
    """
    global _initialized
    if _initialized:
        return True

    import ee

    # ── Mode 1: Streamlit Secrets (production) ────────────────────────────────
    try:
        import streamlit as st
        if "gee" in st.secrets:
            gee_cfg = st.secrets["gee"]
            credentials_dict = {
                "type":                        gee_cfg.get("type", "service_account"),
                "project_id":                  gee_cfg.get("project_id", GEE_PROJECT),
                "private_key_id":              gee_cfg.get("private_key_id", ""),
                "private_key":                 gee_cfg["private_key"],
                "client_email":                gee_cfg["client_email"],
                "client_id":                   gee_cfg.get("client_id", ""),
                "auth_uri":                    "https://accounts.google.com/o/oauth2/auth",
                "token_uri":                   "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url":        gee_cfg.get("client_x509_cert_url", ""),
            }

            # Write to temp file for ee.ServiceAccountCredentials
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                             delete=False) as f:
                json.dump(credentials_dict, f)
                tmp_path = f.name

            credentials = ee.ServiceAccountCredentials(
                email=credentials_dict["client_email"],
                key_file=tmp_path
            )
            ee.Initialize(credentials=credentials, project=GEE_PROJECT)
            os.unlink(tmp_path)   # delete temp file immediately

            _initialized = True
            print(f"[GEE] ✅ Initialized via Streamlit Secrets")
            print(f"[GEE] Service account: {credentials_dict['client_email']}")
            return True

    except Exception as exc:
        print(f"[GEE] Streamlit Secrets failed: {exc}")

    # ── Mode 2: Local secrets.toml ────────────────────────────────────────────
    try:
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            import tomllib
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
            if "gee" in secrets:
                gee_cfg = secrets["gee"]
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                                 delete=False) as f:
                    json.dump({
                        "type":        gee_cfg.get("type", "service_account"),
                        "project_id":  gee_cfg.get("project_id", GEE_PROJECT),
                        "private_key": gee_cfg["private_key"],
                        "client_email":gee_cfg["client_email"],
                        "auth_uri":    "https://accounts.google.com/o/oauth2/auth",
                        "token_uri":   "https://oauth2.googleapis.com/token",
                    }, f)
                    tmp_path = f.name

                credentials = ee.ServiceAccountCredentials(
                    email=gee_cfg["client_email"],
                    key_file=tmp_path
                )
                ee.Initialize(credentials=credentials, project=GEE_PROJECT)
                os.unlink(tmp_path)
                _initialized = True
                print(f"[GEE] ✅ Initialized via local secrets.toml")
                return True
    except Exception as exc:
        print(f"[GEE] Local secrets failed: {exc}")

    # ── Mode 3: Personal credentials fallback (local dev) ─────────────────────
    try:
        ee.Initialize(project=GEE_PROJECT)
        _initialized = True
        print(f"[GEE] ✅ Initialized via personal credentials")
        return True
    except Exception as exc:
        print(f"[GEE] Personal credentials failed: {exc}")

    print("[GEE] ❌ All authentication methods failed")
    return False


def get_ee():
    """Get initialized ee module. Call this instead of importing ee directly."""
    import ee
    if not _initialized:
        init_gee()
    return ee


def test_connection() -> dict:
    """Test GEE connection and return status."""
    try:
        ee = get_ee()
        val = ee.Number(42).getInfo()
        region = ee.Geometry.Rectangle([34.0, 10.0, 38.0, 13.0])
        gpm = (ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
               .filterDate("2023-06-01", "2023-06-02")
               .first()
               .select("precipitation")
               .reduceRegion(ee.Reducer.mean(), region, 11132)
               .getInfo())
        return {
            "status":    "connected",
            "project":   GEE_PROJECT,
            "test_val":  val,
            "gpm_test":  round(gpm.get("precipitation", 0) * 24, 3),
            "auth_mode": "service_account",
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


if __name__ == "__main__":
    print("=" * 50)
    print("HSAE v6.01 — GEE Auth Test")
    print("=" * 50)
    result = test_connection()
    if result["status"] == "connected":
        print(f"✅ Connected to GEE")
        print(f"   Project:  {result['project']}")
        print(f"   GPM test: {result['gpm_test']} mm/day")
    else:
        print(f"❌ Failed: {result.get('error')}")
