# GroqHybridRecovery_Agent.py — 混合雲·批量修復（本地 + Groq）
# 掃描 06_Exports_Output/Archive/format_error（含 unrecoverable）內非空 .json；
# 本地解碼／啟發式 → 失敗則 Groq 語義校準；成功者寫入 C2_核心知識庫。
# 選項 A：格式問題僅 json_format_warning，不寫 Failed（避免門下省誤封駁）。

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

_workflows = os.path.normpath(os.path.join(_here, "..", "04_Workflows"))
if _workflows not in sys.path:
    sys.path.insert(0, _workflows)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from gov_paths import get_secret, get_tang_gov_root, resolve_agent_output_path  # type: ignore
from Recovery_Agent import ENCODING_FALLBACKS  # type: ignore

import _tang_http  # type: ignore


def reset_groq_wave_usage() -> None:
    """委託 _tang_http：新一輪 Wave 前清空 usage 累計。"""
    _tang_http.reset_groq_wave_usage()


def format_groq_quota_telegram_suffix() -> Tuple[str, str]:
    """（今日彈藥餘裕, 本次精煉花費）兩行戰報文字。"""
    return _tang_http.format_groq_quota_telegram_suffix()


GROQ_URL_DEFAULT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL_DEFAULT = "llama-3.3-70b-versatile"


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


def _http_json(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    timeout: int = 120,
) -> Tuple[int, Any]:
    """Groq Chat POST → _tang_http.json_request_dual_ssl（智慧撥彈）；其餘維持舊 urllib 雙 SSL。"""
    final_headers: Dict[str, str] = {"User-Agent": DEFAULT_UA, "Accept": "application/json"}
    if headers:
        final_headers.update(headers)

    if body and "api.groq.com" in url and method.upper() == "POST":
        return _tang_http.json_request_dual_ssl(
            url,
            method=method,
            headers=final_headers,
            body=body,
            timeout=timeout,
            user_agent=DEFAULT_UA,
            groq_chat_failover=True,
        )

    last_http_err: Optional[BaseException] = None
    for ctx in (_ssl_ctx(), ssl._create_unverified_context()):  # type: ignore[attr-defined]
        try:
            req = urllib.request.Request(url, data=body, method=method)
            for k, v in final_headers.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return resp.getcode(), json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            try:
                parsed = json.loads(err_body) if err_body.strip() else {}
            except json.JSONDecodeError:
                parsed = {"raw": err_body[:2000]}
            return e.code, parsed
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, json.JSONDecodeError) as e:
            last_http_err = e
            continue
    return 0, {"error": repr(last_http_err)}


def _decode_raw(raw: bytes) -> Tuple[Optional[str], Optional[str]]:
    for enc in ENCODING_FALLBACKS:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
        except LookupError:
            continue
    return None, None


