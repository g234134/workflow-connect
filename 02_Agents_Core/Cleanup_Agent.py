# Cleanup_Agent.py — 工部·物理銷毀執行器
# 嚴格守則：未提供 signed_token 直接拒絕；每件刪除以 cleanup_executed 事件入 C3。

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from gov_paths import (  # type: ignore
    get_tang_gov_root,
    resolve_agent_output_path,
)


class Cleanup_Agent:
    """工部·物理銷毀器：依簽押 token 對指定路徑執行 os.remove。"""

    AGENT_NAME = "Cleanup_Agent"
    DEPARTMENT = "工部"

    def __init__(self, *, dest_root: Optional[str] = None, signed_token: str = "") -> None:
        if not signed_token:
            raise ValueError("Cleanup_Agent 拒絕無簽押啟動：missing_signed_token")
        self.signed_token = signed_token
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        self.archive_dir = resolve_agent_output_path(self.dest_root, "06_Exports_Output", "archive")
        self.format_error_dir = os.path.join(self.archive_dir, "format_error")

    def list_zero_byte_in_format_error(self) -> List[str]:
        files: List[str] = []
        if not os.path.isdir(self.format_error_dir):
            return files
        for dp, _, fns in os.walk(self.format_error_dir):
            for fn in fns:
                if fn == ".department.txt":
                    continue
                fp = os.path.join(dp, fn)
                try:
                    if os.path.getsize(fp) == 0:
                        files.append(fp)
                except OSError:
                    continue
        files.sort()
        return files

    def destroy_files(self, paths: List[str], *, scope: str = "format_error_zero_byte") -> Dict[str, Any]:
        self.agent.set_status(AgentStatus.Running.value, reason=f"cleanup_destroy_start scope={scope}")
        self.agent.log_event(
            event="cleanup_destroy_start",
            scope=scope,
            target_count=len(paths),
            signed_token=self.signed_token,
        )

        deleted: List[str] = []
        errors: List[Dict[str, str]] = []
        for fp in paths:
            try:
                size = os.path.getsize(fp) if os.path.exists(fp) else -1
            except OSError:
                size = -1
            try:
                os.remove(fp)
                deleted.append(fp)
                self.agent.log_event(
                    event="cleanup_executed",
                    path=fp,
                    size_bytes=size,
                    scope=scope,
                )
            except OSError as e:
                errors.append({"path": fp, "error": str(e)})
                self.agent.log_event(
                    event="cleanup_failed",
                    status=AgentStatus.Failed.value,
                    path=fp,
                    error=str(e),
                )

        self.agent.set_status(
            AgentStatus.Success.value if not errors else AgentStatus.Manual.value,
            reason=f"cleanup_done deleted={len(deleted)} errors={len(errors)}",
        )
        return {
            "ok": not errors,
            "deleted_count": len(deleted),
            "errors": errors,
            "deleted_paths": deleted,
            "scope": scope,
            "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Cleanup_Agent CLI")
    parser.add_argument("--signed-token", required=True)
    parser.add_argument("--scope", default="format_error_zero_byte")
    args = parser.parse_args()

    a = Cleanup_Agent(signed_token=args.signed_token)
    targets = a.list_zero_byte_in_format_error()
    out = a.destroy_files(targets, scope=args.scope)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
