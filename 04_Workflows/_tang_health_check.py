#!/usr/bin/env python3
"""
_tang_health_check.py — 共享異常檢測器（Hermes ↔ Cursor 共用）

功能：
  1. 掃描關鍵產出檔，偵測已知異常模式（P1~P4 等）
  2. 比對 cross_agent_fix_ledger.yaml，判斷狀態是否一致
  3. 新異常 → 自動寫入 ledger 標記為 open
  4. 已修異常復發 → 自動標記 needs_reverify
  5. 記錄到 shared_activity.log（跨 agent 審計）
  6. 輸出 JSON 報告到 reports/tang_health_check.json

用法：
  /c/Users/666LAG/crew_tank/Scripts/python.exe _tang_health_check.py --agent hermes|cursor

回傳碼：
  0 = 無異常（全部 ✅）
  1 = 有異常（至少一個 pending / needs_reverify）
  2 = 腳本執行失敗
"""

import sys
import json
import pathlib
import datetime
import traceback

try:
    from ruamel.yaml import YAML
except ImportError:
    print("ERROR: 需要 ruamel.yaml。 pip install ruamel.yaml", file=sys.stderr)
    sys.exit(2)

# ── Project root ────────────────────────────────────────────────────
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent  # 04_Workflows/ 的上層
REPORTS_DIR = PROJECT_ROOT / "06_Exports_Output" / "reports"
LEDGER_PATH = PROJECT_ROOT / "04_Workflows" / "cross_agent_fix_ledger.yaml"
ACTIVITY_LOG = PROJECT_ROOT / "04_Workflows" / "shared_activity.log"
OUTPUT_PATH = REPORTS_DIR / "tang_health_check.json"

# ruamel.yaml 實例（round-trip 模式）
_yaml = YAML()
_yaml.indent(mapping=2, sequence=4, offset=2)
_yaml.width = 120


# ── Check 定義 ──────────────────────────────────────────────────────

def _check_elite_cache():
    """P1: elite_cache.json 不應為空，min_heuristic_score 應為 7.5"""
    path = REPORTS_DIR / "elite_cache.json"
    if not path.exists():
        return False, "elite_cache.json 不存在", "file_missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stats = data.get("stats") or {}
        count = stats.get("elite_count", 0) if isinstance(stats, dict) else 0
        score = data.get("min_heuristic_score")
        if count == 0:
            return False, f"elite_count=0（cache 空置）", f"elite_count=0; min_heuristic_score={score}"
        if score is None or score < 7.0:
            return False, f"min_heuristic_score={score} 偏低", f"elite_count={count}; score={score}"
        return True, f"elite_count={count}, min_heuristic_score={score}", f"elite_count={count}; score={score}; built_at={data.get('built_at','?')}"
    except (json.JSONDecodeError, OSError) as e:
        return False, f"讀取失敗: {e}", f"error={e}"


def _check_groq_quota_state():
    """P3: groq_quota_state.json 應有 requests_per_model"""
    path = REPORTS_DIR / "groq_quota_state.json"
    if not path.exists():
        return False, "groq_quota_state.json 不存在", "file_missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        rp = data.get("requests_per_model") or {}
        if not rp:
            return False, "requests_per_model 為空（無使用紀錄）", f"requests_per_model={rp!r}"
        utc_date = data.get("utc_date", "")
        if utc_date:
            try:
                dt = datetime.datetime.strptime(utc_date, "%Y-%m-%d")
                age = (datetime.datetime.utcnow() - dt).total_seconds()
                if age > 172800:  # 48h
                    return False, f"資料已過期 {age/3600:.0f}h（utc_date={utc_date}）", f"age_h={age/3600:.0f}"
            except ValueError:
                pass
        detail = "; ".join(f"{k}={v}" for k, v in rp.items())
        return True, f"requests_per_model 正常: {detail}", f"utc_date={utc_date}; {detail}"
    except (json.JSONDecodeError, OSError) as e:
        return False, f"讀取失敗: {e}", f"error={e}"


def _check_groq_wiring():
    """P2: _report_generator.py 應包含 groq_chat_failover=True"""
    path = PROJECT_ROOT / "04_Workflows" / "_report_generator.py"
    if not path.exists():
        return False, "_report_generator.py 不存在", "file_missing"
    try:
        text = path.read_text(encoding="utf-8")
        if "groq_chat_failover=True" in text:
            return True, "groq_chat_failover 已接線", "wiring_present"
        else:
            return False, "groq_chat_failover=True 不存在（P2 可能復發）", "wiring_missing"
    except OSError as e:
        return False, f"讀取失敗: {e}", f"error={e}"


