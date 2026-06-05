"""
dispatcher.py - 路由器（Ollama / SmartRouter / Cursor）

策略：
- 先用 task_scorer.score_task 取得 difficulty 與 route 建議
- route=ollama：打本機 Ollama /api/chat
- route=smartrouter：打 SmartRouter（OpenAI-compatible /v1/chat/completions）
- route=cursor：輸出「需要 Cursor 介入」的交接 JSON（不在這裡自動改檔）
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from task_scorer import ScoreResult, score_task


OLLAMA_URL_DEFAULT = "http://127.0.0.1:11434/api/chat"
SMARTROUTER_URL_DEFAULT = "http://127.0.0.1:8000/v1/chat/completions"


@dataclass(frozen=True)
class DispatchResult:
    score: ScoreResult
    used_route: str
    ok: bool
    elapsed_s: float
    output_text: str
    raw: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score.to_dict(),
            "used_route": self.used_route,
            "ok": self.ok,
            "elapsed_s": self.elapsed_s,
            "output_text": self.output_text,
            "raw": self.raw,
        }


def _extract_openai_content(resp_json: Dict[str, Any]) -> str:
    try:
        return resp_json["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(resp_json, ensure_ascii=False)


def _call_smartrouter(
    *,
    router_url: str,
    messages: List[Dict[str, str]],
    timeout_s: float,
) -> Dict[str, Any]:
    payload = {"messages": messages}
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(router_url, json=payload)
        resp.raise_for_status()
        return resp.json()


def _call_ollama(
    *,
    ollama_url: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout_s: float,
) -> Dict[str, Any]:
    payload = {"model": model, "messages": messages, "stream": False}
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(ollama_url, json=payload)
        resp.raise_for_status()
        return resp.json()


def dispatch_task(
    *,
    task_text: str,
    low: int = 3,
    high: int = 8,
    ollama_url: str = OLLAMA_URL_DEFAULT,
    ollama_model: str = "llama3:latest",
    smartrouter_url: str = SMARTROUTER_URL_DEFAULT,
    timeout_s: float = 60.0,
) -> DispatchResult:
    score = score_task(task_text, low=low, high=high)
    messages = [
        {"role": "system", "content": "請用繁體中文，直接給可執行的步驟或答案。"},
        {"role": "user", "content": task_text},
    ]

    start = time.time()

    if score.route == "ollama":
        resp_json = _call_ollama(
            ollama_url=ollama_url,
            model=os.getenv("TANK_OLLAMA_MODEL", ollama_model),
            messages=messages,
            timeout_s=timeout_s,
        )
        text = ""
        try:
            text = resp_json["message"]["content"]
        except Exception:
            text = json.dumps(resp_json, ensure_ascii=False)
        return DispatchResult(
            score=score,
            used_route="ollama",
            ok=True,
            elapsed_s=round(time.time() - start, 3),
            output_text=text,
            raw={"ollama": resp_json},
        )

    if score.route == "smartrouter":
        resp_json = _call_smartrouter(router_url=smartrouter_url, messages=messages, timeout_s=timeout_s)
        text = _extract_openai_content(resp_json)
        return DispatchResult(
            score=score,
            used_route="smartrouter",
            ok=True,
            elapsed_s=round(time.time() - start, 3),
            output_text=text,
            raw={"smartrouter": resp_json},
        )

    # Cursor route：不在這裡自動動工作區，只輸出交接包
    handoff = {
        "needs_cursor": True,
        "reason": "difficulty>=8 or high-risk signals present",
        "task_text": task_text,
        "score": score.to_dict(),
        "suggested_next_steps": [
            "在 Cursor 中開啟相關檔案",
            "列出修改範圍與測試指令",
            "逐步實作並以實際執行結果驗證",
        ],
    }
    return DispatchResult(
        score=score,
        used_route="cursor",
        ok=True,
        elapsed_s=round(time.time() - start, 3),
        output_text="需要 Cursor 介入（已輸出交接 JSON）",
        raw={"cursor_handoff": handoff},
    )


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Dispatch task to Ollama / SmartRouter / Cursor")
    p.add_argument("--text", required=True, help="Task text")
    p.add_argument("--low", type=int, default=3)
    p.add_argument("--high", type=int, default=8)
    p.add_argument("--timeout", type=float, default=60.0)
    args = p.parse_args()

    res = dispatch_task(task_text=args.text, low=args.low, high=args.high, timeout_s=args.timeout)
    print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

