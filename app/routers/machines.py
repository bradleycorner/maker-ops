from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import MachineCreate, MachineRead

router = APIRouter(prefix="/machines", tags=["machines"])


@router.post("/", response_model=MachineRead, status_code=201)
def create_machine(machine: MachineCreate, db: Session = Depends(get_db)) -> MachineRead:
    """Create a new machine record."""
    db_machine = models.Machine(**machine.model_dump())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine


@router.get("/", response_model=list[MachineRead])
def list_machines(db: Session = Depends(get_db)) -> list[MachineRead]:
    """Return all machines."""
    return db.query(models.Machine).all()


@router.get("/{machine_id}", response_model=MachineRead)
def get_machine(machine_id: int, db: Session = Depends(get_db)) -> MachineRead:
    """Return a single machine by ID."""
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine
