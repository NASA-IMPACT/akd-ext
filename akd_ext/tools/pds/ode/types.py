"""Shared type definitions for ODE tools."""

from typing import Literal

# Supported planetary targets in the ODE system
TargetType = Literal["mars", "moon", "mercury", "phobos", "deimos", "venus"]
