# _hybrid_cloud_batch.py — 混合雲第一戰（Telegram + 本地/Groq 批量修復）

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gov_paths import get_secret, get_tang_gov_root, resolve_artifact_under_root  # type: ignore
from GroqHybridRecovery_Agent import GroqHybridRecovery_Agent  # type: ignore


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ssl_ctx():
    try:
        return ssl.create_default_context()
    except Exception:  # noqa: BLE001
        return ssl._create_unverified_context()  # type: ignore[attr-defined]


def _tg_request(method: str, token: str, **params: str) -> Tuple[int, Any]:
    q = urllib.parse.urlencode(params)
    url = f"https://api.telegram.org/bot{token}/{method}?{q}"
    last_err: Optional[BaseException] = None
    for ctx in (_ssl_ctx(), ssl._create_unverified_context()):  # type: ignore[attr-defined]
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return resp.getcode(), json.loads(raw)
        except (urllib.error.URLError, ssl.SSLError, TimeoutError) as e:
            last_err = e
            continue
    raise RuntimeError(f"Telegram request failed: {last_err!r}") from last_err


def resolve_telegram_chat_id(token: str) -> Optional[str]:
    cid = (get_secret("TELEGRAM_CHAT_ID", "") or "").strip()
    if cid:
        return cid
    uid = (get_secret("TELEGRAM_USER_ID", "") or "").strip()
    if uid:
        return uid
    code, data = _tg_request("getUpdates", token)
    if code != 200 or not data.get("ok"):
        return None
    best = None
    best_ts = -1
    for u in data.get("result", []):
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat") or {}
        if chat.get("type") != "private":
            continue
        cid_i = chat.get("id")
        ts = int(msg.get("date") or u.get("update_id") or 0)
        if cid_i and ts >= best_ts:
            best_ts = ts
            best = str(cid_i)
    return best


def send_telegram(token: str, chat_id: str, text: str) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    last_err: Optional[BaseException] = None
    for ctx in (_ssl_ctx(), ssl._create_unverified_context()):  # type: ignore[attr-defined]
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return {"http": resp.getcode(), "body": json.loads(raw)}
        except (urllib.error.URLError, ssl.SSLError, TimeoutError) as e:
            last_err = e
            continue
    return {"http": 0, "body": {"ok": False, "error": repr(last_err)}}


def _patch_status(dest_root: str, patch: Dict[str, Any]) -> None:
    path = resolve_artifact_under_root(dest_root, "status_json")
    data: Dict[str, Any] = {}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data.update(patch)
    data["updated_at"] = _utc_iso()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> int:
    dest_root = get_tang_gov_root()
    token = (get_secret("TELEGRAM_BOT_TOKEN", "") or "").strip()

    chat_id: Optional[str] = None
    telegram_start: Dict[str, Any] = {"skipped": True}
    if token and "PLACEHOLDER" not in token:
        chat_id = resolve_telegram_chat_id(token)
        if chat_id:
            msg = "啟稟尚書省，大唐戰車混合雲系統初始化成功，遠端監控已就緒。"
            telegram_start = send_telegram(token, chat_id, msg)
        else:
            telegram_start = {"skipped": False, "error": "no_chat_id"}
    else:
        telegram_start = {"skipped": True, "error": "no_bot_token"}

    agent = GroqHybridRecovery_Agent(dest_root=dest_root)
    result = agent.run_batch()

    summary_line = (
        f"混合雲批量修復完畢｜Run_ID={result['run_id']}｜"
        f"掃描={result['target_count']}｜本地={result['ok_local']}｜Groq={result['ok_groq']}｜"
        f"未復原={result['failed']}｜成功率={result['success_rate']}"
    )

    telegram_end: Dict[str, Any] = {"skipped": True}
    if token and chat_id:
        telegram_end = send_telegram(token, chat_id, summary_line)

    _patch_status(
        dest_root,
        {
            "pipeline_status": "Success",
            "hybrid_cloud_last_wave": {
                "status": "Success",
                "run_id": result["run_id"],
                "target_count": result["target_count"],
                "ok_local": result["ok_local"],
                "ok_groq": result["ok_groq"],
                "failed": result["failed"],
                "groq_skipped": result["groq_skipped"],
                "success_rate": result["success_rate"],
                "telegram_chat_resolved": bool(chat_id),
                "telegram_start_ok": bool(telegram_start.get("body", {}).get("ok")),
                "telegram_end_ok": bool(telegram_end.get("body", {}).get("ok")),
                "completed_at": result["completed_at"],
            },
        },
    )

    print(json.dumps({"telegram_start": telegram_start, "batch": result, "telegram_end": telegram_end}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
