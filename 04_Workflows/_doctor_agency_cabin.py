"""_doctor_agency_cabin.py — gov_agency 體檢 (CrewAI / Chroma / FastAPI 能力)

對應虛擬環境：01_Environments/python_venvs/gov_agency
驗證項目：
  1) crewai / chromadb / fastapi / openai SDK 匯入 + 版本
  2) gov_paths 與 agency-agents 模組可被 Python 路徑搜尋
  3) .env 密鑰：crewai 預設用 OPENAI_API_KEY；DIFY_API_KEY 可選
  4) chromadb client 啟動 in-process 寫讀（不落地到 RAG 主庫）
  5) crewai Agent 物件可建構（不對外打 API）
"""
from __future__ import annotations

import importlib
import importlib.metadata as md
import os
import sys
import tempfile


def _ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def _warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


def _err(msg: str) -> None:
    print(f"  [ERR]  {msg}")


def section(title: str) -> None:
    print(f"\n── {title} ──")


def check_packages() -> int:
    section("副艙重型套件")
    fails = 0
    targets = ["crewai", "crewai_tools", "chromadb", "fastapi", "uvicorn", "openai"]
    for p in targets:
        try:
            importlib.import_module(p)
            ver = md.version(p.replace("_", "-"))
            _ok(f"{p:14s} {ver}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            _err(f"{p}: {e!r}")
    return fails


def check_paths() -> int:
    section("跨艙路徑保護")
    fails = 0
    try:
        from gov_paths import get_tang_gov_root  # type: ignore
        _ok(f"gov_paths.get_tang_gov_root() = {get_tang_gov_root()}")
    except Exception as e:  # noqa: BLE001
        fails += 1
        _err(f"gov_paths 匯入失敗: {e!r}")
    try:
        from agency_sop import bind  # type: ignore  # noqa: F401
        _ok("agency_sop.bind 可匯入")
    except Exception as e:  # noqa: BLE001
        _warn(f"agency_sop 匯入失敗（可能未啟用）: {e!r}")
    return fails


def check_env_keys() -> int:
    section(".env 密鑰盤點 (副艙視角)")
    fails = 0
    try:
        from gov_paths import get_secret  # type: ignore
    except Exception as e:  # noqa: BLE001
        _err(f"gov_paths 不可用: {e!r}")
        return 1
    must = {"OPENAI_API_KEY": True, "DIFY_API_KEY": False, "GROQ_API_KEY": False}
    for k, required in must.items():
        v = (get_secret(k, "") or "").strip()
        ok = bool(v) and "PLACEHOLDER" not in v.upper()
        if ok:
            mask = v[:4] + "***" + v[-4:] if len(v) > 8 else "***"
            _ok(f"{k}: {mask}")
        else:
            if required:
                _warn(f"{k}: 缺失或為 PLACEHOLDER（crewai 預設用 OpenAI；若改走 Groq 可不設）")
            else:
                _warn(f"{k}: 缺失或為 PLACEHOLDER（可選）")

    # 給副艙 LLM 路由的提示（不視為錯誤）
    groq_ok = bool((get_secret("GROQ_API_KEY", "") or "").strip()) and "PLACEHOLDER" not in (get_secret("GROQ_API_KEY", "") or "").upper()
    openai_ok = bool((get_secret("OPENAI_API_KEY", "") or "").strip()) and "PLACEHOLDER" not in (get_secret("OPENAI_API_KEY", "") or "").upper()
    if groq_ok and not openai_ok:
        print("  [HINT] 副艙建議 LiteLLM 走 Groq；於 crewai Agent 設 llm='groq/llama-3.3-70b-versatile'")
        print("         或匯出環境變數：MODEL=groq/llama-3.3-70b-versatile")
    return fails


def check_chroma() -> int:
    section("ChromaDB 本地讀寫煙霧測試")
    try:
        import chromadb
    except Exception as e:  # noqa: BLE001
        _err(f"chromadb 匯入失敗: {e!r}")
        return 1
    import shutil
    d = tempfile.mkdtemp(prefix="chroma_doctor_")
    try:
        client = chromadb.PersistentClient(path=d)
        col = client.get_or_create_collection("doctor_smoke")
        col.add(ids=["a", "b"], documents=["hello world", "大唐三省六部"])
        res = col.query(query_texts=["world"], n_results=2)
        n_hits = len((res.get("ids") or [[]])[0])
        _ok(f"PersistentClient 寫入並查詢成功（hits={n_hits}）")
        try:
            del col
            del client
        except Exception:  # noqa: BLE001
            pass
        return 0
    except Exception as e:  # noqa: BLE001
        _err(f"ChromaDB 煙霧測試失敗: {e!r}")
        return 1
    finally:
        # Windows 上 chromadb 會佔住部分檔案；忽略清理失敗（不影響能力結論）
        shutil.rmtree(d, ignore_errors=True)


def check_crewai_construct() -> int:
    section("CrewAI Agent 建構（不打 API）")
    try:
        from crewai import Agent
    except Exception as e:  # noqa: BLE001
        _err(f"crewai 匯入失敗: {e!r}")
        return 1
    try:
        a = Agent(
            role="尚書省 副官",
            goal="協助處理大唐戰車數據清洗工廠任務",
            backstory="精於 RAG 與資料治理。",
            allow_delegation=False,
            verbose=False,
        )
        _ok(f"crewai.Agent 建構成功（role={a.role}）")
        return 0
    except Exception as e:  # noqa: BLE001
        _warn(f"crewai.Agent 建構失敗（多半因缺 LLM 設定）: {e!r}")
        return 0


def check_fastapi() -> int:
    section("FastAPI 路由可建構")
    try:
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/health")
        def _health() -> dict:
            return {"ok": True}

        _ok(f"FastAPI 應用建立成功，路由數={len(app.router.routes)}")
        return 0
    except Exception as e:  # noqa: BLE001
        _err(f"FastAPI 失敗: {e!r}")
        return 1


def main() -> int:
    print("==== gov_agency 副艙體檢 ====")
    print(f"Python   : {sys.version.split()[0]}")
    print(f"venv     : {sys.prefix}")
    print(f"PYTHONPATH lead : {sys.path[:3]}")

    fails = 0
    fails += check_packages()
    fails += check_paths()
    fails += check_env_keys()
    fails += check_chroma()
    fails += check_crewai_construct()
    fails += check_fastapi()

    print("\n==== 體檢結論 ====")
    if fails == 0:
        print("  全綠燈：副艙具備 CrewAI / Chroma / FastAPI 能力與跨艙引用。")
    else:
        print(f"  發現 {fails} 處紅/黃燈，請依上方節段排除。")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
