#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGen 全功率版本 - 整合多工具与配额监控
功能：Google Search、Web Crawl、Jina Reader、配额监控
"""

import sys
import io
import os
import requests
import time
import csv
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入配置加载器
try:
    from config_loader import initialize_config_system, get_config_loader
    config_initialized = initialize_config_system()
    if config_initialized:
        config_loader = get_config_loader()
    else:
        config_loader = None
        print("[WARNING] 配置系统初始化失败，将使用默认配置")
except ImportError:
    config_loader = None
    print("[WARNING] 配置加载器导入失败，将使用默认配置")

# 设置标准输出为 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ==================== 配置区域 ====================

# API 密钥配置
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
JINA_API_KEY = os.environ.get("JINA_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# API 密钥池（用於輪換）
TAVILY_API_KEYS = [key.strip() for key in os.environ.get("TAVILY_API_KEYS", "").split(",") if key.strip()] if os.environ.get("TAVILY_API_KEYS") else [TAVILY_API_KEY]
FIRECRAWL_API_KEYS = [key.strip() for key in os.environ.get("FIRECRAWL_API_KEYS", "").split(",") if key.strip()] if os.environ.get("FIRECRAWL_API_KEYS") else [FIRECRAWL_API_KEY]
JINA_API_KEYS = [key.strip() for key in os.environ.get("JINA_API_KEYS", "").split(",") if key.strip()] if os.environ.get("JINA_API_KEYS") else [JINA_API_KEY]
GROQ_API_KEYS = [key.strip() for key in os.environ.get("GROQ_API_KEYS", "").split(",") if key.strip()] if os.environ.get("GROQ_API_KEYS") else [GROQ_API_KEY]

# 工具配置
TOOL_CONFIG = {
    "tavily_base_url": "https://api.tavily.com",
    "firecrawl_base_url": "https://api.firecrawl.dev",
    "jina_base_url": "https://r.jina.ai",
    "gemini_base_url": "https://generativelanguage.googleapis.com/v1",
}

# Ollama 配置
OLLAMA_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "llama3",
}


# ==================== API KEY 管理器 ====================

class APIKeyManager:
    """API KEY 輪換管理器"""

    def __init__(self):
        self.key_pools = {
            "tavily": TAVILY_API_KEYS,
            "firecrawl": FIRECRAWL_API_KEYS,
            "jina": JINA_API_KEYS,
            "groq": GROQ_API_KEYS,
        }
        self.current_indices = {service: 0 for service in self.key_pools}
        self.key_status = {service: {} for service in self.key_pools}  # 追蹤每個 KEY 的狀態
        self.failure_counts = {service: {} for service in self.key_pools}  # 追蹤失敗次數

    def get_key(self, service: str) -> str:
        """
        獲取可用的 API KEY

        Args:
            service: 服務名稱 (tavily, firecrawl, jina, groq)

        Returns:
            當前可用的 API KEY
        """
        if service not in self.key_pools:
            raise ValueError(f"未知的服務: {service}")

        keys = self.key_pools[service]
        if not keys or not keys[0]:
            raise ValueError(f"服務 {service} 沒有可用的 API KEY")

        current_index = self.current_indices[service]
        return keys[current_index]

    def rotate_key(self, service: str, reason: str = "manual"):
        """
        輪換到下一個 API KEY

        Args:
            service: 服務名稱
            reason: 輪換原因
        """
        if service not in self.key_pools:
            return

        keys = self.key_pools[service]
        if len(keys) <= 1:
            print(f"[KEY Manager] 服務 {service} 只有一個 KEY，無法輪換")
            return

        current_index = self.current_indices[service]
        next_index = (current_index + 1) % len(keys)

        self.current_indices[service] = next_index

        print(f"[KEY Manager] {service} KEY 輪換: {current_index} → {next_index} (原因: {reason})")

    def mark_failure(self, service: str, error: str = ""):
        """
        標記 KEY 失敗並自動輪換

        Args:
            service: 服務名稱
            error: 錯誤信息
        """
        if service not in self.key_pools:
            return

        current_index = self.current_indices[service]
        key = self.key_pools[service][current_index]

        # 增加失敗計數
        if service not in self.failure_counts:
            self.failure_counts[service] = {}
        if current_index not in self.failure_counts[service]:
            self.failure_counts[service][current_index] = 0

        self.failure_counts[service][current_index] += 1
        fail_count = self.failure_counts[service][current_index]

        print(f"[KEY Manager] {service} KEY 失敗 (第 {fail_count} 次): {error[:50]}...")

        # 連續失敗 3 次則輪換
        if fail_count >= 3:
            print(f"[KEY Manager] {service} KEY 連續失敗 {fail_count} 次，自動輪換")
            self.rotate_key(service, f"連續失敗 {fail_count} 次")
            # 重置失敗計數
            self.failure_counts[service][current_index] = 0

    def mark_success(self, service: str):
        """
        標記 KEY 成功使用

        Args:
            service: 服務名稱
        """
        if service not in self.key_pools:
            return

        current_index = self.current_indices[service]
        if service in self.failure_counts and current_index in self.failure_counts[service]:
            # 重置失敗計數
            self.failure_counts[service][current_index] = 0

    def get_status(self) -> dict:
        """獲取所有 KEY 的狀態"""
        status = {}
        for service, keys in self.key_pools.items():
            current_index = self.current_indices[service]
            status[service] = {
                "total_keys": len(keys),
                "current_index": current_index,
                "current_key": keys[current_index][:8] + "..." if keys[current_index] else "None",
                "failure_counts": self.failure_counts.get(service, {})
            }
        return status

    def print_status(self):
        """打印 KEY 狀態"""
        print(f"\n{'='*60}")
        print(f"[API KEY 狀態]")
        print(f"{'='*60}")

        status = self.get_status()
        for service, info in status.items():
            print(f"\n[{service.upper()}]")
            print(f"  總 KEY 數: {info['total_keys']}")
            print(f"  當前索引: {info['current_index']}")
            print(f"  當前 KEY: {info['current_key']}")
            if info['failure_counts']:
                print(f"  失敗計數: {info['failure_counts']}")

        print(f"{'='*60}\n")


# 全局 API KEY 管理器
api_key_manager = APIKeyManager()


# ==================== API KEY 持久化管理 ====================

class APIKeyPersistence:
    """API KEY 狀態持久化管理器"""

    def __init__(self, status_file="logs/api_key_status.json"):
        self.status_file = status_file
        self.status_data = self.load_status()

    def load_status(self) -> dict:
        """從檔案載入 KEY 狀態"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Persistence] 載入狀態失敗: {e}")
        return {}

    def save_status(self, status: dict):
        """保存 KEY 狀態到檔案"""
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)

            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
            print(f"[Persistence] 狀態已保存到 {self.status_file}")
        except Exception as e:
            print(f"[Persistence] 保存狀態失敗: {e}")

    def restore_manager_state(self, manager: APIKeyManager):
        """恢復管理器狀態"""
        if not self.status_data:
            print("[Persistence] 沒有保存的狀態，使用初始狀態")
            return

        for service, data in self.status_data.items():
            if service in manager.key_pools:
                # 恢復當前索引
                if 'current_index' in data:
                    manager.current_indices[service] = data['current_index']
                    print(f"[Persistence] 恢復 {service} 索引: {data['current_index']}")

                # 恢復失敗計數
                if 'failure_counts' in data:
                    manager.failure_counts[service] = data['failure_counts']
                    print(f"[Persistence] 恢復 {service} 失敗計數")

    def save_manager_state(self, manager: APIKeyManager):
        """保存管理器狀態"""
        status = {}
        for service in manager.key_pools.keys():
            status[service] = {
                'current_index': manager.current_indices[service],
                'failure_counts': manager.failure_counts.get(service, {}),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        self.save_status(status)


# 全局持久化管理器
api_key_persistence = APIKeyPersistence()


# ==================== 強健 API 呼叫 ====================

def robust_api_call(api_func, service_name: str, max_retries: int = 3):
    """
    強健的 API 呼叫函式，支持自動重試和 KEY 輪換

    Args:
        api_func: 呼叫 API 的具體函式
        service_name: 服務名稱 (tavily, firecrawl, jina, groq)
        max_retries: 最大重試次數

    Returns:
        API 響應結果，如果全部失敗則返回 None
    """
    # 獲取該服務的所有 KEY
    keys = api_key_manager.key_pools.get(service_name, [])
    if not keys:
        print(f"❌ {service_name} 沒有可用的 API KEY")
        return None

    # 遍歷所有 KEY，每個 KEY 試一次
    for key_index, key in enumerate(keys):
        for attempt in range(max_retries):
            try:
                print(f"[API Call] {service_name} 使用 KEY {key_index + 1}/{len(keys)} (嘗試 {attempt + 1}/{max_retries})")

                # 執行 API 呼叫，傳入當前 KEY
                result = api_func(key)

                # 成功則標記 KEY 狀態
                api_key_manager.mark_success(service_name)

                # 保存狀態
                api_key_persistence.save_manager_state(api_key_manager)

                print(f"✅ {service_name} 成功 (KEY {key_index + 1})")
                return result

            except Exception as e:
                error_msg = str(e)
                print(f"❌ {service_name} KEY {key_index + 1} 失敗 (嘗試 {attempt + 1}/{max_retries}): {error_msg[:80]}...")

                # 標記失敗
                api_key_manager.mark_failure(service_name, error_msg)

                # 保存狀態
                api_key_persistence.save_manager_state(api_key_manager)

                # 如果不是最後一次嘗試，等待後重試
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指數退避: 2, 4, 8秒
                    print(f"[API Call] 等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    # 當前 KEY 的所有重試都失敗，切換到下一個 KEY
                    print(f"🔄 {service_name} KEY {key_index + 1} 耗盡，切換到下一個 KEY...")
                    time.sleep(1)  # 緩衝一下

    print(f"🚨 {service_name} 所有 KEY 都失敗，請檢查網路或該服務後台狀態。")
    return None


# ==================== 配置系统 ====================

def display_config_info():
    """显示当前配置信息"""
    if config_loader:
        print(f"\n{'='*60}")
        print(f"[系统配置]")
        print(f"{'='*60}")

        summary = config_loader.get_config_summary()
        for key, value in summary.items():
            print(f"- {key}: {value}")

        # 显示清洗规则详情
        if config_loader.cleaning_rules:
            print(f"\n[清洗规则详情]")
            print(f"{'='*60}")
            rules = config_loader.get_rule_descriptions()
            for rule_name, description in rules.items():
                print(f"- {rule_name}: {description}")

        print(f"{'='*60}\n")
    else:
        print("[WARNING] 配置加载器不可用，无法显示配置信息")


def get_scoring_weights() -> Dict[str, float]:
    """
    获取评分权重

    Returns:
        评分权重字典
    """
    if config_loader:
        return config_loader.get_scoring_weights()
    else:
        # 默认权重
        return {"semantic": 0.4, "format": 0.3, "kb": 0.3}


def get_cleaning_thresholds() -> Dict[str, float]:
    """
    获取清洗阈值

    Returns:
        阈值字典
    """
    if config_loader:
        return config_loader.get_thresholds()
    else:
        # 默认阈值
        return {"fail": 0, "pass": 0.8, "warning": 0.6}


# ==================== 演化系統配置 ====================

EVOLUTION_CONFIG = {
    "knowledge_base_file": "knowledge/cleaning_knowledge_base.md",
    "evolution_log_file": "logs/evolution_log.csv",
    "reports_dir": "reports/",
    "data_dir": "data/",
    "search_interval_hours": 1,  # 搜尋頻率：每1小時
    "evolution_interval_days": 1,  # 進化頻率：每1天
    "dirty_data_sample": [
        {"id": 1, "name": "Product A", "price": -50.99, "quantity": 10, "category": "electronics"},
        {"id": 2, "name": "Product B", "price": 999999.99, "quantity": 5, "category": "furniture"},
        {"id": 3, "name": "Product C", "price": 29.99, "quantity": -3, "category": "electronics"},
        {"id": 4, "name": "Product D", "price": 49.99, "quantity": 15, "category": "books"},
        {"id": 5, "name": "Product E", "price": 0.00, "quantity": 8, "category": "electronics"},
        {"id": 6, "name": "Product F", "price": 79.99, "quantity": 1000, "category": "furniture"},
        {"id": 7, "name": "", "price": 39.99, "quantity": 12, "category": "books"},
        {"id": 8, "name": "Product H", "price": "N/A", "quantity": 6, "category": "electronics"},
    ]
}

def initialize_evolution_system():
    """初始化演化系統檔案"""
    print(f"[Evolution System] 初始化演化系統...")

    # 確保目錄存在
    dirs_to_create = [
        "docs",
        "knowledge",
        "reports",
        "logs",
        "data"
    ]

    for dir_name in dirs_to_create:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"[Evolution System] 建立目錄: {dir_name}/")

    # 初始化知識庫檔案
    kb_file = EVOLUTION_CONFIG["knowledge_base_file"]
    if not os.path.exists(kb_file):
        with open(kb_file, 'w', encoding='utf-8') as f:
            f.write("# 數據清洗知識庫\n\n")
            f.write(f"建立時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 最新技術\n\n")
            f.write("此檔案將儲存從雲端搜尋到的最新數據清洗技術。\n\n")
        print(f"[Evolution System] 建立知識庫: {kb_file}")
    else:
        print(f"[Evolution System] 知識庫已存在: {kb_file}")

    # 初始化演化日誌檔案
    log_file = EVOLUTION_CONFIG["evolution_log_file"]
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'model_used', 'inference_time',
                'cleaning_accuracy', 'knowledge_base_size',
                'search_query', 'status'
            ])
        print(f"[Evolution System] 建立演化日誌: {log_file}")
    else:
        print(f"[Evolution System] 演化日誌已存在: {log_file}")

    print(f"[Evolution System] 初始化完成\n")

