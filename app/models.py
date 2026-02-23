from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Integer, Float, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Machine(Base):
    """Manufacturing equipment used during production."""

    __tablename__ = "machines"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    machine_type = Column(String, nullable=False)  # FDM / Resin / Laser
    purchase_cost = Column(Float, nullable=False)
    lifetime_hours = Column(Float, nullable=False)
    maintenance_factor = Column(Float, nullable=False)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

    products = relationship("Product", back_populates="machine")


class Material(Base):
    """Raw material with a known cost per gram."""

    __tablename__ = "materials"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    cost_per_gram = Column(Float, nullable=False)
    supplier = Column(String)

    product_materials = relationship("ProductMaterial", back_populates="material")


class Product(Base):
    """A manufactured product definition."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String)
    print_hours = Column(Float, nullable=False)
    labor_minutes = Column(Integer, nullable=False)
    hardware_cost = Column(Float, nullable=False, default=0.0)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=False)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())

    machine = relationship("Machine", back_populates="products")
    product_materials = relationship("ProductMaterial", back_populates="product")
    show_sales = relationship("ShowSale", back_populates="product")
    design_experiments = relationship("DesignExperiment", back_populates="product")


class ProductMaterial(Base):
    """Join table recording how many grams of each material a product uses."""

    __tablename__ = "product_materials"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    grams_used = Column(Float, nullable=False)

    product = relationship("Product", back_populates="product_materials")
    material = relationship("Material", back_populates="product_materials")


class Show(Base):
    """A craft or jewelry show event."""

    __tablename__ = "shows"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    booth_cost = Column(Float, nullable=False)
    travel_cost = Column(Float, nullable=False)
    duration_hours = Column(Float, nullable=False)
    date = Column(String, nullable=False)

    sales = relationship("ShowSale", back_populates="show")


class ShowSale(Base):
    """A product sold at a specific show."""

    __tablename__ = "show_sales"

    id = Column(Integer, primary_key=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    sale_price = Column(Float, nullable=False)

    show = relationship("Show", back_populates="sales")
    product = relationship("Product", back_populates="show_sales")


class DesignExperiment(Base):
    """Design iteration data correlated with observed sales interest."""

    __tablename__ = "design_experiments"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    reflector_type = Column(String)
    material_combo = Column(String)
    light_temperature = Column(Integer)
    perceived_interest = Column(Integer)
    notes = Column(Text)

    product = relationship("Product", back_populates="design_experiments")
