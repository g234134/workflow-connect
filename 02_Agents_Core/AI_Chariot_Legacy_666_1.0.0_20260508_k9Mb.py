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
2. If a tool returns an error or "not found", DO NOT repeat the same call. Try another tool or give Final Answer.
3. Be concise.

{{historic_messages}}
Question: {{query}}
{{agent_scratchpad}}
Thought:"""

ENGLISH_REACT_COMPLETION_AGENT_SCRATCHPAD_TEMPLATES = """Observation: {{observation}}
Thought:"""

ENGLISH_REACT_CHAT_PROMPT_TEMPLATES = """Respond to the human as helpfully and accurately as possible.

{{instruction}}

You have access to the following tools:

{{tools}}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).
Valid "action" values: "Final Answer" or {{tool_names}}

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
{
  "action": $TOOL_NAME,
  "action_input": $ACTION_INPUT
}
```
Observation: action result
... (repeat Thought/Action/Observation N times)
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
2. If a tool fails, DO NOT repeat it. Try something else.
"""

ENGLISH_REACT_CHAT_AGENT_SCRATCHPAD_TEMPLATES = ""

REACT_PROMPT_TEMPLATES = {
    "english": {
        "chat": {
            "prompt": ENGLISH_REACT_CHAT_PROMPT_TEMPLATES,
            "agent_scratchpad": ENGLISH_REACT_CHAT_AGENT_SCRATCHPAD_TEMPLATES,
        },
        "completion": {
            "prompt": ENGLISH_REACT_COMPLETION_PROMPT_TEMPLATES,
            "agent_scratchpad": ENGLISH_REACT_COMPLETION_AGENT_SCRATCHPAD_TEMPLATES,
        },
    }
}