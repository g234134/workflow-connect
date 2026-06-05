import json
import requests
from pathlib import Path

def generate_site_structure(reference_url, goal="木地板品牌官網"):
    secret_path = Path(r'C:\AI_Project\secrets.json')
    with open(secret_path, 'r', encoding='utf-8-sig') as f:
        secrets = json.load(f)
    
    api_key = secrets.get('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    prompt = f"""
    你是前端開發專家。我要參考這個網址做一個木地板網站：{reference_url}
    目標：{goal}
    要求：
    1. 使用現代化的 HTML5 與 Tailwind CSS (CDN版，方便直接運行)。
    2. 樣式要大氣、溫潤，符合木地板質感。
    3. 包含：首頁大圖區、產品分類清單、關於我們、聯絡資訊。
    4. 暫時不需要真實圖片，請用佔位圖 (Placeholder)，但樣式細節(陰影、圓角、排版)要完整。
    請直接回傳完整的 HTML 檔案代碼。
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"❌ 雲端設計師罷工中: {str(e)}"

if __name__ == "__main__":
    # 這裡等造物主傳入網址
    print("等待網址輸入中...")
