import os
import chromadb

def audit_system():
    print("="*50)
    print("?? 64GB 蝞?銝剖?嚗蝟餌絞??抒′?貉那??)
    print("="*50)

    # 1. 閮箸 RAG (ChromaDB)
    print("\n[1/3] 甇??脤?嚗ocker ChromaDB...")
    try:
        # ?岫?? Docker ?身??8000 ??        client = chromadb.HttpClient(host='localhost', port=8000)
        colls = client.list_collections()
        print(f" ????????菜葫??{len(colls)} ?霅澈??)
    except Exception as e:
        print(f" ????仃??隢Ⅱ隤?Docker 摰孵?臬????)

    # 2. 閮箸 瑼??? (DESIGN.md)
    print("\n[2/3] 甇???嚗laude Design 瑼?...")
    target_file = r"C:\dev\agency-agents\DESIGN.md"
    if os.path.exists(target_file):
        size = os.path.getsize(target_file)
        print(f" ???菜葫??嚗??DESIGN.md ({size} bytes)??)
    else:
        print(f" ????憭望?嚗楝敺?瘝? DESIGN.md??)

    # 3. 閮箸 ?啣??楝敺?    print("\n[3/3] 甇?瑼Ｘ嚗gent 撌乩??桅?...")
    target_dir = r"C:\dev\agency-agents"
    if os.path.exists(target_dir):
        print(f" ???桅?甇?虜嚗target_dir}")
    else:
        print(f" ???桅??箏仃嚗???撱箇?閰脰??冗??)

    print("\n" + "="*50)
    print("? 閮箸蝯?嚗??寞?銝膩蝯?蝣箄???扼?)
    print("="*50)

if __name__ == "__main__":
    audit_system()
