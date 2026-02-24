# Maker-Ops AI Bootstrap Context

## Project Purpose
Maker-Ops is a local-first manufacturing cost calculator and show analytics tool.
It is NOT SaaS and must remain offline-capable.

## Current Status
Milestone 1 COMPLETE:
- FastAPI backend operational
- SQLite schema stable
- Deterministic pricing engine implemented
- Regression verification via tools/verify_project.py

Current work:
Milestone 2 — Test generation and parser infrastructure.

## Architecture Rules (MANDATORY)
- Routers contain NO business logic
- Services contain all calculations
- calculations.py must remain pure functions
- Deterministic outputs only
- No cloud dependencies
- No authentication systems

## Testing System
All changes must pass:

python tools/verify_project.py

Tests validate:
- server startup
- API endpoints
- pricing calculations
- schema stability

Current failure:
Test generation and expansion work is incomplete.

## Developer Expectation
When generating code:
1. Prefer small incremental changes.
2. Do not refactor unrelated modules.
3. Maintain backward compatibility.
4. Add tests before adding new behavior.

## Immediate Task
Assist with implementing test generation infrastructure without breaking existing regression tests.
