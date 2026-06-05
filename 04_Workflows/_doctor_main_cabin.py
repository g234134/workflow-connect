"""_doctor_main_cabin.py — gov_main 體檢 (能力 + 密鑰 + 既有 Agent 整合)"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, Tuple

from _tang_http import json_request_dual_ssl  # type: ignore
from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)


def _ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def _warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


def _err(msg: str) -> None:
    print(f"  [ERR]  {msg}")


def section(title: str) -> None:
    print(f"\n── {title} ──")


def check_packages() -> int:
    section("第三方套件")
    fails = 0
    pkgs = ["pydantic", "yaml", "watchdog", "tenacity", "psutil", "rich"]
    import importlib
    import importlib.metadata as md

    for p in pkgs:
        try:
            importlib.import_module(p)
            ver = md.version("PyYAML" if p == "yaml" else p)
            _ok(f"{p:10s} {ver}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            _err(f"{p}: {e!r}")
    return fails


def check_core_modules() -> int:
    section("核心模組（gov_paths / Base_Agent / Registry）")
    fails = 0
    try:
        from gov_paths import (  # type: ignore
            get_artifact_path,
            get_secret,
            get_tang_gov_root,
            resolve_agent_output_path,
        )
        root = get_tang_gov_root()
        sp = get_artifact_path("status_json")
        c3 = resolve_agent_output_path(root, "03_RAG_Database", "c3_logs")
        _ok(f"gov_paths: root={root}")
        _ok(f"  status_json={sp}")
        _ok(f"  C3_Logs   ={c3}")
    except Exception as e:  # noqa: BLE001
        fails += 1
        _err(f"gov_paths: {e!r}")

    try:
        from Base_Agent import AgentStatus, Base_Agent  # type: ignore  # noqa: F401
        _ok("Base_Agent 匯入正常")
    except Exception as e:  # noqa: BLE001
        fails += 1
        _err(f"Base_Agent: {e!r}")

    try:
        from Chariot_Registry import Chariot_Registry  # type: ignore  # noqa: F401
        _ok("Chariot_Registry 匯入正常")
    except Exception as e:  # noqa: BLE001
        fails += 1
        _err(f"Chariot_Registry: {e!r}")
    return fails


def check_existing_agents() -> int:
    section("既有 Agent 類別（僅匯入，不執行）")
    fails = 0
    targets = [
        ("Code_Cleaner_Agent", "Code_Cleaner_Agent"),
        ("Code_Cleaner_Throttled_Agent", "Code_Cleaner_Throttled_Agent"),
        ("Recovery_Agent", "Recovery_Agent"),
        ("GroqHybridRecovery_Agent", "GroqHybridRecovery_Agent"),
        ("Cleanup_Agent", "Cleanup_Agent"),
        ("Indexing_Agent", "Indexing_Agent"),
        ("Liquidation_Agent", "Liquidation_Agent"),
        ("Asset_Value_Evaluator_Agent", "Asset_Value_Evaluator_Agent"),
        ("Warning_Repair_Agent", "Warning_Repair_Agent"),
        ("Telegram_Listener_Agent", "Telegram_Listener_Agent"),
    ]
    for module_name, attr in targets:
        try:
            mod = __import__(module_name)
            if hasattr(mod, attr):
                _ok(f"{module_name}.{attr}")
            else:
                _warn(f"{module_name} 載入但未見類別 {attr}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            _err(f"{module_name}: {e!r}")
    return fails


def check_env_keys() -> Tuple[int, Dict[str, bool]]:
    section(".env 密鑰盤點")
    from gov_paths import get_secret  # type: ignore

    keys = {
        "TELEGRAM_BOT_TOKEN": True,
        "TELEGRAM_ALLOWED_CHAT_IDS": True,
        "GROQ_API_KEY": True,
        "GROQ_MODEL": False,
        "OPENAI_API_KEY": False,
        "ANTHROPIC_API_KEY": False,
        "DIFY_API_KEY": False,
    }
    fails = 0
    status: Dict[str, bool] = {}
    for k, required in keys.items():
        v = (get_secret(k, "") or "").strip()
        ok = bool(v) and "PLACEHOLDER" not in v.upper()
        status[k] = ok
        if ok:
            _ok(f"{k}: present")
        else:
            if required:
                fails += 1
                _err(f"{k}: 缺失或為 PLACEHOLDER")
            else:
                _warn(f"{k}: 缺失或為 PLACEHOLDER（可選）")
    return fails, status


def check_groq(status: Dict[str, bool]) -> int:
    section("Groq 雲端副官實打 (chat.completions)")
    if not status.get("GROQ_API_KEY"):
        _warn("略過：GROQ_API_KEY 不可用")
        return 0
    from gov_paths import get_secret  # type: ignore

    key = (get_secret("GROQ_API_KEY", "") or "").strip()
    primary = (get_secret("GROQ_MODEL", "") or "llama-3.3-70b-versatile").strip()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    payload = {
        "model": primary,
        "max_tokens": 16,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "Reply with one word."},
            {"role": "user", "content": "ping"},
        ],
    }
    code, data = json_request_dual_ssl(
        url,
        method="POST",
        headers=headers,
        body=json.dumps(payload).encode("utf-8"),
        timeout=25,
        groq_chat_failover=True,
    )
    if code == 200:
        txt = ""
        try:
            txt = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        except Exception:  # noqa: BLE001
            pass
        _ok(f"Groq chat.completions: 200 → {txt!r}（智慧撥彈鏈）")
        return 0
    err_msg = ""
    if isinstance(data, dict):
        if isinstance(data.get("error"), dict):
            err_msg = str(data["error"].get("message"))[:120]
        elif isinstance(data.get("error"), str):
            err_msg = data["error"][:120]
    _warn(f"Groq ping: HTTP {code} {err_msg}")
    _err("Groq 實打失敗（含 failover）")
    return 1


def check_telegram(status: Dict[str, bool]) -> int:
    section("Telegram getMe 心跳")
    if not status.get("TELEGRAM_BOT_TOKEN"):
        _warn("略過：TELEGRAM_BOT_TOKEN 不可用")
        return 0
    from gov_paths import get_secret  # type: ignore

    token = (get_secret("TELEGRAM_BOT_TOKEN", "") or "").strip()
    code, data = json_request_dual_ssl(
        f"https://api.telegram.org/bot{token}/getMe",
        method="GET",
        timeout=15,
    )
    if code == 200 and isinstance(data, dict) and data.get("ok"):
        u = data.get("result") or {}
        _ok(f"Bot @{u.get('username')} (id={u.get('id')}, name={u.get('first_name')})")
        return 0
    _err(f"getMe 失敗: HTTP {code} → {data}")
    return 1


def main() -> int:
    print("==== gov_main 主艙體檢 ====")
    print(f"Python   : {sys.version.split()[0]}")
    print(f"venv     : {sys.prefix}")
    print(f"PYTHONPATH lead : {sys.path[:3]}")

    fails = 0
    fails += check_packages()
    fails += check_core_modules()
    fails += check_existing_agents()
    f, status = check_env_keys()
    fails += f
    fails += check_groq(status)
    fails += check_telegram(status)

    print("\n==== 體檢結論 ====")
    if fails == 0:
        print("  全綠燈：主艙具備所需套件、密鑰、Agent 匯入與雲端通訊能力。")
    else:
        print(f"  發現 {fails} 處紅/黃燈，請依上方節段排除。")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
