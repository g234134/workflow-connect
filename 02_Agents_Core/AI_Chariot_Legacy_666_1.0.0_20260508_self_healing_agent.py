import requests
import json
import subprocess
import sys

def call_ollama(model, prompt):
    url = "http://host.docker.internal:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    return requests.post(url, json=payload).json()['response']

# ??隞餃?
task = "隢鼠?蝙??pandas 撱箇?銝????'Name' ??'Score' ??Excel 瑼?? test.xlsx????鋆?pandas ??openpyxl嚗???鋆?
history = "" # ?其?蝝?隤歹?霈?Coder 摮貊?

for attempt in range(3): # 蝯?AI 銝活靽格迤璈?
    print(f"\n?? [?岫蝚?{attempt+1} 甈（...")
    
    coder_prompt = f"隞餃?嚗task}\n??仃???航炊閮嚗history}\n隢神?箔耨甇??????Python 隞?Ⅳ?閬誨蝣潘?銝?閫????
    code = call_ollama("qwen2.5-coder:7b", coder_prompt).strip("`").replace("python", "")
    
    print("?? [?瑁?銝苗...")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("??[??]嚗遙?歇??嚗?)
        print(f"頛詨嚗result.stdout}")
        break
    else:
        print(f"??[憭望?]嚗皜砍?航炊嚗迤?典??喟策憭扯...")
        # 撠隤方??舫今?策銝?甈∠? Prompt
        history = f"隞?Ⅳ嚗n{code}\n?航炊閮嚗n{result.stderr}"
        if attempt == 2:
            print("?? [?蝯仃?嚗I 撌脩??隢炎?仿?頛胯?)

# 皜???憟辣 (憒?銝?閬?閰?
# subprocess.run(["pip", "uninstall", "-y", "pandas", "openpyxl"])
