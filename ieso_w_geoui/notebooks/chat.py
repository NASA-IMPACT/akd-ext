"""Multi-turn chat with IESOWorldviewGeoUIAgent.

Run from the worktree root:

    marimo edit ieso_w_geoui/notebooks/chat.py     # interactive editor
    marimo run  ieso_w_geoui/notebooks/chat.py     # read-only app

Requires `.env` with at minimum OPENAI_API_KEY and VECTOR_DB_TOOL_KEY
(see `.env.example`). The notebook auto-loads `.env` by walking up from
the cwd via python-dotenv.
"""

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _setup_marimo():
    import marimo as mo

    return (mo,)


@app.cell
def _intro(mo):
    mo.md(
        """
        # IESO Worldview GeoUI Agent — Multi-turn Chat

        Multi-turn chat with `IESOWorldviewGeoUIAgent`. The agent speaks
        **GeoIntent** through the GeoUI Protocol; visualisations come back
        as Worldview permalink URLs. Each turn carries forward the agent's
        prior `run_context`, so the conversation has memory.

        ### One-time setup

        Launch Chromium with remote debugging **before** opening this
        notebook, and point `PLAYWRIGHT_CDP_ENDPOINT` at it:

        ```bash
        # In one terminal — leave running:
        /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
            --remote-debugging-port=9222 \\
            --user-data-dir=/tmp/worldview-chromium

        # In the notebook's .env (or shell that launches marimo):
        export PLAYWRIGHT_CDP_ENDPOINT=http://localhost:9222
        ```

        Each agent turn attaches a fresh Playwright MCP to this
        already-running Chromium via CDP, so the map's URL / pan / zoom
        survives across turns even though the MCP itself doesn't.

        ### Using it

        - Type a query (e.g. *"Show Saharan dust over the Atlantic on 2023-06-15"*).
        - The agent may answer directly, ask a clarifying question, or
          render a URL via `geoui_render_intent` once it has enough info.
        - After rendering, the agent calls `browser_navigate` to open the
          URL in your Chromium window. Pan, zoom, or scrub directly in
          the map — on the next turn the agent reads the live URL back
          via `browser_evaluate` and refines from there.
        """
    )
    return


@app.cell
def _env(mo):
    """Load `.env` and surface missing required keys before any agent
    instantiation downstream.
    """
    import os

    from dotenv import load_dotenv

    load_dotenv()  # walks up from cwd; no-op if .env is missing

    required_keys = ["OPENAI_API_KEY", "VECTOR_DB_TOOL_KEY"]
    missing_keys = [k for k in required_keys if not os.getenv(k)]

    cdp_endpoint = os.getenv("PLAYWRIGHT_CDP_ENDPOINT")

    if missing_keys:
        env_status = mo.callout(
            mo.md(
                f"**Missing env vars:** `{', '.join(missing_keys)}`. "
                f"Create `.env` from `.env.example` in the worktree root and re-run."
            ),
            kind="danger",
        )
    elif not cdp_endpoint:
        env_status = mo.callout(
            mo.md(
                "**`PLAYWRIGHT_CDP_ENDPOINT` not set.** The agent will boot a "
                "fresh Chromium per turn and your pan/zoom state will not "
                "survive between turns. Launch Chrome with "
                "`--remote-debugging-port=9222` and export "
                "`PLAYWRIGHT_CDP_ENDPOINT=http://localhost:9222` to get "
                "persistent state (see the intro for the full command)."
            ),
            kind="warn",
        )
    else:
        env_status = mo.callout(
            mo.md(f"Env OK — required keys present and `PLAYWRIGHT_CDP_ENDPOINT={cdp_endpoint}` will be used."),
            kind="success",
        )
    env_status
    return missing_keys, cdp_endpoint


@app.cell
def _warm_button(mo):
    """Manual MCP warm-up trigger.

    The first call to a remote MCP after it has gone cold (FastMCP
    DNS-level suspension, Lambda cold-start) can take several
    seconds. ``start.sh`` warms them once at launch; this button
    lets you re-warm mid-session — useful before kicking off a query
    you care about timing.
    """
    warm_btn = mo.ui.run_button(label="Warm MCPs")
    warm_btn
    return (warm_btn,)


