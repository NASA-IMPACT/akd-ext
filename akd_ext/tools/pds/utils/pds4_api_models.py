"""Pydantic models for PDS4 API responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def get_first_value(properties: dict[str, Any], key: str) -> str | None:
    """Extract first value from a PDS4 properties array.

    PDS4 API returns property values as arrays. This helper extracts
    the first element or returns None if empty/missing.

    Args:
        properties: Dictionary of PDS4 properties
        key: The property key to extract

    Returns:
        First value from the array, or None if empty/missing
    """
    values = properties.get(key, [])
    if isinstance(values, list):
        return str(values[0]) if values else None
    return str(values) if values is not None else None


def parse_datetime(value: str | None) -> datetime | None:
    """Parse a datetime string from PDS4 API response.

    Handles ISO 8601 format datetime strings with timezone.

    Args:
        value: ISO 8601 datetime string or None

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not value:
        return None
    try:
        # Handle 'Z' suffix (UTC)
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def parse_int(value: str | None) -> int | None:
    """Parse an integer string from PDS4 API response.

    Args:
        value: Integer string or None

    Returns:
        Parsed integer or None if parsing fails
    """
    if not value:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def has_values(model: BaseModel) -> bool:
    """Check if a Pydantic model has any non-None values.

    Args:
        model: Pydantic model instance

    Returns:
        True if any field has a non-None value
    """
    return any(model.model_dump(exclude_none=True).values())


class PDS4Summary(BaseModel):
    """PDS4 search response summary."""

    hits: int
    took: int | None = None
    q: str | None = None
    start: int = 0
    properties: list[Any] = Field(default_factory=list)
    facets: list[dict[str, Any]] = Field(default_factory=list)


class PDS4Facet(BaseModel):
    """PDS4 facet information."""

    property: str
    type: str
    counts: dict[str, int]


class PDS4IdentificationArea(BaseModel):
    """PDS4 Identification Area properties."""

    model_config = ConfigDict(populate_by_name=True)

    title: str | None = Field(None, alias="pds:Identification_Area.pds:title")
    logical_identifier: str | None = Field(None, alias="pds:Identification_Area.pds:logical_identifier")
    version_id: str | None = Field(None, alias="pds:Identification_Area.pds:version_id")
    product_class: str | None = Field(None, alias="pds:Identification_Area.pds:product_class")

    @classmethod
    def from_properties(cls, properties: dict[str, Any]) -> "PDS4IdentificationArea":
        """Create from PDS4 properties dict where values are arrays."""
        return cls(
            title=get_first_value(properties, "pds:Identification_Area.pds:title"),
            logical_identifier=get_first_value(properties, "pds:Identification_Area.pds:logical_identifier"),
            version_id=get_first_value(properties, "pds:Identification_Area.pds:version_id"),
            product_class=get_first_value(properties, "pds:Identification_Area.pds:product_class"),
        )


class PDS4ScienceFacets(BaseModel):
    """PDS4 Science Facets properties."""

    model_config = ConfigDict(populate_by_name=True)

    discipline_name: str | None = Field(None, alias="pds:Science_Facets.pds:discipline_name")
    wavelength_range: str | None = Field(None, alias="pds:Science_Facets.pds:wavelength_range")
    domain: str | None = Field(None, alias="pds:Science_Facets.pds:domain")


class PDS4InvestigationArea(BaseModel):
    """PDS4 Investigation Area properties."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(None, alias="pds:Investigation_Area.pds:name")
    type: str | None = Field(None, alias="pds:Investigation_Area.pds:type")
    title: str | None = Field(None, alias="pds:Investigation_Area.pds:title")

    @classmethod
    def from_properties(cls, properties: dict[str, Any]) -> "PDS4InvestigationArea":
        """Create from PDS4 properties dict where values are arrays."""
        return cls(
            name=get_first_value(properties, "pds:Investigation_Area.pds:name"),
            type=get_first_value(properties, "pds:Investigation_Area.pds:type"),
            title=get_first_value(properties, "pds:Investigation_Area.pds:title"),
        )


class PDS4TargetIdentification(BaseModel):
    """PDS4 Target Identification properties."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(None, alias="pds:Target_Identification.pds:name")
    type: str | None = Field(None, alias="pds:Target_Identification.pds:type")


