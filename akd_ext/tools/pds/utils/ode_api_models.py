"""Pydantic models for ODE REST API responses.

The Orbital Data Explorer (ODE) provides access to NASA's planetary science
data archives for Mars, Moon, Mercury, and other bodies.
"""

import xml.etree.ElementTree as ET
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _parse_float(value: Any) -> float | None:
    """Parse a value to float, returning None if not possible."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_int(value: Any) -> int:
    """Parse a value to int, returning 0 if not possible."""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


class ODEProductFile(BaseModel):
    """ODE product file information."""

    model_config = ConfigDict(populate_by_name=True)

    file_name: str | None = Field(None, alias="FileName")
    url: str | None = Field(None, alias="URL")
    description: str | None = Field(None, alias="Description")
    file_type: str | None = Field(None, alias="Type")
    kbytes: str | None = Field(None, alias="KBytes")
    creation_date: str | None = Field(None, alias="Creation_date")


class ODEProduct(BaseModel):
    """ODE product representation."""

    model_config = ConfigDict(populate_by_name=True)

    # Identifiers
    pdsid: str | None = None
    ode_id: str | None = None
    data_set_id: str | None = None
    ihid: str | None = None
    iid: str | None = None
    pt: str | None = None

    # Geographic
    center_latitude: float | None = None
    center_longitude: float | None = None
    minimum_latitude: float | None = None
    maximum_latitude: float | None = None
    westernmost_longitude: float | None = None
    easternmost_longitude: float | None = None

    # Footprint
    footprint_geometry: str | None = None

    # Temporal
    observation_time: str | None = None
    utc_start_time: str | None = None
    utc_stop_time: str | None = None

    # Viewing geometry
    emission_angle: float | None = None
    incidence_angle: float | None = None
    phase_angle: float | None = None

    # Resolution
    map_scale: float | None = None

    # Metadata
    target_name: str | None = None
    label_file_name: str | None = None
    description: str | None = None

    # Files
    product_files: list[ODEProductFile] = Field(default_factory=list)

    # URLs
    product_url: str | None = None
    label_url: str | None = None
    files_url: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "ODEProduct":
        """Create ODEProduct from raw API response data."""
        # Handle nested Product_files structure
        product_files: list[ODEProductFile] = []
        files_data = data.get("Product_files", {})
        if files_data:
            file_list = files_data.get("Product_file", [])
            # Handle both single file (dict) and multiple files (list)
            if isinstance(file_list, dict):
                file_list = [file_list]
            for file_data in file_list:
                product_files.append(ODEProductFile(**file_data))

        return cls(
            pdsid=data.get("pdsid"),
            ode_id=data.get("ode_id"),
            data_set_id=data.get("Data_Set_Id"),
            ihid=data.get("ihid"),
            iid=data.get("iid"),
            pt=data.get("pt"),
            center_latitude=_parse_float(data.get("Center_latitude")),
            center_longitude=_parse_float(data.get("Center_longitude")),
            minimum_latitude=_parse_float(data.get("Minimum_latitude")),
            maximum_latitude=_parse_float(data.get("Maximum_latitude")),
            westernmost_longitude=_parse_float(data.get("Westernmost_longitude")),
            easternmost_longitude=_parse_float(data.get("Easternmost_longitude")),
            footprint_geometry=data.get("Footprint_C0_geometry"),
            observation_time=data.get("Observation_time"),
            utc_start_time=data.get("UTC_start_time"),
            utc_stop_time=data.get("UTC_stop_time"),
            emission_angle=_parse_float(data.get("Emission_angle")),
            incidence_angle=_parse_float(data.get("Incidence_angle")),
            phase_angle=_parse_float(data.get("Phase_angle")),
            map_scale=_parse_float(data.get("Map_scale")),
            target_name=data.get("Target_name"),
            label_file_name=data.get("LabelFileName"),
            description=data.get("Description"),
            product_files=product_files,
            product_url=data.get("ProductURL"),
            label_url=data.get("LabelURL"),
            files_url=data.get("FilesURL"),
        )


class ODEProductSearchResponse(BaseModel):
    """ODE product search response."""

    status: str
    count: int = 0
    products: list[ODEProduct] = Field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "ODEProductSearchResponse":
        """Create from raw API response."""
        if not isinstance(data, dict):
            return cls(status="ERROR", error=f"Invalid response format: expected dict, got {type(data).__name__}")
        ode_results = data.get("ODEResults", {})
        status = ode_results.get("Status", "ERROR")

        if status == "ERROR":
            return cls(
                status=status,
                error=ode_results.get("Error"),
            )

        # Parse products
        products_data = ode_results.get("Products", {})
        product_list = products_data.get("Product", [])

        # Handle single product (dict) vs multiple (list)
        if isinstance(product_list, dict):
            product_list = [product_list]

        # Filter out non-dict items and parse valid products
        products = [ODEProduct.from_raw_data(p) for p in product_list if isinstance(p, dict)]

        # Get count
        count = _parse_int(ode_results.get("Count", len(products)))

        return cls(
            status=status,
            count=count,
            products=products,
        )


class ODEProductCountResponse(BaseModel):
    """ODE product count response."""

    status: str
    count: int = 0
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "ODEProductCountResponse":
        """Create from raw API response."""
        if not isinstance(data, dict):
            return cls(status="ERROR", error=f"Invalid response format: expected dict, got {type(data).__name__}")
        ode_results = data.get("ODEResults", {})
        status = ode_results.get("Status", "ERROR")

        if status == "ERROR":
            return cls(status=status, error=ode_results.get("Error"))

        return cls(
            status=status,
            count=_parse_int(ode_results.get("Count", 0)),
        )


class ODEInstrumentInfo(BaseModel):
    """ODE instrument/product type information."""

    model_config = ConfigDict(populate_by_name=True)

    ihid: str = Field(alias="IHID")
    ihn: str = Field(default="", alias="IHN")  # Instrument Host Name (older API format)
    ih_name: str = Field(default="", alias="IHName")  # Instrument Host Name (newer API format)
    iid: str = Field(alias="IID")
    iin: str = Field(default="", alias="IIN")  # Instrument Name (older API format)
    i_name: str = Field(default="", alias="IName")  # Instrument Name (newer API format)
    pt: str = Field(alias="PT")
    pt_name: str = Field(alias="PTName")
    number_products: int = Field(default=0, alias="NumberProducts")

    @property
    def instrument_host_name(self) -> str:
        """Get instrument host name from either API format."""
        return self.ih_name or self.ihn

    @property
    def instrument_name(self) -> str:
        """Get instrument name from either API format."""
        return self.i_name or self.iin


class ODEIIPTResponse(BaseModel):
    """ODE IIPT (Instrument/Product Type) response."""

    status: str
    instruments: list[ODEInstrumentInfo] = Field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "ODEIIPTResponse":
        """Create from raw API response."""
        if not isinstance(data, dict):
            return cls(status="ERROR", error=f"Invalid response format: expected dict, got {type(data).__name__}")
        ode_results = data.get("ODEResults", {})
        status = ode_results.get("Status", "ERROR")

        if status == "ERROR":
            return cls(status=status, error=ode_results.get("Error"))

        # Handle both "IIPT" and "IIPTSets" keys (API inconsistency)
        iipt_data = ode_results.get("IIPT", {}) or ode_results.get("IIPTSets", {})
        iipt_set = iipt_data.get("IIPTSet", [])

        # Handle single item vs list
        if isinstance(iipt_set, dict):
            iipt_set = [iipt_set]

        instruments = []
        for item in iipt_set:
            instruments.append(
                ODEInstrumentInfo(
                    IHID=item.get("IHID", ""),
                    IHN=item.get("IHN", ""),
                    IHName=item.get("IHName", ""),
                    IID=item.get("IID", ""),
                    IIN=item.get("IIN", ""),
                    IName=item.get("IName", ""),
                    PT=item.get("PT", ""),
                    PTName=item.get("PTName", ""),
                    NumberProducts=_parse_int(item.get("NumberProducts", 0)),
                )
            )

        return cls(status=status, instruments=instruments)


class ODEFeature(BaseModel):
    """ODE planetary feature."""

    feature_class: str
    feature_name: str
    min_lat: float
    max_lat: float
    west_lon: float
    east_lon: float


class ODEFeatureDataResponse(BaseModel):
    """ODE feature data response."""

    status: str
    features: list[ODEFeature] = Field(default_factory=list)
    count: int = 0
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "ODEFeatureDataResponse":
        """Create from raw JSON API response."""
        if not isinstance(data, dict):
            return cls(status="ERROR", error=f"Invalid response format: expected dict, got {type(data).__name__}")
        ode_results = data.get("ODEResults", {})
        status = ode_results.get("Status", "ERROR")

        if status == "ERROR":
            return cls(status=status, error=ode_results.get("Error"))

        features_data = ode_results.get("Features", {})
        feature_list = features_data.get("Feature", [])

        if isinstance(feature_list, dict):
            feature_list = [feature_list]

        features = []
        for f in feature_list:
            features.append(
                ODEFeature(
                    feature_class=f.get("FeatureClass", ""),
                    feature_name=f.get("FeatureName", ""),
                    min_lat=float(f.get("MinLat", 0)),
                    max_lat=float(f.get("MaxLat", 0)),
                    west_lon=float(f.get("WestLon", 0)),
                    east_lon=float(f.get("EastLon", 0)),
                )
            )

        return cls(
            status=status,
            features=features,
            count=_parse_int(ode_results.get("Count", len(features))),
        )

    @classmethod
    def from_xml(cls, xml_text: str) -> "ODEFeatureDataResponse":
        """Create from XML API response."""
        try:
            root = ET.fromstring(xml_text)

            status = root.findtext("Status", "ERROR")
            if status == "ERROR":
                return cls(status=status, error=root.findtext("Error"))

            features = []
            for feature_elem in root.findall(".//Feature"):
                features.append(
                    ODEFeature(
                        feature_class=feature_elem.findtext("FeatureClass", ""),
                        feature_name=feature_elem.findtext("FeatureName", ""),
                        min_lat=float(feature_elem.findtext("MinLat", "0")),
                        max_lat=float(feature_elem.findtext("MaxLat", "0")),
                        west_lon=float(feature_elem.findtext("WestLon", "0")),
                        east_lon=float(feature_elem.findtext("EastLon", "0")),
                    )
                )

            return cls(
                status=status,
                features=features,
                count=_parse_int(root.findtext("Count", str(len(features)))),
            )
        except ET.ParseError as e:
            return cls(status="ERROR", error=f"XML parse error: {e}")


class ODEFeatureClassesResponse(BaseModel):
    """ODE feature classes response."""

    status: str
    feature_classes: list[str] = Field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "ODEFeatureClassesResponse":
        """Create from raw API response."""
        if not isinstance(data, dict):
            return cls(status="ERROR", error=f"Invalid response format: expected dict, got {type(data).__name__}")
        ode_results = data.get("ODEResults", {})
        status = ode_results.get("Status", "ERROR")

        if status == "ERROR":
            return cls(status=status, error=ode_results.get("Error"))

        # Handle both "FeatureTypes" and "FeatureClasses" keys (API inconsistency)
        feature_types = ode_results.get("FeatureTypes", {}) or ode_results.get("FeatureClasses", {})
        feature_type_list = feature_types.get("FeatureType", []) or feature_types.get("FeatureClass", [])

        if isinstance(feature_type_list, str):
            feature_type_list = [feature_type_list]

        return cls(status=status, feature_classes=feature_type_list)


class ODEFeatureNamesResponse(BaseModel):
    """ODE feature names response."""

    status: str
    feature_names: list[str] = Field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "ODEFeatureNamesResponse":
        """Create from raw API response."""
        if not isinstance(data, dict):
            return cls(status="ERROR", error=f"Invalid response format: expected dict, got {type(data).__name__}")
        ode_results = data.get("ODEResults", {})
        status = ode_results.get("Status", "ERROR")

        if status == "ERROR":
            return cls(status=status, error=ode_results.get("Error"))

        feature_names_data = ode_results.get("FeatureNames", {})
        feature_name_list = feature_names_data.get("FeatureName", [])

        if isinstance(feature_name_list, str):
            feature_name_list = [feature_name_list]

        return cls(status=status, feature_names=feature_name_list)
