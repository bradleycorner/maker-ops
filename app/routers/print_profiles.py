from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import PrintProfileCreate, PrintProfileRead

router = APIRouter(prefix="/print-profiles", tags=["print-profiles"])


@router.post("/", response_model=PrintProfileRead, status_code=201)
def create_print_profile(
    profile: PrintProfileCreate, db: Session = Depends(get_db)
) -> PrintProfileRead:
    """Create a new FDM slicer print profile."""
    db_profile = models.PrintProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


@router.get("/", response_model=list[PrintProfileRead])
def list_print_profiles(db: Session = Depends(get_db)) -> list[PrintProfileRead]:
    """Return all print profiles."""
    return db.query(models.PrintProfile).all()


@router.get("/{profile_id}", response_model=PrintProfileRead)
def get_print_profile(
    profile_id: int, db: Session = Depends(get_db)
) -> PrintProfileRead:
    """Return a single print profile by ID."""
    profile = db.query(models.PrintProfile).filter(models.PrintProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Print profile not found")
    return profile
