#!/usr/bin/env python3
"""Offline smoke test for B Hooks v0.1."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
TEST_TICKET = "TEST-SUB-001"
TEST_CONV = "smoke-conv-001"
TEST_FILE = ".cursor/hooks/smoke_test_scratch.txt"
TEST_FILE_ABS = (REPO_ROOT / TEST_FILE).resolve()


def run_hook(script_name: str, payload: dict) -> tuple[int, str, str]:
    script = HOOKS_DIR / script_name
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        timeout=10,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def assert_true(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    TEST_FILE_ABS.parent.mkdir(parents=True, exist_ok=True)
    TEST_FILE_ABS.write_text("smoke scratch\n", encoding="utf-8")

    subagent_dir = REPO_ROOT / ".cursor/hooks_state/subagent_out" / TEST_TICKET
    subagent_dir.mkdir(parents=True, exist_ok=True)
    (subagent_dir / "implementation.json").write_text(
        json.dumps(
            {
                "ok": True,
                "ticket_id": TEST_TICKET,
                "files_changed": [TEST_FILE],
                "commands_run": [{"command": "echo smoke", "exit_ok": True, "summary": "ok"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (subagent_dir / "checker.json").write_text(
        json.dumps(
            {
                "ok": True,
                "ticket_id": TEST_TICKET,
                "accepted": True,
                "verdict": "accepted",
                "evidence": [{"command": "echo smoke", "exit_ok": True}],
                "battle_report_json_draft": {"results": "checker draft merge"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    workspace_roots = [str(REPO_ROOT)]

    steps = [
        (
            "beforeSubmitPrompt",
            "capture_session_context.py",
            {
                "prompt": f"ticket_id={TEST_TICKET} smoke test",
                "conversation_id": TEST_CONV,
                "hook_event_name": "beforeSubmitPrompt",
                "workspace_roots": workspace_roots,
            },
            {"continue": True},
        ),
        (
            "afterFileEdit",
            "update_scope_ledger.py",
            {
                "file_path": str(TEST_FILE_ABS),
                "edits": [{"old_string": "a", "new_string": "b"}],
                "conversation_id": TEST_CONV,
                "generation_id": "gen-smoke-001",
                "hook_event_name": "afterFileEdit",
                "workspace_roots": workspace_roots,
            },
            None,
        ),
        (
            "stop",
            "prepare_battle_report.py",
            {
                "status": "completed",
                "conversation_id": TEST_CONV,
                "loop_count": 0,
                "hook_event_name": "stop",
                "workspace_roots": workspace_roots,
            },
            None,
        ),
    ]

    print("B Hooks v0.1 smoke test")
    print("=" * 40)

    for name, script, payload, expected_stdout in steps:
        code, out, err = run_hook(script, payload)
        print(f"[{name}] exit={code}")
        if err:
            print(f"  stderr: {err}")
        assert_true(code == 0, f"{name}: expected exit 0, got {code}", failures)
        if expected_stdout is not None:
            try:
                parsed = json.loads(out) if out else {}
            except json.JSONDecodeError:
                parsed = {}
            assert_true(
                parsed == expected_stdout,
                f"{name}: stdout mismatch expected {expected_stdout}, got {parsed}",
                failures,
            )

    ledger_path = REPO_ROOT / ".cursor/scope_ledger.json"
    latest_draft_path = REPO_ROOT / ".cursor/hooks_state/latest_battle_report_draft.json"

    assert_true(ledger_path.is_file(), "scope_ledger.json missing", failures)
    assert_true(latest_draft_path.is_file(), "latest_battle_report_draft.json missing", failures)

    if ledger_path.is_file():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        session = (ledger.get("sessions") or {}).get(TEST_CONV) or {}
        paths = [e.get("path") for e in session.get("files_changed") or []]
        assert_true(TEST_FILE in paths, f"scope ledger missing {TEST_FILE}", failures)
        assert_true(session.get("ticket_id") == TEST_TICKET, "scope ledger ticket_id mismatch", failures)

    if latest_draft_path.is_file():
        draft = json.loads(latest_draft_path.read_text(encoding="utf-8"))
        required = ["ticket_id", "role", "executed", "results", "blockers", "next_steps"]
        missing = [k for k in required if not draft.get(k)]
        assert_true(not missing, f"battle draft missing fields: {missing}", failures)
        assert_true(draft.get("ticket_id") == TEST_TICKET, "battle draft ticket_id mismatch", failures)
        assert_true(draft.get("status") == "draft", "battle draft status must be draft", failures)

    print("=" * 40)
    if failures:
        print("FAIL")
        for item in failures:
            print(f" - {item}")
        return 1

    print("PASS")
    print(f"scope_ledger: {ledger_path.relative_to(REPO_ROOT).as_posix()}")
    print(f"latest_draft: {latest_draft_path.relative_to(REPO_ROOT).as_posix()}")
    print(
        "next: python 04_Workflows/_ops_cycle.py validate-report "
        "--json .cursor/hooks_state/latest_battle_report_draft.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
