# GEMINI.md

This file provides guidance to Gemini CLI when working with code in this repository.

---

## Project Overview

Maker-Ops is a **local-first manufacturing cost calculator and show analytics tool**. It is an internal decision-support system — not a SaaS product. It runs entirely on macOS with no cloud services, no authentication, and no background workers.

Primary goals:
1. Determine true product manufacturing cost and suggested retail price **before manufacturing**.
2. Capture real-world craft/jewelry show sales data to inform future product decisions.

---

## Status

- **Milestone 1 (Core Cost Engine):** COMPLETE.
- **Milestone 2 (Open Slicer Ingestion):** COMPLETE.
  - Parsers for Creality and Generic G-code implemented.
  - `POST /products/calculate/from-gcode` endpoint verified.
  - `python-multipart` added to dependencies.
- **Milestone 3 (Engineering Asset System):** COMPLETE.
  - `EngineeringAsset` and `ProductAsset` models/schemas added.
  - Cost engine updated to include amortized design labor.
  - Verification script updated and passing.
- **Milestone 4 (Design Comparison Engine):** COMPLETE.
  - `POST /products/compare` implemented for side-by-side analysis.
  - "Profit per Print Hour" metric added to cost engine.
  - Verification script updated and passing.
- **Milestone 5 (Automation Interfaces):** COMPLETE.
  - `maker-ops-cli.py` implemented for headless interaction.
  - `POST /automation/batch-calculate` added for batch processing.
  - Sample FreeCAD macro provided in `docs/macros/`.
  - Verification script updated and passing.
- **Milestone 6 (CAD Integration Foundations):** IN PROGRESS.
  - Specification drafted in `docs/milestone-6-cad-integration.md`.
  - Goal: Implement geometry-based cost estimation (volume/flow-rate).

---

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload

# Verify
python tools/verify_project.py
```

The app auto-creates the SQLite database at `data/maker_ops.db` on startup.

---

## Technology Stack

- **Python 3.11+**
- FastAPI
- SQLAlchemy
- Pydantic v2
- SQLite

**Strictly forbidden:** Celery, Redis, Docker, Authentication, External APIs, Cloud infra, Frontend frameworks.

---

## Architecture & Rules

### Directory Structure
- `app/routers/`: Orchestration only. No business logic.
- `app/services/`: All business logic.
- `app/calculations.py`: Pure, deterministic math functions (No DB access).
- `app/parsers/`: G-code translators (No DB access, no pricing logic).
- `app/models.py`: SQLAlchemy ORM.
- `app/schemas.py`: Pydantic models.

### Mandatory Pricing Formula
```
material_cost = SUM(grams_used * cost_per_gram) * waste_factor
machine_cost  = print_hours * machine_hourly_rate
labor_cost    = (labor_minutes / 60) * target_hourly_rate

true_unit_cost         = material_cost + machine_cost + labor_cost + hardware_cost
suggested_retail_price = true_unit_cost * pricing_multiplier
```
**Defaults:** `pricing_multiplier = 2.7`, `waste_factor = 1.1`, `target_hourly_rate = 25.0`.

---

## Engineering Standards

1. **Deterministic Calculations:** Identical inputs must produce identical outputs.
2. **No Side Effects:** Calculations and Parsers must be pure functions.
3. **Local-First:** No external dependencies or network calls during core operations.
4. **Milestone Adherence:** Follow the order defined in `docs/PROJECT.md`.
5. **Verification:** Always run `tools/verify_project.py` after changes.

---

## Pull Request & Code Review

Prioritize:
1. Preservation of deterministic pricing logic.
2. Strict separation of concerns (Routers vs Services vs Parsers).
3. Compliance with milestone goals.
4. Backwards compatibility of existing endpoints.
5. Clean, type-hinted Python code.

Reject any introduction of SaaS patterns or unnecessary infrastructure.
