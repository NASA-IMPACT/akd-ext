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

    if missing_keys:
        agent = None
    else:
        playwright = make_playwright_mcp(cdp_endpoint=cdp_endpoint)
        agent = IESOWorldviewGeoUIAgent(
            IESOWorldviewGeoUIAgentConfig(
                capabilities=[
                    *get_default_ieso_worldview_geoui_capabilities(),
                    playwright_capability(playwright),
                ],
            ),
        )

    # Mutable container so the async chat handler can persist
    # `agent.last_run_context` across turns.
    # ``cum_usage`` is our own running tally: we pass ``usage=None`` per
    # turn (so pydantic_ai's request_limit doesn't trip on cumulative
    # counts — AKD's base config caps request_limit at 50), then add the
    # turn's usage here for display.
    session = {
        "ctx": None,
        "turns": 0,
        "last_output": None,
        "cum_usage": None,
        "cdp_endpoint": cdp_endpoint,
    }
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

    async def _handler(messages, config):
        if agent is None:
            return "Agent not initialised — fix the missing env vars above and re-run the notebook."

        latest = messages[-1].content if messages else ""
        try:
            output = await agent.arun(
                IESOWorldviewGeoUIAgentInputSchema(query=latest),
                run_context=session["ctx"],
                # Reset per-turn usage. AKD's _wire_usage_limits caps
                # request_limit at max_tool_iterations (≤50), and the
                # default arun threads cumulative usage from
                # run_context — together they fire UsageLimitExceeded
                # after ~5–10 turns of tool-heavy chat. Per-turn reset
                # restores request_limit's intended runaway-protection
                # role; cumulative requests are tracked below for the
                # session-state view.
                usage=None,
            )
        except BaseException as exc:  # noqa: BLE001 — surface ExceptionGroup too
            return _format_error(exc)

        # Persist context for the next turn.
        session["ctx"] = agent.last_run_context
        session["turns"] += 1
        session["last_output"] = output
        # Accumulate usage manually since we no longer thread it through
        # pydantic_ai's run-level counter. AKDRunUsage has no __add__,
        # so we sum the three numeric fields by hand.
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

        # Clarification / mid-conversation text: render the markdown body.
        if isinstance(output, TextOutput):
            return output.content

        # Structured final output: `result` (sectioned markdown) + `url`.
        # Returning ``str(output)`` here would give the Pydantic repr —
        # escaped newlines, unwrapped one-liner — which is what shows up
        # as "long text with literal \n" in the chat UI.
        lines = [output.result.strip()]
        url = getattr(output, "url", "") or ""
        if url.strip():
            lines.append(f"\n**Worldview URL:** [{url}]({url})")
        return "\n".join(lines)

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

    mo.md(
        f"""
        ### Session state

        - **Turns:** {turns}
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
        session["ctx"] = None
        session["turns"] = 0
        session["last_output"] = None
        session["cum_usage"] = None
        mo.md("_Session memory cleared. Next message starts a fresh conversation._")
    else:
        mo.md("")
    return


if __name__ == "__main__":
    app.run()
