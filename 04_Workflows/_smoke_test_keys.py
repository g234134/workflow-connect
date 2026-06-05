"""_smoke_test_keys.py — 盲測：OpenAI / Groq / Telegram

嚴守保密規範：
  - 永不在 stdout / stderr 印出任何金鑰字串（含遮罩片段）。
  - 僅輸出 [OK] / [FAILED] 與 HTTP 狀態碼，以及最少必要的錯誤類型。
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, Tuple

from _tang_http import blind_http_dual_ssl  # type: ignore
from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from gov_paths import get_secret  # type: ignore


def _key_present(name: str) -> bool:
    v = (get_secret(name, "") or "").strip()
    if not v:
        return False
    if "PLACEHOLDER" in v.upper():
        return False
    return True


def test_openai() -> Tuple[str, int, str]:
    if not _key_present("OPENAI_API_KEY"):
        return "FAILED", 0, "key_missing"
    key = (get_secret("OPENAI_API_KEY", "") or "").strip()
    code, etype = blind_http_dual_ssl(
        "https://api.openai.com/v1/models",
        method="GET",
        headers={"Authorization": f"Bearer {key}"},
        timeout=20,
    )
    return ("OK" if code == 200 else "FAILED"), code, etype


def test_groq() -> Tuple[str, int, str]:
    if not _key_present("GROQ_API_KEY"):
        return "FAILED", 0, "key_missing"
    key = (get_secret("GROQ_API_KEY", "") or "").strip()
    payload = json.dumps({
        "model": (get_secret("GROQ_MODEL", "") or "llama-3.1-8b-instant").strip(),
        "max_tokens": 1,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "ping"},
            {"role": "user", "content": "ping"},
        ],
    }).encode("utf-8")
    code, etype = blind_http_dual_ssl(
        "https://api.groq.com/openai/v1/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        body=payload,
        timeout=25,
    )
    return ("OK" if code == 200 else "FAILED"), code, etype


def test_telegram() -> Tuple[str, int, str]:
    if not _key_present("TELEGRAM_BOT_TOKEN"):
        return "FAILED", 0, "key_missing"
    token = (get_secret("TELEGRAM_BOT_TOKEN", "") or "").strip()
    code, etype = blind_http_dual_ssl(
        f"https://api.telegram.org/bot{token}/getMe",
        method="GET",
        headers={},
        timeout=20,
    )
    return ("OK" if code == 200 else "FAILED"), code, etype


def main() -> int:
    results: Dict[str, Tuple[str, int, str]] = {
        "OpenAI": test_openai(),
        "Groq": test_groq(),
        "Telegram": test_telegram(),
    }
    print("==== 三鑰盲測 (do not print keys) ====")
    rc = 0
    for name, (status, code, etype) in results.items():
        suffix = ""
        if status != "OK":
            suffix = f" code={code}"
            if etype:
                suffix += f" type={etype}"
            rc = 1
        print(f"  {name:8s} : [{status}]{suffix}")
    print("======================================")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
