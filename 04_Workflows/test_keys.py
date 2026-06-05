# test_keys.py — 糧草效能校準（全軍閱兵）
# 對通訊／大腦／偵察三類 API 進行最小負載連通測試，回報 OK/Fail/延遲(ms)/備註。
# 嚴禁將密鑰本體輸出至日誌或控制台；僅以 length+masked tail 顯示存在性。

from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gov_paths import get_secret, get_tang_gov_root, resolve_agent_output_path  # type: ignore


HTTP_TIMEOUT = int(os.environ.get("KEY_TEST_TIMEOUT", "20"))


def _ssl_ctx() -> ssl.SSLContext:
    try:
        return ssl.create_default_context()
    except Exception:  # noqa: BLE001
        return ssl._create_unverified_context()  # type: ignore[attr-defined]


DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 TangChariot/1.0"
)


def _http(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    timeout: int = HTTP_TIMEOUT,
) -> Tuple[int, Any, int]:
    """回傳 (status_code, parsed_json_or_raw_str, latency_ms)；雙 SSL ctx 回退。"""
    last_err: Optional[BaseException] = None
    final_headers = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
    if headers:
        final_headers.update(headers)
    for ctx in (_ssl_ctx(), ssl._create_unverified_context()):  # type: ignore[attr-defined]
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(url, data=body, method=method)
            for k, v in final_headers.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                lat = int((time.perf_counter() - t0) * 1000)
                try:
                    parsed = json.loads(raw) if raw.strip() else {}
                except json.JSONDecodeError:
                    parsed = {"_raw": raw[:400]}
                return resp.getcode(), parsed, lat
        except urllib.error.HTTPError as e:
            lat = int((time.perf_counter() - t0) * 1000)
            err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            try:
                parsed = json.loads(err_body) if err_body.strip() else {}
            except json.JSONDecodeError:
                parsed = {"_raw": err_body[:400]}
            return e.code, parsed, lat
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
            continue
    return 0, {"error": repr(last_err)}, -1


def _mask(v: str) -> str:
    if not v:
        return "(empty)"
    if len(v) <= 8:
        return "*" * len(v)
    return f"len={len(v)}|tail={v[-4:]}"


def _result(
    name: str, ok: bool, latency_ms: int, note: str = "", *, http: Optional[int] = None
) -> Dict[str, Any]:
    return {
        "api": name,
        "status": "OK" if ok else "Fail",
        "latency_ms": latency_ms,
        "note": note,
        "http": http,
    }


# ── 通訊類 ──
def test_telegram() -> Dict[str, Any]:
    token = (get_secret("TELEGRAM_BOT_TOKEN", "") or "").strip()
    if not token or "PLACEHOLDER" in token:
        return _result("TELEGRAM_BOT_TOKEN", False, -1, "missing/placeholder")
    code, data, lat = _http(f"https://api.telegram.org/bot{token}/getMe")
    if code == 200 and isinstance(data, dict) and data.get("ok"):
        r = data.get("result") or {}
        return _result(
            "TELEGRAM_BOT_TOKEN",
            True,
            lat,
            f"@{r.get('username')} id={r.get('id')}",
            http=code,
        )
    desc = (data or {}).get("description") if isinstance(data, dict) else str(data)
    return _result("TELEGRAM_BOT_TOKEN", False, lat, f"{desc}", http=code)


