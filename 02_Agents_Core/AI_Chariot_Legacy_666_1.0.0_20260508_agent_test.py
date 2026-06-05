import requests
def call(m, p):
    r = requests.post("http://host.docker.internal:11434/api/generate", json={"model": m, "prompt": p, "stream": False})
    return r.json().get('response', 'Error')
print("--- ??憭?賡?皜祈岫 ---")
s = call("qwen2.5:7b", "摰儔銝?I?格?")
print(f"憭扯撅? {s}")
c = call("qwen2.5-coder:7b", f"?寞??格?撖思誨蝣? {s}")
print(f"銵?撅? {c}")
