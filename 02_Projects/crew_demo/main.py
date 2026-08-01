"""
CrewAI 多代理範例
- 兩個代理：研究員（researcher）+ 撰稿者（writer）
- 模型可在 .env 用 LLM_PROVIDER 切換：ollama / groq / nvidia / huggingface
- 工具可在 .env 用 ENABLE_TOOLS=true 啟用：Tavily / Firecrawl
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM


load_dotenv()


def build_llm() -> LLM:
    provider = os.environ.get("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "ollama":
        return LLM(
            model=f"ollama/{os.environ.get('OLLAMA_MODEL', 'llama3.1:latest')}",
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            temperature=0.4,
        )

    if provider == "groq":
        _require("GROQ_API_KEY")
        return LLM(
            model=f"groq/{os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')}",
            api_key=os.environ["GROQ_API_KEY"],
            temperature=0.4,
        )

    if provider == "nvidia":
        _require("NVIDIA_NIM_API_KEY")
        return LLM(
            model=f"nvidia_nim/{os.environ.get('NVIDIA_NIM_MODEL', 'meta/llama-3.3-70b-instruct')}",
            api_key=os.environ["NVIDIA_NIM_API_KEY"],
            temperature=0.4,
        )

    if provider == "huggingface":
        _require("HUGGINGFACE_API_KEY")
        return LLM(
            model=f"huggingface/{os.environ.get('HUGGINGFACE_MODEL', 'meta-llama/Llama-3.3-70B-Instruct')}",
            api_key=os.environ["HUGGINGFACE_API_KEY"],
            temperature=0.4,
        )

    raise ValueError(
        f"未知的 LLM_PROVIDER：{provider!r}；可用值：ollama / groq / nvidia / huggingface"
    )


def _require(name: str) -> None:
    if not os.environ.get(name):
        sys.exit(f"[錯誤] .env 缺少 {name}，無法使用此供應商。")


def build_tools() -> list:
    if os.environ.get("ENABLE_TOOLS", "false").strip().lower() != "true":
        return []

    tools: list = []

    if os.environ.get("TAVILY_API_KEY"):
        try:
            from crewai_tools import TavilySearchTool

            tools.append(TavilySearchTool())
        except Exception as exc:
            print(f"[警告] Tavily 工具載入失敗：{exc}")

    if os.environ.get("FIRECRAWL_API_KEY"):
        try:
            from crewai_tools import FirecrawlScrapeWebsiteTool

            tools.append(FirecrawlScrapeWebsiteTool())
        except Exception as exc:
            print(f"[警告] Firecrawl 工具載入失敗：{exc}")

    return tools


def main() -> None:
    topic = os.environ.get("TOPIC", "人工智慧的歷史")
    llm = build_llm()
    tools = build_tools()

    print(f"[INFO] LLM_PROVIDER = {os.environ.get('LLM_PROVIDER', 'ollama')}")
    print(f"[INFO] ENABLE_TOOLS = {os.environ.get('ENABLE_TOOLS', 'false')}")
    print(f"[INFO] 工具數量      = {len(tools)}")
    print(f"[INFO] 主題          = {topic}\n")

    researcher = Agent(
        role="研究員",
        goal=f"針對主題「{topic}」蒐集 5 條最重要的事實或里程碑，每條一行、不重複。",
        backstory="你是一位中文研究員，擅長以條列方式整理重點，用詞精確。",
        llm=llm,
        tools=tools,
        allow_delegation=False,
        verbose=True,
    )

    writer = Agent(
        role="撰稿者",
        goal="根據研究員提供的要點，寫一段 200~300 字的繁體中文摘要。",
        backstory="你是一位中文撰稿者，擅長把要點整合成易讀段落，風格平實。",
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )

    research_task = Task(
        description=(
            f"請針對主題：{topic}\n"
            "輸出 5 條重點，每條一行，使用 '-' 開頭，不要加多餘說明。"
            "若你有可用工具，可使用工具上網查證。"
        ),
        expected_output="5 行，每行一條重點。",
        agent=researcher,
    )

    write_task = Task(
        description=(
            "依據研究員給的 5 條重點，撰寫 200~300 字的繁體中文摘要。\n"
            "要求：流暢、不要再用條列、不要加多餘前言或結語。"
        ),
        expected_output="一段 200~300 字的繁體中文摘要。",
        agent=writer,
        context=[research_task],
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff(inputs={"topic": topic})

    out_path = os.path.join(os.path.dirname(__file__), "output.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"主題：{topic}\n")
        f.write(f"供應商：{os.environ.get('LLM_PROVIDER', 'ollama')}\n\n")
        f.write(str(result))
    print(f"\n[OK] 結果已寫入：{out_path}")


if __name__ == "__main__":
    main()
