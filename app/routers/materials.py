from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import MaterialCreate, MaterialRead

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("/", response_model=MaterialRead, status_code=201)
def create_material(material: MaterialCreate, db: Session = Depends(get_db)) -> MaterialRead:
    """Create a new material record."""
    db_material = models.Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material


@router.get("/", response_model=list[MaterialRead])
def list_materials(db: Session = Depends(get_db)) -> list[MaterialRead]:
    """Return all materials."""
    return db.query(models.Material).all()


@router.get("/{material_id}", response_model=MaterialRead)
def get_material(material_id: int, db: Session = Depends(get_db)) -> MaterialRead:
    """Return a single material by ID."""
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material
