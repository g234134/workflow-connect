import requests
import json

def call_ollama(model, prompt):
    url = "http://host.docker.internal:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    resp = requests.post(url, json=payload).json()
    return resp['response']

# 1. 撖虫???畾?coder_prompt = """
雿鞈楛撌亦?撣怒??寞?隞乩?蝖祇?鞈?嚗神銝?陛?桃? Python ?單靘炎皜祉頂蝯梯?頛?
蝖祇?鞈?嚗ntel i5-11400F, 64GB RAM, RTX 2060??頛詨閬?嚗頛詨隞?Ⅳ嚗?閬圾??"""
print("??儭?[Coder]: 甇?蝺典神?單...")
code = call_ollama("qwen2.5-coder:7b", coder_prompt)
print(f"--- ??隞?Ⅳ ---\n{code}\n")

# 2. 撖拇??畾?reviewer_prompt = f"""
雿隞?Ⅳ撖拇?～?瑼Ｘ隞乩?隞?Ⅳ?臬??瘜隤斗??摩蝻箏仃??隞?Ⅳ?批捆嚗?{code}

隢策?箇陛?剔?閰嚗蒂?冽?敺?銵神銝?????"""
print("?? [Reviewer]: 甇?撖拇隞?Ⅳ...")
review = call_ollama("qwen2.5:7b", reviewer_prompt)
print(f"--- 撖拇?? ---\n{review}")

# 3. ?蝯捱蝑?(?停?舀?祟?訾?蝵?
if "?詨?" in review:
    print("\n??瘚???嚗誨蝣澆歇?? AI ?芯蜓撖拇嚗?)
else:
    print("\n??瘚?銝剜嚗祟?詨撱箄降靽格??)
