import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Generator, Mapping, Sequence
from typing import Any, TypedDict

from graphon.model_runtime.entities.llm_entities import LLMResult, LLMResultChunk, LLMResultChunkDelta, LLMUsage
from graphon.model_runtime.entities.message_entities import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)

from core.agent.base_agent_runner import BaseAgentRunner
from core.agent.entities import AgentScratchpadUnit
from core.agent.errors import AgentMaxIterationError
from core.agent.output_parser.cot_output_parser import CotAgentOutputParser
from core.app.apps.base_app_queue_manager import PublishFrom
from core.app.entities.queue_entities import QueueAgentThoughtEvent, QueueMessageEndEvent, QueueMessageFileEvent
from core.ops.ops_trace_manager import TraceQueueManager
from core.prompt.agent_history_prompt_transform import AgentHistoryPromptTransform
from core.tools.__base.tool import Tool
from core.tools.entities.tool_entities import ToolInvokeMeta
from core.tools.tool_engine import ToolEngine
from models.model import Message

logger = logging.getLogger(__name__)

# --- 核心優化常數 ---
MAX_OBSERVATION_LENGTH = 3000  # 限制工具回傳的最大字元數，防止上下文溢出
MAX_HISTORY_STEPS = 10         # 限制保留的歷史思維步數，節省 Token 並維持推理專注度

class ActionDict(TypedDict):
    """AgentScratchpadUnit.Action.to_dict() 產生的結構體。"""
    action: str
    action_input: dict[str, Any] | str

