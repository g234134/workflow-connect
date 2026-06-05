# Code_Cleaner_Throttled_Agent.py — 兵部·全量清剿（節流模式）
# SHA256 內容去重 · 0-byte / 低價值暫存排除 · 500 件一波 · 狀態持久化 ·
# Groq 僅限 (.py/.php/.json*) 且本地 json+json5+啟發式全敗後 · 連敗不中斷（容錯跳過） ·
# 失敗落 C3_Logs · Status.json 累計 total_failed_count · Telegram 批次／結束戰報。

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from gov_paths import (  # type: ignore
    get_secret,
    get_tang_gov_root,
    resolve_agent_output_path,
)
from Code_Cleaner_Agent import (  # type: ignore
    PATH_BLACKLIST_DIRS,
    SKIP_EXT,
    _decode,
    _detect_type,
    _summarize,
)
from GroqHybridRecovery_Agent import (  # type: ignore
    DEFAULT_UA,
    GROQ_MODEL_DEFAULT,
    GROQ_URL_DEFAULT,
    _extract_json_from_llm,
    _http_json,
    _try_json5,
    _try_kit_line_json,
    _try_parse_json_text,
)
from Recovery_Agent import ENCODING_FALLBACKS  # type: ignore
import pipeline_meta  # type: ignore  # 碼源清洗戰役 v2: jobs+events SDK

# ---- Langfuse（可選依賴；版本差異收斂於 _lf_*，不在 run() 散落判斷）----
try:  # pragma: no cover - 環境未必安裝 langfuse
    from langfuse import get_client as _langfuse_get_client  # type: ignore
except ImportError:  # pragma: no cover
    _langfuse_get_client = None  # type: ignore[misc, assignment]

try:  # pragma: no cover
    from langfuse import Langfuse as _LangfuseClass  # type: ignore
except ImportError:  # pragma: no cover
    _LangfuseClass = None  # type: ignore[misc, assignment]


# ---- code_cleaning_pipeline_v2 metadata 常量（README §2 對應） ----
PIPELINE_NAME = "code_cleaning_pipeline_v2"
PIPELINE_INPUT_ROOT = "05_Temp_Cache/raw_inbound"
PIPELINE_CLEANED_OUTPUT_ROOT = "05_Temp_Cache/cleaned_full"
PIPELINE_FAILED_OUTPUT_ROOT = "06_Exports_Output/Archive/format_error"


THROTTLE_SKIP_EXT = SKIP_EXT | {
    ".tmp", ".temp", ".bak", ".swp", ".swo", ".orig", ".rej", ".cache",
}

LOW_VALUE_FILENAMES = {
    "thumbs.db",
    "desktop.ini",
    ".ds_store",
}

PATH_BLACKLIST_EXTRA = PATH_BLACKLIST_DIRS | {"cleaned_full"}

IMPORTANT_EXT_FOR_GROQ = {".py", ".php", ".json", ".jsonc", ".json5"}

MAX_FILE_BYTES = int(os.environ.get("THROTTLE_MAX_FILE_BYTES", str(8 * 1024 * 1024)))
WAVE_DEFAULT = 500
GROQ_DELAY_SEC = float(os.environ.get("GROQ_REQUEST_DELAY_SEC", "") or "0.35")
TELEGRAM_FAILURE_BATCH = int(os.environ.get("THROTTLE_TELEGRAM_FAIL_BATCH", "") or "50")


def _lf_env_truthy(name: str, default: str = "true") -> bool:
    raw = (os.environ.get(name) if name else None) or default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _lf_langfuse_import_ok() -> bool:
    return _langfuse_get_client is not None or _LangfuseClass is not None


def _lf_credentials_present() -> bool:
    pub = (os.environ.get("LANGFUSE_PUBLIC_KEY") or "").strip()
    sec = (os.environ.get("LANGFUSE_SECRET_KEY") or "").strip()
    return bool(pub and sec)


def _lf_prepare_sdk_host_env() -> None:
    """LANGFUSE_HOST 為主；未設時退回 LANGFUSE_BASE_URL。僅補齊 SDK 常讀之變數，不印值。"""
    host = (os.environ.get("LANGFUSE_HOST") or "").strip()
    base = (os.environ.get("LANGFUSE_BASE_URL") or "").strip()
    resolved = host or base
    if not resolved:
        return
    if not host and base:
        os.environ["LANGFUSE_HOST"] = base
    if not (os.environ.get("LANGFUSE_BASE_URL") or "").strip():
        os.environ["LANGFUSE_BASE_URL"] = resolved


def _lf_trace_enabled() -> bool:
    if not _lf_langfuse_import_ok():
        return False
    if not _lf_env_truthy("LANGFUSE_ENABLED", default="true"):
        return False
    return _lf_credentials_present()


def _lf_acquire_client() -> Any:
    """回傳 Langfuse client singleton 或建構實例；失敗回 None。"""
    if not _lf_trace_enabled():
        return None
    try:
        _lf_prepare_sdk_host_env()
    except Exception:  # noqa: BLE001
        pass
    try:
        if _langfuse_get_client is not None:
            return _langfuse_get_client()
    except Exception:  # noqa: BLE001
        pass
    try:
        if _LangfuseClass is not None:
            return _LangfuseClass()
    except Exception:  # noqa: BLE001
        return None
    return None


