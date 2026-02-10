"""OPUS type definitions.

Shared type definitions for OPUS tools based on the OPUS API
and MCP resource definitions.
"""

from typing import Literal

# Valid planets in OPUS database
OPUS_PLANETS = Literal["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Other"]

# Valid missions in OPUS database
OPUS_MISSIONS = Literal["Cassini", "Voyager 1", "Voyager 2", "Galileo", "New Horizons", "Juno", "Hubble"]

# Valid instruments in OPUS database (from MCP resource://opus_instruments)
# Organized by mission for clarity
OPUS_INSTRUMENTS = Literal[
    # Cassini
    "ISS",
    "VIMS",
    "UVIS",
    "CIRS",
    "RSS",
    # Voyager
    "IRIS",
    # Galileo
    "SSI",
    # New Horizons
    "LORRI",
    "MVIC",
    # Juno
    "JunoCam",
    "JIRAM",
    # Hubble
    "WFPC2",
    "WFC3",
    "ACS",
    "STIS",
    "NICMOS",
]
