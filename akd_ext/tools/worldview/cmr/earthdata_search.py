"""Earthdata Search dataset landing page URL builder tool.

Given a CMR collection ``concept_id`` (as returned by the CMR agent), produces
a URL that opens the dataset's landing page on
``search.earthdata.nasa.gov``.
"""

import re
from urllib.parse import urlencode

from pydantic import Field

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool

from akd_ext.mcp import mcp_tool


CONCEPT_ID_PATTERN = re.compile(r"^C\d+-\w+$")
EARTHDATA_SEARCH_BASE_URL = "https://search.earthdata.nasa.gov/search"


class EarthdataSearchLandingPageInputSchema(InputSchema):
    """Input schema for the EarthdataSearchLandingPageTool."""

    concept_id: str = Field(
        ...,
        description=("CMR collection concept_id in the form C<digits>-<PROVIDER>, e.g. C2769216080-LARC_CLOUD."),
    )


class EarthdataSearchLandingPageOutputSchema(OutputSchema):
    """Output schema for the EarthdataSearchLandingPageTool."""

    url: str = Field(
        ...,
        description=("Earthdata Search dataset landing page URL focused on the given collection."),
    )


@mcp_tool
class EarthdataSearchLandingPageTool(
    BaseTool[EarthdataSearchLandingPageInputSchema, EarthdataSearchLandingPageOutputSchema]
):
    """Generate a NASA Earthdata Search dataset landing page URL from a CMR collection concept_id.

    Returns a URL like https://search.earthdata.nasa.gov/search?p=<concept_id>
    that opens Earthdata Search focused on the given collection.
    """

    input_schema = EarthdataSearchLandingPageInputSchema
    output_schema = EarthdataSearchLandingPageOutputSchema

    async def _arun(
        self,
        params: EarthdataSearchLandingPageInputSchema,
    ) -> EarthdataSearchLandingPageOutputSchema:
        concept_id = params.concept_id.strip()
        if not CONCEPT_ID_PATTERN.match(concept_id):
            raise ValueError(f"Invalid concept_id {concept_id!r}; expected format C<digits>-<PROVIDER>")
        url = f"{EARTHDATA_SEARCH_BASE_URL}?{urlencode({'p': concept_id})}"
        return EarthdataSearchLandingPageOutputSchema(url=url)


if __name__ == "__main__":
    import asyncio
    import sys

    from loguru import logger

    concept_id = sys.argv[1] if len(sys.argv) > 1 else "C2769216080-LARC_CLOUD"
    tool = EarthdataSearchLandingPageTool()
    result = asyncio.run(tool.arun(EarthdataSearchLandingPageInputSchema(concept_id=concept_id)))
    logger.info(result.model_dump())
