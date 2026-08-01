"""
_smoke_rag.py — 簡短煙霧測試：確認 ChromaDB persistence + 查得回 result。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 加入專案路徑
_AGENTS_CORE = Path(__file__).resolve().parent
sys.path.insert(0, str(_AGENTS_CORE))

from _rag_config import get_default_chroma_client, get_chroma_collection

# ── 1. 檢查 collection ──
client = get_default_chroma_client()
cols = client.list_collections()
print(f"📦 Collections ({len(cols)}):")
for c in cols:
    print(f"   · {c.name}: {c.count()} docs")

# ── 2. 查詢知識庫 ──
col = get_chroma_collection("knowledge_base", client=client)
count = col.count()
print(f"\n📊 knowledge_base total docs: {count}")

if count == 0:
    print("❌ 空 collection — 需要先跑 _ingest_knowledge_to_chroma.py")
    sys.exit(1)

# ── 3. 多種查詢 ──
TEST_QUERIES = [
    "什麼是戰車數據清洗",
    "API 設計文件",
    "schema 定義",
    "embedding model",
    "python 套件依賴",
]

print(f"\n🔍 查詢測試（{len(TEST_QUERIES)} 組）")
print("=" * 60)

for q in TEST_QUERIES:
    res = col.query(query_texts=[q], n_results=3)
    ids = (res.get("ids") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]

    print(f"\n▶ 查詢: 「{q}」")
    for i, (doc_id, dist) in enumerate(zip(ids, dists)):
        snippet = (docs[i][:120] + "…") if len(docs[i]) > 120 else docs[i]
        print(f"  [{i+1}] {doc_id}  (dist={dist:.4f})")
        print(f"       {snippet}")

print(f"\n{'='*60}")
print("✅ RAG 煙霧測試完成")
print(f"   持久化路徑: {client._system.settings.persist_directory}")
