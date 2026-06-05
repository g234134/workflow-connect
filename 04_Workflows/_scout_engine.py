"""_scout_engine.py — v2.55b/v2.56 前線偵察兵（Playwright + 結構化進料 + ROI 閉環）。

執行環境：請使用 **gov_agency** venv（與 crewai 同艙；已含 playwright / httpx / bs4）。

目標平台：環境變數 `SCOUT_PLATFORM` = v2ex | mock | http（預留 upwork / ptt 同屬 http 客製 URL）。
  · V2EX：`https://www.v2ex.com/go/jobs`（節流、僅取首頁可見列；請遵守網站條款與禮儀）。
  · mock：不連外網，寫入測試案源（含唯一 UUID 以利指紋入隊）。
  · http：`SCOUT_TARGET_URL` 指向任意 HTML 頁，抽取 title 與正文摘要。

進料：`05_Temp_Cache/raw_inbound/market_scout_*.json` → 觸發 `_inbound_watchdog` / 或 `--enqueue` 直接呼叫主艙指紋腳本入 pending。

Telegram：`Asset_Value_Evaluator_Agent._telegram_scout_high_yield` + Inline `scout:*`（由 `Telegram_Listener_Agent` 接收）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore

SCOUT_CALLBACK_PREFIX = "scout:"


def _save_scout_pipeline(
    lead: Dict[str, Any],
    match_report: Optional[Dict[str, Any]],
    run_tag: str,
    *,
    dest_root: Optional[str] = None,
) -> str:
    root = os.path.abspath(dest_root or get_tang_gov_root())
    rep = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    os.makedirs(rep, exist_ok=True)
    path = os.path.join(rep, "scout_last_pipeline.json")
    data = {
        "schema_version": "1.0",
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_tag": run_tag,
        "lead": lead,
        "match_report": match_report or {},
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path


def _utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _slug(s: str, max_len: int = 48) -> str:
    t = re.sub(r"[^A-Za-z0-9._-]+", "_", (s or "lead").strip())[:max_len].strip("_")
    return t or "lead"


def build_scout_inline_keyboard(run_tag: str) -> Dict[str, Any]:
    """Telegram Inline 按鈕（callback_data ≤64B）：跟進 / 略過 / 結案草案（scout:confirm）。"""
    rt = re.sub(r"[^a-f0-9]", "", (run_tag or "")[:12])
    if not rt:
        rt = uuid.uuid4().hex[:12]
    return {
        "inline_keyboard": [
            [
                {"text": "標記跟進", "callback_data": f"{SCOUT_CALLBACK_PREFIX}f:{rt}"},
                {"text": "略過", "callback_data": f"{SCOUT_CALLBACK_PREFIX}i:{rt}"},
            ],
            [
                {
                    "text": "結案草案",
                    "callback_data": f"{SCOUT_CALLBACK_PREFIX}confirm:{rt[:10]}",
                },
            ],
        ]
    }


def _gov_main_python() -> str:
    return os.path.normpath(
        os.path.join(_root, "01_Environments", "python_venvs", "gov_main", "Scripts", "python.exe")
    )


def enqueue_register_pending(abs_path: str, run_id: str) -> int:
    """經主艙執行 `_register_fingerprints.py --clean-status pending`（與生料哨兵一致）。"""
    py = _gov_main_python()
    if not os.path.isfile(py):
        print("[WARN] gov_main python 不存在，略過指紋入隊", file=sys.stderr)
        return 1
    script = os.path.join(_here, "_register_fingerprints.py")
    cmd = [
        py,
        script,
        "--files",
        abs_path,
        "--label",
        "raw_inbound",
        "--clean-status",
        "pending",
        "--run-id",
        run_id,
        "--agent",
        "market_scout_v2_55b",
    ]
    r = subprocess.run(cmd, cwd=_here, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout:
        sys.stdout.write(r.stdout)
    if r.stderr:
        sys.stderr.write(r.stderr)
    return int(r.returncode)


def write_lead_to_raw_inbound(lead: Dict[str, Any], *, dest_root: Optional[str] = None) -> str:
    root = os.path.abspath(dest_root or get_tang_gov_root())
    raw_dir = resolve_agent_output_path(root, "05_Temp_Cache", "raw_inbound")
    os.makedirs(raw_dir, exist_ok=True)
    title = str(lead.get("title") or "untitled")
    fn = f"market_scout_{_utc_compact()}_{_slug(title)}.json"
    path = os.path.join(raw_dir, fn)
    payload = {
        "schema_version": "1.0",
        "kind": "market_scout_lead",
        "gathered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **lead,
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path


def fetch_v2ex_jobs(*, limit: int = 12) -> List[Dict[str, Any]]:
    from bs4 import BeautifulSoup  # type: ignore
    from playwright.sync_api import sync_playwright  # type: ignore

    url = "https://www.v2ex.com/go/jobs"
    out: List[Dict[str, Any]] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(45_000)
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(0.85)
                html = page.content()
            finally:
                browser.close()
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] v2ex fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        return []
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.select("span.item_title a"):
        if len(out) >= limit:
            break
        title = a.get_text(strip=True)
        href = (a.get("href") or "").strip()
        if not title or not href.startswith("/t/"):
            continue
        full_url = "https://www.v2ex.com" + href if href.startswith("/") else href
        out.append(
            {
                "platform": "v2ex",
                "title": title,
                "description": "",
                "budget": "",
                "url": full_url,
            }
        )
    return out


def fetch_http_landing(url: str, *, limit: int = 1) -> List[Dict[str, Any]]:
    from bs4 import BeautifulSoup  # type: ignore
    from playwright.sync_api import sync_playwright  # type: ignore

    out: List[Dict[str, Any]] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(45_000)
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(0.65)
                html = page.content()
            finally:
                browser.close()
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] http fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        return []
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string if soup.title else "").strip() or url
    chunks: List[str] = []
    for tag in soup.find_all(["article", "main", "body"]):
        t = tag.get_text(" ", strip=True)
        if t:
            chunks.append(t[:4000])
            break
    desc = chunks[0] if chunks else ""
    for i in range(min(limit, 3)):
        out.append(
            {
                "platform": "http",
                "title": title if i == 0 else f"{title} ({i})",
                "description": desc[:8000],
                "budget": "",
                "url": url,
            }
        )
    return out[:limit]


def build_mock_leads() -> List[Dict[str, Any]]:
    """模擬案源：嵌入唯一 run_nonce 以產生新 SHA256 → pending 隊列上升。"""
    nonce = uuid.uuid4().hex
    return [
        {
            "platform": "mock",
            "title": f"Python automation pipeline {nonce[:8]}",
            "description": (
                "Seeking senior Python engineer to extend data cleaning pipeline, "
                "SQLite registry, and Groq-throttled evaluators. "
                f"run_nonce={nonce} keywords: functions classes imports json_summary"
            ),
            "budget": "TWD 80k-120k",
            "url": f"https://example.invalid/scout/{nonce}",
        }
    ]


def run_cycle(
    *,
    platform: str,
    limit: int,
    enqueue: bool,
    do_match: bool,
    notify: bool,
    use_groq_semantic: bool,
) -> Dict[str, Any]:
    platform = (platform or "mock").strip().lower()
    if platform == "mock":
        leads = build_mock_leads()
    elif platform == "v2ex":
        leads = fetch_v2ex_jobs(limit=limit)
    elif platform == "http":
        url = (os.environ.get("SCOUT_TARGET_URL") or "").strip()
        if not url:
            return {"ok": False, "error": "SCOUT_TARGET_URL_required_for_http"}
        leads = fetch_http_landing(url, limit=max(1, min(limit, 3)))
    elif platform in ("upwork", "ptt"):
        return {
            "ok": False,
            "error": "platform_placeholder",
            "hint": "請改 SCOUT_PLATFORM=http 並設定 SCOUT_TARGET_URL，或實作專屬解析器。",
        }
    else:
        return {"ok": False, "error": f"unknown_platform:{platform}"}

    if not leads:
        return {"ok": False, "error": "no_leads", "platform": platform}

    from Asset_Value_Evaluator_Agent import (  # type: ignore
        match_against_registry,
        _telegram_scout_high_yield,
    )

    written: List[str] = []
    match_reports: List[Dict[str, Any]] = []
    for lead in leads[:limit]:
        path = write_lead_to_raw_inbound(lead)
        written.append(path)
        rid = f"scout_{uuid.uuid4().hex[:16]}"
        rc = 0
        if enqueue:
            rc = enqueue_register_pending(path, rid)
        mr: Optional[Dict[str, Any]] = None
        if do_match:
            mr = match_against_registry(lead, use_groq_semantic=use_groq_semantic)
            match_reports.append(mr)
            try:
                _save_scout_pipeline(lead, mr, rid)
            except Exception as e:  # noqa: BLE001
                print(f"[WARN] scout pipeline 寫檔失敗: {e}", file=sys.stderr)
            if notify and mr.get("is_high_yield"):
                cov = float(mr.get("coverage_pct") or 0.0)
                _telegram_scout_high_yield(
                    title=str(lead.get("title") or ""),
                    budget=str(lead.get("budget") or ""),
                    coverage_pct=cov,
                    reply_markup=build_scout_inline_keyboard(rid),
                )
        time.sleep(0.05)

    return {
        "ok": True,
        "platform": platform,
        "written": written,
        "enqueue": enqueue,
        "match_reports": match_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="大唐戰車 v2.55b 前線偵察兵")
    parser.add_argument(
        "--platform",
        default=os.environ.get("SCOUT_PLATFORM", "mock"),
        help="v2ex | mock | http | upwork | ptt（後兩者為占位）",
    )
    parser.add_argument("--limit", type=int, default=3, help="最多處理幾筆案源")
    parser.add_argument(
        "--enqueue",
        action="store_true",
        help="寫檔後立即以主艙 _register_fingerprints 標記 pending（推薦自檢）",
    )
    parser.add_argument("--match", action="store_true", help="執行 match_against_registry")
    parser.add_argument("--notify", action="store_true", help="高產能案源時發 Telegram")
    parser.add_argument(
        "--groq-semantic",
        action="store_true",
        help="邊界區啟用最多 1 次 Groq 覆核（仍走 v2.54 彈藥護欄）",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="等同 --platform mock --limit 1 --enqueue --match（自檢）",
    )
    args = parser.parse_args()

    if args.simulate:
        args.platform = "mock"
        args.limit = 1
        args.enqueue = True
        args.match = True

    out = run_cycle(
        platform=args.platform,
        limit=max(1, args.limit),
        enqueue=args.enqueue,
        do_match=args.match,
        notify=args.notify,
        use_groq_semantic=args.groq_semantic,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