def _check_local_similarity():
    """P4: scout_last_pipeline.json 的 local_similarity_pct 不應全 null"""
    path = REPORTS_DIR / "scout_last_pipeline.json"
    if not path.exists():
        return False, "scout_last_pipeline.json 不存在", "file_missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        tm = (data.get("match_report") or {}).get("top_matches") or []
        if not tm:
            return False, "top_matches 為空", "top_matches_empty"
        vals = [x.get("local_similarity_pct") for x in tm]
        non_null = [v for v in vals if v is not None]
        if not non_null:
            return False, f"全部 {len(vals)} 筆 similarity 皆為 null（P4 可能復發）", "all_null"
        return True, f"{len(non_null)}/{len(vals)} 筆有實數值: {non_null[:5]}", f"ok_count={len(non_null)}; total={len(vals)}"
    except (json.JSONDecodeError, OSError) as e:
        return False, f"讀取失敗: {e}", f"error={e}"


def _check_reports_dir():
    """通用：reports/ 目錄應存在且非空"""
    if not REPORTS_DIR.exists():
        return False, "reports 目錄不存在", "dir_missing"
    files = list(REPORTS_DIR.glob("*.json"))
    if not files:
        return False, "reports 目錄無任何 .json 檔案", "empty_dir"
    return True, f"reports 目錄存在，含 {len(files)} 個 .json", f"file_count={len(files)}"


# 註冊所有檢查
CHECKS = [
    {
        "id": "P1-elite-cache-empty",
        "name": "精英快取（elite_cache）",
        "check_fn": _check_elite_cache,
        "auto_create": True,
    },
    {
        "id": "P3-ammo-margin-always-100",
        "name": "Groq 配額狀態（quota_state）",
        "check_fn": _check_groq_quota_state,
        "auto_create": True,
    },
    {
        "id": "P2-fake-savings-number",
        "name": "Groq 接線（groq_chat_failover）",
        "check_fn": _check_groq_wiring,
        "auto_create": True,
    },
    {
        "id": "P4-local-similarity-null",
        "name": "本地相似度（similarity）",
        "check_fn": _check_local_similarity,
        "auto_create": True,
    },
    {
        "id": "GEN-reports-dir",
        "name": "產出目錄完整性",
        "check_fn": _check_reports_dir,
        "auto_create": False,
    },
]


# ── Ledger 操作（ruamel.yaml round-trip） ──────────────────────────

def load_ledger():
    """載入 ledger，回傳 (defects_dict, raw_data, rYAML)"""
    if not LEDGER_PATH.exists():
        return {}, {"defects": []}, None
    data = _yaml.load(LEDGER_PATH)
    if data is None:
        data = {"defects": []}
    defects = {}
    for d in data.get("defects") or []:
        if isinstance(d, dict) and "id" in d:
            defects[d["id"]] = d
    return defects, data, _yaml


