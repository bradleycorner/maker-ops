from fastapi import FastAPI

from app.database import BASE_DIR, engine
from app.routers import analytics, assets, machines, materials, products, shows

# Auto-create tables on startup (data/ directory is created in database.py)
from app import models  # noqa: F401 — side-effect: registers all ORM models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Maker Ops",
    description=(
        "Local-first manufacturing cost calculator and show analytics tool. "
        "Determines true product cost and suggested retail price before manufacturing."
    ),
    version="1.0.0",
)

app.include_router(machines.router)
app.include_router(materials.router)
app.include_router(products.router)
app.include_router(assets.router)
app.include_router(shows.router)
app.include_router(analytics.router)


@app.get("/", tags=["health"])
def health_check() -> dict:
    """Confirm the API is running."""
    return {"status": "ok", "app": "maker-ops", "db": str(BASE_DIR / "data" / "maker_ops.db")}
