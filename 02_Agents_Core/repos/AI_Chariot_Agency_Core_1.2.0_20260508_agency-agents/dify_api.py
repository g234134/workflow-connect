from fastapi import FastAPI
import json
import os
import uvicorn

app = FastAPI()

@app.get("/get_copywriting")
def get_copywriting():
    path = r"C:\dev\agency-agents\dify_input.json"
    if os.path.exists(path):
        try:
            # 使用 utf-8-sig 會自動處理有無 BOM 的情況
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"讀取 JSON 失敗: {str(e)}"}
    return {"error": "找不到指定路徑的 JSON 檔案"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
