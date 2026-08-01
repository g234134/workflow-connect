"""P3 regression: GroqQuotaTracker.record_success must persist quota state."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "04_Workflows"


def _load_tang_http():
    spec = importlib.util.spec_from_file_location("_tang_http", WF / "_tang_http.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(WF))
    spec.loader.exec_module(mod)
    return mod


def test_record_success_persists_rpd_counter(tmp_path, monkeypatch):
    mod = _load_tang_http()
    state_path = tmp_path / "groq_quota_state.json"
    monkeypatch.setattr(mod.GroqQuotaTracker, "__init__", lambda self, root: None)
    tracker = mod.GroqQuotaTracker.__new__(mod.GroqQuotaTracker)
    tracker._root = str(tmp_path)
    tracker._lock = mod.threading.Lock()
    tracker._registry = {"models": {"llama-3.1-8b-instant": {"RPM": 30, "RPD": 100, "TPM": 6000}}}
    tracker._alias_map = {"llama-3.1-8b-instant": "llama-3.1-8b-instant"}
    tracker._rpm_events = {}
    tracker._state_path = state_path
    tracker._state = {"utc_date": tracker._utc_day(), "requests_per_model": {}}

    tracker.record_success(
        "llama-3.1-8b-instant",
        {"usage": {"total_tokens": 42}, "choices": [{"message": {"content": "ok"}}]},
    )

    assert state_path.is_file()
    saved = json.loads(state_path.read_text(encoding="utf-8"))
    assert saved["requests_per_model"]["llama-3.1-8b-instant"] == 1
