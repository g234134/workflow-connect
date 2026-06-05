import requests
import os
from crewai.tools import BaseTool
from pydantic import Field

class ScraperAPITool(BaseTool):
    name: str = "scraper_api_tool"
    description: str = "當你需要深度抓取特定同行網頁內容時使用。輸入參數為 URL。"

    def _run(self, url: str) -> str:
        api_key = os.getenv("SCRAPERAPI_API_KEY")
        if not api_key:
            return "錯誤：找不到 SCRAPERAPI_API_KEY 環境變數"
        
        payload = {'api_key': api_key, 'url': url, 'render': 'true'}
        try:
            response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
            return response.text[:5000]
        except Exception as e:
            return f"抓取失敗：{str(e)}"
