"""
本機 RAG 入庫：只讀取 D:\\rag檔案庫（或 .env 的 RAG_ROOT）底下的檔案。
不對外爬網、不自動下載網頁。

支援副檔名：.pdf .txt .md .markdown .html .htm
嵌入模型：本機 Ollama（預設 nomic-embed-text），向量庫：Chroma（持久化在目錄）。
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

import httpx
from dotenv import load_dotenv

try:
    import chromadb
except ImportError as exc:
    raise SystemExit("請先安裝：pip install chromadb") from exc


load_dotenv()

RAG_ROOT = Path(os.environ.get("RAG_ROOT", r"D:\rag檔案庫")).resolve()
CHROMA_DIR = Path(
    os.environ.get("CHROMA_PERSIST_DIR", str(RAG_ROOT / ".chroma_index"))
).resolve()
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHUNK_SIZE = int(os.environ.get("RAG_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", "120"))
COLLECTION_NAME = os.environ.get("RAG_COLLECTION", "rag_local")


class _StripHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.buf: list[str] = []

    def handle_data(self, data: str) -> None:
        self.buf.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.buf)).strip()


def _read_pdf(path: Path) -> str:
    try:
        import pdfplumber  # type: ignore

        parts: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
        return "\n".join(parts)
    except Exception:
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as exc:
            raise RuntimeError(f"無法讀取 PDF：{path.name}（{exc})") from exc


def _read_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    p = _StripHTML()
    p.feed(raw)
    return p.text()


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_text(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".pdf":
        return _read_pdf(path)
    if suf in {".html", ".htm"}:
        return _read_html(path)
    if suf in {".txt", ".md", ".markdown"}:
        return _read_text_file(path)
    return ""


def _chunk(text: str, size: int, overlap: int) -> Iterable[str]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return
    step = max(size - overlap, 1)
    for i in range(0, len(text), step):
        yield text[i : i + size]


def _embed_one(client: httpx.Client, text: str) -> list[float]:
    r = client.post(
        f"{OLLAMA_BASE}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=120.0,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"嵌入失敗 HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    emb = data.get("embedding")
    if not emb:
        raise RuntimeError("嵌入回應缺少 embedding")
    return emb


def _collect_files(root: Path) -> list[Path]:
    exts = {".pdf", ".txt", ".md", ".markdown", ".html", ".htm"}
    out: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            # 跳過索引目錄本身
            if ".chroma" in p.parts or ".chroma_index" in p.parts:
                continue
            out.append(p)
    return sorted(out)


def main() -> None:
    if not RAG_ROOT.is_dir():
        sys.exit(f"[錯誤] RAG_ROOT 不存在：{RAG_ROOT}")

    files = _collect_files(RAG_ROOT)
    if not files:
        print(f"[警告] {RAG_ROOT} 底下尚未找到可索引檔（pdf/txt/md/html）。")
        return

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client_db = chromadb.PersistentClient(path=str(CHROMA_DIR))
    coll = client_db.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "local files under RAG_ROOT"},
    )

    # 清空後重建（簡化版；若要增量索引可再改）
    try:
        client_db.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    coll = client_db.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "local files under RAG_ROOT"},
    )

    http = httpx.Client()

    total_chunks = 0
    for fp in files:
        try:
            body = _extract_text(fp)
        except Exception as exc:
            print(f"[跳過] {fp}: {exc}")
            continue
        if not body.strip():
            print(f"[跳過] 空白內容：{fp}")
            continue
        rel = str(fp.relative_to(RAG_ROOT))
        for idx, chunk in enumerate(_chunk(body, CHUNK_SIZE, CHUNK_OVERLAP)):
            cid = hashlib.sha256(f"{rel}:{idx}:{chunk[:80]}".encode("utf-8")).hexdigest()
            vec = _embed_one(http, chunk)
            coll.add(
                ids=[cid],
                embeddings=[vec],
                documents=[chunk],
                metadatas=[{"path": rel, "file": fp.name}],
            )
            total_chunks += 1
            if total_chunks % 20 == 0:
                print(f"[INFO] 已索引 chunk 數：{total_chunks}")

    http.close()
    print(f"[OK] 完成。檔案數：{len(files)}，chunk 數：{total_chunks}")
    print(f"[OK] 向量庫目錄：{CHROMA_DIR}")


if __name__ == "__main__":
    main()
