import requests
import json
import sys
from io import StringIO

def call_ollama(model, prompt):
    url = "http://host.docker.internal:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    return requests.post(url, json=payload).json()['response']

# 1. Coder 撖思誨蝣?print("??儭?[Coder]: 甇?蝺典神蝟餌絞瑼Ｘ葫?單...")
coder_prompt = "雿撌亦?撣怒?撖思?畾萇陛?桃? Python 隞?Ⅳ嚗?蝞?1 ??1000000 ?像?孵?嚗蒂??箇????瑁????閬撓?箔誨蝣潘?銝?閫????
code = call_ollama("qwen2.5-coder:7b", coder_prompt).strip("`").replace("python", "")

# 2. Reviewer 撖拇
print("?? [Reviewer]: 甇?摰撖拇...")
reviewer_prompt = f"雿摰撠振?挾隞?Ⅳ?臬摰嚗?芷瑼??蝬脰楝?餅?嚗??亙??刻???????血???誨蝣潘?\n{code}"
review = call_ollama("qwen2.5:7b", reviewer_prompt)

# 3. ?芸??瑁? (瘝?璅∪?)
if "?詨?" in review:
    print("??撖拇??嚗??銵?..")
    print(f"--- ?瑁?隞?Ⅳ ---\n{code}\n")
    
    # ?? Python 頛詨
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    
    try:
        exec(code) # <--- ?????剁??迤頝絲靘?
        sys.stdout = old_stdout
        execution_result = redirected_output.getvalue()
        print(f"--- ?瑁?蝯? ---\n{execution_result}")
        
        # 4. ?蝯蜇蝯?        summary = call_ollama("qwen2.5:7b", f"AI ???瑁?鈭誨蝣潘?蝯??荔?{execution_result}??蝯衣?嗡??陛?剔?蝮賜???)
        print(f"?? [AI 蝮賜?]: {summary}")
        
    except Exception as e:
        sys.stdout = old_stdout
        print(f"???瑁??粹: {e}")
else:
    print(f"??撖拇?芷?: {review}")
