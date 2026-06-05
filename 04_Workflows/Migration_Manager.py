"""
Migration_Manager.py (draft / logic check)

Purpose:
  - Shadow migration (Copy Only) into the Six-Ministry layout.
  - Semantic routing:
      * .csv/.json with filename containing "dirty" or "raw"  -> 05_Temp_Cache
      * .py -> 02_Agents_Core
      * GitHub project "whole package" (repo directory) -> 03_* (configurable subdir)
  - Forced naming rule for moved files:
      [project]_[solution]_[version]_[date]_[original_filename]
  - Full monitoring:
      * Uses Base_Agent (Run_ID, status control, JSON logging, Status.json update)
  - Error handling + stop:
      * try/except with retries
      * if error events > 2 => status becomes Manual and stop
  - Snapshots:
      * creates RAG 部門下 Master_Map.sub_directories.snapshots 目錄並記錄先前 stable 路徑

Important clarification (needs your confirmation):
  For a "whole repo directory" we copy the directory as a unit and rename only
  the *repo root folder* using the forced naming format. We do NOT rename every
  file inside the repo (renaming all files can break internal references).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def ensure_parent_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def unique_file_path(dest_path: Path) -> Path:
    """If dest_path exists, append __dup001, __dup002, ... before extension (never overwrite)."""
    if not dest_path.exists():
        return dest_path
    parent = dest_path.parent
    stem = dest_path.stem
    suffix = dest_path.suffix
    n = 1
    while True:
        candidate = parent / f"{stem}__dup{n:03d}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def unique_dir_path(dest_dir: Path) -> Path:
    """If directory exists, append __dup001, ... (never overwrite tree)."""
    if not dest_dir.exists():
        return dest_dir
    n = 1
    while True:
        candidate = Path(str(dest_dir) + f"__dup{n:03d}")
        if not candidate.exists():
            return candidate
        n += 1


def forced_name(
    project_name: str,
    solution: str,
    version: str,
    date_yyyymmdd: str,
    original_filename: str,
) -> str:
    # Naming rule:
    #   [project]_[solution]_[version]_[date]_[original_filename]
    return f"{project_name}_{solution}_{version}_{date_yyyymmdd}_{original_filename}"


def guess_date_yyyymmdd() -> str:
    return datetime.now().strftime("%Y%m%d")


def normalize_path(p: str) -> str:
    return str(Path(p))


def load_items(input_list_path: Path) -> List[Dict[str, Any]]:
    """
    Supported formats:
      - JSON:
          * either an array
          * or an object with "items": [...]
        Each item can be:
          * string path
          * or object: {"path": "...", "kind": "repo|file"} (kind optional)

      - CSV:
          * header must include one of: path/src/source/file
          * other columns are ignored
    """
    if not input_list_path.exists():
        raise FileNotFoundError(f"input list not found: {input_list_path}")

    suffix = input_list_path.suffix.lower()
    if suffix == ".json":
        data = json.loads(input_list_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
        else:
            items = data
        if not isinstance(items, list):
            raise ValueError("JSON input must be an array or object with 'items' array.")

        out: List[Dict[str, Any]] = []
        for it in items:
            if isinstance(it, str):
                out.append({"path": it})
            elif isinstance(it, dict):
                out.append(
                    {
                        "path": it.get("path") or it.get("src_path") or it.get("src") or it.get("source"),
                        "kind": it.get("kind"),
                    }
                )
            else:
                raise ValueError("Each JSON item must be a string or object.")
        return out

    if suffix == ".csv":
        with input_list_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("CSV must have a header row.")
            fieldnames = [n.lower() for n in reader.fieldnames]
            col = None
            for candidate in ["path", "src", "source", "file"]:
                if candidate in fieldnames:
                    col = reader.fieldnames[fieldnames.index(candidate)]
                    break
            if not col:
                raise ValueError("CSV header must include one of: path/src/source/file")

            out: List[Dict[str, Any]] = []
            for row in reader:
                if not row.get(col):
                    continue
                out.append({"path": row[col], "kind": row.get("kind")})
            return out

    raise ValueError(f"Unsupported input list extension: {suffix}")


@dataclass(frozen=True)
class TargetRule:
    """路由規則：department / sub_type 為 Master_Map 的邏輯鍵；實體路徑僅能經 Base_Agent.get_path 解析。"""
    department: str
    sub_type: Optional[str] = None
    preserve_structure_for_dir: bool = False  # used only for repo directories


class MigrationManager:
    def __init__(
        self,
        *,
        dest_root: str,
        project_name: str,
        solution: str,
        version: str,
        date_yyyymmdd: str,
        github_target_subdir: str,
        source_base: Optional[str],
        execute: bool,
    ) -> None:
        dest_root_abs = os.path.abspath(dest_root)
        mp = os.path.join(dest_root_abs, "04_Workflows", "Master_Map.json")
        if not os.path.isfile(mp):
            raise FileNotFoundError(f"Master_Map.json not found: {mp}")
        with open(mp, "r", encoding="utf-8") as f:
            self._master_map: Dict[str, Any] = json.load(f)

        dept_map = self._master_map.get("departments") or {}
        agents_rel = str(dept_map.get("02_Agents_Core", "02_Agents_Core")).replace("/", os.sep)
        base_agent_dir = os.path.normpath(os.path.join(dest_root_abs, agents_rel))
        sys.path.insert(0, base_agent_dir)
        from Base_Agent import Base_Agent, AgentStatus  # type: ignore

        self.Base_Agent = Base_Agent
        self.AgentStatus = AgentStatus

        self.dest_root = dest_root_abs
        self.project_name = project_name
        self.solution = solution
        self.version = version
        self.date_yyyymmdd = date_yyyymmdd
        self.github_target_subdir = github_target_subdir
        self.source_base = source_base
        self.execute = execute

        self.agent = Base_Agent(dest_root=self.dest_root, department="流程部", agent_name="Migration_Manager")
        self.failure_events = 0
        self.any_failure = False
        self.copied_dest_paths: List[Path] = []

        d = self._master_map.get("departments") or {}
        self._ministry_order_segments = [str(d[k]).replace("/", os.sep) for k in sorted(d.keys())]

        self._snapshots_dir = Path(Base_Agent.get_path("03_RAG_Database", "snapshots", dest_root=self.dest_root))
        os.makedirs(self._snapshots_dir, exist_ok=True)
        # DryRun 預覽不會改變目標內容，因此不需要寫入回滾快照。
        if self.execute:
            self._snapshot_previous_stable()

    def _snapshot_previous_stable(self) -> None:
        latest_file = self._snapshots_dir / "latest_stable.json"
        previous: Dict[str, Any] = {}
        if latest_file.exists():
            try:
                previous = json.loads(latest_file.read_text(encoding="utf-8"))
            except Exception:
                previous = {}
        snapshot = {
            "run_id": self.agent.run_id,
            "created_at": utc_now_iso(),
            "previous_latest_stable": previous,
            "intended_dest_root": self.dest_root,
        }
        out = self._snapshots_dir / f"pre_{self.agent.run_id}.json"
        out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        self.agent.log_event(event="snapshot_pre_created", snapshot_path=str(out))

    def _update_latest_stable(self) -> None:
        latest_file = self._snapshots_dir / "latest_stable.json"
        payload = {"run_id": self.agent.run_id, "updated_at": utc_now_iso(), "stable_dest_root": self.dest_root}
        latest_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.agent.log_event(event="snapshot_latest_updated", snapshot_path=str(latest_file))

    def _resolve_src_path(self, raw_path: str) -> Path:
        p = Path(raw_path)
        if self.source_base and not p.is_absolute():
            p = Path(self.source_base) / p
        return p

    def _is_repo_dir(self, src_path: Path) -> bool:
        # Heuristic for "GitHub project整包"
        if src_path.is_dir():
            if (src_path / ".git").exists():
                return True
            # Common indicators
            if (src_path / "README.md").exists() and (
                (src_path / "pyproject.toml").exists() or (src_path / "requirements.txt").exists()
            ):
                return True
        return False

    def _route_file(self, src_path: Path) -> Optional[TargetRule]:
        name_lower = src_path.name.lower()
        suffix = src_path.suffix.lower()

        # 02_兵部: .py (CODE PRIORITY)
        # Rule: any .py must go to 02_Agents_Core even if filename contains raw/dirty.
        if suffix == ".py":
            return TargetRule(department="02_Agents_Core")

        # 05_刑部: filename 含 dirty/raw 或副檔名為 .csv/.json
        # sub_type 對應 Master_Map.sub_directories["05_Temp_Cache"]
        if ("dirty" in name_lower or "raw" in name_lower or suffix in {".csv", ".json"}):
            if "raw" in name_lower:
                return TargetRule(department="05_Temp_Cache", sub_type="raw_inbound")
            return TargetRule(department="05_Temp_Cache", sub_type="quarantine")

        # Not matched => skip (no default routing specified)
        return None

    def _route_repo(self, src_dir: Path) -> Path:
        # Whole-repo packages：目標為 Master_Map.sub_directories["02_Agents_Core"]["repos"]
        base = Path(self.Base_Agent.get_path("02_Agents_Core", "repos", dest_root=self.dest_root))
        base.mkdir(parents=True, exist_ok=True)

        new_root_name = forced_name(
            project_name=self.project_name,
            solution=self.solution,
            version=self.version,
            date_yyyymmdd=self.date_yyyymmdd,
            original_filename=src_dir.name,
        )
        return base / new_root_name

    def _copy_file(self, src_path: Path, dest_dir: Path, overwrite: bool = False) -> Path:
        original_filename = src_path.name
        dest_filename = forced_name(
            project_name=self.project_name,
            solution=self.solution,
            version=self.version,
            date_yyyymmdd=self.date_yyyymmdd,
            original_filename=original_filename,
        )
        dest_path = dest_dir / dest_filename
        ensure_parent_dir(dest_path)

        if dest_path.exists() and not overwrite:
            dest_path = unique_file_path(dest_path)
            ensure_parent_dir(dest_path)
            self.agent.log_event(
                event="copy_renamed_avoid_collision",
                status=self.agent.status,
                source=str(src_path),
                dest=str(dest_path),
            )

        if self.execute:
            shutil.copy2(str(src_path), str(dest_path))
        self.agent.log_event(
            event="copy_file",
            status="Success" if self.execute else "DryRun",
            source=str(src_path),
            dest=str(dest_path),
        )
        self.copied_dest_paths.append(dest_path)
        return dest_path

    def _copy_repo_dir(self, src_dir: Path, dest_dir: Path, overwrite: bool = False) -> Path:
        if dest_dir.exists() and not overwrite:
            dest_dir = unique_dir_path(dest_dir)
            self.agent.log_event(
                event="repo_copy_renamed_avoid_collision",
                status=self.agent.status,
                source=str(src_dir),
                dest=str(dest_dir),
            )

        if self.execute:
            # Exclude .git by default to avoid huge copies; change if you need full VCS snapshot.
            ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
            shutil.copytree(str(src_dir), str(dest_dir), dirs_exist_ok=False, ignore=ignore)
        self.agent.log_event(
            event="copy_repo_dir",
            status="Success" if self.execute else "DryRun",
            source=str(src_dir),
            dest=str(dest_dir),
        )
        self.copied_dest_paths.append(dest_dir)
        return dest_dir

    def _dest_dir_for_rule(self, rule: TargetRule) -> Path:
        return Path(
            self.Base_Agent.get_path(rule.department, rule.sub_type, dest_root=self.dest_root)
        )

    def _workflows_dir(self) -> Path:
        return Path(self.Base_Agent.get_path("04_Workflows", None, dest_root=self.dest_root))

    def _find_repo_dirs(self, source_root: Path) -> List[Path]:
        """
        Identify GitHub repo directories heuristically:
          - contains ".git" OR
          - contains "README.md" + ("pyproject.toml" or "requirements.txt")

        When a repo is detected, we prune its children to avoid double-processing nested paths.
        """
        repo_dirs: List[Path] = []
        for dirpath, dirnames, _filenames in os.walk(source_root):
            # Prune obvious venv/build dirs to speed up and avoid noise
            dirnames[:] = [d for d in dirnames if d not in {"venv", ".venv", "__pycache__", "node_modules"}]
            current = Path(dirpath)
            if self._is_repo_dir(current):
                repo_dirs.append(current)
                dirnames[:] = []  # do not descend into this repo
        # Stable ordering for deterministic preview
        repo_dirs = sorted(set(repo_dirs), key=lambda p: str(p))
        return repo_dirs

    def _file_is_inside_any_repo(self, p: Path, repo_dirs: List[Path]) -> bool:
        for r in repo_dirs:
            try:
                p.relative_to(r)
                return True
            except ValueError:
                continue
        return False

    def _plan_from_source_root(self, source_root: Path) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Returns:
          - actions: list of dicts
          - stats: counts by route type
        Actions:
          - { "kind": "repo", "src_dir": Path, "dest_dir": Path }
          - { "kind": "file", "src_path": Path, "rule": TargetRule }
        """
        repo_dirs = self._find_repo_dirs(source_root)

        actions: List[Dict[str, Any]] = []
        stats = {
            "repo_dirs": len(repo_dirs),
            "py_files": 0,
            "dirty_raw_or_csvjson_files": 0,
            "unmatched_files_skipped": 0,
        }

        # Repo actions (copy repo as unit; rename only repo root folder)
        for rd in repo_dirs:
            dest_dir = self._route_repo(rd)
            actions.append({"kind": "repo", "src_dir": rd, "dest_dir": dest_dir})

        # File actions (exclude anything inside repo dirs)
        # IMPORTANT: do NOT pre-collect + sort all files; it can be huge and stall execution.
        scanned_files = 0
        for dirpath, dirnames, filenames in os.walk(source_root):
            # Prune obvious venv/build dirs to speed up and avoid noise
            dirnames[:] = [d for d in dirnames if d not in {"venv", ".venv", "__pycache__", "node_modules"}]
            for fn in filenames:
                scanned_files += 1
                if scanned_files % 200000 == 0:
                    print(f"Scanning: {scanned_files} files visited...", flush=True)

                fp = Path(dirpath) / fn
                if self._file_is_inside_any_repo(fp, repo_dirs):
                    continue
                rule = self._route_file(fp)
                if rule is None:
                    stats["unmatched_files_skipped"] += 1
                    continue

                if fp.suffix.lower() == ".py":
                    stats["py_files"] += 1
                else:
                    stats["dirty_raw_or_csvjson_files"] += 1

                actions.append({"kind": "file", "src_path": fp, "rule": rule})

        return actions, stats

    def run_scan(self, source_root: Path, *, overwrite: bool = False, max_retries: int = 2) -> None:
        """
        Scan entire source_root and perform Copy-Only shadow migration.
        Default is DryRun preview; enable real copies by running with --execute.
        """
        self.agent.set_status(self.AgentStatus.Running.value, reason="migration_scan_start")

        source_root = (Path(source_root).resolve())
        actions, stats = self._plan_from_source_root(source_root)

        # Preview plan output
        plan_out = self._workflows_dir() / f"migration_plan_{self.agent.run_id}.json"
        plan_payload = {
            "run_id": self.agent.run_id,
            "generated_at": utc_now_iso(),
            "dest_root": self.dest_root,
            "source_root": str(source_root),
            "execute": self.execute,
            "forced_naming": {
                "project_name": self.project_name,
                "solution": self.solution,
                "version": self.version,
                "date_yyyymmdd": self.date_yyyymmdd,
            },
            "stats": stats,
            "actions_preview": [],
        }
        def ministry_index(dest: str) -> int:
            d = os.path.normpath(dest)
            for i, seg in enumerate(self._ministry_order_segments):
                needle = os.sep + seg + os.sep
                if needle in d or d.endswith(os.sep + seg) or os.path.basename(d) == seg:
                    return i
            for i, seg in enumerate(self._ministry_order_segments):
                if seg in d:
                    return i
            return 99

        # IMPORTANT:
        # - In --execute mode, do NOT write a full actions list (it can be enormous and stall before copying starts).
        # - We only keep a small preview (N items) for traceability.
        preview_actions: List[Dict[str, Any]] = []
        for a in actions:
            if a["kind"] == "repo":
                dest_dir_str = str(a["dest_dir"])
                preview_actions.append(
                    {"kind": "repo", "src_dir": str(a["src_dir"]), "dest_dir": dest_dir_str, "_order": ministry_index(dest_dir_str)}
                )
            else:
                sp: Path = a["src_path"]
                rule: TargetRule = a["rule"]
                dest_dir = self._dest_dir_for_rule(rule)
                dest_filename = forced_name(
                    project_name=self.project_name,
                    solution=self.solution,
                    version=self.version,
                    date_yyyymmdd=self.date_yyyymmdd,
                    original_filename=sp.name,
                )
                dest_path_str = str(dest_dir / dest_filename)
                preview_actions.append(
                    {
                        "kind": "file",
                        "src_path": str(sp),
                        "rule": {"department": rule.department, "sub_type": rule.sub_type},
                        "dest_path": dest_path_str,
                        "_order": ministry_index(dest_path_str),
                    }
                )

        preview_actions_sorted = sorted(preview_actions, key=lambda x: x["_order"])
        N = 30
        plan_payload["actions_preview"] = [
            {k: v for k, v in item.items() if k != "_order"} for item in preview_actions_sorted[:N]
        ]
        plan_payload["preview_total_actions"] = len(preview_actions_sorted)

        plan_out.parent.mkdir(parents=True, exist_ok=True)
        plan_out.write_text(json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        # Human-readable preview to console
        print("\n=== Migration Plan Preview ===")
        print(f"Run_ID: {self.agent.run_id}")
        print(f"SourceRoot: {source_root}")
        print(f"Execute: {self.execute}")
        print(f"Stats: {stats}")
        print(f"Plan file: {plan_out}")

        # Show preview N (already sorted by 01..06)
        preview_actions = plan_payload["actions_preview"]
        for item in preview_actions:
            if item["kind"] == "repo":
                print(f"[REPO] {item['src_dir']}  ->  {item['dest_dir']}")
            else:
                print(f"[FILE] {item['src_path']}  ->  {item['dest_path']}")
        if plan_payload.get("preview_total_actions", 0) > N:
            print(f"... (and {plan_payload['preview_total_actions'] - N} more)")

        if not self.execute:
            self.agent.set_status(self.AgentStatus.Success.value, reason="dry_run_preview_generated")
            return

        # Execute copies (with retries)
        self.failure_events = 0
        self.any_failure = False
        error_events = 0
        total_actions = len(actions)

        tc_bucket = (self._master_map.get("sub_directories") or {}).get("05_Temp_Cache") or {}
        tc_sub_keys = list(tc_bucket.keys()) if tc_bucket else ["raw_inbound", "quarantine"]
        moved_counts: Dict[str, int] = {"02_Agents_Core_files": 0, "02_Agents_Core_repos": 0}
        for st in tc_sub_keys:
            moved_counts[f"05_Temp_Cache:{st}_files"] = 0

        for idx, action in enumerate(actions):
            attempt = 0
            while attempt <= max_retries:
                attempt += 1
                try:
                    if action["kind"] == "repo":
                        self._copy_repo_dir(
                            src_dir=action["src_dir"], dest_dir=action["dest_dir"], overwrite=overwrite
                        )
                        moved_counts["02_Agents_Core_repos"] += 1
                    else:
                        sp: Path = action["src_path"]
                        rule: TargetRule = action["rule"]
                        dest_dir = self._dest_dir_for_rule(rule)
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        self._copy_file(src_path=sp, dest_dir=dest_dir, overwrite=overwrite)
                        if rule.department == "02_Agents_Core":
                            moved_counts["02_Agents_Core_files"] += 1
                        elif rule.department == "05_Temp_Cache":
                            sk = rule.sub_type or "unknown"
                            ck = f"05_Temp_Cache:{sk}_files"
                            moved_counts[ck] = moved_counts.get(ck, 0) + 1

                    # Progress output
                    done = idx + 1
                    if done % 1000 == 0 or done == total_actions:
                        print(f"Progress: {done}/{total_actions} actions completed", flush=True)
                    break

                except Exception as e:
                    error_events += 1
                    last_exc = str(e)
                    self.agent.log_event(
                        event="copy_failed",
                        attempt=attempt,
                        status="Failed",
                        source=str(action.get("src_dir") or action.get("src_path") or ""),
                        dest=str(action.get("dest_dir") or ""),
                        error=last_exc,
                    )

                    if error_events > 2:
                        self.agent.set_status(self.AgentStatus.Manual.value, reason="too_many_errors")
                        self.agent.log_event(
                            event="stop_due_to_failures",
                            error_events=error_events,
                            failed_item_index=idx,
                        )
                        return

                    if attempt > max_retries:
                        self.failure_events += 1
                        self.any_failure = True
                        break

                    time.sleep(0.2)

        # Final report (execute only): versioned file + latest pointer
        wf = self._workflows_dir()
        safe_sol = "".join(c if c.isalnum() or c in "._-" else "_" for c in self.solution)
        versioned_name = f"Final_Migration_Report_{safe_sol}_{self.version}_{self.agent.run_id}.json"
        report_path_versioned = wf / versioned_name
        report_path_latest = wf / "Final_Migration_Report.json"
        report = {
            "run_id": self.agent.run_id,
            "project_name": self.project_name,
            "solution": self.solution,
            "version": self.version,
            "source_root": str(source_root),
            "dest_root": self.dest_root,
            "executed": True,
            "generated_at": utc_now_iso(),
            "counts": moved_counts,
            "errors": {"error_events": error_events, "failure_events": self.failure_events},
            "incremental_note": "Duplicate destinations get __dupNNN suffix; wave uses solution+version in forced name.",
        }
        body = json.dumps(report, ensure_ascii=False, indent=2)
        report_path_versioned.write_text(body, encoding="utf-8")
        report_path_latest.write_text(body, encoding="utf-8")
        self.agent.log_event(
            event="final_report_written",
            report_path=str(report_path_latest),
            report_path_versioned=str(report_path_versioned),
        )

        if self.any_failure:
            self.agent.set_status(self.AgentStatus.Failed.value, reason="completed_with_failures")
        else:
            self.agent.set_status(self.AgentStatus.Success.value, reason="completed_successfully")
            self._update_latest_stable()
            try:
                sp = Path(self.agent._status_path)
                st = json.loads(sp.read_text(encoding="utf-8"))
                st["migration_last_wave"] = {
                    "status": "Success",
                    "run_id": self.agent.run_id,
                    "project_name": self.project_name,
                    "solution": self.solution,
                    "version": self.version,
                    "source_root": str(source_root),
                    "updated_at": utc_now_iso(),
                }
                sp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                self.agent.log_event(event="status_json_merge_failed", error=str(e))

        self.agent.log_event(event="migration_finished", any_failure=self.any_failure)

    def run(self, input_list_path: Path, *, overwrite: bool = False, max_retries: int = 2) -> None:
        """
        max_retries:
          - total attempts = 1 + max_retries
          - stop when error events > 2
        """
        self.agent.set_status(self.AgentStatus.Running.value, reason="migration_start")

        items = load_items(input_list_path)
        self.agent.log_event(event="migration_input_loaded", item_count=len(items))

        for idx, item in enumerate(items):
            raw_src = item.get("path")
            if not raw_src:
                continue

            kind = item.get("kind")  # optional hint
            src_path = self._resolve_src_path(str(raw_src))

            attempt = 0
            last_exc: Optional[str] = None
            while attempt <= max_retries:
                attempt += 1
                try:
                    # Repo directory route (if kind hints or heuristic)
                    if kind == "repo" or (kind is None and src_path.is_dir() and self._is_repo_dir(src_path)):
                        dest_repo_root = self._route_repo(src_path)
                        self.agent.log_event(
                            event="route_repo",
                            attempt=attempt,
                            source=str(src_path),
                            dest=str(dest_repo_root),
                        )
                        self._copy_repo_dir(src_dir=src_path, dest_dir=dest_repo_root, overwrite=overwrite)
                        last_exc = None
                        break

                    # File route
                    if not src_path.is_file():
                        self.agent.log_event(
                            event="skip_not_file_or_repo",
                            attempt=attempt,
                            source=str(src_path),
                        )
                        last_exc = None
                        break

                    rule = self._route_file(src_path)
                    if rule is None:
                        self.agent.log_event(
                            event="skipped_unmatched",
                            attempt=attempt,
                            source=str(src_path),
                        )
                        last_exc = None
                        break

                    dest_dir = self._dest_dir_for_rule(rule)
                    dest_dir.mkdir(parents=True, exist_ok=True)

                    self.agent.log_event(
                        event="route_file",
                        attempt=attempt,
                        source=str(src_path),
                        dest=str(dest_dir),
                    )
                    self._copy_file(src_path=src_path, dest_dir=dest_dir, overwrite=overwrite)
                    last_exc = None
                    break

                except Exception as e:
                    last_exc = str(e)
                    self.agent.log_event(
                        event="copy_failed",
                        attempt=attempt,
                        status="Failed",
                        source=str(src_path),
                        error=last_exc,
                    )
                    if attempt > max_retries:
                        self.failure_events += 1
                        self.any_failure = True

                        #  Stop rule:
                        if self.failure_events > 2:
                            self.agent.set_status(self.AgentStatus.Manual.value, reason="too_many_errors")
                            self.agent.log_event(
                                event="stop_due_to_failures",
                                failure_events=self.failure_events,
                                failed_item_index=idx,
                            )
                            return
                        # else: continue next item
                    else:
                        time.sleep(0.2)

            if last_exc is not None and attempt > max_retries:
                # The item ultimately failed, already counted.
                continue

        # Final status
        if self.any_failure:
            self.agent.set_status(self.AgentStatus.Failed.value, reason="completed_with_failures")
        else:
            self.agent.set_status(self.AgentStatus.Success.value, reason="completed_successfully")
            self._update_latest_stable()

        self.agent.log_event(event="migration_finished", any_failure=self.any_failure)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Shadow migration manager (Copy Only, monitored).")
    p.add_argument(
        "--dest-root",
        default="",
        help="六部根目錄；留空則由 Master_Map.json / 環境變數推導（見 gov_paths）。",
    )
    p.add_argument("--source-root", default=None, help="Legacy project root to scan recursively.")
    p.add_argument("--input-list", default=None, help="Optional JSON/CSV file listing old paths.")
    p.add_argument("--project-name", required=True, help="Project name for forced naming.")
    p.add_argument("--solution", required=True, help="方案/strategy name for forced naming.")
    p.add_argument("--version", required=True, help="Version for forced naming.")
    p.add_argument("--date-yyyymmdd", default=guess_date_yyyymmdd(), help="YYYYMMDD for forced naming.")
    p.add_argument(
        "--github-target-subdir",
        default="(unused now; kept for backwards compat)",
        help="Deprecated: repo packages are routed into 02_Agents_Core\\repos in the 01-06 layout.",
    )
    p.add_argument("--source-base", default=None, help="Base dir to resolve relative paths in input-list.")
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite destination files/folders (default: skip existing).",
    )
    p.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform copy. Without --execute, runs in DryRun mode (logic check).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    dest_root = (args.dest_root or "").strip()
    if not dest_root:
        here = os.path.dirname(os.path.abspath(__file__))
        mp_local = os.path.join(here, "Master_Map.json")
        if os.path.isfile(mp_local):
            with open(mp_local, "r", encoding="utf-8") as f:
                _boot = json.load(f)
            _d = _boot.get("departments") or {}
            _agents_rel = str(_d.get("02_Agents_Core", "02_Agents_Core")).replace("/", os.sep)
            agents_core = os.path.normpath(os.path.join(here, "..", _agents_rel))
        else:
            agents_core = os.path.normpath(os.path.join(here, "..", "02_Agents_Core"))
        if agents_core not in sys.path:
            sys.path.insert(0, agents_core)
        from gov_paths import get_tang_gov_root

        dest_root = get_tang_gov_root()

    mgr = MigrationManager(
        dest_root=dest_root,
        project_name=args.project_name,
        solution=args.solution,
        version=args.version,
        date_yyyymmdd=args.date_yyyymmdd,
        github_target_subdir=args.github_target_subdir,
        source_base=args.source_base,
        execute=bool(args.execute),
    )

    if args.source_root:
        mgr.run_scan(Path(args.source_root), overwrite=bool(args.overwrite), max_retries=2)
    elif args.input_list:
        mgr.run(Path(args.input_list), overwrite=bool(args.overwrite), max_retries=2)
    else:
        raise SystemExit("Provide either --source-root (recommended) or --input-list.")


if __name__ == "__main__":
    main()