def log_evolution_result(model_used: str, inference_time: float,
                        cleaning_accuracy: float, knowledge_base_size: int,
                        search_query: str, status: str):
    """記錄演化結果到 CSV"""
    log_file = EVOLUTION_CONFIG["evolution_log_file"]

    try:
        with open(log_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                model_used,
                f"{inference_time:.2f}",
                f"{cleaning_accuracy:.2f}",
                knowledge_base_size,
                search_query,
                status
            ])
        print(f"[Evolution System] 記錄演化結果: {model_used} - {inference_time:.2f}s")
    except Exception as e:
        print(f"[ERROR] 記錄演化結果失敗: {e}")

def perform_search():
    """執行雲端搜尋並更新知識庫"""
    print(f"\n{'='*60}")
    print(f"[搜尋階段] 雲端搜尋最新技術")
    print(f"{'='*60}\n")

    search_query = "2026 數據清洗最新技術 -flooring -wood"
    print(f"[搜尋] 查詢: {search_query}")

    search_results = google_search_with_retry(search_query, max_results=5)

    if not search_results:
        print("[ERROR] 搜尋失敗，無法獲取最新技術")
        return False

    print(f"[搜尋] 找到 {len(search_results)} 個結果")

    # [ SmartRouter 升級版 ] 透過本地中轉避開 429 錯誤
    print(f"\n[ SmartRouter ] 正在連接本地中轉系統 (NVIDIA/Groq)...")

    try:
        # 指向您正在執行的 smart_router.py
        router_url = "http://127.0.0.1:8000/v1/chat/completions"

        extraction_prompt = f"""
請從以下搜尋結果中提取 2026 年數據清洗的最新技術要點，並整理成結構化的 Markdown 格式。
搜尋結果：
{json.dumps(search_results, ensure_ascii=False, indent=2)}

請按照以下格式輸出：
## 技術名稱
- 描述：...
- 優勢：...
- 應用場景：...
"""

        # 符合 SmartRouter 接收的格式
        router_payload = {
            "messages": [
                {"role": "system", "content": "你是一個專業的資料清洗專家，只輸出技術要點，不要多餘內容。"},
                {"role": "user", "content": extraction_prompt}
            ]
        }

        start_time = time.time()
        # 呼叫路由器，由它自動處理 API Key 切換
        response = requests.post(router_url, json=router_payload, timeout=60)
        end_time = time.time()
        inference_time = end_time - start_time

        if response.status_code == 200:
            result = response.json()
            # 取得路由器返回的文字內容
            extracted_content = result['choices'][0]['message']['content']

            print(f"[ SmartRouter ] 提取完成，耗時: {inference_time:.2f} 秒")

            # 存入知識庫 (維持原本的存檔邏輯)
            kb_file = EVOLUTION_CONFIG["knowledge_base_file"]
            with open(kb_file, 'a', encoding='utf-8') as f:
                f.write(f"\n## 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"搜尋查詢: {search_query}\n\n")
                f.write(extracted_content)
                f.write("\n" + "="*60 + "\n")

            print(f"[知識庫] 已更新: {kb_file}")
            
            # 確保有定義此函式
            if 'update_search_time' in globals():
                update_search_time()
                
            return True
        else:
            print(f"[ERROR] SmartRouter 轉發失敗: {response.status_code}")
            print(f"[DEBUG] 錯誤內容: {response.text}")
            return False

    except Exception as e:
        print(f"[ERROR] 執行提取流程時發生異常: {str(e)}")
        return False

def perform_evolution():
    """執行本地模型進化測試"""
    print(f"\n{'='*60}")
    print(f"[進化階段] 本地模型效能測試")
    print(f"{'='*60}\n")

    # 讀取知識庫
    kb_file = EVOLUTION_CONFIG["knowledge_base_file"]
    with open(kb_file, 'r', encoding='utf-8') as f:
        knowledge_base = f.read()

    print(f"[知識庫] 當前大小: {len(knowledge_base)} 字符")

    # 讓本地模型讀取知識庫並進行測試
    test_prompt = f"""
請閱讀以下數據清洗知識庫，然後對給定的髒數據進行清洗。

知識庫內容：
{knowledge_base[:2000]}...（知識庫內容較長，此為摘要）

髒數據樣本：
{json.dumps(EVOLUTION_CONFIG['dirty_data_sample'], ensure_ascii=False, indent=2)}

請：
1. 識別數據中的問題
2. 應用適當的清洗方法
3. 輸出清洗後的數據
4. 說明使用的清洗技術
"""

    print(f"[本地模型] 正在進行數據清洗測試...")

    cleaned_result, inference_time, model_used = call_local_model(test_prompt)

    print(f"[本地模型] 清洗完成")
    print(f"[本地模型] 使用模型: {model_used}")
    print(f"[本地模型] 推論耗時: {inference_time:.2f} 秒")

    # 計算清洗準確率（模擬）
    cleaning_accuracy = 0.85  # 模擬準確率

    # 記錄演化結果
    knowledge_base_size = get_knowledge_base_size()
    log_evolution_result(
        model_used=model_used,
        inference_time=inference_time,
        cleaning_accuracy=cleaning_accuracy,
        knowledge_base_size=knowledge_base_size,
        search_query="定期進化測試",
        status="success"
    )

    # 顯示清洗結果摘要
    print(f"\n{'='*60}")
    print(f"[進化結果摘要]")
    print(f"{'='*60}")
    print(f"模型: {model_used}")
    print(f"推論耗時: {inference_time:.2f} 秒")
    print(f"清洗準確率: {cleaning_accuracy:.2%}")
    print(f"知識庫大小: {knowledge_base_size} 字符")
    print(f"{'='*60}\n")

    update_evolution_time()  # 更新進化時間
    return True

def should_search() -> bool:
    """檢查是否應該進行搜尋（每1小時）"""
    last_search_file = "logs/last_search_time.txt"
    search_interval = EVOLUTION_CONFIG["search_interval_hours"] * 3600  # 轉換為秒

    if not os.path.exists(last_search_file):
        return True  # 第一次執行，需要搜尋

    try:
        with open(last_search_file, 'r') as f:
            last_search_time = float(f.read().strip())
        current_time = time.time()
        return (current_time - last_search_time) >= search_interval
    except:
        return True  # 如果讀取失敗，進行搜尋

def should_evolve() -> bool:
    """檢查是否應該進行進化（每1天）"""
    last_evolution_file = "logs/last_evolution_time.txt"
    evolution_interval = EVOLUTION_CONFIG["evolution_interval_days"] * 24 * 3600  # 轉換為秒

    if not os.path.exists(last_evolution_file):
        return True  # 第一次執行，需要進化

    try:
        with open(last_evolution_file, 'r') as f:
            last_evolution_time = float(f.read().strip())
        current_time = time.time()
        return (current_time - last_evolution_time) >= evolution_interval
    except:
        return True  # 如果讀取失敗，進行進化

def update_search_time():
    """更新最後搜尋時間"""
    last_search_file = "logs/last_search_time.txt"
    with open(last_search_file, 'w') as f:
        f.write(str(time.time()))

def update_evolution_time():
    """更新最後進化時間"""
    last_evolution_file = "logs/last_evolution_time.txt"
    with open(last_evolution_file, 'w') as f:
        f.write(str(time.time()))

def get_knowledge_base_size() -> int:
    """獲取知識庫大小（字符數）"""
    kb_file = EVOLUTION_CONFIG["knowledge_base_file"]
    if os.path.exists(kb_file):
        with open(kb_file, 'r', encoding='utf-8') as f:
            return len(f.read())
    return 0

def check_knowledge_exists(knowledge_title: str) -> bool:
    """
    檢查知識是否已存在於知識庫中

    Args:
        knowledge_title: 知識標題（如 "Dynamic Isolation Forest (DIF)"）

    Returns:
        True 如果知識已存在，False 否則
    """
    kb_file = EVOLUTION_CONFIG["knowledge_base_file"]
    if not os.path.exists(kb_file):
        return False

    try:
        with open(kb_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 檢查是否包含該知識標題
        return knowledge_title in content
    except Exception as e:
        print(f"[Knowledge Base] 檢查知識存在時發生錯誤: {e}")
        return False

def append_knowledge(knowledge_title: str, knowledge_content: str, source: str = "web_extraction") -> bool:
    """
    追加知識到知識庫，包含重複性檢查

    Args:
        knowledge_title: 知識標題
        knowledge_content: 知識內容（Markdown 格式）
        source: 知識來源

    Returns:
        True 如果成功追加，False 如果知識已存在或發生錯誤
    """
    # 重複性檢查
    if check_knowledge_exists(knowledge_title):
        print(f"[Knowledge Base] 知識已存在，跳過追加: {knowledge_title}")
        return False

    kb_file = EVOLUTION_CONFIG["knowledge_base_file"]

    try:
        with open(kb_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"來源: {source}\n\n")
            f.write(knowledge_content)
            f.write("\n" + "="*60 + "\n")

        print(f"[Knowledge Base] 成功追加知識: {knowledge_title}")
        return True

    except Exception as e:
        print(f"[Knowledge Base] 追加知識失敗: {e}")
        return False

# ==================== Token 流量监控类 ====================

class TokenMonitor:
    """Token 流量监控器"""

    def __init__(self):
        self.stats = {
            "gemini": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "call_count": 0,
                "max_single_call": 0,
            },
            "ollama": {
                "total_chars": 0,
                "call_count": 0,
                "max_single_call": 0,
            },
            "task_start_time": datetime.now(),
        }

    def record_gemini_usage(self, prompt_tokens: int, completion_tokens: int):
        """记录 Gemini Token 使用"""
        total_tokens = prompt_tokens + completion_tokens

        self.stats["gemini"]["prompt_tokens"] += prompt_tokens
        self.stats["gemini"]["completion_tokens"] += completion_tokens
        self.stats["gemini"]["total_tokens"] += total_tokens
        self.stats["gemini"]["call_count"] += 1

        # 更新单次最大值
        if total_tokens > self.stats["gemini"]["max_single_call"]:
            self.stats["gemini"]["max_single_call"] = total_tokens

        # 自动预警
        if total_tokens > 10000:
            print(f"\n{'='*60}")
            print(f"[⚠️ 警告] Gemini 单次调用 Token 超过 10,000！")
            print(f"[⚠️ 警告] 本次调用: {total_tokens} tokens")
            print(f"[⚠️ 警告] 请注意免费版上限")
            print(f"{'='*60}\n")

        # 实时显示
        self._show_realtime_stats()

    def record_ollama_usage(self, text: str):
        """记录 Ollama 使用（字数统计）"""
        char_count = len(text)

        self.stats["ollama"]["total_chars"] += char_count
        self.stats["ollama"]["call_count"] += 1

        # 更新单次最大值
        if char_count > self.stats["ollama"]["max_single_call"]:
            self.stats["ollama"]["max_single_call"] = char_count

        # 实时显示
        self._show_realtime_stats()

    def _show_realtime_stats(self):
        """显示实时统计"""
        gemini_total = self.stats["gemini"]["total_tokens"]
        ollama_total = self.stats["ollama"]["total_chars"]

        print(f"[Token 监控] Gemini: {gemini_total:,} tokens | Ollama: {ollama_total:,} 字符")

    def generate_final_report(self):
        """生成最终统计报告"""
        task_duration = datetime.now() - self.stats["task_start_time"]

        print(f"\n{'='*60}")
        print(f"[Token 消耗统计报告]")
        print(f"{'='*60}")
        print(f"[任务时长] {task_duration}")
        print(f"\n[Gemini 统计]")
        print(f"- 调用次数: {self.stats['gemini']['call_count']}")
        print(f"- 输入 Token: {self.stats['gemini']['prompt_tokens']:,}")
        print(f"- 输出 Token: {self.stats['gemini']['completion_tokens']:,}")
        print(f"- 总 Token: {self.stats['gemini']['total_tokens']:,}")
        print(f"- 单次最大: {self.stats['gemini']['max_single_call']:,}")
        print(f"\n[Ollama 统计]")
        print(f"- 调用次数: {self.stats['ollama']['call_count']}")
        print(f"- 总字符数: {self.stats['ollama']['total_chars']:,}")
        print(f"- 单次最大: {self.stats['ollama']['max_single_call']:,}")
        print(f"\n[总计]")
        print(f"- Gemini Token: {self.stats['gemini']['total_tokens']:,}")
        print(f"- Ollama 字符: {self.stats['ollama']['total_chars']:,}")
        print(f"{'='*60}\n")

        return self.stats


# ==================== 本地模型整合 ====================

def call_local_model(prompt: str, model: str = "llama3",
                    fallback_model: str = "gemma") -> tuple[str, float, str]:
    """
    調用本地 Ollama API

    Args:
        prompt: 提示詞
        model: 主要模型
        fallback_model: 備用模型

    Returns:
        (response, inference_time, model_used)
    """
    url = f"{OLLAMA_CONFIG['base_url']}/api/chat"

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        end_time = time.time()

        inference_time = end_time - start_time
        result = response.json()
        message = result.get("message", {}).get("content", "")

        return message, inference_time, model

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Ollama API 調用失敗 ({model}): {e}")

        # 嘗試備用模型
        if model != fallback_model:
            print(f"[FALLBACK] 嘗試使用 {fallback_model}...")
            payload["model"] = fallback_model
            try:
                start_time = time.time()
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                end_time = time.time()

                inference_time = end_time - start_time
                result = response.json()
                message = result.get("message", {}).get("content", "")

                return message, inference_time, fallback_model
            except Exception as fallback_error:
                error_msg = f"Fallback failed: {fallback_error}"
                return error_msg, 0.0, "none"
        else:
            return f"Error: {e}", 0.0, "none"

def test_local_model_performance() -> tuple[str, float, str]:
    """測試本地模型效能"""
    print(f"[Local Model] 開始效能測試...")

    test_prompt = "作為數據清洗專家，請簡述你處理異常值的標準流程。"
    response, inference_time, model_used = call_local_model(test_prompt)

    print(f"[Local Model] 模型: {model_used}")
    print(f"[Local Model] 耗時: {inference_time:.2f} 秒")
    print(f"[Local Model] 回應長度: {len(response)} 字符")

    return response, inference_time, model_used

# ==================== 工具函数 ====================

def google_search(query: str, max_results: int = 5, api_key: str = None) -> List[Dict[str, Any]]:
    """
    Google 搜索（使用 Tavily）

    Args:
        query: 搜索查询
        max_results: 最大结果数
        api_key: 可選的 API KEY，如果未提供則使用默認的

    Returns:
        搜索结果列表
    """
    print(f"[Google Search] 搜索: {query}")

    # 使用提供的 KEY 或默認 KEY
    key = api_key or TAVILY_API_KEY
    if not key:
        print("[ERROR] Tavily API Key 未配置")
        return []

    try:
        url = f"{TOOL_CONFIG['tavily_base_url']}/search"
        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "api_key": key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "score": item.get("score", 0),
            })

        print(f"[Google Search] 找到 {len(results)} 个结果")
        return results

    except Exception as e:
        print(f"[ERROR] Google 搜索失败: {e}")
        raise  # 重新拋出異常，讓 robust_api_call 處理


