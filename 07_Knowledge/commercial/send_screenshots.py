#!/usr/bin/env python3
"""一鍵發送截圖到 Telegram"""
import http.client, os

env = {}
with open("D:/Hermes/.env") as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

TOKEN = env.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = env.get("TELEGRAM_HOME_CHANNEL")
DIR = "D:/大唐三省六部/07_Knowledge/commercial"

def send_photo(filepath, caption=""):
    boundary = "----FormBoundary"
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_data = f.read()
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{CHAT_ID}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{filename}\"\r\n"
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    conn = http.client.HTTPSConnection("api.telegram.org", timeout=30)
    conn.request("POST", f"/bot{TOKEN}/sendPhoto", body=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "Content-Length": str(len(body))})
    resp = conn.getresponse()
    print(f"{'✅' if resp.status==200 else '❌'} {filename} → {resp.status}")

send_photo(f"{DIR}/preview_landing.png", "📄 Landing Page — 戰車數據清洗")
send_photo(f"{DIR}/preview_order_form.png", "📋 訂單表單 — 立即下單頁面")
