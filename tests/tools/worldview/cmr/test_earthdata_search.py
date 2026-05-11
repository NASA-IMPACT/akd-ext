import pytest

from akd_ext.tools.worldview.cmr.earthdata_search import (
    EARTHDATA_SEARCH_BASE_URL,
    EarthdataSearchLandingPageInputSchema,
    EarthdataSearchLandingPageOutputSchema,
    EarthdataSearchLandingPageTool,
)


@pytest.fixture
def tool() -> EarthdataSearchLandingPageTool:
    return EarthdataSearchLandingPageTool()


@pytest.mark.asyncio
async def test_happy_path(tool: EarthdataSearchLandingPageTool) -> None:
    result = await tool.arun(EarthdataSearchLandingPageInputSchema(concept_id="C2769216080-LARC_CLOUD"))
    assert result.url == "https://search.earthdata.nasa.gov/search?p=C2769216080-LARC_CLOUD"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "concept_id",
    [
        "C123456-LPDAAC_ECS",
        "C9999999-NSIDC_ECS",
        "C2769216080-LARC_CLOUD",
    ],
)
async def test_provider_names_preserved(tool: EarthdataSearchLandingPageTool, concept_id: str) -> None:
    result = await tool.arun(EarthdataSearchLandingPageInputSchema(concept_id=concept_id))
    assert result.url == f"{EARTHDATA_SEARCH_BASE_URL}?p={concept_id}"


@pytest.mark.asyncio
async def test_whitespace_is_stripped(tool: EarthdataSearchLandingPageTool) -> None:
    result = await tool.arun(EarthdataSearchLandingPageInputSchema(concept_id="  C123-LARC  "))
    assert result.url == "https://search.earthdata.nasa.gov/search?p=C123-LARC"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_input",
    [
        "",
        "   ",
        "foo",
        "C123",
        "123-LARC",
        "X123-LARC",
        "C-LARC",
    ],
)
async def test_invalid_input_raises(tool: EarthdataSearchLandingPageTool, bad_input: str) -> None:
    with pytest.raises(ValueError, match="Invalid concept_id"):
        await tool.arun(EarthdataSearchLandingPageInputSchema(concept_id=bad_input))


def test_tool_exposes_schemas(tool: EarthdataSearchLandingPageTool) -> None:
    assert tool.input_schema is EarthdataSearchLandingPageInputSchema
    assert tool.output_schema is EarthdataSearchLandingPageOutputSchema


def test_top_level_reexport() -> None:
    from akd_ext.tools import (
        EarthdataSearchLandingPageInputSchema as ReExportedInput,
        EarthdataSearchLandingPageOutputSchema as ReExportedOutput,
        EarthdataSearchLandingPageTool as ReExportedTool,
    )

    assert ReExportedTool is EarthdataSearchLandingPageTool
    assert ReExportedInput is EarthdataSearchLandingPageInputSchema
    assert ReExportedOutput is EarthdataSearchLandingPageOutputSchema
