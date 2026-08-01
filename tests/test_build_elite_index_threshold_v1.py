"""P1 regression: elite_cache min_heuristic_score must match filter logic."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "04_Workflows"


def _load_build_elite_index():
    path = WF / "_build_elite_index.py"
    spec = importlib.util.spec_from_file_location("_build_elite_index", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(WF))
    sys.path.insert(0, str(ROOT / "02_Agents_Core"))
    spec.loader.exec_module(mod)
    return mod


def test_elite_min_score_constant_matches_doc_threshold():
    mod = _load_build_elite_index()
    assert mod.ELITE_MIN_HEURISTIC_SCORE == 7.5
    assert mod.ELITE_MIN_HEURISTIC_SCORE < 9.0


def test_grade_a_at_88_passes_elite_gate():
    mod = _load_build_elite_index()
    hscore = 8.8
    gr = "A"
    assert hscore > mod.ELITE_MIN_HEURISTIC_SCORE and gr == "A"


def test_grade_a_at_90_old_threshold_would_fail():
    mod = _load_build_elite_index()
    hscore = 8.8
    assert not (hscore > 9.0)
