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
