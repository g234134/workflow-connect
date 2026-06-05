# _send_keytest_to_telegram.py — 將最新 key_test 報告透過 Telegram 推送至白名單 chat_id

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gov_paths import get_secret, get_tang_gov_root, resolve_agent_output_path  # type: ignore


def _ctxs():
    try:
        yield ssl.create_default_context()
    except Exception:  # noqa: BLE001
        pass
    yield ssl._create_unverified_context()  # type: ignore[attr-defined]


def _post(url: str, body: bytes, headers: Dict[str, str]) -> Tuple[int, Any]:
    last_err: Optional[BaseException] = None
    for ctx in _ctxs():
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return resp.getcode(), json.loads(raw) if raw.strip() else {}
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
            continue
    return 0, {"error": repr(last_err)}


def _newest_keytest_report() -> Optional[str]:
    reports = resolve_agent_output_path(None, "06_Exports_Output", "reports")
    if not os.path.isdir(reports):
        return None
    cands = [f for f in os.listdir(reports) if f.startswith("key_test_") and f.endswith(".json")]
    if not cands:
        return None
    cands.sort(reverse=True)
    return os.path.join(reports, cands[0])


def render_compact_table(rows):
    out = []
    out.append("🛡️ 糧草效能校準")
    ok = sum(1 for r in rows if r["status"] == "OK")
    out.append(f"通過 {ok}/{len(rows)}")
    out.append("")
    for r in rows:
        emoji = "✅" if r["status"] == "OK" else "❌"
        api = r["api"]
        lat = r["latency_ms"]
        note = (r.get("note") or "")[:60]
        out.append(f"{emoji} {api}")
        out.append(f"   {r['status']} · {lat}ms · http={r.get('http')}")
        if note:
            out.append(f"   {note}")
    return "\n".join(out)


def main() -> int:
    get_tang_gov_root()
    token = (get_secret("TELEGRAM_BOT_TOKEN", "") or "").strip()
    if not token or "PLACEHOLDER" in token:
        print(json.dumps({"ok": False, "reason": "no_token"}))
        return 1
    chat_id = (get_secret("TELEGRAM_CHAT_ID", "") or "").strip()
    if not chat_id:
        print(json.dumps({"ok": False, "reason": "no_chat_id"}))
        return 2
    fp = _newest_keytest_report()
    if not fp:
        print(json.dumps({"ok": False, "reason": "no_report"}))
        return 3
    with open(fp, "r", encoding="utf-8") as f:
        summary = json.load(f)
    text = render_compact_table(summary.get("rows") or [])
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    code, data = _post(url, body, {"Content-Type": "application/json"})
    print(json.dumps({"http": code, "ok": bool(isinstance(data, dict) and data.get("ok")), "report_path": fp}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