def _try_parse_json_text(text: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(text), "raw"
    except json.JSONDecodeError:
        pass
    cleaned = text.lstrip("\ufeff").strip()
    if cleaned != text:
        try:
            return json.loads(cleaned), "stripped"
        except json.JSONDecodeError:
            pass
    if cleaned:
        for opener, closer in (("{", "}"), ("[", "]")):
            start = cleaned.find(opener)
            end = cleaned.rfind(closer)
            if start != -1 and end > start:
                candidate = cleaned[start : end + 1]
                try:
                    return json.loads(candidate), f"substring_{opener}{closer}"
                except json.JSONDecodeError:
                    continue
    return None, None


def _try_kit_line_json(text: str) -> Tuple[Optional[Any], Optional[str]]:
    """Omniverse kit catalog：每行前綴非 JSON，由首個 '{' 起截斷為單一物件。"""
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        i = s.find("{")
        if i == -1:
            continue
        cand = s[i:]
        try:
            return json.loads(cand), "kit_line_prefix"
        except json.JSONDecodeError:
            continue
    return None, None


def _extract_json_from_llm(content: str) -> Optional[Any]:
    s = content.strip()
    for fence in ("```json", "```"):
        if fence in s:
            parts = s.split(fence)
            for p in parts:
                chunk = p.strip()
                if chunk.startswith("json"):
                    chunk = chunk[4:].lstrip()
                if chunk.endswith("```"):
                    chunk = chunk[:-3].strip()
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    continue
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    obj, _ = _try_parse_json_text(s)
    return obj


def _try_json5(text: str) -> Tuple[Optional[Any], Optional[str]]:
    """JSONC / JSON5（VS Code tsconfig、argv.json 等）。"""
    try:
        import json5  # type: ignore
    except ImportError:
        return None, None
    try:
        return json5.loads(text), "json5"
    except Exception:  # noqa: BLE001
        return None, None


class GroqHybridRecovery_Agent:
    AGENT_NAME = "GroqHybridRecovery_Agent"
    DEPARTMENT = "混合雲"

    def __init__(self, *, dest_root: Optional[str] = None) -> None:
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        self.archive_dir = resolve_agent_output_path(self.dest_root, "06_Exports_Output", "archive")
        self.format_error_root = os.path.join(self.archive_dir, "format_error")
        self.c2_dir = resolve_agent_output_path(self.dest_root, "03_RAG_Database", "c2_core")
        os.makedirs(self.c2_dir, exist_ok=True)

    def _list_targets(self) -> List[str]:
        files: List[str] = []
        if not os.path.isdir(self.format_error_root):
            return files
        skip = {"metadata_index.json", ".department.txt"}
        for dp, _, fns in os.walk(self.format_error_root):
            for fn in fns:
                if fn in skip or fn.startswith("."):
                    continue
                if not fn.lower().endswith(".json"):
                    continue
                fp = os.path.join(dp, fn)
                try:
                    if os.path.getsize(fp) > 0:
                        files.append(fp)
                except OSError:
                    continue
        files.sort()
        return files

    @staticmethod
    def _unique_dest(dest: str) -> str:
        if not os.path.exists(dest):
            return dest
        base, ext = os.path.splitext(dest)
        n = 1
        while os.path.exists(f"{base}__hyb{n:03d}{ext}"):
            n += 1
        return f"{base}__hyb{n:03d}{ext}"

    def _groq_extract_json(self, raw_text: str, *, basename: str) -> Tuple[Optional[Any], Optional[str]]:
        key = get_secret("GROQ_API_KEY", "") or ""
        if not key or "PLACEHOLDER" in key:
            return None, "groq_key_missing"
        model = get_secret("GROQ_MODEL", "") or GROQ_MODEL_DEFAULT
        url = get_secret("GROQ_API_URL", "") or GROQ_URL_DEFAULT
        max_chars = int(get_secret("GROQ_MAX_INPUT_CHARS", "") or "28000")
        snippet = raw_text if len(raw_text) <= max_chars else raw_text[:max_chars] + "\n...[truncated]"
        system = (
            "You repair corrupted or prefixed JSON-like text. "
            "Return exactly ONE valid JSON value (object or array) using UTF-8 semantics. "
            "If the input is a kit/extension catalog line with a non-JSON prefix before '{', "
            "extract only the JSON object starting at the first '{'. "
            "If multiple JSON objects exist, return the first complete one. "
            "Output ONLY raw JSON text with no markdown fences and no commentary."
        )
        user = f"Filename hint: {basename}\n\n---BEGIN TEXT---\n{snippet}\n---END TEXT---"
        payload = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        }
        code, data = _http_json(url, method="POST", headers=headers, body=body, timeout=120)
        if code != 200:
            return None, f"groq_http_{code}"
        try:
            choices = data.get("choices") or []
            msg = (choices[0].get("message") or {}) if choices else {}
            content = str(msg.get("content") or "")
        except Exception:  # noqa: BLE001
            return None, "groq_bad_response"
        obj = _extract_json_from_llm(content)
        if obj is None:
            return None, "groq_parse_failed"
        return obj, "groq_ok"

    def run_batch(self) -> Dict[str, Any]:
        self.agent.set_status(AgentStatus.Running.value, reason="hybrid_batch_start")
        targets = self._list_targets()
        self.agent.log_event(event="hybrid_batch_start", target_count=len(targets))

        groq_delay = float(get_secret("GROQ_REQUEST_DELAY_SEC", "") or "0.35")

        ok_local = 0
        ok_groq = 0
        failed = 0
        groq_skipped = 0

        for fp in targets:
            name = os.path.basename(fp)
            try:
                with open(fp, "rb") as bf:
                    raw = bf.read()
            except OSError as e:
                self.agent.log_event(event="json_format_warning", path=fp, error=f"read_failed:{e}")
                failed += 1
                continue

            text, enc = _decode_raw(raw)
            if text is None:
                self.agent.log_event(event="json_format_warning", path=fp, error="decode_failed")
                failed += 1
                continue

            obj: Optional[Any] = None
            strat: Optional[str] = None

            obj, strat = _try_parse_json_text(text)
            if obj is None:
                obj, strat = _try_kit_line_json(text)
            if obj is None:
                obj, strat = _try_json5(text)

            used_groq = False
            if obj is None:
                obj, groq_reason = self._groq_extract_json(text, basename=name)
                strat = groq_reason
                used_groq = obj is not None
                if used_groq:
                    time.sleep(groq_delay)
                else:
                    if groq_reason == "groq_key_missing":
                        groq_skipped += 1
                    self.agent.log_event(
                        event="json_format_warning",
                        path=fp,
                        encoding=enc,
                        groq_reason=groq_reason,
                    )

            if obj is None:
                failed += 1
                continue

            dst = self._unique_dest(os.path.join(self.c2_dir, name))
            try:
                with open(dst, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(obj, f, ensure_ascii=False, indent=2)
                os.remove(fp)
                if used_groq:
                    ok_groq += 1
                else:
                    ok_local += 1
                self.agent.log_event(
                    event="hybrid_recovered",
                    path=fp,
                    dst=dst,
                    strategy=strat,
                    encoding=enc,
                    via_groq=used_groq,
                )
            except OSError as e:
                self.agent.log_event(event="json_format_warning", path=fp, error=f"write_failed:{e}")
                failed += 1

        total = len(targets)
        repaired = ok_local + ok_groq
        rate = round((repaired / total), 4) if total else 0.0
        self.agent.log_event(
            event="hybrid_batch_done",
            target_count=total,
            ok_local=ok_local,
            ok_groq=ok_groq,
            failed=failed,
            groq_skipped=groq_skipped,
            success_rate=rate,
        )
        self.agent.set_status(AgentStatus.Success.value, reason="hybrid_batch_complete")
        return {
            "run_id": self.agent.run_id,
            "target_count": total,
            "ok_local": ok_local,
            "ok_groq": ok_groq,
            "failed": failed,
            "groq_skipped": groq_skipped,
            "success_rate": rate,
            "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
