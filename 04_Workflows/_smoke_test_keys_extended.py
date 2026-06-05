"""_smoke_test_keys_extended.py — 多供應商金鑰盲測

嚴守：永不印出金鑰、回應 body、或 .env 內容；僅 [OK]/[FAILED]、HTTP code、簡短錯誤類型。
原三鑰（OpenAI / Groq / Telegram）邏輯與 _smoke_test_keys.py 一致。
"""
from __future__ import annotations

import json
import os
from typing import Callable, List, Tuple

from _tang_http import blind_http_dual_ssl  # type: ignore
from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from gov_paths import get_secret  # type: ignore  # noqa: E402

from _smoke_test_keys import (  # type: ignore  # noqa: E402
    test_groq,
    test_openai,
    test_telegram,
)


def _key_present(name: str) -> bool:
    v = (get_secret(name, "") or "").strip()
    if not v:
        return False
    if "PLACEHOLDER" in v.upper():
        return False
    return True


def _qwen_key() -> str:
    for n in ("QWEN_API_KEY", "QWEN_APIKEY", "DASHSCOPE_API_KEY"):
        if _key_present(n):
            return (get_secret(n, "") or "").strip()
    return ""


def test_nvidia() -> Tuple[str, int, str]:
    if not _key_present("NVIDIA_API_KEY"):
        return "FAILED", 0, "key_missing"
    key = (get_secret("NVIDIA_API_KEY", "") or "").strip()
    code, etype = blind_http_dual_ssl(
        "https://integrate.api.nvidia.com/v1/models",
        method="GET",
        headers={"Authorization": f"Bearer {key}"},
        timeout=25,
    )
    return ("OK" if code == 200 else "FAILED"), code, etype


def test_tavily() -> Tuple[str, int, str]:
    if not _key_present("TAVILY_API_KEY"):
        return "FAILED", 0, "key_missing"
    key = (get_secret("TAVILY_API_KEY", "") or "").strip()
    body = json.dumps(
        {"api_key": key, "query": "ping", "max_results": 1}
    ).encode("utf-8")
    code, etype = blind_http_dual_ssl(
        "https://api.tavily.com/search",
        method="POST",
        headers={"Content-Type": "application/json"},
        body=body,
        timeout=30,
    )
    return ("OK" if code == 200 else "FAILED"), code, etype


def test_firecrawl() -> Tuple[str, int, str]:
    if not _key_present("FIRECRAWL_API_KEY"):
        return "FAILED", 0, "key_missing"
    key = (get_secret("FIRECRAWL_API_KEY", "") or "").strip()
    last_code, last_etype = 0, ""
    for url in (
        "https://api.firecrawl.dev/v2/team/credit-usage",
        "https://api.firecrawl.dev/v1/usage",
    ):
        code, etype = blind_http_dual_ssl(
            url,
            method="GET",
            headers={"Authorization": f"Bearer {key}"},
            timeout=25,
        )
        last_code, last_etype = code, etype
        if code == 200:
            return "OK", 200, ""
    return "FAILED", last_code, last_etype


def test_jina() -> Tuple[str, int, str]:
    if not _key_present("JINA_API_KEY"):
        return "FAILED", 0, "key_missing"
    key = (get_secret("JINA_API_KEY", "") or "").strip()
    body = json.dumps(
        {
            "model": "jina-embeddings-v2-base-en",
            "input": ["ping"],
        }
    ).encode("utf-8")
    code, etype = blind_http_dual_ssl(
        "https://api.jina.ai/v1/embeddings",
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        body=body,
        timeout=30,
    )
    return ("OK" if code == 200 else "FAILED"), code, etype


def test_hf() -> Tuple[str, int, str]:
    if not _key_present("HF_TOKEN"):
        return "FAILED", 0, "key_missing"
    key = (get_secret("HF_TOKEN", "") or "").strip()
    code, etype = blind_http_dual_ssl(
        "https://huggingface.co/api/whoami-v2",
        method="GET",
        headers={"Authorization": f"Bearer {key}"},
        timeout=25,
    )
    return ("OK" if code == 200 else "FAILED"), code, etype


def test_qwen() -> Tuple[str, int, str]:
    k = _qwen_key()
    if not k:
        return "FAILED", 0, "key_missing"
    body = json.dumps(
        {
            "model": "qwen-turbo",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
        }
    ).encode("utf-8")
    for base in (
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    ):
        code, etype = blind_http_dual_ssl(
            base,
            method="POST",
            headers={
                "Authorization": f"Bearer {k}",
                "Content-Type": "application/json",
            },
            body=body,
            timeout=35,
        )
        if code == 200:
            return "OK", 200, ""
    return "FAILED", code, etype


def _run(
    items: List[Tuple[str, Callable[[], Tuple[str, int, str]]]],
) -> int:
    print("==== 擴充金鑰盲測 (do not print keys) ====")
    rc = 0
    for label, fn in items:
        status, code, etype = fn()
        if status != "OK":
            rc = 1
        suffix = ""
        if status != "OK":
            suffix = f" code={code}"
            if etype:
                suffix += f" type={etype}"
        print(f"  {label:20s} : [{status}]{suffix}")
    print("==========================================")
    return rc


def main() -> int:
    items: List[Tuple[str, Callable[[], Tuple[str, int, str]]]] = [
        ("OpenAI", test_openai),
        ("Groq", test_groq),
        ("Telegram", test_telegram),
        ("NVIDIA", test_nvidia),
        ("Tavily", test_tavily),
        ("Firecrawl", test_firecrawl),
        ("Jina", test_jina),
        ("HuggingFace", test_hf),
        ("Qwen (DashScope)", test_qwen),
    ]
    return _run(items)


if __name__ == "__main__":
    raise SystemExit(main())
