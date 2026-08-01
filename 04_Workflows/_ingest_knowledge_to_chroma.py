#!/usr/bin/env python
"""
ingest_knowledge_to_chroma.py — 將 C2_核心知識庫 的 JSON 餵入 ChromaDB 持久化。

Usage:
    PYTHONPATH="" python _ingest_knowledge_to_chroma.py        # ingest all
    PYTHONPATH="" python _ingest_knowledge_to_chroma.py --dry-run  # 只看不寫
"""
from __future__ import annotations

import json
import os
import sys
import argparse
from pathlib import Path

# ── 專案路徑 ───────────────────────────────────────────────────
_THIS = Path(__file__).resolve().parent
_TANG = _THIS.parent  # 大唐三省六部
CHROMA_DIR = _TANG / "03_RAG_Database" / "vector_stores" / "chroma_db"
KNOWLEDGE_DIR = _TANG / "03_RAG_Database" / "C2_核心知識庫"
COLLECTION_NAME = "knowledge_base"

os.makedirs(CHROMA_DIR, exist_ok=True)


def get_json_files() -> list[Path]:
    """回傳 C2_核心知識庫 所有 .json（依修改時間排序，最新的在最後追加）。"""
    files = sorted(KNOWLEDGE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    return files


def load_json_content(path: Path) -> str:
    """將 JSON 檔轉為純文字字串（含扁平化 key=value）。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return f"[PARSE_ERROR: {e}]"

    # 扁平化
    if isinstance(data, dict):
        parts = []
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool)):
                parts.append(f"{k}={v}")
            elif isinstance(v, (list, dict)):
                s = json.dumps(v, ensure_ascii=False, indent=1)
                if len(s) < 2000:
                    parts.append(f"{k}={s}")
            elif v is None:
                continue
        return "\n".join(parts)
    elif isinstance(data, list):
        return "\n".join(
            json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else str(item)
            for item in data
        )
    else:
        return str(data)


def main():
    parser = argparse.ArgumentParser(description="C2 知識庫 → ChromaDB")
    parser.add_argument("--dry-run", action="store_true", help="只看不寫")
    args = parser.parse_args()

    files = get_json_files()
    print(f"📂 找到 {len(files)} 個 JSON 檔")

    if not files:
        print("❌ 沒有 JSON 可消化")
        return

    # ── 載入 ChromaDB ──
    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # 使用預設 embedding（ONNX all-MiniLM-L6-v2，不需額外安裝）
    ef = embedding_functions.DefaultEmbeddingFunction()

    # 檢查是否已有資料
    existing = client.list_collections()
    existing_names = {c.name for c in existing}

    if COLLECTION_NAME in existing_names:
        col = client.get_collection(COLLECTION_NAME)
        print(f"📦 現有 collection '{COLLECTION_NAME}'，現有 {col.count()} 筆")
        if args.dry_run:
            print("🧪 --dry-run：跳過新增")
            return
    else:
        col = client.create_collection(COLLECTION_NAME, embedding_function=ef)
        print(f"🆕 建立 collection '{COLLECTION_NAME}'")

    # ── Ingest ──
    batch: list[dict] = []
    skipped = 0
    ingested = 0

    for fp in files:
        doc = load_json_content(fp)
        if not doc.strip():
            skipped += 1
            continue

        # 用檔名當 id（去重）
        doc_id = fp.stem  # 不含 .json

        # 避免重複寫入（idempotent）
        if args.dry_run:
            print(f"  [DRY] {doc_id} ({len(doc)} chars)")
            continue

        batch.append({
            "id": doc_id,
            "document": doc,
            "metadata": {
                "source": str(fp.relative_to(_TANG)),
                "mtime": str(fp.stat().st_mtime),
                "size_bytes": fp.stat().st_size,
            },
        })

        if len(batch) >= 10:
            col.upsert(
                ids=[b["id"] for b in batch],
                documents=[b["document"] for b in batch],
                metadatas=[b["metadata"] for b in batch],
            )
            ingested += len(batch)
            print(f"  ✅ batch {ingested}/{len(files)}")
            batch = []

    # 最後一批
    if batch and not args.dry_run:
        col.upsert(
            ids=[b["id"] for b in batch],
            documents=[b["document"] for b in batch],
            metadatas=[b["metadata"] for b in batch],
        )
        ingested += len(batch)
        print(f"  ✅ final batch {ingested}/{len(files)}")

    # ── 驗證 ──
    if args.dry_run:
        return

    total = col.count()
    print(f"\n{'='*50}")
    print(f"📊 ChromaDB 摘要")
    print(f"  collection: {COLLECTION_NAME}")
    print(f"  total docs: {total}")
    print(f"  persist_path: {CHROMA_DIR}")

    # 簡單查詢驗證
    test_queries = ["設計", "API", "schema", "模型"]
    for q in test_queries:
        res = col.query(query_texts=[q], n_results=2)
        hits = (res.get("ids") or [[]])[0]
        print(f"  🔍 query('{q}'): {len(hits)} hits → {hits[:2]}")

    print(f"\n✅ 完成！持久化路徑：{CHROMA_DIR}")


if __name__ == "__main__":
    main()
