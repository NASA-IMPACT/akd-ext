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
