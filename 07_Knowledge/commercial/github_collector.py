#!/usr/bin/env python3
"""
GitHub AI 資訊收集器
搜尋 MCP servers、AI skills、agent frameworks 等，
儲存到 Obsidian vault。

用法:
  python github_collector.py              # 執行一次收集
  python github_collector.py --cron       # 排程模式（每 6 小時）
  python github_collector.py --search "mcp server"  # 自訂搜尋關鍵字
"""

import json
import os
import re
import sys
import time
import subprocess
import ssl
from datetime import datetime, timedelta
from pathlib import Path

# === 設定 ===
VAULT_ROOT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "C:/Users/666LAG/OneDrive/文件/Obsidian Vault"))
VAULT_PATH = VAULT_ROOT / "AI-Research"
GITHUB_API = "https://api.github.com"
STATE_FILE = Path("D:/大唐三省六部/07_Knowledge/commercial/github_collector_state.json")
REBUILD_SCRIPT = VAULT_ROOT / "AI-Research" / "scripts" / "rebuild_indexes.py"

# folder → (area, category) — must match destination path
FOLDER_META = {
    "MCP-Servers": ("ai-research", "mcp-servers"),
    "Skills": ("ai-research", "skills"),
    "Agent-Frameworks": ("ai-research", "agent-frameworks"),
    "Tools": ("ai-research", "tools"),
    "Projects": ("ai-research", "projects"),
}

ssl_ctx = ssl.create_default_context()


def _normalize_github(url: str) -> str:
    if not url:
        return ""
    url = url.strip().rstrip("/").lower()
    url = re.sub(r"\.git$", "", url)
    m = re.search(r"(https?://github\.com/[^/\s]+/[^/\s?#]+)", url)
    return m.group(1) if m else url


def find_existing_note_by_github(url: str):
    """Skip creating a second copy if the same github URL already exists anywhere in AI areas."""
    target = _normalize_github(url)
    if not target:
        return None
    for area in ("AI-Learning", "AI-Research"):
        root = VAULT_ROOT / area
        if not root.exists():
            continue
        for md in root.rglob("*.md"):
            if md.stem.startswith("_") or "Novels" in md.parts or "Daily-Digest" in md.parts:
                continue
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            m = re.search(
                r"(?:github|github_url|repo_url):\s*[\"']?(https?://github\.com/[^\s\"']+)",
                text,
                re.I,
            )
            if m and _normalize_github(m.group(1)) == target:
                return md
    return None


def rebuild_indexes():
    """Always regenerate category indexes after collection (canonical nested paths only)."""
    if not REBUILD_SCRIPT.exists():
        print(f"  ⚠️ rebuild script missing: {REBUILD_SCRIPT}")
        return
    result = subprocess.run(
        [sys.executable, str(REBUILD_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"  ⚠️ rebuild_indexes failed: {result.stderr[-300:] if result.stderr else result.stdout[-300:]}")
    else:
        print("  📋 indexes rebuilt")

# 搜尋關鍵字（可擴充）
SEARCH_QUERIES = [
    # MCP 生態系
    ("MCP Servers", "model context protocol server", "MCP-Servers"),
    ("MCP Clients", "model context protocol client", "MCP-Servers"),
    
    # AI Skills / Agent 工具
    ("AI Skills", "agent skill plugin", "Skills"),
    ("Prompt Tools", "prompt engineering tool", "Skills"),
    
    # Agent Frameworks
    ("Agent Frameworks", "ai agent framework", "Agent-Frameworks"),
    ("Multi-Agent", "multi agent orchestration", "Agent-Frameworks"),
    ("LangChain", "langchain agent", "Agent-Frameworks"),
    ("CrewAI", "crewai agent", "Agent-Frameworks"),
    ("AutoGen", "autogen microsoft", "Agent-Frameworks"),
    
    # AI 工具鏈
    ("RAG Tools", "rag retrieval augmented", "Skills"),
    ("Embedding Tools", "text embedding tool", "Skills"),
    ("Vector DB", "vector database tool", "Skills"),
    
    # 新興趨勢
    ("AI Gateway", "ai api gateway proxy", "Agent-Frameworks"),
    ("LLM Ops", "llm operations monitoring", "Agent-Frameworks"),
    ("Fine-tuning", "llm fine-tuning tool", "Skills"),
]

# 每次搜尋取前 N 個結果
RESULTS_PER_QUERY = 10


def load_state():
    """載入上次收集狀態"""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"last_run": None, "seen_repos": [], "total_collected": 0}


def save_state(state):
    """儲存收集狀態"""
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def github_search(query, sort="stars", per_page=10):
    """搜尋 GitHub repo"""
    params = urllib.parse.urlencode({
        "q": query + " stars:>10",
        "sort": sort,
        "per_page": per_page,
    })
    try:
        result = subprocess.run(
            ["gh", "api", f"search/repositories?{params}"],
            capture_output=True, text=True, timeout=20,
        )
        if result.returncode != 0:
            print(f"  ⚠️ 搜尋失敗: {result.stderr[:200]}")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"  ⚠️ 搜尋失敗: {e}")
        return None


