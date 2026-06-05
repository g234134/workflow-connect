# Warning_Repair_Agent.py — 兵部·黃區深度修復（Warning-Only）
# 1) 將舊 hashes.txt 遷入 Chariot_Registry.db (SQLite)
# 2) 掃描 05_Temp_Cache/cleaned_full/*.json，僅處理 clean_status='warning'
# 3) 依病因分桶 Encoding / Structure / Unknown_Type
# 4) 重新解碼 / 解析；對 .py .php .json .jsonc .json5 .yml .yaml .toml 失敗時可呼叫 Groq
# 5) 失敗→C3_Logs；不熔斷；終戰報透過 Telegram 推播

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from Chariot_Registry import Chariot_Registry, default_db_path  # type: ignore
from Code_Cleaner_Agent import _detect_type, _summarize  # type: ignore
from Code_Cleaner_Throttled_Agent import (  # type: ignore
    GROQ_DELAY_SEC,
    _decode_full,
    _groq_json_repair,
    _groq_recover_decode_fail,
    _telegram_alert,
)
from GroqHybridRecovery_Agent import (  # type: ignore
    _try_json5,
    _try_kit_line_json,
    _try_parse_json_text,
)
from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore


GROQ_EXTS = {".py", ".php", ".json", ".jsonc", ".json5", ".yml", ".yaml", ".toml"}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def classify(warnings: List[Any], ext: str, original_type: str) -> str:
    """病因分桶：Encoding / Structure / Unknown_Type。"""
    txt = " | ".join(str(w) for w in (warnings or []))
    if "decode_failed" in txt or "groq_decode_recover_failed" in txt:
        return "Encoding"
    if (not original_type) or original_type == "unknown" or not ext:
        return "Unknown_Type"
    return "Structure"


