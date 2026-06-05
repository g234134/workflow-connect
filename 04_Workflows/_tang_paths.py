"""Workflow 共用：sys.path 靴帶 + 檔案 SHA256。

凡 `04_Workflows/*.py` 需 import `gov_paths` / Agents_Core 模組者，先呼叫
`bootstrap_sys_path(os.path.dirname(os.path.abspath(__file__)))`。
"""
from __future__ import annotations

import hashlib
import os
import sys
from typing import Final


def bootstrap_sys_path(workflows_dir: str) -> str:
    """將 `02_Agents_Core` 與 `04_Workflows` 置入 sys.path 前段；回傳 tang_gov 根目錄。"""
    root = os.path.normpath(os.path.join(workflows_dir, ".."))
    agents = os.path.join(root, "02_Agents_Core")
    for p in (agents, workflows_dir):
        if p not in sys.path:
            sys.path.insert(0, p)
    return root


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
