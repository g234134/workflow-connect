"""OpenAI 單鑰盲測（與 _smoke_test_keys 同規範：不印金鑰含遮罩）。

若需三鑰一併驗證，請改用 _smoke_test_keys.py。
"""
from __future__ import annotations

import os
import sys

from _tang_http import blind_http_dual_ssl  # type: ignore
from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from gov_paths import get_secret  # type: ignore


def main() -> int:
    key = (get_secret("OPENAI_API_KEY", "") or "").strip()
    if not key:
        print("[FAILED] OPENAI_API_KEY code=0 type=key_missing")
        return 1
    if "PLACEHOLDER" in key.upper():
        print("[FAILED] OPENAI_API_KEY code=0 type=placeholder")
        return 1
    code, etype = blind_http_dual_ssl(
        "https://api.openai.com/v1/models",
        method="GET",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    status = "OK" if code == 200 else "FAILED"
    suf = f" code={code}" + (f" type={etype}" if etype else "")
    print(f"[{status}] OpenAI /v1/models{suf}")
    return 0 if code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
