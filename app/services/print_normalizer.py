"""Pure, deterministic FDM print process normalization.

Replaces the single-formula M6 approximation with a physics-grounded
decomposition: perimeter + infill + top/bottom + purge.

All functions are pure — zero database access.
"""

from dataclasses import dataclass
from math import floor
from typing import Optional


@dataclass
class ProfileParams:
    nozzle_diameter_mm: float
    layer_height_mm: float
    wall_count: int
    infill_percentage: float
    top_layers: int
    bottom_layers: int
    extrusion_width_factor: float
    volumetric_flow_rate_mm3s: float
    purge_mass_per_change_g: float


@dataclass
class NormalizationResult:
    estimated_mass_grams: float
    estimated_print_hours: float
    perimeter_g: float
    infill_g: float
    top_bottom_g: float
    purge_g: float
    confidence_level: str  # "medium" | "low"


def normalize_from_geometry(
    volume_mm3: float,
    dimensions_mm: Optional[dict[str, float]],
    density_g_cm3: float,
    profile: ProfileParams,
    color_changes: int = 0,
) -> NormalizationResult:
    """Decompose FDM mass and print time into perimeter/infill/top-bottom/purge.

    When dimensions_mm (x, y, z) are present the bounding-box rectangle
    approximation is used (confidence = "medium").  When absent the function
    falls back to the M6 volume-only formula (confidence = "low").
    """
    if dimensions_mm and all(k in dimensions_mm for k in ("x", "y", "z")):
        return _normalize_with_dimensions(
            volume_mm3, dimensions_mm, density_g_cm3, profile, color_changes
        )
    return _normalize_volume_only(volume_mm3, density_g_cm3, profile, color_changes)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_with_dimensions(
    volume_mm3: float,
    dimensions_mm: dict[str, float],
    density_g_cm3: float,
    profile: ProfileParams,
    color_changes: int,
) -> NormalizationResult:
    x = dimensions_mm["x"]
    y = dimensions_mm["y"]
    z = dimensions_mm["z"]

    extrusion_width = profile.nozzle_diameter_mm * profile.extrusion_width_factor
    layer_count = max(1, floor(z / profile.layer_height_mm))

    # Perimeter — bounding-box rectangle per layer
    perimeter_length = 2.0 * (x + y)
    perimeter_volume = (
        perimeter_length
        * profile.wall_count
        * extrusion_width
        * profile.layer_height_mm
        * layer_count
    )

    # Top + bottom solid layers
    footprint_area = x * y
    top_bottom_volume = (
        footprint_area
        * (profile.top_layers + profile.bottom_layers)
        * profile.layer_height_mm
    )

    # Internal infill
    shell_volume = perimeter_volume + top_bottom_volume
    internal_volume = max(0.0, volume_mm3 - shell_volume)
    infill_volume = internal_volume * (profile.infill_percentage / 100.0)

    # Purge mass
    purge_g = color_changes * profile.purge_mass_per_change_g

    # Convert mm³ volumes → grams  (mm³ / 1000 = cm³, × density)
    perimeter_g  = (perimeter_volume  / 1000.0) * density_g_cm3
    top_bottom_g = (top_bottom_volume / 1000.0) * density_g_cm3
    infill_g     = (infill_volume     / 1000.0) * density_g_cm3
    total_g      = perimeter_g + infill_g + top_bottom_g + purge_g

    # Print time from total extruded volume
    total_extruded = perimeter_volume + infill_volume + top_bottom_volume
    print_hours = (total_extruded / profile.volumetric_flow_rate_mm3s) / 3600.0

    return NormalizationResult(
        estimated_mass_grams=total_g,
        estimated_print_hours=print_hours,
        perimeter_g=round(perimeter_g, 4),
        infill_g=round(infill_g, 4),
        top_bottom_g=round(top_bottom_g, 4),
        purge_g=round(purge_g, 4),
        confidence_level="medium",
    )


def _normalize_volume_only(
    volume_mm3: float,
    density_g_cm3: float,
    profile: ProfileParams,
    color_changes: int,
) -> NormalizationResult:
    """M6 fallback: single-formula approximation."""
    volume_cm3 = volume_mm3 / 1000.0
    infill_g = volume_cm3 * density_g_cm3 * (profile.infill_percentage / 100.0)
    purge_g  = color_changes * profile.purge_mass_per_change_g
    total_g  = infill_g + purge_g

    actual_volume = volume_mm3 * (profile.infill_percentage / 100.0)
    print_hours = (actual_volume / profile.volumetric_flow_rate_mm3s) / 3600.0

    return NormalizationResult(
        estimated_mass_grams=total_g,
        estimated_print_hours=print_hours,
        perimeter_g=0.0,
        infill_g=round(infill_g, 4),
        top_bottom_g=0.0,
        purge_g=round(purge_g, 4),
        confidence_level="low",
    )