def _lf_root_observation_cm(
    client: Any,
    *,
    name: str,
    metadata: Dict[str, Any],
    session_id: Optional[str],
):
    """回傳可作為 with 物件的 observation context manager；API 不支援時回 nullcontext。"""
    if client is None:
        return contextlib.nullcontext(None)
    try:
        cm_factory = getattr(client, "start_as_current_observation", None)
        if callable(cm_factory):
            try:
                cm = cm_factory(
                    as_type="span",
                    name=name,
                    metadata=metadata,
                    session_id=session_id,
                )
            except TypeError:
                try:
                    cm = cm_factory(as_type="span", name=name, metadata=metadata)
                except TypeError:
                    cm = cm_factory(as_type="span", name=name)
            if cm is None or not (hasattr(cm, "__enter__") and hasattr(cm, "__exit__")):
                return contextlib.nullcontext(None)
            return cm
    except Exception:  # noqa: BLE001
        pass
    # 極舊版：若存在 trace() 且回傳 context manager
    try:
        tr_factory = getattr(client, "trace", None)
        if callable(tr_factory):
            try:
                cm = tr_factory(name=name, metadata=metadata, session_id=session_id)
            except TypeError:
                cm = tr_factory(name=name, metadata=metadata)
            if cm is None or not (hasattr(cm, "__enter__") and hasattr(cm, "__exit__")):
                return contextlib.nullcontext(None)
            return cm
    except Exception:  # noqa: BLE001
        pass
    return contextlib.nullcontext(None)


def _lf_finalize(span: Any, *, result: Optional[Dict[str, Any]], err: Optional[BaseException]) -> None:
    if span is None:
        return
    try:
        if err is not None:
            msg = f"{type(err).__name__}: {err}"
            upd = getattr(span, "update", None)
            if callable(upd):
                try:
                    upd(status_message=msg[:500], level="ERROR")
                except TypeError:
                    upd(output={"error": type(err).__name__, "message": msg[:500]})
        elif result is not None:
            slim = {
                k: result.get(k)
                for k in (
                    "run_id",
                    "stop_reason",
                    "paused_wave_limit",
                    "total_unique_processed",
                    "total_failed_count",
                    "aborted",
                )
                if k in result
            }
            upd = getattr(span, "update", None)
            if callable(upd):
                try:
                    upd(output=slim)
                except TypeError:
                    upd(metadata={"result_summary": slim})
    except Exception:  # noqa: BLE001
        pass


# Langfuse root observation 名稱（與 pipeline 常數區分，便於 UI 篩選）
_LF_ROOT_TRACE_NAME = "code_cleaning_pipeline_v2.throttled_run"


def _lf_flush_shutdown(client: Any) -> None:
    if client is None:
        return
    try:
        flush = getattr(client, "flush", None)
        if callable(flush):
            flush()
    except Exception:  # noqa: BLE001
        pass
    try:
        shutdown = getattr(client, "shutdown", None)
        if callable(shutdown):
            shutdown()
    except Exception:  # noqa: BLE001
        pass


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _decode_full(raw: bytes) -> Tuple[Optional[str], Optional[str]]:
    """優先 Recovery 全編碼鏈，其次 Code_Cleaner 簡鏈。"""
    for enc in ENCODING_FALLBACKS:
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return _decode(raw)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _groq_json_repair(text: str, basename: str) -> Tuple[Optional[Any], str]:
    key = get_secret("GROQ_API_KEY", "") or ""
    if not key or "PLACEHOLDER" in key:
        return None, "groq_key_missing"
    model = get_secret("GROQ_MODEL", "") or GROQ_MODEL_DEFAULT
    url = get_secret("GROQ_API_URL", "") or GROQ_URL_DEFAULT
    max_chars = int(get_secret("GROQ_MAX_INPUT_CHARS", "") or "16000")
    snippet = text if len(text) <= max_chars else text[:max_chars] + "\n...[truncated]"
    system = (
        "You repair corrupted JSON / JSONC / JSON5 / kit-catalog lines. "
        "Return exactly ONE valid JSON value (object or array). "
        "If a line has non-JSON prefix before '{', extract only the first complete JSON object from that line. "
        "Output ONLY raw JSON with no markdown fences."
    )
    user = f"Filename: {basename}\n\n---BEGIN---\n{snippet}\n---END---"
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    code, data = _http_json(url, method="POST", headers=headers, body=body, timeout=120)
    if code != 200:
        return None, f"groq_http_{code}"
    try:
        choices = data.get("choices") or []
        content = str((choices[0].get("message") or {}).get("content") or "")
    except Exception:  # noqa: BLE001
        return None, "groq_bad_response"
    obj = _extract_json_from_llm(content)
    if obj is None:
        return None, "groq_parse_failed"
    return obj, "groq_ok"


def _groq_recover_decode_fail(raw: bytes, basename: str, lang: str) -> Tuple[Optional[str], str]:
    """解碼全敗時，將 Latin-1 視圖送 Groq，要求回 JSON {recovered_utf8_text, notes}。"""
    key = get_secret("GROQ_API_KEY", "") or ""
    if not key or "PLACEHOLDER" in key:
        return None, "groq_key_missing"
    model = get_secret("GROQ_MODEL", "") or GROQ_MODEL_DEFAULT
    url = get_secret("GROQ_API_URL", "") or GROQ_URL_DEFAULT
    snippet = raw.decode("latin-1", errors="replace")[:12000]
    system = (
        "The user has a source file that failed all UTF encodings. "
        "Input is Latin-1 representation of raw bytes. "
        "Return ONE JSON object with keys: recovered_utf8_text (string), notes (string). "
        "recovered_utf8_text must be valid UTF-8 content as if fixing mojibake; "
        "if impossible, return best-effort partial recovery. "
        "Output ONLY raw JSON, no markdown."
    )
    user = f"Language hint: {lang}\nFilename: {basename}\n\n---BEGIN---\n{snippet}\n---END---"
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    code, data = _http_json(url, method="POST", headers=headers, body=body, timeout=120)
    if code != 200:
        return None, f"groq_http_{code}"
    try:
        choices = data.get("choices") or []
        content = str((choices[0].get("message") or {}).get("content") or "")
    except Exception:  # noqa: BLE001
        return None, "groq_bad_response"
    obj = _extract_json_from_llm(content)
    if not isinstance(obj, dict):
        return None, "groq_not_object"
    txt = obj.get("recovered_utf8_text")
    if not isinstance(txt, str):
        return None, "groq_no_recovered_text"
    return txt, "groq_decode_recover_ok"


