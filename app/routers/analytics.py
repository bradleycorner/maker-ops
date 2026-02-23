from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.calculations import MaterialUsage
from app.database import get_db
from app.schemas import ShowAnalytics
from app.services.cost_engine import compute_product_cost

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/shows/{show_id}", response_model=ShowAnalytics)
def get_show_analytics(show_id: int, db: Session = Depends(get_db)) -> ShowAnalytics:
    """Return performance analytics for a single show.

    Calculates:
        total_show_cost  = booth_cost + travel_cost
        total_revenue    = SUM(quantity_sold * sale_price)
        profit           = total_revenue - total_show_cost
        revenue_per_hour = total_revenue / duration_hours
        break_even_units = total_show_cost / avg_product_profit
    """
    show = db.query(models.Show).filter(models.Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    sales = db.query(models.ShowSale).filter(models.ShowSale.show_id == show_id).all()

    total_show_cost: float = show.booth_cost + show.travel_cost
    total_revenue: float = sum(s.quantity_sold * s.sale_price for s in sales)
    units_sold: int = sum(s.quantity_sold for s in sales)
    profit: float = total_revenue - total_show_cost
    revenue_per_hour: float = (
        total_revenue / show.duration_hours if show.duration_hours > 0 else 0.0
    )

    # Compute avg_product_profit per unit using the cost engine.
    # Each sale line contributes (sale_price - true_cost) per unit sold.
    weighted_profits: list[float] = []
    for sale in sales:
        product = sale.product
        machine = product.machine
        materials = [
            MaterialUsage(grams_used=pm.grams_used, cost_per_gram=pm.material.cost_per_gram)
            for pm in product.product_materials
        ]
        result = compute_product_cost(
            print_hours=product.print_hours,
            labor_minutes=product.labor_minutes,
            hardware_cost=product.hardware_cost,
            purchase_cost=machine.purchase_cost,
            lifetime_hours=machine.lifetime_hours,
            maintenance_factor=machine.maintenance_factor,
            materials=materials,
        )
        unit_profit = sale.sale_price - result["true_cost"]
        weighted_profits.extend([unit_profit] * sale.quantity_sold)

    avg_product_profit: float = (
        sum(weighted_profits) / len(weighted_profits) if weighted_profits else 0.0
    )
    break_even_units: float = (
        total_show_cost / avg_product_profit if avg_product_profit > 0 else 0.0
    )

    return ShowAnalytics(
        show_id=show.id,
        show_name=show.name,
        total_show_cost=round(total_show_cost, 2),
        total_revenue=round(total_revenue, 2),
        profit=round(profit, 2),
        revenue_per_hour=round(revenue_per_hour, 2),
        break_even_units=round(break_even_units, 2),
        units_sold=units_sold,
    )