def save_ledger(raw_data: dict):
    """以 round-trip 寫回 YAML"""
    raw_data["updated_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    _yaml.dump(raw_data, LEDGER_PATH)


def write_activity_log(agent: str, action: str, detail: str):
    """Append 一行到 shared_activity.log"""
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(str(ACTIVITY_LOG), "a", encoding="utf-8") as f:
        f.write(f"{ts} | {agent:<8} | {action:<22} | {detail}\n")


# ── Main ────────────────────────────────────────────────────────────

def main():
    agent = "auto"
    cron_mode = False
    args = sys.argv[1:]
    if "--agent" in args:
        idx = args.index("--agent")
        if idx + 1 < len(args):
            agent = args[idx + 1]
    if "--cron" in args:
        cron_mode = True

    if not cron_mode:
        print(f"🔍 _tang_health_check.py — 共享健康檢查")
        print(f"   專案: {PROJECT_ROOT}")
        print(f"   Agent: {agent}")
        print()

    # 1. 載入 ledger
    defects_dict, raw_data, _ = load_ledger()
    if not cron_mode:
        print(f"📋 Ledger: {len(defects_dict)} 個已知缺陷")
        print()

    # 2. 執行所有檢查
    results = []
    new_entries = []
    regressions = []
    all_ok = True

    for chk in CHECKS:
        cid = chk["id"]
        cname = chk["name"]
        try:
            ok, message, evidence = chk["check_fn"]()
        except Exception as e:
            ok, message, evidence = False, f"例外: {e}", traceback.format_exc()

        icon = "✅" if ok else "❌"
        if not cron_mode:
            print(f"  {icon} [{cid}] {cname}")
            print(f"      → {message}")

        results.append({
            "id": cid,
            "name": cname,
            "ok": ok,
            "message": message,
            "evidence": evidence,
        })

        known = defects_dict.get(cid)

        if not ok:
            all_ok = False
            if known is None and chk["auto_create"]:
                # 新異常 → 自動建立 ledger entry
                now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                new_entries.append({
                    "id": cid,
                    "status": "open",
                    "owner_last": agent,
                    "source_of_truth": "auto_detect",
                    "evidence": evidence,
                    "verify_cmd": "",
                    "claim_owner": None,
                    "touched_paths": [],
                    "updated_at": now,
                    "notes": f"[auto_detect @ {now}] {message}",
                    "auto_detect": True,
                })
                if not cron_mode:
                    print(f"      📝 → 自動建立 ledger open 條目")
                write_activity_log(agent, "auto_open", f"{cid}: {message}")
            elif known and known.get("status") == "fixed":
                # 已修復的又復發
                regressions.append(cid)
                if not cron_mode:
                    print(f"      ⚠️ → 已修復但異常復發！標記 needs_reverify")
                write_activity_log(agent, "regression_detected", f"{cid}: {message}")
        elif ok and known and known.get("status") == "open":
            if not cron_mode:
                print(f"      🔄 → 異常已消失，ledger 仍標 open，建議驗證")
            write_activity_log(agent, "auto_heal_observed", f"{cid}: {message}")

        if not cron_mode:
            print()

    # 3. 寫入新條目到 ledger
    changed = False
    if new_entries:
        existing = list(raw_data.get("defects") or [])
        for ne in new_entries:
            existing.append(ne)
        raw_data["defects"] = existing
        save_ledger(raw_data)
        changed = True
        if not cron_mode:
            print(f"📌 Ledger 已更新：新增 {len(new_entries)} 條 open 記錄")
            print()

    # 4. 處理復發
    if regressions:
        existing = list(raw_data.get("defects") or [])
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        for d in existing:
            if isinstance(d, dict) and d.get("id") in regressions:
                d["status"] = "needs_reverify"
                d["owner_last"] = agent
                d["updated_at"] = now_str
                notes = d.get("notes", "")
                tag = f"[regression @ {now_str}]"
                if tag not in notes:
                    d["notes"] = (notes + " " + tag).strip()
        raw_data["defects"] = existing
        save_ledger(raw_data)
        changed = True
        if not cron_mode:
            print(f"📌 Ledger 已更新：{len(regressions)} 條標記為 needs_reverify")
            print()

    if not changed and not cron_mode:
        print("📌 Ledger 無變更（所有狀態一致）")
        print()

    # 5. 寫入 JSON 報告
    report = {
        "check_time": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent": agent,
        "project_root": str(PROJECT_ROOT),
        "all_ok": all_ok,
        "checks": results,
        "ledger_changed": changed,
        "new_entries_added": len(new_entries),
        "regressions_detected": len(regressions),
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not cron_mode:
        print(f"📄 報告寫入: {OUTPUT_PATH}")
        print()

    # 6. 摘要
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = sum(1 for r in results if not r["ok"])

    if cron_mode:
        # 靜默模式：只在有異常時輸出
        if not all_ok:
            print(f"🔍 _tang_health_check ({agent}) — 發現 {fail_count} 個異常")
            for r in results:
                if not r["ok"]:
                    print(f"  ❌ [{r['id']}] {r['name']}")
                    print(f"      → {r['message']}")
            if new_entries:
                print(f"  📝 Ledger 新增 {len(new_entries)} 條 open 記錄")
            if regressions:
                print(f"  ⚠️  {len(regressions)} 個異常被標記為 needs_reverify")
            print(f"  完整報告: {OUTPUT_PATH}")
    else:
        print(f"{'='*50}")
        print(f"  健康檢查摘要")
        print(f"{'='*50}")
        print(f"  ✅ 正常:        {ok_count}")
        print(f"  ❌ 異常:        {fail_count}")
        print(f"  新開 ledger:   {len(new_entries)}")
        print(f"  復發偵測:      {len(regressions)}")
        print()
        if all_ok:
            print("  ✅ 全部正常，無需處理。")
        else:
            print("  ⚠️  發現異常，請查看上方 ❌ 項目。")
            print("  執行 verify_cmd 或手動確認後更新 ledger。")

    return 0 if all_ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n💥 嚴重錯誤: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(2)
