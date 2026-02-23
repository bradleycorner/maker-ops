from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import ShowCreate, ShowRead, ShowSaleCreate, ShowSaleRead

router = APIRouter(prefix="/shows", tags=["shows"])


@router.post("/", response_model=ShowRead, status_code=201)
def create_show(show: ShowCreate, db: Session = Depends(get_db)) -> ShowRead:
    """Create a new show event."""
    db_show = models.Show(**show.model_dump())
    db.add(db_show)
    db.commit()
    db.refresh(db_show)
    return db_show


@router.get("/", response_model=list[ShowRead])
def list_shows(db: Session = Depends(get_db)) -> list[ShowRead]:
    """Return all shows."""
    return db.query(models.Show).all()


@router.get("/{show_id}", response_model=ShowRead)
def get_show(show_id: int, db: Session = Depends(get_db)) -> ShowRead:
    """Return a single show by ID."""
    show = db.query(models.Show).filter(models.Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show


@router.post("/{show_id}/sales", response_model=ShowSaleRead, status_code=201)
def add_show_sale(
    show_id: int,
    sale: ShowSaleCreate,
    db: Session = Depends(get_db),
) -> ShowSaleRead:
    """Record a product sale within a show."""
    show = db.query(models.Show).filter(models.Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    product = db.query(models.Product).filter(models.Product.id == sale.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_sale = models.ShowSale(show_id=show_id, **sale.model_dump())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


@router.get("/{show_id}/sales", response_model=list[ShowSaleRead])
def list_show_sales(show_id: int, db: Session = Depends(get_db)) -> list[ShowSaleRead]:
    """Return all sales recorded for a show."""
    show = db.query(models.Show).filter(models.Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show.sales
