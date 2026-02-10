"""PDS4 type definitions.

Shared type definitions for PDS4 tools based on the PDS4 registry API.
"""

from typing import Literal

# Processing levels for PDS4 data products
PROCESSING_LEVEL = Literal["Raw", "Calibrated", "Derived"]

# Instrument host types
INSTRUMENT_HOST_TYPE = Literal["Rover", "Lander", "Spacecraft"]

# Instrument types from PDS4 registry
INSTRUMENT_TYPE = Literal[
    "Energetic Particle Detector",
    "Plasma Analyzer",
    "Regolith Properties",
    "Spectrograph",
    "Imager",
    "Atmospheric Sciences",
    "Spectrometer",
    "Radio-Radar",
    "Ultraviolet Spectrometer",
    "Small Bodies Sciences",
    "Dust",
    "Particle Detector",
    "Photometer",
    "Polarimeter",
    "Plasma Wave Spectrometer",
]

# Target types from PDS4 registry
TARGET_TYPE = Literal[
    "Planetary Nebula",
    "Galaxy",
    "Calibrator",
    "Trans-Neptunian Object",
    "Planetary System",
    "Satellite",
    "Centaur",
    "Astrophysical",
    "Star Cluster",
    "Laboratory Analog",
    "Dust",
    "Asteroid",
    "Comet",
    "Equipment",
    "Star",
    "Ring",
    "Dwarf Planet",
    "Calibration Field",
    "Planet",
    "Plasma Cloud",
    "Plasma Stream",
    "Magnetic Field",
]
