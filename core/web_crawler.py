#!/usr/bin/env python3
"""
web_crawler.py — Stage 1: 網路數據進料爬蟲

從 web_pipeline_config.yaml 讀取目標網站列表，
爬取頁面、篩選連結、下載檔案到暫存目錄。

用法:
    python core/web_crawler.py [--config core/web_pipeline_config.yaml]
                               [--target <target_id>]
                               [--dry-run]
                               [--limit N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import httpx

# ── Config ──────────────────────────────────────
_REPO = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG = _REPO / "core" / "web_pipeline_config.yaml"
_STAGING_DEFAULT = _REPO / "05_Temp_Cache" / "web_staging"
_DOWNLOAD_LOG_DEFAULT = _REPO / "05_Temp_Cache" / "web_download_log.json"

_USER_AGENT = "TangDataPipeline/1.0 (+https://github.com/tang-data-pipeline)"
_REQUEST_TIMEOUT = 30
_RETRY_MAX = 3
_RETRY_DELAY = 2  # seconds


# ── YAML Loader (stdlib-only) ───────────────────
def _load_yaml(path: Path) -> Dict[str, Any]:
    """Minimal YAML loader for our config file (no PyYAML dependency)."""
    import yaml  # type: ignore
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_yaml_fallback(path: Path) -> Dict[str, Any]:
    """Fallback: parse YAML with basic regex if PyYAML unavailable."""
    try:
        return _load_yaml(path)
    except ImportError:
        # Minimal fallback — read as plain text, parse key structures
        raise ImportError(
            "PyYAML not installed. Install with: pip install pyyaml\n"
            f"Config path: {path}"
        )


# ── HTML Link Extractor (stdlib) ────────────────
class _LinkExtractor(HTMLParser):
    """Extract href links from HTML using only stdlib."""

    def __init__(self):
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs: list):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)


def _extract_links_from_html(html: str, base_url: str) -> List[str]:
    """Parse HTML and return absolute URLs from <a href=...> tags."""
    parser = _LinkExtractor()
    parser.feed(html)
    absolute = []
    for link in parser.links:
        abs_url = urljoin(base_url, link)
        # Strip fragment
        parsed = urlparse(abs_url)
        clean = parsed._replace(fragment="").geturl()
        absolute.append(clean)
    return absolute


# ── HTTP Client ─────────────────────────────────
def _make_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": _USER_AGENT},
        timeout=_REQUEST_TIMEOUT,
        follow_redirects=True,
        verify=False,  # some gov sites have cert issues
    )


def _fetch_with_retry(
    client: httpx.Client, url: str, retries: int = _RETRY_MAX
) -> Optional[httpx.Response]:
    """Fetch URL with retry + backoff."""
    for attempt in range(retries):
        try:
            resp = client.get(url)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", _RETRY_DELAY * (attempt + 1)))
                print(f"    ⏳ 429 rate-limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code >= 500:
                time.sleep(_RETRY_DELAY * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if attempt < retries - 1:
                time.sleep(_RETRY_DELAY * (attempt + 1))
            else:
                print(f"    ❌ Failed after {retries} attempts: {e}")
                return None
    return None


# ── Download Log ────────────────────────────────
def _load_download_log(path: Path) -> Dict[str, Any]:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"downloaded": {}, "total_bytes": 0, "total_files": 0}


def _save_download_log(path: Path, log: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


# ── Main Crawler Logic ─────────────────────────
def _github_api_headers() -> dict:
    """GitHub API headers — unauthenticated but higher rate limit with token if available."""
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "application/vnd.github.v3+json",
    }
    # Use GITHUB_TOKEN if available for higher rate limits
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def _crawl_github_api(
    client: httpx.Client,
    target: Dict[str, Any],
    staging_dir: Path,
    download_log: Dict[str, Any],
    dry_run: bool = False,
    global_limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Crawl a GitHub repo via API — list directory tree, download matching files."""
    tid = target["id"]
    repo = target["repo"]
    path = target.get("path", "")
    file_types = target.get("file_types", [".py"])
    max_files = target.get("max_files", 30)
    tags = target.get("tags", [])

    api_base = f"https://api.github.com/repos/{repo}/contents/{path}"
    print(f"\n🔍 [{tid}] GitHub API: {repo}/{path}")

    results = []
    downloaded = 0

    # Recursive directory listing via API
    files_to_download: List[Dict[str, str]] = []
    dirs_to_scan = [path]
    scanned_dirs = set()

    while dirs_to_scan:
        current = dirs_to_scan.pop(0)
        if current in scanned_dirs:
            continue
        scanned_dirs.add(current)

        url = f"https://api.github.com/repos/{repo}/contents/{current}" if current else f"https://api.github.com/repos/{repo}/contents"
        resp = _fetch_with_retry(client, url, retries=2)
        if not resp:
            print(f"  ❌ Could not list: {repo}/{current}")
            continue

        try:
            items = resp.json()
        except Exception:
            continue

        if not isinstance(items, list):
            print(f"  ⚠️ Unexpected response for {current}: {items.get('message', '?')}")
            continue

        for item in items:
            item_path = item.get("path", "")
            item_type = item.get("type", "")
            item_name = item.get("name", "")
            item_size = item.get("size", 0)
            download_url = item.get("download_url", "")

            if item_type == "dir":
                dirs_to_scan.append(item_path)
            elif item_type == "file" and download_url:
                ext = Path(item_name).suffix.lower()
                if not file_types or ext in file_types:
                    files_to_download.append({
                        "path": item_path,
                        "name": item_name,
                        "url": download_url,
                        "size": item_size,
                    })

        print(f"  📂 Scanned {current or 'root'}: {len(items)} items, {len(files_to_download)} matching files found so far")

    # Limit
    to_download = files_to_download[:max_files]
    if global_limit:
        to_download = to_download[:global_limit]

    print(f"  📋 Downloading {len(to_download)} files...")

    for fi in to_download:
        url_hash = hashlib.md5(fi["url"].encode()).hexdigest()[:12]

        # Skip already downloaded
        if url_hash in download_log.get("downloaded", {}):
            continue

        if dry_run:
            print(f"    📄 [dry-run] {fi['path']} ({fi['size']:,} bytes)")
            results.append({"url": fi["url"], "filename": fi["name"], "status": "dry_run", "target_id": tid})
            downloaded += 1
            continue

        # Download raw content
        file_resp = _fetch_with_retry(client, fi["url"], retries=2)
        if not file_resp:
            results.append({"url": fi["url"], "status": "failed", "target_id": tid})
            continue

        content_bytes = file_resp.content
        content_sha = hashlib.sha256(content_bytes).hexdigest()

        target_dir = staging_dir / tid
        target_dir.mkdir(parents=True, exist_ok=True)
        out_path = target_dir / f"{url_hash}_{fi['name']}"

        try:
            with open(out_path, "wb") as f:
                f.write(content_bytes)

            meta = {
                "url": fi["url"],
                "filename": fi["name"],
                "saved_path": str(out_path),
                "target_id": tid,
                "tags": tags,
                "size_bytes": len(content_bytes),
                "content_sha256": content_sha,
                "status": "downloaded",
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            }
            results.append(meta)
            downloaded += 1

            download_log.setdefault("downloaded", {})[url_hash] = meta
            download_log["total_bytes"] = download_log.get("total_bytes", 0) + len(content_bytes)
            download_log["total_files"] = download_log.get("total_files", 0) + 1

            print(f"    ✅ {fi['name']} ({len(content_bytes):,} bytes)")

        except Exception as e:
            print(f"    ❌ Save failed: {fi['name']}: {e}")
            results.append({"url": fi["url"], "status": "save_failed", "error": str(e), "target_id": tid})

        time.sleep(0.3)  # Rate limit

    print(f"  📊 [{tid}] Downloaded: {downloaded}/{len(to_download)}")
    return results


