# Path: C:\Users\666LAG\Desktop\AI_Project\Library\lesson_04_tool_use.py

import torch
import asyncio
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# -----------------------------------------------------------------------------
# 1. 工具定義 (Business Logic: 木地板庫存查詢)
# -----------------------------------------------------------------------------
def query_flooring_inventory(material: str) -> str:
    """查詢特定材質木地板的庫存狀態"""
    inventory = {
        "橡木": "庫存充足，剩餘 500 平方米",
        "胡桃木": "庫存緊張，剩餘 20 平方米",
        "柚木": "已售罄"
    }
    return inventory.get(material, "查無此材質資訊")

TOOLS = {
    "query_flooring_inventory": query_flooring_inventory
}

# -----------------------------------------------------------------------------
# 2. 本地 AI Agent 核心架構 (針對 RTX 2060 6GB 優化)
# -----------------------------------------------------------------------------
class LocalToolAgent:
    def __init__(self, model_id: str = "meta-llama/Llama-3.2-3B-Instruct"):
        # 關鍵優化：強制使用 4-bit 量化
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )

        print(f"Loading model {model_id} with 4-bit quantization...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map="auto"
        )
        torch.cuda.empty_cache()

    async def _async_generate(self, prompt: str) -> str:
        def _generate():
            inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = self.model.generate(**inputs, max_new_tokens=150)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        result = await asyncio.to_thread(_generate)
        torch.cuda.empty_cache()
        return result

    async def run_agent_loop(self, user_input: str):
        print(f"\n[Agent] 處理請求: {user_input}")
        
        # 模擬 Agent 決定呼叫工具
        if "庫存" in user_input:
            print("[Agent] 判定需要執行工具: query_flooring_inventory")
            material = "橡木" if "橡木" in user_input else "胡桃木"
            tool_result = await asyncio.to_thread(TOOLS["query_flooring_inventory"], material)
            print(f"[Tool Output] {tool_result}")
            return f"根據系統查詢，{material} 的狀態為: {tool_result}"
        
        return "無需執行工具，AI 直接回答。"

# -----------------------------------------------------------------------------
# 3. 測試執行
# -----------------------------------------------------------------------------
async def main():
    try:
        agent = LocalToolAgent()
        user_query = "幫我查一下橡木地板還有多少庫存？"
        response = await agent.run_agent_loop(user_query)
        
        print("-" * 30)
        print(f"Final Response: {response}")
        print("-" * 30)
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        torch.cuda.empty_cache()

if __name__ == "__main__":
    asyncio.run(main())