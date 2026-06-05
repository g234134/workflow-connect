# -*- coding: utf-8 -*-
import os
import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

app = FastAPI()

class SmartRouter:
    def __init__(self):
        self.nvidia_key = os.getenv("NVIDIA_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        print(f"[SmartRouter] 系統初始化完成")
        print(f" - NVIDIA Key: {'已載入' if self.nvidia_key else '缺失'}")
        print(f" - Groq Key: {'已載入' if self.groq_key else '缺失'}")

    async def route_request(self, payload):
        messages = payload.get("messages", [])
        # 優先呼叫 NVIDIA
        print("[SmartRouter] 正在呼叫 NVIDIA NIM...")
        response = await self.call_nvidia(messages)
        
        # 如果失敗則切換到 Groq
        if "error" in response:
            print(f"[SmartRouter] NVIDIA 失敗，切換至 Groq...")
            response = await self.call_groq(messages)
        return response

    async def call_nvidia(self, messages):
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.nvidia_key}", "Content-Type": "application/json"}
        data = {"model": "meta/llama-3.1-8b-instruct", "messages": messages, "temperature": 0.5}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=data, timeout=30.0)
                return resp.json() if resp.status_code == 200 else {"error": "NVIDIA_FAIL"}
            except: return {"error": "NVIDIA_CONN_FAIL"}

    async def call_groq(self, messages):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        data = {"model": "llama-3.1-8b-instant", "messages": messages}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=data, timeout=30.0)
                return resp.json() if resp.status_code == 200 else {"error": "GROQ_FAIL"}
            except: return {"error": "GROQ_CONN_FAIL"}

router = SmartRouter()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    payload = await request.json()
    response = await router.route_request(payload)
    return JSONResponse(content=response)

# --- 這是讓程式跑起來的關鍵 ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)