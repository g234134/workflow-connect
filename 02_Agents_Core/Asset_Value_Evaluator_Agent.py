# Asset_Value_Evaluator_Agent.py — 兵部·數據精煉（Asset Value）
# SOP 綁定：02_Agents_Core/Agent_SOP_Template.md（v2.5）
# 任務：從 05_Temp_Cache/cleaned_full 隨機抽取 N 筆，先本地 heuristic 評估「功能價值」，
#       僅高難度（白名單副檔 + 本地評分含糊）才送 Groq；結果寫 reports，狀態局部回寫，Telegram 終戰報。

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from Chariot_Registry import Chariot_Registry  # type: ignore
from Code_Cleaner_Throttled_Agent import (  # type: ignore
    GROQ_DELAY_SEC,
    _telegram_alert,
)
from GroqHybridRecovery_Agent import (  # type: ignore
    GROQ_MODEL_DEFAULT,
    GROQ_URL_DEFAULT,
    format_groq_quota_telegram_suffix,
    reset_groq_wave_usage,
    _http_json,
    _extract_json_from_llm,
)
from gov_paths import (  # type: ignore
    get_secret,
    get_tang_gov_root,
    resolve_agent_output_path,
)


GROQ_WHITELIST_EXT = {".py", ".php", ".json", ".jsonc", ".json5", ".yml", ".yaml", ".toml"}

DIFFICULT_CASE_LIBRARY = "difficult_case_library.json"
LOCAL_JUDGE_RULES = "local_judge_rules.json"


def _case_library_path(dest_root: str) -> str:
    d = resolve_agent_output_path(dest_root, "06_Exports_Output", "reports")
    return os.path.join(d, DIFFICULT_CASE_LIBRARY)


def _local_judge_rules_path(dest_root: str) -> str:
    d = resolve_agent_output_path(dest_root, "06_Exports_Output", "reports")
    return os.path.join(d, LOCAL_JUDGE_RULES)


def _norm_judge_path(p: Any) -> str:
    if not p:
        return ""
    return os.path.normpath(str(p)).replace("\\", "/").lower()