def format_stars(n):
    """格式化星標數"""
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def create_repo_note(repo, folder, query_name):
    """建立 repo 的 Obsidian 筆記（同 github URL 已存在則就地更新／跳過第二份）。"""
    name = repo["name"]
    full_name = repo["full_name"]
    desc = repo.get("description", "No description") or "No description"
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    lang = repo.get("language", "N/A") or "N/A"
    url = repo["html_url"]
    topics = repo.get("topics", [])
    created = repo.get("created_at", "")[:10]
    updated = repo.get("updated_at", "")[:10]
    license_info = repo.get("license")
    license_name = license_info["spdx_id"] if license_info else "N/A"
    area, category = FOLDER_META.get(folder, ("ai-research", folder.lower()))

    if folder not in FOLDER_META:
        raise ValueError(f"refusing unknown folder {folder!r} — not in FOLDER_META")

    if len(desc) > 200:
        desc = desc[:197] + "..."

    dest_dir = VAULT_PATH / folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    note_path = dest_dir / f"{name}.md"

    existing = find_existing_note_by_github(url)
    if existing is not None:
        try:
            existing.relative_to(dest_dir)
            note_path = existing  # update in place
        except ValueError:
            print(f"  ⏭️  skip duplicate github → {existing.relative_to(VAULT_ROOT).as_posix()}")
            return None

    content = f"""---
type: resource
area: {area}
category: {category}
github: {url}
stars: {stars}
forks: {forks}
language: {lang}
created: {created}
updated: {updated}
license: {license_name}
query: {query_name}
collected: {datetime.now().strftime('%Y-%m-%d')}
source: github
tags: [github, ai, ai-research, {category}, resource]
---

# {full_name}

> {desc}

## 基本資訊

| 項目 | 內容 |
|------|------|
| ⭐ Stars | {format_stars(stars)} |
| 🍴 Forks | {forks} |
| 💻 語言 | {lang} |
| 📜 License | {license_name} |
| 📅 建立 | {created} |
| 🔄 更新 | {updated} |

## 連結

- [GitHub]({url})

"""

    if topics:
        content += f"## Topics\n\n{', '.join(['`' + t + '`' for t in topics])}\n\n"

    content += f"""## 相關

- [[_{folder} Index|{folder} 主目錄]]

---
*Collected by Tank AI Collector — {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    note_path.write_text(content, encoding="utf-8")
    return note_path


def create_daily_digest(repos_by_folder, date_str):
    """建立每日摘要"""
    content = f"""---
tags: [daily-digest, ai-research]
date: {date_str}
collected: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# AI 研究日報 — {date_str}

## 📊 今日收集統計

