"""Download upstream docs into gov_core_system / Departments.

唯讀外部 → 寫入指定子資料夾。已存在檔案會覆寫（snapshot 用途）。
HTTP 非 200 視為失敗、記錄 URL 與狀態碼後跳過。

Usage:
    python 04_Workflows/_download_dept_docs.py
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple

ROOT = Path(
    r"D:\大唐三省六部\01_Environments\python_venvs\gov_core_system\Departments"
)
TIMEOUT = 30
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chariot-Doc-Snapshot/1.0"
    ),
    "Accept": "*/*",
}

# (relative_subdir, url, output_filename)
JOBS: List[Tuple[str, str, str]] = [
    ("01_Orchestration",
     "https://github.com/langchain-ai/langgraph/raw/main/README.md",
     "README_langgraph.md"),
    ("01_Orchestration",
     "https://docs.langchain.com/oss/python/langgraph/overview",
     "langgraph_overview.html"),

    ("02_Brain_GraphRAG",
     "https://github.com/microsoft/graphrag/raw/main/README.md",
     "README_graphrag.md"),
    ("02_Brain_GraphRAG",
     "https://raw.githubusercontent.com/microsoft/graphrag/main/docs/get_started.md",
     "graphrag_get_started.md"),
    ("02_Brain_GraphRAG",
     "https://microsoft.github.io/graphrag/",
     "graphrag_home.html"),

    ("03_Observability",
     "https://github.com/langfuse/langfuse-python/raw/main/README.md",
     "README_langfuse_python.md"),
    ("03_Observability",
     "https://langfuse.com/self-hosting/deployment/infrastructure/postgres",
     "langfuse_postgres_self_hosting.html"),
]


def download(url: str, out_path: Path) -> Tuple[bool, int, int]:
    """Return (success, http_status, bytes_written).

    stdlib only — urllib.request 自動跟隨 redirect。
    """
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            data = resp.read()
    except urllib.error.HTTPError as exc:
        return False, exc.code, 0
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"  [ERR ] {url} -> {exc!r}")
        return False, -1, 0

    if status != 200:
        return False, status, 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return True, 200, len(data)


def main() -> int:
    if not ROOT.exists():
        print(f"[FATAL] Departments root not found: {ROOT}")
        return 2

    print(f"Departments root : {ROOT}")
    print(f"Total jobs       : {len(JOBS)}")
    print("-" * 78)

    successes: List[Tuple[Path, int]] = []
    failures: List[Tuple[str, int]] = []

    for subdir, url, fname in JOBS:
        out = ROOT / subdir / fname
        ok, code, n = download(url, out)
        if ok:
            print(f"  [OK   {n:>10,} B] {subdir}/{fname}")
            successes.append((out, n))
        else:
            print(f"  [FAIL HTTP={code}] {url}")
            failures.append((url, code))

    print("-" * 78)
    infra = ROOT / "04_Infrastructure" / "docker-compose.yml"
    if infra.exists():
        sz = infra.stat().st_size
        print(f"  [INFRA] docker-compose.yml present, size={sz:,} B")
        print(f"          path={infra}")
    else:
        print(f"  [INFRA] docker-compose.yml MISSING in {infra.parent}")

    print()
    print("=" * 78)
    print(f"SUMMARY  success={len(successes)}   failure={len(failures)}")
    if failures:
        print("Failures:")
        for url, code in failures:
            print(f"  - HTTP {code}: {url}")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
