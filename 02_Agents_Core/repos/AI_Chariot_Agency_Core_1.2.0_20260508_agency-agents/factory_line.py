import os
from crewai import Agent, Task, Crew

# 1. ?瑁摰儔嚗?亦策撌亙?璅?銝神撱Ｚ店??嚗?coder = Agent(
    role='HTML_Generator',
    goal='?Ｗ蝝?HTML 蝯?瑼?,
    backstory='雿銝?誨蝣潭??其犖嚗鞎痊頛詨 HTML??, # ?閬神嚗???摰?誘
    llm="ollama/qwen2.5-coder:3b",
    allow_delegation=False
)

stylist = Agent(
    role='CSS_Styler',
    goal='?交 HTML 銝行釣??CSS 璅??',
    backstory='雿?鞎祆??嗅??HTML ??蝢???CSS 璅????,
    llm="ollama/qwen2.5-coder:3b",
    allow_delegation=False
)

# 2. 隞餃?瘚偌蝺?A ???梯正蝯?B
task1 = Task(
    description='?寞? C:\dev\agency-agents\DESIGN.md 撖怠 HTML??閬神隞颱?閫??????,
    expected_output='銝畾萇? HTML 隞?Ⅳ??,
    agent=coder
)

task2 = Task(
    description='??task1 ?Ｗ??HTML嚗 <style> 璅惜?批??亦隞?? CSS嚗敶晞?閫鞈芷??莎???,
    expected_output='摰??HTML+CSS ?游?隞?Ⅳ??,
    agent=stylist,
    context=[task1] # 撘瑕?鞈??瘝??task1 ?镼選?task2 銝??)

# 3. ???蝺?factory = Crew(
    agents=[coder, stylist],
    tasks=[task1, task2],
    verbose=True # ??????隞?祇?鞈?
)

print("\n--- [?蝺???甇??極蝬脤?...] ---")
result = str(factory.kickoff())

# 4. 撌亙??箄疏嚗祕擃神瑼?with open(r"C:\dev\agency-agents\index.html", "w", encoding="utf-8") as f:
    f.write(result.replace('`html', '').replace('`', '').strip())

os.startfile(r"C:\dev\agency-agents\index.html")
