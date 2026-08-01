#!/usr/bin/env python3
"""
戰車數據清洗 — Telegram 收單機器人
接收客戶檔案，建立訂單，通知營運方。

用法:
  python telegram_order_bot.py          # 啟動 long-polling bot
  python telegram_order_bot.py --test   # 測試模式（僅列出手機器人資訊）
"""

import json
import os
import sys
import time
import urllib.request
import ssl
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ORDERS_DIR = BASE_DIR / "orders"
UPLOAD_DIR = BASE_DIR / "uploads"
QUEUE_FILE = BASE_DIR / "order_queue.jsonl"

for d in (ORDERS_DIR, UPLOAD_DIR):
    d.mkdir(exist_ok=True)

# 讀取 .env
env = {}
env_path = Path("D:/Hermes/.env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = env.get("TELEGRAM_HOME_CHANNEL", "")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

ssl_ctx = ssl.create_default_context()


def send_message(chat_id, text, parse_mode="Markdown"):
    """發送文字訊息"""
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }).encode()
    req = urllib.request.Request(
        f"{API_BASE}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
        return json.loads(resp.read())


def download_file(file_id, save_path):
    """下載 Telegram 檔案"""
    # 取得檔案路徑
    payload = json.dumps({"file_id": file_id}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/getFile",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
        info = json.loads(resp.read())
    
    if not info.get("ok"):
        return None
    
    file_path = info["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    
    # 下載檔案
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
        data = resp.read()
    
    with open(save_path, "wb") as f:
        f.write(data)
    
    return save_path


def create_order(name, email, plan, filename, filepath, file_size, notes=""):
    """建立訂單"""
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{os.urandom(3).hex().upper()}"
    ts = datetime.now().isoformat()
    
    order = {
        "order_id": order_id,
        "name": name,
        "email": email,
        "plan": plan,
        "notes": notes,
        "filename": filename,
        "filepath": filepath,
        "file_size": file_size,
        "status": "received",
        "created_at": ts,
    }
    
    # 寫入 JSONL 佇列
    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(order, ensure_ascii=False) + "\n")
    
    # 寫入獨立訂單檔
    order_file = ORDERS_DIR / f"{order_id}.json"
    order_file.write_text(json.dumps(order, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return order_id


def handle_message(msg):
    """處理收到的訊息"""
    chat_id = msg["chat"]["id"]
    user = msg.get("from", {})
    text = msg.get("text", "")
    document = msg.get("document")
    
    # 指令處理
    if text == "/start":
        send_message(chat_id, 
            "/welcome to 戰車數據清洗！\n\n"
            "📊 *服務項目*\n"
            "• 數據清洗（去重、補值、格式修正）\n"
            "• Excel/CSV 格式標準化\n"
            "• 資料合併與整理\n\n"
            "💰 *定價方案*\n"
            "• 基礎版 $999（5,000筆內）\n"
            "• 專業版 $2,999（50,000筆內）\n"
            "• 企業版 客製報價\n\n"
            "📝 *如何下單*\n"
            "直接傳送您的 Excel/CSV 檔案給我，\n"
            "我會自動建立訂單並開始處理！\n\n"
            "❓ 輸入 /help 查看更多資訊"
        )
        return "OK"
    
    if text == "/help":
        send_message(chat_id,
            "📖 *使用說明*\n\n"
            "1️⃣ 傳送 Excel/CSV 檔案\n"
            "2️⃣ 我會自動建立訂單\n"
            "3️⃣ 等待清洗完成（24hr 內）\n"
            "4️⃣ 收回乾淨的檔案 + 報告\n\n"
            "💡 *提示*\n"
            "• 輸入方案名稱可指定：`基礎版` / `專業版` / `企業版`\n"
            "• 預設使用基礎版\n"
            "• 輸入 /status 查詢訂單狀態"
        )
        return "OK"
    
    if text == "/status":
        # 查詢最近訂單
        orders = sorted(ORDERS_DIR.glob("*.json"), reverse=True)[:5]
        if not orders:
            send_message(chat_id, "📭 目前沒有訂單紀錄")
            return "OK"
        
        msg_lines = ["📋 *最近訂單*\n"]
        for f in orders:
            o = json.loads(f.read_text(encoding="utf-8"))
            status_icon = {"received": "📥", "processing": "🔄", "completed": "✅"}.get(o.get("status"), "❓")
            msg_lines.append(f"{status_icon} `{o.get('order_id')}` — {o.get('status')}")
        
        send_message(chat_id, "\n".join(msg_lines))
        return "OK"
    
    # 處理檔案上傳
    if document:
        file_id = document["file_id"]
        filename = document.get("file_name", "unknown")
        
        # 檢查檔案類型
        ext = Path(filename).suffix.lower()
        if ext not in (".xlsx", ".xls", ".csv"):
            send_message(chat_id, f"❌ 不支援的檔案格式：{ext}\n\n請上傳 Excel (.xlsx/.xls) 或 CSV (.csv) 檔案。")
            return "ERROR"
        
        # 檢查檔案大小（限制 50MB）
        file_size = document.get("file_size", 0)
        if file_size > 50 * 1024 * 1024:
            send_message(chat_id, "❌ 檔案太大（超過 50MB）\n\n請壓縮後再上傳，或聯繫我們處理大檔案。")
            return "ERROR"
        
        # 下載檔案
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{os.urandom(3).hex().upper()}"
        save_path = UPLOAD_DIR / f"{order_id}{ext}"
        
        try:
            download_file(file_id, str(save_path))
        except Exception as e:
            send_message(chat_id, f"❌ 檔案下載失敗：{e}")
            return "ERROR"
        
        # 建立訂單（預設基礎版）
        plan = "basic"
        name = user.get("first_name", "Telegram 用戶")
        
        order_id = create_order(
            name=name,
            email="",
            plan=plan,
            filename=filename,
            filepath=str(save_path),
            file_size=file_size,
        )
        
        # 通知用戶
        send_message(chat_id,
            f"✅ *訂單已建立*\n\n"
            f"📋 訂單編號：`{order_id}`\n"
            f"📄 檔案：{filename}\n"
            f"💰 方案：基礎版 $999\n"
            f"⏱️ 預計交付：24 小時內\n\n"
            f"📝 如需升級方案，請輸入：\n"
            f"• `專業版` — $2,999（12hr 交付）\n"
            f"• `企業版` — 客製報價"
        )
        
        # 通知營運方
        send_message(CHAT_ID,
            f"🔔 *新訂單通知*\n\n"
            f"📋 `{order_id}`\n"
            f"👤 {name}\n"
            f"📄 {filename} ({file_size:,} bytes)\n"
            f"💰 基礎版 $999"
        )
        
        return "OK"
    
    # 方案升級
    if "專業版" in text:
        send_message(chat_id, "📝 請先上傳檔案，我們會為您建立專業版訂單。")
        return "OK"
    
    if "企業版" in text:
        send_message(chat_id, "📝 企業版請聯繫：contact@tankdataclean.com\n\n我們會有專人與您洽談客製方案。")
        return "OK"
    
    # 未知指令
    send_message(chat_id, "❓ 我不太確定您的意思。\n\n請輸入 /start 查看使用說明，或直接傳送檔案開始下單！")
    return "OK"


def main():
    if not BOT_TOKEN:
        print("❌ 找不到 TELEGRAM_BOT_TOKEN")
        print("請在 D:/Hermes/.env 中設定")
        sys.exit(1)
    
    test_mode = "--test" in sys.argv
    if test_mode:
        print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
        print(f"📢 通知頻道: {CHAT_ID}")
        
        # 測試發送
        try:
            send_message(CHAT_ID, "🤖 戰車數據清洗機器人已上線！\n\n用法：直接傳送 Excel/CSV 檔案開始下單。")
            print("✅ 測試訊息已發送")
        except Exception as e:
            print(f"❌ 發送失敗: {e}")
        return
    
    # 啟動 long-polling
    print("🤖 戰車數據清洗機器人啟動中...")
    print("📡 等待客戶訊息...\n")
    
    offset = 0
    while True:
        try:
            # Long polling
            url = f"{API_BASE}/getUpdates?offset={offset}&timeout=30"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=35, context=ssl_ctx) as resp:
                data = json.loads(resp.read())
            
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if msg:
                        result = handle_message(msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg['chat']['id']}: {result}")
        
        except KeyboardInterrupt:
            print("\n🛑 機器人已停止")
            break
        except Exception as e:
            print(f"⚠️ 錯誤: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
