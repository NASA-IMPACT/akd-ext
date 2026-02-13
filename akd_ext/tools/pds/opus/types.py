"""OPUS type definitions.

Shared type definitions for OPUS tools based on the OPUS API
and MCP resource definitions.
"""

from typing import Literal

# Valid planets in OPUS database
OPUS_PLANETS = Literal["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Other"]

# Valid missions in OPUS database
OPUS_MISSIONS = Literal["Cassini", "Voyager 1", "Voyager 2", "Galileo", "New Horizons", "Juno", "Hubble"]

# Valid instruments in OPUS database.
# Values must match the full instrument names expected by the OPUS API
# ``instrument`` query parameter (e.g. "Cassini ISS", not just "ISS").
OPUS_INSTRUMENTS = Literal[
    # Cassini
    "Cassini ISS",
    "Cassini VIMS",
    "Cassini UVIS",
    "Cassini CIRS",
    "Cassini RSS",
    # Voyager
    "Voyager ISS",
    "Voyager IRIS",
    # Galileo
    "Galileo SSI",
    # New Horizons
    "New Horizons LORRI",
    "New Horizons MVIC",
    # Juno
    "Juno JunoCam",
    "Juno JIRAM",
    # Hubble
    "Hubble WFPC2",
    "Hubble WFC3",
    "Hubble ACS",
    "Hubble STIS",
    "Hubble NICMOS",
]