def _telegram_alert(
    text: str,
    *,
    reply_markup: Optional[Dict[str, Any]] = None,
) -> None:
    token = (get_secret("TELEGRAM_BOT_TOKEN", "") or "").strip()
    chat_id = (get_secret("TELEGRAM_CHAT_ID", "") or "").strip()
    if not token or not chat_id:
        return
    payload: Dict[str, Any] = {"chat_id": chat_id, "text": text[:3900]}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": DEFAULT_UA}
    ctx = ssl._create_unverified_context()  # type: ignore[attr-defined]
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            r.read()
    except Exception:  # noqa: BLE001
        pass


def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:100]


def _large_skip_signature(fp: str, sz: int, mtime_ns: int) -> str:
    key = f"{os.path.normcase(os.path.normpath(fp))}|{sz}|{mtime_ns}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _failure_bucket(rec: Dict[str, Any]) -> str:
    warns = rec.get("warnings") or []
    if any(str(w).startswith("oversized_exceeds_limit") for w in warns):
        return "oversized"
    if not warns:
        return "unknown"
    head = str(warns[0])
    if head.startswith("groq_after_decode_recover"):
        return "post_groq_summary_failed"
    if head.startswith("groq_http_"):
        return "groq_http_error"
    if "groq_json_failed" in head or "groq_json_after_decode_fail" in head:
        return "groq_json_repair_failed"
    if "groq_decode_recover_failed" in head:
        return "groq_decode_recover_failed"
    if head.startswith("json_local_repair_failed"):
        return "json_corrupt_no_cloud"
    if head.startswith("decode_failed"):
        return "decode_unknown_encoding"
    if head.startswith("summary_error"):
        return "local_summary_failed"
    if "groq_key_missing" in head:
        return "groq_key_missing"
    return "other"


def _failure_analysis_lines(counter: Counter[str]) -> List[str]:
    explain = {
        "oversized": "超過單檔容量上限，未進行完整解析（常為日誌／打包片段／資產誤標副檔名）",
        "json_corrupt_no_cloud": "副檔為 JSON 家族但本地+json5 無法解析，且副檔不在 Groq 白名單（節流故意不送雲）",
        "groq_json_repair_failed": "JSON／JSON5／啟發式皆失敗且 Groq 無法還原結構（API 錯誤或語義過碎）",
        "groq_decode_recover_failed": "原始位元組無法本地解碼，Groq 亦無法還原為可用 UTF-8 文字",
        "groq_http_error": "Groq HTTP 非 200（配額、網路或 Cloudflare）",
        "decode_unknown_encoding": "所有本地編碼鏈解碼失敗，可能為二進位、加密或碎裂編碼",
        "post_groq_summary_failed": "Groq 已還原文字，但後續摘要／結構抽取仍失敗（內容可能仍異常）",
        "local_summary_failed": "解碼成功但摘要／結構抽取例外（內容異常或正則邊界）",
        "groq_key_missing": "未設定有效 GROQ_API_KEY，雲端修復跳過",
        "unknown": "原因未分類",
        "other": "其他警告組合",
    }
    lines = []
    for k, n in counter.most_common():
        hint = explain.get(k, explain["other"])
        lines.append(f"· {k}: {n} 件 — {hint}")
    return lines


