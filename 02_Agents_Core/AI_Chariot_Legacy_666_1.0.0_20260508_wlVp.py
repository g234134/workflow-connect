from fastapi import FastAPI, HTTPException
import uvicorn
import dify_api  # 這裡正式引入你的業務邏輯檔案

app = FastAPI(title="666lag 專業木地板 Agent")

@app.get("/")
def health_check():
    return {
        "status": "online",
        "owner": "666lag",
        "hardware": "RTX 2060 Ready",
        "port": 8001,
        "msg": "Agent 基地已就緒，8001 端口暢通！"
    }

# Dify 工具調用時通常會打這個 POST 接口
@app.post("/chat")
async def chat_with_agent(data: dict):
    """
    接收 Dify 的指令並調用生圖邏輯
    """
    try:
        # 假設你的 dify_api 裡面有一個處理生圖的函式叫 process_request
        # 如果你的函式名稱不同，請自行修改
        result = dify_api.process_request(data) 
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 啟動 666lag 專業 Agent 伺服器...")
    print("📡 正在監聽端口: 8001")
    # 將 port 改為 8001，host 改為 0.0.0.0 方便 ngrok 穿透
    uvicorn.run(app, host="0.0.0.0", port=8001)