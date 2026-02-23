# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

Maker-Ops is a **local-first manufacturing cost calculator and show analytics tool**. It is an internal decision-support system — not a SaaS product. It runs entirely on macOS with no cloud services, no authentication, and no background workers.

The system serves a hybrid manufacturing workflow combining:

- FDM 3D printing
- Resin printing
- Laser fabrication
- Manual finishing

Primary goals:

1. Determine true product manufacturing cost and suggested retail price **before manufacturing**
2. Capture real-world craft/jewelry show sales data to inform future product decisions

This system models **manufacturing reality**, not generic software abstractions.

---

## Status

The repository is currently in the **specification phase**. All source code is to be implemented following the specs in `docs/` and `BOOTSTRAP_PROMPT.md`.

No `app/` directory exists yet.

Claude MUST NOT assume missing implementation files are errors.

---

## Development Commands

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The app auto-creates the SQLite database at `/data/maker_ops.db` on startup and immediately exposes OpenAPI docs.

---

## Technology Stack

- **Python 3.11+**
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite

Nothing else.

Explicitly forbidden unless requested:

- Celery
- Redis
- Docker
- Authentication systems
- External APIs
- Cloud infrastructure

---

## Architecture

```
Client (Browser / iPad / iPhone)
    ↓
FastAPI app (app/main.py)
    ↓
Routers — orchestration only, no business logic (app/routers/)
    ↓
Services — all business logic (app/services/)
    ↓
SQLite via SQLAlchemy SessionLocal pattern (app/database.py)
```

### Architectural Rules (MANDATORY)

- Routers orchestrate only.
- ALL business logic lives in `app/services/`.
- Calculation functions remain deterministic and pure.
- Database access must NEVER occur inside calculation functions.
- No hidden state or implicit dependencies.

---

### File Layout

```
app/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── calculations.py
├── routers/
│   ├── products.py
│   ├── machines.py
│   ├── shows.py
│   └── analytics.py
└── services/
    ├── cost_engine.py
    └── amortization.py

data/
└── maker_ops.db
```

---

## Core Design Rules

1. **Routers only orchestrate** — business logic belongs in `app/services/`
2. **Calculation functions are pure**
3. **Deterministic behavior** — identical inputs produce identical outputs
4. **No global state**
5. Type hints required everywhere
6. Avoid circular imports

Calculation functions MUST include:

- `calculate_material_cost()`
- `calculate_machine_cost()`
- `calculate_labor_cost()`
- `calculate_true_cost()`
- `calculate_suggested_price()`

These functions accept explicit parameters and perform zero database access.

---

## Mandatory Pricing Formula (DO NOT MODIFY)

```
material_cost = SUM(grams_used * cost_per_gram) * waste_factor
machine_cost  = print_hours * machine_hourly_rate
labor_cost    = (labor_minutes / 60) * target_hourly_rate

true_unit_cost         = material_cost + machine_cost + labor_cost + hardware_cost
suggested_retail_price = true_unit_cost * pricing_multiplier

# Defaults
pricing_multiplier = 2.7
waste_factor       = 1.1

# Machine amortization
machine_hourly_rate =
  (purchase_cost / lifetime_hours) * (1 + maintenance_factor)
```

Claude MUST NOT alter this formula unless explicitly instructed.

---

## Database Schema (7 tables)

| Table | Purpose |
|---|---|
| `machines` | Equipment definition (FDM/Resin/Laser) |
| `materials` | Material costs |
| `products` | Product definitions |
| `product_materials` | Material usage join table |
| `shows` | Event data |
| `show_sales` | Sales results |
| `design_experiments` | Design iteration tracking |

All tables use integer primary keys and ISO timestamps.

Schema authority lives in `docs/database-schema.md`.

---

## Engineering Asset Concept (IMPORTANT CONTEXT)

This system treats reusable CAD components as **engineering assets**.

Examples:

- LED mounting brackets
- reflector cores
- tripod hubs
- wire routing modules
- fixture mounts

Engineering assets:

- originate as parametric FreeCAD templates
- represent amortized design effort
- reduce repeated CAD labor
- will eventually integrate into product costing

Claude should understand that CAD reuse is part of manufacturing economics.

Future schema expansion may include an `engineering_assets` table.

---

## FreeCAD Integration Direction (Future Context)

Future development may include:

- FreeCAD macro automation
- parametric template insertion
- spreadsheet-driven geometry
- possible FreeCAD workbench tooling

Design preference:

- parameter-driven systems
- reusable component generation
- deterministic inputs

Claude must NOT assume GUI automation or introduce CAD dependencies into backend services.

---

## Key Endpoint

```
POST /products/{id}/calculate
```

Returns:

```
{
  "true_cost": 72.10,
  "suggested_price": 194.67,
  "profit_margin": 62.9
}
```

Analytics calculations:

```
total_show_cost = booth_cost + travel_cost
revenue_per_hour = total_revenue / duration_hours
break_even_units = total_show_cost / avg_product_profit
```

---

## Pull Request Review Expectations

When reviewing pull requests, Claude must prioritize:

1. Preservation of deterministic pricing logic.
2. Architectural separation:
   - routers contain no business logic
   - services contain calculations
   - parsers remain isolated translators.
3. Compliance with PROJECT.md milestone ordering.
4. Backwards compatibility with existing API endpoints.
5. Successful execution of `tools/verify_project.py`.

Suggestions that introduce SaaS patterns, authentication,
cloud dependencies, or unnecessary infrastructure must be rejected.

## Explicit Non-Goals (Permanent Constraints)

The following must NEVER be added unless explicitly requested:

- Login systems, JWT, session management
- React/Vue or any frontend framework
- Background jobs or task queues
- Caching layers
- Ecommerce integration
- Payment processing
- Inventory management
- Cloud sync or multi-user support
- Admin dashboards
- Microservices or distributed architecture

