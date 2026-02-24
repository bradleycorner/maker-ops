from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------

class MachineCreate(BaseModel):
    name: str
    machine_type: str
    purchase_cost: float
    lifetime_hours: float
    maintenance_factor: float


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
    material_cost: float
    machine_cost: float
    labor_cost: float
    asset_cost: float
    machine_hourly_rate: float


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
