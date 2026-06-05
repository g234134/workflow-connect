#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雜訊模式分析與正則表達式生成
"""

import pandas as pd
import re

def analyze_noise_patterns():
    """分析雜訊模式並生成正則表達式"""

    # 讀取前 50 筆數據
    df = pd.read_csv('data/dirty_data_100k.csv')
    sample = df.head(50)

    print("="*60)
    print("Noise Pattern Analysis & Regex Generation")
    print("="*60)

    # 定義雜訊模式及其對應的正則表達式
    noise_regexes = {
        "HTML Tags": {
            "patterns": [
                r"<div[^>]*>.*?</div>",  # HTML div 標籤
                r"<u>.*?</u>",          # HTML 下劃線標籤
                r"<[^>]+>",             # 通用 HTML 標籤
            ],
            "description": "移除所有 HTML 標籤和標籤內容"
        },
        "Advertisement Text": {
            "patterns": [
                r"---廣告贊助---",      # 廣告文字
                r"點我領取優惠",        # 優惠廣告
                r"下殺五折",           # 折扣廣告
                r"優惠|折扣|促銷",      # 促銷相關詞
            ],
            "description": "移除廣告和促銷相關文字"
        },
        "JavaScript/Code": {
            "patterns": [
                r"undefined",          # JavaScript undefined
                r"NaN",                # Not a Number
                r"ERROR_\w+",          # 錯誤訊息
                r"JS_CALLBACK_FUNC\([^)]+\)",  # JavaScript 回調函數
                r"0x[0-9a-fA-F]+",     # 十六進位數字
            ],
            "description": "移除 JavaScript 代碼和錯誤訊息"
        },
        "Special Characters": {
            "patterns": [
                r"!{3,}",              # 3 個以上的驚嘆號
                r"\?{2,}",             # 2 個以上的問號
                r"[~@#$%^&*]{2,}",    # 2 個以上的特殊符號
            ],
            "description": "移除過多的特殊字符"
        },
        "Control Characters": {
            "patterns": [
                r"[\x00-\x1F\x7F]",   # 控制字符
                r"[\r\n\t]",           # 換行和製表符
            ],
            "description": "移除控制字符"
        }
    }

    # 生成完整的正則表達式
    print("\n[GENERATED] Regex Patterns:\n")

    all_patterns = []
    for category, info in noise_regexes.items():
        print(f"{category}:")
        print(f"  Description: {info['description']}")
        print(f"  Patterns:")

        for pattern in info["patterns"]:
            print(f"    - {pattern}")
            all_patterns.append(pattern)

        print()

    # 生成組合正則表達式
    combined_pattern = "|".join(all_patterns)
    print(f"[COMBINED] Combined Regex Pattern:")
    print(f"  {combined_pattern[:200]}...")
    print()

    # 測試正則表達式
    print("[TEST] Testing regex patterns:\n")

    test_cases = [
        "iPad<u>下殺五折</u>",
        "<div class='ad'>點我領取優惠</div>Sony Headphone",
        "undefinedMacBook",
        "!!!Samsung TV",
        "iPadNaN",
        "---廣告贊助---iPhone",
        "JS_CALLBACK_FUNC(0x666)Samsung TV",
        "ERROR_404_NOT_FOUNDiPad",
    ]

    for test_case in test_cases:
        # 應用所有正則表達式
        cleaned = test_case
        for pattern in all_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 清理多餘空格
        cleaned = ' '.join(cleaned.split())

        print(f"  Original: {test_case}")
        print(f"  Cleaned:  {cleaned}")
        print()

    return noise_regexes, combined_pattern

def generate_knowledge_base_content():
    """生成知識庫內容"""

    noise_regexes, combined_pattern = analyze_noise_patterns()

    # 生成知識庫內容
    knowledge_content = """## 非結構化雜訊過濾正則表達式
