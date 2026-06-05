import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="/app/chroma_db")
emb_fn = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_collection(name="hw_specs", embedding_function=emb_fn)

# 璅⊥閰Ｗ?
query = "???餉???園?鞈?嚗?
results = collection.query(query_texts=[query], n_results=1)

print(f"\n?? 瑼Ｙ揣蝯?: {results['documents'][0][0]}")
