import json
import re
from collections.abc import Generator
from typing import Union

from graphon.model_runtime.entities.llm_entities import LLMResultChunk

from core.agent.entities import AgentScratchpadUnit


class CotAgentOutputParser:
    @classmethod
    def handle_react_stream_output(
        cls, llm_response: Generator[LLMResultChunk, None, None], usage_dict: dict
    ) -> Generator[Union[str, AgentScratchpadUnit.Action], None, None]:
        
        def parse_action(action) -> Union[str, AgentScratchpadUnit.Action]:
            """
            解析模型輸出的 Action 區塊，並具備修復不規範 JSON 的能力。
            即使模型在 JSON 前後輸出廢話，也能準確提取。
            """
            action_name = None
            action_input = None
            
            if isinstance(action, str):
                # 1. 基礎清理：去除前後空白
                cleaned_action = action.strip()
                
                # 2. 移除可能的 Markdown JSON 標籤 (例如 ```json ... ```)
                cleaned_action = re.sub(r'^