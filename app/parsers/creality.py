"""Creality G-code parser.

Handles output from Creality Print and Creality Slicer.
Detects the format via header markers and extracts filament usage and
print time from structured comment lines.

Supports three header formats:

    Legacy:
        ;Filament used: 486.9g
        ;Estimated printing time (normal mode): 9h5m

    V7 / OrcaSlicer (single/dual extruder):
        ;Filament used: [486.9g, 0g]
        ;Estimated printing time (normal mode): 13h 28m 58s

    V7 K2 Plus (multi-extruder, unit-labelled):
        ; filament used [g] = 0.00, 0.00, 0.00, 269.17
        ; estimated printing time (normal mode) = 6h 33m 24s
        Values are per-extruder; all are summed for total filament.
"""

import re

from app.parsers.base import BaseParser, PrintEstimate

_DETECTION_MARKERS: tuple[str, ...] = (
    "creality",
    "crealityprint",
)

# Handles:
#   ;Filament used: 486.9g                    (legacy)
#   ;Filament used: [486.9g, 0g]              (V7 bracket array)
_FILAMENT_PATTERN = re.compile(
    r";\s*filament used\s*[=:]\s*\[?([\d.]+)g",
    re.IGNORECASE,
)

# Handles:
#   ; filament used [g] = 0.00, 0.00, 0.00, 269.17    (K2 Plus multi-extruder)
# All per-extruder values are summed to get total filament.
_FILAMENT_K2_PATTERN = re.compile(
    r";\s*filament used\s*\[g\]\s*=\s*([\d.,\s]+)",
    re.IGNORECASE,
)

# Handles both:
#   9h5m
#   13h 28m 58s
_TIME_PATTERN = re.compile(
    r";\s*estimated printing time[^:=]*[=:]\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?",
    re.IGNORECASE,
)

# Optional metadata — supports both : and = separators
_LAYER_HEIGHT_PATTERN  = re.compile(r";\s*layer height\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_NOZZLE_PATTERN        = re.compile(r";\s*nozzle diameter\s*[=:]\s*([\d.]+)", re.IGNORECASE)

# V7 / OrcaSlicer extras
_WALL_COUNT_PATTERN    = re.compile(r";\s*wall loops\s*[=:]\s*(\d+)", re.IGNORECASE)
_INFILL_PCT_PATTERN    = re.compile(r";\s*sparse infill density\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_SPEED_OUTER_PATTERN   = re.compile(r";\s*outer wall speed\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_SPEED_INNER_PATTERN   = re.compile(r";\s*inner wall speed\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_SPEED_INFILL_PATTERN  = re.compile(r";\s*sparse infill speed\s*[=:]\s*([\d.]+)", re.IGNORECASE)
_FILAMENT_VOL_PATTERN  = re.compile(r";\s*filament used\s*\[mm3\]\s*[=:]\s*([\d.]+)", re.IGNORECASE)


def _sum_extruder_values(raw: str) -> float:
    """Sum comma-separated per-extruder filament values (K2 Plus format)."""
    return sum(float(v.strip()) for v in raw.split(",") if v.strip())


def _parse_time_to_seconds(
    hours: str | None, minutes: str | None, seconds: str | None
) -> int:
    h = int(hours) if hours else 0
    m = int(minutes) if minutes else 0
    s = int(seconds) if seconds else 0
    return h * 3600 + m * 60 + s


def _optional_float(match: re.Match | None, group: int = 1) -> float | None:
    return float(match.group(group)) if match else None


def _optional_int(match: re.Match | None, group: int = 1) -> int | None:
    return int(match.group(group)) if match else None


class CrealityGcodeParser(BaseParser):
    """Parser for Creality Print / Creality Slicer G-code output.

    Handles both legacy (pre-V7) and V7 / OrcaSlicer header formats.
    """

    def can_parse(self, text: str) -> bool:
        lower = text.lower()
        return any(marker in lower for marker in _DETECTION_MARKERS)

    def extract(self, text: str) -> PrintEstimate:
        # Try bracket/legacy format first, then K2 Plus unit-labelled format
        filament_match = _FILAMENT_PATTERN.search(text)
        k2_match = _FILAMENT_K2_PATTERN.search(text)

        if filament_match:
            filament_grams = float(filament_match.group(1))
        elif k2_match:
            filament_grams = _sum_extruder_values(k2_match.group(1))
        else:
            raise ValueError("CrealityGcodeParser: filament usage not found in header")

        time_match = _TIME_PATTERN.search(text)
        if not time_match:
            raise ValueError("CrealityGcodeParser: print time not found in header")
        print_time_seconds = _parse_time_to_seconds(
            time_match.group(1), time_match.group(2), time_match.group(3)
        )

        return PrintEstimate(
            filament_grams=filament_grams,
            print_time_seconds=print_time_seconds,
            slicer_name="creality",
            layer_height=_optional_float(_LAYER_HEIGHT_PATTERN.search(text)),
            nozzle_diameter=_optional_float(_NOZZLE_PATTERN.search(text)),
            wall_count=_optional_int(_WALL_COUNT_PATTERN.search(text)),
            infill_percentage=_optional_float(_INFILL_PCT_PATTERN.search(text)),
            speed_wall_outer_mm_s=_optional_float(_SPEED_OUTER_PATTERN.search(text)),
            speed_wall_inner_mm_s=_optional_float(_SPEED_INNER_PATTERN.search(text)),
            speed_infill_mm_s=_optional_float(_SPEED_INFILL_PATTERN.search(text)),
            filament_volume_cm3=_optional_float(_FILAMENT_VOL_PATTERN.search(text)),
        )
