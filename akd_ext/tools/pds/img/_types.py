"""Shared type definitions for IMG Atlas tools.

This module defines common Literal types used across multiple IMG tools
to avoid repetition and ensure consistency.
"""

from typing import Literal

# Target bodies available in IMG Atlas
IMGTarget = Literal[
    "Mars",
    "Saturn",
    "Moon",
    "Mercury",
    "Titan",
    "Enceladus",
    "Jupiter",
    "Io",
    "Europa",
    "Ganymede",
    "Callisto",
]

# Missions available in IMG Atlas
IMGMission = Literal[
    "MARS EXPLORATION ROVER",
    "MARS SCIENCE LABORATORY",
    "MARS 2020",
    "CASSINI-HUYGENS",
    "VOYAGER",
    "LUNAR RECONNAISSANCE ORBITER",
    "MESSENGER",
]

# Instruments available in IMG Atlas (flattened from all missions)
IMGInstrument = Literal[
    "CHEMCAM",
    "HAZCAM",
    "ISS",
    "LROC",
    "MAHLI",
    "MARDI",
    "MASTCAM",
    "MASTCAM-Z",
    "MDIS",
    "MI",
    "NAVCAM",
    "PANCAM",
    "PIXL",
    "SHERLOC",
    "VIMS",
]

# Product types
IMGProductType = Literal["EDR", "RDR"]

# Sort fields
IMGSortField = Literal["START_TIME", "PLANET_DAY_NUMBER", "EXPOSURE_DURATION"]

# Sort order
IMGSortOrder = Literal["asc", "desc"]

# Facet fields for get_facets tool
IMGFacetField = Literal[
    "TARGET",
    "ATLAS_MISSION_NAME",
    "ATLAS_INSTRUMENT_NAME",
    "ATLAS_SPACECRAFT_NAME",
    "PRODUCT_TYPE",
    "FRAME_TYPE",
    "FILTER_NAME",
    "pds_standard",
]