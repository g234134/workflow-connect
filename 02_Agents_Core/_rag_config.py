"""
_rag_config.py — 戰車數據清洗專案的 Rag 統一設定。

用法（在 crew 宣告前呼叫）：
    from _rag_config import get_chroma_collection, get_default_chroma_client

    client = get_default_chroma_client()
    col = get_chroma_collection("knowledge_base")   # ← 已載入 C2_核心知識庫
"""
from __future__ import annotations

import os
from pathlib import Path

import chromadb
from chromadb import Collection
from chromadb.utils import embedding_functions

_TANG_ROOT = Path(__file__).resolve().parent.parent  # 大唐三省六部
CHROMA_DIR = _TANG_ROOT / "03_RAG_Database" / "vector_stores" / "chroma_db"
os.makedirs(str(CHROMA_DIR), exist_ok=True)


def get_default_chroma_client() -> chromadb.PersistentClient:
    """回傳 PersistentClient，指向專案內 vector_stores/chroma_db。"""
    return chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=chromadb.config.Settings(
            anonymized_telemetry=False,
            allow_reset=False,
        ),
    )


def get_chroma_collection(
    name: str = "knowledge_base",
    client: chromadb.PersistentClient | None = None,
) -> Collection:
    """取得（或建立）指定名稱的 collection，使用本機 ONNX embedding。"""
    c = client or get_default_chroma_client()
    ef = embedding_functions.DefaultEmbeddingFunction()  # ONNX all-MiniLM-L6-v2
    return c.get_or_create_collection(
        name=name,
        embedding_function=ef,
    )


def build_crew_rag_config() -> dict:
    """回傳可餵入 Crew(embedder=...) 的 embedder dict。

    讓 Crew 的 knowledge_sources 使用本機 persistence + ONNX embedding。
    """
    return {
        "provider": "chromadb",
        "config": {
            "persist_directory": str(CHROMA_DIR),
            "allow_reset": True,
            "anonymized_telemetry": False,
        },
        "embeddings": {
            "provider": "openai",   # CrewAI 內部 mapping，非真正 call OpenAI
            "model": "text-embedding-3-small",
        },
    }