def _local_json_repair(text: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(text), "json_std"
    except json.JSONDecodeError:
        pass
    obj, strat = _try_json5(text)
    if obj is not None:
        return obj, strat
    obj, strat = _try_parse_json_text(text)
    if obj is not None:
        return obj, strat
    obj, strat = _try_kit_line_json(text)
    if obj is not None:
        return obj, strat
    return None, None


def _try_yaml(text: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return None, "yaml_missing"
    try:
        return yaml.safe_load(text), "yaml_safe_load"
    except Exception as e:  # noqa: BLE001
        return None, f"yaml_error:{type(e).__name__}"


def _try_toml(text: str) -> Tuple[Optional[Any], Optional[str]]:
    mod = None
    try:
        import tomllib as mod  # type: ignore  # Py3.11+
    except ImportError:
        try:
            import tomli as mod  # type: ignore
        except ImportError:
            return None, "toml_missing"
    try:
        return mod.loads(text), "tomllib_loads"
    except Exception as e:  # noqa: BLE001
        return None, f"toml_error:{type(e).__name__}"


class Warning_Repair_Agent:
    AGENT_NAME = "Warning_Repair_Agent"
    DEPARTMENT = "兵部"

    def __init__(self, *, dest_root: Optional[str] = None) -> None:
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        self.workflows_dir = resolve_agent_output_path(self.dest_root, "04_Workflows")
        self.cleaned_full_dir = resolve_agent_output_path(self.dest_root, "05_Temp_Cache", "cleaned_full")
        self.c3_failed_dir = os.path.join(
            resolve_agent_output_path(self.dest_root, "03_RAG_Database", "c3_logs"),
            "Warning_Repair",
        )
        os.makedirs(self.c3_failed_dir, exist_ok=True)
        self.registry_path = default_db_path(self.dest_root)
        self.registry = Chariot_Registry(db_path=self.registry_path)
        self.legacy_hashes = os.path.join(self.workflows_dir, ".code_cleaner_throttle_hashes.txt")

    def _patch_status(self, block: Dict[str, Any]) -> None:
        sp = os.path.join(self.workflows_dir, "Status.json")
        data: Dict[str, Any] = {}
        if os.path.isfile(sp):
            try:
                with open(sp, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:  # noqa: BLE001
                data = {}
        data["warning_repair"] = block
        data["updated_at"] = _utc_iso()
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _migrate_hashes(self) -> Dict[str, Any]:
        result = self.registry.migrate_from_textfile(
            self.legacy_hashes, agent="Code_Cleaner_Throttled_Agent"
        )
        result["db_path"] = self.registry_path
        result["count_after"] = self.registry.count()
        result["status"] = "no_legacy_file" if result.get("file_missing") else "ok"
        self.agent.log_event(event="sqlite_migration_done", **result)
        return result

    def _enumerate_warnings(self) -> List[Tuple[str, Dict[str, Any]]]:
        items: List[Tuple[str, Dict[str, Any]]] = []
        if not os.path.isdir(self.cleaned_full_dir):
            return items
        for fn in os.listdir(self.cleaned_full_dir):
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(self.cleaned_full_dir, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    rec = json.load(f)
            except Exception:  # noqa: BLE001
                continue
            if str(rec.get("clean_status")) == "warning":
                items.append((fp, rec))
        return items

    def _log_failed_c3(
        self,
        *,
        repair_path: str,
        rec: Dict[str, Any],
        reason: str,
        category: str,
        groq_used: bool,
    ) -> None:
        row = {
            "ts": _utc_iso(),
            "run_id": self.agent.run_id,
            "agent": self.AGENT_NAME,
            "status": "failed",
            "category": category,
            "reason": reason,
            "groq_used": groq_used,
            "repair_record_path": repair_path,
            "source_path": rec.get("source_path"),
            "extension": rec.get("extension"),
            "original_type": rec.get("original_type"),
            "content_sha256": rec.get("content_sha256"),
            "size_bytes": rec.get("size_bytes"),
            "original_warnings": rec.get("warnings") or rec.get("original_warnings"),
        }
        path = os.path.join(self.c3_failed_dir, "failed_events.jsonl")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError as e:
            self.agent.log_event(event="c3_failed_log_write_error", path=path, error=str(e))

    def _attempt_repair(
        self,
        rec: Dict[str, Any],
        stats: Counter,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        src = str(rec.get("source_path") or "")
        ext = str(rec.get("extension") or "").lower()
        otype = str(rec.get("original_type") or "")
        name = str(rec.get("name") or os.path.basename(src) or "unknown")

        if not src or not os.path.isfile(src):
            return False, "source_missing", {"groq_used": False}

        try:
            with open(src, "rb") as f:
                raw = f.read()
        except OSError as e:
            return False, f"read_error:{type(e).__name__}", {"groq_used": False}

        groq_used = False
        text, enc = _decode_full(raw)
        if text is None:
            if ext in GROQ_EXTS:
                stats["groq_calls"] += 1
                lang = "python" if ext == ".py" else ("php" if ext == ".php" else "text")
                recovered, reason = _groq_recover_decode_fail(raw, name, lang)
                time.sleep(GROQ_DELAY_SEC)
                if recovered is None:
                    return False, f"encoding_unrecoverable:{reason}", {"groq_used": True}
                text = recovered
                enc = "groq_recovered_utf8"
                groq_used = True
            else:
                return False, "encoding_unrecoverable_no_cloud", {"groq_used": False}

        if ext in (".json", ".jsonc", ".json5"):
            obj, strat = _local_json_repair(text)
            if obj is None and ext in GROQ_EXTS:
                stats["groq_calls"] += 1
                obj2, gr = _groq_json_repair(text, name)
                time.sleep(GROQ_DELAY_SEC)
                if obj2 is None:
                    return False, f"json_unrecoverable:{gr}", {"groq_used": True}
                obj, strat = obj2, gr
                groq_used = True
            if obj is None:
                return False, "json_unrecoverable_no_cloud", {"groq_used": groq_used}
            summary = {"json_normalized": True, "strategy": strat, "via_groq": "groq" in (strat or "")}
            if isinstance(obj, dict):
                summary.update({"root_type": "dict", "items_count": len(obj), "top_keys": list(obj.keys())[:20]})
            elif isinstance(obj, list):
                summary.update({"root_type": "list", "items_count": len(obj)})
            return True, "ok", {
                "encoding": enc, "groq_used": groq_used, "parse_strategy": strat,
                "content_summary": summary, "parsed_json": obj,
            }

        if ext in (".yml", ".yaml"):
            obj, strat = _try_yaml(text)
            if obj is None and ext in GROQ_EXTS:
                stats["groq_calls"] += 1
                obj2, gr = _groq_json_repair(text, name)
                time.sleep(GROQ_DELAY_SEC)
                if obj2 is None:
                    return False, f"yaml_unrecoverable:{strat}|{gr}", {"groq_used": True}
                obj = obj2
                strat = f"groq_yaml_to_json:{gr}"
                groq_used = True
            if obj is None:
                return False, f"yaml_unrecoverable:{strat}", {"groq_used": groq_used}
            summary = {"yaml_normalized": True, "strategy": strat, "root_type": type(obj).__name__}
            return True, "ok", {
                "encoding": enc, "groq_used": groq_used, "parse_strategy": strat,
                "content_summary": summary, "parsed_json": obj,
            }

        if ext == ".toml":
            obj, strat = _try_toml(text)
            if obj is None and ext in GROQ_EXTS:
                stats["groq_calls"] += 1
                obj2, gr = _groq_json_repair(text, name)
                time.sleep(GROQ_DELAY_SEC)
                if obj2 is None:
                    return False, f"toml_unrecoverable:{strat}|{gr}", {"groq_used": True}
                obj = obj2
                strat = f"groq_toml_to_json:{gr}"
                groq_used = True
            if obj is None:
                return False, f"toml_unrecoverable:{strat}", {"groq_used": groq_used}
            summary = {"toml_normalized": True, "strategy": strat, "root_type": type(obj).__name__}
            return True, "ok", {
                "encoding": enc, "groq_used": groq_used, "parse_strategy": strat,
                "content_summary": summary, "parsed_json": obj,
            }

        try:
            summary = _summarize(otype or _detect_type(src), text)
        except Exception as e:  # noqa: BLE001
            return False, f"summary_failed:{type(e).__name__}", {"groq_used": groq_used}
        return True, "ok", {
            "encoding": enc, "groq_used": groq_used, "parse_strategy": "resummary",
            "content_summary": summary,
        }

    def run(self) -> Dict[str, Any]:
        self.agent.set_status(AgentStatus.Running.value, reason="warning_repair_start")
        migration = self._migrate_hashes()
        items = self._enumerate_warnings()
        scanned = len(items)

        cat_counter: Counter = Counter()
        for _, rec in items:
            cat_counter[
                classify(
                    rec.get("warnings") or [],
                    str(rec.get("extension") or "").lower(),
                    str(rec.get("original_type") or ""),
                )
            ] += 1

        stats: Counter = Counter()
        repaired = 0
        still_failed = 0
        per_cat_repair: Counter = Counter()
        per_cat_failed: Counter = Counter()
        failure_buckets: Counter = Counter()

        def _block(status: str) -> Dict[str, Any]:
            return {
                "status": status,
                "run_id": self.agent.run_id,
                "scanned": scanned,
                "by_category": dict(cat_counter),
                "repaired": repaired,
                "still_failed": still_failed,
                "repaired_by_category": dict(per_cat_repair),
                "failed_by_category": dict(per_cat_failed),
                "failure_buckets": dict(failure_buckets),
                "groq_calls": int(stats.get("groq_calls", 0)),
                "sqlite_migration": migration,
                "registry_count": self.registry.count(),
                "cleaned_full_dir": self.cleaned_full_dir,
                "c3_failed_dir": self.c3_failed_dir,
                "registry_db_path": self.registry_path,
                "updated_at": _utc_iso(),
            }

        self._patch_status(_block("Running"))

        for fp, rec in items:
            ext = str(rec.get("extension") or "").lower()
            otype = str(rec.get("original_type") or "")
            warns = rec.get("warnings") or []
            category = classify(warns, ext, otype)

            ok, reason, patch = self._attempt_repair(rec, stats)
            groq_used = bool(patch.get("groq_used"))

            if ok:
                repaired += 1
                per_cat_repair[category] += 1
                rec.setdefault("original_warnings", warns)
                rec["clean_status"] = "ok"
                rec["warnings"] = []
                if patch.get("encoding"):
                    rec["encoding"] = patch["encoding"]
                if patch.get("parse_strategy"):
                    rec["parse_strategy"] = patch["parse_strategy"]
                if patch.get("groq_used"):
                    rec["groq_used"] = True
                if patch.get("content_summary") is not None:
                    rec["content_summary"] = patch["content_summary"]
                if "parsed_json" in patch:
                    rec["parsed_json"] = patch["parsed_json"]
                rec["repair"] = {
                    "by": self.AGENT_NAME,
                    "run_id": self.agent.run_id,
                    "category": category,
                    "completed_at": _utc_iso(),
                    "result": "ok",
                    "groq_used": groq_used,
                }
                try:
                    with open(fp, "w", encoding="utf-8") as f:
                        json.dump(rec, f, ensure_ascii=False, indent=2)
                except OSError as e:
                    repaired -= 1
                    per_cat_repair[category] -= 1
                    still_failed += 1
                    per_cat_failed[category] += 1
                    failure_buckets["write_error"] += 1
                    self._log_failed_c3(
                        repair_path=fp, rec=rec,
                        reason=f"write_error:{type(e).__name__}",
                        category=category, groq_used=groq_used,
                    )
                else:
                    if rec.get("content_sha256"):
                        self.registry.add(
                            str(rec["content_sha256"]),
                            agent=self.AGENT_NAME,
                            source_path=rec.get("source_path"),
                            clean_status="ok",
                            extension=ext,
                            original_type=otype,
                        )
            else:
                still_failed += 1
                per_cat_failed[category] += 1
                bucket = reason.split(":", 1)[0]
                failure_buckets[bucket] += 1
                rec.setdefault("original_warnings", warns)
                rec["clean_status"] = "failed"
                rec["repair"] = {
                    "by": self.AGENT_NAME,
                    "run_id": self.agent.run_id,
                    "category": category,
                    "completed_at": _utc_iso(),
                    "result": "failed",
                    "reason": reason,
                    "groq_used": groq_used,
                }
                try:
                    with open(fp, "w", encoding="utf-8") as f:
                        json.dump(rec, f, ensure_ascii=False, indent=2)
                except OSError:
                    pass
                self._log_failed_c3(
                    repair_path=fp, rec=rec,
                    reason=reason, category=category, groq_used=groq_used,
                )
                if rec.get("content_sha256"):
                    self.registry.add(
                        str(rec["content_sha256"]),
                        agent=self.AGENT_NAME,
                        source_path=rec.get("source_path"),
                        clean_status="failed",
                        extension=ext,
                        original_type=otype,
                    )

            if (repaired + still_failed) % 100 == 0:
                self._patch_status(_block("Running"))

        self._patch_status(_block("Success"))

        analysis = "\n".join(f"· {k}: {n}" for k, n in failure_buckets.most_common()) or "（無失敗 bucket）"
        body = (
            f"[黃區深度修復] 終戰報\n"
            f"Run_ID={self.agent.run_id}\n"
            f"掃描 warning={scanned}\n"
            f"分類: Encoding={cat_counter.get('Encoding', 0)} "
            f"Structure={cat_counter.get('Structure', 0)} "
            f"Unknown_Type={cat_counter.get('Unknown_Type', 0)}\n"
            f"修復成功={repaired}（依類別 {dict(per_cat_repair) or {}}）\n"
            f"最終失敗={still_failed}（依類別 {dict(per_cat_failed) or {}}）\n"
            f"Groq 呼叫={int(stats.get('groq_calls', 0))}\n"
            f"SQLite 遷移：狀態={migration.get('status')} 新增={migration.get('rows_inserted')} "
            f"已掃={migration.get('rows_seen')} 總筆數={self.registry.count()} "
            f"DB={os.path.basename(self.registry_path)}\n"
            f"--- 失敗主因 ---\n{analysis}"
        )
        _telegram_alert(body)

        self.agent.log_event(
            event="warning_repair_done",
            scanned=scanned,
            repaired=repaired,
            still_failed=still_failed,
            groq_calls=int(stats.get("groq_calls", 0)),
            registry_count=self.registry.count(),
        )
        self.agent.set_status(AgentStatus.Success.value, reason="warning_repair_complete")
        return {
            "run_id": self.agent.run_id,
            "scanned": scanned,
            "by_category": dict(cat_counter),
            "repaired": repaired,
            "still_failed": still_failed,
            "repaired_by_category": dict(per_cat_repair),
            "failed_by_category": dict(per_cat_failed),
            "failure_buckets": dict(failure_buckets),
            "groq_calls": int(stats.get("groq_calls", 0)),
            "sqlite_migration": migration,
            "registry_count": self.registry.count(),
            "registry_db_path": self.registry_path,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Warning_Repair_Agent")
    args = parser.parse_args()
    get_tang_gov_root()
    out = Warning_Repair_Agent().run()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
