"""Machine amortization calculations.

Computes the effective hourly operating cost of a machine, factoring in
purchase price, expected lifetime, and ongoing maintenance overhead.
"""


def calculate_machine_hourly_rate(
    purchase_cost: float,
    lifetime_hours: float,
    maintenance_factor: float,
) -> float:
    """Return the amortized hourly rate for a machine.

    Formula:
        machine_hourly_rate = (purchase_cost / lifetime_hours) * (1 + maintenance_factor)

    Args:
        purchase_cost: Original purchase price of the machine in USD.
        lifetime_hours: Expected total usable hours over the machine's life.
        maintenance_factor: Fractional overhead for maintenance (e.g. 0.15 = 15 %).

    Raises:
        ValueError: If lifetime_hours is not positive.
    """
    if lifetime_hours <= 0:
        raise ValueError(f"lifetime_hours must be > 0, got {lifetime_hours}")
    return (purchase_cost / lifetime_hours) * (1.0 + maintenance_factor)