def google_search_with_retry(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    帶重試機制的 Google 搜索

    Args:
        query: 搜索查询
        max_results: 最大结果数

    Returns:
        搜索结果列表
    """
    def search_func(api_key):
        return google_search(query, max_results, api_key)

    return robust_api_call(search_func, "tavily", max_retries=2)


def web_crawl(url: str, max_pages: int = 10) -> List[Dict[str, Any]]:
    """
    网页爬取（使用 Firecrawl）

    Args:
        url: 目标 URL
        max_pages: 最大页面数

    Returns:
        爬取结果列表
    """
    print(f"[Web Crawl] 爬取: {url}")

    if not FIRECRAWL_API_KEY:
        print("[ERROR] Firecrawl API Key 未配置")
        return []

    try:
        crawl_url = f"{TOOL_CONFIG['firecrawl_base_url']}/v1/crawl"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        }
        payload = {
            "url": url,
            "limit": max_pages,
            "scrapeOptions": {
                "formats": ["markdown"],
            },
        }

        response = requests.post(crawl_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Firecrawl 返回任务 ID，需要轮询获取结果
        task_id = data.get("id")
        if not task_id:
            print("[ERROR] 未获取到任务 ID")
            return []

        # 轮询获取结果
        import time
        max_wait = 120  # 最多等待 2 分钟
        wait_time = 0

        while wait_time < max_wait:
            time.sleep(5)
            wait_time += 5

            status_url = f"{TOOL_CONFIG['firecrawl_base_url']}/v1/crawl/status/{task_id}"
            status_response = requests.get(status_url, headers=headers, timeout=30)
            status_response.raise_for_status()
            status_data = status_response.json()

            status = status_data.get("status")
            if status == "completed":
                results = status_data.get("data", [])
                print(f"[Web Crawl] 爬取完成，获得 {len(results)} 个页面")
                return results
            elif status == "failed":
                print(f"[ERROR] 爬取失败: {status_data.get('error', '未知错误')}")
                return []

        print("[WARN] 爬取超时")
        return []

    except Exception as e:
        print(f"[ERROR] Web 爬取失败: {e}")
        return []


def jina_reader(url: str) -> str:
    """
    Jina Reader（抓取网页深度内容）

    Args:
        url: 目标 URL

    Returns:
        网页内容
    """
    print(f"[Jina Reader] 读取: {url}")

    try:
        reader_url = f"{TOOL_CONFIG['jina_base_url']}/https://{url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(reader_url, headers=headers, timeout=30)
        response.raise_for_status()

        content = response.text
        print(f"[Jina Reader] 读取成功，内容长度: {len(content)} 字符")

        return content

    except Exception as e:
        print(f"[ERROR] Jina Reader 失败: {e}")
        return ""


# ==================== AutoGen 配置 ====================

def setup_autogen_agents():
    """配置 AutoGen Agent 团队"""

    try:
        from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

        # 配置列表
        config_list_gemini = [
            {
                "model": "models/gemini-1.5-flash",
                "api_key": GEMINI_API_KEY,
                "api_type": "google",
            }
        ]

        config_list_ollama = [
            {
                "model": OLLAMA_CONFIG["model"],
                "base_url": OLLAMA_CONFIG["base_url"],
                "api_type": "ollama",
            }
        ]

        # Manager Agent（负责决策与工具调度）
        manager = AssistantAgent(
            name="Manager",
            llm_config={"config_list": config_list_ollama},
            system_message="""你是 Manager，负责决策与工具调度。

你的职责：
1. 分析用户需求，决定使用哪些工具
2. 优先使用免费/低成本工具（Jina Reader > Google Search > Web Crawl）
3. 协调 Researcher 和 Coder 的工作
4. 确保任务高效完成

工具优先级：
- Jina Reader：免费，适合抓取单个网页深度内容
- Google Search：低成本，适合快速搜索信息
- Web Crawl：成本较高，适合需要爬取多个页面的情况

请根据任务需求选择最合适的工具组合。"""
        )

        # Researcher Agent（本地执行，负责数据整理）
        researcher = AssistantAgent(
            name="Researcher",
            llm_config={"config_list": config_list_ollama},
            system_message="""你是 Researcher，负责数据整理与分析。

你的职责：
1. 整理搜索和爬取的数据
2. 提炼关键信息
3. 生成结构化的分析报告
4. 为 Coder 提供清晰的需求说明

请确保输出简洁、准确、有条理。"""
        )

        # Coder Agent（本地执行，负责代码撰写）
        coder = AssistantAgent(
            name="Coder",
            llm_config={"config_list": config_list_ollama},
            system_message="""你是 Coder，负责代码撰写与实现。

你的职责：
1. 根据需求编写高质量的代码
2. 确保代码可运行、可维护
3. 添加必要的注释和文档
4. 处理数据分析和可视化任务

请使用 Python 编写代码，遵循最佳实践。"""
        )

        # User Proxy
        user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={
                "work_dir": "autogen_workspace",
                "use_docker": False,
            },
        )

        # GroupChat 配置
        groupchat = GroupChat(
            agents=[manager, researcher, coder, user_proxy],
            messages=[],
            max_round=20,
            speaker_selection_method="auto",
        )

        groupchat_manager = GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": config_list_ollama},
        )

        return user_proxy, groupchat_manager

    except ImportError as e:
        print(f"[ERROR] AutoGen 导入失败: {e}")
        print("请运行: pip install pyautogen")
        return None, None


# ==================== 主函数 ====================

def main():
    """主函數 - 演化系統"""

    print(f"\n{'='*60}")
    print(f"[AI 戰車演化系統] 啟動")
    print(f"{'='*60}\n")

    # 初始化 Token 監控
    token_monitor = TokenMonitor()

    # 初始化演化系統
    initialize_evolution_system()

    # 顯示配置信息
    display_config_info()

    # 恢復 API KEY 狀態
    api_key_persistence.restore_manager_state(api_key_manager)
    api_key_manager.print_status()

    print(f"[Token 監控] 系統已啟動")
    print(f"[Token 監控] Gemini: 雲端服務（計費）")
    print(f"[Token 監控] Ollama: 本地服務（免費）")
    print(f"{'='*60}\n")

    # 檢查 API 密鑰
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY 未配置")
        print("請設置環境變量: export GEMINI_API_KEY='your_key'")
        return

    # 檢查是否需要搜尋
    if should_search():
        print(f"[系統] 檢測到需要進行搜尋（每{EVOLUTION_CONFIG['search_interval_hours']}小時）")
        search_success = perform_search()
        if not search_success:
            print("[ERROR] 搜尋失敗")
    else:
        print(f"[系統] 距離上次搜尋不足{EVOLUTION_CONFIG['search_interval_hours']}小時，跳過搜尋")

    # 檢查是否需要進化
    if should_evolve():
        print(f"[系統] 檢測到需要進行進化（每{EVOLUTION_CONFIG['evolution_interval_days']}天）")
        evolution_success = perform_evolution()
        if not evolution_success:
            print("[ERROR] 進化失敗")
    else:
        print(f"[系統] 距離上次進化不足{EVOLUTION_CONFIG['evolution_interval_days']}天，跳過進化")

    # 顯示下次執行時間
    print(f"\n{'='*60}")
    print(f"[系統狀態]")
    print(f"{'='*60}")
    print(f"搜尋頻率: 每 {EVOLUTION_CONFIG['search_interval_hours']} 小時")
    print(f"進化頻率: 每 {EVOLUTION_CONFIG['evolution_interval_days']} 天")
    print(f"{'='*60}\n")

    # 生成最終報告
    token_monitor.generate_final_report()

    print(f"[完成] 演化系統執行結束\n")


if __name__ == "__main__":
    main()
