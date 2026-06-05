"""_register_fingerprints.py — SHA256 指紋補登。

模式：
  · 預設（無 --dir / --files）：掃描治理集（04_Workflows / 02_Agents_Core / config / 根 docs）。
  · --dir <path>：遞迴掃描指定目錄下所有檔案，標籤=raw_inbound（或 --label）。
  · --files a b c：只登錄列出的檔案（常搭配 --clean-status pending 供刑部哨兵呼叫）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Tuple

from _tang_paths import bootstrap_sys_path, sha256_file  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from Chariot_Registry import Chariot_Registry  # type: ignore


def _gather_governance() -> List[Tuple[str, str]]:
    targets: List[Tuple[str, str]] = []

    workflows = os.path.join(_root, "04_Workflows")
    for fn in sorted(os.listdir(workflows)):
        ext = os.path.splitext(fn)[1].lower()
        if ext in {".ps1", ".py"}:
            targets.append((os.path.join(workflows, fn), "workflow_script"))

    agents_core = os.path.join(_root, "02_Agents_Core")
    for fn in sorted(os.listdir(agents_core)):
        full = os.path.join(agents_core, fn)
        if os.path.isfile(full) and fn.lower().endswith(".py"):
            targets.append((full, "agent_core"))

    cfg_dir = os.path.join(_root, "01_Environments", "config")
    if os.path.isdir(cfg_dir):
        for fn in sorted(os.listdir(cfg_dir)):
            ext = os.path.splitext(fn)[1].lower()
            if ext in {".yaml", ".yml"}:
                targets.append((os.path.join(cfg_dir, fn), "config_yaml"))

    extras = [
        os.path.join(_root, ".gitignore"),
        os.path.join(_root, "README_Refresher.md"),
        os.path.join(_root, "AGENTS.md"),
        os.path.join(_root, "01_Environments", ".gitignore"),
        os.path.join(_root, "01_Environments", "requirements.main.txt"),
        os.path.join(_root, "01_Environments", "requirements.agency.txt"),
        os.path.join(_root, "01_Environments", "requirements.main.lock.txt"),
        os.path.join(_root, "01_Environments", "requirements.agency.lock.txt"),
    ]
    for p in extras:
        if os.path.isfile(p):
            targets.append((p, "governance_doc"))
    return targets


def _gather_directory(root_dir: str, label: str) -> List[Tuple[str, str]]:
    """遞迴蒐集 root_dir 底下的常規檔案（跳過 venv / __pycache__）。"""
    skip = {"__pycache__", ".git", "python_venvs"}
    targets: List[Tuple[str, str]] = []
    for cur, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in skip]
        for fn in sorted(files):
            full = os.path.join(cur, fn)
            if os.path.isfile(full):
                targets.append((full, label))
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description="指紋補登（治理集 / 指定目錄）")
    parser.add_argument("--dir", dest="scan_dir", default=None,
                        help="遞迴掃描指定目錄；省略時走治理集預設範圍")
    parser.add_argument("--label", default="raw_inbound",
                        help="--dir 模式下使用的 original_type 標籤")
    parser.add_argument("--run-id", dest="run_id", default="bookmark_v2_55",
                        help="event 寫入時使用的 run_id")
    parser.add_argument(
        "--agent",
        default="register_fingerprints_v2_55",
        help="寫入 content_hashes.agent / events.agent",
    )
    parser.add_argument(
        "--clean-status",
        dest="clean_status",
        default="indexed",
        help="非 pending 模式時寫入的 clean_status；pending 走不降級邏輯",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        default=None,
        help="只登錄列出的檔案（一個以上，絕對或相對路徑）；與 --dir 互斥，省略時走治理集",
    )
    args = parser.parse_args()

    reg = Chariot_Registry()
    print(f"DB: {reg.db_path}")

    if args.files:
        if args.scan_dir:
            print("[ERR] 不可同時指定 --files 與 --dir", file=sys.stderr)
            return 2
        items = []
        for raw in args.files:
            fp = os.path.abspath(os.path.normpath(raw))
            if not os.path.isfile(fp):
                print(f"[ERR] --files 含非檔案路徑：{fp}", file=sys.stderr)
                return 2
            items.append((fp, args.label))
        mode = "register_explicit_paths"
    elif args.scan_dir:
        scan_dir = os.path.abspath(args.scan_dir)
        if not os.path.isdir(scan_dir):
            print(f"[ERR] --dir 不存在或不是資料夾：{scan_dir}", file=sys.stderr)
            return 2
        print(f"Scan dir: {scan_dir}  label={args.label}")
        items = _gather_directory(scan_dir, args.label)
        mode = "register_directory_explicit"
    else:
        items = _gather_governance()
        mode = "register_governance_set"

    print(f"Targets: {len(items)} files")

    by_label: Dict[str, int] = {}
    by_label_new: Dict[str, int] = {}
    outcomes: Dict[str, int] = {}
    failures = 0

    for fp, label in items:
        try:
            digest = sha256_file(fp)
            existed = reg.has(digest)
            ext = os.path.splitext(fp)[1].lower()
            try:
                rel = os.path.relpath(fp, _root).replace("\\", "/")
            except ValueError:
                rel = fp.replace("\\", "/")
            if args.clean_status == "pending" and label == "raw_inbound":
                oc = reg.register_raw_inbound_pending(
                    digest,
                    agent=args.agent,
                    source_path=rel,
                    extension=ext,
                    original_type=label,
                )
                outcomes[oc] = outcomes.get(oc, 0) + 1
                if oc == "inserted_pending":
                    by_label_new[label] = by_label_new.get(label, 0) + 1
            else:
                st = "indexed" if mode == "register_governance_set" else args.clean_status
                reg.add(
                    digest,
                    agent=args.agent,
                    source_path=rel,
                    clean_status=st,
                    extension=ext,
                    original_type=label,
                )
                if not existed:
                    by_label_new[label] = by_label_new.get(label, 0) + 1
            by_label[label] = by_label.get(label, 0) + 1
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"[FAIL] {fp}: {type(e).__name__}")

    reg.add_event(
        agent=args.agent,
        run_id=args.run_id,
        kind=mode,
        payload={
            "scan_dir": args.scan_dir,
            "label": args.label,
            "by_label": by_label,
            "by_label_new": by_label_new,
            "outcomes": outcomes,
            "failures": failures,
            "clean_status": args.clean_status,
        },
    )

    print("---- 指紋補登 ----")
    print(json.dumps({
        "mode": mode,
        "scan_dir": args.scan_dir,
        "explicit_files": args.files,
        "by_label": by_label,
        "newly_inserted": by_label_new,
        "outcomes": outcomes,
        "failures": failures,
        "registry_total_rows": reg.count(),
    }, ensure_ascii=False, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
