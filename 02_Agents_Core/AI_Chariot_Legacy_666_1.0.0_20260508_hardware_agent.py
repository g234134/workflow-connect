import requests
import json

def get_local_config(device_name):
    print(f"\n[? 蝟餌絞??]: 甇?敺?唳?獢???{device_name} ???..")
    return {
        "CPU": "Intel i5-11400F",
        "RAM": "64GB DDR4 (32GB x 2)",
        "GPU": "RTX 2060 (6GB VRAM)",
        "Highlight": "?璈??頞之 64GB 閮擃??虜?拙?頝???AI Agent??
    }

def run_agent(user_query):
    url = "http://host.docker.internal:11434/api/chat"
    tools = [{
        "name": "get_local_config",
        "description": "???砍?餉蝖祇??蔭",
        "parameters": {
            "type": "object",
            "properties": {"device_name": {"type": "string"}},
            "required": ["device_name"]
        }
    }]

    # 蝚砌?頛迎?隢?撌亙
    payload = {
        "model": "qwen2.5-coder:7b",
        "messages": [{"role": "user", "content": user_query}],
        "tools": tools, "stream": False
    }
    
    resp = requests.post(url, json=payload).json()
    msg = resp.get('message', {})

    if 'tool_calls' in msg or 'name' in msg.get('content', ''):
        # ?瑁?撌亙
        res = get_local_config("my_desktop")
        
        # --- ?嚗洵鈭活?澆??隞文撥??---
        payload['messages'].append(msg)
        payload['messages'].append({
            "role": "tool", 
            "content": f"?敺′蝣?啁?鞈?嚗json.dumps(res)}??刻??寞???鞈?嚗閬芸??葉??閬?塚?銝血???64GB RAM ?暺?
        })
        
        final_resp = requests.post(url, json=payload).json()
        return final_resp['message']['content']
    
    return msg.get('content', 'AI 瘝???)

print("\n?? [擃?EQ ? Agent ??銝?..")
print(f"\nAI ??蝯蜇蝯? \n{run_agent('??獢 (my_desktop) ?蔭?鈭漁暺?')}")