@app.cell
async def _warm_handler(mo, warm_btn):
    """React to the warm button. Idle until ``warm_btn.value`` flips
    to True on click, then call ``warm()`` and render one line per
    endpoint with its HTTP status (or transport-error class).

    Marimo cell bodies are top-level code (mid-cell ``return`` is a
    syntax error), so we compute ``out`` in an if/else chain and
    display it once at the end.
    """
    if not warm_btn.value:
        out = mo.md("")
    else:
        from ieso_w_geoui.warm_mcps import warm

        results = await warm()
        if not results:
            out = mo.md("_No remote MCPs configured — nothing to warm._")
        else:
            lines = [f"**Warmed {len(results)} endpoint(s):**", ""]
            for r in results:
                if r.ok:
                    lines.append(f"- `{r.url}` → HTTP **{r.status}**")
                else:
                    lines.append(f"- `{r.url}` → warm failed ({r.error})")
            out = mo.md("\n".join(lines))
    out
    return


@app.cell
def _agent(cdp_endpoint, missing_keys):
    """Instantiate the agent. Per-turn MCP lifecycle; Chromium is held
    *outside* the notebook via CDP (see ``PLAYWRIGHT_CDP_ENDPOINT`` in
    the env cell). Each ``agent.arun`` spawns a fresh Playwright MCP
    that attaches to the running Chromium and tears down cleanly when
    the arun completes — anyio's same-task enter/exit rule stays
    satisfied because the MCP's scope is fully contained in the arun
    task.
    """
    from akd._base import TextOutput
    from pydantic_ai.capabilities.hooks import Hooks

    from ieso_benchmark import new_session_id
    from ieso_w_geoui import (
        IESOWorldviewGeoUIAgent,
        IESOWorldviewGeoUIAgentConfig,
        IESOWorldviewGeoUIAgentInputSchema,
    )
    from ieso_w_geoui.agent import (
        get_default_ieso_worldview_geoui_capabilities,
        make_playwright_mcp,
        playwright_capability,
    )

    # Session dict has to exist before the trace hook so the hook's
    # closure can append to ``current_turn_tools``.
    # ``cum_usage`` is our own running tally: we pass ``usage=None`` per
    # turn (so pydantic_ai's request_limit doesn't trip on cumulative
    # counts — AKD's base config caps request_limit at 50), then add the
    # turn's usage here for display.
    # ``log_session_id`` groups all log rows from this marimo session;
    # ``attempts`` increments on every ``_handler`` call (success +
    # error), so error turns get their own ``turn_index`` rather than
    # being silently skipped.
    session = {
        "ctx": None,
        "turns": 0,
        "attempts": 0,
        "log_session_id": new_session_id(),
        "last_output": None,
        "cum_usage": None,
        "cdp_endpoint": cdp_endpoint,
        "current_turn_tools": [],
    }

    # before_tool_execute fires once per model-issued tool call. We
    # record the names in order so the chat can render a collapsible
    # trace. The handler clears this list before each ``arun``.
    trace_hook = Hooks()

    @trace_hook.on.before_tool_execute
    async def _record_tool_call(ctx, *, call, tool_def, args):
        session["current_turn_tools"].append(tool_def.name)
        return args

    if missing_keys:
        agent = None
    else:
        playwright = make_playwright_mcp(cdp_endpoint=cdp_endpoint)
        agent = IESOWorldviewGeoUIAgent(
            IESOWorldviewGeoUIAgentConfig(
                capabilities=[
                    *get_default_ieso_worldview_geoui_capabilities(),
                    playwright_capability(playwright),
                    trace_hook,
                ],
            ),
        )

    return IESOWorldviewGeoUIAgentInputSchema, TextOutput, agent, session


