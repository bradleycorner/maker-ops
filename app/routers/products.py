from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.calculations import MaterialUsage
from app.database import get_db
from app.schemas import (
    CalculationRequest,
    CalculationResult,
    DesignExperimentCreate,
    DesignExperimentRead,
    ProductCreate,
    ProductRead,
)
from app.services.cost_engine import compute_product_cost

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductRead, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    """Create a product and attach its material usage records."""
    machine = db.query(models.Machine).filter(models.Machine.id == product.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    product_data = product.model_dump(exclude={"materials"})
    db_product = models.Product(**product_data)
    db.add(db_product)
    db.flush()  # populate db_product.id before creating children

    for mat in product.materials:
        material = db.query(models.Material).filter(models.Material.id == mat.material_id).first()
        if not material:
            raise HTTPException(status_code=404, detail=f"Material {mat.material_id} not found")
        db.add(
            models.ProductMaterial(
                product_id=db_product.id,
                material_id=mat.material_id,
                grams_used=mat.grams_used,
            )
        )

    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)) -> list[ProductRead]:
    """Return all products."""
    return db.query(models.Product).all()


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    """Return a single product by ID."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/{product_id}/calculate", response_model=CalculationResult)
def calculate_product_cost(
    product_id: int,
    request: Annotated[CalculationRequest, Body()] = CalculationRequest(),
    db: Session = Depends(get_db),
) -> CalculationResult:
    """Calculate true cost and suggested retail price for a product.

    The request body is optional — all fields default to the spec values:
      target_hourly_rate=25.0, pricing_multiplier=2.7, waste_factor=1.1
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    machine = product.machine
    if not machine:
        raise HTTPException(status_code=400, detail="Product has no associated machine")

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
        target_hourly_rate=request.target_hourly_rate,
        pricing_multiplier=request.pricing_multiplier,
        waste_factor=request.waste_factor,
    )
    return result


# ---------------------------------------------------------------------------
# Design experiments (nested under products)
# ---------------------------------------------------------------------------

@router.post("/{product_id}/experiments", response_model=DesignExperimentRead, status_code=201)
def create_experiment(
    product_id: int,
    experiment: DesignExperimentCreate,
    db: Session = Depends(get_db),
) -> DesignExperimentRead:
    """Record a design experiment for a product."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = experiment.model_dump()
    data["product_id"] = product_id
    db_exp = models.DesignExperiment(**data)
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)
    return db_exp


@router.get("/{product_id}/experiments", response_model=list[DesignExperimentRead])
def list_experiments(
    product_id: int,
    db: Session = Depends(get_db),
) -> list[DesignExperimentRead]:
    """Return all design experiments for a product."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.design_experiments
