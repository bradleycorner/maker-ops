# Maker Ops Backend Bootstrap Prompt

You are acting as a senior backend engineer implementing a deterministic internal tool.

Your task is to generate a COMPLETE working FastAPI backend that strictly follows the provided documentation.

You MUST follow architecture exactly as defined.

---

## Project Context

This is an INTERNAL local-first manufacturing decision tool.

It is NOT a SaaS product.

Constraints:

- Runs locally on macOS
- SQLite database only
- No authentication
- No cloud services
- No background workers
- No async message queues
- No frontend framework required (API only)

Primary goal:

Determine true product manufacturing cost and suggested retail pricing.

---

## Required Documentation Sources

You MUST read and follow:

- `/docs/fdm-maker-cost-engine.md`
- `/docs/database-schema.md`
- `/docs/project-structure.md`

These documents define the system specification.

Do NOT invent additional architecture.

---

## Technology Requirements

Use ONLY:

- Python 3.11+
- FastAPI
- SQLAlchemy (ORM)
- Pydantic
- SQLite

Avoid:

- Celery
- Redis
- Docker
- Authentication systems
- External APIs

---

## Implementation Rules

### 1. Deterministic Logic

All pricing calculations MUST exist in:

```
app/services/cost_engine.py
```

Routes must NOT contain business logic.

---

### 2. Database Layer

Implement SQLAlchemy models exactly matching:

`database-schema.md`

Use:

```
SessionLocal pattern
```

Database file location:

```
/data/maker_ops.db
```

Auto-create tables on startup.

---

### 3. API Structure

Implement routers:

```
/products
/machines
/shows
/analytics
```

Each router must:

- support create
- list
- retrieve

Products router must include:

```
POST /products/{id}/calculate
```

---

### 4. Cost Calculation Engine

Create pure functions:

```
calculate_material_cost()
calculate_machine_cost()
calculate_labor_cost()
calculate_true_cost()
calculate_suggested_price()
```

Inputs must be explicit parameters.

NO database access inside calculation functions.

---

### 5. Pricing Formula (MANDATORY)

```
material_cost =
  SUM(grams_used * cost_per_gram) * waste_factor

machine_cost =
  print_hours * machine_hourly_rate

labor_cost =
  (labor_minutes / 60) * target_hourly_rate

true_unit_cost =
  material_cost + machine_cost + labor_cost + hardware_cost

suggested_retail_price =
  true_unit_cost * pricing_multiplier
```

Defaults:

```
pricing_multiplier = 2.7
waste_factor = 1.1
```

---

### 6. Code Quality Requirements

- Type hints everywhere
- Clear docstrings
- No global state
- Small functions
- Predictable imports
- No circular dependencies

---

### 7. Startup Behavior

Running:

```
uvicorn app.main:app --reload
```

must:

- create database automatically
- expose OpenAPI docs
- allow immediate product cost calculation

---

### 8. Deliverables

Generate:

- working FastAPI application
- SQLAlchemy models
- routers
- services
- calculation engine
- requirements.txt

Application must run without manual edits.

---

### 9. Explicit Non-Goals

Do NOT add:

- login systems
- JWT
- admin dashboards
- React/Vue frontend
- caching layers
- background jobs

This is an engineering calculator, not a web product.

---

## Execution Plan

1. Create folder structure exactly as documented.
2. Implement database layer.
3. Implement schemas.
4. Implement services.
5. Implement routers.
6. Wire application startup.
7. Provide run instructions.

Work sequentially and keep implementation minimal and correct.
