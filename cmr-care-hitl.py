ur import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
    # CMR CARE Human-in-the-Loop Demo

    This notebook demonstrates the **CMR CARE Agent** (Clarify, Analyze, Rank, Explain)
    with real-time streaming and human-in-the-loop support.

    ## How to Use
    1. Enter an Earth science query below
    2. Click "Start Agent" to begin
    3. Watch the real-time event stream
    4. If the agent needs clarification, a response input will appear
    5. View the final ranked datasets and report when complete
    """
    )
    return


@app.cell
def _():
    import os
    import time as time_mod

    from akd._base.streaming import (
        CompletedEvent,
        FailedEvent,
        HumanInputRequiredEvent,
        StreamingTokenEvent,
    )
    from akd._base.tool_calling import HumanResponse, RunContext
    from akd.tools import HumanTool

    from akd_ext.agents import CMRCareAgent, CMRCareConfig
    from akd_ext.agents.cmr_care import (
        CMRCareAgentInputSchema,
        CMRCareAgentOutputSchema,
        get_default_cmr_tools,
    )

    return (
        CMRCareAgent,
        CMRCareAgentInputSchema,
        CMRCareAgentOutputSchema,
        CMRCareConfig,
        CompletedEvent,
        FailedEvent,
        HumanInputRequiredEvent,
        HumanResponse,
        HumanTool,
        RunContext,
        StreamingTokenEvent,
        get_default_cmr_tools,
        os,
        time_mod,
    )


@app.cell
def _(mo, os):
    _existing_url = os.environ.get("CMR_MCP_URL", "")
    cmr_mcp_url_input = mo.ui.text(
        placeholder="Enter your CMR MCP server URL...",
        label="CMR MCP URL (leave blank to use default)",
        value=_existing_url,
        full_width=True,
    )
    if not _existing_url:
        mo.callout(
            "**CMR_MCP_URL** not set in environment. The default public endpoint will be used.",
            kind="info",
        )
    return (cmr_mcp_url_input,)


@app.cell
def _(
    CMRCareAgent,
    CMRCareConfig,
    HumanTool,
    cmr_mcp_url_input,
    get_default_cmr_tools,
    os,
):
    # Set MCP URL from input if provided
    _url = cmr_mcp_url_input.value
    if _url:
        os.environ["CMR_MCP_URL"] = _url

    _cfg = CMRCareConfig(
        tools=get_default_cmr_tools() + [HumanTool()],
    )

    agent = CMRCareAgent(config=_cfg)
    return (agent,)


@app.cell
def _(mo):
    # State management
    get_phase, set_phase = mo.state("idle")
    get_logs, set_logs = mo.state("")
    get_result, set_result = mo.state(None)

    # HITL state
    get_human_prompt, set_human_prompt = mo.state("")
    get_human_context, set_human_context = mo.state("")
    get_human_options, set_human_options = mo.state(None)
    get_saved_history, set_saved_history = mo.state(None)
    get_tool_call_id, set_tool_call_id = mo.state(None)

    return (
        get_human_context,
        get_human_options,
        get_human_prompt,
        get_logs,
        get_phase,
        get_result,
        get_saved_history,
        get_tool_call_id,
        set_human_context,
        set_human_options,
        set_human_prompt,
        set_logs,
        set_phase,
        set_result,
        set_saved_history,
        set_tool_call_id,
    )


@app.cell
def _(mo):
    query_input = mo.ui.text_area(
        placeholder="Enter your Earth science query here...",
        label="Research Query",
        value="What datasets are available for sea ice thickness monitoring?",
        full_width=True,
    )
    return (query_input,)


@app.cell
def _(mo):
    human_response_input = mo.ui.text_area(
        placeholder="Enter your response to the agent's question...",
        label="Your Response",
        value="",
        full_width=True,
    )
    return (human_response_input,)


@app.cell
def _(mo):
    start_button = mo.ui.run_button(label="Start Agent", kind="success")
    submit_button = mo.ui.run_button(label="Submit Response", kind="warn")
    reset_button = mo.ui.button(label="Reset", kind="neutral")
    return reset_button, start_button, submit_button


@app.cell
def _(
    get_human_context,
    get_human_options,
    get_human_prompt,
    get_phase,
    human_response_input,
    mo,
    query_input,
    reset_button,
    start_button,
    submit_button,
):
    """Main UI layout."""
    _phase = get_phase()

    _phase_colors = {
        "idle": ("Ready", "info"),
        "running": ("Running...", "warn"),
        "waiting_for_human": ("Waiting for Human Input", "danger"),
        "completed": ("Completed", "success"),
        "failed": ("Failed", "danger"),
    }
    _phase_text, _phase_kind = _phase_colors.get(_phase, ("Unknown", "info"))

    _status = mo.callout(f"**Status:** {_phase_text}", kind=_phase_kind)

    _query_section = mo.vstack([
        mo.md("### Query"),
        query_input,
        mo.hstack([start_button, reset_button], justify="start", gap=1),
    ])

    if _phase == "waiting_for_human":
        _prompt = get_human_prompt()
        _context = get_human_context()
        _options = get_human_options()

        _q = f"**Agent asks:** {_prompt}"
        if _context:
            _q += f"\n\n*Context:* {_context}"
        if _options:
            _q += "\n\n*Suggested options:*\n" + "\n".join(f"- {o}" for o in _options)

        _human_section = mo.vstack([
            mo.callout(_q, kind="warn"),
            human_response_input,
            submit_button,
        ])
    else:
        _human_section = None

    mo.vstack(
        [_status, _query_section] + ([_human_section] if _human_section else []),
        gap=2,
    )
    return


@app.cell
def _(get_logs, get_phase, mo):
    """Real-time log display."""
    _phase = get_phase()
    _logs = get_logs()

    if _logs or _phase != "idle":
        mo.vstack([
            mo.md("### Agent Logs"),
            mo.Html(f'''
                <div style="
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    font-size: 12px;
                    padding: 12px;
                    border-radius: 8px;
                    height: 400px;
                    overflow-y: auto;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    border: 1px solid #333;
                ">
{_logs if _logs else "Waiting for agent to start..."}
                </div>
            '''),
        ])
    return


@app.cell
def _(get_phase, get_result, mo):
    """Final result display."""
    _result = get_result()
    _phase = get_phase()

    if _phase == "completed" and _result:
        _report = _result._response if hasattr(_result, "_response") else str(_result)
        _ids = _result.dataset_concept_ids if hasattr(_result, "dataset_concept_ids") else []

        _id_elements = []
        if _ids:
            _id_elements = [
                mo.md(
                    " | ".join(
                        f"[`{cid}`](https://cmr.earthdata.nasa.gov/search/concepts/{cid}.html)"
                        for cid in _ids
                    )
                ),
            ]
        else:
            _id_elements = [mo.md("No dataset IDs found")]

        mo.vstack([
            mo.md("### Discovered Datasets"),
            *_id_elements,
            mo.md("### Report"),
            mo.callout(mo.md(_report), kind="success"),
        ])
    elif _phase == "failed":
        mo.callout("Agent failed. Check logs above.", kind="danger")
    return


@app.cell
def _(
    CompletedEvent,
    FailedEvent,
    HumanInputRequiredEvent,
    StreamingTokenEvent,
    mo,
    time_mod,
):
    """Shared event handler for streaming agent events."""

    async def handle_agent_stream(
        stream,
        set_phase,
        set_result,
        set_human_prompt,
        set_human_context,
        set_human_options,
        set_saved_history,
        set_tool_call_id,
        set_logs,
        existing_logs="",
    ):
        """Process an agent event stream, updating UI state via typed events.

        Args:
            stream: AsyncIterator[StreamEvent] from agent.astream()
            set_*: Marimo state setters
            existing_logs: Previously accumulated log text
        """

        def _log(msg):
            _timestamp = time_mod.strftime("%H:%M:%S")
            mo.output.append(mo.md(f"`[{_timestamp}]` {msg}"))

        _all_logs = existing_logs
        _event_count = 0

        try:
            async for event in stream:
                _event_count += 1

                # Skip streaming tokens for cleaner output
                if isinstance(event, StreamingTokenEvent):
                    continue

                # Display event in real-time
                _event_json = event.model_dump_json(indent=2)
                _etype = type(event).__name__
                mo.output.append(
                    mo.vstack([
                        mo.md(f"**Event #{_event_count}: {_etype}**"),
                        mo.Html(
                            f'<pre style="background:#1e1e1e;color:#d4d4d4;padding:8px;'
                            f'border-radius:4px;font-size:11px;max-height:200px;'
                            f'overflow:auto;">{_event_json}</pre>'
                        ),
                    ])
                )
                _all_logs += f"\n--- {_etype} ---\n{_event_json}\n"

                # Handle terminal events using typed isinstance checks
                if isinstance(event, HumanInputRequiredEvent):
                    set_phase("waiting_for_human")
                    set_human_prompt(event.data.human_input.question)
                    set_tool_call_id(event.data.tool_call_id)
                    set_saved_history(event.run_context.messages or [])
                    set_human_context(
                        getattr(event.data.human_input, "context", "") or ""
                    )
                    set_human_options(
                        getattr(event.data.human_input, "options", None)
                    )
                    _log("**Waiting for human input**")
                    break

                elif isinstance(event, CompletedEvent):
                    set_phase("completed")
                    output = event.data.output
                    set_result(output)
                    _log("**Agent completed**")
                    _response = output._response if hasattr(output, "_response") else str(output)
                    mo.output.append(mo.callout(mo.md(_response), kind="success"))
                    break

                elif isinstance(event, FailedEvent):
                    set_phase("failed")
                    _log(f"**Failed:** {event.data.error}")
                    break

        except Exception as e:
            _log(f"**Error:** {e}")
            set_phase("failed")

        set_logs(_all_logs)

    return (handle_agent_stream,)


@app.cell
def _(
    agent,
    reset_button,
    set_human_context,
    set_human_options,
    set_human_prompt,
    set_logs,
    set_phase,
    set_result,
    set_saved_history,
    set_tool_call_id,
):
    """Reset handler."""
    if reset_button.value:
        set_phase("idle")
        set_logs("")
        set_result(None)
        set_human_prompt("")
        set_human_context("")
        set_human_options(None)
        set_saved_history(None)
        set_tool_call_id(None)
        agent.reset_memory()
    return


@app.cell
async def _(
    CMRCareAgentInputSchema,
    agent,
    handle_agent_stream,
    mo,
    time_mod,
    query_input,
    set_human_context,
    set_human_options,
    set_human_prompt,
    set_logs,
    set_phase,
    set_result,
    set_saved_history,
    set_tool_call_id,
    start_button,
):
    """Start agent handler."""

    if start_button.value:
        set_phase("running")
        set_logs("")
        agent.reset_memory()

        mo.output.clear()
        _timestamp = time_mod.strftime("%H:%M:%S")
        mo.output.append(
            mo.md(f"`[{_timestamp}]` **Agent started** - Query: {query_input.value}")
        )

        _stream = agent.astream(
            CMRCareAgentInputSchema(query=query_input.value),
            token_batch_size=100,
        )

        await handle_agent_stream(
            _stream,
            set_phase=set_phase,
            set_result=set_result,
            set_human_prompt=set_human_prompt,
            set_human_context=set_human_context,
            set_human_options=set_human_options,
            set_saved_history=set_saved_history,
            set_tool_call_id=set_tool_call_id,
            set_logs=set_logs,
        )

    return


@app.cell
async def _(
    CMRCareAgentInputSchema,
    HumanResponse,
    RunContext,
    agent,
    handle_agent_stream,
    mo,
    time_mod,
    get_logs,
    get_phase,
    get_saved_history,
    get_tool_call_id,
    human_response_input,
    query_input,
    set_human_context,
    set_human_options,
    set_human_prompt,
    set_logs,
    set_phase,
    set_result,
    set_saved_history,
    set_tool_call_id,
    submit_button,
):
    """Submit human response handler."""

    if submit_button.value and get_phase() == "waiting_for_human":
        set_phase("running")

        _run_context = RunContext(
            messages=get_saved_history(),
            human_response=HumanResponse(
                tool_call_id=get_tool_call_id() or "user",
                content={"response": human_response_input.value},
            ),
        )

        mo.output.clear()
        _timestamp = time_mod.strftime("%H:%M:%S")
        mo.output.append(
            mo.md(
                f"`[{_timestamp}]` **Human response submitted:** {human_response_input.value}"
            )
        )

        _stream = agent.astream(
            CMRCareAgentInputSchema(query=query_input.value),
            run_context=_run_context,
            token_batch_size=100,
        )

        await handle_agent_stream(
            _stream,
            set_phase=set_phase,
            set_result=set_result,
            set_human_prompt=set_human_prompt,
            set_human_context=set_human_context,
            set_human_options=set_human_options,
            set_saved_history=set_saved_history,
            set_tool_call_id=set_tool_call_id,
            set_logs=set_logs,
            existing_logs=get_logs(),
        )

    return


if __name__ == "__main__":
    app.run()
