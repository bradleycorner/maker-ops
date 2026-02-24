from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.models import EngineeringAsset
from app.schemas import EngineeringAssetCreate, EngineeringAssetRead

router = APIRouter(prefix="/assets", tags=["Engineering Assets"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=EngineeringAssetRead)
def create_asset(asset: EngineeringAssetCreate, db: Session = Depends(get_db)):
    db_asset = EngineeringAsset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.get("/", response_model=List[EngineeringAssetRead])
def list_assets(db: Session = Depends(get_db)):
    return db.query(EngineeringAsset).all()


@router.get("/{asset_id}", response_model=EngineeringAssetRead)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    db_asset = db.query(EngineeringAsset).filter(EngineeringAsset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset
