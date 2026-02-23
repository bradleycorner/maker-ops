"""Generic G-code parser — fallback for unrecognised slicer formats.

Searches for the most common comment patterns shared across slicers
(PrusaSlicer, OrcaSlicer, Bambu Studio, Cura, etc.).  Always reports
itself as capable of parsing so it functions as a last-resort fallback.

Supported comment patterns:
    Filament  — ;filament used [g]:  /  ;filament used:  /  ;material:
    Time      — ;estimated printing time:  /  ;print time:  /  ;TIME:
"""

import re

from app.parsers.base import BaseParser, PrintEstimate

# Filament in grams — covers multiple slicer conventions
_FILAMENT_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r";\s*filament used \[g\]\s*[=:]\s*([\d.]+)", re.IGNORECASE),
    re.compile(r";\s*filament used\s*[=:]\s*([\d.]+)\s*g", re.IGNORECASE),
    re.compile(r";\s*material\s*[=:]\s*([\d.]+)\s*g", re.IGNORECASE),
    re.compile(r";\s*total filament used\s*[=:]\s*([\d.]+)\s*g", re.IGNORECASE),
)

# Time in seconds — Cura/Bambu emit raw seconds with ;TIME:
_TIME_SECONDS_PATTERN = re.compile(r"^;TIME:\s*(\d+)", re.IGNORECASE | re.MULTILINE)

# Time as human-readable duration: 9h5m  /  2h 30m  /  45m  /  1h
# Separator may be ':' (Creality-style) or '=' (PrusaSlicer-style)
_TIME_HUMAN_PATTERN = re.compile(
    r";\s*(?:estimated printing time|print time)[^:=]*[=:]\s*(?:(\d+)h)?\s*(?:(\d+)m)?",
    re.IGNORECASE,
)

_LAYER_HEIGHT_PATTERN = re.compile(r";\s*layer height\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_NOZZLE_PATTERN = re.compile(r";\s*nozzle diameter\s*[=:]\s*([\d.]+)", re.IGNORECASE)


def _find_filament_grams(text: str) -> float | None:
    for pattern in _FILAMENT_PATTERNS:
        m = pattern.search(text)
        if m:
            return float(m.group(1))
    return None


def _find_print_time_seconds(text: str) -> int | None:
    m = _TIME_SECONDS_PATTERN.search(text)
    if m:
        return int(m.group(1))

    m = _TIME_HUMAN_PATTERN.search(text)
    if m:
        hours = int(m.group(1)) if m.group(1) else 0
        minutes = int(m.group(2)) if m.group(2) else 0
        total = hours * 3600 + minutes * 60
        if total > 0:
            return total

    return None


class GenericGcodeParser(BaseParser):
    """Fallback parser covering common slicer comment conventions."""

    def can_parse(self, text: str) -> bool:
        return True  # always attempt as last resort

    def extract(self, text: str) -> PrintEstimate:
        filament_grams = _find_filament_grams(text)
        if filament_grams is None:
            raise ValueError(
                "GenericGcodeParser: filament usage not found — "
                "file may not contain recognisable G-code metadata"
            )

        print_time_seconds = _find_print_time_seconds(text)
        if print_time_seconds is None:
            raise ValueError(
                "GenericGcodeParser: print time not found — "
                "file may not contain recognisable G-code metadata"
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
            slicer_name="generic",
            layer_height=layer_height,
            nozzle_diameter=nozzle_diameter,
        )
