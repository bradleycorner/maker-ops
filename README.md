# Maker-Ops

Local-first manufacturing cost calculator and show analytics tool for a hybrid FDM / resin / laser fabrication workflow.

Determines true product cost and suggested retail price **before manufacturing**, and captures real-world craft/jewelry show sales data to inform future product decisions.

---

## Overview

Maker-Ops is an internal decision-support system. It runs entirely on macOS with no cloud services, no authentication, and no background workers. The entire system is a single FastAPI process backed by a local SQLite database.

**Primary goals**

1. Calculate true unit cost and suggested retail price from materials, machine time, and labor — before a single part is printed.
2. Record show sales and compute per-event profitability metrics.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| API framework | FastAPI |
| ORM | SQLAlchemy |
| Validation | Pydantic v2 |
| Database | SQLite (`data/maker_ops.db`) |

No Docker, no Redis, no Celery, no authentication, no frontend framework.

---

## Pricing Formula

```
material_cost          = SUM(grams_used × cost_per_gram) × waste_factor
machine_hourly_rate    = (purchase_cost / lifetime_hours) × (1 + maintenance_factor)
machine_cost           = print_hours × machine_hourly_rate
labor_cost             = (labor_minutes / 60) × target_hourly_rate

true_unit_cost         = material_cost + machine_cost + labor_cost + hardware_cost
suggested_retail_price = true_unit_cost × pricing_multiplier
```

**Defaults:** `waste_factor = 1.1` · `pricing_multiplier = 2.7` · `target_hourly_rate = $25.00/hr`

### Example

| Input | Value |
|---|---|
| Machine | $800 FDM printer, 800 hr lifetime, 15% maintenance |
| Material | 40 g PLA @ $0.025/g |
| Print time | 2.5 hours |
| Labor | 30 minutes |
| Hardware | $3.00 |

| Output | Value |
|---|---|
| `machine_hourly_rate` | $1.15 / hr |
| `material_cost` | $1.10 |
| `machine_cost` | $2.88 |
| `labor_cost` | $12.50 |
| **`true_cost`** | **$19.48** |
| **`suggested_price`** | **$52.58** |
| **`profit_margin`** | **62.96 %** |

---

## Project Structure

```
maker-ops/
├── app/
│   ├── main.py               # FastAPI app entry point, router wiring, table creation
│   ├── database.py           # SQLite engine, SessionLocal, get_db() dependency
│   ├── models.py             # SQLAlchemy ORM models (7 tables)
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── calculations.py       # Pure deterministic math functions (zero DB access)
│   ├── routers/
│   │   ├── machines.py       # /machines endpoints
│   │   ├── materials.py      # /materials endpoints
│   │   ├── products.py       # /products endpoints + /calculate + experiments
│   │   ├── shows.py          # /shows endpoints + /sales
│   │   └── analytics.py      # /analytics endpoints
│   └── services/
│       ├── amortization.py   # calculate_machine_hourly_rate()
│       └── cost_engine.py    # compute_product_cost() orchestrator
├── docs/
│   ├── fdm-maker-cost-engine.md
│   ├── database-schema.md
│   └── project-structure.md
├── data/
│   └── maker_ops.db          # auto-created on first startup
├── BOOTSTRAP_PROMPT.md
├── CLAUDE.md
├── requirements.txt
└── run.sh
```

### Architecture

```
Client (Browser / iPad / iPhone)
    ↓
FastAPI  app/main.py
    ↓
Routers  — orchestration only, no business logic
    ↓
Services — all business logic
    ↓
SQLite   via SQLAlchemy SessionLocal
```

---

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Or use the bootstrap script (creates the venv, installs deps, and starts the server):

```bash
./run.sh
```

---

## Running

```bash
uvicorn app.main:app --reload
```

On first startup the app automatically creates `data/maker_ops.db` and all tables.

| URL | Description |
|---|---|
| `http://localhost:8000/docs` | Interactive OpenAPI UI |
| `http://localhost:8000/redoc` | ReDoc API reference |
| `http://localhost:8000/openapi.json` | Raw OpenAPI schema |

---

## API Reference

### Machines

| Method | Path | Description |
|---|---|---|
| `POST` | `/machines/` | Create a machine |
| `GET` | `/machines/` | List all machines |
| `GET` | `/machines/{id}` | Get a machine |

**Create machine**
```json
POST /machines/
{
  "name": "Bambu X1C",
  "machine_type": "FDM",
  "purchase_cost": 800.0,
  "lifetime_hours": 800.0,
  "maintenance_factor": 0.15
}
```
`machine_type` accepts `FDM`, `Resin`, or `Laser`.

---

### Materials

