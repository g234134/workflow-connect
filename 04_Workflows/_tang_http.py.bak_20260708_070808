"""雙 SSL 降級 HTTP 客戶端（企業 MITM / 自簽鏈友善）。

v2.54：可選 Groq Chat Completions「智慧撥彈」（RPM/RPD/TPM 護欄 + 429 自動換模型）。
不含 gov_paths；repo root 由本檔位置推導（…/04_Workflows → 倉庫根）。
"""
from __future__ import annotations

import json
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Deque, Dict, Final, List, Optional, Tuple

UA_SMOKE: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 TangChariot/SmokeTest"
)
UA_TOOL: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 TangChariot/Doctor"
)

_REPO_ROOT: Optional[str] = None
_REGISTRY_CACHE: Optional[Dict[str, Any]] = None
_TRACKER_SINGLETON: Optional["GroqQuotaTracker"] = None
_TRACKER_LOCK = threading.Lock()

_WAVE_USAGE_LOCK = threading.Lock()
_WAVE_USAGE_ROWS: List[Dict[str, Any]] = []


def _repo_root() -> str:
    global _REPO_ROOT
    if _REPO_ROOT is None:
        _REPO_ROOT = str(Path(__file__).resolve().parent.parent)
    return _REPO_ROOT


def reset_groq_wave_usage() -> None:
    """新一輪精煉／批次前清空 token 累計（供戰報「省下 X 元」）。"""
    global _WAVE_USAGE_ROWS
    with _WAVE_USAGE_LOCK:
        _WAVE_USAGE_ROWS = []


