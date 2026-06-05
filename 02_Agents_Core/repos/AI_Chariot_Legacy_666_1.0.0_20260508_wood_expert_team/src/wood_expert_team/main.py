#!/usr/bin/env python
import sys
import warnings
from wood_expert_team.crew import WoodExpertTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    執行 CrewAI 團隊任務並輸出 Token 消耗數據。
    """
    inputs = {
        'topic': '2026 台灣木地板市場競爭力分析'
    }
    try:
        # 獲取執行結果對象
        result = WoodExpertTeam().crew().kickoff(inputs=inputs)
        
        # --- 監控儀表板 ---
        print("\n" + "="*50)
        print("📊 LOCAL OLLAMA 執行統計報告")
        print("="*50)
        print(f"✅ 最終任務狀態: 成功")
        print(f"📝 總 Prompt Tokens    : {result.token_usage.prompt_tokens}")
        print(f"✍️ 總 Completion Tokens: {result.token_usage.completion_tokens}")
        print(f"🚀 總計 Token 消耗     : {result.token_usage.total_tokens}")
        print("="*50 + "\n")
        
    except Exception as e:
        raise Exception(f"執行期間發生錯誤: {e}")

if __name__ == "__main__":
    run()