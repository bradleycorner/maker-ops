from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import models
from app.calculations import (
    AssetUsage,
    MaterialUsage,
    calculate_mass_from_volume,
    calculate_print_time_from_flow,
)
from app.database import get_db
from app.parsers.registry import parse_gcode
from app.schemas import (
    CalculationRequest,
    CalculationResult,
    DesignExperimentCreate,
    DesignExperimentRead,
    GeometryEstimationRequest,
    GeometryEstimationResponse,
    NormalizationBreakdown,
    PrintProfileCreate,
    ProductAssetRead,
    ProductComparisonRequest,
    ProductComparisonResponse,
    ComparisonDetail,
    ComparisonDelta,
    ProductCreate,
    ProductRead,
)
from app.services.cost_engine import compute_product_cost
from app.services.print_normalizer import ProfileParams, normalize_from_geometry

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
    save_profile: bool = Form(False),
    profile_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> CalculationResult:
    """Calculate profitability directly from a G-code file upload.

    Parses the file header to extract print time and filament usage, then
    calls the cost engine to produce a pricing result.

    Optionally saves the extracted slicer settings as a reusable print profile
    by passing save_profile=true and profile_name=<name>.
    """
    # 1. Read the full file. Creality Print V7 writes filament summary at the
    # end of the file rather than the header, so we cannot limit to first N bytes.
    content = await file.read()
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

    # 5. Optionally save extracted slicer settings as a reusable print profile.
    # Requires save_profile=True, a non-empty profile_name, and at minimum
    # layer_height and nozzle_diameter (both are required schema fields with no
    # meaningful fallback). Failure to save does not affect the cost result.
    if save_profile and profile_name and estimate.layer_height and estimate.nozzle_diameter:
        profile_data = PrintProfileCreate(
            name=profile_name,
            nozzle_diameter_mm=estimate.nozzle_diameter,
            layer_height_mm=estimate.layer_height,
            wall_count=estimate.wall_count if estimate.wall_count is not None else 3,
            infill_percentage=estimate.infill_percentage if estimate.infill_percentage is not None else 20.0,
            speed_wall_mm_s=estimate.speed_wall_outer_mm_s if estimate.speed_wall_outer_mm_s is not None else 200.0,
            speed_infill_mm_s=estimate.speed_infill_mm_s if estimate.speed_infill_mm_s is not None else 250.0,
        )
        db_profile = models.PrintProfile(**profile_data.model_dump())
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        result["saved_profile_id"] = db_profile.id

    return result


@router.post("/estimate-from-geometry", response_model=GeometryEstimationResponse)
def estimate_from_geometry(
    request: GeometryEstimationRequest,
    db: Session = Depends(get_db),
) -> GeometryEstimationResponse:
    """Estimate costs directly from CAD geometry (volume, dimensions).

    When ``print_profile_id`` and ``dimensions_mm`` are both provided the
    Physics-grounded Print Process Normalization layer (M7) is used.
    Otherwise the M6 single-formula approximation is used unchanged.
    """
    # 1. Get machine and material
    machine = db.query(models.Machine).filter(models.Machine.id == request.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    material = db.query(models.Material).filter(models.Material.id == request.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    density = material.density_g_cm3 or 1.25

    # 2. Estimate mass and time — normalizer path or M6 fallback
    normalization: NormalizationBreakdown | None = None

    if request.print_profile_id is not None and request.dimensions_mm:
        db_profile = (
            db.query(models.PrintProfile)
            .filter(models.PrintProfile.id == request.print_profile_id)
            .first()
        )
        if not db_profile:
            raise HTTPException(status_code=404, detail="Print profile not found")

        profile_params = ProfileParams(
            nozzle_diameter_mm=db_profile.nozzle_diameter_mm,
            layer_height_mm=db_profile.layer_height_mm,
            wall_count=db_profile.wall_count,
            infill_percentage=db_profile.infill_percentage,
            top_layers=db_profile.top_layers,
            bottom_layers=db_profile.bottom_layers,
            extrusion_width_factor=db_profile.extrusion_width_factor,
            volumetric_flow_rate_mm3s=db_profile.volumetric_flow_rate_mm3s,
            purge_mass_per_change_g=db_profile.purge_mass_per_change_g,
        )

        norm_result = normalize_from_geometry(
            volume_mm3=request.volume_mm3,
            dimensions_mm=request.dimensions_mm,
            density_g_cm3=density,
            profile=profile_params,
            color_changes=request.color_changes,
        )

        mass_g = norm_result.estimated_mass_grams
        hours = norm_result.estimated_print_hours
        normalization = NormalizationBreakdown(
            perimeter_g=norm_result.perimeter_g,
            infill_g=norm_result.infill_g,
            top_bottom_g=norm_result.top_bottom_g,
            purge_g=norm_result.purge_g,
            confidence_level=norm_result.confidence_level,
        )
    else:
        # M6 fallback — unchanged
        flow_rate = request.volumetric_flow_rate or machine.default_volumetric_flow_rate or 10.0
        mass_g = calculate_mass_from_volume(
            volume_mm3=request.volume_mm3,
            material_density_g_cm3=density,
            infill_percentage=request.infill_percentage,
        )
        hours = calculate_print_time_from_flow(
            volume_mm3=request.volume_mm3,
            volumetric_flow_rate_mm3_s=flow_rate,
            infill_percentage=request.infill_percentage,
        )

    # 3. Compute cost
    materials = [MaterialUsage(grams_used=mass_g, cost_per_gram=material.cost_per_gram)]

    res = compute_product_cost(
        print_hours=hours,
        labor_minutes=request.labor_minutes,
        hardware_cost=request.hardware_cost,
        purchase_cost=machine.purchase_cost,
        lifetime_hours=machine.lifetime_hours,
        maintenance_factor=machine.maintenance_factor,
        materials=materials,
        assets=[],
        target_hourly_rate=request.target_hourly_rate,
        pricing_multiplier=request.pricing_multiplier,
        waste_factor=request.waste_factor,
    )

    flow_rate_meta = request.volumetric_flow_rate or machine.default_volumetric_flow_rate or 10.0
    metadata = {
        "volume_mm3": request.volume_mm3,
        "infill_percentage": request.infill_percentage,
        "volumetric_flow_rate": flow_rate_meta,
        "estimated_density": density,
        "dimensions_mm": request.dimensions_mm or {},
    }

    if request.save:
        db_product = models.Product(
            name=request.name,
            print_hours=hours,
            labor_minutes=request.labor_minutes,
            hardware_cost=request.hardware_cost,
            machine_id=request.machine_id,
            geometry_metadata=metadata,
        )
        db.add(db_product)
        db.flush()
        db.add(
            models.ProductMaterial(
                product_id=db_product.id,
                material_id=request.material_id,
                grams_used=mass_g,
            )
        )
        db.commit()

    return GeometryEstimationResponse(
        calculation=CalculationResult(**res),
        estimated_mass_g=round(mass_g, 2),
        estimated_print_hours=round(hours, 4),
        geometry_metadata=metadata,
        normalization=normalization,
        print_profile_id=request.print_profile_id,
    )


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