class CotAgentRunner(BaseAgentRunner, ABC):
    _is_first_iteration = True
    _ignore_observation_providers = ["wenxin"]
    _historic_prompt_messages: list[PromptMessage]
    _agent_scratchpad: list[AgentScratchpadUnit]
    _instruction: str
    _query: str
    _prompt_messages_tools: Sequence[PromptMessageTool]

    def run(self, message: Message, query: str, inputs: Mapping[str, str]) -> Generator:
        app_generate_entity = self.application_generate_entity
        self._repack_app_generate_entity(app_generate_entity)
        self._init_react_state(query)
        trace_manager = app_generate_entity.trace_manager

        if "Observation" not in app_generate_entity.model_conf.stop:
            if app_generate_entity.model_conf.provider not in self._ignore_observation_providers:
                app_generate_entity.model_conf.stop.append("Observation")

        app_config = self.app_config
        assert app_config.agent

        inputs = inputs or {}
        instruction = app_config.prompt_template.simple_prompt_template or ""
        self._instruction = self._fill_in_inputs_from_external_data_tools(instruction, inputs)

        iteration_step = 1
        max_iteration_steps = min(app_config.agent.max_iteration, 99) + 1
        tool_instances, prompt_messages_tools = self._init_prompt_tools()
        self._prompt_messages_tools = prompt_messages_tools

        function_call_state = True
        llm_usage: dict[str, LLMUsage | None] = {"usage": None}
        final_answer = ""
        prompt_messages: list = []
        agent_thought_id = ""

        def increase_usage(final_llm_usage_dict: dict[str, LLMUsage | None], usage: LLMUsage):
            if not final_llm_usage_dict["usage"]:
                final_llm_usage_dict["usage"] = usage
            else:
                u = final_llm_usage_dict["usage"]
                u.prompt_tokens += usage.prompt_tokens
                u.completion_tokens += usage.completion_tokens
                u.total_tokens += usage.total_tokens
                u.prompt_price += usage.prompt_price
                u.completion_price += usage.completion_price
                u.total_price += usage.total_price

        model_instance = self.model_instance

        while function_call_state and iteration_step <= max_iteration_steps:
            function_call_state = False
            if iteration_step == max_iteration_steps:
                self._prompt_messages_tools = []

            message_file_ids: list[str] = []
            agent_thought_id = self.create_agent_thought(
                message_id=message.id, message="", tool_name="", tool_input="", messages_ids=message_file_ids
            )

            if iteration_step > 1:
                self.queue_manager.publish(QueueAgentThoughtEvent(agent_thought_id=agent_thought_id), PublishFrom.APPLICATION_MANAGER)

            prompt_messages = self._organize_prompt_messages()
            self.recalc_llm_max_tokens(self.model_config, prompt_messages)
            chunks = model_instance.invoke_llm(
                prompt_messages=prompt_messages,
                model_parameters=app_generate_entity.model_conf.parameters,
                tools=[],
                stop=app_generate_entity.model_conf.stop,
                stream=True,
                callbacks=[],
            )

            usage_dict: dict[str, LLMUsage | None] = {}
            react_chunks = CotAgentOutputParser.handle_react_stream_output(chunks, usage_dict)
            scratchpad = AgentScratchpadUnit(agent_response="", thought="", action_str="", observation="", action=None)

            if iteration_step == 1:
                self.queue_manager.publish(QueueAgentThoughtEvent(agent_thought_id=agent_thought_id), PublishFrom.APPLICATION_MANAGER)

            for chunk in react_chunks:
                if isinstance(chunk, AgentScratchpadUnit.Action):
                    action = chunk
                    scratchpad.agent_response += json.dumps(chunk.model_dump(), ensure_ascii=False)
                    scratchpad.action_str = json.dumps(chunk.model_dump(), ensure_ascii=False)
                    scratchpad.action = action
                else:
                    scratchpad.agent_response += chunk
                    scratchpad.thought += chunk
                    yield LLMResultChunk(
                        model=self.model_config.model,
                        prompt_messages=prompt_messages,
                        delta=LLMResultChunkDelta(index=0, message=AssistantPromptMessage(content=chunk), usage=None),
                        system_fingerprint="",
                    )

            scratchpad.thought = scratchpad.thought.strip() or "Thinking..."
            self._agent_scratchpad.append(scratchpad)

            if iteration_step == max_iteration_steps and scratchpad.action:
                if scratchpad.action.action_name.lower() != "final answer":
                    raise AgentMaxIterationError(app_config.agent.max_iteration)

            if "usage" in usage_dict and usage_dict["usage"]:
                increase_usage(llm_usage, usage_dict["usage"])

            self.save_agent_thought(
                agent_thought_id=agent_thought_id,
                tool_name=(scratchpad.action.action_name if scratchpad.action and not scratchpad.is_final() else ""),
                tool_input={scratchpad.action.action_name: scratchpad.action.action_input} if scratchpad.action else {},
                tool_invoke_meta={},
                thought=scratchpad.thought or "",
                observation="",
                answer=scratchpad.agent_response or "",
                messages_ids=[],
                llm_usage=usage_dict.get("usage"),
            )

            if not scratchpad.is_final():
                self.queue_manager.publish(QueueAgentThoughtEvent(agent_thought_id=agent_thought_id), PublishFrom.APPLICATION_MANAGER)

            if not scratchpad.action:
                final_answer = ""
            else:
                if scratchpad.action.action_name.lower() == "final answer":
                    val = scratchpad.action.action_input
                    final_answer = json.dumps(val, ensure_ascii=False) if isinstance(val, dict) else str(val)
                else:
                    function_call_state = True
                    tool_invoke_response, tool_invoke_meta = self._handle_invoke_action(
                        action=scratchpad.action,
                        tool_instances=tool_instances,
                        message_file_ids=message_file_ids,
                        trace_manager=trace_manager,
                    )
                    scratchpad.observation = tool_invoke_response
                    scratchpad.agent_response = tool_invoke_response

                    self.save_agent_thought(
                        agent_thought_id=agent_thought_id,
                        tool_name=scratchpad.action.action_name,
                        tool_input={scratchpad.action.action_name: scratchpad.action.action_input},
                        thought=scratchpad.thought or "",
                        observation={scratchpad.action.action_name: tool_invoke_response},
                        tool_invoke_meta={scratchpad.action.action_name: tool_invoke_meta.to_dict()},
                        answer=scratchpad.agent_response,
                        messages_ids=message_file_ids,
                        llm_usage=usage_dict.get("usage"),
                    )
                    self.queue_manager.publish(QueueAgentThoughtEvent(agent_thought_id=agent_thought_id), PublishFrom.APPLICATION_MANAGER)

                for prompt_tool in self._prompt_messages_tools:
                    self.update_prompt_message_tool(tool_instances[prompt_tool.name], prompt_tool)

            iteration_step += 1

        yield LLMResultChunk(
            model=model_instance.model_name,
            prompt_messages=prompt_messages,
            delta=LLMResultChunkDelta(index=0, message=AssistantPromptMessage(content=final_answer), usage=llm_usage["usage"]),
            system_fingerprint="",
        )

        self.save_agent_thought(agent_thought_id=agent_thought_id, tool_name="", tool_input={}, tool_invoke_meta={},
                                thought=final_answer, observation={}, answer=final_answer, messages_ids=[])
        
        self.queue_manager.publish(QueueMessageEndEvent(llm_result=LLMResult(
            model=model_instance.model_name, prompt_messages=prompt_messages, 
            message=AssistantPromptMessage(content=final_answer), usage=llm_usage["usage"] or LLMUsage.empty_usage(),
            system_fingerprint=""
        )), PublishFrom.APPLICATION_MANAGER)

    def _handle_invoke_action(self, action, tool_instances, message_file_ids, trace_manager=None) -> tuple[str, ToolInvokeMeta]:
        tool_call_name = action.action_name
        tool_call_args = action.action_input
        tool_instance = tool_instances.get(tool_call_name)
        if not tool_instance:
            answer = f"there is not a tool named {tool_call_name}"
            return answer, ToolInvokeMeta.error_instance(answer)

        if isinstance(tool_call_args, str):
            try: tool_call_args = json.loads(tool_call_args)
            except: pass

        tool_invoke_response, message_files, tool_invoke_meta = ToolEngine.agent_invoke(
            tool=tool_instance, tool_parameters=tool_call_args, user_id=self.user_id,
            tenant_id=self.tenant_id, message=self.message, invoke_from=self.application_generate_entity.invoke_from,
            agent_tool_callback=self.agent_callback, trace_manager=trace_manager,
        )

        # --- 優化 1：內容截斷防止 Token 溢出 ---
        if len(tool_invoke_response) > MAX_OBSERVATION_LENGTH:
            tool_invoke_response = tool_invoke_response[:MAX_OBSERVATION_LENGTH] + "\n...[內容因過長已自動截斷]"

        for message_file_id in message_files:
            self.queue_manager.publish(QueueMessageFileEvent(message_file_id=message_file_id), PublishFrom.APPLICATION_MANAGER)
            message_file_ids.append(message_file_id)
        return tool_invoke_response, tool_invoke_meta

    def _organize_historic_prompt_messages(self, current_session_messages=None) -> list[PromptMessage]:
        result: list[PromptMessage] = []
        scratchpads: list[AgentScratchpadUnit] = []
        current_scratchpad = None

        for message in self.history_prompt_messages:
            if isinstance(message, AssistantPromptMessage):
                if not current_scratchpad:
                    current_scratchpad = AgentScratchpadUnit(agent_response=str(message.content), thought=str(message.content), action_str="", action=None, observation=None)
                    scratchpads.append(current_scratchpad)
                if message.tool_calls:
                    try:
                        current_scratchpad.action = AgentScratchpadUnit.Action(
                            action_name=message.tool_calls[0].function.name,
                            action_input=json.loads(message.tool_calls[0].function.arguments))
                        current_scratchpad.action_str = json.dumps(current_scratchpad.action.to_dict(), ensure_ascii=False)
                    except: pass
            elif isinstance(message, ToolPromptMessage):
                if current_scratchpad: current_scratchpad.observation = str(message.content)
            elif isinstance(message, UserPromptMessage):
                if scratchpads:
                    result.append(AssistantPromptMessage(content=self._format_assistant_message(scratchpads)))
                    scratchpads, current_scratchpad = [], None
                result.append(message)

        if scratchpads:
            result.append(AssistantPromptMessage(content=self._format_assistant_message(scratchpads)))

        # --- 優化 2：滑動窗口機制限制歷史訊息條數 ---
        if len(result) > MAX_HISTORY_STEPS:
            # 保留最初的系統訊息與最近的對話內容
            sys_msgs = [m for m in result if isinstance(m, SystemPromptMessage)]
            other_msgs = [m for m in result if not isinstance(m, SystemPromptMessage)]
            result = sys_msgs + other_msgs[-MAX_HISTORY_STEPS:]

        return AgentHistoryPromptTransform(
            model_config=self.model_config, prompt_messages=current_session_messages or [],
            history_messages=result, memory=self.memory,
        ).get_prompt()

    @abstractmethod
    def _organize_prompt_messages(self) -> list[PromptMessage]: pass
    def _convert_dict_to_action(self, action: ActionDict) -> AgentScratchpadUnit.Action:
        return AgentScratchpadUnit.Action(action_name=action["action"], action_input=action["action_input"])
    def _fill_in_inputs_from_external_data_tools(self, instruction: str, inputs: Mapping[str, Any]) -> str:
        for k, v in inputs.items():
            try: instruction = instruction.replace(f"{{{{{k}}}}}", str(v))
            except: continue
        return instruction
    def _init_react_state(self, query):
        self._query, self._agent_scratchpad = query, []
        self._historic_prompt_messages = self._organize_historic_prompt_messages()
    def _format_assistant_message(self, agent_scratchpad: list[AgentScratchpadUnit]) -> str:
        message = ""
        for s in agent_scratchpad:
            if s.is_final(): message += f"Final Answer: {s.agent_response}"
            else:
                message += f"Thought: {s.thought}\n\n"
                if s.action_str: message += f"Action: {s.action_str}\n\n"
                if s.observation: message += f"Observation: {s.observation}\n\n"
        return message