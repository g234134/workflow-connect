import os
import json
from crewai import Agent, Task, Crew

# 1. 定義文案生產機器人
copywriter = Agent(
    role='木地板文案專家',
    goal='產出高品質、具備 SEO 優勢的木地板產品描述',
    backstory='你是一個專業的文案生成器。你只輸出 JSON 格式的數據，不寫任何廢話。',
    llm="ollama/qwen2.5-coder:3b"
)

# 2. 定義任務：產出結構化資料
task = Task(
    description='''
    1. 參考 C:\dev\agency-agents\DESIGN.md 的風格。
    2. 針對「超耐磨胡桃木地板」編寫三種風格的文案：專業感、居家感、奢華感。
    3. 必須以 JSON 格式輸出，包含標題(title)、內容(content) 和 標籤(tags)。
    ''',
    expected_output='純 JSON 格式的文案數據。',
    agent=copywriter
)

# 3. 執行
factory = Crew(agents=[copywriter], tasks=[task])
result = str(factory.kickoff())

# 4. 存成 Dify 喜歡的格式
try:
    # 提取 JSON 部分
    start = result.find('{')
    end = result.rfind('}') + 1
    json_data = result[start:end]
    
    output_path = r"C:\dev\agency-agents\dify_input.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_data)
    
    print("\n" + "="*50)
    print(f"🚀 文案生產完成！已存入：{output_path}")
    print("📢 你現在可以直接把這個 JSON 餵給 Dify 的 HTTP Request 節點。")
    print("="*50)
    
    # 順便印出來給你看
    print(json_data)
except Exception as e:
    print(f"❌ 解析失敗，Agent 噴了垃圾話：{e}")