class PDS4TimeCoordinates(BaseModel):
    """PDS4 Time Coordinates properties."""

    model_config = ConfigDict(populate_by_name=True)

    start_date_time: datetime | None = Field(None, alias="pds:Time_Coordinates.pds:start_date_time")
    stop_date_time: datetime | None = Field(None, alias="pds:Time_Coordinates.pds:stop_date_time")


class PDS4Provenance(BaseModel):
    """PDS4 Operational Provenance properties."""

    model_config = ConfigDict(populate_by_name=True)

    parent_bundle_identifier: str | None = Field(None, alias="ops:Provenance.ops:parent_bundle_identifier")
    parent_collection_identifier: str | None = Field(None, alias="ops:Provenance.ops:parent_collection_identifier")


class PDS4HarvestInfo(BaseModel):
    """PDS4 Harvest Information properties."""

    model_config = ConfigDict(populate_by_name=True)

    node_name: str | None = Field(None, alias="ops:Harvest_Info.ops:node_name")
    harvest_date_time: datetime | None = Field(None, alias="ops:Harvest_Info.ops:harvest_date_time")


class PDS4DataFileInfo(BaseModel):
    """PDS4 Data File Information properties."""

    model_config = ConfigDict(populate_by_name=True)

    file_ref: str | None = Field(None, alias="ops:Data_File_Info.ops:file_ref")
    file_size: int | None = Field(None, alias="ops:Data_File_Info.ops:file_size")
    mime_type: str | None = Field(None, alias="ops:Data_File_Info.ops:mime_type")


class PDS4PrimaryResultSummary(BaseModel):
    """PDS4 Primary Result Summary properties."""

    model_config = ConfigDict(populate_by_name=True)

    processing_level: str | None = Field(None, alias="pds:Primary_Result_Summary.pds:processing_level")
    purpose: str | None = Field(None, alias="pds:Primary_Result_Summary.pds:purpose")


class PDS4Collection(BaseModel):
    """PDS4 Collection properties."""

    model_config = ConfigDict(populate_by_name=True)

    collection_type: str | None = Field(None, alias="pds:Collection.pds:collection_type")


class PDS4BundleMemberEntry(BaseModel):
    """PDS4 Bundle Member Entry properties."""

    model_config = ConfigDict(populate_by_name=True)

    lidvid_reference: str | None = Field(None, alias="pds:Bundle_Member_Entry.pds:lidvid_reference")
    member_status: str | None = Field(None, alias="pds:Bundle_Member_Entry.pds:member_status")


class PDS4Investigation(BaseModel):
    """PDS4 Investigation properties."""

    model_config = ConfigDict(populate_by_name=True)

    start_date: str | None = Field(None, alias="pds:Investigation.pds:start_date")
    stop_date: str | None = Field(None, alias="pds:Investigation.pds:stop_date")
    type: str | None = Field(None, alias="pds:Investigation.pds:type")


class PDS4Target(BaseModel):
    """PDS4 Target properties."""

    model_config = ConfigDict(populate_by_name=True)

    type: str | None = Field(None, alias="pds:Target.pds:type")
    description: str | None = Field(None, alias="pds:Target.pds:description")


class PDS4Instrument(BaseModel):
    """PDS4 Instrument properties."""

    model_config = ConfigDict(populate_by_name=True)

    type: str | None = Field(None, alias="pds:Instrument.pds:type")
    description: str | None = Field(None, alias="pds:Instrument.pds:description")


class PDS4InstrumentHost(BaseModel):
    """PDS4 Instrument Host properties."""

    model_config = ConfigDict(populate_by_name=True)

    type: str | None = Field(None, alias="pds:Instrument_Host.pds:type")
    description: str | None = Field(None, alias="pds:Instrument_Host.pds:description")


class PDS4Alias(BaseModel):
    """PDS4 Alias properties."""

    model_config = ConfigDict(populate_by_name=True)

    alternate_title: str | None = Field(None, alias="pds:Alias.pds:alternate_title")


class PDS4LabelFileInfo(BaseModel):
    """PDS4 Label File Info properties."""

    model_config = ConfigDict(populate_by_name=True)

    file_ref: str | None = Field(None, alias="ops:Label_File_Info.ops:file_ref")


