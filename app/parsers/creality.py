"""Creality G-code parser.

Handles output from Creality Print and Creality Slicer.
Detects the format via header markers and extracts filament usage and
print time from structured comment lines.

Expected header examples:
    ;Filament used: 486.9g
    ;Estimated printing time (normal mode): 9h5m
"""

import re

from app.parsers.base import BaseParser, PrintEstimate

_DETECTION_MARKERS: tuple[str, ...] = (
    "creality",
    "crealityprint",
)

# ;Filament used: 486.9g
_FILAMENT_PATTERN = re.compile(r";\s*filament used\s*:\s*([\d.]+)\s*g", re.IGNORECASE)

# ;Estimated printing time (normal mode): 9h5m  /  2h30m  /  45m  /  1h
_TIME_PATTERN = re.compile(
    r";\s*estimated printing time[^:]*:\s*(?:(\d+)h)?\s*(?:(\d+)m)?",
    re.IGNORECASE,
)

# Optional metadata
_LAYER_HEIGHT_PATTERN = re.compile(r";\s*layer height\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_NOZZLE_PATTERN = re.compile(r";\s*nozzle diameter\s*[=:]\s*([\d.]+)", re.IGNORECASE)


def _parse_time_to_seconds(hours: str | None, minutes: str | None) -> int:
    h = int(hours) if hours else 0
    m = int(minutes) if minutes else 0
    return h * 3600 + m * 60


class CrealityGcodeParser(BaseParser):
    """Parser for Creality Print / Creality Slicer G-code output."""

    def can_parse(self, text: str) -> bool:
        lower = text.lower()
        return any(marker in lower for marker in _DETECTION_MARKERS)

    def extract(self, text: str) -> PrintEstimate:
        filament_match = _FILAMENT_PATTERN.search(text)
        if not filament_match:
            raise ValueError("CrealityGcodeParser: filament usage not found in header")

        time_match = _TIME_PATTERN.search(text)
        if not time_match:
            raise ValueError("CrealityGcodeParser: print time not found in header")

        filament_grams = float(filament_match.group(1))
        print_time_seconds = _parse_time_to_seconds(
            time_match.group(1), time_match.group(2)
        )

        layer_height: float | None = None
        layer_match = _LAYER_HEIGHT_PATTERN.search(text)
        if layer_match:
            layer_height = float(layer_match.group(1))

        nozzle_diameter: float | None = None
        nozzle_match = _NOZZLE_PATTERN.search(text)
        if nozzle_match:
            nozzle_diameter = float(nozzle_match.group(1))

        return PrintEstimate(
            filament_grams=filament_grams,
            print_time_seconds=print_time_seconds,
            slicer_name="creality",
            layer_height=layer_height,
            nozzle_diameter=nozzle_diameter,
        )
