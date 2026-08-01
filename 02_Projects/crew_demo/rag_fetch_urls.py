"""
從「網址清單」取得網頁內容，存成 Markdown 到 RAG 資料夾，供後續 rag_ingest_local.py 入庫。

預設優先走 Firecrawl（你在 .env 的 FIRECRAWL_API_KEY），由第三方服務輸出乾淨 Markdown。
若沒有 Firecrawl key，可用 --mode direct，並會嘗試遵守 robots.txt（仍請自行確認授權／條款）。

此腳本不會自動「整站爬蟲」，只處理清單內逐行 URL。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from dotenv import load_dotenv

load_dotenv()

RAG_ROOT = Path(os.environ.get("RAG_ROOT", r"D:\rag檔案庫")).resolve()
DEFAULT_LIST = RAG_ROOT / "urls_allowlist.txt"
FIRECRAWL_KEY = os.environ.get("FIRECRAWL_API_KEY", "").strip()
USER_AGENT = os.environ.get(
    "FETCH_USER_AGENT",
    "RAGLocalFetcher/1.0 (+local-rag; respect robots.txt)",
)


def _find_web_out_dir(root: Path) -> Path:
    for name in ("網頁", "web", "Web"):
        p = root / name
        if p.is_dir():
            return p
    p = root / "網頁"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _slug_from_url(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    try:
        host = urlparse(url).netloc.replace(":", "_") or "site"
        host = re.sub(r"[^\w\-.]+", "_", host)[:40]
    except Exception:
        host = "site"
    return f"{host}_{h}"


def _load_urls(path: Path) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(f"找不到清單：{path}")
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if not s.lower().startswith(("http://", "https://")):
            continue
        lines.append(s)
    return lines


def _robots_allows(url: str) -> tuple[bool, str]:
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.netloc:
            return False, "bad-url"
        robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        ok = rp.can_fetch(USER_AGENT, url)
        return ok, robots_url
    except Exception as exc:
        return False, f"robots-error:{exc}"


def fetch_firecrawl(url: str, client: httpx.Client) -> tuple[str, dict]:
    r = client.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={
            "Authorization": f"Bearer {FIRECRAWL_KEY}",
            "Content-Type": "application/json",
        },
        json={"url": url, "formats": ["markdown"]},
        timeout=120.0,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Firecrawl HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"Firecrawl success=false: {str(data)[:300]}")
    md = (data.get("data") or {}).get("markdown") or ""
    meta = (data.get("data") or {}).get("metadata") or {}
    if not md.strip():
        raise RuntimeError("Firecrawl 回傳空白 markdown")
    header = f"<!-- source_url: {url} -->\n"
    return header + md.strip() + "\n", meta


def fetch_direct(url: str, client: httpx.Client) -> str:
    allows, info = _robots_allows(url)
    if not allows:
        raise RuntimeError(f"robots.txt 不允許或未通過檢查：{info}")
    r = client.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"},
        timeout=60.0,
        follow_redirects=True,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}")
    # 粗略保存 HTML；後續 ingest 會走簡單去標籤（或由你再轉 md）
    html = r.text
    header = f"<!-- source_url: {url} -->\n<!-- fetched_mode: direct_html -->\n"
    return header + html


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--list",
        type=Path,
        default=DEFAULT_LIST,
        help=f"URL 清單（一行一個），預設：{DEFAULT_LIST}",
    )
    ap.add_argument(
        "--mode",
        choices=("auto", "firecrawl", "direct"),
        default="auto",
        help="auto：有 Firecrawl key 就走 Firecrawl，否則需你再指定 direct",
    )
    ap.add_argument("--delay", type=float, default=2.0, help="direct 模式每個 URL 之間秒數")
    ap.add_argument(
        "--i-know-direct-risk",
        action="store_true",
        help="當沒有 Firecrawl 且要用 direct 時必須加上（提醒自己確認授權）",
    )
    args = ap.parse_args()

    urls = _load_urls(args.list.resolve())
    if not urls:
        print(f"[警告] 清單沒有有效 URL：{args.list}")
        return

    out_dir = _find_web_out_dir(RAG_ROOT)
    mode = args.mode
    if mode == "auto":
        mode = "firecrawl" if FIRECRAWL_KEY else "direct"

    if mode == "direct" and not args.i_know_direct_risk:
        print(
            "[錯誤] direct 模式可能牽涉網站條款／著作權。\n"
            "若你沒有 Firecrawl key，請改用：\n"
            "  1) 在 .env 填 FIRECRAWL_API_KEY（建議），或\n"
            "  2) 加上參數：--i-know-direct-risk\n"
            "並確認你只抓取你有權使用的內容。"
        )
        sys.exit(2)

    http = httpx.Client()
    ok = 0
    for i, url in enumerate(urls, start=1):
        slug = _slug_from_url(url)
        try:
            if mode == "firecrawl":
                if not FIRECRAWL_KEY:
                    raise RuntimeError("缺少 FIRECRAWL_API_KEY")
                body, _meta = fetch_firecrawl(url, http)
                out_path = out_dir / f"{i:03d}_{slug}.md"
                out_path.write_text(body, encoding="utf-8")
            else:
                body = fetch_direct(url, http)
                out_path = out_dir / f"{i:03d}_{slug}.html"
                out_path.write_text(body, encoding="utf-8")
            print(f"[OK] {i}/{len(urls)} -> {out_path.name}")
            ok += 1
        except Exception as exc:
            print(f"[FAIL] {url}  ({exc})")

        if mode == "direct" and args.delay > 0:
            time.sleep(args.delay)

    http.close()
    print(f"\n[完成] 成功 {ok}/{len(urls)}。輸出目錄：{out_dir}")
    print("下一步：python rag_ingest_local.py  （把新檔案索引進向量庫）")


if __name__ == "__main__":
    main()
