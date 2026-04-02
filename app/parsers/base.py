"""Base parser interface for G-code ingestion.

All parsers are pure text translators — no database access, no pricing logic.
They receive raw G-code text and return a normalized PrintEstimate.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PrintEstimate:
    """Normalized output produced by any G-code parser.

    Required fields must be populated by every parser.
    Optional fields may be None when the slicer does not emit them.
    """

    filament_grams: float
    print_time_seconds: int
    slicer_name: str
    source: str = "gcode"
    layer_height: Optional[float] = None
    nozzle_diameter: Optional[float] = None
    # V7 / OrcaSlicer extras
    wall_count: Optional[int] = None
    infill_percentage: Optional[float] = None
    speed_wall_outer_mm_s: Optional[float] = None
    speed_wall_inner_mm_s: Optional[float] = None
    speed_infill_mm_s: Optional[float] = None
    filament_volume_cm3: Optional[float] = None


class BaseParser(ABC):
    """Contract that every G-code parser must satisfy."""

    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Return True if this parser recognises the file format."""

    @abstractmethod
    def extract(self, text: str) -> PrintEstimate:
        """Return a normalized PrintEstimate from G-code header text.

        Must not perform database access or pricing calculations.
        """
