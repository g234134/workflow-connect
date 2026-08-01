"""
在本機 Chroma 向量庫做相似度檢索（僅查已入庫資料）。
用法：python rag_search_local.py "你的問題"
"""

from __future__ import annotations

import os
import sys

import httpx
from dotenv import load_dotenv

try:
    import chromadb
except ImportError as exc:
    raise SystemExit("請先安裝：pip install chromadb") from exc

load_dotenv()

RAG_ROOT = os.environ.get("RAG_ROOT", r"D:\rag檔案庫")
CHROMA_DIR = os.environ.get(
    "CHROMA_PERSIST_DIR", str(os.path.join(RAG_ROOT, ".chroma_index"))
)
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
COLLECTION_NAME = os.environ.get("RAG_COLLECTION", "rag_local")


def embed_query(q: str) -> list[float]:
    r = httpx.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": q},
        timeout=120.0,
    )
    r.raise_for_status()
    emb = r.json().get("embedding")
    if not emb:
        raise RuntimeError("嵌入回應缺少 embedding")
    return emb


def main() -> None:
    q = " ".join(sys.argv[1:]).strip()
    if not q:
        print('用法：python rag_search_local.py "關鍵問題"')
        sys.exit(1)

    client_db = chromadb.PersistentClient(path=CHROMA_DIR)
    coll = client_db.get_collection(name=COLLECTION_NAME)
    vec = embed_query(q)
    res = coll.query(query_embeddings=[vec], n_results=int(os.environ.get("RAG_TOP_K", "5")))

    docs = res.get("documents") or [[]]
    metas = res.get("metadatas") or [[]]
    dists = res.get("distances") or [[]]

    print("--- 檢索結果（僅供參考，請自行判讀）---\n")
    for i, doc in enumerate(docs[0]):
        meta = metas[0][i] if metas and metas[0] else {}
        dist = dists[0][i] if dists and dists[0] else None
        label = f"[{i+1}] {meta.get('path','?')}  distance={dist}"
        print(label)
        print(doc[:1200])
        print()


if __name__ == "__main__":
    main()