# ── 大腦類（OpenAI 兼容 chat.completions）──
def _chat_completion(
    name: str, url: str, key: str, model: str, *, prompt: str = "Hi"
) -> Dict[str, Any]:
    if not key or "PLACEHOLDER" in key:
        return _result(name, False, -1, "missing/placeholder")
    payload = {
        "model": model,
        "max_tokens": 5,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    code, data, lat = _http(url, method="POST", headers=headers, body=body)
    if code == 200 and isinstance(data, dict):
        try:
            content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            usage = data.get("usage") or {}
            tokens = usage.get("total_tokens") or "?"
            return _result(
                name,
                True,
                lat,
                f"model={model} tok={tokens} reply={content[:30]!r}",
                http=code,
            )
        except Exception as e:  # noqa: BLE001
            return _result(name, False, lat, f"parse_error:{e}", http=code)
    err = ""
    if isinstance(data, dict):
        err = str((data.get("error") or {}).get("message") or data.get("message") or data)[:120]
    return _result(name, False, lat, err or "unknown", http=code)


def test_groq() -> Dict[str, Any]:
    return _chat_completion(
        "GROQ_API_KEY",
        "https://api.groq.com/openai/v1/chat/completions",
        (get_secret("GROQ_API_KEY", "") or "").strip(),
        get_secret("GROQ_MODEL", "") or "llama-3.3-70b-versatile",
    )


def test_qwen() -> Dict[str, Any]:
    # 阿里雲百煉 OpenAI-compatible 端點：國際版 dashscope-intl，簡中版 dashscope
    url = (
        get_secret("QWEN_API_URL", "")
        or "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    )
    return _chat_completion(
        "QWEN_APIKEY",
        url,
        (get_secret("QWEN_APIKEY", "") or "").strip(),
        get_secret("QWEN_MODEL", "") or "qwen-turbo",
    )


def test_nvidia() -> Dict[str, Any]:
    return _chat_completion(
        "NVIDIA_API_KEY",
        get_secret("NVIDIA_API_URL", "") or "https://integrate.api.nvidia.com/v1/chat/completions",
        (get_secret("NVIDIA_API_KEY", "") or "").strip(),
        get_secret("NVIDIA_MODEL", "") or "meta/llama-3.1-8b-instruct",
    )


# ── 偵察類 ──
def test_firecrawl() -> Dict[str, Any]:
    key = (get_secret("FIRECRAWL_API_KEY", "") or "").strip()
    if not key or "PLACEHOLDER" in key:
        return _result("FIRECRAWL_API_KEY", False, -1, "missing/placeholder")
    code, data, lat = _http(
        "https://api.firecrawl.dev/v1/team/credit-usage",
        headers={"Authorization": f"Bearer {key}"},
    )
    if code == 200 and isinstance(data, dict):
        r = data.get("data") or data
        return _result(
            "FIRECRAWL_API_KEY",
            True,
            lat,
            f"credits_remaining={r.get('remaining_credits') or r.get('remainingCredits') or '?'}",
            http=code,
        )
    if code == 401 or code == 403:
        return _result("FIRECRAWL_API_KEY", False, lat, "unauthorized", http=code)
    msg = str(data)[:120] if data else "?"
    return _result("FIRECRAWL_API_KEY", False, lat, msg, http=code)


def test_tavily() -> Dict[str, Any]:
    key = (get_secret("TAVILY_API_KEY", "") or "").strip()
    if not key or "PLACEHOLDER" in key:
        return _result("TAVILY_API_KEY", False, -1, "missing/placeholder")
    payload = {
        "api_key": key,
        "query": "hello",
        "search_depth": "basic",
        "max_results": 1,
        "include_answer": False,
        "include_raw_content": False,
    }
    body = json.dumps(payload).encode("utf-8")
    code, data, lat = _http(
        "https://api.tavily.com/search",
        method="POST",
        headers={"Content-Type": "application/json"},
        body=body,
    )
    if code == 200 and isinstance(data, dict):
        n = len((data.get("results") or []))
        return _result("TAVILY_API_KEY", True, lat, f"results={n}", http=code)
    msg = ""
    if isinstance(data, dict):
        msg = str(data.get("error") or data.get("detail") or data)[:120]
    return _result("TAVILY_API_KEY", False, lat, msg, http=code)


def test_jina() -> Dict[str, Any]:
    key = (get_secret("JINA_API_KEY", "") or "").strip()
    if not key or "PLACEHOLDER" in key:
        return _result("JINA_API_KEY", False, -1, "missing/placeholder")
    payload = {
        "model": get_secret("JINA_EMBED_MODEL", "") or "jina-embeddings-v3",
        "input": ["hi"],
    }
    body = json.dumps(payload).encode("utf-8")
    code, data, lat = _http(
        "https://api.jina.ai/v1/embeddings",
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        body=body,
    )
    if code == 200 and isinstance(data, dict):
        items = data.get("data") or []
        usage = data.get("usage") or {}
        dim = len((items[0].get("embedding") if items else []) or [])
        return _result(
            "JINA_API_KEY",
            True,
            lat,
            f"dim={dim} tok={usage.get('total_tokens', '?')}",
            http=code,
        )
    msg = ""
    if isinstance(data, dict):
        msg = str(data.get("detail") or data.get("error") or data)[:120]
    return _result("JINA_API_KEY", False, lat, msg, http=code)


# ── 主流程 ──
def run_all() -> Dict[str, Any]:
    get_tang_gov_root()  # 確保 .env 載入
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows: List[Dict[str, Any]] = []
    for fn, group in (
        (test_telegram, "通訊"),
        (test_groq, "大腦"),
        (test_qwen, "大腦"),
        (test_nvidia, "大腦"),
        (test_firecrawl, "偵察"),
        (test_tavily, "偵察"),
        (test_jina, "偵察"),
    ):
        r = fn()
        r["group"] = group
        rows.append(r)

    ok_count = sum(1 for r in rows if r["status"] == "OK")
    summary = {
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok_count": ok_count,
        "total": len(rows),
        "rows": rows,
    }
    # 落盤至 reports
    try:
        reports_dir = resolve_agent_output_path(None, "06_Exports_Output", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        out_path = os.path.join(
            reports_dir,
            f"key_test_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json",
        )
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        summary["report_path"] = out_path
    except Exception as e:  # noqa: BLE001
        summary["report_path_error"] = str(e)
    return summary


def render_table(rows: List[Dict[str, Any]]) -> str:
    """ASCII 表格（適合 Telegram 純文字）。"""
    headers = ("API", "狀態", "延遲(ms)", "備註")
    data = [(r["api"], r["status"], str(r["latency_ms"]), (r["note"] or "")[:80]) for r in rows]
    widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], _wlen(cell))
    sep = "+".join("-" * (w + 2) for w in widths)
    sep = f"+{sep}+"
    def fmt_row(row: Tuple[str, ...]) -> str:
        cells = [_pad(row[i], widths[i]) for i in range(len(row))]
        return "| " + " | ".join(cells) + " |"
    out_lines = [sep, fmt_row(headers), sep]
    for row in data:
        out_lines.append(fmt_row(row))
    out_lines.append(sep)
    return "\n".join(out_lines)


def _wlen(s: str) -> int:
    """中文寬字符 +1（粗略）。"""
    n = 0
    for ch in s:
        n += 2 if ord(ch) > 127 else 1
    return n


def _pad(s: str, w: int) -> str:
    return s + " " * max(0, w - _wlen(s))


def main() -> int:
    summary = run_all()
    table = render_table(summary["rows"])
    print(table)
    print()
    print(json.dumps(
        {
            "ok_count": summary["ok_count"],
            "total": summary["total"],
            "report_path": summary.get("report_path"),
            "rows": [
                {
                    "api": r["api"],
                    "status": r["status"],
                    "latency_ms": r["latency_ms"],
                    "http": r["http"],
                    "note": r["note"],
                }
                for r in summary["rows"]
            ],
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