@app.cell
def _chat(IESOWorldviewGeoUIAgentInputSchema, TextOutput, agent, mo, session):
    """The chat itself.

    Async handler. All MCPs (Playwright + CMR) are spun up and torn
    down per ``arun``. Chromium state is preserved by attaching the
    Playwright MCP to an externally-owned Chromium via CDP, so the
    cheap thing (subprocess spawn + JSON-RPC handshake) happens each
    turn while the expensive thing (Chromium launch + page render) is
    one-shot at the start of the session.
    """

    def _flatten_exceptions(exc: BaseException) -> list[BaseException]:
        """Recursively flatten ExceptionGroup into its leaf exceptions."""
        if isinstance(exc, BaseExceptionGroup):
            leaves: list[BaseException] = []
            for sub in exc.exceptions:
                leaves.extend(_flatten_exceptions(sub))
            return leaves
        return [exc]

    def _format_tool_trace(tools: list[str]) -> str:
        """Render an ordered tool-call trace as a collapsible details block.

        Empty string when no tools were called this turn — keeps simple
        clarification replies clean.
        """
        if not tools:
            return ""
        items = "\n".join(f"{i}. `{name}`" for i, name in enumerate(tools, 1))
        suffix = "" if len(tools) == 1 else "s"
        return f"\n\n<details><summary>Tool trace ({len(tools)} call{suffix})</summary>\n\n{items}\n\n</details>"

    def _format_error(exc: BaseException) -> str:
        """Format an exception (including ExceptionGroup) as a markdown
        block listing the leaf cause(s) plus the head of each traceback.
        """
        import traceback

        leaves = _flatten_exceptions(exc)
        if not leaves:
            return f"**Error:** {type(exc).__name__}: {exc}"

        sections = [f"**Error:** {len(leaves)} underlying exception(s)"]
        for i, leaf in enumerate(leaves, 1):
            tb_text = "".join(traceback.format_exception(type(leaf), leaf, leaf.__traceback__))
            # Trim very long tracebacks to keep the chat usable.
            if len(tb_text) > 1500:
                tb_text = tb_text[-1500:]
                tb_text = "  …\n" + tb_text
            sections.append(
                f"\n**[{i}] {type(leaf).__name__}:** {leaf}\n\n"
                f"<details><summary>Traceback</summary>\n\n```\n{tb_text}\n```\n\n</details>"
            )
        return "\n".join(sections)

    import asyncio
    import time

    from ieso_benchmark import TurnRecord, append_turn_record, extract_usage

    async def _handler(messages, config):
        """Streaming handler with live tool-call visibility.

        Streams a collapsible ``<details><summary>Tool calls</summary>``
        block whose contents grow as ``before_tool_execute`` fires. The
        user can expand it mid-turn to see whether the agent is making
        progress or has entered a loop — that visibility is what makes
        manual stop usable.

        Tradeoffs we're explicitly accepting:

        - Marimo's chat-streaming protocol can raise
          ``Received text-delta for missing text part`` under heavy
          chunking. We mitigate by polling slowly (0.5s) and batching
          every new tool fired since the last poll into a single yield,
          which keeps the chunk count to ~one per second.
        - ``asyncio.create_task`` detaches ``arun`` from this generator's
          task. If the user hits stop, marimo closes the generator and
          we'd leak a background task that keeps firing tools. The
          ``finally`` block below cancels ``arun_task`` on any exit
          (normal, error, or ``GeneratorExit``).
        """
        if agent is None:
            yield "Agent not initialised — fix the missing env vars above and re-run the notebook."
            return

        # Reset per-turn tool trace. The hook in _agent appends to this
        # list on each before_tool_execute fire.
        session["current_turn_tools"] = []

        # Bump attempt counter immediately so error turns get a
        # unique turn_index in the log even if the arun fails before
        # ``session["turns"]`` (successful turns) advances.
        session["attempts"] += 1
        t_start = time.monotonic()

        latest = messages[-1].content if messages else ""
        arun_task = asyncio.create_task(
            agent.arun(
                IESOWorldviewGeoUIAgentInputSchema(query=latest),
                run_context=session["ctx"],
                # Reset per-turn usage. AKD's _wire_usage_limits caps
                # request_limit at max_tool_iterations (≤50); the
                # default arun threads cumulative usage from run_context
                # — together they fire UsageLimitExceeded after ~5–10
                # tool-heavy turns. Per-turn reset restores
                # request_limit's intended runaway-protection role;
                # cumulative usage is tracked manually below.
                usage=None,
                # Bump OpenAI HTTP timeout from the SDK default
                # (10 min) to 15 min for headroom; harmless when
                # responses arrive fast. Mirrored from the VLM
                # notebook to keep both surfaces aligned.
                model_settings={"timeout": 900},
            )
        )

        details_opened = False
        last_count = 0

        def _flush_new_tools() -> str:
            """Build a chunk for any tools recorded since the last yield.

            Empty string when no new tools fired this tick. Opens the
            ``<details>`` block lazily on the first tool so turns that
            never call a tool don't render an empty collapsible.
            """
            nonlocal details_opened, last_count
            tools = list(session["current_turn_tools"])
            if len(tools) <= last_count:
                return ""
            chunk = ""
            if not details_opened:
                # Closed by default — Gemini-style "show thinking" toggle.
                chunk = "<details><summary>Tool calls</summary>\n\n"
                details_opened = True
            new = tools[last_count:]
            chunk += "".join(f"{i}. `{n}`\n" for i, n in enumerate(new, last_count + 1))
            last_count = len(tools)
            return chunk

        try:
            # Poll the trace list while arun runs. 0.5s timeout keeps
            # this cooperative without flooding the marimo wire protocol.
            # asyncio.wait doesn't cancel the task on timeout — it just
            # bounds how long we wait before checking again.
            while not arun_task.done():
                await asyncio.wait({arun_task}, timeout=0.5)
                chunk = _flush_new_tools()
                if chunk:
                    yield chunk

            # Drain anything that fired in the final tick.
            chunk = _flush_new_tools()
            if chunk:
                yield chunk

            closer = "\n</details>\n" if details_opened else ""
            sep = "\n---\n\n" if details_opened else ""

            output = None
            turn_error: BaseException | None = None
            try:
                output = arun_task.result()
            except BaseException as exc:  # noqa: BLE001 — surface ExceptionGroup too
                turn_error = exc

            wall_clock = time.monotonic() - t_start

            # Build + write benchmark log row. We log success and
            # error turns uniformly; the distinguishing field is
            # ``output_kind``. On error we set ``ctx=None`` so we
            # don't misattribute the previous turn's ``run_id`` /
            # ``usage`` to this errored attempt.
            ctx = agent.last_run_context if turn_error is None else None
            if turn_error is not None:
                output_kind = "error"
                final_url = None
                error_type = type(turn_error).__name__
                error_message = str(turn_error)[:500]
            elif isinstance(output, TextOutput):
                output_kind = "text"
                final_url = None
                error_type = None
                error_message = None
            else:
                output_kind = "structured"
                final_url = getattr(output, "url", None)
                error_type = None
                error_message = None

            try:
                append_turn_record(
                    TurnRecord(
                        agent="geoui",
                        session_id=session["log_session_id"],
                        run_id=str(getattr(ctx, "run_id", None)) if ctx else None,
                        turn_index=session["attempts"],
                        user_prompt=latest,
                        tool_calls=list(session["current_turn_tools"]),
                        tool_call_count=len(session["current_turn_tools"]),
                        wall_clock_s=round(wall_clock, 3),
                        usage=extract_usage(getattr(ctx, "usage", None)) if ctx else None,
                        output_kind=output_kind,
                        final_url=final_url,
                        error_type=error_type,
                        error_message=error_message,
                    )
                )
            except Exception:  # noqa: BLE001 — never let logging break the chat
                pass

            if turn_error is not None:
                yield closer + sep + _format_error(turn_error)
                return

            # Persist context for the next turn.
            session["ctx"] = agent.last_run_context
            session["turns"] += 1
            session["last_output"] = output
            # AKDRunUsage has no __add__; sum field-wise.
            turn_usage = getattr(agent.last_run_context, "usage", None)
            if turn_usage is not None:
                cum = session.get("cum_usage")
                if cum is None:
                    session["cum_usage"] = turn_usage
                else:
                    session["cum_usage"] = type(turn_usage)(
                        input_tokens=(cum.input_tokens or 0) + (turn_usage.input_tokens or 0),
                        output_tokens=(cum.output_tokens or 0) + (turn_usage.output_tokens or 0),
                        requests=(cum.requests or 0) + (turn_usage.requests or 0),
                    )

            if isinstance(output, TextOutput):
                body = output.content
            else:
                # Structured final output: render `result` markdown + clickable url.
                # ``str(output)`` would give the Pydantic repr with escaped \n.
                lines = [output.result.strip()]
                url = getattr(output, "url", "") or ""
                if url.strip():
                    lines.append(f"\n**Worldview URL:** [{url}]({url})")
                body = "\n".join(lines)

            yield closer + sep + body
        finally:
            # Cancel the detached arun_task on any exit path (normal,
            # exception, or generator close from a "stop" click). Without
            # this, hitting stop leaves the agent firing tools in the
            # background — exactly the leak that contributed to turn 3's
            # surprise behaviour.
            if not arun_task.done():
                arun_task.cancel()
                try:
                    await arun_task
                except BaseException:  # noqa: BLE001 — swallow cancel propagation
                    pass

    chat = mo.ui.chat(
        _handler,
        prompts=[
            "I'd like to look at Saharan dust transport over the Atlantic on June 15, 2023.",
            "Show aerosol optical depth over California on September 15, 2025.",
            "What datasets do you have for sea-surface temperature?",
        ],
    )
    chat
    return (chat,)