def _wave_accumulate_usage(model_id: str, data: Dict[str, Any]) -> None:
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return
    row = {"model": model_id}
    for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
        if k in usage:
            try:
                row[k] = int(usage[k])
            except (TypeError, ValueError):
                pass
    if len(row) <= 1:
        return
    with _WAVE_USAGE_LOCK:
        _WAVE_USAGE_ROWS.append(row)


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        import yaml  # type: ignore
    except Exception:  # noqa: BLE001
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            out = yaml.safe_load(f)
        return out if isinstance(out, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _load_registry() -> Dict[str, Any]:
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE
    reg_path = Path(_repo_root()) / "01_Environments" / "config" / "model_registry.yaml"
    _REGISTRY_CACHE = _load_yaml(reg_path)
    return _REGISTRY_CACHE


def _alias_to_canonical(registry: Dict[str, Any]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    models = registry.get("models")
    if not isinstance(models, dict):
        return mapping
    for canon, spec in models.items():
        if not isinstance(spec, dict):
            continue
        gid = str(spec.get("groq_model_id") or canon)
        mapping[canon] = gid
        mapping[gid] = gid
        for a in spec.get("aliases") or []:
            mapping[str(a)] = gid
    return mapping


class GroqQuotaTracker:
    """RPM/RPD/TPM 記憶體 gate + 每日 RPD 持久化（JSON）。"""

    def __init__(self, root: str) -> None:
        self._root = root
        self._lock = threading.Lock()
        self._registry = _load_registry()
        self._alias_map = _alias_to_canonical(self._registry)
        self._rpm_events: Dict[str, Deque[Tuple[float, int]]] = {}
        self._state_path = Path(root) / "06_Exports_Output" / "reports" / "groq_quota_state.json"
        self._state: Dict[str, Any] = {"utc_date": "", "requests_per_model": {}}
        self._load_state()

    def _load_state(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._state_path.is_file():
            return
        try:
            with self._state_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                self._state = raw
        except Exception:  # noqa: BLE001
            pass
        if "requests_per_model" not in self._state or not isinstance(self._state["requests_per_model"], dict):
            self._state["requests_per_model"] = {}

    def persist(self) -> None:
        with self._lock:
            self._state["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            try:
                with self._state_path.open("w", encoding="utf-8") as f:
                    json.dump(self._state, f, ensure_ascii=False, indent=2)
            except Exception:  # noqa: BLE001
                pass

    def _utc_day(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _ensure_day(self) -> None:
        d = self._utc_day()
        if self._state.get("utc_date") != d:
            self._state["utc_date"] = d
            self._state["requests_per_model"] = {}

    def normalize_model(self, name: Optional[str]) -> str:
        if not name:
            return ""
        s = str(name).strip()
        return self._alias_map.get(s, s)

    def model_caps(self, canonical_id: str) -> Tuple[int, int, int]:
        models = self._registry.get("models")
        if not isinstance(models, dict):
            return 30, 100_000, 6000
        spec = models.get(canonical_id)
        if not isinstance(spec, dict):
            return 30, 100_000, 6000
        return (
            int(spec.get("RPM") or 30),
            int(spec.get("RPD") or 100_000),
            int(spec.get("TPM") or 6000),
        )

    def build_chain(self, payload_model: Optional[str]) -> List[str]:
        chain = self._registry.get("failover_chain")
        if not isinstance(chain, list) or not chain:
            chain = [
                "llama-3.3-70b-versatile",
                "qwen/qwen3-32b",
                "llama-3.1-8b-instant",
            ]
        canon_chain = [self.normalize_model(str(x)) for x in chain]
        primary = self.normalize_model(payload_model)
        if primary and primary in canon_chain:
            idx = canon_chain.index(primary)
            return canon_chain[idx:]
        return list(canon_chain)

    def _rpm_ok(self, model: str, rpm: int, est_tokens: int, tpm: int) -> bool:
        now = time.monotonic()
        dq = self._rpm_events.setdefault(model, deque())
        while dq and now - dq[0][0] > 60.0:
            dq.popleft()
        req_count = len(dq)
        tok_sum = sum(t for _, t in dq)
        return req_count < rpm and (tok_sum + est_tokens) <= tpm

    def _rpm_wait(self, model: str, rpm: int, est_tokens: int, tpm: int, max_wait: float = 8.0) -> None:
        deadline = time.monotonic() + max_wait
        while time.monotonic() < deadline:
            if self._rpm_ok(model, rpm, est_tokens, tpm):
                return
            time.sleep(0.1)

    def acquire_slot(self, model: str, payload: Dict[str, Any], *, is_last_in_chain: bool) -> bool:
        rpm, rpd, tpm = self.model_caps(model)
        est = _estimate_tokens(payload)

        with self._lock:
            self._ensure_day()
            used = int(self._state["requests_per_model"].get(model, 0))
            if used >= rpd:
                return False

        if not self._rpm_ok(model, rpm, est, tpm):
            if not is_last_in_chain:
                return False
            self._rpm_wait(model, rpm, est, tpm)

        return True

    def record_success(self, model: str, data: Dict[str, Any]) -> None:
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        tok = int(usage.get("total_tokens") or 0) or _estimate_tokens_from_usage_fallback(data)

        with self._lock:
            self._ensure_day()
            self._state["requests_per_model"][model] = int(self._state["requests_per_model"].get(model, 0)) + 1
            now = time.monotonic()
            dq = self._rpm_events.setdefault(model, deque())
            while dq and now - dq[0][0] > 60.0:
                dq.popleft()
            dq.append((now, tok))

    def rpd_snapshot_lines(self) -> List[str]:
        """各模型 RPD 剩餘百分比（簡短）。"""
        with self._lock:
            self._ensure_day()
            models = self._registry.get("models")
            if not isinstance(models, dict):
                return []
            lines: List[str] = []
            chain = self.build_chain(None)
            for mid in chain:
                _, rpd, _ = self.model_caps(mid)
                used = int(self._state.get("requests_per_model", {}).get(mid, 0))
                rem = max(0.0, (rpd - used) / max(1, rpd) * 100.0)
                short = mid.split("/")[-1]
                lines.append(f"{short}:{rem:.1f}%")
            return lines


def _estimate_tokens(payload: Dict[str, Any]) -> int:
    n = 0
    for m in payload.get("messages") or []:
        if isinstance(m, dict) and m.get("content"):
            n += len(str(m["content"]))
    mt = payload.get("max_tokens")
    try:
        n += int(mt) * 4 if mt is not None else 256
    except (TypeError, ValueError):
        n += 256
    return max(64, n // 4)


def _estimate_tokens_from_usage_fallback(data: Dict[str, Any]) -> int:
    try:
        choices = data.get("choices") or []
        content = str((choices[0].get("message") or {}).get("content") or "")
        return max(16, len(content) // 4)
    except Exception:  # noqa: BLE001
        return 64


def _get_tracker() -> GroqQuotaTracker:
    global _TRACKER_SINGLETON
    with _TRACKER_LOCK:
        if _TRACKER_SINGLETON is None:
            _TRACKER_SINGLETON = GroqQuotaTracker(_repo_root())
        return _TRACKER_SINGLETON


def format_groq_quota_telegram_suffix() -> Tuple[str, str]:
    """回傳（今日彈藥餘裕行, 本次精煉花費行）。無 PyYAML／無 registry 時給保守占位。"""
    reg = _load_registry()
    fx = float((reg.get("fx") or {}).get("twd_per_usd") or 32.0)
    tracker = _get_tracker()
    ammo = tracker.rpd_snapshot_lines()
    ammo_line = "今日彈藥餘裕：" + (" ".join(ammo) if ammo else "（registry 未載入）")

    models_spec = reg.get("models") if isinstance(reg.get("models"), dict) else {}

    total_usd = 0.0
    with _WAVE_USAGE_LOCK:
        rows = list(_WAVE_USAGE_ROWS)

    for row in rows:
        mid = str(row.get("model") or "")
        spec = models_spec.get(mid) if isinstance(models_spec, dict) else None
        if not isinstance(spec, dict):
            continue
        pr = spec.get("pricing_usd_per_1m_tokens") or {}
        if not isinstance(pr, dict):
            continue
        pin = float(pr.get("input") or 0)
        pout = float(pr.get("output") or 0)
        pt = float(row.get("prompt_tokens") or 0)
        ct = float(row.get("completion_tokens") or 0)
        total_usd += (pt / 1_000_000.0) * pin + (ct / 1_000_000.0) * pout

    twd_saved = int(round(total_usd * fx))
    if not rows:
        cost_line = "本次精煉花費：$0 元（免費額度），省下 [—] 元（尚無 Groq usage 可供換算）"
    else:
        cost_line = f"本次精煉花費：$0 元（免費額度），省下 [{twd_saved}] 元（Groq 標價示意×{fx} TWD/USD）"
    return ammo_line, cost_line


def _merge_headers(base: str, extra: Optional[Dict[str, str]]) -> Dict[str, str]:
    h = {"User-Agent": base, "Accept": "application/json"}
    if extra:
        h.update(extra)
    return h


def _error_type_from_http_body(raw: str) -> str:
    if not raw.strip():
        return ""
    try:
        parsed = json.loads(raw)
        err = parsed.get("error") if isinstance(parsed, dict) else None
        if isinstance(err, dict):
            return str(err.get("type") or err.get("code") or "")[:24]
        if isinstance(err, str):
            return err[:24]
    except json.JSONDecodeError:
        pass
    return ""


def blind_http_dual_ssl(
    url: str,
    *,
    method: str,
    headers: Optional[Dict[str, str]] = None,
    body: bytes = b"",
    timeout: int = 25,
    discard_body_bytes: int = 64,
    user_agent: str = UA_SMOKE,
) -> Tuple[int, str]:
    """成功時丟棄 body 前 discard_body_bytes；回傳 (http_code, error_hint)。
    error_hint 於 200 時為空字串；失敗時為簡短類型或 NetworkError。"""
    hdrs = _merge_headers(user_agent, headers)
    last_err = ""
    ctxs: List[ssl.SSLContext] = [
        ssl.create_default_context(),
        ssl._create_unverified_context(),  # type: ignore[attr-defined]
    ]
    for ctx in ctxs:
        try:
            req = urllib.request.Request(url, data=body if body else None, method=method)
            for k, v in hdrs.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                _ = resp.read(discard_body_bytes)
                return resp.getcode(), ""
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
            return e.code, _error_type_from_http_body(raw)
        except Exception as e:  # noqa: BLE001
            last_err = type(e).__name__
            continue
    return 0, last_err or "NetworkError"


def _json_request_dual_ssl_once(
    url: str,
    *,
    method: str,
    headers: Optional[Dict[str, str]],
    body: Optional[bytes],
    timeout: int,
    user_agent: str,
) -> Tuple[int, Any]:
    hdrs = _merge_headers(user_agent, headers)
    ctxs: List[ssl.SSLContext] = [
        ssl.create_default_context(),
        ssl._create_unverified_context(),  # type: ignore[attr-defined]
    ]
    last_err: Any = None
    data = body if body is not None else None
    for ctx in ctxs:
        try:
            req = urllib.request.Request(url, data=data, method=method)
            for k, v in hdrs.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return resp.getcode(), (json.loads(raw) if raw.strip() else {})
        except urllib.error.HTTPError as e:
            b = e.read().decode("utf-8", errors="replace") if e.fp else ""
            try:
                return e.code, json.loads(b) if b.strip() else {}
            except json.JSONDecodeError:
                return e.code, {"raw": b[:500]}
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
    return 0, {"error": repr(last_err)}


def json_request_dual_ssl(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    timeout: int = 25,
    user_agent: str = UA_TOOL,
    groq_chat_failover: bool = False,
    groq_meta_out: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Any]:
    """完整讀 body 並嘗試 JSON 解析；回傳 (code, dict_or_error_wrap)。

    groq_chat_failover：
      · 僅在 POST 至 api.groq.com 且 body 為 chat completions JSON（含 messages）時生效。
      · 請求前檢查 registry 內 RPM/RPD/TPM；429 時依 failover_chain 自動換模型。
      · groq_meta_out 可選：填入 models_tried 等（不含金鑰）。
    """
    if groq_meta_out is not None:
        groq_meta_out.clear()

    plain = (
        not groq_chat_failover
        or "api.groq.com" not in url
        or method.upper() != "POST"
        or not body
    )
    if plain:
        return _json_request_dual_ssl_once(
            url, method=method, headers=headers, body=body, timeout=timeout, user_agent=user_agent
        )

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return _json_request_dual_ssl_once(
            url, method=method, headers=headers, body=body, timeout=timeout, user_agent=user_agent
        )

    if not isinstance(payload, dict) or "messages" not in payload:
        return _json_request_dual_ssl_once(
            url, method=method, headers=headers, body=body, timeout=timeout, user_agent=user_agent
        )

    tracker = _get_tracker()
    chain = tracker.build_chain(payload.get("model"))
    if groq_meta_out is not None:
        groq_meta_out["failover_chain"] = list(chain)

    last_code = 0
    last_data: Any = {}

    for i, mid in enumerate(chain):
        is_last = i == len(chain) - 1
        if not tracker.acquire_slot(mid, payload, is_last_in_chain=is_last):
            if groq_meta_out is not None:
                groq_meta_out.setdefault("models_tried", []).append(
                    {"model": mid, "skipped": "rpm_or_rpd_gate"}
                )
            continue

        attempt = dict(payload)
        attempt["model"] = mid
        attempt_body = json.dumps(attempt).encode("utf-8")

        code, data = _json_request_dual_ssl_once(
            url,
            method=method,
            headers=headers,
            body=attempt_body,
            timeout=timeout,
            user_agent=user_agent,
        )

        if groq_meta_out is not None:
            groq_meta_out.setdefault("models_tried", []).append({"model": mid, "http_code": code})

        last_code, last_data = code, data

        if code == 429:
            continue

        if code in (401, 403):
            return code, data

        if code == 200 and isinstance(data, dict):
            tracker.record_success(mid, data)
            tracker.persist()
            _wave_accumulate_usage(mid, data)
            return code, data

        # 其他錯誤：不盲目換模型（避免掩蓋金鑰／契約錯誤）
        return code, data

    return last_code or 429, last_data if last_data else {"error": {"message": "groq_failover_exhausted"}}

