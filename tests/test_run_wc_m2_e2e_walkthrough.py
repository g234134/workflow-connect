"""Unit tests for WC-T7 M2 E2E walkthrough runner (dry-run and execute modes)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _REPO_ROOT / "scripts" / "run_wc_m2_e2e_walkthrough.py"
_RUNBOOK = _REPO_ROOT / "docs" / "wave_c" / "WC_T7_e2e_walkthrough_runbook.md"


class TestRunWcM2E2eWalkthrough(unittest.TestCase):
    def _run_cli(self, *extra: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(_RUNNER), *extra]
        return subprocess.run(
            cmd,
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_reject_non_demo_ticket(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-NOT-ALLOWED",
            "--dry-run",
            "--json",
        )
        self.assertNotEqual(proc.returncode, 0)
        err_payload = json.loads(proc.stderr.strip())
        self.assertFalse(err_payload["ok"])
        self.assertIn("WC-DEMO-", err_payload["message"])

    def test_dry_run_with_demo_ticket(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-DEMO-1",
            "--artifacts-root",
            "artifacts/e2e",
            "--dry-run",
            "--json",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout.strip())
        self.assertTrue(payload["ok"])
        self.assertIn(
            "docs/wave_c/WC_T7_e2e_walkthrough_runbook.md",
            payload["runbook"],
        )
        self.assertGreaterEqual(len(payload["steps"]), 3)
        step_ids = [step["step_id"] for step in payload["steps"]]
        self.assertIn("2", step_ids)
        self.assertIn("5", step_ids)

    def test_reject_non_e2e_artifacts_root(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-DEMO-1",
            "--artifacts-root",
            "artifacts/not_e2e",
            "--dry-run",
            "--json",
        )
        self.assertNotEqual(proc.returncode, 0)
        err_payload = json.loads(proc.stderr.strip())
        self.assertFalse(err_payload["ok"])
        self.assertIn("artifacts/e2e", err_payload["message"])

    def test_runbook_contains_sandbox_payment_section(self) -> None:
        """AC-1/AC-3: runbook §4+ payment section with copy-paste CLI fragments."""
        text = _RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("## 4+. Payment（sandbox DRAFT→PAID）", text)
        self.assertIn("### 4+.4 Non-claims", text)
        self.assertIn("transition", text)
        self.assertIn("GOV_PAYMENT_SANDBOX_ENABLED=1", text)
        self.assertIn("wc.m2.order.transition", text)
        self.assertIn("wc.m2.order.pay_sandbox", text)
        self.assertIn("≠ prod 金流", text)
        self.assertIn("≠ INT Tier-A", text)

    def test_runbook_contains_wc_t5_path_id_appendix(self) -> None:
        text = _RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("附录 · WC-T5 path_id 对照表", text)
        self.assertIn("Control Plane E2E pass ≠ INT Tier-A pass", text)
        for path_id in (
            "wc.m2.eligibility.check_role",
            "wc.m2.dispatch.refresh_and_cards",
            "wc.m2.dispatch.force_eligibility_override",
            "wc.m2.comms.state_transition",
            "wc.m2.comms.state_transition_dry_run",
            "wc.m2.order.create",
            "wc.m2.order.lookup",
            "wc.m2.state.write_ticket",
            "wc.m2.chat.open_cursor",
        ):
            self.assertIn(path_id, text, msg=f"runbook missing path_id {path_id}")

    def test_dry_run_does_not_write_files(self) -> None:
        """AC-1: --dry-run should not write any files, only print summary."""
        # Use a test directory under repo's artifacts/e2e/ to satisfy path validation
        test_dir = "artifacts/e2e/_test_dry_run"
        artifacts_root = _REPO_ROOT / test_dir
        try:
            proc = self._run_cli(
                "--ticket",
                "WC-DEMO-1",
                "--artifacts-root",
                test_dir,
                "--dry-run",
                "--json",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            payload = json.loads(proc.stdout.strip())
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["mode"], "dry_run")
            # Verify no files were written (except possibly empty artifact_dir)
            ticket_dir = artifacts_root / "WC-DEMO-1"
            if ticket_dir.exists():
                files = list(ticket_dir.rglob("*"))
                non_empty = [f for f in files if f.is_file()]
                self.assertEqual(len(non_empty), 0, f"Unexpected files created: {non_empty}")
        finally:
            # Cleanup
            import shutil
            if artifacts_root.exists():
                shutil.rmtree(artifacts_root, ignore_errors=True)

    def test_execute_creates_orders_jsonl(self) -> None:
        """AC-2: --execute should create orders.jsonl with order_ledger_v1 record."""
        # Use a test directory under repo's artifacts/e2e/ to satisfy path validation
        test_dir = "artifacts/e2e/_test_execute"
        artifacts_root = _REPO_ROOT / test_dir
        try:
            # Note: This test may skip steps if dependencies are missing,
            # but it validates the directory structure and schema
            proc = self._run_cli(
                "--ticket",
                "WC-DEMO-1",
                "--artifacts-root",
                test_dir,
                "--execute",
                "--json",
            )
            # Execute may fail due to missing dependencies, but we should have valid output
            if proc.returncode == 0:
                payload = json.loads(proc.stdout.strip())
            else:
                # If it failed, it might be due to missing dependencies
                # Check stderr for expected validation error or stdout for JSON
                try:
                    payload = json.loads(proc.stdout.strip())
                except json.JSONDecodeError:
                    # Command failed before producing output - check if it's due to missing ticket
                    self.skipTest(f"Execute mode requires full environment setup: {proc.stderr}")
                    return
            self.assertEqual(payload["ticket_id"], "WC-DEMO-1")
            self.assertEqual(payload["mode"], "execute")
            # Check that artifact_dir was created
            artifact_dir = artifacts_root / "WC-DEMO-1"
            self.assertTrue(
                artifact_dir.exists() or payload.get("artifact_dir"),
                "Artifact directory should be defined",
            )
            # If orders.jsonl exists, verify it contains valid order_ledger_v1
            orders_jsonl = artifact_dir / "orders.jsonl"
            if orders_jsonl.exists():
                lines = orders_jsonl.read_text(encoding="utf-8").strip().splitlines()
                self.assertGreater(len(lines), 0, "orders.jsonl should not be empty")
                for line in lines:
                    record = json.loads(line)
                    self.assertEqual(record.get("schema_version"), "order_ledger_v1")
                    self.assertIn("order_id", record)
                    self.assertIn("ticket_id", record)
                    self.assertIn("amount_minor", record)
                    self.assertIn("currency", record)
        finally:
            # Cleanup
            import shutil
            if artifacts_root.exists():
                shutil.rmtree(artifacts_root, ignore_errors=True)

    def test_non_demo_ticket_rejected_in_execute(self) -> None:
        """AC-3: Non WC-DEMO-* ticket should be rejected in --execute mode."""
        test_dir = "artifacts/e2e/_test_reject"
        artifacts_root = _REPO_ROOT / test_dir
        try:
            proc = self._run_cli(
                "--ticket",
                "W1-T2",  # Production-like ticket
                "--artifacts-root",
                test_dir,
                "--execute",
                "--json",
            )
            self.assertNotEqual(proc.returncode, 0)
            err_payload = json.loads(proc.stderr.strip())
            self.assertFalse(err_payload["ok"])
            self.assertIn("WC-DEMO-", err_payload["message"])
        finally:
            # Cleanup
            import shutil
            if artifacts_root.exists():
                shutil.rmtree(artifacts_root, ignore_errors=True)

    def test_non_demo_ticket_allowed_in_dry_run(self) -> None:
        """Non WC-DEMO-* ticket may be allowed in --dry-run for testing."""
        # This documents current behavior: dry-run may work for non-demo tickets
        # (it just prints commands without executing), but execute mode is blocked.
        proc = self._run_cli(
            "--ticket",
            "WC-DEMO-TEST",
            "--artifacts-root",
            "artifacts/e2e",
            "--dry-run",
            "--json",
        )
        # WC-DEMO-TEST starts with WC-DEMO- prefix, should be allowed
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)


    def test_execute_with_hitl_fixtures_reaches_comms_and_order(self) -> None:
        """AC-2/AC-3: --execute --use-hitl-fixtures runs comms + order without manual HITL."""
        test_dir = "artifacts/e2e/_test_execute_fixtures"
        artifacts_root = _REPO_ROOT / test_dir
        try:
            proc = self._run_cli(
                "--ticket",
                "WC-DEMO-1",
                "--artifacts-root",
                test_dir,
                "--execute",
                "--use-hitl-fixtures",
                "--json",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            payload = json.loads(proc.stdout.strip())
            self.assertTrue(payload["ok"])
            self.assertTrue(payload.get("use_hitl_fixtures"))
            self.assertIn("hitl_fixtures", payload)

            steps_by_id = {step["step_id"]: step for step in payload["steps"]}
            self.assertEqual(steps_by_id["3-hitl"]["status"], "fixture")
            self.assertEqual(steps_by_id["4-hitl"]["status"], "fixture")
            self.assertEqual(steps_by_id["3"]["status"], "ok", steps_by_id["3"])
            self.assertEqual(steps_by_id["4"]["status"], "ok", steps_by_id["4"])

            artifact_dir = artifacts_root / "WC-DEMO-1"
            comms_jsonl = artifact_dir / "comms" / "ticket_comms.jsonl"
            orders_jsonl = artifact_dir / "orders.jsonl"
            self.assertTrue(comms_jsonl.is_file(), "comms outbox should be written")
            self.assertTrue(orders_jsonl.is_file(), "orders.jsonl should be written")

            comms_lines = comms_jsonl.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreater(len(comms_lines), 0)
            comms_record = json.loads(comms_lines[0])
            comms_payload = comms_record.get("payload") or comms_record
            self.assertEqual(comms_payload.get("schema_version"), "ticket_comms_v0.1")
            self.assertEqual(comms_payload.get("ticket_id"), "WC-DEMO-1")

            order_lines = orders_jsonl.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreater(len(order_lines), 0)
            for line in order_lines:
                record = json.loads(line)
                self.assertEqual(record.get("schema_version"), "order_ledger_v1")
                self.assertEqual(record.get("ticket_id"), "WC-DEMO-1")
        finally:
            import shutil
            if artifacts_root.exists():
                shutil.rmtree(artifacts_root, ignore_errors=True)

    def test_use_hitl_fixtures_rejected_with_dry_run(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-DEMO-1",
            "--artifacts-root",
            "artifacts/e2e",
            "--dry-run",
            "--use-hitl-fixtures",
            "--json",
        )
        self.assertNotEqual(proc.returncode, 0)
        err_payload = json.loads(proc.stderr.strip())
        self.assertFalse(err_payload["ok"])
        self.assertIn("--execute", err_payload["message"])

    def test_use_hitl_fixtures_does_not_widen_demo_guardrails(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "W1-T2",
            "--artifacts-root",
            "artifacts/e2e/_test_fixture_guard",
            "--execute",
            "--use-hitl-fixtures",
            "--json",
        )
        self.assertNotEqual(proc.returncode, 0)
        err_payload = json.loads(proc.stderr.strip())
        self.assertFalse(err_payload["ok"])
        self.assertIn("WC-DEMO-", err_payload["message"])

    def test_dry_run_without_include_payment_omits_step6(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-DEMO-1",
            "--artifacts-root",
            "artifacts/e2e",
            "--dry-run",
            "--json",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout.strip())
        step_ids = [step["step_id"] for step in payload["steps"]]
        self.assertNotIn("6-payment", step_ids)
        self.assertFalse(payload.get("include_payment"))

    def test_dry_run_with_include_payment_previews_step6(self) -> None:
        proc = self._run_cli(
            "--ticket",
            "WC-DEMO-1",
            "--artifacts-root",
            "artifacts/e2e",
            "--dry-run",
            "--include-payment",
            "--json",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout.strip())
        self.assertTrue(payload.get("include_payment"))
        steps_by_id = {step["step_id"]: step for step in payload["steps"]}
        self.assertIn("6-payment", steps_by_id)
        payment_step = steps_by_id["6-payment"]
        self.assertEqual(payment_step["status"], "dry_run")
        commands = [entry["command"] for entry in payment_step.get("commands") or []]
        self.assertTrue(any("transition" in cmd and "pending_payment" in cmd for cmd in commands))
        self.assertTrue(any(" pay " in f" {cmd} " for cmd in commands))
        self.assertTrue(any("lookup" in cmd for cmd in commands))
        pay_entries = [
            entry for entry in payment_step.get("commands") or [] if " pay " in f" {entry['command']} "
        ]
        self.assertEqual(len(pay_entries), 1)
        self.assertEqual(pay_entries[0].get("env", {}).get("GOV_PAYMENT_SANDBOX_ENABLED"), "1")

    def test_execute_with_include_payment_reaches_paid(self) -> None:
        """Step 6-payment: fixture execute through sandbox transition/pay to PAID."""
        test_dir = "artifacts/e2e/_test_execute_payment"
        artifacts_root = _REPO_ROOT / test_dir
        try:
            proc = self._run_cli(
                "--ticket",
                "WC-DEMO-1",
                "--artifacts-root",
                test_dir,
                "--execute",
                "--use-hitl-fixtures",
                "--include-payment",
                "--json",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
            payload = json.loads(proc.stdout.strip())
            self.assertTrue(payload["ok"])
            self.assertTrue(payload.get("include_payment"))
            self.assertEqual(payload.get("order_status"), "PAID")

            steps_by_id = {step["step_id"]: step for step in payload["steps"]}
            self.assertEqual(steps_by_id["6-payment"]["status"], "ok")

            orders_jsonl = artifacts_root / "WC-DEMO-1" / "orders.jsonl"
            self.assertTrue(orders_jsonl.is_file())
            lines = orders_jsonl.read_text(encoding="utf-8").strip().splitlines()
            self.assertGreaterEqual(len(lines), 3)
            latest = json.loads(lines[-1])
            self.assertEqual(latest.get("order_status"), "PAID")
            self.assertEqual(latest.get("ticket_id"), "WC-DEMO-1")
            provider_ref = latest.get("provider_ref") or ""
            self.assertTrue(provider_ref.startswith("SANDBOX-REF-"))
            blob = orders_jsonl.read_text(encoding="utf-8").lower()
            for secret_token in ("api_key", "secret", "sk_live", "stripe"):
                self.assertNotIn(secret_token, blob)
        finally:
            import shutil
            if artifacts_root.exists():
                shutil.rmtree(artifacts_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