class PDS4Product(BaseModel):
    """PDS4 Product representation with structured properties."""

    # Universal identifiers
    id: str
    lid: str | None = None
    lidvid: str | None = None
    title: str | None = None

    # Structured properties
    identification_area: PDS4IdentificationArea | None = None
    science_facets: PDS4ScienceFacets | None = None
    investigation_area: PDS4InvestigationArea | None = None
    target_identification: PDS4TargetIdentification | None = None
    time_coordinates: PDS4TimeCoordinates | None = None
    provenance: PDS4Provenance | None = None
    harvest_info: PDS4HarvestInfo | None = None
    data_file_info: PDS4DataFileInfo | None = None
    primary_result_summary: PDS4PrimaryResultSummary | None = None
    collection: PDS4Collection | None = None
    bundle_member_entry: PDS4BundleMemberEntry | None = None

    # Context-specific properties
    investigation: PDS4Investigation | None = None
    target: PDS4Target | None = None
    instrument: PDS4Instrument | None = None
    instrument_host: PDS4InstrumentHost | None = None
    alias: PDS4Alias | None = None
    label_file_info: PDS4LabelFileInfo | None = None

    # Reference fields for collections
    ref_lid_instrument: str | None = None
    ref_lid_target: str | None = None
    ref_lid_instrument_host: str | None = None
    ref_lid_investigation: str | None = None

    # Raw properties for any additional fields
    properties: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "PDS4Product":
        """Create PDS4Product from raw API response data.

        Parses the raw JSON response from the PDS4 API into a structured
        PDS4Product model with properly typed fields.

        Args:
            data: Raw API response dictionary

        Returns:
            Populated PDS4Product instance
        """
        props = data.get("properties", {}) if "properties" in data else data

        identification_area = PDS4IdentificationArea.from_properties(props)
        investigation_area = PDS4InvestigationArea.from_properties(props)

        # Simplified extraction for other properties
        science_facets = PDS4ScienceFacets(
            discipline_name=get_first_value(props, "pds:Science_Facets.pds:discipline_name"),
            wavelength_range=get_first_value(props, "pds:Science_Facets.pds:wavelength_range"),
            domain=get_first_value(props, "pds:Science_Facets.pds:domain"),
        )

        target_identification = PDS4TargetIdentification(
            name=get_first_value(props, "pds:Target_Identification.pds:name"),
            type=get_first_value(props, "pds:Target_Identification.pds:type"),
        )

        # Parse datetime fields from string values
        time_coordinates = PDS4TimeCoordinates(
            start_date_time=parse_datetime(get_first_value(props, "pds:Time_Coordinates.pds:start_date_time")),
            stop_date_time=parse_datetime(get_first_value(props, "pds:Time_Coordinates.pds:stop_date_time")),
        )

        provenance = PDS4Provenance(
            parent_bundle_identifier=get_first_value(props, "ops:Provenance.ops:parent_bundle_identifier"),
            parent_collection_identifier=get_first_value(props, "ops:Provenance.ops:parent_collection_identifier"),
        )

        harvest_info = PDS4HarvestInfo(
            node_name=get_first_value(props, "ops:Harvest_Info.ops:node_name"),
            harvest_date_time=parse_datetime(get_first_value(props, "ops:Harvest_Info.ops:harvest_date_time")),
        )

        data_file_info = PDS4DataFileInfo(
            file_ref=get_first_value(props, "ops:Data_File_Info.ops:file_ref"),
            file_size=parse_int(get_first_value(props, "ops:Data_File_Info.ops:file_size")),
            mime_type=get_first_value(props, "ops:Data_File_Info.ops:mime_type"),
        )

        primary_result_summary = PDS4PrimaryResultSummary(
            processing_level=get_first_value(props, "pds:Primary_Result_Summary.pds:processing_level"),
            purpose=get_first_value(props, "pds:Primary_Result_Summary.pds:purpose"),
        )

        collection = PDS4Collection(
            collection_type=get_first_value(props, "pds:Collection.pds:collection_type"),
        )

        bundle_member_entry = PDS4BundleMemberEntry(
            lidvid_reference=get_first_value(props, "pds:Bundle_Member_Entry.pds:lidvid_reference"),
            member_status=get_first_value(props, "pds:Bundle_Member_Entry.pds:member_status"),
        )

        # Context-specific properties
        investigation = PDS4Investigation(
            start_date=get_first_value(props, "pds:Investigation.pds:start_date"),
            stop_date=get_first_value(props, "pds:Investigation.pds:stop_date"),
            type=get_first_value(props, "pds:Investigation.pds:type"),
        )

        target = PDS4Target(
            type=get_first_value(props, "pds:Target.pds:type"),
            description=get_first_value(props, "pds:Target.pds:description"),
        )

        instrument = PDS4Instrument(
            type=get_first_value(props, "pds:Instrument.pds:type"),
            description=get_first_value(props, "pds:Instrument.pds:description"),
        )

        instrument_host = PDS4InstrumentHost(
            type=get_first_value(props, "pds:Instrument_Host.pds:type"),
            description=get_first_value(props, "pds:Instrument_Host.pds:description"),
        )

        alias = PDS4Alias(
            alternate_title=get_first_value(props, "pds:Alias.pds:alternate_title"),
        )

        label_file_info = PDS4LabelFileInfo(
            file_ref=get_first_value(props, "ops:Label_File_Info.ops:file_ref"),
        )

        return cls(
            id=data.get("id", ""),
            lid=get_first_value(props, "lid"),
            lidvid=get_first_value(props, "lidvid"),
            title=(
                data.get("title")
                or get_first_value(props, "pds:Identification_Area.pds:title")
                or get_first_value(props, "title")
            ),
            identification_area=identification_area if has_values(identification_area) else None,
            science_facets=science_facets if has_values(science_facets) else None,
            investigation_area=investigation_area if has_values(investigation_area) else None,
            target_identification=target_identification if has_values(target_identification) else None,
            time_coordinates=time_coordinates if has_values(time_coordinates) else None,
            provenance=provenance if has_values(provenance) else None,
            harvest_info=harvest_info if has_values(harvest_info) else None,
            data_file_info=data_file_info if has_values(data_file_info) else None,
            primary_result_summary=primary_result_summary if has_values(primary_result_summary) else None,
            collection=collection if has_values(collection) else None,
            bundle_member_entry=bundle_member_entry if has_values(bundle_member_entry) else None,
            investigation=investigation if has_values(investigation) else None,
            target=target if has_values(target) else None,
            instrument=instrument if has_values(instrument) else None,
            instrument_host=instrument_host if has_values(instrument_host) else None,
            alias=alias if has_values(alias) else None,
            label_file_info=label_file_info if has_values(label_file_info) else None,
            ref_lid_instrument=get_first_value(props, "ref_lid_instrument"),
            ref_lid_target=get_first_value(props, "ref_lid_target"),
            ref_lid_instrument_host=get_first_value(props, "ref_lid_instrument_host"),
            ref_lid_investigation=get_first_value(props, "ref_lid_investigation"),
            properties=props,
        )


class PDS4SearchResponse(BaseModel):
    """PDS4 search response wrapper."""

    summary: PDS4Summary
    data: list[PDS4Product] = Field(default_factory=list)
    facets: list[PDS4Facet] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "PDS4SearchResponse":
        """Create PDS4SearchResponse from raw API response data."""
        summary_data = data.get("summary", {})

        # Parse facets from summary
        facets = []
        for facet_data in summary_data.get("facets", []):
            facets.append(PDS4Facet(**facet_data))

        # Create summary without facets (they're handled separately)
        summary = PDS4Summary(
            hits=summary_data.get("hits", 0),
            took=summary_data.get("took"),
            q=summary_data.get("q"),
            start=summary_data.get("start", 0),
            properties=summary_data.get("properties", []),
        )

        products = []
        for item in data.get("data", []):
            products.append(PDS4Product.from_raw_data(item))

        return cls(
            summary=summary,
            data=products,
            facets=facets,
        )


class PDS4Error(BaseModel):
    """PDS4 API error response."""

    status: int
    title: str
    detail: str | None = None


class PDS4ErrorResponse(BaseModel):
    """PDS4 API error response wrapper."""

    errors: list[PDS4Error]
