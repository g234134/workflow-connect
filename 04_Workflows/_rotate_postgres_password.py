"""Rotate POSTGRES_PASSWORD inside 01_Environments/.env.

Governance:
- 嚴禁將金鑰原文輸出至 stdout/stderr/log（AGENTS.md §紅線）。
- 32 char [A-Za-z0-9] via secrets.choice（CSPRNG）。
- 原子寫入：先寫 .env.tmp 再 os.replace 以避免半寫。
- 既有其他 key 一律保留、僅 upsert 目標 key。

Usage:
    python 04_Workflows/_rotate_postgres_password.py
"""
from __future__ import annotations

import os
import secrets
import string
import sys
from pathlib import Path

ENV_PATH = Path(r"D:\大唐三省六部\01_Environments\.env")
KEY = "POSTGRES_PASSWORD"
LENGTH = 32
ALPHABET = string.ascii_letters + string.digits  # [A-Za-z0-9]


def gen_password() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))


def _key_of(line: str) -> str | None:
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if s.startswith("export "):
        s = s[len("export "):]
    eq = s.find("=")
    if eq <= 0:
        return None
    return s[:eq].strip()


def upsert_env(path: Path, key: str, value: str) -> tuple[list[str], str]:
    """Upsert key=value into .env. Returns (sorted_unique_keys, action)."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{key}={value}\n", encoding="utf-8")
        return [key], "created"

    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()
    new_lines: list[str] = []
    found = False
    for ln in lines:
        if _key_of(ln) == key:
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(ln)
    if not found:
        new_lines.append(f"{key}={value}")

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)

    keys: list[str] = []
    for ln in new_lines:
        k = _key_of(ln)
        if k:
            keys.append(k)
    return sorted(set(keys)), ("updated" if found else "inserted")


def main() -> int:
    pwd = gen_password()
    try:
        keys, action = upsert_env(ENV_PATH, KEY, pwd)
    except Exception as exc:
        # 不洩漏訊息細節，避免極端情況下含敏感片段
        print(f"[FAIL] {type(exc).__name__}: <redacted>")
        return 1
    finally:
        del pwd  # 立刻釋出引用

    print(f"[OK] {KEY} {action} in .env  (len={LENGTH}, alphabet=[A-Za-z0-9])")
    print(f"[OK] .env keys total: {len(keys)}")
    print("Keys (sorted, NO values):")
    for k in keys:
        print(f"  - {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
