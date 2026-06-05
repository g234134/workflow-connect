import os
import json
from crewai import Agent, Task, Crew

target_path = r"C:\dev\agency-agents"
design_file = os.path.join(target_path, "data", "DESIGN.md")
output_file = os.path.join(target_path, "web", "index.html")

# (其餘代碼內容...)
