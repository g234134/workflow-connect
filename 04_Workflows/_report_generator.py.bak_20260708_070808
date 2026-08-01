"""_report_generator.py — v2.56 自動結案報告器（Groq 70b 彈夾 + v2.54 費率戰報）。

讀取 06_Exports_Output/reports/scout_last_pipeline.json（由偵察兵寫入）與 elite_cache.json，
產出「技術亮點」「使用建議」結案草案；可選 --telegram-send 發送尚書省。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_secret, get_tang_gov_root, resolve_agent_output_path  # type: ignore

PIPELINE_FN = "scout_last_pipeline.json"
ELITE_FN = "elite_cache.json"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _reports_dir(root: str) -> str:
    return resolve_agent_output_path(root, "06_Exports_Output", "reports")


def _tang_groq(body: bytes) -> Tuple[int, Any, Dict[str, Any]]:
    wf = _here
    if wf not in sys.path:
        sys.path.insert(0, wf)
    from _tang_http import json_request_dual_ssl  # type: ignore

    from GroqHybridRecovery_Agent import GROQ_MODEL_DEFAULT, GROQ_URL_DEFAULT  # type: ignore

    url = (get_secret("GROQ_API_URL", "") or GROQ_URL_DEFAULT).strip()
    key = (get_secret("GROQ_API_KEY", "") or "").strip()
    if not key or "PLACEHOLDER" in key:
        return 0, {"error": "groq_key_missing"}, {}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    meta: Dict[str, Any] = {}
    code, data = json_request_dual_ssl(
        url,
        method="POST",
        headers=headers,
        body=body,
        timeout=120,
        groq_chat_failover=True,
        groq_meta_out=meta,
    )
    return int(code), data, meta


def _extract_json_from_llm(content: str) -> Any:
    sys.path.insert(0, os.path.join(_root, "02_Agents_Core"))
    from GroqHybridRecovery_Agent import _extract_json_from_llm as ext  # type: ignore

    return ext(content)


def load_inputs(root: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    rep = _reports_dir(root)
    pipe_p = os.path.join(rep, PIPELINE_FN)
    elite_p = os.path.join(rep, ELITE_FN)
    if not os.path.isfile(pipe_p):
        raise FileNotFoundError(f"missing {pipe_p}")
    with open(pipe_p, "r", encoding="utf-8") as f:
        pipe = json.load(f)
    elite: Dict[str, Any] = {}
    if os.path.isfile(elite_p):
        with open(elite_p, "r", encoding="utf-8") as f:
            elite = json.load(f)
    return pipe, elite


def _estimate_virtual_savings_twd(pipe: Dict[str, Any], elite: Dict[str, Any]) -> Tuple[float, str]:
    """依 v2.54 model_registry 標價 × 推定 token（粗估）示意虛擬節省。"""
    wf = _here
    if wf not in sys.path:
        sys.path.insert(0, wf)
    from _tang_http import _load_registry  # type: ignore

    reg = _load_registry()
    fx = float((reg.get("fx") or {}).get("twd_per_usd") or 32.0)
    models = reg.get("models") if isinstance(reg.get("models"), dict) else {}
    main = models.get("llama-3.3-70b-versatile")
    pin = float((main or {}).get("pricing_usd_per_1m_tokens", {}).get("input") or 0.59)
    pout = float((main or {}).get("pricing_usd_per_1m_tokens", {}).get("output") or 0.79)
    mr = pipe.get("match_report") or {}
    scanned = int(mr.get("scanned") or 0)
    # 粗估本次 ROI 比對若全用 70b 雲端之 token（僅示意）
    est_prompt = 800 + min(scanned, 5000) * 40
    est_out = 900
    usd = (est_prompt / 1e6) * pin + (est_out / 1e6) * pout
    twd = round(usd * fx, 2)
    note = f"（示意：以 70b 標價 input={pin}/1M output={pout}/1M ×{fx} TWD/USD 粗估 token）"
    return twd, note


def generate_closing_draft(
    pipe: Dict[str, Any],
    elite: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    lead = pipe.get("lead") or {}
    mr = pipe.get("match_report") or {}
    pool = int(mr.get("pool_size") or 0)
    scanned = int(mr.get("scanned") or 0)
    elite_n = int(mr.get("elite_assets_matched") or 0)
    noise = 0.0
    if scanned > 0:
        noise = round(100.0 * (scanned - elite_n) / scanned, 2)
    elite_total = int((elite.get("stats") or {}).get("elite_count") or len(elite.get("entries") or []))
    if elite_total and pool:
        noise_alt = round(100.0 * max(0, pool - elite_total) / pool, 2)
    else:
        noise_alt = noise
    noise_use = max(noise, noise_alt)

    top = mr.get("top_matches") or []
    a_list_lines = []
    for i, x in enumerate(top[:12], 1):
        a_list_lines.append(
            f"{i}. {x.get('name')} | score={x.get('heuristic_score')} | sim={x.get('local_similarity_pct')}% | {x.get('source_path')}"
        )
    a_block = "\n".join(a_list_lines) if a_list_lines else "（本次無 A 級命中清單）"

    twd_saved, price_note = _estimate_virtual_savings_twd(pipe, elite)

    system = (
        "你是大唐戰車商務副官。根據下列結構化資料，輸出 ONLY raw JSON，鍵為："
        "technical_highlights（字串陣列 3-6 條）、usage_recommendations（字串陣列 3-6 條）、"
        "executive_summary（<=400字繁中）。語氣精煉、可執行、避免空話。"
    )
    user = json.dumps(
        {
            "lead": lead,
            "match_report": {
                "coverage_pct": mr.get("coverage_pct"),
                "is_high_yield": mr.get("is_high_yield"),
                "elite_assets_matched": elite_n,
                "scanned": scanned,
                "pool_size": pool,
            },
            "elite_index_stats": elite.get("stats"),
            "noise_filter_rate_pct_hint": noise_use,
            "virtual_savings_twd_hint": twd_saved,
        },
        ensure_ascii=False,
    )[:14000]
    payload = {
        "model": get_secret("GROQ_MODEL", "").strip() or "llama-3.3-70b-versatile",
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    code, data, meta = _tang_groq(body)
    highlights: List[str] = []
    recs: List[str] = []
    exec_sum = ""
    if code == 200 and isinstance(data, dict):
        try:
            choices = data.get("choices") or []
            content = str((choices[0].get("message") or {}).get("content") or "")
        except Exception:
            content = ""
        obj = _extract_json_from_llm(content)
        if isinstance(obj, dict):
            th = obj.get("technical_highlights")
            ur = obj.get("usage_recommendations")
            exec_sum = str(obj.get("executive_summary") or "")
            if isinstance(th, list):
                highlights = [str(x) for x in th[:8]]
            if isinstance(ur, list):
                recs = [str(x) for x in ur[:8]]

    if not highlights:
        highlights = [
            "已接通 elite_cache 與 scout 管線（v2.56）",
            f"池內掃描/快取比對量：scanned={scanned} pool={pool}",
        ]
    if not recs:
        recs = [
            "若覆蓋率偏低：擴充 elite_cache 或調整案源關鍵字與技術棧描述",
            "若覆蓋率高：優先複核命中資產授權與交付邊界後再報價",
        ]

    lines = [
        "【結案報告草案 · v2.56】",
        f"生成時間：{_utc_iso()}",
        "",
        f"一、處理總量：池 {pool} 件；本次比對掃描/快取 {scanned} 條；A 級命中 {elite_n} 條",
        f"二、雜訊過濾率（示意）：{noise_use}%（相對掃描樣本中非 elite 命中占比）",
        f"三、本次精煉虛擬節省（示意 TWD）：約 {twd_saved} 元 {price_note}",
        "",
        "四、A 級資產清單（Top）：",
        a_block,
        "",
        "五、技術亮點：",
        *[f"  · {h}" for h in highlights],
        "",
        "六、使用建議：",
        *[f"  · {r}" for r in recs],
        "",
        "七、摘要：",
        exec_sum or "（Groq 未回摘要，以上為規則化草案骨架）",
    ]
    try:
        sys.path.insert(0, os.path.join(_root, "02_Agents_Core"))
        from GroqHybridRecovery_Agent import format_groq_quota_telegram_suffix  # type: ignore

        ammo, cost = format_groq_quota_telegram_suffix()
        lines.extend(["", "附：彈藥餘裕／精煉花費（v2.54 戰報格式）", ammo, cost])
    except Exception:
        pass
    lines.append("")
    lines.append(f"Groq meta（無金鑰）：{json.dumps(meta, ensure_ascii=False)[:800]}")
    text = "\n".join(lines)
    meta_out = {
        "http_code": code,
        "groq_models_tried": meta.get("models_tried"),
        "failover_chain": meta.get("failover_chain"),
    }
    return text, meta_out


def _telegram_alert_chunks(text: str, *, reply_markup: Optional[Dict[str, Any]] = None) -> None:
    sys.path.insert(0, os.path.join(_root, "02_Agents_Core"))
    from Code_Cleaner_Throttled_Agent import _telegram_alert  # type: ignore

    chunks: List[str] = []
    cur = ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > 3800:
            chunks.append(cur)
            cur = line + "\n"
        else:
            cur += line + "\n"
    if cur.strip():
        chunks.append(cur)
    for i, ch in enumerate(chunks):
        mk = reply_markup if i == 0 else None
        _telegram_alert(ch.strip(), reply_markup=mk)


def main() -> int:
    parser = argparse.ArgumentParser(description="結案報告草案產生器 v2.56")
    parser.add_argument("--write", action="store_true", help="寫入 reports/closing_draft_*.txt")
    parser.add_argument("--telegram-send", action="store_true", help="以 Telegram 發送（可分段）")
    args = parser.parse_args()

    root = get_tang_gov_root()
    try:
        pipe, elite = load_inputs(root)
    except FileNotFoundError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 2
    text, meta = generate_closing_draft(pipe, elite)
    print(text)
    print(json.dumps({"ok": True, "meta": meta}, ensure_ascii=False, indent=2))

    if args.write:
        out_dir = _reports_dir(root)
        fn = f"closing_draft_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.txt"
        p = os.path.join(out_dir, fn)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        print(json.dumps({"written": p}, ensure_ascii=False))

    if args.telegram_send:
        _telegram_alert_chunks(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
