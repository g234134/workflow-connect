"""_integration_v256_scout_closeout.py — v2.56 整合測試（elite 索引 → 偵察 → 結案草案）。

預設不發 Telegram；若環境變數 RUN_TELEGRAM_CLOSEOUT=1 則最後一步加上 --telegram-send。
"""
from __future__ import annotations

import os
import subprocess
import sys

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)


def _gov_main() -> str:
    return os.path.normpath(
        os.path.join(_root, "01_Environments", "python_venvs", "gov_main", "Scripts", "python.exe")
    )


def _gov_agency() -> str:
    return os.path.normpath(
        os.path.join(_root, "01_Environments", "python_venvs", "gov_agency", "Scripts", "python.exe")
    )


def run() -> int:
    os.environ.setdefault("TANG_GOV_ROOT", _root)
    os.environ.setdefault("PYTHONUTF8", "1")
    wf = _here
    ac = os.path.join(_root, "02_Agents_Core")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([_root, ac, wf])

    gm, ga = _gov_main(), _gov_agency()
    if not os.path.isfile(gm) or not os.path.isfile(ga):
        print("venv missing", file=sys.stderr)
        return 2

    maxf = os.environ.get("ELITE_BUILD_MAX", "600")
    r1 = subprocess.run(
        [gm, os.path.join(wf, "_build_elite_index.py"), "--max-files", maxf],
        cwd=wf,
        env=env,
    )
    if r1.returncode != 0:
        return r1.returncode

    r2 = subprocess.run(
        [ga, os.path.join(wf, "_scout_engine.py"), "--simulate"],
        cwd=wf,
        env=env,
    )
    if r2.returncode != 0:
        return r2.returncode

    r3 = subprocess.run(
        [gm, os.path.join(wf, "_report_generator.py"), "--write"],
        cwd=wf,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    sys.stdout.write(r3.stdout or "")
    sys.stderr.write(r3.stderr or "")
    if r3.returncode != 0:
        return r3.returncode

    if os.environ.get("RUN_TELEGRAM_CLOSEOUT") == "1":
        r4 = subprocess.run(
            [gm, os.path.join(wf, "_report_generator.py"), "--telegram-send"],
            cwd=wf,
            env=env,
        )
        if r4.returncode != 0:
            return r4.returncode

    print("[OK] v2.56 integration: elite_cache + scout_last_pipeline + closing_draft (--write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
