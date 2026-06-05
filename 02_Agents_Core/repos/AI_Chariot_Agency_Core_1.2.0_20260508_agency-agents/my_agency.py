import os
from crewai import Agent, Task, Crew

# 1. 確保工作目錄存在
target_dir = r"C:\dev\agency-agents"
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# 2. 定義 Agent
writer_agent = Agent(
    role='在地化網頁設計師',
    goal='設計一個專業且在地化的木地板公司網站',
    backstory='你是一位精通 HTML/CSS 的設計師，現在要撰寫一份適合台灣市場的專業木地板公司 HTML 頁面。',
    llm="ollama/qwen2.5-coder:3b",
    verbose=True
)

# 3. 定義任務
task = Task(
    description='請幫我產出一個簡潔的在地化網頁 HTML 程式碼。標題為「64GB 磁磚木地板專家：頂級在地化服務」。',
    expected_output='純 HTML 程式碼內容',
    agent=writer_agent
)

crew = Crew(agents=[writer_agent], tasks=[task])
result = crew.kickoff()
print(result)

# --- 以下為自動補上的存檔邏輯 ---
import json

# 將 Agent 的結果轉換為字串並存入 JSON
output_data = {
    "title": "64GB 磁磚木地板專家",
    "content": str(result)
}

# 寫入專案目錄下的 dify_input.json
target_file = r"C:\dev\agency-agents\dify_input.json"
with open(target_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print(f"\n--- 任務完成！內容已存入: {target_file} ---")