@app.cell
def _session_view(chat, mo, session):
    """Reactive view of session state — re-renders after every turn
    because it depends on `chat` (which updates on each message).
    """
    _ = chat  # reactive trigger

    turns = session.get("turns", 0)
    last = session.get("last_output")
    ctx = session.get("ctx")

    def _format_last(obj):
        if obj is None:
            return "_(no output yet)_"
        cls_name = type(obj).__name__
        if hasattr(obj, "model_dump_json"):
            try:
                snippet = obj.model_dump_json(indent=2, exclude_none=True)
                if len(snippet) > 800:
                    snippet = snippet[:800] + "\n  …"
                return f"`{cls_name}`\n\n```json\n{snippet}\n```"
            except Exception:  # noqa: BLE001
                pass
        return f"`{cls_name}`: {obj}"

    last_usage_str = "n/a"
    run_id_str = "n/a"
    if ctx is not None:
        last_usage_str = str(ctx.usage) if ctx.usage is not None else "n/a"
        run_id_str = ctx.run_id or "n/a"

    cum_usage = session.get("cum_usage")
    cum_usage_str = str(cum_usage) if cum_usage is not None else "n/a"

    from ieso_benchmark import DEFAULT_LOG_PATH

    log_session = session.get("log_session_id", "n/a")
    attempts = session.get("attempts", 0)

    mo.md(
        f"""
        ### Session state

        - **Turns:** {turns}
        - **Attempts (logged):** {attempts}
        - **Log session id:** `{log_session}`
        - **Log file:** `{DEFAULT_LOG_PATH}`
        - **Last `run_id`:** `{run_id_str}`
        - **Last turn usage:** `{last_usage_str}`
        - **Cumulative usage:** `{cum_usage_str}`

        #### Last output

        {_format_last(last)}
        """
    )
    return


@app.cell
def _reset_controls(mo, session):
    """Reset the conversation memory without restarting the kernel."""
    reset = mo.ui.run_button(label="Reset conversation memory")
    reset
    return (reset,)


@app.cell
def _reset_handler(mo, reset, session):
    if reset.value:
        # Aliased to ``_new_session_id`` so marimo doesn't flag this
        # cell as a duplicate definition of ``new_session_id``
        # (which is also imported by the ``_agent`` cell for the
        # initial session-id assignment).
        from ieso_benchmark import new_session_id as _new_session_id

        session["ctx"] = None
        session["turns"] = 0
        session["attempts"] = 0
        session["log_session_id"] = _new_session_id()
        session["last_output"] = None
        session["cum_usage"] = None
        mo.md("_Session memory cleared. Next message starts a fresh conversation._")
    else:
        mo.md("")
    return


if __name__ == "__main__":
    app.run()
