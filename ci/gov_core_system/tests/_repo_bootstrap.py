"""Path bootstrap for gov_core_system unittest (no hardcoded disk paths)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from core.repo_paths import ensure_repo_root_on_path, find_repo_root

__all__ = [
    "bootstrap_gov_core_tests",
    "ensure_repo_root_on_path",
    "find_repo_root",
    "prepare_test_idempotency_env",
]


def bootstrap_gov_core_tests(*, test_file: Path | None = None) -> tuple[Path, Path | None]:
    """
    Ensure ``gov_core_system`` and optional repo root are on ``sys.path``.

    Call from test modules before importing ``app_api`` / ``core.*``.
    """
    anchor = (test_file or Path(__file__)).resolve()
    gov_root = anchor.parents[1]
    gov_s = str(gov_root)
    if gov_s not in sys.path:
        sys.path.insert(0, gov_s)

    repo_root = ensure_repo_root_on_path(start=anchor)
    return gov_root, repo_root


def prepare_test_idempotency_env() -> None:
    """
    B-line / app_api unittest: SQLite idempotency only (no PG connect attempts).

    Order: set ``GOV_CORE_TEST_USE_INMEM_IDEM=1``, drop ``DATABASE_URL``, then clear store.
    Call from setUp/tearDown before restoring a saved env that may still carry DATABASE_URL.
    """
    from core.idempotency import ENV_TEST_USE_INMEM_IDEM, clear_store_for_tests

    os.environ[ENV_TEST_USE_INMEM_IDEM] = "1"
    os.environ.pop("DATABASE_URL", None)
    clear_store_for_tests()
