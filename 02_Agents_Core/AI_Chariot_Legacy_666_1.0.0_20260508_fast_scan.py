import os
import json
import time
import sys

# 強制設定輸出為 UTF-8，防止 cp950 報錯
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fast_scan(path=".", max_depth=3):
    exclude = {'.git', 'node_modules', 'venv', '__pycache__', '.venv', 'dify', 'dify-docker'}
    result = {}
    
    print(f"Starting Fast Scan: {path} (Max Depth: {max_depth})")
    
    for root, dirs, files in os.walk(path):
        depth = root[len(path):].count(os.sep)
        if depth >= max_depth:
            del dirs[:]
            continue
            
        dirs[:] = [d for d in dirs if d not in exclude]
        
        # 維持 40 轉/分鐘的節奏
        time.sleep(0.5) 
        
        result[root] = {
            "dirs": dirs,
            "files": files
        }
        print(f"Indexed: {root}")

    with open("project_map.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
    print("\nCache Complete! Saved to project_map.json")

if __name__ == "__main__":
    fast_scan()
