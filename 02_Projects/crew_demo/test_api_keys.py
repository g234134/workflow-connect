"""
Probe external APIs using keys from .env — prints only OK/FAIL, never secrets.
Run from project folder: python test_api_keys.py
"""

from __future__ import annotations

import glob
import os
from typing import Callable

import httpx
from dotenv import load_dotenv


def _pick(*names: str) -> str:
    """Return first non-empty env value; supports legacy plural *_API_KEYS."""
    for n in names:
        v = os.environ.get(n, "").strip()
        if not v:
            continue
        if "," in v:
            v = v.split(",")[0].strip()
        return v
    return ""


def _ok(name: str, detail: str = "") -> None:
    print(f"OK   {name}" + (f"  ({detail})" if detail else ""))


def _fail(name: str, err: str) -> None:
    print(f"FAIL {name}  ({err})")


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(here, ".env"))

    # 若主 .env 六個槽都是空的，嘗試載入 .env.backup*（新版覆蓋舊版）
    def count_filled() -> int:
        return sum(
            1
            for _ in (
                _pick("GROQ_API_KEY", "GROQ_API_KEYS"),
                _pick("NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY"),
                _pick("HUGGINGFACE_API_KEY", "HF_TOKEN"),
                _pick("TAVILY_API_KEY", "TAVILY_API_KEYS"),
                _pick("FIRECRAWL_API_KEY", "FIRECRAWL_API_KEYS"),
                _pick("JINA_API_KEY", "JINA_API_KEYS"),
            )
            if _
        )

    if count_filled() == 0:
        backs = sorted(glob.glob(os.path.join(here, ".env.backup*")))
        for p in backs:
            load_dotenv(p, override=True)

    filled = count_filled()
    print("--- API key probe (keys loaded from .env in this folder) ---")
    print(f"Working dir: {here}")
    print(f"Non-empty key slots: {filled}/6  (no names/values shown)\n")

    tests: list[tuple[str, Callable[[], None]]] = []
    any_ran = False

    # --- Groq ---
    def t_groq() -> None:
        key = _pick("GROQ_API_KEY", "GROQ_API_KEYS")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set")
        r = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
                "messages": [{"role": "user", "content": "Say OK."}],
                "max_tokens": 8,
            },
            timeout=60.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    tests.append(("Groq chat", t_groq))

    # --- NVIDIA NIM (OpenAI-compatible chat) ---
    def t_nvidia() -> None:
        key = _pick("NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY")
        if not key:
            raise RuntimeError("NVIDIA_NIM_API_KEY not set")
        model = os.environ.get("NVIDIA_NIM_MODEL", "meta/llama-3.3-70b-instruct")
        r = httpx.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say OK in one word."}],
                "max_tokens": 10,
            },
            timeout=120.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    tests.append(("NVIDIA NIM chat", t_nvidia))

    # --- Hugging Face token ---
    def t_hf() -> None:
        key = _pick("HUGGINGFACE_API_KEY", "HF_TOKEN")
        if not key:
            raise RuntimeError("HUGGINGFACE_API_KEY not set")
        r = httpx.get(
            "https://huggingface.co/api/whoami-v2",
            headers={"Authorization": f"Bearer {key}"},
            timeout=30.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    tests.append(("Hugging Face whoami", t_hf))

    # --- Tavily ---
    def t_tavily() -> None:
        key = _pick("TAVILY_API_KEY", "TAVILY_API_KEYS")
        if not key:
            raise RuntimeError("TAVILY_API_KEY not set")
        r = httpx.post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": "Python programming", "max_results": 1},
            timeout=60.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    tests.append(("Tavily search", t_tavily))

    # --- Firecrawl (scrape minimal) ---
    def t_firecrawl() -> None:
        key = _pick("FIRECRAWL_API_KEY", "FIRECRAWL_API_KEYS")
        if not key:
            raise RuntimeError("FIRECRAWL_API_KEY not set")
        r = httpx.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"url": "https://example.com", "formats": ["markdown"]},
            timeout=60.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    tests.append(("Firecrawl scrape", t_firecrawl))

    # --- Jina (reader — GET with auth header) ---
    def t_jina() -> None:
        key = _pick("JINA_API_KEY", "JINA_API_KEYS")
        if not key:
            raise RuntimeError("JINA_API_KEY not set")
        r = httpx.get(
            "https://r.jina.ai/https://example.com",
            headers={"Authorization": f"Bearer {key}"},
            timeout=60.0,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    tests.append(("Jina reader (r.jina.ai)", t_jina))

    print()
    for name, fn in tests:
        try:
            fn()
            _ok(name)
            any_ran = True
        except RuntimeError as e:
            msg = str(e)
            if "not set" in msg.lower():
                _fail(name, "skipped — key empty in .env")
            else:
                _fail(name, msg[:180])
        except Exception as e:
            _fail(name, f"{type(e).__name__}: {str(e)[:160]}")

    if not any_ran:
        print("\n(No successful calls — fill keys in .env and re-run.)")

    print("\nDone.")


if __name__ == "__main__":
    main()
