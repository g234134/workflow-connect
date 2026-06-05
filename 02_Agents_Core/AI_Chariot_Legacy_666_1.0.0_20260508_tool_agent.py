import requests
import json

# 1. 摰儔銝??撖衣? Python ?賣
def add_numbers(a, b):
    return a + b

# 2. 摰儔撌亙??JSON Schema (?迄 AI ?極?瑟獐??
tools = [
    {
        "name": "add_numbers",
        "description": "?嗥?園?閬?蝞?摮?蝮賢??蝙?冽迨撌亙",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "蝚砌??摮?},
                "b": {"type": "number", "description": "蝚砌??摮?}
            },
            "required": ["a", "b"]
        }
    }
]

def chat_with_tools(user_input):
    url = "http://host.docker.internal:11434/api/chat"
    # ?蝙??qwen2.5:7b嚗??箏??典極?瑁矽?其??虜蝛拙?
    payload = {
        "model": "qwen2.5:7b",
        "messages": [{"role": "user", "content": user_input}],
        "tools": tools,
        "stream": False
    }
    
    response = requests.post(url, json=payload).json()
    message = response['message']

    # 3. 瑼Ｘ AI ?臬?唾?隤輻撌亙
    if 'tool_calls' in message:
        for tool in message['tool_calls']:
            func_name = tool['function']['name']
            args = tool['function']['arguments']
            print(f"\n[AI 隢?隤輻撌亙]: {func_name} ?: {args}")
            
            if func_name == "add_numbers":
                result = add_numbers(args['a'], args['b'])
                print(f"[撌亙?瑁?蝯?]: {result}")
                return f"閮?蝯???{result}"
    
    return message['content']

print("--- ??撌亙隤輻皜祈岫 ---")
print(f"AI ??: {chat_with_tools('撟急?閮? 12345 ?? 67890 ?臬?撠?')}")
