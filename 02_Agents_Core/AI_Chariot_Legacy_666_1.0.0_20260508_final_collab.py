import requests
import json
import chromadb
from chromadb.utils import embedding_functions

# 1. 瑼Ｙ揣?挾 (敺????澈?輻′擃???
client = chromadb.PersistentClient(path="/app/chroma_db")
emb_fn = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_collection(name="hw_specs", embedding_function=emb_fn)
query_res = collection.query(query_texts=["??餉?底蝝圈?蝵殷?"], n_results=3)
hw_info = " ".join(query_res['documents'][0])

def call_ollama(model, prompt):
    url = "http://host.docker.internal:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    return requests.post(url, json=payload).json()['response']

# 2. Coder 撖虫??挾
coder_prompt = f"雿?嗆?撣怒??餉??蝵殷?{hw_info}嚗神銝畾?Python 隞?Ⅳ靘芋?祇?鞎????頛詨隞?Ⅳ??
print("\n??儭?[Coder]: 甇??寞?鞈?摨怠?′擃??潭撖怎?撘Ⅳ...")
code = call_ollama("qwen2.5-coder:7b", coder_prompt)
print(f"\n--- Coder ?Ｗ?誨蝣?---\n{code}\n")

# 3. Reviewer 撖拇?挾
reviewer_prompt = f"雿撠振?炎?仿挾隞?Ⅳ?臬?拙???{hw_info} 銝?嚗?敺????????n隞?Ⅳ嚗code}"
print("?? [Reviewer]: 甇?撖拇隞?Ⅳ摰??..")
review = call_ollama("qwen2.5:7b", reviewer_prompt)
print(f"\n--- 撖拇?? ---\n{review}")

if "?詨?" in review:
    print("\n???蝯???RAG ??瘚??遛??嚗?)
