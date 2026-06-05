import os
import platform
import importlib.metadata

def check_env():
    print(f"--- 系統環境偵測 ---")
    print(f"作業系統: {platform.system()} {platform.version()}")
    print(f"Python 版本: {platform.python_version()}")
    
    # 定義要檢查的關鍵套件
    packages = ["crewai", "langchain", "pydantic", "ollama", "chromadb"]
    print(f"\n--- 已安裝套件清單 ---")
    for pkg in packages:
        try:
            version = importlib.metadata.version(pkg)
            print(f"{pkg}: {version}")
        except importlib.metadata.PackageNotFoundError:
            print(f"{pkg}: 未安裝")

if __name__ == '__main__':
    check_env()
