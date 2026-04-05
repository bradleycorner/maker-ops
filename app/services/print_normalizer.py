"""Pure, deterministic FDM print process normalization.

Replaces the single-formula M6 approximation with a physics-grounded
decomposition: perimeter + infill + top/bottom + purge.

All functions are pure — zero database access.
"""

from dataclasses import dataclass, field
from math import floor
from typing import Optional

# Travel moves (rapid positioning) consume ~12-15% of total print time.
# This factor is applied on top of extrusion time to approximate wall-clock time.
_TRAVEL_OVERHEAD = 1.15


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
    speed_wall_mm_s: float = 200.0   # outer + inner wall speed (conservative: use outer)
    speed_infill_mm_s: float = 250.0


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
    lateral_surface_area_mm2: Optional[float] = None,
) -> NormalizationResult:
    """Decompose FDM mass and print time into perimeter/infill/top-bottom/purge.

    When dimensions_mm (x, y, z) are present the normalizer uses a
    volume-derived cross-section for top/bottom area and either the
    FreeCAD lateral surface area (when provided) or a bounding-box
    rectangle approximation for perimeter length (confidence = "medium").

    When absent the function falls back to the M6 volume-only formula
    (confidence = "low").

    Args:
        lateral_surface_area_mm2: Total lateral surface area of the shape
            as reported by FreeCAD's shape.Area (mm²). When provided this
            replaces the bounding-box rectangle perimeter approximation and
            correctly handles hollow, ribbed, and faceted geometry.
    """
    if dimensions_mm and all(k in dimensions_mm for k in ("x", "y", "z")):
        return _normalize_with_dimensions(
            volume_mm3, dimensions_mm, density_g_cm3, profile, color_changes,
            lateral_surface_area_mm2,
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
    lateral_surface_area_mm2: Optional[float],
) -> NormalizationResult:
    x = dimensions_mm["x"]
    y = dimensions_mm["y"]
    z = dimensions_mm["z"]

    extrusion_width = profile.nozzle_diameter_mm * profile.extrusion_width_factor
    layer_count = max(1, floor(z / profile.layer_height_mm))

    # Perimeter length per layer — used for MASS calculation only.
    # Bounding-box rectangle is used here regardless of lateral_surface_area_mm2
    # because shape.Area includes horizontal faces (ribs, top, bottom) which would
    # inflate the mass estimate.  The volume/z footprint fix below handles the
    # top/bottom overestimate.  shape.Area is used only for time (see below).
    perimeter_length = 2.0 * (x + y)

    perimeter_volume = (
        perimeter_length
        * profile.wall_count
        * extrusion_width
        * profile.layer_height_mm
        * layer_count
    )

    # Top + bottom solid layers.
    # Use volume-derived cross-section instead of bounding-box x*y footprint.
    # x*y overestimates hollow/thin-wall geometry by as much as 7.5×.
    footprint_area = volume_mm3 / z if z > 0 else x * y
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

    # Print time.
    #
    # When lateral_surface_area_mm2 is available (from FreeCAD shape.Area) we
    # use a speed-aware path-length calculation that correctly handles ribbed and
    # hollow geometry.  shape.Area captures the actual tool-path surface so
    # lateral_area/z gives a realistic per-layer path length.
    #
    # Without shape.Area we fall back to the volumetric flow rate approach (same
    # as M6) to avoid regressing accuracy on shapes where bounding-box perimeter
    # is the only available approximation.
    wall_xsec = extrusion_width * profile.layer_height_mm
    if lateral_surface_area_mm2 and lateral_surface_area_mm2 > 0 and z > 0:
        # Speed-based: wall path derived from actual surface area
        time_perimeter_length = lateral_surface_area_mm2 / z
        wall_length_mm   = time_perimeter_length * profile.wall_count * layer_count
        infill_length_mm = (infill_volume / wall_xsec) if wall_xsec > 0 else 0.0
        wall_time_s   = (wall_length_mm   / profile.speed_wall_mm_s)   if profile.speed_wall_mm_s   > 0 else 0.0
        infill_time_s = (infill_length_mm / profile.speed_infill_mm_s) if profile.speed_infill_mm_s > 0 else 0.0
        print_hours   = ((wall_time_s + infill_time_s) * _TRAVEL_OVERHEAD) / 3600.0
    else:
        # Volumetric flow rate fallback — no regression vs M7 baseline
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
