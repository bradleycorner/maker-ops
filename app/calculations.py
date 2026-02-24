"""Pure, deterministic calculation functions.

These functions accept explicit parameters and perform zero database access.
Identical inputs always produce identical outputs.
"""

from dataclasses import dataclass

DEFAULT_PRICING_MULTIPLIER: float = 2.7
DEFAULT_WASTE_FACTOR: float = 1.1


@dataclass
class MaterialUsage:
    """Represents the quantity and unit cost of one material in a product."""

    grams_used: float
    cost_per_gram: float


@dataclass
class AssetUsage:
    """Represents the amortized cost of an engineering asset."""

    design_hours: float
    labor_rate: float
    target_uses: int


def calculate_material_cost(
    materials: list[MaterialUsage],
    waste_factor: float = DEFAULT_WASTE_FACTOR,
) -> float:
    """Return total material cost including the waste/failure allowance.

    Formula:
        material_cost = SUM(grams_used * cost_per_gram) * waste_factor
    """
    raw_cost: float = sum(m.grams_used * m.cost_per_gram for m in materials)
    return raw_cost * waste_factor


def calculate_machine_cost(
    print_hours: float,
    machine_hourly_rate: float,
) -> float:
    """Return the machine usage cost for a given print job.

    Formula:
        machine_cost = print_hours * machine_hourly_rate
    """
    return print_hours * machine_hourly_rate


def calculate_labor_cost(
    labor_minutes: int,
    target_hourly_rate: float,
) -> float:
    """Return labor cost based on post-processing and assembly time.

    Formula:
        labor_cost = (labor_minutes / 60) * target_hourly_rate
    """
    return (labor_minutes / 60.0) * target_hourly_rate


def calculate_asset_cost(
    design_hours: float,
    labor_rate: float,
    target_uses: int,
) -> float:
    """Return the amortized engineering asset cost for a single product unit.

    Formula:
        asset_unit_cost = (design_hours * labor_rate) / target_uses
    """
    if target_uses <= 0:
        return 0.0
    return (design_hours * labor_rate) / target_uses


def calculate_true_cost(
    material_cost: float,
    machine_cost: float,
    labor_cost: float,
    hardware_cost: float,
    asset_cost: float = 0.0,
) -> float:
    """Return the true unit cost from all cost components.

    Formula:
        true_unit_cost = material_cost + machine_cost + labor_cost + hardware_cost + asset_cost
    """
    return material_cost + machine_cost + labor_cost + hardware_cost + asset_cost


def calculate_suggested_price(
    true_unit_cost: float,
    pricing_multiplier: float = DEFAULT_PRICING_MULTIPLIER,
) -> float:
    """Return the suggested retail price.

    Formula:
        suggested_retail_price = true_unit_cost * pricing_multiplier
    """
    return true_unit_cost * pricing_multiplier


def calculate_profit_margin(
    true_cost: float,
    suggested_price: float,
) -> float:
    """Return profit margin as a percentage of the suggested retail price."""
    if suggested_price == 0.0:
        return 0.0
    return round(((suggested_price - true_cost) / suggested_price) * 100, 2)


def calculate_profit_per_hour(
    true_cost: float,
    suggested_price: float,
    print_hours: float,
) -> float:
    """Return the profit earned per hour of machine time.

    Formula:
        profit_per_print_hour = (suggested_price - true_cost) / print_hours
    """
    if print_hours <= 0:
        return 0.0
    return (suggested_price - true_cost) / print_hours


# ---------------------------------------------------------------------------
# Geometric Estimation
# ---------------------------------------------------------------------------

def calculate_mass_from_volume(
    volume_mm3: float,
    material_density_g_cm3: float = 1.25,  # PLA default
    infill_percentage: float = 20.0,
) -> float:
    """Return estimated mass in grams from geometry.

    Formula:
        mass = (volume / 1000) * density * (infill / 100)
    """
    volume_cm3 = volume_mm3 / 1000.0
    return volume_cm3 * material_density_g_cm3 * (infill_percentage / 100.0)


def calculate_print_time_from_flow(
    volume_mm3: float,
    volumetric_flow_rate_mm3_s: float = 10.0,
    infill_percentage: float = 20.0,
) -> float:
    """Return estimated print time in hours from geometry.

    Formula:
        hours = (volume * (infill/100) / flow_rate) / 3600
    """
    if volumetric_flow_rate_mm3_s <= 0:
        return 0.0
    actual_volume = volume_mm3 * (infill_percentage / 100.0)
    seconds = actual_volume / volumetric_flow_rate_mm3_s
    return seconds / 3600.0
