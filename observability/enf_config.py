"""
ENF runtime flags for eval / CI pipeline (Phase A wiring only).

Reads GOV_ENF_* env before ENF wrapper or eval_ci_check. Controls whether ENF
runs and in which mode; does not change eval_gate pass/fail or blocking behavior.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final, Literal, Mapping

ENV_GOV_ENF_ENABLE: Final[str] = "GOV_ENF_ENABLE"
ENV_ENF_ENABLE: Final[str] = "ENF_ENABLE"
ENV_GOV_ENF_BLOCKING_CANARY: Final[str] = "GOV_ENF_BLOCKING_CANARY"
ENV_GOV_ENF_BLOCKING_CANARY_DISABLE: Final[str] = "GOV_ENF_BLOCKING_CANARY_DISABLE"

CONFIG_LOG_PREFIX: Final[str] = "[ENF] config:"
AUDIT_WARN_PREFIX: Final[str] = "[ENF] WARNING:"

EnfMode = Literal["skipped", "shadow-only"]

_TRUTHY = frozenset({"1", "true", "yes", "on", "enabled"})
_FALSY = frozenset({"0", "false", "no", "off", "disabled"})


def _parse_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUTHY:
        return True
    if normalized in _FALSY:
        return False
    return default


def _raw_or_unset(key: str, *, environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    raw = env.get(key)
    if raw is None:
        return "unset"
    return raw.strip()


@dataclass(frozen=True)
class EnfRuntimeConfig:
    """Resolved ENF flags for CI / preview entrypoints."""

    enabled: bool
    blocking_canary: bool
    mode: EnfMode
    gov_enf_enable_raw: str
    enf_enable_raw: str
    blocking_canary_raw: str
    blocking_canary_disable_raw: str

    @property
    def should_run_enf(self) -> bool:
        return self.enabled and self.mode == "shadow-only"

    def format_config_log_line(self) -> str:
        enable_display = "1" if self.enabled else "0"
        canary_display = "1" if self.blocking_canary else "0"
        return (
            f"{CONFIG_LOG_PREFIX} "
            f"{ENV_GOV_ENF_ENABLE}={enable_display}, "
            f"{ENV_GOV_ENF_BLOCKING_CANARY}={canary_display} "
            f"({self.mode})"
        )


def load_enf_config(*, environ: Mapping[str, str] | None = None) -> EnfRuntimeConfig:
    """
    Load ENF flags from environment.

    Backward compatible defaults (unset env):
    - ENF enabled (shadow preview runs as today)
    - blocking_canary off (shadow-only; no job impact)

    ``GOV_ENF_ENABLE`` wins over ``ENF_ENABLE`` when set.
    """
    env = os.environ if environ is None else environ

    gov_raw = env.get(ENV_GOV_ENF_ENABLE)
    legacy_raw = env.get(ENV_ENF_ENABLE)
    canary_raw = env.get(ENV_GOV_ENF_BLOCKING_CANARY)
    canary_disable_raw = env.get(ENV_GOV_ENF_BLOCKING_CANARY_DISABLE)

    if gov_raw is not None and gov_raw.strip():
        enabled = _parse_bool(gov_raw, default=True)
    elif legacy_raw is not None and legacy_raw.strip():
        enabled = _parse_bool(legacy_raw, default=True)
    else:
        enabled = True

    if canary_disable_raw is not None and _parse_bool(canary_disable_raw, default=False):
        blocking_canary = False
    else:
        blocking_canary = _parse_bool(canary_raw, default=False)
    mode: EnfMode = "shadow-only" if enabled else "skipped"

    return EnfRuntimeConfig(
        enabled=enabled,
        blocking_canary=blocking_canary,
        mode=mode,
        gov_enf_enable_raw=_raw_or_unset(ENV_GOV_ENF_ENABLE, environ=env),
        enf_enable_raw=_raw_or_unset(ENV_ENF_ENABLE, environ=env),
        blocking_canary_raw=_raw_or_unset(ENV_GOV_ENF_BLOCKING_CANARY, environ=env),
        blocking_canary_disable_raw=_raw_or_unset(
            ENV_GOV_ENF_BLOCKING_CANARY_DISABLE,
            environ=env,
        ),
    )


def collect_enf_audit_warnings(config: EnfRuntimeConfig) -> list[str]:
    """
    Return audit lines when ENF or blocking canary is explicitly disabled via env.

    Default unset env (shadow-only, blocking off) does not emit warnings — only
    explicit disable values are surfaced for reviewer visibility.
    """
    warnings: list[str] = []

    if not config.enabled:
        if config.gov_enf_enable_raw != "unset" and not _parse_bool(
            config.gov_enf_enable_raw,
            default=True,
        ):
            warnings.append(
                f"{AUDIT_WARN_PREFIX} ENF is DISABLED via "
                f"{ENV_GOV_ENF_ENABLE}={config.gov_enf_enable_raw}"
            )
        elif config.enf_enable_raw != "unset" and not _parse_bool(
            config.enf_enable_raw,
            default=True,
        ):
            warnings.append(
                f"{AUDIT_WARN_PREFIX} ENF is DISABLED via "
                f"{ENV_ENF_ENABLE}={config.enf_enable_raw}"
            )

    if config.blocking_canary_disable_raw != "unset" and _parse_bool(
        config.blocking_canary_disable_raw,
        default=False,
    ):
        warnings.append(
            f"{AUDIT_WARN_PREFIX} Blocking canary is DISABLED via "
            f"{ENV_GOV_ENF_BLOCKING_CANARY_DISABLE}={config.blocking_canary_disable_raw}"
        )
    elif config.blocking_canary_raw != "unset" and not config.blocking_canary:
        warnings.append(
            f"{AUDIT_WARN_PREFIX} Blocking canary is DISABLED via "
            f"{ENV_GOV_ENF_BLOCKING_CANARY}={config.blocking_canary_raw}"
        )

    return warnings


def _github_actions_warning(message: str) -> None:
    """Emit a non-fatal GitHub Actions annotation (visibility only, never fails job)."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::warning title=ENF config audit::{escaped}", flush=True)


def log_enf_audit_warnings(config: EnfRuntimeConfig) -> list[str]:
    """Print audit warnings to stdout; mirror to GH Actions when in CI."""
    warnings = collect_enf_audit_warnings(config)
    for line in warnings:
        print(line, flush=True)
        _github_actions_warning(line)
    return warnings


def log_enf_config(config: EnfRuntimeConfig) -> None:
    """Emit config line plus optional audit warnings to stdout (CI observability)."""
    print(config.format_config_log_line(), flush=True)
    log_enf_audit_warnings(config)


def main(argv: list[str] | None = None) -> int:
    """CLI entry for CI audit step: print config + non-fatal disable warnings."""
    _ = argv
    config = load_enf_config()
    log_enf_config(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