def _load_difficult_case_library(dest_root: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """回傳 (by_sha, by_path)：路徑鍵已正規化；by_path 的值與案例庫條目為同一 dict。"""
    p = _case_library_path(dest_root)
    by_sha: Dict[str, Any] = {}
    by_path: Dict[str, Any] = {}
    if not os.path.isfile(p):
        return by_sha, by_path
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return by_sha, by_path
        raw_cases = data.get("cases") or {}
        if isinstance(raw_cases, dict):
            by_sha = {}
            for k, v in raw_cases.items():
                if not isinstance(v, dict):
                    continue
                kk = str(k).strip().lower()
                if kk:
                    by_sha[kk] = v
        for ent in by_sha.values():
            for pk in ("stored_path", "source_path"):
                np = _norm_judge_path(ent.get(pk))
                if np:
                    by_path.setdefault(np, ent)
        aliases = data.get("path_aliases") or {}
        if isinstance(aliases, dict):
            for norm, sha_key in aliases.items():
                nk = _norm_judge_path(norm)
                sk = str(sha_key or "").strip()
                if nk and sk and sk in by_sha:
                    by_path.setdefault(nk, by_sha[sk])
        path_only = data.get("path_only") or {}
        if isinstance(path_only, dict):
            for norm, ent in path_only.items():
                nk = _norm_judge_path(norm)
                if nk and isinstance(ent, dict):
                    by_path.setdefault(nk, ent)
    except Exception:  # noqa: BLE001
        pass
    return by_sha, by_path


def _lookup_case_entry(
    by_sha: Dict[str, Any],
    by_path: Dict[str, Any],
    rec: Dict[str, Any],
    record_fp: str,
    sha_key: str,
) -> Optional[Dict[str, Any]]:
    if sha_key and sha_key in by_sha:
        return by_sha[sha_key]
    for p in (
        _norm_judge_path(rec.get("stored_path")),
        _norm_judge_path(rec.get("source_path")),
        _norm_judge_path(record_fp),
    ):
        if p and p in by_path:
            return by_path[p]
    return None


def _load_local_judge_rules(dest_root: str) -> Dict[str, Any]:
    p = _local_judge_rules_path(dest_root)
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _local_judge_match(
    rules: Dict[str, Any],
    *,
    ext: str,
    otype: str,
    local_score: float,
    confidence: float,
    ambiguous: bool,
) -> Tuple[bool, str]:
    """曾高失敗率之灰區特徵 → 跳過雲端，改走本地策略。"""
    if not ambiguous or not rules:
        return False, ""
    profiles = rules.get("dodge_profiles") or []
    if not isinstance(profiles, list):
        return False, ""
    ex = ext.lower()
    ot = (otype or "unknown").lower()
    for pr in profiles:
        if not isinstance(pr, dict):
            continue
        if str(pr.get("extension") or "").lower() != ex:
            continue
        if str(pr.get("original_type") or "").lower() != ot:
            continue
        lo = float(pr.get("local_score_min", 0))
        hi = float(pr.get("local_score_max", 10))
        if not (lo <= local_score <= hi):
            continue
        ch = float(pr.get("confidence_max", 1.0))
        if confidence > ch:
            continue
        rid = str(pr.get("rule_id") or "dodge")
        return True, f"local_judge:{rid}"
    return False, ""

# 本地評分權重
TYPE_BASE = {
    "python": 6.0, "python_stub": 5.0,
    "php": 5.5,
    "javascript": 4.5, "typescript": 4.8, "javascript_react": 5.0, "typescript_react": 5.0,
    "vue": 4.8,
    "html": 3.0, "css": 2.0, "scss": 2.5, "less": 2.5,
    "sql": 5.0,
    "json": 4.0, "jsonc": 4.0, "json5": 4.0,
    "yaml": 3.5, "toml": 3.5,
    "markdown": 2.5, "rst": 2.0, "text": 1.0,
    "shell": 4.0, "powershell": 4.0, "batch": 3.0,
    "dockerfile": 4.5,
    "rust": 5.5, "go": 5.5, "java": 5.0, "kotlin": 5.0,
    "c": 5.0, "c_header": 4.0, "cpp": 5.0, "cpp_header": 4.0,
    "ruby": 4.5, "perl": 3.5, "lua": 4.0,
    "swift": 5.0, "dart": 4.5, "scala": 4.5,
    "csv": 1.5, "tsv": 1.5, "xml": 2.5,
    "ini": 2.0,
}

VENDOR_HINTS = (
    "node_modules", "site-packages", "vendor",
    "dist", "build", ".min.", "/min/",
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_file_quick(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _heuristic_score(rec: Dict[str, Any]) -> Tuple[float, float, List[str]]:
    """回傳 (score 0~10, confidence 0~1, tags)。本地啟發式：類型 / 結構 / 大小 / 摘要密度 / vendor 折扣。"""
    tags: List[str] = []
    otype = str(rec.get("original_type") or "")
    base = TYPE_BASE.get(otype, 1.5)

    summary = rec.get("content_summary") or {}
    size = int(rec.get("size_bytes") or 0)
    src = str(rec.get("source_path") or "").replace("\\", "/").lower()

    # 類型基礎
    score = base
    tags.append(f"type:{otype or 'unknown'}")

    # vendor / 三方折扣
    if any(v in src for v in VENDOR_HINTS):
        score -= 2.5
        tags.append("vendor_or_minified")

    # 結構特徵：python / php
    funcs = summary.get("functions") or []
    classes = summary.get("classes") or []
    imports = summary.get("imports") or []
    if otype in ("python", "python_stub", "php"):
        score += min(2.5, 0.05 * len(funcs) + 0.15 * len(classes) + 0.04 * len(imports))
        if classes:
            tags.append(f"classes:{len(classes)}")
        if funcs:
            tags.append(f"funcs:{len(funcs)}")

    # JSON 家族：節點豐度
    if otype in ("json", "jsonc", "json5"):
        if summary.get("json_valid") is False:
            score -= 1.0
            tags.append("json_invalid")
        items = int(summary.get("items_count") or 0)
        score += min(2.0, items / 50.0)
        if items:
            tags.append(f"json_items:{items}")

    # SQL：陳述句數量
    if otype == "sql":
        kw = summary.get("keywords") or {}
        kw_total = sum(int(v) for v in kw.values()) if isinstance(kw, dict) else 0
        score += min(2.0, kw_total / 10.0)
        if kw_total:
            tags.append(f"sql_kw:{kw_total}")

    # 文字密度：char_count / size 比例
    char_count = int(summary.get("char_count") or 0)
    if size > 0 and char_count > 0:
        density = char_count / max(1, size)
        if density < 0.3:  # 太多控制字符 / mojibake 殘渣
            score -= 0.8
            tags.append("low_text_density")
        else:
            score += 0.3 * min(1.0, density)

    # 太小或太大
    if size < 64:
        score -= 1.5
        tags.append("tiny")
    elif size > 4 * 1024 * 1024:
        score -= 0.5
        tags.append("very_large")

    # 摘要太空（只有 line_count）
    rich_keys = [k for k in summary.keys() if k not in {"line_count", "non_empty_lines", "char_count", "preview_lines"}]
    if not rich_keys:
        score -= 0.8
        tags.append("summary_thin")

    # clean_status 影響
    cs = str(rec.get("clean_status") or "ok")
    if cs == "warning":
        score -= 0.6
        tags.append("warning")
    elif cs == "failed":
        score -= 2.0
        tags.append("failed")

    # confidence：摘要越豐富、類型越明確 → 越自信
    confidence = 0.5
    if otype and otype != "unknown":
        confidence += 0.2
    if rich_keys:
        confidence += 0.2
    if size >= 64:
        confidence += 0.05
    confidence = max(0.1, min(0.95, confidence))

    score = max(0.0, min(10.0, score))
    return round(score, 3), round(confidence, 3), tags


def _grade(score: float) -> str:
    if score >= 7.5:
        return "A"
    if score >= 5.5:
        return "B"
    if score >= 3.5:
        return "C"
    return "D"


def _flatten_summary_for_match(summary: Any) -> str:
    if not isinstance(summary, dict):
        return ""
    parts: List[str] = []
    for k in (
        "preview_lines",
        "functions",
        "classes",
        "imports",
        "keywords",
        "items_count",
        "line_count",
        "char_count",
    ):
        v = summary.get(k)
        if v is None:
            continue
        parts.append(f"{k}={json.dumps(v, ensure_ascii=False)[:800]}")
    return "\n".join(parts)


def _semantic_overlap_pct(needle: str, haystack: str) -> float:
    """本地「語義覆蓋」近似：Jaccard(詞袋) 與 SequenceMatcher 混合 → 0~100。"""
    from difflib import SequenceMatcher

    a = re.sub(r"\s+", " ", (needle or "").lower()).strip()
    b = re.sub(r"\s+", " ", (haystack or "").lower()).strip()
    if not a or not b:
        return 0.0
    wa = {w for w in re.split(r"[^\w+./#-]+", a) if len(w) > 1}
    wb = {w for w in re.split(r"[^\w+./#-]+", b) if len(w) > 1}
    if not wa or not wb:
        seq = SequenceMatcher(None, a[:4000], b[:40000]).ratio()
        return round(100.0 * seq, 2)
    inter = len(wa & wb)
    union = len(wa | wb) or 1
    jacc = inter / union
    seq = SequenceMatcher(None, a[:4000], b[:12000]).ratio()
    blended = 0.55 * jacc + 0.45 * seq
    return round(100.0 * max(0.0, min(1.0, blended)), 2)


def _tang_http_groq_chat(body: bytes) -> Tuple[int, Any, Dict[str, Any]]:
    """走 v2.54 配額護欄（RPM/RPD/TPM + failover）。"""
    wf = os.path.normpath(os.path.join(_here, "..", "04_Workflows"))
    if wf not in sys.path:
        sys.path.insert(0, wf)
    from _tang_http import json_request_dual_ssl  # type: ignore

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
        timeout=90,
        groq_chat_failover=True,
        groq_meta_out=meta,
    )
    return int(code), data, meta


def groq_roi_semantic_similarity_pct(
    opportunity_text: str,
    asset_blob: str,
) -> Tuple[Optional[float], str]:
    """單次 Groq 評分（0~100）；受 model_registry.yaml 護欄約束。失敗回 (None, reason)。"""
    model = get_secret("GROQ_MODEL", "") or GROQ_MODEL_DEFAULT
    snippet_opp = opportunity_text[:3500]
    snippet_ast = asset_blob[:3500]
    system = (
        "You compare a freelance/market opportunity against an internal code-asset summary. "
        "Return ONLY raw JSON: {\"similarity\": <number 0-100>} where 100 means the asset "
        "would very likely satisfy most of the opportunity without major new work."
    )
    user = f"OPPORTUNITY:\n{snippet_opp}\n\nASSET_SUMMARY:\n{snippet_ast}\n"
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    code, data, _meta = _tang_http_groq_chat(body)
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
    try:
        v = float(obj.get("similarity"))
    except Exception:  # noqa: BLE001
        return None, "groq_similarity_not_number"
    return max(0.0, min(100.0, v)), "groq_ok"


def match_against_registry(
    opportunity: Dict[str, Any],
    *,
    dest_root: Optional[str] = None,
    max_pool_scan: int = 2400,
    seed: Optional[int] = None,
    use_groq_semantic: bool = False,
) -> Dict[str, Any]:
    """
    比對 cleaned_full 資產池（≈3.6 萬量級）：抽樣掃描，挑出啟發式 Score>9 的資產，
    與案源需求做本地語義覆蓋率；可選 1 次 Groq 覆核（仍走 v2.54 彈藥護欄）。

    高產能案源：存在 Score>9 且 grade A 之資產，使覆蓋率 >= 70%。
    """
    root = os.path.abspath(dest_root or get_tang_gov_root())
    cleaned = resolve_agent_output_path(root, "05_Temp_Cache", "cleaned_full")
    if not os.path.isdir(cleaned):
        return {
            "ok": False,
            "error": "cleaned_full_missing",
            "coverage_pct": 0.0,
            "is_high_yield": False,
            "assets_considered": 0,
            "elite_assets_matched": 0,
        }

    title = str(opportunity.get("title") or "")
    desc = str(opportunity.get("description") or opportunity.get("body") or "")
    budget = str(opportunity.get("budget") or "")
    needle = "\n".join([title, desc, budget]).strip()

    paths = sorted(
        os.path.join(cleaned, fn)
        for fn in os.listdir(cleaned)
        if fn.endswith(".json")
    )
    pool_size = len(paths)
    rng = random.Random(seed if seed is not None else 20260509)

    elite: List[Dict[str, Any]] = []
    match_source = "sampled_pool"
    n_scan = 0

    elite_cache_path = os.path.join(
        root, "06_Exports_Output", "reports", "elite_cache.json"
    )
    use_cache = False
    if os.path.isfile(elite_cache_path):
        try:
            with open(elite_cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:  # noqa: BLE001
            cache = {}
        tmp_elite: List[Dict[str, Any]] = []
        for e in cache.get("entries") or []:
            if not isinstance(e, dict):
                continue
            try:
                hs = float(e.get("heuristic_score") or 0)
            except (TypeError, ValueError):
                continue
            if hs <= 9.0:
                continue
            blob = str(e.get("feature_blob") or "")
            tmp_elite.append(
                {
                    "path": e.get("json_path"),
                    "heuristic_score": hs,
                    "grade": str(e.get("grade") or "A"),
                    "blob": blob,
                    "source_path": e.get("source_path"),
                    "name": e.get("name"),
                }
            )
        if tmp_elite:
            elite = tmp_elite
            n_scan = len(elite)
            match_source = "elite_cache"
            use_cache = True

    if not use_cache:
        n_scan = min(max(1, int(max_pool_scan)), pool_size)
        sampled = rng.sample(paths, n_scan) if pool_size else []
        for fp in sampled:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    rec = json.load(f)
            except Exception:  # noqa: BLE001
                continue
            hscore, _conf, _tags = _heuristic_score(rec)
            gr = _grade(hscore)
            if hscore > 9.0 and gr == "A":
                blob = _flatten_summary_for_match(rec.get("content_summary"))
                blob = blob or str(rec.get("source_path") or rec.get("name") or "")
                elite.append(
                    {
                        "path": fp,
                        "heuristic_score": hscore,
                        "grade": gr,
                        "blob": blob,
                        "source_path": rec.get("source_path"),
                        "name": rec.get("name"),
                    }
                )

    best_pct = 0.0
    best_row: Optional[Dict[str, Any]] = None
    groq_note = "skipped"
    for row in elite:
        pct = _semantic_overlap_pct(needle, row["blob"])
        if pct > best_pct:
            best_pct = pct
            best_row = {**row, "local_similarity_pct": pct}

    if (
        use_groq_semantic
        and best_row
        and 55.0 <= best_pct < 70.0
        and best_row.get("blob")
    ):
        gv, reason = groq_roi_semantic_similarity_pct(needle, str(best_row["blob"]))
        time.sleep(GROQ_DELAY_SEC)
        groq_note = reason
        if gv is not None and gv > best_pct:
            best_pct = float(gv)
            if best_row is not None:
                best_row["groq_similarity_pct"] = gv

    is_high = bool(elite) and best_pct >= 70.0
    top_matches = []
    if elite:
        scored = sorted(
            (
                {
                    **e,
                    "local_similarity_pct": _semantic_overlap_pct(needle, e["blob"]),
                }
                for e in elite
            ),
            key=lambda x: x["local_similarity_pct"],
            reverse=True,
        )[:8]
        top_matches = [
            {
                "source_path": x.get("source_path"),
                "name": x.get("name"),
                "heuristic_score": x.get("heuristic_score"),
                "local_similarity_pct": x.get("local_similarity_pct"),
            }
            for x in scored
        ]

    return {
        "ok": True,
        "pool_size": pool_size,
        "scanned": n_scan,
        "match_source": match_source,
        "elite_assets_matched": len(elite),
        "coverage_pct": round(best_pct, 2),
        "is_high_yield": is_high,
        "best_match": best_row,
        "top_matches": top_matches,
        "groq_semantic_note": groq_note,
    }


def _telegram_scout_high_yield(
    *,
    title: str,
    budget: str,
    coverage_pct: float,
    reply_markup: Optional[Dict[str, Any]] = None,
) -> None:
    body = (
        "發現獵物！\n"
        f"案名：[{title[:200]}]\n"
        f"預算：[{budget or '未標示'}]\n"
        f"資產覆蓋率：[{coverage_pct:.1f}%]\n"
        "預估開發成本：極低"
    )
    _telegram_alert(body, reply_markup=reply_markup)


def _groq_value_call(rec: Dict[str, Any]) -> Tuple[Optional[float], Optional[str], str]:
    """送 Groq 取得 (value 0~10, rationale, reason)；失敗時 value=None。"""
    key = (get_secret("GROQ_API_KEY", "") or "").strip()
    if not key or "PLACEHOLDER" in key:
        return None, None, "groq_key_missing"
    model = get_secret("GROQ_MODEL", "") or GROQ_MODEL_DEFAULT
    url = get_secret("GROQ_API_URL", "") or GROQ_URL_DEFAULT
    src = str(rec.get("source_path") or "")
    name = os.path.basename(src) or str(rec.get("name") or "unknown")
    summary = rec.get("content_summary") or {}
    snippet = json.dumps(
        {
            "name": name,
            "extension": rec.get("extension"),
            "original_type": rec.get("original_type"),
            "size_bytes": rec.get("size_bytes"),
            "summary": summary,
        },
        ensure_ascii=False,
    )[:6000]
    system = (
        "You are a senior code reviewer. Rate the *function value* of the described asset "
        "on a 0-10 scale based on the JSON summary. Use these anchors: "
        "0-2 trivial/boilerplate; 3-4 minor utility; 5-6 useful module; "
        "7-8 substantial reusable component; 9-10 core domain logic. "
        'Respond ONLY raw JSON: {"value": <0-10 number>, "rationale": "<<=120 chars>"}.'
    )
    user = f"Asset summary JSON follows.\n{snippet}"
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
    code, data = _http_json(url, method="POST", headers=headers, body=body, timeout=60)
    if code != 200:
        return None, None, f"groq_http_{code}"
    try:
        choices = data.get("choices") or []
        content = str((choices[0].get("message") or {}).get("content") or "")
    except Exception:  # noqa: BLE001
        return None, None, "groq_bad_response"
    obj = _extract_json_from_llm(content)
    if not isinstance(obj, dict):
        return None, None, "groq_not_object"
    try:
        v = float(obj.get("value"))
    except Exception:  # noqa: BLE001
        return None, None, "groq_value_not_number"
    rationale = str(obj.get("rationale") or "")[:200]
    return max(0.0, min(10.0, v)), rationale, "groq_ok"


class Asset_Value_Evaluator_Agent:
    AGENT_NAME = "Asset_Value_Evaluator_Agent"
    DEPARTMENT = "兵部"
    STATUS_KEY = "asset_value_evaluator"

    def __init__(
        self,
        *,
        sample_size: int = 50,
        seed: Optional[int] = None,
        progress_every: int = 0,
        progress_callback: Optional[Any] = None,
    ) -> None:
        self.dest_root = get_tang_gov_root()
        self.sample_size = int(sample_size)
        self.rng = random.Random(seed if seed is not None else 20260509)
        self.progress_every = max(0, int(progress_every))
        # callback signature: fn(state: Dict[str, Any]) -> None
        self.progress_callback = progress_callback
        self.agent = Base_Agent(
            dest_root=self.dest_root, department=self.DEPARTMENT, agent_name=self.AGENT_NAME
        )
        self.cleaned_full_dir = resolve_agent_output_path(
            self.dest_root, "05_Temp_Cache", "cleaned_full"
        )
        self.reports_dir = resolve_agent_output_path(
            self.dest_root, "06_Exports_Output", "reports"
        )
        os.makedirs(self.reports_dir, exist_ok=True)
        self.workflows_dir = resolve_agent_output_path(self.dest_root, "04_Workflows")
        self.registry = Chariot_Registry()

    def _patch_status(self, block: Dict[str, Any]) -> None:
        sp = os.path.join(self.workflows_dir, "Status.json")
        data: Dict[str, Any] = {}
        if os.path.isfile(sp):
            try:
                with open(sp, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:  # noqa: BLE001
                data = {}
        data[self.STATUS_KEY] = block
        data["updated_at"] = _utc_iso()
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _enumerate(self) -> List[str]:
        if not os.path.isdir(self.cleaned_full_dir):
            return []
        return sorted(
            os.path.join(self.cleaned_full_dir, fn)
            for fn in os.listdir(self.cleaned_full_dir)
            if fn.endswith(".json")
        )

    def run(self) -> Dict[str, Any]:
        self.agent.set_status(AgentStatus.Running.value, reason="evaluator_start")
        files = self._enumerate()
        pool_size = len(files)
        if pool_size == 0:
            self.agent.set_status(AgentStatus.Manual.value, reason="empty_pool")
            return {"error": "empty_pool", "pool_size": 0}

        n = min(self.sample_size, pool_size)
        sampled = self.rng.sample(files, n)
        self.agent.log_event(event="sampled", pool_size=pool_size, sampled=n)

        reset_groq_wave_usage()

        t_eval0 = time.monotonic()
        case_by_sha, case_by_path = _load_difficult_case_library(self.dest_root)
        case_library_size = len(case_by_sha)
        case_library_hits = 0
        local_judge_skips = 0
        judge_rules = _load_local_judge_rules(self.dest_root)

        rows: List[Dict[str, Any]] = []
        groq_calls = 0
        groq_success = 0
        grade_counter: Counter = Counter()
        type_counter: Counter = Counter()
        tag_counter: Counter = Counter()

        for fp in sampled:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    rec = json.load(f)
            except Exception as e:  # noqa: BLE001
                rows.append({"record_path": fp, "error": f"read_failed:{e}"})
                continue

            srcp = str(rec.get("source_path") or "").strip()
            cur_sha = str(rec.get("content_sha256") or "").strip().lower()
            if (not cur_sha or len(cur_sha) != 64) and srcp and os.path.isfile(srcp):
                try:
                    rec["content_sha256"] = _sha256_file_quick(srcp).lower()
                except OSError:
                    pass

            ext = str(rec.get("extension") or "").lower()
            otype = str(rec.get("original_type") or "")
            local_score, confidence, tags = _heuristic_score(rec)

            groq_value: Optional[float] = None
            groq_reason: Optional[str] = None
            rationale: Optional[str] = None
            used_groq = False
            case_library_hit = False

            # 雲端介入判準：白名單副檔 + (信心 < 0.65 或 score 落於 4~6 灰區)
            ambiguous = (confidence < 0.65) or (4.0 <= local_score <= 6.0)
            sha_key = str(rec.get("content_sha256") or "").strip().lower()
            cached = _lookup_case_entry(case_by_sha, case_by_path, rec, fp, sha_key)

            dodge, dodge_reason = _local_judge_match(
                judge_rules,
                ext=ext,
                otype=otype or "unknown",
                local_score=float(local_score),
                confidence=float(confidence),
                ambiguous=bool(ambiguous),
            )

            if (
                ext in GROQ_WHITELIST_EXT
                and ambiguous
                and isinstance(cached, dict)
                and cached.get("groq_reason") == "groq_ok"
                and isinstance(cached.get("groq_value"), (int, float))
            ):
                groq_value = float(cached["groq_value"])
                rationale = cached.get("groq_rationale") if isinstance(cached.get("groq_rationale"), str) else None
                groq_reason = "case_library_hit"
                case_library_hit = True
                case_library_hits += 1
            elif ext in GROQ_WHITELIST_EXT and ambiguous and dodge:
                mul = float((judge_rules.get("defaults") or {}).get("local_score_multiplier", 1.0))
                groq_reason = dodge_reason or "local_judge_skip_cloud"
                local_judge_skips += 1
                adj = round(min(10.0, max(0.0, local_score * mul)), 3)
                # 本地修正策略：不呼叫雲端，以調整後本地分數作為最終分（略保守）
                final_score = adj
                grade = _grade(final_score)
                grade_counter[grade] += 1
                type_counter[otype or "unknown"] += 1
                for t in tags:
                    tag_counter[t] += 1
                row = {
                    "stored_path": rec.get("stored_path") or fp,
                    "source_path": rec.get("source_path"),
                    "name": rec.get("name"),
                    "extension": ext,
                    "original_type": otype,
                    "size_bytes": rec.get("size_bytes"),
                    "content_sha256": rec.get("content_sha256"),
                    "clean_status": rec.get("clean_status"),
                    "local_score": local_score,
                    "confidence": confidence,
                    "tags": tags,
                    "groq_used": False,
                    "groq_reason": groq_reason,
                    "groq_value": None,
                    "groq_rationale": None,
                    "case_library_hit": False,
                    "local_judge_skip": True,
                    "final_score": final_score,
                    "grade": grade,
                }
                rows.append(row)
                if rec.get("content_sha256"):
                    self.registry.add(
                        str(rec["content_sha256"]),
                        agent=self.AGENT_NAME,
                        source_path=rec.get("source_path"),
                        clean_status=str(rec.get("clean_status") or "ok"),
                        extension=ext,
                        original_type=otype,
                    )
                if self.progress_every and (len(rows) % self.progress_every == 0):
                    processed = len(rows)
                    avg_so_far = round(
                        sum(r.get("final_score", 0) or 0 for r in rows) / max(1, processed),
                        3,
                    )
                    state = {
                        "wave": "wave_01",
                        "phase": "running",
                        "processed": processed,
                        "of": n,
                        "pool_size": pool_size,
                        "avg_so_far": avg_so_far,
                        "grades_so_far": dict(grade_counter),
                        "groq_calls": groq_calls,
                        "groq_success": groq_success,
                        "case_library_hits": case_library_hits,
                        "local_judge_skips": local_judge_skips,
                        "updated_at": _utc_iso(),
                    }
                    self._patch_status({**state, "status": "Running"})
                    if self.progress_callback is not None:
                        try:
                            self.progress_callback(state)
                        except Exception as e:  # noqa: BLE001
                            self.agent.log_event(
                                event="evaluator_progress_callback_failed",
                                error=repr(e),
                                processed=processed,
                            )
                continue
            elif ext in GROQ_WHITELIST_EXT and ambiguous:
                groq_calls += 1
                used_groq = True
                gv, rationale, groq_reason = _groq_value_call(rec)
                time.sleep(GROQ_DELAY_SEC)
                if gv is not None:
                    groq_success += 1
                    groq_value = gv

            final_score = round(0.6 * local_score + 0.4 * groq_value, 3) if groq_value is not None else local_score
            grade = _grade(final_score)
            grade_counter[grade] += 1
            type_counter[otype or "unknown"] += 1
            for t in tags:
                tag_counter[t] += 1

            row = {
                "stored_path": rec.get("stored_path") or fp,
                "source_path": rec.get("source_path"),
                "name": rec.get("name"),
                "extension": ext,
                "original_type": otype,
                "size_bytes": rec.get("size_bytes"),
                "content_sha256": rec.get("content_sha256"),
                "clean_status": rec.get("clean_status"),
                "local_score": local_score,
                "confidence": confidence,
                "tags": tags,
                "groq_used": used_groq,
                "groq_reason": groq_reason,
                "groq_value": groq_value,
                "groq_rationale": rationale,
                "case_library_hit": case_library_hit,
                "local_judge_skip": False,
                "final_score": final_score,
                "grade": grade,
            }
            rows.append(row)

            if rec.get("content_sha256"):
                self.registry.add(
                    str(rec["content_sha256"]),
                    agent=self.AGENT_NAME,
                    source_path=rec.get("source_path"),
                    clean_status=str(rec.get("clean_status") or "ok"),
                    extension=ext,
                    original_type=otype,
                )

            # ── 節流回報：每 progress_every 件觸發一次（含 Status 局部回寫 + Telegram） ──
            if self.progress_every and (len(rows) % self.progress_every == 0):
                processed = len(rows)
                avg_so_far = round(
                    sum(r.get("final_score", 0) or 0 for r in rows) / max(1, processed),
                    3,
                )
                state = {
                    "wave": "wave_01",
                    "phase": "running",
                    "processed": processed,
                    "of": n,
                    "pool_size": pool_size,
                    "avg_so_far": avg_so_far,
                    "grades_so_far": dict(grade_counter),
                    "groq_calls": groq_calls,
                    "groq_success": groq_success,
                    "case_library_hits": case_library_hits,
                    "local_judge_skips": local_judge_skips,
                    "updated_at": _utc_iso(),
                }
                self._patch_status({**state, "status": "Running"})
                if self.progress_callback is not None:
                    try:
                        self.progress_callback(state)
                    except Exception as e:  # noqa: BLE001
                        self.agent.log_event(
                            event="evaluator_progress_callback_failed",
                            error=repr(e),
                            processed=processed,
                        )

        rows_sorted = sorted(rows, key=lambda r: r.get("final_score", -1), reverse=True)
        avg_score = round(sum(r.get("final_score", 0) for r in rows) / max(1, len(rows)), 3)
        evaluate_duration_sec = round(time.monotonic() - t_eval0, 3)

        report = {
            "schema_version": "1.0",
            "run_id": self.agent.run_id,
            "generated_at": _utc_iso(),
            "pool_size": pool_size,
            "sampled": len(sampled),
            "avg_score": avg_score,
            "grades": dict(grade_counter),
            "by_type": dict(type_counter),
            "top_tags": dict(tag_counter.most_common(20)),
            "groq_calls": groq_calls,
            "groq_success": groq_success,
            "case_library_loaded": case_library_size,
            "case_library_hits": case_library_hits,
            "local_judge_skips": local_judge_skips,
            "evaluate_duration_sec": evaluate_duration_sec,
            "rows": rows_sorted,
        }
        report_path = os.path.join(
            self.reports_dir, f"asset_value_eval_{self.agent.run_id}.json"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        block = {
            "status": "Success",
            "run_id": self.agent.run_id,
            "pool_size": pool_size,
            "sampled": len(sampled),
            "avg_score": avg_score,
            "grades": dict(grade_counter),
            "groq_calls": groq_calls,
            "groq_success": groq_success,
            "case_library_loaded": case_library_size,
            "case_library_hits": case_library_hits,
            "local_judge_skips": local_judge_skips,
            "evaluate_duration_sec": evaluate_duration_sec,
            "report_path": report_path,
            "updated_at": _utc_iso(),
        }
        self._patch_status(block)

        top5 = [
            f"  {i+1}. [{r['grade']} {r['final_score']}] {r.get('name')} ({r.get('original_type')})"
            for i, r in enumerate(rows_sorted[:5])
        ]
        ammo_line, cost_line = format_groq_quota_telegram_suffix()
        body = (
            "[數據精煉] 首戰通報\n"
            f"Run_ID={self.agent.run_id}\n"
            f"取樣 {len(sampled)}/{pool_size}  平均分 {avg_score}\n"
            f"等級分布 {dict(grade_counter)}\n"
            f"Groq 呼叫 {groq_calls}（成功 {groq_success}） 案例庫命中 {case_library_hits} 本地預判閃避 {local_judge_skips}\n"
            f"{ammo_line}\n"
            f"{cost_line}\n"
            "Top5:\n" + "\n".join(top5)
        )
        _telegram_alert(body)

        self.agent.log_event(
            event="evaluator_done",
            pool_size=pool_size,
            sampled=len(sampled),
            avg_score=avg_score,
            grades=dict(grade_counter),
            groq_calls=groq_calls,
            groq_success=groq_success,
            report_path=report_path,
        )
        self.agent.set_status(AgentStatus.Success.value, reason="evaluator_complete")
        return {
            "run_id": self.agent.run_id,
            "pool_size": pool_size,
            "sampled": len(sampled),
            "avg_score": avg_score,
            "grades": dict(grade_counter),
            "groq_calls": groq_calls,
            "groq_success": groq_success,
            "case_library_loaded": case_library_size,
            "case_library_hits": case_library_hits,
            "local_judge_skips": local_judge_skips,
            "evaluate_duration_sec": evaluate_duration_sec,
            "report_path": report_path,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Asset_Value_Evaluator_Agent")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--progress-every", type=int, default=0)
    args = parser.parse_args()
    out = Asset_Value_Evaluator_Agent(
        sample_size=args.n,
        seed=args.seed,
        progress_every=args.progress_every,
    ).run()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
