#!/usr/bin/env python3
"""Scrape ALL 贩罪 chapters from piaotia.com (full series)."""
import requests
import re
import os
import time
import sys

BASE_URL = "https://www.piaotia.com/html/1/1084/"
OUTPUT_DIR = "C:/Users/666LAG/OneDrive/文件/Obsidian Vault/Novels/贩罪/chapters"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
NOVEL_TITLE = "贩罪"
NOVEL_AUTHOR = "三天两觉"


def get_chapter_list():
    """Get all chapter links from index page."""
    resp = requests.get(BASE_URL + "index.html", headers=HEADERS, timeout=15)
    resp.encoding = 'gbk'
    soup_text = resp.text
    chapters = re.findall(r'<a\s+href=\"(\d+\.html)\"\s*>(.+?)</a>', soup_text)
    return chapters


def get_chapter_content(chapter_id):
    """Get chapter content by ID."""
    url = BASE_URL + chapter_id
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = 'gbk'
    text = resp.text

    # Content is between '返回书页</a></div>' and '<!-- 翻页上AD开始'
    start_marker = '返回书页</a></div>'
    end_marker = '<!-- 翻页上AD开始'

    start = text.find(start_marker)
    end = text.find(end_marker)

    if start > 0 and end > 0:
        content_html = text[start + len(start_marker):end]
        # Clean HTML
        content = re.sub(r'<[^>]+>', '', content_html)
        content = content.replace('&nbsp;', ' ')
        content = re.sub(r'\r?\n{3,}', '\n\n', content)
        content = content.strip()
        return content

    return None


def sanitize_filename(name):
    """Remove illegal chars from filename."""
    return re.sub(r'[\\/*?:"<>|]', '', name)


def main():
    start_chapter = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end_chapter = int(sys.argv[2]) if len(sys.argv) > 2 else 999

    print(f"=== {NOVEL_TITLE} 小说抓取 (第{start_chapter}-{end_chapter}章) ===")

    # Ensure output dir exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Check existing chapters
    existing = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.md'):
            match = re.match(r'(\d+)_', f)
            if match:
                existing.add(int(match.group(1)))
    print(f"现有章节: {len(existing)}")

    # Get chapter list
    print("\n获取章节列表...")
    chapters = get_chapter_list()
    total = len(chapters)
    print(f"网站总章节数: {total}")

    # Download chapters
    print(f"\n开始抓取第{start_chapter}-{end_chapter}章...")

    new_count = 0
    skip_count = 0
    fail_count = 0

    for i, (chapter_id, title) in enumerate(chapters):
        chapter_num = i + 1

        if chapter_num < start_chapter:
            continue
        if chapter_num > end_chapter or chapter_num > total:
            break

        # Skip if already exists
        if chapter_num in existing:
            skip_count += 1
            continue

        print(f"  [{chapter_num}/{total}] {title}...", end=' ', flush=True)

        content = get_chapter_content(chapter_id)

        if content and len(content) > 100:
            safe_title = sanitize_filename(title)
            filename = f"{chapter_num:03d}_{safe_title}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("---\n")
                f.write("type: novel-chapter\n")
                f.write(f"series: {NOVEL_TITLE}\n")
                f.write(f"chapter: {chapter_num}\n")
                f.write(f"title: {title}\n")
                f.write(f"author: {NOVEL_AUTHOR}\n")
                f.write("source: piaotia.com\n")
                f.write("tags: [贩罪]\n")
                f.write("date: 2026-08-02\n")
                f.write("---\n\n")
                f.write(f"# {title}\n\n")
                f.write(content)
                f.write("\n\n---\n\n")
                f.write("## 📖 相关链接\n\n")
                f.write("- [[index|贩罪索引]] — 返回主索引\n")

            print(f"✅ ({len(content)} chars)")
            new_count += 1
        else:
            print("❌ 内容获取失败")
            fail_count += 1

        # Sleep between requests
        time.sleep(2.0)

    print(f"\n=== 完成 ===")
    print(f"新增: {new_count} 章")
    print(f"跳过(已有): {skip_count} 章")
    print(f"失败: {fail_count} 章")
    print(f"总计: {len(existing) + new_count} 章")


if __name__ == '__main__':
    main()
