from akd.agents._base import BaseAgent, BaseAgentConfig
from akd._base import InputSchema, OutputSchema


class OpenAIBaseAgentConfig(BaseAgentConfig):
    """Configuration for OpenAI agents based AKD Agents.
    This configuration extends BaseConfig to provide OpenAI-specific
    settings for agents built with OpenAI's platform agent builder.
    """

    pass


class OpenAIBaseAgent[
    InSchema: InputSchema,
    OutSchema: OutputSchema,
](BaseAgent):
    """Base class for OpenAI agents.
    Any agent generated from the openai's platform agent builder should inherit from this class.
    """

    input_schema = InputSchema
    output_schema = OutputSchema

    def __init__(self, config: OpenAIBaseAgentConfig | None = None, debug: bool = False) -> None:
        super().__init__(config=config, debug=debug)
        self.config = config

    async def _arun(self, params: InSchema, **kwargs) -> OutSchema:
        raise NotImplementedError("Subclasses must implement this method.")
