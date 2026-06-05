# bridge_agency.py — Agency-Agents HTTP 橋接（URL / 逾時由 .env 提供）

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


def _ensure_env() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    agents = os.path.normpath(os.path.join(here, "..", "02_Agents_Core"))
    if agents not in sys.path:
        sys.path.insert(0, agents)
    try:
        from gov_paths import get_secret, get_tang_gov_root

        get_tang_gov_root()
    except Exception:
        pass


def _default_base() -> str:
    _ensure_env()
    try:
        from gov_paths import get_secret

        return get_secret("AGENCY_BASE_URL", "http://127.0.0.1:8001") or "http://127.0.0.1:8001"
    except Exception:
        return os.environ.get("AGENCY_BASE_URL", "http://127.0.0.1:8001")


def _default_timeout() -> float:
    _ensure_env()
    try:
        from gov_paths import get_secret

        raw = get_secret("AGENCY_HTTP_TIMEOUT", "120")
        return float(raw or 120)
    except Exception:
        return float(os.environ.get("AGENCY_HTTP_TIMEOUT", "120"))


def run_api_task(payload: Dict[str, Any], *, base_url: Optional[str] = None) -> Dict[str, Any]:
    base = (base_url or _default_base()).rstrip("/")
    url = f"{base}/chat"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_default_timeout()) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {"ok": True, "empty": True}
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = str(e)
        return {"ok": False, "error": f"HTTP {e.code}", "detail": detail}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def health_check(base_url: Optional[str] = None) -> Dict[str, Any]:
    base = (base_url or _default_base()).rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/", timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
