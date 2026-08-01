#!/usr/bin/env python3
"""Remove UTF-8 BOM from JSON config files under D:\\AI_HUB\\config.

Preserves exact file content (field order, whitespace) by stripping only the
3-byte BOM prefix instead of re-serializing JSON.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime

BOM = b"\xef\xbb\xbf"
DEFAULT_CONFIG_DIR = r"D:\大唐三省六部\06_Exports_Output\Legacy\AI_HUB\config"


def has_bom(path: str) -> bool:
    with open(path, "rb") as f:
        return f.read(3) == BOM


def strip_bom(path: str) -> bool:
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(BOM):
        return False
    with open(path, "wb") as f:
        f.write(data[len(BOM) :])
    return True


def verify_json_utf8(path: str) -> None:
    import json

    with open(path, encoding="utf-8") as f:
        json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove UTF-8 BOM from JSON config files")
    parser.add_argument(
        "--config-dir",
        default=DEFAULT_CONFIG_DIR,
        help=f"Config directory (default: {DEFAULT_CONFIG_DIR})",
    )
    parser.add_argument("--no-backup", action="store_true", help="Skip backup before modifying")
    parser.add_argument("--check-only", action="store_true", help="Report BOM status only")
    args = parser.parse_args()

    config_dir = os.path.abspath(args.config_dir)
    if not os.path.isdir(config_dir):
        print(f"ERROR: config dir not found: {config_dir}", file=sys.stderr)
        return 1

    json_files = sorted(
        fn for fn in os.listdir(config_dir) if fn.lower().endswith(".json")
    )
    if not json_files:
        print(f"No JSON files in {config_dir}")
        return 0

    print(f"Config dir: {config_dir}")
    print(f"JSON files: {', '.join(json_files)}")

    bom_files = [fn for fn in json_files if has_bom(os.path.join(config_dir, fn))]
    if args.check_only:
        for fn in json_files:
            status = "BOM" if fn in bom_files else "OK"
            print(f"  {fn}: {status}")
        return 1 if bom_files else 0

    if bom_files:
        if not args.no_backup:
            parent = os.path.dirname(config_dir.rstrip("\\/"))
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = os.path.join(parent, f"config.backup_{stamp}")
            shutil.copytree(config_dir, backup)
            print(f"Backup: {backup}")

        for fn in bom_files:
            path = os.path.join(config_dir, fn)
            strip_bom(path)
            print(f"Fixed: {fn} (BOM removed)")
    else:
        print("No BOM found; nothing to fix.")

    print("\nVerification:")
    failed = False
    for fn in json_files:
        path = os.path.join(config_dir, fn)
        try:
            verify_json_utf8(path)
            bom = "BOM" if has_bom(path) else "no BOM"
            print(f"  {fn}: utf-8 json.load OK, {bom}")
        except Exception as exc:
            print(f"  {fn}: FAIL — {exc}")
            failed = True

    return 1 if failed or bom_files and args.check_only else 0


if __name__ == "__main__":
    raise SystemExit(main())
