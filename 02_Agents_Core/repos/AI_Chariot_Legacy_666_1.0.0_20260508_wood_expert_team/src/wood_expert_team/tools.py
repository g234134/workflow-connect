import requests
import os
from crewai.tools import BaseTool

class ScraperAPITool(BaseTool):
    name: str = "scraper_api_tool"
    description: str = "當你需要深度抓取特定同行網頁內容時使用。輸入參數為 URL。"

    def _run(self, url: str) -> str:
        api_key = os.getenv("SCRAPERAPI_API_KEY")
        payload = {'api_key': api_key, 'url': url, 'render': 'true'}
        response = requests.get('http://api.scraperapi.com', params=payload)
        return response.text[:5000] # 截取前 5000 字防止顯存爆炸
