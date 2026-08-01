#!/usr/bin/env python3
"""One-command MVP mainline regression runner (Wave 1 · W1-T3).

Runs gate → cleaning → bundle E2E for demo_phase and sampleco/2026-0001.
Wraps tests/test_mvp_mainline.py for local runs and CI.

Usage:
    python scripts/run_mvp_mainline_regression.py
    python scripts/run_mvp_mainline_regression.py -v
"""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run MVP mainline regression (demo_phase + sampleco).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose unittest output")
    args = parser.parse_args(argv)

    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(_REPO_ROOT / "tests"),
        pattern="test_mvp_mainline.py",
        top_level_dir=str(_REPO_ROOT),
    )
    runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("PASS MVP mainline regression (demo_phase + sampleco + generic-low-risk)")
        return 0

    print("FAIL MVP mainline regression — see errors above", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
