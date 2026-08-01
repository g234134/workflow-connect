#!/usr/bin/env python3
"""Rebuild all Obsidian vault category indexes from frontmatter."""
import os, re, sys
from pathlib import Path
from datetime import date

VAULT = Path(r"C:/Users/666LAG/OneDrive/文件/Obsidian Vault")
TODAY = date.today().isoformat()

# Category definitions: (dir relative to vault, index file relative to vault, display name, frontmatter block)
CATEGORIES = [
    ("AI-Research/Agent-Frameworks", "AI-Research/Agent-Frameworks/_Agent-Frameworks Index.md",
     "AI Agent Frameworks", """---
category: Agent Frameworks
repo_url: ''
source: github
stars: 0
tags:
- agent-frameworks
- ai-database
- ai-research
- index
- moc
type: resource
updated_at: '{date}'
---"""),
    ("AI-Research/MCP-Servers", "AI-Research/MCP-Servers/_MCP-Servers Index.md",
     "MCP Servers", """---
category: MCP Servers
repo_url: ''
source: github
stars: 0
tags:
- ai-database
- ai-research
- index
- mcp-servers
- moc
type: resource
updated_at: '{date}'
---"""),
    ("AI-Research/Tools", "AI-Research/Tools/_Tools Index.md",
     "AI Research Tools", ""),
    ("AI-Research/Skills", "AI-Research/Skills/_Agent Skills MOC.md",
     "Agent Skills", """---
category: Agent Skills
repo_url: ''
source: github
stars: 0
tags:
- ai-research
- index
- skills
- moc
type: resource
updated_at: '{date}'
---"""),
    ("AI-Learning/Courses", "AI-Learning/Courses/_Courses Index.md",
     "AI Learning Courses", """---
type: moc
area: ai-learning
category: courses
tags: [moc, ai-learning, index]
---"""),
    ("AI-Learning/Guides", "AI-Learning/Guides/_Guides Index.md",
     "AI Learning Guides", """---
type: moc
area: ai-learning
category: guides
tags: [moc, ai-learning, index]
---"""),
    ("AI-Learning/Tools", "AI-Learning/_Tools Index.md",
     "工具索引", """---
type: moc
area: ai-learning
category: tools
tags: [moc, ai-learning, index]
---"""),
]


def extract_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from markdown."""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split('\n'):
        k, _, v = line.partition(':')
        k = k.strip()
        v = v.strip().strip("'\"")
        if k:
            fm[k] = v
    return fm


def parse_notes(dir_path: Path) -> list[dict]:
    """Scan directory for .md notes, extract frontmatter."""
    notes = []
    if not dir_path.exists():
        return notes
    for f in sorted(dir_path.glob("*.md")):
        name = f.stem
        # Skip index/MOC files
        if name.startswith('_'):
            continue
        text = f.read_text(encoding='utf-8', errors='replace')
        fm = extract_frontmatter(text)
        stars = fm.get('stars', '?')
        github = fm.get('github', fm.get('repo_url', ''))
        # Try to extract github URL from body if not in frontmatter
        if not github or github == "''":
            gmatch = re.search(r'https://github\.com/[^\s\)]+', text)
            if gmatch:
                github = gmatch.group(0).rstrip(')')
        notes.append({
            'name': name,
            'stars': stars,
            'github': github,
        })
    return notes


def build_index(notes: list[dict], display_name: str, fm_block: str, date_str: str) -> str:
    """Build index markdown content."""
    lines = []
    if fm_block:
        lines.append(fm_block.format(date=date_str))
        lines.append("")

    lines.append(f"# {display_name}")
    lines.append("")
    lines.append(f"最後更新：{date_str}")
    lines.append("")
    lines.append(f"共 {len(notes)} 筆筆記")
    lines.append("")
    lines.append("## 筆記列表")
    lines.append("")

    for n in notes:
        stars_str = f"⭐{n['stars']}" if n['stars'] and n['stars'] != '?' else '⭐?'
        github_str = n['github'] if n['github'] and n['github'] not in ('?', '') else ''
        if github_str:
            lines.append(f"- [[{n['name']}]] {stars_str} — {github_str}")
        else:
            lines.append(f"- [[{n['name']}]] {stars_str}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📌 所属分类")
    lines.append("* 大目录：[[AI Agent 知识库 MOC]]")
    lines.append("")
    lines.append("## 🔗 相关工具与延伸链接")
    lines.append(f"* {display_name}")
    lines.append("")

    return '\n'.join(lines)


def main():
    total = 0
    for rel_dir, rel_index, display_name, fm_block in CATEGORIES:
        dir_path = VAULT / rel_dir
        index_path = VAULT / rel_index
        notes = parse_notes(dir_path)
        content = build_index(notes, display_name, fm_block, TODAY)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(content, encoding='utf-8')
        print(f"✅ {rel_index} — {len(notes)} notes")
        total += len(notes)

    print(f"\n🎉 Done! Updated {len(CATEGORIES)} indexes, {total} total notes.")


if __name__ == "__main__":
    main()
