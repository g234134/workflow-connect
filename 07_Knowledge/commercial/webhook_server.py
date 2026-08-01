#!/usr/bin/env python3
"""
戰車數據清洗 — 收單 Webhook Endpoint
輕量 FastAPI 服務，接收訂單表單 + 檔案上傳，寫入本地佇列。

啟動方式:
  python webhook_server.py
  # 或指定 port: python webhook_server.py --port 9000

API:
  POST /api/order          — 接收訂單（multipart form）
  GET  /api/health         — 健康檢查
  GET  /api/orders         — 列出最近訂單
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# ── 配置 ──
BASE_DIR = Path(__file__).resolve().parent
ORDERS_DIR = BASE_DIR / "orders"
UPLOAD_DIR = BASE_DIR / "uploads"
QUEUE_FILE = BASE_DIR / "order_queue.jsonl"

for d in (ORDERS_DIR, UPLOAD_DIR):
    d.mkdir(exist_ok=True)


def create_app():
    """建立 FastAPI app（延遲 import，避免未安裝时报錯清晰）"""
    try:
        from fastapi import FastAPI, UploadFile, File, Form, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
    except ImportError:
        print("❌ 需要安裝 FastAPI: pip install fastapi uvicorn python-multipart")
        sys.exit(1)

    app = FastAPI(title="戰車數據清洗 — 收單 API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health():
        return {"status": "online", "service": "tank-data-cleansing", "ts": datetime.now().isoformat()}

    @app.post("/api/order")
    async def create_order(
        name: str = Form(...),
        email: str = Form(...),
        phone: str = Form(""),
        plan: str = Form(...),
        notes: str = Form(""),
        file: UploadFile = File(...),
    ):
        # 驗證方案
        if plan not in ("basic", "pro", "enterprise"):
            raise HTTPException(400, "plan 必須是 basic / pro / enterprise")

        # 生成訂單 ID
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        ts = datetime.now().isoformat()

        # 儲存上傳檔案
        ext = Path(file.filename).suffix if file.filename else ".xlsx"
        save_path = UPLOAD_DIR / f"{order_id}{ext}"
        content = await file.read()
        save_path.write_bytes(content)

        # 訂單紀錄
        order = {
            "order_id": order_id,
            "name": name,
            "email": email,
            "phone": phone,
            "plan": plan,
            "notes": notes,
            "filename": file.filename,
            "filepath": str(save_path),
            "file_size": len(content),
            "status": "received",
            "created_at": ts,
        }

        # 寫入 JSONL 佇列
        with open(QUEUE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(order, ensure_ascii=False) + "\n")

        # 寫入獨立訂單檔
        order_file = ORDERS_DIR / f"{order_id}.json"
        order_file.write_text(json.dumps(order, ensure_ascii=False, indent=2), encoding="utf-8")

        return JSONResponse({
            "success": True,
            "order_id": order_id,
            "message": f"訂單已收到，預計 {('24小時' if plan == 'basic' else '12小時' if plan == 'pro' else '依約定')} 內交付",
        })

    @app.get("/api/orders")
    def list_orders():
        orders = []
        for f in sorted(ORDERS_DIR.glob("*.json"), reverse=True)[:20]:
            try:
                orders.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
        return {"orders": orders, "count": len(orders)}

    return app


def main():
    parser = argparse.ArgumentParser(description="戰車數據清洗收單 API")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    app = create_app()

    try:
        import uvicorn
        print(f"🚀 戰車收單 API 啟動: http://{args.host}:{args.port}")
        print(f"📋 API docs: http://127.0.0.1:{args.port}/docs")
        uvicorn.run(app, host=args.host, port=args.port)
    except ImportError:
        print("❌ 需要安裝 uvicorn: pip install uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()
