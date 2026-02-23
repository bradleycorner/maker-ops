# Project Structure
## Maker Ops Cost Engine (FastAPI)

---

## Repository Layout

```
maker-ops/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── calculations.py
│   ├── routers/
│   │   ├── products.py
│   │   ├── machines.py
│   │   ├── shows.py
│   │   └── analytics.py
│   │
│   └── services/
│       ├── cost_engine.py
│       └── amortization.py
│
├── docs/
│   ├── fdm-maker-cost-engine.md
│   ├── database-schema.md
│   └── project-structure.md
│
├── data/
│   └── maker_ops.db
│
├── requirements.txt
├── README.md
└── run.sh
```

---

## Core Components

### main.py
Initializes FastAPI app and routers.

### database.py
SQLite connection and session management.

### models.py
SQLAlchemy ORM models.

### schemas.py
Pydantic request/response schemas.

### calculations.py
Pure math functions (NO database logic).

---

## Cost Engine Service

Responsible for:

- material aggregation
- machine hourly cost lookup
- labor valuation
- final pricing calculation

---

## Example Endpoint

```
POST /products/calculate
```

Input:

```json
{
  "product_id": 1
}
```

Output:

```json
{
  "true_cost": 72.10,
  "suggested_price": 194.67,
  "profit_margin": 62.9
}
```

---

## Development Startup

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## Design Rules

- Business logic lives in `/services`
- Routes only orchestrate
- Calculations remain deterministic and testable
- Database optional for unit testing
