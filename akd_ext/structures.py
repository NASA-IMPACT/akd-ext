"""Common data structures and enums for akd_ext."""

from enum import StrEnum


class NASASMDDivision(StrEnum):
    """NASA Science Mission Directorate (SMD) divisions."""

    ASTROPHYSICS = "Astrophysics"
    HELIOPHYSICS = "Heliophysics"
    EARTH_SCIENCE = "Earth Science"
    BIOLOGICAL_PHYSICAL_SCIENCES = "Biological and Physical Sciences"
    PLANETARY_SCIENCE = "Planetary Science"
    OTHER = "Other"


class SDEIndexedDocumentType(StrEnum):
    """Document types available in the SDE."""

    DATA = "Data"
    IMAGES = "Images"
    DOCUMENTATION = "Documentation"
    SOFTWARE_TOOLS = "Software and Tools"
    MISSIONS_INSTRUMENTS = "Missions and Instruments"


class EONETCategory(StrEnum):
    """EONET v3 event categories. Values match the IDs accepted by the EONET API."""

    DROUGHT = "drought"
    DUST_HAZE = "dustHaze"
    EARTHQUAKES = "earthquakes"
    FLOODS = "floods"
    LANDSLIDES = "landslides"
    MANMADE = "manmade"
    SEA_LAKE_ICE = "seaLakeIce"
    SEVERE_STORMS = "severeStorms"
    SNOW = "snow"
    TEMP_EXTREMES = "tempExtremes"
    VOLCANOES = "volcanoes"
    WATER_COLOR = "waterColor"
    WILDFIRES = "wildfires"


class EONETStatus(StrEnum):
    """EONET event lifecycle status filter."""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"
