from fastapi import FastAPI
import uvicorn
# 確保你之前 ls 看到的 dify_api.py 也在同一個資料夾
# import dify_api 

app = FastAPI(title="666lag 專業木地板 Agent")

@app.get("/")
def health_check():
    """讓你知道 Agent 活著的檢查點"""
    return {
        "status": "online",
        "owner": "666lag",
        "hardware": "RTX 2060 Ready",
        "msg": "Agent 基地已就緒，隨時待命！"
    }

# 這裡是未來對接 Dify 的地方
@app.post("/chat")
async def chat_with_agent(data: dict):
    # 你可以在這裡呼叫你的 dify_api 邏輯
    return {"reply": "收到指令，正在準備處理..."}

if __name__ == "__main__":
    print("🚀 啟動 666lag Agent 伺服器...")
    # 執行後，視窗會停住，這才是正確的
    uvicorn.run(app, host="127.0.0.1", port=8000)