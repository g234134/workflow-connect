# 補全型 (Completion) ReAct 提示詞模板
ENGLISH_REACT_COMPLETION_PROMPT_TEMPLATES = """Respond to the human as helpfully and accurately as possible.

{{instruction}}

You have access to the following tools:

{{tools}}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).
Valid "action" values: "Final Answer" or {{tool_names}}

Provide only ONE action per $JSON_BLOB.

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond
Action:
```
{
  "action": "Final Answer",
  "action_input": "Final response to human"
}
```

Begin! 
Reminder:
1. ALWAYS respond with a valid json blob.
2. If a tool returns an error or "not found", DO NOT repeat the same call. Try a different approach or give a Final Answer.
3. Keep your thoughts concise to save space.

{{historic_messages}}
Question: {{query}}
{{agent_scratchpad}}
Thought:"""  # noqa: E501


# 思考過程暫存模板 (Scratchpad)
ENGLISH_REACT_COMPLETION_AGENT_SCRATCHPAD_TEMPLATES = """Observation: {{observation}}
Thought:"""


# 對話型 (Chat) ReAct 提示詞模板
ENGLISH_REACT_CHAT_PROMPT_TEMPLATES = """Respond to the human as helpfully and accurately as possible.

{{instruction}}

You have access to the following tools:

{{tools}}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).
Valid "action" values: "Final Answer" or {{tool_names}}

Provide only ONE action per $JSON_BLOB, as shown:

```
{
  "action": $TOOL_NAME,
  "action_input": $ACTION_INPUT
}
```

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond
Action:
```
{
  "action": "Final Answer",
  "action_input": "Final response to human"
}