import sys
import warnings
from code_expert_team.crew import CodeExpertTeam

# 隱藏警告
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    inputs = {
        'code_snippet': '請分析我的網頁 index.html 結構是否符合 SEO 標準。'
    }
    try:
        print("\n🚀 啟動：前端代碼優化團隊...\n")
        result = CodeExpertTeam().crew().kickoff(inputs=inputs)
        
        print("\n" + "="*50)
        print("🖥️  代碼專家團隊 - LOCAL OLLAMA 執行統計")
        print("="*50)
        print(f"✅ 任務狀態：執行完成")
        print(f"🚀 總計 Token 消耗 : {result.token_usage.total_tokens}")
        print("="*50 + "\n")
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")

if __name__ == "__main__":
    run()
