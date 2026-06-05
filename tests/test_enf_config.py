"""Unit tests for observability.enf_config (ENF env flag wiring)."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock

from observability.enf_config import (
    AUDIT_WARN_PREFIX,
    CONFIG_LOG_PREFIX,
    ENV_GOV_ENF_BLOCKING_CANARY,
    ENV_GOV_ENF_BLOCKING_CANARY_DISABLE,
    ENV_GOV_ENF_ENABLE,
    ENV_ENF_ENABLE,
    collect_enf_audit_warnings,
    load_enf_config,
    log_enf_config,
)


class TestEnfConfigDefaults(unittest.TestCase):
    def test_unset_env_defaults_to_enabled_shadow(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            config = load_enf_config()
        self.assertTrue(config.enabled)
        self.assertFalse(config.blocking_canary)
        self.assertEqual(config.mode, "shadow-only")
        self.assertTrue(config.should_run_enf)

    def test_unset_env_config_log_line(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            config = load_enf_config()
        line = config.format_config_log_line()
        self.assertIn(CONFIG_LOG_PREFIX, line)
        self.assertIn("GOV_ENF_ENABLE=1", line)
        self.assertIn("GOV_ENF_BLOCKING_CANARY=0", line)
        self.assertIn("(shadow-only)", line)
        self.assertEqual(collect_enf_audit_warnings(config), [])

    def test_unset_env_log_has_no_audit_warning(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            config = load_enf_config()
        buf = io.StringIO()
        with redirect_stdout(buf):
            log_enf_config(config)
        output = buf.getvalue()
        self.assertNotIn(AUDIT_WARN_PREFIX, output)


class TestEnfConfigEnable(unittest.TestCase):
    def test_gov_enf_enable_off_skips(self) -> None:
        with mock.patch.dict(os.environ, {"GOV_ENF_ENABLE": "0"}, clear=True):
            config = load_enf_config()
        self.assertFalse(config.enabled)
        self.assertEqual(config.mode, "skipped")
        self.assertFalse(config.should_run_enf)
        self.assertIn("(skipped)", config.format_config_log_line())

    def test_enf_enable_legacy_alias_off(self) -> None:
        with mock.patch.dict(os.environ, {"ENF_ENABLE": "false"}, clear=True):
            config = load_enf_config()
        self.assertFalse(config.enabled)
        self.assertEqual(config.mode, "skipped")

    def test_gov_enf_enable_wins_over_legacy(self) -> None:
        env = {"GOV_ENF_ENABLE": "1", "ENF_ENABLE": "0"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = load_enf_config()
        self.assertTrue(config.enabled)

    def test_explicit_enable_shadow(self) -> None:
        env = {"GOV_ENF_ENABLE": "1", "GOV_ENF_BLOCKING_CANARY": "0"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = load_enf_config()
        self.assertTrue(config.should_run_enf)
        self.assertIn("(shadow-only)", config.format_config_log_line())


class TestEnfConfigBlockingCanaryFlag(unittest.TestCase):
    def test_blocking_canary_on_still_shadow_only_this_phase(self) -> None:
        env = {"GOV_ENF_ENABLE": "1", "GOV_ENF_BLOCKING_CANARY": "1"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = load_enf_config()
        self.assertTrue(config.blocking_canary)
        self.assertTrue(config.should_run_enf)
        self.assertEqual(config.mode, "shadow-only")
        line = config.format_config_log_line()
        self.assertIn("GOV_ENF_BLOCKING_CANARY=1", line)
        self.assertIn("(shadow-only)", line)
        self.assertEqual(collect_enf_audit_warnings(config), [])

    def test_explicit_blocking_canary_off_emits_audit_warning(self) -> None:
        env = {"GOV_ENF_ENABLE": "1", "GOV_ENF_BLOCKING_CANARY": "0"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = load_enf_config()
        warnings = collect_enf_audit_warnings(config)
        self.assertEqual(len(warnings), 1)
        self.assertIn(AUDIT_WARN_PREFIX, warnings[0])
        self.assertIn("Blocking canary is DISABLED", warnings[0])
        self.assertIn(f"{ENV_GOV_ENF_BLOCKING_CANARY}=0", warnings[0])

    def test_blocking_canary_disable_alias_emits_audit_warning(self) -> None:
        env = {"GOV_ENF_ENABLE": "1", "GOV_ENF_BLOCKING_CANARY_DISABLE": "true"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = load_enf_config()
        self.assertFalse(config.blocking_canary)
        warnings = collect_enf_audit_warnings(config)
        self.assertEqual(len(warnings), 1)
        self.assertIn(f"{ENV_GOV_ENF_BLOCKING_CANARY_DISABLE}=true", warnings[0])


class TestEnfConfigAuditWarnings(unittest.TestCase):
    def test_gov_enf_enable_off_emits_audit_warning(self) -> None:
        with mock.patch.dict(os.environ, {"GOV_ENF_ENABLE": "0"}, clear=True):
            config = load_enf_config()
        warnings = collect_enf_audit_warnings(config)
        self.assertEqual(len(warnings), 1)
        self.assertIn(f"{ENV_GOV_ENF_ENABLE}=0", warnings[0])

    def test_enf_enable_legacy_off_emits_audit_warning(self) -> None:
        with mock.patch.dict(os.environ, {"ENF_ENABLE": "false"}, clear=True):
            config = load_enf_config()
        warnings = collect_enf_audit_warnings(config)
        self.assertEqual(len(warnings), 1)
        self.assertIn(f"{ENV_ENF_ENABLE}=false", warnings[0])

    def test_log_enf_config_prints_audit_warning_when_disabled(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"GOV_ENF_BLOCKING_CANARY": "0"},
            clear=True,
        ):
            config = load_enf_config()
        buf = io.StringIO()
        with redirect_stdout(buf):
            log_enf_config(config)
        output = buf.getvalue()
        self.assertIn(AUDIT_WARN_PREFIX, output)
        self.assertIn("Blocking canary is DISABLED", output)


class TestEnfConfigLog(unittest.TestCase):
    def test_log_enf_config_prints_to_stdout(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            config = load_enf_config()
        buf = io.StringIO()
        with redirect_stdout(buf):
            log_enf_config(config)
        self.assertIn("[ENF] config:", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
