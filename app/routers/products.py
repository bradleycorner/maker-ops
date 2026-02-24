from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import models
from app.calculations import AssetUsage, MaterialUsage
from app.database import get_db
from app.parsers.registry import parse_gcode
from app.schemas import (
    CalculationRequest,
    CalculationResult,
    DesignExperimentCreate,
    DesignExperimentRead,
    ProductAssetRead,
    ProductComparisonRequest,
    ProductComparisonResponse,
    ComparisonDetail,
    ComparisonDelta,
    ProductCreate,
    ProductRead,
)
from app.services.cost_engine import compute_product_cost

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/calculate/from-gcode", response_model=CalculationResult)
async def calculate_from_gcode(
    file: UploadFile = File(...),
    machine_id: int = Form(...),
    labor_minutes: int = Form(...),
    hardware_cost: float = Form(0.0),
    material_cost_per_gram: float = Form(...),
    target_hourly_rate: float = Form(25.0),
    pricing_multiplier: float = Form(2.7),
    waste_factor: float = Form(1.1),
    db: Session = Depends(get_db),
) -> CalculationResult:
    """Calculate profitability directly from a G-code file upload.

    Parses the file header to extract print time and filament usage, then
    calls the cost engine to produce a pricing result.
    """
    # 1. Read the beginning of the file (usually headers are in first 100KB)
    content = await file.read(102400)
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    # 2. Parse G-code
    try:
        estimate = parse_gcode(text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Get machine details
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    # 4. Compute cost
    materials = [
        MaterialUsage(
            grams_used=estimate.filament_grams,
            cost_per_gram=material_cost_per_gram
        )
    ]

    result = compute_product_cost(
        print_hours=estimate.print_time_seconds / 3600.0,
        labor_minutes=labor_minutes,
        hardware_cost=hardware_cost,
        purchase_cost=machine.purchase_cost,
        lifetime_hours=machine.lifetime_hours,
        maintenance_factor=machine.maintenance_factor,
        materials=materials,
        assets=[],
        target_hourly_rate=target_hourly_rate,
        pricing_multiplier=pricing_multiplier,
        waste_factor=waste_factor,
    )

    return result


@router.post("/", response_model=ProductRead, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    """Create a product and attach its material usage records."""
    machine = db.query(models.Machine).filter(models.Machine.id == product.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    product_data = product.model_dump(exclude={"materials", "asset_ids"})
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

    for asset_id in product.asset_ids:
        asset = db.query(models.EngineeringAsset).filter(models.EngineeringAsset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Engineering Asset {asset_id} not found")
        db.add(
            models.ProductAsset(
                product_id=db_product.id,
                asset_id=asset_id,
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

    assets = [
        AssetUsage(
            design_hours=pa.asset.design_hours,
            labor_rate=pa.asset.labor_rate,
            target_uses=pa.asset.target_uses
        )
        for pa in product.product_assets
    ]

    result = compute_product_cost(
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
    return result


@router.post("/{product_id}/assets", response_model=ProductAssetRead)
def attach_asset(product_id: int, asset_id: int, db: Session = Depends(get_db)):
    """Attach an engineering asset to a product."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    asset = db.query(models.EngineeringAsset).filter(models.EngineeringAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Check if already attached
    existing = db.query(models.ProductAsset).filter(
        models.ProductAsset.product_id == product_id,
        models.ProductAsset.asset_id == asset_id
    ).first()
    if existing:
        return existing

    db_product_asset = models.ProductAsset(product_id=product_id, asset_id=asset_id)
    db.add(db_product_asset)
    db.commit()
    db.refresh(db_product_asset)
    return db_product_asset


@router.get("/{product_id}/assets", response_model=list[ProductAssetRead])
def list_product_assets(product_id: int, db: Session = Depends(get_db)):
    """List assets attached to a product."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.product_assets


@router.post("/compare", response_model=ProductComparisonResponse)
def compare_products(
    request: ProductComparisonRequest,
    db: Session = Depends(get_db),
) -> ProductComparisonResponse:
    """Compare two products side-by-side."""
    def get_calc(product_id: int):
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        machine = product.machine
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
        
        res = compute_product_cost(
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
        return product.name, res

    name_a, res_a = get_calc(request.product_a_id)
    name_b, res_b = get_calc(request.product_b_id)

    detail_a = ComparisonDetail(
        name=name_a,
        true_cost=res_a["true_cost"],
        suggested_price=res_a["suggested_price"],
        profit_per_print_hour=res_a["profit_per_print_hour"]
    )
    detail_b = ComparisonDetail(
        name=name_b,
        true_cost=res_b["true_cost"],
        suggested_price=res_b["suggested_price"],
        profit_per_print_hour=res_b["profit_per_print_hour"]
    )

    better = "product_a" if res_a["profit_per_print_hour"] >= res_b["profit_per_print_hour"] else "product_b"

    delta = ComparisonDelta(
        true_cost=round(res_b["true_cost"] - res_a["true_cost"], 2),
        profit_per_print_hour=round(res_b["profit_per_print_hour"] - res_a["profit_per_print_hour"], 2),
        better_variant=better
    )

    return ProductComparisonResponse(
        product_a=detail_a,
        product_b=detail_b,
        delta=delta
    )


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