| 分類 | 數量 |
|------|------|
"""
    
    total = 0
    for folder, repos in repos_by_folder.items():
        content += f"| {folder} | {len(repos)} |\n"
        total += len(repos)
    
    content += f"| **總計** | **{total}** |\n\n"
    
    # Top repos by stars
    all_repos = []
    for repos in repos_by_folder.values():
        all_repos.extend(repos)
    all_repos.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    
    content += "## 🌟 今日 Top 10（按星標）\n\n"
    for i, repo in enumerate(all_repos[:10], 1):
        stars = format_stars(repo.get("stargazers_count", 0))
        desc = (repo.get("description") or "No description")[:80]
        content += f"{i}. **[{repo['full_name']}]({repo['html_url']})** ⭐ {stars}\n"
        content += f"   {desc}\n\n"
    
    content += f"\n---\n*Generated by Tank AI Collector — {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    
    digest_path = VAULT_PATH / "Daily-Digest" / f"{date_str}.md"
    digest_path.write_text(content, encoding="utf-8")
    return digest_path


def run_collection():
    """執行一次完整收集"""
    print(f"🔍 開始收集 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    state = load_state()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 檢查今天是否已經收集過（防止重複）
    last_run = state.get("last_run") or ""
    if last_run.startswith(date_str):
        print("📅 今天已經收集過了，跳過")
        return
    
    seen = set(state.get("seen_repos", []))
    repos_by_folder = {}
    new_count = 0
    
    for folder, query, category in SEARCH_QUERIES:
        print(f"🔍 搜尋: {query} ({category})")
        result = github_search(query, per_page=RESULTS_PER_QUERY)
        
        if not result or not result.get("items"):
            print(f"  ⚠️ 無結果")
            continue
        
        repos = result["items"]
        print(f"  📦 找到 {len(repos)} 個 repo")
        
        if category not in repos_by_folder:
            repos_by_folder[category] = []
        
        for repo in repos:
            full_name = repo["full_name"]
            if full_name in seen:
                continue
            
            # 建立筆記
            try:
                note_path = create_repo_note(repo, category, folder)
                if note_path is None:
                    seen.add(full_name)
                    continue
                repos_by_folder[category].append(repo)
                seen.add(full_name)
                new_count += 1
                print(f"  ✅ {full_name} ({format_stars(repo.get('stargazers_count', 0))} ⭐)")
            except Exception as e:
                print(f"  ❌ {full_name}: {e}")
        
        # GitHub API 限速：未認證每小時 10 次搜尋
        time.sleep(2)
    
    # 建立每日摘要（只寫入 Daily-Digest，永不寫 vault root）
    if repos_by_folder:
        digest_dir = VAULT_PATH / "Daily-Digest"
        digest_dir.mkdir(parents=True, exist_ok=True)
        digest_path = create_daily_digest(repos_by_folder, date_str)
        print(f"\n📊 日報已建立: {digest_path}")

    # 索引一律由磁碟重建（禁止在 area root 另寫 Index）
    rebuild_indexes()
    
    # 更新狀態
    state["last_run"] = datetime.now().isoformat()
    state["seen_repos"] = list(seen)
    state["total_collected"] = state.get("total_collected", 0) + new_count
    save_state(state)
    
    print(f"\n✅ 完成！新增 {new_count} 個 repo，累計 {state['total_collected']} 個")


def main():
    if "--verify" in sys.argv:
        if not REBUILD_SCRIPT.exists():
            print(f"missing {REBUILD_SCRIPT}")
            sys.exit(1)
        result = subprocess.run(
            [sys.executable, str(REBUILD_SCRIPT), "--verify"],
        )
        sys.exit(result.returncode)
    if "--rebuild" in sys.argv:
        rebuild_indexes()
        return
    if "--cron" in sys.argv:
        # 排程模式：每天收集 2 次（02:00, 14:00）
        while True:
            now = datetime.now()
            hour = now.hour
            
            # 在 2:00 或 14:00 執行
            if hour in (2, 14):
                run_collection()
            
            # 等到下一個小時
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0)
            wait_seconds = (next_hour - now).total_seconds()
            print(f"⏳ 等待 {wait_seconds/3600:.1f} 小時...")
            time.sleep(wait_seconds)
    elif "--search" in sys.argv:
        # 自訂搜尋
        idx = sys.argv.index("--search")
        if idx + 1 < len(sys.argv):
            query = sys.argv[idx + 1]
            print(f"🔍 自訂搜尋: {query}")
            result = github_search(query, per_page=20)
            if result and result.get("items"):
                for repo in result["items"]:
                    stars = format_stars(repo.get("stargazers_count", 0))
                    print(f"  {repo['full_name']} — ⭐ {stars}")
                    print(f"    {(repo.get('description') or '')[:80]}")
                    print()
    else:
        # 單次執行
        run_collection()


if __name__ == "__main__":
    import urllib.parse
    main()
