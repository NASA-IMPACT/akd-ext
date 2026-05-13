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

        - Type a query (e.g. *"Show Saharan dust over the Atlantic on 2023-06-15"*).
        - The agent may answer directly, ask a clarifying question, or
          render a URL via `geoui_render_intent` once it has enough info.
        - URLs in the response are clickable.
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

    env_status = (
        mo.callout(
            mo.md(
                f"**Missing env vars:** `{', '.join(missing_keys)}`. "
                f"Create `.env` from `.env.example` in the worktree root and re-run."
            ),
            kind="danger",
        )
        if missing_keys
        else mo.callout(mo.md(f"Env OK — keys present: `{', '.join(required_keys)}`."), kind="success")
    )
    env_status
    return (missing_keys,)


@app.cell
def _agent(missing_keys):
    """Instantiate the agent once. If env is missing, surface as None
    and the chat cell will render a placeholder instead.
    """
    from akd._base import TextOutput

    from ieso_w_geoui import (
        IESOWorldviewGeoUIAgent,
        IESOWorldviewGeoUIAgentConfig,
        IESOWorldviewGeoUIAgentInputSchema,
    )

    if missing_keys:
        agent = None
    else:
        agent = IESOWorldviewGeoUIAgent(IESOWorldviewGeoUIAgentConfig())

    # Mutable container so the async chat handler can persist
    # `agent.last_run_context` across turns.
    session = {"ctx": None, "turns": 0, "last_output": None}
    return IESOWorldviewGeoUIAgentInputSchema, TextOutput, agent, session


@app.cell
def _chat(IESOWorldviewGeoUIAgentInputSchema, TextOutput, agent, mo, session):
    """The chat itself.

    The handler is async; pydantic_ai's MCP toolset is set up on first
    use and torn down per-`arun` (so MCP cold-start cost shows up on
    the first turn but not subsequent ones).
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
            )
        except BaseException as exc:  # noqa: BLE001 — surface ExceptionGroup too
            return _format_error(exc)

        # Persist context for the next turn.
        session["ctx"] = agent.last_run_context
        session["turns"] += 1
        session["last_output"] = output

        if isinstance(output, TextOutput):
            return output.content
        return getattr(output, "text", None) or str(output)

        # Structured output: `result` (sectioned narrative) + `url`.
        lines = [output.result.strip()]
        if getattr(output, "url", "").strip():
            lines.append(f"\n**Worldview URL:** [{output.url}]({output.url})")
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

    usage_str = "n/a"
    run_id_str = "n/a"
    if ctx is not None:
        usage_str = str(ctx.usage) if ctx.usage is not None else "n/a"
        run_id_str = ctx.run_id or "n/a"

    mo.md(
        f"""
        ### Session state

        - **Turns:** {turns}
        - **Last `run_id`:** `{run_id_str}`
        - **Cumulative usage:** `{usage_str}`

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
        mo.md("_Session memory cleared. Next message starts a fresh conversation._")
    else:
        mo.md("")
    return


if __name__ == "__main__":
    app.run()
