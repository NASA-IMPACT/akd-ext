"""IESO Worldview agent — VLM-baseline variant.

Companion to ``ieso_w_geoui``. Same Worldview surface, same
discovery tools, but observation goes through Playwright screenshot
+ accessibility snapshot and actions are issued as browser clicks /
typing / drags against the live Worldview UI. No permalink builder,
no URL parser. This is the realistic-default baseline for the
poster's token-efficiency comparison against the GeoUI Protocol.
"""

from ieso_w_vlm.agent import (
    IESOWorldviewVLMAgent,
    IESOWorldviewVLMAgentConfig,
    IESOWorldviewVLMAgentInputSchema,
    IESOWorldviewVLMAgentOutputSchema,
)

__all__ = [
    "IESOWorldviewVLMAgent",
    "IESOWorldviewVLMAgentConfig",
    "IESOWorldviewVLMAgentInputSchema",
    "IESOWorldviewVLMAgentOutputSchema",
]
