"""Cost engine service.

Orchestrates data already retrieved from the database into pure calculation
calls.  No database access occurs here — all inputs are explicit parameters.
"""

from app.calculations import (
    DEFAULT_PRICING_MULTIPLIER,
    DEFAULT_WASTE_FACTOR,
    AssetUsage,
    MaterialUsage,
    calculate_asset_cost,
    calculate_labor_cost,
    calculate_machine_cost,
    calculate_material_cost,
    calculate_profit_margin,
    calculate_suggested_price,
    calculate_true_cost,
)
from app.services.amortization import calculate_machine_hourly_rate


def compute_product_cost(
    print_hours: float,
    labor_minutes: int,
    hardware_cost: float,
    purchase_cost: float,
    lifetime_hours: float,
    maintenance_factor: float,
    materials: list[MaterialUsage],
    assets: list[AssetUsage] = [],
    target_hourly_rate: float = 25.0,
    pricing_multiplier: float = DEFAULT_PRICING_MULTIPLIER,
    waste_factor: float = DEFAULT_WASTE_FACTOR,
) -> dict:
    """Return a complete cost breakdown for a product.

    All inputs are explicit parameters — the caller is responsible for loading
    data from the database before invoking this function.

    Returns a dict with keys:
        true_cost, suggested_price, profit_margin,
        material_cost, machine_cost, labor_cost, machine_hourly_rate, asset_cost
    """
    machine_hourly_rate: float = calculate_machine_hourly_rate(
        purchase_cost=purchase_cost,
        lifetime_hours=lifetime_hours,
        maintenance_factor=maintenance_factor,
    )

    material_cost: float = calculate_material_cost(
        materials=materials,
        waste_factor=waste_factor,
    )
    machine_cost: float = calculate_machine_cost(
        print_hours=print_hours,
        machine_hourly_rate=machine_hourly_rate,
    )
    labor_cost: float = calculate_labor_cost(
        labor_minutes=labor_minutes,
        target_hourly_rate=target_hourly_rate,
    )
    asset_cost: float = sum(
        calculate_asset_cost(a.design_hours, a.labor_rate, a.target_uses)
        for a in assets
    )
    true_cost: float = calculate_true_cost(
        material_cost=material_cost,
        machine_cost=machine_cost,
        labor_cost=labor_cost,
        hardware_cost=hardware_cost,
        asset_cost=asset_cost,
    )
    suggested_price: float = calculate_suggested_price(
        true_unit_cost=true_cost,
        pricing_multiplier=pricing_multiplier,
    )
    profit_margin: float = calculate_profit_margin(
        true_cost=true_cost,
        suggested_price=suggested_price,
    )

    return {
        "true_cost": round(true_cost, 2),
        "suggested_price": round(suggested_price, 2),
        "profit_margin": profit_margin,
        "material_cost": round(material_cost, 2),
        "machine_cost": round(machine_cost, 4),
        "labor_cost": round(labor_cost, 2),
        "machine_hourly_rate": round(machine_hourly_rate, 4),
        "asset_cost": round(asset_cost, 2),
    }
