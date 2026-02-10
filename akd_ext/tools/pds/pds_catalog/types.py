"""PDS Catalog type definitions.

Shared type definitions for PDS Catalog tools.
"""

from typing import Literal

# Valid PDS node types
PDS_NODE = Literal["atm", "geo", "img", "naif", "ppi", "rms", "sbn"]

# Valid PDS archive versions
PDS_VERSION = Literal["PDS3", "PDS4"]

# Valid dataset types
DATASET_TYPE = Literal["volume", "bundle", "collection"]

# Valid field profile levels
FIELD_PROFILE = Literal["essential", "summary", "full"]
