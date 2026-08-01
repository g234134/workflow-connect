"""P2 regression: sync_wave propagates local_similarity_pct into scout pipeline."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "04_Workflows"


def _load_sync_wave():
    spec = importlib.util.spec_from_file_location("_sync_wave", WF / "_sync_wave_to_scout_pipeline.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(WF))
    sys.path.insert(0, str(ROOT / "02_Agents_Core"))
    spec.loader.exec_module(mod)
    return mod


def test_top_matches_include_local_similarity_pct(monkeypatch, tmp_path):
    mod = _load_sync_wave()
    rep_dir = tmp_path / "reports"
    rep_dir.mkdir()
    report = {
        "run_id": "test-run",
        "pool_size": 100,
        "sampled": 10,
        "rows": [
            {
                "grade": "A",
                "final_score": 9.1,
                "local_score": 8.2,
                "local_similarity_pct": 77.5,
                "source_path": "/x/a.py",
                "name": "a.py",
            }
        ],
    }
    rep_path = rep_dir / "asset_value_eval_test.json"
    rep_path.write_text(json.dumps(report), encoding="utf-8")

    monkeypatch.setattr(mod, "get_tang_gov_root", lambda: str(tmp_path))
    monkeypatch.setattr(
        mod,
        "resolve_agent_output_path",
        lambda root, *parts: str(Path(root).joinpath(*parts)),
    )
    monkeypatch.setattr(mod, "_latest_eval_report", lambda root: str(rep_path))

    assert mod.main() == 0
    out_path = tmp_path / "06_Exports_Output" / "reports" / "scout_last_pipeline.json"
    out = json.loads(out_path.read_text(encoding="utf-8"))
    top = out["match_report"]["top_matches"][0]
    assert top["local_similarity_pct"] == 77.5
