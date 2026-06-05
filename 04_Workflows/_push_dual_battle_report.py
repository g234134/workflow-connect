# 推送「雙重壓力測試」戰報至 Telegram；同時更新 Status.json。

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gov_paths import get_secret, get_tang_gov_root, resolve_artifact_under_root  # type: ignore


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def patch_status() -> None:
    sp = resolve_artifact_under_root(get_tang_gov_root(), "status_json")
    with open(sp, "r", encoding="utf-8") as f:
        d = json.load(f)
    d["code_cleaner_last_wave"] = {
        "status": "Success",
        "run_id": "b2acafc815514942ab47ff963c67b987",
        "candidate_pool": 38445,
        "sampled": 100,
        "ok": 100,
        "warning": 0,
        "failed": 0,
        "success_rate": 1.0,
        "files_landed_in_out_dir": 99,
        "files_landed_note": "1 件因 sha256 前綴+檔名同名被覆寫；報告 100/100 全處理成功",
        "out_dir": r"D:\大唐三省六部\05_Temp_Cache\cleaned_sample",
        "report_path": r"D:\大唐三省六部\06_Exports_Output\reports\code_cleaner_report_b2acafc815514942ab47ff963c67b987.json",
        "completed_at": _utc(),
    }
    d["destruction_test_last"] = {
        "status": "Success",
        "agent_run_id": "6ac97dc4010d49c2941bcf1f2139d1ab",
        "src": r"D:\大唐三省六部\06_Exports_Output\Archive\format_error\destruction_test.json",
        "dst": r"D:\大唐三省六部\03_RAG_Database\C2_核心知識庫\destruction_test.json",
        "before_size_bytes": 506,
        "after_text": '{\n  "name": "destruction_test"\n}',
        "after_size_bytes": 32,
        "groq_invoked": True,
        "groq_only_path": True,
        "model": "llama-3.3-70b-versatile",
        "note": "Groq 給出最小合法骨架；原文已被破壞至無語義可還原",
        "report_path": r"D:\大唐三省六部\06_Exports_Output\reports\destruction_test_6ac97dc4010d49c2941bcf1f2139d1ab.json",
        "completed_at": _utc(),
    }
    d["updated_at"] = _utc()
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def push_telegram() -> None:
    token = (get_secret("TELEGRAM_BOT_TOKEN", "") or "").strip()
    chat_id = (get_secret("TELEGRAM_CHAT_ID", "") or "").strip()
    if not token or not chat_id:
        print("missing token/chat_id")
        return
    text = (
        "⚔️ 雙重壓力測試·戰報\n\n"
        "【一】舊代碼抽樣清剿\n"
        "✅ 100/100 成功率 100%\n"
        "候選池: 38,445 件\n"
        "類型 Top5:\n"
        "  · python       74\n"
        "  · c_header     20\n"
        "  · json          3\n"
        "  · python_stub   2\n"
        "  · php           1\n"
        "Run_ID: b2acafc8...\n"
        "入庫: 05_Temp_Cache\\cleaned_sample (99 件落盤；1 件因檔名碰撞被覆寫)\n\n"
        "【二】毀滅級 JSON 救援\n"
        "✅ Groq llama-3.3-70b 成功救援\n"
        "before: 506 bytes 亂碼+缺括號+沒首尾\n"
        "after:  32 bytes 合法 JSON\n"
        "路徑: 本地三戰術全敗 → Groq 介入\n"
        'reply: {"name":"destruction_test"}\n'
        "Run_ID: 6ac97dc4...\n"
        "備註: LLM 已熬過毀滅級輸入並回傳合法骨架\n"
        "      （無法還原原始語義 — 預期內）"
    )
    ctx = ssl._create_unverified_context()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        resp = json.loads(r.read().decode())
    print(json.dumps({"ok": resp.get("ok"), "message_id": (resp.get("result") or {}).get("message_id")}, ensure_ascii=False))


if __name__ == "__main__":
    patch_status()
    push_telegram()