- 描述：從髒數據中識別和過濾常見的非結構化雜訊模式，包括 HTML 標籤、廣告文字、JavaScript 代碼片段和特殊字符
- 優勢：
    - **多模式識別**：同時處理多種類型的雜訊模式
    - **高效過濾**：使用正則表達式快速清理大量數據
    - **可擴展性**：易於添加新的雜訊模式識別規則
    - **保留核心內容**：精準移除雜訊，保留有效數據
- 應用場景：網頁抓取數據清洗、用戶生成內容過濾、日誌數據清理、文本數據預處理

### 正則表達式模式庫

#### 1. HTML 標籤過濾
```python
# 移除 HTML div 標籤及其內容
r"<div[^>]*>.*?</div>"

# 移除 HTML 下劃線標籤及其內容
r"<u>.*?</u>"

# 移除所有 HTML 標籤
r"<[^>]+>"
```

#### 2. 廣告文字過濾
```python
# 移除廣告贊助文字
r"---廣告贊助---"

# 移除優惠促銷文字
r"點我領取優惠|下殺五折|優惠|折扣|促銷"
```

#### 3. JavaScript/程式碼過濾
```python
# 移除 JavaScript undefined
r"undefined"

# 移除 NaN 值
r"NaN"

# 移除錯誤訊息
r"ERROR_\w+"

# 移除 JavaScript 回調函數
r"JS_CALLBACK_FUNC\([^)]+\)"

# 移除十六進位數字
r"0x[0-9a-fA-F]+"
```

#### 4. 特殊字符過濾
```python
# 移除過多的驚嘆號
r"!{3,}"

# 移除過多的問號
r"\?{2,}"

# 移除過多的特殊符號
r"[~@#$%^&*]{2,}"
```

#### 5. 控制字符過濾
```python
# 移除控制字符
r"[\x00-\x1F\x7F]"

# 移除換行和製表符
r"[\r\n\t]"
```

### 組合使用範例

```python
import re

def clean_dirty_text(text):
    '''清理髒文本中的雜訊'''

    # 定義所有雜訊模式
    noise_patterns = [
        r"<div[^>]*>.*?</div>",
        r"<u>.*?</u>",
        r"<[^>]+>",
        r"---廣告贊助---",
        r"點我領取優惠|下殺五折",
        r"undefined|NaN",
        r"ERROR_\w+",
        r"JS_CALLBACK_FUNC\([^)]+\)",
        r"0x[0-9a-fA-F]+",
        r"!{3,}",
        r"\?{2,}",
        r"[~@#$%^&*]{2,}",
        r"[\x00-\x1F\x7F]",
        r"[\r\n\t]"
    ]

    # 應用所有過濾規則
    cleaned = text
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # 清理多餘空格
    cleaned = ' '.join(cleaned.split())

    return cleaned

# 使用範例
dirty_text = "<div class='ad'>點我領取優惠</div>iPad<u>下殺五折</u>!!!"
clean_text = clean_dirty_text(dirty_text)
# 結果: "iPad"
```

### 效能優化建議

1. **預編譯正則表達式**：對於大量數據處理，預先編譯正則表達式可提升效能
2. **按優先級處理**：先處理最常見的雜訊模式
3. **批量處理**：使用向量化操作處理大量文本
4. **緩存機制**：對重複出現的雜訊模式建立緩存

### 擴展方向

- 支持自定義雜訊模式配置
- 添加機器學習輔助的雜訊識別
- 支持多語言雜訊過濾
- 實時雜訊檢測和預警機制
"""

    return knowledge_content

if __name__ == "__main__":
    # 生成知識庫內容
    knowledge_content = generate_knowledge_base_content()

    # 顯示生成的內容
    print("="*60)
    print("Generated Knowledge Base Content")
    print("="*60)
    print(knowledge_content[:500] + "...")
    print()

    # 保存到檔案（可選）
    # with open("noise_filtering_knowledge.md", "w", encoding="utf-8") as f:
    #     f.write(knowledge_content)

    print("="*60)
    print("Analysis Complete")
    print("="*60)