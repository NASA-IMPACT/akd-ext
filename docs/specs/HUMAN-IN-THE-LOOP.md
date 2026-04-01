# Human-in-the-Loop (HITL)

## Overview

`HumanTool` (`akd.tools.human.HumanTool`) is an AKD tool that enables agents to pause execution and request input from a human. When the LLM calls the `ask_human` tool, the agent stream emits a `HUMAN_INPUT_REQUIRED` event and stops. The caller collects the human's answer and resumes the agent with a `RunContext`.

## Enabling HITL

Add `HumanTool()` to the agent's tools list. Include guidance in the system prompt so the model knows when to ask:

```python
from akd.tools.human import HumanTool
from akd_ext.agents import OpenAIBaseAgentConfig

config = OpenAIBaseAgentConfig(
    system_prompt="You are a helpful assistant. Ask the user for clarification when the request is ambiguous.",
    tools=[HumanTool()],
)
```

`HumanTool` is a `BaseTool` subclass, so it goes through the same auto-conversion path as any AKD tool — no special wiring needed.

## Event Flow

```
Agent streaming
    |
    v
LLM calls `ask_human` tool
    |
    v
Agent emits HUMAN_INPUT_REQUIRED event
  - event.data.tool_call_id   -> needed for resumption
  - event.data.human_input    -> question, context, options
  - event.run_context.messages -> conversation history
    |
    v
Stream ends gracefully
    |
    v
Caller gets human input (UI, CLI, API, etc.)
    |
    v
Caller resumes agent with RunContext(human_response=...)
    |
    v
Agent continues from where it left off
```

## Code Example

```python
from akd._base import RunContext, HumanResponse, StreamEventType
from akd.tools.human import HumanTool
from akd_ext.agents import CMRDataSearchAgent, CMRDataSearchAgentConfig
from akd_ext.agents.cmr_care import get_default_cmr_tools, CMRDataSearchAgentInputSchema

# 1. Create agent with HITL enabled
agent = CMRDataSearchAgent(config=CMRDataSearchAgentConfig(
    tools=get_default_cmr_tools() + [HumanTool()],
))

input_params = CMRDataSearchAgentInputSchema(query="Find sea ice datasets")

# 2. Stream until human input is needed
saved_event = None
async for event in agent.astream(input_params):
    if event.event_type == StreamEventType.HUMAN_INPUT_REQUIRED:
        saved_event = event
        break
    # handle other events (STREAMING, TOOL_CALLING, etc.)

# 3. Collect human input
if saved_event:
    tool_call_id = saved_event.data.tool_call_id
    question = saved_event.data.human_input.question

    user_answer = input(f"{question}: ")  # your UI here

    # 4. Resume with RunContext
    run_context = RunContext(
        human_response=HumanResponse(
            tool_call_id=tool_call_id,
            content={"response": user_answer},
        ),
        messages=saved_event.run_context.messages,
    )

    async for event in agent.astream(input_params, run_context=run_context):
        if event.event_type == StreamEventType.COMPLETED:
            print(event.data.output)
```

## Key Types

| Type | Import | Purpose |
|------|--------|---------|
| `HumanTool` | `akd.tools.human` | Tool to inject into agent config |
| `HumanResponse` | `akd._base` | Wraps the human's answer for resumption |
| `RunContext` | `akd._base` | Carries `human_response` + `messages` for resume |
| `HumanInputRequiredEvent` | `akd._base` | Stream event emitted when agent pauses |
| `HumanResponseEvent` | `akd._base` | Stream event emitted on successful resume |

## Reference Implementation

- Agent with HITL support: `akd_ext/agents/cmr_care.py` (`CMRDataSearchAgent`)
- HITL handling in base agent: `akd_ext/agents/_base.py` (`_stream_llm_response`, see `ask_human` branch)

## Further Reading

Base definitions for `HumanTool`, `RunContext`, `HumanResponse`, and streaming events live in [akd-core](https://github.com/NASA-IMPACT/accelerated-discovery/):

- `akd.tools.human` — `HumanTool`, `HumanToolInput`, `HumanToolOutput`
- `akd._base.tool_calling` — `RunContext`, `HumanResponse`
- `akd._base.streaming` — `HumanInputRequiredEvent`, `HumanResponseEvent`
