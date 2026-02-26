from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Print Profile
# ---------------------------------------------------------------------------

class PrintProfileCreate(BaseModel):
    name: str
    nozzle_diameter_mm: float
    filament_diameter_mm: float = 1.75
    layer_height_mm: float
    wall_count: int = 3
    infill_percentage: float = 20.0
    top_layers: int = 4
    bottom_layers: int = 4
    extrusion_width_factor: float = 1.2
    volumetric_flow_rate_mm3s: float = 10.0
    purge_mass_per_change_g: float = 3.0


class PrintProfileRead(PrintProfileCreate):
    id: int
    created_at: str

    model_config = {"from_attributes": True}


class NormalizationBreakdown(BaseModel):
    perimeter_g: float
    infill_g: float
    top_bottom_g: float
    purge_g: float
    confidence_level: str  # "medium" (bounding box) | "low" (volume only)


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------

class MachineCreate(BaseModel):
    name: str
    machine_type: str
    purchase_cost: float
    lifetime_hours: float
    maintenance_factor: float
    default_volumetric_flow_rate: Optional[float] = None


class MachineRead(MachineCreate):
    id: int
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------

class MaterialCreate(BaseModel):
    name: str
    cost_per_gram: float
    density_g_cm3: float = 1.25
    supplier: Optional[str] = None


class MaterialRead(MaterialCreate):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# ProductMaterial
# ---------------------------------------------------------------------------

class ProductMaterialCreate(BaseModel):
    material_id: int
    grams_used: float


class ProductMaterialRead(BaseModel):
    id: int
    product_id: int
    material_id: int
    grams_used: float
    material: MaterialRead

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# EngineeringAsset
# ---------------------------------------------------------------------------

class EngineeringAssetCreate(BaseModel):
    name: str
    design_hours: float
    labor_rate: float
    target_uses: int


class EngineeringAssetRead(EngineeringAssetCreate):
    id: int
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# ProductAsset
# ---------------------------------------------------------------------------

class ProductAssetCreate(BaseModel):
    asset_id: int


class ProductAssetRead(BaseModel):
    id: int
    product_id: int
    asset_id: int
    asset: EngineeringAssetRead

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductCreate(BaseModel):
    name: str
    version: Optional[str] = None
    print_hours: float
    labor_minutes: int
    hardware_cost: float = 0.0
    machine_id: int
    materials: list[ProductMaterialCreate] = []
    asset_ids: list[int] = []
    geometry_metadata: Optional[dict] = None


class ProductRead(BaseModel):
    id: int
    name: str
    version: Optional[str]
    print_hours: float
    labor_minutes: int
    hardware_cost: float
    machine_id: int
    created_at: str
    product_materials: list[ProductMaterialRead] = []
    product_assets: list[ProductAssetRead] = []
    geometry_metadata: Optional[dict] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Show
# ---------------------------------------------------------------------------

class ShowCreate(BaseModel):
    name: str
    booth_cost: float
    travel_cost: float
    duration_hours: float
    date: str


class ShowRead(ShowCreate):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# ShowSale
# ---------------------------------------------------------------------------

class ShowSaleCreate(BaseModel):
    product_id: int
    quantity_sold: int
    sale_price: float


class ShowSaleRead(ShowSaleCreate):
    id: int
    show_id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# DesignExperiment
# ---------------------------------------------------------------------------

class DesignExperimentCreate(BaseModel):
    product_id: int
    reflector_type: Optional[str] = None
    material_combo: Optional[str] = None
    light_temperature: Optional[int] = None
    perceived_interest: Optional[int] = None
    notes: Optional[str] = None


class DesignExperimentRead(DesignExperimentCreate):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Cost Calculation
# ---------------------------------------------------------------------------

class CalculationRequest(BaseModel):
    """Optional overrides for calculation constants.  All fields default to
    the values defined in the pricing specification."""

    target_hourly_rate: float = 25.0
    pricing_multiplier: float = 2.7
    waste_factor: float = 1.1


class CalculationResult(BaseModel):
    true_cost: float
    suggested_price: float
    profit_margin: float
    profit_per_print_hour: float
    material_cost: float
    machine_cost: float
    labor_cost: float
    asset_cost: float
    machine_hourly_rate: float


# ---------------------------------------------------------------------------
# Design Comparison
# ---------------------------------------------------------------------------

class ProductComparisonRequest(CalculationRequest):
    product_a_id: int
    product_b_id: int


class ComparisonDetail(BaseModel):
    name: str
    true_cost: float
    suggested_price: float
    profit_per_print_hour: float


class ComparisonDelta(BaseModel):
    true_cost: float
    profit_per_print_hour: float
    better_variant: str  # "product_a" or "product_b"


class ProductComparisonResponse(BaseModel):
    product_a: ComparisonDetail
    product_b: ComparisonDetail
    delta: ComparisonDelta


# ---------------------------------------------------------------------------
# Automation / Batch
# ---------------------------------------------------------------------------

class BatchCalculationRequest(CalculationRequest):
    product_ids: list[int]


class BatchCalculationResponse(BaseModel):
    results: dict[int, CalculationResult]


# ---------------------------------------------------------------------------
# CAD / Geometry
# ---------------------------------------------------------------------------

class GeometryEstimationRequest(CalculationRequest):
    name: str
    volume_mm3: float
    material_id: int
    machine_id: int
    infill_percentage: float = 20.0
    volumetric_flow_rate: Optional[float] = None  # mm3/s
    labor_minutes: int = 0
    hardware_cost: float = 0.0
    dimensions_mm: Optional[dict[str, float]] = None
    save: bool = False
    print_profile_id: Optional[int] = None
    color_changes: int = 0


class GeometryEstimationResponse(BaseModel):
    calculation: CalculationResult
    estimated_mass_g: float
    estimated_print_hours: float
    geometry_metadata: dict
    normalization: Optional[NormalizationBreakdown] = None
    print_profile_id: Optional[int] = None


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class ShowAnalytics(BaseModel):
    show_id: int
    show_name: str
    total_show_cost: float
    total_revenue: float
    profit: float
    revenue_per_hour: float
    break_even_units: float
    units_sold: int
