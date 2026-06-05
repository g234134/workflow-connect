import requests
import json
import os

def run_simple_task():
    # 甇仿? 1: ??撟?AI 霈??獢???    files = os.listdir('/app')
    config_files = [f for f in files if 'config' in f]
    
    print(f"--- [?? 蝟餌絞?菜葫]: ?潛瑼? {config_files} ---")
    
    # 甇仿? 2: ??獢摰寡??箔?
    file_contents = {}
    for f in config_files:
        with open(f"/app/{f}", 'r') as content:
            file_contents[f] = content.read()

    # 甇仿? 3: ??????蝯?AI嚗?摰??敺???頛臬?瑯?    url = "http://host.docker.internal:11434/api/chat"
    payload = {
        "model": "qwen2.5-coder:7b",
        "messages": [
            {
                "role": "system", 
                "content": "雿銝??璆剔?蝟餌絞??撣怒??策雿???桀?瑼??批捆嚗?撟急?蝮賜????蔭??暺?
            },
            {
                "role": "user", 
                "content": f"?桅?銝??賊?瑼???{config_files}?摰孵?銝?{json.dumps(file_contents)}????鈭桅???
            }
        ],
        "stream": False
    }

    print("\n[?? AI 甇????豢?]...")
    resp = requests.post(url, json=payload).json()
    return resp['message']['content']

print("\n?? [蝯???RAG 蝪∪?? ??銝?..")
print(f"\nAI ???勗?: \n{run_simple_task()}")