class Code_Cleaner_Throttled_Agent:
    AGENT_NAME = "Code_Cleaner_Throttled_Agent"
    DEPARTMENT = "兵部"

    def __init__(
        self,
        *,
        dest_root: Optional[str] = None,
        wave_size: int = WAVE_DEFAULT,
        max_waves: int = 0,
    ) -> None:
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.wave_size = int(wave_size)
        self.max_waves = int(max_waves)
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        workflows_dir = resolve_agent_output_path(self.dest_root, "04_Workflows")
        self.state_path = os.path.join(workflows_dir, ".code_cleaner_throttle_state.json")
        self.hash_log_path = os.path.join(workflows_dir, ".code_cleaner_throttle_hashes.txt")
        self.large_skip_path = os.path.join(workflows_dir, ".code_cleaner_throttle_large_skips.txt")
        self.out_dir = resolve_agent_output_path(self.dest_root, "05_Temp_Cache", "cleaned_full")
        self.c3_failed_dir = os.path.join(
            resolve_agent_output_path(self.dest_root, "03_RAG_Database", "c3_logs"),
            "Code_Cleaner_Throttle",
        )
        os.makedirs(self.out_dir, exist_ok=True)
        os.makedirs(self.c3_failed_dir, exist_ok=True)

        self._hash_done: Set[str] = set()
        self._large_skip_sigs: Set[str] = set()
        self._load_hashes()
        self._load_large_skips()

    def _load_hashes(self) -> None:
        if not os.path.isfile(self.hash_log_path):
            return
        try:
            with open(self.hash_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    h = line.strip()
                    if len(h) == 64:
                        self._hash_done.add(h)
        except OSError:
            pass

    def _load_large_skips(self) -> None:
        if not os.path.isfile(self.large_skip_path):
            return
        try:
            with open(self.large_skip_path, "r", encoding="utf-8") as f:
                for line in f:
                    h = line.strip()
                    if len(h) == 64:
                        self._large_skip_sigs.add(h)
        except OSError:
            pass

    def _append_large_skip_sig(self, sig: str) -> None:
        self._large_skip_sigs.add(sig)
        with open(self.large_skip_path, "a", encoding="utf-8") as f:
            f.write(sig + "\n")

    def _log_failed_c3(
        self,
        *,
        fp: str,
        rec: Dict[str, Any],
        content_sha256: Optional[str],
        size_bytes: Optional[int],
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        bucket = _failure_bucket(rec)
        row = {
            "ts": _utc_iso(),
            "run_id": self.agent.run_id,
            "agent": self.AGENT_NAME,
            "status": "failed",
            "failure_bucket": bucket,
            "source_path": fp,
            "content_sha256": content_sha256,
            "size_bytes": size_bytes,
            "original_type": rec.get("original_type"),
            "extension": rec.get("extension"),
            "encoding": rec.get("encoding"),
            "groq_used": rec.get("groq_used"),
            "groq_reason": rec.get("groq_reason"),
            "warnings": rec.get("warnings"),
            "extra": extra or {},
        }
        path = os.path.join(self.c3_failed_dir, "failed_events.jsonl")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError as e:
            self.agent.log_event(event="c3_failed_log_write_error", path=path, error=str(e))

    def _append_hash(self, h: str) -> None:
        self._hash_done.add(h)
        with open(self.hash_log_path, "a", encoding="utf-8") as f:
            f.write(h + "\n")

    def _load_json_state(self) -> Dict[str, Any]:
        if not os.path.isfile(self.state_path):
            return {}
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {}

    def _save_json_state(self, payload: Dict[str, Any]) -> None:
        payload["updated_at"] = _utc_iso()
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _patch_status(self, throttle_block: Dict[str, Any]) -> None:
        sp = os.path.join(resolve_agent_output_path(self.dest_root, "04_Workflows"), "Status.json")
        data: Dict[str, Any] = {}
        if os.path.isfile(sp):
            try:
                with open(sp, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:  # noqa: BLE001
                data = {}
        data["code_cleaner_throttle"] = throttle_block
        data["updated_at"] = _utc_iso()
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _eligible_path(self, fp: str) -> bool:
        norm = os.path.normpath(fp)
        parts = set(norm.split(os.sep))
        if parts & PATH_BLACKLIST_EXTRA:
            return False
        base = os.path.basename(fp).lower()
        if base in LOW_VALUE_FILENAMES:
            return False
        if base.startswith("~$"):
            return False
        ext = os.path.splitext(base)[1]
        if ext in THROTTLE_SKIP_EXT:
            return False
        if _detect_type(fp) == "unknown":
            return False
        return True

    def enumerate_sorted_paths(self) -> List[str]:
        paths: List[str] = []
        for dp, dns, fns in os.walk(self.dest_root):
            dns[:] = [d for d in dns if d not in PATH_BLACKLIST_EXTRA]
            for fn in fns:
                fp = os.path.join(dp, fn)
                if self._eligible_path(fp):
                    paths.append(fp)
        paths.sort()
        return paths

    def _local_json_repair(self, text: str) -> Tuple[Optional[Any], Optional[str]]:
        try:
            return json.loads(text), "json_std"
        except json.JSONDecodeError:
            pass
        obj, strat = _try_json5(text)
        if obj is not None:
            return obj, strat
        obj, strat = _try_parse_json_text(text)
        if obj is not None:
            return obj, strat
        obj, strat = _try_kit_line_json(text)
        if obj is not None:
            return obj, strat
        return None, None

    def _process_one(
        self,
        fp: str,
        raw: bytes,
        content_hash: str,
        *,
        allow_groq: bool,
        stats: Dict[str, int],
    ) -> Dict[str, Any]:
        name = os.path.basename(fp)
        ext = os.path.splitext(name)[1].lower()
        otype = _detect_type(fp)
        rec: Dict[str, Any] = {
            "source_path": fp,
            "name": name,
            "extension": ext,
            "original_type": otype,
            "size_bytes": len(raw),
            "content_sha256": content_hash,
            "encoding": None,
            "parse_strategy": None,
            "groq_used": False,
            "groq_reason": None,
            "clean_status": "ok",
            "warnings": [],
            "content_summary": {},
        }

        json_family = ext in (".json", ".jsonc", ".json5") or otype in ("json", "jsonc", "json5")

        text, enc = _decode_full(raw)
        rec["encoding"] = enc

        if text is None:
            # 解碼全敗
            if allow_groq and ext in (".py", ".php"):
                stats["groq_attempts"] += 1
                lang = "python" if ext == ".py" else "php"
                recovered, reason = _groq_recover_decode_fail(raw, name, lang)
                rec["groq_used"] = True
                rec["groq_reason"] = reason
                time.sleep(GROQ_DELAY_SEC)
                if recovered is None:
                    stats["groq_fail_streak"] += 1
                    rec["clean_status"] = "failed"
                    rec["warnings"].append(f"groq_decode_recover_failed:{reason}")
                    return rec
                stats["groq_fail_streak"] = 0
                stats["groq_success"] += 1
                text = recovered
                rec["encoding"] = "groq_recovered_utf8"
                try:
                    rec["content_summary"] = _summarize(otype, text)
                except Exception as e:  # noqa: BLE001
                    rec["clean_status"] = "failed"
                    rec["warnings"].append(f"groq_after_decode_recover:{e}")
                    rec["content_summary"] = {}
                return rec
            if allow_groq and json_family:
                stats["groq_attempts"] += 1
                latin = raw.decode("latin-1", errors="replace")
                obj2, reason = _groq_json_repair(latin, name)
                rec["groq_used"] = True
                rec["groq_reason"] = reason
                time.sleep(GROQ_DELAY_SEC)
                if obj2 is None:
                    stats["groq_fail_streak"] += 1
                    rec["clean_status"] = "failed"
                    rec["warnings"].append(f"groq_json_after_decode_fail:{reason}")
                    return rec
                stats["groq_fail_streak"] = 0
                stats["groq_success"] += 1
                rec["parse_strategy"] = reason
                rec["encoding"] = "groq_from_binary_view"
                rec["content_summary"] = {"json_normalized": True, "strategy": reason, "via_groq": True}
                rec["_parsed_json"] = obj2
                return rec
            rec["clean_status"] = "failed"
            rec["warnings"].append("decode_failed_no_groq_eligible")
            return rec

        # 解碼成功
        if json_family:
            obj, strat = self._local_json_repair(text)
            if obj is not None:
                rec["parse_strategy"] = strat
                rec["content_summary"] = {"json_normalized": True, "strategy": strat}
                return rec
            # 本地 JSON 全敗 → 僅重要後綴允許 Groq
            if allow_groq:
                stats["groq_attempts"] += 1
                obj2, reason = _groq_json_repair(text, name)
                rec["groq_used"] = True
                rec["groq_reason"] = reason
                time.sleep(GROQ_DELAY_SEC)
                if obj2 is None:
                    stats["groq_fail_streak"] += 1
                    rec["clean_status"] = "failed"
                    rec["warnings"].append(f"groq_json_failed:{reason}")
                    try:
                        rec["content_summary"] = _summarize(otype, text)
                    except Exception:  # noqa: BLE001
                        rec["content_summary"] = {}
                    return rec
                stats["groq_fail_streak"] = 0
                stats["groq_success"] += 1
                rec["parse_strategy"] = reason
                rec["content_summary"] = {"json_normalized": True, "strategy": reason, "via_groq": True}
                # 將 obj2 附加於輸出檔頂層由 run() 處理
                rec["_parsed_json"] = obj2
                return rec
            rec["clean_status"] = "failed"
            rec["warnings"].append("json_local_repair_failed_no_groq")
            try:
                rec["content_summary"] = _summarize(otype, text)
            except Exception:  # noqa: BLE001
                rec["content_summary"] = {}
            return rec

        # 非 JSON 家族：正常摘要
        try:
            rec["content_summary"] = _summarize(otype, text)
        except Exception as e:  # noqa: BLE001
            rec["clean_status"] = "failed"
            rec["warnings"].append(f"summary_error:{e}")
            rec["content_summary"] = {}
        return rec

    def run(self) -> Dict[str, Any]:
        """Public entry — wrapped with pipeline_meta.job_run (碼源清洗戰役 v2)。

        本 wrapper 唯一職責：開 job、寫 pipeline_started/finished/aborted、
        確保例外時 status='failed' + notes=exc。所有實際清洗邏輯延伸到
        `_run_inner()`（既有 run() 之 body，未動半行）。
        事件由 `_run_inner` 內部於 raw_scan / wave / format_error 等
        checkpoint 寫入；job_id 透過 `self._meta_job_id` 供內層存取。

        Langfuse：可選 root span（`_lf_*`）；失敗不影響主鏈；finally 安全 flush。
        """
        self.agent.set_status(AgentStatus.Running.value, reason="throttle_start")
        st = self._load_json_state()
        _meta_initial_wave = (int(st.get("total_wave_ticks", 0)) // self.wave_size) + 1
        _triggered_by = (
            (os.environ.get("TRIGGERED_BY") or os.environ.get("CODE_CLEANER_TRIGGERED_BY") or "manual").strip()
            or "manual"
        )
        lf_client = _lf_acquire_client()
        try:
            with pipeline_meta.job_run(
                pipeline_name=PIPELINE_NAME,
                run_id=self.agent.run_id,
                wave=_meta_initial_wave,
                input_root=PIPELINE_INPUT_ROOT,
                cleaned_output_root=PIPELINE_CLEANED_OUTPUT_ROOT,
                failed_output_root=PIPELINE_FAILED_OUTPUT_ROOT,
                triggered_by=_triggered_by,
                notes=f"wave_size={self.wave_size} max_waves={self.max_waves}",
            ) as _meta_job_id:
                lf_md: Dict[str, Any] = {
                    "pipeline_name": PIPELINE_NAME,
                    "run_id": self.agent.run_id,
                    "job_id": _meta_job_id,
                    "triggered_by": _triggered_by,
                    "agent_name": self.agent.agent_name,
                    "session_id": self.agent.run_id,
                }
                lf_cm = _lf_root_observation_cm(
                    lf_client,
                    name=_LF_ROOT_TRACE_NAME,
                    metadata=lf_md,
                    session_id=self.agent.run_id,
                )
                with lf_cm as _lf_span:
                    # 把 metadata 鉤子掛到 instance，給內層 _run_inner / closures 取用
                    self._meta_job_id = _meta_job_id
                    self._meta_initial_processed = int(st.get("total_unique_processed", 0))
                    self._meta_initial_failed = int(st.get("total_failed_count", 0))
                    self._meta_session_success_at_last_chk = 0
                    self._meta_session_failed_at_last_chk = 0
                    pipeline_meta.record_event(
                        job_id=_meta_job_id,
                        event_type="raw_scan_started",
                        message=f"dest_root={self.dest_root}",
                    )
                    try:
                        out = self._run_inner(st)
                    except BaseException as exc:
                        _lf_finalize(_lf_span, result=None, err=exc)
                        raise
                    else:
                        _lf_finalize(_lf_span, result=out, err=None)
                        return out
        finally:
            _lf_flush_shutdown(lf_client)

    def _run_inner(self, st: Dict[str, Any]) -> Dict[str, Any]:
        total_processed = int(st.get("total_unique_processed", 0))
        total_failed_count = int(st.get("total_failed_count", 0))
        dup_skip = int(st.get("total_duplicate_skipped", 0))
        zero_skip = int(st.get("total_zero_byte_skipped", 0))
        large_skip = int(st.get("total_large_skipped", 0))
        groq_attempts_total = int(st.get("groq_attempts_total", 0))
        groq_success_total = int(st.get("groq_success_total", 0))
        bucket_totals: Counter[str] = Counter(
            {str(k): int(v) for k, v in (st.get("failure_bucket_totals") or {}).items()}
        )
        total_wave_ticks = int(st.get("total_wave_ticks", total_processed + total_failed_count))

        stats = {
            "groq_attempts": 0,
            "groq_success": 0,
            "groq_fail_streak": int(st.get("last_groq_fail_streak", 0)),
        }

        paths = self.enumerate_sorted_paths()
        self.agent.log_event(event="throttle_scan_done", path_count=len(paths))
        # ---- pipeline_meta v2: 掃料完成事件 + 首波 wave_started ----
        pipeline_meta.record_event(
            job_id=self._meta_job_id,
            event_type="raw_scan_completed",
            detail_payload={"path_count": len(paths)},
        )
        pipeline_meta.update_job_counts(
            job_id=self._meta_job_id, total_files_seen=len(paths),
        )
        pipeline_meta.record_event(
            job_id=self._meta_job_id,
            event_type="wave_started",
            detail_payload={
                "wave": (int(st.get("total_wave_ticks", 0)) // self.wave_size) + 1,
                "wave_size": self.wave_size,
                "remaining_paths": len(paths),
            },
        )

        waves_finished_this_run = 0
        paused_wave_limit = False
        stop_reason = ""
        failures_since_telegram = 0
        failures_this_session = 0

        payload: Dict[str, Any] = {
            "run_id": self.agent.run_id,
            "last_wave_completed": total_wave_ticks // self.wave_size,
            "total_unique_processed": total_processed,
            "total_failed_count": total_failed_count,
            "failure_bucket_totals": dict(bucket_totals),
            "total_wave_ticks": total_wave_ticks,
            "total_duplicate_skipped": dup_skip,
            "total_zero_byte_skipped": zero_skip,
            "total_large_skipped": large_skip,
            "groq_attempts_total": groq_attempts_total,
            "groq_success_total": groq_success_total,
            "last_groq_fail_streak": stats["groq_fail_streak"],
            "out_dir": self.out_dir,
            "c3_failed_dir": self.c3_failed_dir,
            "stop_reason": "",
        }

        def build_throttle_status(*, running: bool, status: str) -> Dict[str, Any]:
            waves_done = total_wave_ticks // self.wave_size
            denom = max(1, total_processed + total_failed_count)
            damage_ratio = round(total_failed_count / denom, 6)
            return {
                "status": status,
                "run_id": self.agent.run_id,
                "waves_completed_full": waves_done,
                "wave_size": self.wave_size,
                "total_unique_processed": total_processed,
                "total_failed_count": total_failed_count,
                "damage_ratio_approx": damage_ratio,
                "failure_bucket_totals": dict(bucket_totals),
                "total_wave_ticks": total_wave_ticks,
                "duplicate_skipped": dup_skip,
                "zero_byte_skipped": zero_skip,
                "large_skipped": large_skip,
                "groq_fail_streak": stats["groq_fail_streak"],
                "groq_attempts_total": groq_attempts_total + stats["groq_attempts"],
                "groq_success_total": groq_success_total + stats["groq_success"],
                "paused_wave_limit": paused_wave_limit,
                "stop_reason": stop_reason,
                "telegram_failure_batch_size": TELEGRAM_FAILURE_BATCH,
                "aborted": False,
                "updated_at": _utc_iso(),
            }

        def persist_status(*, running: bool, status_override: Optional[str] = None) -> None:
            label = status_override or ("Running" if running else "Success")
            self._patch_status(build_throttle_status(running=running, status=label))

        def emit_telegram_digest(title: str) -> None:
            nonlocal failures_since_telegram
            denom = max(1, total_processed + total_failed_count)
            ratio = round(total_failed_count / denom, 4)
            analysis = "\n".join(_failure_analysis_lines(bucket_totals)[:14])
            if not analysis.strip():
                analysis = "（尚無分類累計）"
            body = (
                f"[節流清剿] {title}\n"
                f"Run_ID={self.agent.run_id}\n"
                f"成功 unique={total_processed} 失敗累計={total_failed_count} "
                f"損毀比約 {ratio}\n"
                f"Groq連敗 streak={stats['groq_fail_streak']}（不中斷；失敗已寫 C3_Logs）\n"
                f"--- 失敗主因分析 ---\n{analysis}"
            )
            _telegram_alert(body)
            failures_since_telegram = 0

        def maybe_telegram_batch() -> None:
            if failures_since_telegram >= TELEGRAM_FAILURE_BATCH:
                emit_telegram_digest(f"批次：新增失敗達 {TELEGRAM_FAILURE_BATCH} 筆")

        def checkpoint_wave_end() -> None:
            nonlocal groq_attempts_total, groq_success_total, waves_finished_this_run, payload
            groq_attempts_total += stats["groq_attempts"]
            groq_success_total += stats["groq_success"]
            stats["groq_attempts"] = 0
            stats["groq_success"] = 0
            waves_finished_this_run += 1
            payload = {
                "run_id": self.agent.run_id,
                "last_wave_completed": total_wave_ticks // self.wave_size,
                "total_unique_processed": total_processed,
                "total_failed_count": total_failed_count,
                "failure_bucket_totals": dict(bucket_totals),
                "total_wave_ticks": total_wave_ticks,
                "total_duplicate_skipped": dup_skip,
                "total_zero_byte_skipped": zero_skip,
                "total_large_skipped": large_skip,
                "groq_attempts_total": groq_attempts_total,
                "groq_success_total": groq_success_total,
                "last_groq_fail_streak": stats["groq_fail_streak"],
                "out_dir": self.out_dir,
                "c3_failed_dir": self.c3_failed_dir,
                "stop_reason": stop_reason,
            }
            self._save_json_state(payload)
            persist_status(running=True)
            # ---- pipeline_meta v2: wave_completed + 下一波 wave_started ----
            _wave_just_done = total_wave_ticks // self.wave_size
            _session_success_now = total_processed - self._meta_initial_processed
            _delta_success = _session_success_now - self._meta_session_success_at_last_chk
            _delta_failed = failures_this_session - self._meta_session_failed_at_last_chk
            self._meta_session_success_at_last_chk = _session_success_now
            self._meta_session_failed_at_last_chk = failures_this_session
            pipeline_meta.record_event(
                job_id=self._meta_job_id,
                event_type="wave_completed",
                detail_payload={
                    "wave": _wave_just_done,
                    "wave_size": self.wave_size,
                    "wave_success_delta": _delta_success,
                    "wave_failed_delta": _delta_failed,
                },
            )
            # opportunistic：若 after_consume_tick 隨即 break，此事件對應的下波不會
            # 真的開始；視為「意圖」記錄，下游消費端應結合 wave_completed 做配對。
            pipeline_meta.record_event(
                job_id=self._meta_job_id,
                event_type="wave_started",
                detail_payload={
                    "wave": _wave_just_done + 1,
                    "wave_size": self.wave_size,
                },
            )

        def after_consume_tick() -> bool:
            """每消耗一筆（成功 / 失敗 / 超大檔標記）後：Telegram 批次、波次檢查。True=應結束外層迴圈。"""
            nonlocal paused_wave_limit, stop_reason
            maybe_telegram_batch()
            if total_wave_ticks > 0 and total_wave_ticks % self.wave_size == 0:
                checkpoint_wave_end()
                if self.max_waves > 0 and waves_finished_this_run >= self.max_waves:
                    paused_wave_limit = True
                    stop_reason = "max_waves_reached"
                    return True
            return False

        for fp in paths:
            try:
                sz = os.path.getsize(fp)
            except OSError:
                continue
            if sz == 0:
                zero_skip += 1
                continue

            if sz > MAX_FILE_BYTES:
                try:
                    st_info = os.stat(fp)
                    st_ns = int(getattr(st_info, "st_mtime_ns", int(st_info.st_mtime * 1_000_000_000)))
                except OSError:
                    continue
                sig = _large_skip_signature(fp, sz, st_ns)
                if sig in self._large_skip_sigs:
                    continue
                ext = os.path.splitext(os.path.basename(fp))[1].lower()
                rec_big: Dict[str, Any] = {
                    "source_path": fp,
                    "name": os.path.basename(fp),
                    "extension": ext,
                    "original_type": _detect_type(fp),
                    "clean_status": "failed",
                    "warnings": [f"oversized_exceeds_limit:{sz}>{MAX_FILE_BYTES}"],
                    "encoding": None,
                    "groq_used": False,
                    "groq_reason": None,
                    "content_summary": {},
                    "parse_strategy": None,
                }
                self._log_failed_c3(
                    fp=fp,
                    rec=rec_big,
                    content_sha256=None,
                    size_bytes=sz,
                    extra={"max_bytes": MAX_FILE_BYTES},
                )
                # ---- pipeline_meta v2: format_error_archived（oversized 分支） ----
                pipeline_meta.record_event(
                    job_id=self._meta_job_id,
                    event_type="format_error_archived",
                    status_level="warning",
                    related_path=fp,
                    detail_payload={
                        "bucket": "oversized",
                        "size_bytes": sz,
                        "max_bytes": MAX_FILE_BYTES,
                    },
                )
                self._append_large_skip_sig(sig)
                total_failed_count += 1
                bucket_totals["oversized"] += 1
                failures_since_telegram += 1
                failures_this_session += 1
                total_wave_ticks += 1
                large_skip += 1
                if after_consume_tick():
                    break
                continue

            try:
                with open(fp, "rb") as f:
                    raw = f.read()
            except OSError:
                continue
            h = _sha256_bytes(raw)
            if h in self._hash_done:
                dup_skip += 1
                continue

            ext = os.path.splitext(os.path.basename(fp))[1].lower()
            allow_groq = ext in IMPORTANT_EXT_FOR_GROQ

            rec = self._process_one(fp, raw, h, allow_groq=allow_groq, stats=stats)

            if rec["clean_status"] == "failed":
                self._log_failed_c3(fp=fp, rec=rec, content_sha256=h, size_bytes=len(raw), extra={})
                _bucket = _failure_bucket(rec)
                # ---- pipeline_meta v2: format_error_archived（一般失敗分支） ----
                pipeline_meta.record_event(
                    job_id=self._meta_job_id,
                    event_type="format_error_archived",
                    status_level="warning",
                    related_path=fp,
                    detail_payload={
                        "bucket": _bucket,
                        "sha256_8": h[:16],
                        "groq_used": rec.get("groq_used"),
                        "groq_reason": rec.get("groq_reason"),
                    },
                )
                self._append_hash(h)
                total_failed_count += 1
                bucket_totals[_bucket] += 1
                failures_since_telegram += 1
                failures_this_session += 1
                total_wave_ticks += 1
                self.agent.log_event(
                    event="throttle_one_failed",
                    path=fp,
                    sha256=h[:16],
                    bucket=_bucket,
                )
                if after_consume_tick():
                    break
                continue

            wave_no = total_processed // self.wave_size + 1
            idx_in_wave = total_processed % self.wave_size + 1

            out_obj: Dict[str, Any] = {
                "schema_version": "2.0",
                "run_id": self.agent.run_id,
                "wave": wave_no,
                "idx_in_wave": idx_in_wave,
                "generated_at": _utc_iso(),
                **{k: v for k, v in rec.items() if not k.startswith("_")},
                "stored_path": "",
            }
            if "_parsed_json" in rec:
                out_obj["parsed_json"] = rec["_parsed_json"]

            stem = h[:16]
            safe = _sanitize_filename(rec["name"])
            out_name = f"full_w{wave_no:04d}_{idx_in_wave:03d}_{stem}_{safe}.json"
            out_path = os.path.join(self.out_dir, out_name)
            out_obj["stored_path"] = out_path
            # cleaned_full 索引：強制補齊內容指紋（與清剿時 raw bytes 一致）
            if not out_obj.get("content_sha256"):
                out_obj["content_sha256"] = h
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(out_obj, f, ensure_ascii=False, indent=2)
            except OSError as e:
                self.agent.log_event(event="throttle_write_failed", path=fp, error=str(e))
                continue

            self._append_hash(h)
            total_processed += 1
            total_wave_ticks += 1

            self.agent.log_event(
                event="throttle_one_done",
                path=fp,
                sha256=h[:16],
                groq_used=rec.get("groq_used"),
                clean_status=rec.get("clean_status"),
            )

            if after_consume_tick():
                break

        groq_attempts_total += stats["groq_attempts"]
        groq_success_total += stats["groq_success"]
        stats["groq_attempts"] = 0
        stats["groq_success"] = 0
        payload = {
            "run_id": self.agent.run_id,
            "last_wave_completed": total_wave_ticks // self.wave_size,
            "total_unique_processed": total_processed,
            "total_failed_count": total_failed_count,
            "failure_bucket_totals": dict(bucket_totals),
            "total_wave_ticks": total_wave_ticks,
            "total_duplicate_skipped": dup_skip,
            "total_zero_byte_skipped": zero_skip,
            "total_large_skipped": large_skip,
            "groq_attempts_total": groq_attempts_total,
            "groq_success_total": groq_success_total,
            "last_groq_fail_streak": stats["groq_fail_streak"],
            "out_dir": self.out_dir,
            "c3_failed_dir": self.c3_failed_dir,
            "stop_reason": stop_reason,
        }
        self._save_json_state(payload)

        final_status = "Paused" if paused_wave_limit else "Success"
        persist_status(running=False, status_override=final_status)

        if failures_this_session > 0:
            emit_telegram_digest("結束總結")
        else:
            denom = max(1, total_processed + total_failed_count)
            ratio = round(total_failed_count / denom, 4)
            _telegram_alert(
                f"[節流清剿] 結束\nRun_ID={self.agent.run_id}\n"
                f"本輪無新增失敗；成功累計 unique={total_processed} "
                f"失敗累計={total_failed_count} 損毀比約 {ratio}"
            )

        self.agent.log_event(
            event="throttle_done",
            aborted=False,
            paused_wave_limit=paused_wave_limit,
            reason=stop_reason,
            total_unique_processed=total_processed,
            total_failed_count=total_failed_count,
            failures_this_session=failures_this_session,
            duplicate_skipped=dup_skip,
        )
        self.agent.set_status(
            AgentStatus.Success.value,
            reason="throttle_wave_limit" if paused_wave_limit else "throttle_complete",
        )
        # ---- pipeline_meta v2: 最終 session 計數寫回 jobs 表 ----
        pipeline_meta.update_job_counts(
            job_id=self._meta_job_id,
            cleaned_success_count=(total_processed - self._meta_initial_processed),
            cleaned_failed_count=failures_this_session,
        )
        return {
            "run_id": self.agent.run_id,
            "aborted": False,
            "paused_wave_limit": paused_wave_limit,
            "stop_reason": stop_reason,
            "total_unique_processed": total_processed,
            "total_failed_count": total_failed_count,
            "failures_this_session": failures_this_session,
            "duplicate_skipped": dup_skip,
            "zero_byte_skipped": zero_skip,
            "large_skipped": large_skip,
            "out_dir": self.out_dir,
            "c3_failed_dir": self.c3_failed_dir,
            "state_path": self.state_path,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Code_Cleaner_Throttled_Agent")
    parser.add_argument("--wave-size", type=int, default=WAVE_DEFAULT)
    parser.add_argument("--max-waves", type=int, default=0, help="0=跑完佇列；>0 每累積 wave_size 筆消耗後暫停")
    args = parser.parse_args()
    get_tang_gov_root()
    out = Code_Cleaner_Throttled_Agent(wave_size=args.wave_size, max_waves=args.max_waves).run()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