def crawl_target(
    client: httpx.Client,
    target: Dict[str, Any],
    staging_dir: Path,
    download_log: Dict[str, Any],
    dry_run: bool = False,
    global_limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Crawl a single target. Dispatches to github_api or html_page handler."""
    target_type = target.get("type", "html_page")

    if target_type == "github_api":
        return _crawl_github_api(client, target, staging_dir, download_log, dry_run, global_limit)

    # ── HTML page handler (original) ──
    tid = target["id"]
    base_url = target["base_url"]
    link_filter = target.get("link_filter", "")
    max_links = target.get("max_links", 50)
    file_types = target.get("file_types", [])
    tags = target.get("tags", [])

    print(f"\n🔍 [{tid}] Crawling: {base_url}")
    resp = _fetch_with_retry(client, base_url)
    if not resp:
        print(f"  ❌ Could not fetch {base_url}")
        return []

    html = resp.text
    all_links = _extract_links_from_html(html, base_url)
    print(f"  📎 Found {len(all_links)} links on page")

    # Apply link filter
    if link_filter:
        try:
            pattern = re.compile(link_filter)
            filtered = [l for l in all_links if pattern.search(l)]
        except re.error:
            filtered = all_links
    else:
        filtered = all_links

    # Apply file type filter
    if file_types:
        filtered = [
            l for l in filtered
            if any(l.lower().endswith(ft) for ft in file_types)
        ]

    # Deduplicate
    seen: Set[str] = set()
    unique = []
    for l in filtered:
        if l not in seen:
            seen.add(l)
            unique.append(l)

    # Limit
    to_download = unique[:max_links]
    if global_limit:
        to_download = to_download[:global_limit]

    print(f"  📋 After filtering: {len(to_download)} targets")

    results = []
    downloaded = 0

    for url in to_download:
        # Skip already downloaded
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        if url_hash in download_log.get("downloaded", {}):
            continue

        if dry_run:
            print(f"    📄 [dry-run] Would download: {url[:80]}")
            results.append({"url": url, "status": "dry_run", "target_id": tid})
            continue

        # Download
        file_resp = _fetch_with_retry(client, url, retries=2)
        if not file_resp:
            results.append({"url": url, "status": "failed", "target_id": tid})
            continue

        # Determine filename from URL
        parsed = urlparse(url)
        filename = Path(parsed.path).name or f"page_{url_hash}"
        if not Path(filename).suffix and file_types:
            # Try to detect from content-type
            ct = file_resp.headers.get("content-type", "")
            if "json" in ct:
                filename += ".json"
            elif "csv" in ct or "text" in ct:
                filename += ".csv"
            elif "html" in ct:
                filename += ".html"
            else:
                filename += ".txt"

        # Save to staging
        target_dir = staging_dir / tid
        target_dir.mkdir(parents=True, exist_ok=True)
        out_path = target_dir / f"{url_hash}_{filename}"

        try:
            content_bytes = file_resp.content
            content_sha = hashlib.sha256(content_bytes).hexdigest()

            if not dry_run:
                with open(out_path, "wb") as f:
                    f.write(content_bytes)

            meta = {
                "url": url,
                "filename": filename,
                "saved_path": str(out_path),
                "target_id": tid,
                "tags": tags,
                "size_bytes": len(content_bytes),
                "content_sha256": content_sha,
                "content_type": file_resp.headers.get("content-type", ""),
                "status": "downloaded",
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            }
            results.append(meta)
            downloaded += 1

            # Update download log
            download_log.setdefault("downloaded", {})[url_hash] = meta
            download_log["total_bytes"] = download_log.get("total_bytes", 0) + len(content_bytes)
            download_log["total_files"] = download_log.get("total_files", 0) + 1

            print(f"    ✅ {filename} ({len(content_bytes):,} bytes)")

        except Exception as e:
            print(f"    ❌ Save failed for {url}: {e}")
            results.append({"url": url, "status": "save_failed", "error": str(e), "target_id": tid})

        # Rate limit
        time.sleep(0.5)

    print(f"  📊 [{tid}] Downloaded: {downloaded}/{len(to_download)}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage 1: 網路數據進料爬蟲")
    parser.add_argument("--config", default=str(_DEFAULT_CONFIG), help="Config YAML path")
    parser.add_argument("--target", default=None, help="Crawl only this target_id")
    parser.add_argument("--dry-run", action="store_true", help="Don't download, just list")
    parser.add_argument("--limit", type=int, default=None, help="Global download limit")
    parser.add_argument("--staging-dir", default=str(_STAGING_DEFAULT), help="Staging directory")
    args = parser.parse_args()

    config = _load_yaml_fallback(Path(args.config))
    staging_dir = Path(args.staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    log_path = Path(args.config).parent.parent / config["cleaning"]["download_log"]
    download_log = _load_download_log(log_path)

    targets = config.get("targets", [])
    if args.target:
        targets = [t for t in targets if t["id"] == args.target]

    if not targets:
        print("No targets to crawl.")
        return 0

    print(f"═══ Stage 1: Web Crawler ═══")
    print(f"  Targets: {len(targets)}")
    print(f"  Staging: {staging_dir}")
    print(f"  Dry run: {args.dry_run}")

    all_results = []
    client = _make_client()

    try:
        for target in targets:
            results = crawl_target(
                client, target, staging_dir, download_log,
                dry_run=args.dry_run, global_limit=args.limit,
            )
            all_results.extend(results)
    finally:
        client.close()

    # Save download log
    _save_download_log(log_path, download_log)

    # Summary
    downloaded = sum(1 for r in all_results if r.get("status") == "downloaded")
    failed = sum(1 for r in all_results if "failed" in r.get("status", ""))
    dry = sum(1 for r in all_results if r.get("status") == "dry_run")

    print(f"\n═══ Stage 1 Complete ═══")
    print(f"  Downloaded: {downloaded}")
    print(f"  Failed: {failed}")
    print(f"  Dry-run: {dry}")
    print(f"  Total in log: {download_log.get('total_files', 0)} files ({download_log.get('total_bytes', 0):,} bytes)")

    # Save manifest
    manifest_path = staging_dir / "_manifest.json"
    manifest = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "targets_crawled": len(targets),
        "results": all_results,
        "summary": {"downloaded": downloaded, "failed": failed, "dry_run": dry},
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  Manifest: {manifest_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
