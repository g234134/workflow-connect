import requests
import json

# 1. 摰儔 RAG ?亥岷撌亙 (璅⊥敺????蝑?蔭瑼?銝剜?撠?
def query_hardware_config(device_name):
    # 璅⊥敺?獢葉瑼Ｙ揣?啁??豢?
    config_data = {
        "獢": "Intel i5-11400F, RTX 2060, 64GB RAM (????",
        "蝑": "Intel i7-7700HQ, GTX 1050, 24GB RAM"
    }
    return config_data.get(device_name, "?曆??啗府閮剖???蝵株?閮?)

# 2. 摰儔撌亙 Schema
tools = [{
    "name": "get_device_specs",
    "description": "?亥岷?孵?閮剖?(憒??餅?蝑)?′擃?蝵株???,
    "parameters": {
        "type": "object",
        "properties": {
            "device": {"type": "string", "enum": ["獢", "蝑"], "description": "閮剖??迂"}
        },
        "required": ["device"]
    }
}]

def run_agent(user_query):
    url = "http://host.docker.internal:11434/api/chat"
    payload = {
        "model": "qwen2.5:7b",
        "messages": [{"role": "user", "content": user_query}],
        "tools": tools,
        "stream": False
    }
    
    # 蝚砌?甈∟矽?剁?AI 瘙箏??臬?閬極??    resp = requests.post(url, json=payload).json()
    msg = resp['message']

    if 'tool_calls' in msg:
        for call in msg['tool_calls']:
            # ?瑁??祕??Python ?賣
            device = call['function']['arguments']['device']
            print(f"\n[憭扯撅斗捱蝑: ?閬閰?{device} ??蝵?..")
            result = query_hardware_config(device)
            
            # 撠極?瑞????喟策 AI ?脰?????蝮賜???            payload['messages'].append(msg) # ? AI ??瘙?            payload['messages'].append({
                "role": "tool",
                "content": result
            })
            
            # 蝚砌?甈∟矽?剁?AI ?寞?撌亙蝯???
            final_resp = requests.post(url, json=payload).json()
            return final_resp['message']['content']
    
    return msg['content']

print("--- ??蝖祇??亥岷 Agent (?賣隤輻 + 璅⊥ RAG) ---")
print(f"\nAI ??蝯?蝑? \n{run_agent('??獢?曉?蔭憒?嚗?)}")