| Method | Path | Description |
|---|---|---|
| `POST` | `/materials/` | Create a material |
| `GET` | `/materials/` | List all materials |
| `GET` | `/materials/{id}` | Get a material |

**Create material**
```json
POST /materials/
{
  "name": "Silk PLA Copper",
  "cost_per_gram": 0.025,
  "supplier": "Polymaker"
}
```

---

### Products

| Method | Path | Description |
|---|---|---|
| `POST` | `/products/` | Create a product |
| `GET` | `/products/` | List all products |
| `GET` | `/products/{id}` | Get a product |
| `POST` | `/products/{id}/calculate` | Calculate cost and price |
| `POST` | `/products/{id}/experiments` | Log a design experiment |
| `GET` | `/products/{id}/experiments` | List design experiments |

**Create product**
```json
POST /products/
{
  "name": "Faceted Lamp Shade",
  "version": "2.0",
  "print_hours": 2.5,
  "labor_minutes": 30,
  "hardware_cost": 3.0,
  "machine_id": 1,
  "materials": [
    { "material_id": 1, "grams_used": 40.0 }
  ]
}
```

**Calculate cost** — all fields optional, defaults apply
```json
POST /products/1/calculate
{
  "target_hourly_rate": 25.0,
  "pricing_multiplier": 2.7,
  "waste_factor": 1.1
}
```

Response:
```json
{
  "true_cost": 19.48,
  "suggested_price": 52.58,
  "profit_margin": 62.96,
  "material_cost": 1.10,
  "machine_cost": 2.875,
  "labor_cost": 12.50,
  "machine_hourly_rate": 1.15
}
```

---

### Shows

| Method | Path | Description |
|---|---|---|
| `POST` | `/shows/` | Create a show |
| `GET` | `/shows/` | List all shows |
| `GET` | `/shows/{id}` | Get a show |
| `POST` | `/shows/{id}/sales` | Record a sale |
| `GET` | `/shows/{id}/sales` | List sales for a show |

**Create show**
```json
POST /shows/
{
  "name": "Springfield Craft Fair",
  "booth_cost": 150.0,
  "travel_cost": 80.0,
  "duration_hours": 8.0,
  "date": "2026-03-15"
}
```

**Record a sale**
```json
POST /shows/1/sales
{
  "product_id": 1,
  "quantity_sold": 3,
  "sale_price": 55.0
}
```

---

### Analytics

| Method | Path | Description |
|---|---|---|
| `GET` | `/analytics/shows/{id}` | Show performance metrics |

**Show analytics**
```json
GET /analytics/shows/1

{
  "show_id": 1,
  "show_name": "Springfield Craft Fair",
  "total_show_cost": 230.0,
  "total_revenue": 165.0,
  "profit": -65.0,
  "revenue_per_hour": 20.62,
  "break_even_units": 6.48,
  "units_sold": 3
}
```

Calculations:
```
total_show_cost  = booth_cost + travel_cost
total_revenue    = SUM(quantity_sold × sale_price)
profit           = total_revenue − total_show_cost
revenue_per_hour = total_revenue / duration_hours
break_even_units = total_show_cost / avg_product_profit
```

---

## Database Schema

| Table | Purpose |
|---|---|
| `machines` | Equipment definition (FDM / Resin / Laser) |
| `materials` | Material costs per gram |
| `products` | Product definitions |
| `product_materials` | Material usage per product (join table) |
| `shows` | Craft/jewelry show events |
| `show_sales` | Per-product sales recorded at a show |
| `design_experiments` | Design iteration tracking correlated to sales interest |

All tables use integer primary keys and ISO 8601 timestamps.

---

## Workflow

### Pre-manufacture pricing

```
Create Machine → Create Materials → Create Product → POST /calculate → Decision: build or iterate
```

### Show feedback loop

```
Attend Show → POST /shows/ → POST /shows/{id}/sales → GET /analytics/shows/{id} → Inform next design
```

---

## Documentation

| Document | Description |
|---|---|
| [Test Status](docs/TEST_STATUS.md) | Milestone verification record and verified capability baseline |
| [FDM Cost Engine](docs/fdm-maker-cost-engine.md) | Functional design model and pricing formula specification |
| [Database Schema](docs/database-schema.md) | Full schema definition for all 7 tables |
| [Project Structure](docs/project-structure.md) | Repository layout and component responsibilities |

---

## Non-Goals

The following are permanent constraints and will not be added:

- Login / JWT / session management
- React, Vue, or any frontend framework
- Background jobs or task queues
- Caching layers
- Ecommerce or payment processing
- Inventory management
- Cloud sync or multi-user support
- Microservices or distributed architecture
