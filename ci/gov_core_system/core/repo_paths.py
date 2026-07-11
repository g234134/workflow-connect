"""Portable repo-root discovery and ``sys.path`` bootstrap for gov_core_system."""

from __future__ import annotations

import sys
from pathlib import Path

_GOV_CORE_ROOT = Path(__file__).resolve().parents[1]


def find_repo_root(*, start: Path | None = None) -> Path | None:
    """
    Walk parents for repo-root markers (portable; no env-specific paths).

    Markers (first match wins):
    1. ``00_master_plan.md`` at a parent directory.
    2. ``01_Environments/`` directory **and** ``context/context_builder.py`` at the same parent.
    """
    anchor = (start or _GOV_CORE_ROOT).resolve()
    for parent in anchor.parents:
        if (parent / "00_master_plan.md").is_file():
            return parent
        if (parent / "01_Environments").is_dir() and (
            parent / "context" / "context_builder.py"
        ).is_file():
            return parent
    return None


def ensure_repo_root_on_path(
    *,
    start: Path | None = None,
    insert_at: int = 1,
) -> Path | None:
    """
    Insert the discovered repo root on ``sys.path`` at ``insert_at`` when absent.

    Default ``insert_at=1`` keeps ``gov_core_system`` at index 0 when bootstrapped
    from ``app_api`` or ``tests._repo_bootstrap``.
    """
    repo_root = find_repo_root(start=start)
    if repo_root is None:
        return None
    repo_s = str(repo_root)
    if repo_s not in sys.path:
        sys.path.insert(insert_at, repo_s)
    return repo_root
