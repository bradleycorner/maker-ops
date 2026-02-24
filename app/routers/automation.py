from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Body

from app import models
from app.calculations import AssetUsage, MaterialUsage
from app.database import get_db
from app.schemas import BatchCalculationRequest, BatchCalculationResponse, CalculationResult
from app.services.cost_engine import compute_product_cost

router = APIRouter(prefix="/automation", tags=["Automation"])


@router.post("/batch-calculate", response_model=BatchCalculationResponse)
def batch_calculate_products(
    request: BatchCalculationRequest,
    db: Session = Depends(get_db),
) -> BatchCalculationResponse:
    """Perform cost calculations for a list of products in a single call."""
    results = {}
    for product_id in request.product_ids:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            continue
        
        machine = product.machine
        if not machine:
            continue

        materials = [
            MaterialUsage(grams_used=pm.grams_used, cost_per_gram=pm.material.cost_per_gram)
            for pm in product.product_materials
        ]
        assets = [
            AssetUsage(
                design_hours=pa.asset.design_hours,
                labor_rate=pa.asset.labor_rate,
                target_uses=pa.asset.target_uses
            )
            for pa in product.product_assets
        ]

        cost_res = compute_product_cost(
            print_hours=product.print_hours,
            labor_minutes=product.labor_minutes,
            hardware_cost=product.hardware_cost,
            purchase_cost=machine.purchase_cost,
            lifetime_hours=machine.lifetime_hours,
            maintenance_factor=machine.maintenance_factor,
            materials=materials,
            assets=assets,
            target_hourly_rate=request.target_hourly_rate,
            pricing_multiplier=request.pricing_multiplier,
            waste_factor=request.waste_factor,
        )
        results[product_id] = CalculationResult(**cost_res)

    return BatchCalculationResponse(results=results)
