import os
from fastapi import FastAPI
from pydantic import BaseModel
from firecrawl import FirecrawlApp
import uvicorn

app_api = FastAPI()

# --- 1. 定義資料格式 ---
class Item(BaseModel):
    url: str
    api_key: str = "local_dev"

# 新增：定義存檔請求的格式
class SaveCodeRequest(BaseModel):
    filename: str
    code: str

# --- 2. 抓取功能 (讀取) ---
@app_api.post("/learn")
async def learn_endpoint(item: Item):
    print(f"🧠 接收到蒸餾請求: {item.url}")
    # 使用你的 Firecrawl API Key
    firecrawl = FirecrawlApp(api_key="fc-b181cfa456544b9a82014ad3cd560310") 

    try:
        print("🕷️ Firecrawl 正在抓取網頁中...")
        scrape_result = firecrawl.scrape_url(
            item.url, 
            params={'formats': ['markdown']}
        )
        markdown_content = scrape_result.get('markdown', '')
        
        if not markdown_content:
            return {"status": "error", "message": "抓取到了空內容"}

        print(f"✅ 抓取成功！長度: {len(markdown_content)}")
        return {"status": "success", "data": markdown_content}
    except Exception as e:
        print(f"❌ 抓取錯誤: {str(e)}")
        return {"status": "error", "message": str(e)}

# --- 3. 自動存檔功能 (寫入) ---
@app_api.post("/save_code")
async def save_code(request: SaveCodeRequest):
    # 鎖定存入你的木地板專案 Library 資料夾
    base_path = r"C:\Users\666LAG\Desktop\AI_Project\Library"
    
    # 如果資料夾不存在就建立它
    if not os.path.exists(base_path):
        os.makedirs(base_path)
        
    full_path = os.path.join(base_path, request.filename)
    
    try:
        print(f"💾 正在嘗試存檔至: {full_path}")
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(request.code)
        print(f"✨ 存檔成功！")
        return {"status": "success", "message": f"Successfully saved to {full_path}"}
    except Exception as e:
        print(f"❌ 存檔失敗: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # 保持在 8000 端口，讓 ngrok 可以穿透
    uvicorn.run(app_api, host="0.0.0.0", port=8000)