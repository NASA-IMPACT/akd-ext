from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from akd_ext.agents.cmr_care import CMRCareAgent, CMRCareAgentInputSchema, CMRCareConfig
from akd._base import (
    CompletedEvent,
    FailedEvent,
    HumanInputRequiredEvent,
    RunContext,
    StreamingTokenEvent,
    ThinkingEvent,
    ToolCallingEvent,
    ToolResultEvent,
    PartialOutputEvent,
    StartingEvent,
    RunningEvent,
)

try:
    from akd._base import HumanResponse
except Exception:  # pragma: no cover - fallback if type isn't available
    HumanResponse = None

try:
    from akd.tools.human import HumanTool
except Exception:  # pragma: no cover - optional in some akd builds
    HumanTool = None


INDEX_HTML_PATH = Path(__file__).resolve().parent / "index.html"


@dataclass
class SessionState:
    agent: CMRCareAgent
    run_context: RunContext | None = None
    pending_human: dict[str, Any] | None = None
    last_query: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


sessions: dict[str, SessionState] = {}


app = FastAPI(title="CMR CARE Chat")


@app.get("/")
async def index() -> HTMLResponse:
    if not INDEX_HTML_PATH.exists():
        return HTMLResponse("Missing UI asset.", status_code=500)
    return HTMLResponse(INDEX_HTML_PATH.read_text())


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _sse(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=True)
    return f"data: {payload}\n\n"


def _build_agent() -> CMRCareAgent:
    base_config = CMRCareConfig()
    tools = list(base_config.tools)
    if HumanTool is not None:
        tools.append(HumanTool())
    return CMRCareAgent(CMRCareConfig(tools=tools))


def _get_session(session_id: str | None) -> tuple[str, SessionState]:
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    new_id = uuid.uuid4().hex
    sessions[new_id] = SessionState(agent=_build_agent())
    return new_id, sessions[new_id]


def _with_human_response(run_context: RunContext, tool_call_id: str, message: str) -> RunContext:
    if HumanResponse is not None:
        response = HumanResponse(tool_call_id=tool_call_id, content={"response": message})
    else:
        response = SimpleNamespace(tool_call_id=tool_call_id, content={"response": message})
    run_context.human_response = response
    return run_context


async def _event_stream(
    session_id: str,
    session: SessionState,
    params: CMRCareAgentInputSchema,
    run_context: RunContext | None,
) -> AsyncIterator[str]:
    yield _sse({"type": "session", "session_id": session_id})

    async with session.lock:
        try:
            async for event in session.agent.astream(params, run_context=run_context):
                if isinstance(event, StartingEvent):
                    yield _sse({"type": "starting", "message": event.message})
                elif isinstance(event, RunningEvent):
                    yield _sse({"type": "running", "message": event.message})
                elif isinstance(event, StreamingTokenEvent):
                    token = getattr(event.data, "token", "") if event.data else ""
                    yield _sse({"type": "token", "text": token, "source": event.source})
                elif isinstance(event, ThinkingEvent):
                    content = getattr(event.data, "thinking_content", "") if event.data else ""
                    if content:
                        yield _sse({"type": "thinking", "text": content, "source": event.source})
                elif isinstance(event, ToolCallingEvent):
                    tool_call = getattr(event.data, "tool_call", None) if event.data else None
                    tool_name = getattr(tool_call, "tool_name", None)
                    yield _sse({"type": "tool_call", "tool_name": tool_name, "source": event.source})
                elif isinstance(event, ToolResultEvent):
                    result = getattr(event.data, "result", None) if event.data else None
                    tool_name = getattr(result, "tool_name", None)
                    yield _sse({"type": "tool_result", "tool_name": tool_name, "source": event.source})
                elif isinstance(event, PartialOutputEvent):
                    partial = getattr(event.data, "partial_output", None) if event.data else None
                    yield _sse({"type": "partial_output", "output": _jsonable(partial)})
                elif isinstance(event, HumanInputRequiredEvent):
                    human_input = getattr(event.data, "human_input", None) if event.data else None
                    question = getattr(human_input, "question", None)
                    tool_call_id = getattr(event.data, "tool_call_id", None) if event.data else None
                    session.pending_human = {
                        "tool_call_id": tool_call_id,
                        "question": question,
                    }
                    session.run_context = getattr(event, "run_context", None)
                    yield _sse(
                        {
                            "type": "human_input_required",
                            "question": question,
                            "tool_call_id": tool_call_id,
                        }
                    )
                    return
                elif isinstance(event, CompletedEvent):
                    output = getattr(event.data, "output", None) if event.data else None
                    session.pending_human = None
                    session.run_context = None
                    yield _sse({"type": "completed", "output": _jsonable(output)})
                elif isinstance(event, FailedEvent):
                    session.pending_human = None
                    session.run_context = None
                    yield _sse({"type": "failed", "message": event.message})
        except Exception as exc:
            session.pending_human = None
            session.run_context = None
            yield _sse({"type": "failed", "message": str(exc)})


@app.post("/api/chat", response_model=None)
async def chat(request: Request):
    payload = await request.json()
    session_id = payload.get("session_id")
    message = (payload.get("message") or "").strip()
    mode = payload.get("mode") or "user"
    tool_call_id = payload.get("tool_call_id")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    session_id, session = _get_session(session_id)

    run_context = None
    if mode == "human" and session.run_context:
        tool_id = tool_call_id or (session.pending_human or {}).get("tool_call_id")
        if not tool_id:
            return JSONResponse({"error": "missing tool_call_id for human response"}, status_code=400)

        run_context = session.run_context
        if hasattr(run_context, "model_copy"):
            run_context = run_context.model_copy()
        run_context = _with_human_response(run_context, tool_id, message)
        params = CMRCareAgentInputSchema(query=session.last_query or message)
    else:
        session.pending_human = None
        session.run_context = None
        session.last_query = message
        params = CMRCareAgentInputSchema(query=message)

    return StreamingResponse(
        _event_stream(session_id, session, params, run_context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def main() -> None:
    import uvicorn

    host = os.environ.get("APP_HOST", "127.0.0.1")
    port = int(os.environ.get("APP_PORT", "8000"))
    log_level = os.environ.get("APP_LOG_LEVEL", "info")
    uvicorn.run(app, host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    main()
