import os
import requests
import chromadb
from crewai import Agent, Task, Crew
from crewai.tools import tool

# --- 1. 連線診斷工具箱 ---

@tool("check_chromadb_connection")
def check_chromadb_connection(query: str):
    """檢查 Docker 裡的 ChromaDB 是否正常連線。"""
    try:
        # 預設 Docker ChromaDB 連接埠通常是 8000
        client = chromadb.HttpClient(host='localhost', port=8000)
        collections = client.list_collections()
        return f"【成功】ChromaDB 已連線！目前有 {len(collections)} 個知識庫。"
    except Exception as e:
        return f"【失敗】無法連上 ChromaDB。請確認 Docker 容器是否啟動。錯誤: {e}"

@tool("check_design_file")
def check_design_file(query: str):
    """檢查指定目錄下是否有 DESIGN.md 檔案。"""
    path = r"C:\dev\agency-agents\DESIGN.md"
    if os.path.exists(path):
        return f"【成功】偵測到 DESIGN.md！檔案大小: {os.path.getsize(path)} bytes。"
    return "【警告】未在目錄下找到 DESIGN.md。請確認 Claude 的檔案已導出至此。"

# --- 2. 定義「連線稽核員」 ---
auditor = Agent(
  role='系統連線稽核員',
  goal='確認 RAG 資料庫、檔案連線與 API 通訊是否全部跑通',
  backstory='你是這個 64GB 算力中心的通訊官，負責確保各個 AI 模組之間沒有斷線。',
  tools=[check_chromadb_connection, check_design_file],
  llm="ollama/qwen2.5-coder:3b",
  verbose=True
)

# --- 3. 診斷任務 ---
task = Task(
  description='''
  請執行以下診斷：
  1. 嘗試連線到 Docker 裡的 ChromaDB。
  2. 搜尋 C:\dev\agency-agents 是否有 DESIGN.md。
  3. 評估目前是否具備「連接別人 AI 網站」的條件。
  ''',
  expected_output='一份完整的連線狀態診斷報告。',
  agent=auditor
)

crew = Crew(agents=[auditor], tasks=[task])
print("\n--- [正在發起全系統診斷...] ---")
result = crew.kickoff()
print("\n" + "="*50)
print(result)