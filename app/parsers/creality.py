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

# Optional metadata — supports both : and = separators, and space or underscore
# between words (V7 uses layer_height / nozzle_diameter; legacy uses spaces)
_LAYER_HEIGHT_PATTERN  = re.compile(r";\s*layer[\s_]height\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_NOZZLE_PATTERN        = re.compile(r";\s*nozzle[\s_]diameter\s*[=:]\s*([\d.]+)", re.IGNORECASE)

# V7 / OrcaSlicer extras
_WALL_COUNT_PATTERN    = re.compile(r";\s*wall loops\s*[=:]\s*(\d+)", re.IGNORECASE)
_INFILL_PCT_PATTERN    = re.compile(r";\s*sparse infill density\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_SPEED_OUTER_PATTERN   = re.compile(r";\s*outer wall speed\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_SPEED_INNER_PATTERN   = re.compile(r";\s*inner wall speed\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_SPEED_INFILL_PATTERN  = re.compile(r";\s*sparse infill speed\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_FILAMENT_VOL_PATTERN  = re.compile(r";\s*filament used\s*\[mm3\]\s*[=:]\s*([\d.]+)", re.IGNORECASE)


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

        def _float(pattern: re.Pattern) -> float | None:
            m = pattern.search(text)
            return float(m.group(1)) if m else None

        def _int(pattern: re.Pattern) -> int | None:
            m = pattern.search(text)
            return int(m.group(1)) if m else None

        return PrintEstimate(
            filament_grams=filament_grams,
            print_time_seconds=print_time_seconds,
            slicer_name="creality",
            layer_height=_float(_LAYER_HEIGHT_PATTERN),
            nozzle_diameter=_float(_NOZZLE_PATTERN),
            wall_count=_int(_WALL_COUNT_PATTERN),
            infill_percentage=_float(_INFILL_PCT_PATTERN),
            speed_wall_outer_mm_s=_float(_SPEED_OUTER_PATTERN),
            speed_wall_inner_mm_s=_float(_SPEED_INNER_PATTERN),
            speed_infill_mm_s=_float(_SPEED_INFILL_PATTERN),
        )
