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
            """
            action_name = None
            action_input = None
            
            if isinstance(action, str):
                # 強化清理：去除前後空白並移除 Markdown 的 JSON 標籤
                cleaned_action = action.strip()
                cleaned_action = re.sub(r'^