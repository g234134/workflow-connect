"""
以 GitHub **官方 REST API** 取得公開儲存庫的 README（原始文字），存進 RAG 資料夾。
不解析網頁 HTML、不繞過登入；請遵守 GitHub 條款與該 repo 授權（LICENSE）。

用法：
  python rag_fetch_github.py
  python rag_fetch_github.py --list D:\\rag檔案庫\\github_repos.txt

環境變數（見 .env）：
  GITHUB_TOKEN          強烈建議設定（Fine-grained 或 classic PAT），提高速率上限
  GITHUB_API_BASE       預設 https://api.github.com
  RAG_ROOT              預設 D:\\rag檔案庫
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

RAG_ROOT = Path(os.environ.get("RAG_ROOT", r"D:\rag檔案庫")).resolve()
DEFAULT_LIST = RAG_ROOT / "github_repos.txt"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
API_BASE = os.environ.get("GITHUB_API_BASE", "https://api.github.com").rstrip("/")

OUT_SUBDIR = os.environ.get("GITHUB_TEXT_DIR", "文字")  # 也可改成「網頁」


def _parse_repo_line(line: str) -> tuple[str, str] | None:
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if "github.com" in s:
        u = urlparse(s)
        parts = [p for p in u.path.split("/") if p]
        if len(parts) >= 2:
            return parts[0], parts[1]
        return None
    if "/" in s:
        a, b = s.split("/", 1)
        if a and b and "/" not in b:
            return a.strip(), b.strip().split()[0]
    return None


def _load_repos(path: Path) -> list[tuple[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"找不到清單：{path}")
    out: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        p = _parse_repo_line(raw)
        if p:
            out.append(p)
    return out


def _out_dir(root: Path) -> Path:
    d = root / OUT_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_readme(owner: str, repo: str, client: httpx.Client) -> str:
    url = f"{API_BASE}/repos/{owner}/{repo}/readme"
    headers = {
        "Accept": "application/vnd.github.raw+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    r = client.get(url, headers=headers, timeout=60.0)
    if r.status_code == 404:
        raise RuntimeError("無 README 或儲存庫不存在／非公開可見內容")
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    return r.text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", type=Path, default=DEFAULT_LIST, help="repo 清單路徑")
    ap.add_argument("--sleep", type=float, default=0.4, help="每個請求之間秒數（禮貌延遲）")
    args = ap.parse_args()

    if not GITHUB_TOKEN:
        print(
            "[警告] 未設定 GITHUB_TOKEN，匿名請求速率較低（約 60 次/小時/IP）。\n"
            "建議在 GitHub → Settings → Developer settings 建立 Personal Access Token，\n"
            "並寫入 .env：GITHUB_TOKEN=ghp_..."
        )

    repos = _load_repos(args.list.resolve())
    if not repos:
        print(f"[錯誤] 清單為空：{args.list}")
        sys.exit(1)

    out_dir = _out_dir(RAG_ROOT)
    ok = 0
    with httpx.Client() as client:
        for owner, repo in repos:
            safe_name = re.sub(r"[^\w\-.]+", "_", f"{owner}__{repo}")
            out_path = out_dir / f"github_README_{safe_name}.md"
            head_path = out_dir / f"github_README_{safe_name}.meta.txt"
            try:
                body = fetch_readme(owner, repo, client)
                header = (
                    f"<!-- source: https://github.com/{owner}/{repo} -->\n"
                    f"<!-- fetched_via: GitHub REST API readme -->\n\n"
                )
                out_path.write_text(header + body, encoding="utf-8")
                head_path.write_text(
                    f"owner={owner}\nrepo={repo}\napi={API_BASE}\n",
                    encoding="utf-8",
                )
                print(f"[OK] {owner}/{repo} -> {out_path.name}")
                ok += 1
            except Exception as exc:
                print(f"[FAIL] {owner}/{repo} ({exc})")
            if args.sleep > 0:
                time.sleep(args.sleep)

    print(f"\n[完成] {ok}/{len(repos)}。輸出：{out_dir}")
    print("下一步：python rag_ingest_local.py")


if __name__ == "__main__":
    main()
