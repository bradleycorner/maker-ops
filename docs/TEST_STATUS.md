# Test Status

## Purpose

This document records the verified behavioral state of the Maker-Ops system at each milestone boundary. It exists to:

- Establish a clear baseline of confirmed system behavior
- Track which functional areas have been validated
- Record when new capabilities are verified or breaking changes are introduced
- Serve as the authoritative record of what the system is known to do correctly

**Update policy — this document is updated only when:**

- Regression test coverage is expanded
- A milestone is completed and its behavior verified
- A breaking change is intentionally introduced

This document does not describe implementation details.

---

## Milestone 1 — Initial Backend Scaffold

**Completed:** 2026-02-23
**Merged:** PR #1 → `main`
**Status:** ✅ Closed — 51/51 checks passed

### Baseline Definition

A local HTTP API that accepts structured input, persists data to a local database, and returns deterministic manufacturing cost figures. The system starts without manual configuration, creates its own database on first run, and serves interactive API documentation immediately.

### Verified Areas

| Area | Status |
|---|---|
| Machine management | ✅ Verified |
| Material management | ✅ Verified |
| Product management | ✅ Verified |
| Cost calculation | ✅ Verified |
| Show management | ✅ Verified |
| Sales recording | ✅ Verified |
| Show analytics | ✅ Verified |
| Error handling | ✅ Verified |

### Verified Capabilities

**Startup behavior**
- System starts without manual configuration
- Database and all tables are created automatically on first run
- Interactive API documentation is available immediately after startup

**Data management**
- Machines can be created, listed, and retrieved by ID
- Materials can be created, listed, and retrieved by ID
- Products can be created with one or more material usage records, listed, and retrieved by ID
- Shows can be created, listed, and retrieved by ID
- Sales can be recorded against a show and listed per show

**Cost calculation**
- True unit cost is computed from material, machine time, and labor inputs
- Suggested retail price is derived from true unit cost
- Profit margin is returned as a percentage of suggested price
- Calculation constants (labor rate, pricing multiplier, waste factor) can be overridden per request without altering stored data
- Default constants produce identical results on repeated calls with identical inputs

**Show analytics**
- Total show cost is the sum of booth and travel costs
- Total revenue is the sum of all sales recorded at a show
- Revenue per hour is derived from total revenue and show duration
- Break-even unit count reflects the number of units needed to cover total show cost
- Profit or loss is reported per show

**Error handling**
- Requests for non-existent resources return a 404 response
- Responses conform to the documented schema

### Test Run Summary

| Milestone | Date | Checks | Passed | Failed | PR |
|---|---|---|---|---|---|
| 1 — Initial backend scaffold | 2026-02-23 | 51 | 51 | 0 | #1 → main |
| 2 — Open Slicer Ingestion | 2026-02-23 | 55 | 55 | 0 | #2 → main |
| 3 — Engineering Asset System | 2026-02-23 | 58 | 58 | 0 | #3 → main |
| 4 — Design Comparison Engine | 2026-02-23 | 61 | 61 | 0 | #4 → main |
| 5 — Automation Interfaces | 2026-02-23 | 65 | 65 | 0 | #5 → main |

---

## Milestone 2 — Open Slicer Ingestion

**Completed:** 2026-02-23
**Status:** ✅ Closed

### Verified Capabilities

**G-code Ingestion**
- Uploading a Creality G-code file returns pricing automatically
- System remains functional without specifying slicer type via fallback parser
- Print time and filament usage are extracted from G-code headers
- Cost engine correctly processes extracted values into true cost and suggested price
- Multipart form-data uploads are supported for G-code files

---

## Milestone 3 — Engineering Asset System

**Completed:** 2026-02-23
**Status:** ✅ Closed

### Verified Capabilities

**Engineering Assets**
- Engineering assets can be created with design hours and labor rates
- Assets can be attached to products to include amortized design cost
- Cost engine correctly includes `asset_cost` in `true_unit_cost`
- Asset cost is calculated as `(design_hours * labor_rate) / target_uses`
- Product cost calculations reflect the sum of all attached engineering assets

---

## Milestone 4 — Design Comparison Engine

**Completed:** 2026-02-23
**Status:** ✅ Closed

### Verified Capabilities

**Design Comparison**
- Side-by-side comparison of two products is supported via `/products/compare`
- `profit_per_print_hour` is calculated and reported for each product
- Comparison delta shows the difference in true cost and profit efficiency
- Delta correctly identifies the "better" variant based on profit per machine hour
- Engineering assets are correctly included in comparison calculations

---

## Milestone 5 — Automation Interfaces

**Completed:** 2026-02-23
**Status:** ✅ Closed

### Verified Capabilities

**Automation & Batching**
- Batch calculation of multiple products in one request via `/automation/batch-calculate`
- Dedicated CLI tool (`tools/maker_ops_cli.py`) supports list, calculate, compare, and upload
- Headless execution produces machine-readable JSON output
- Sample FreeCAD macro demonstrates external integration
- Verification script confirms CLI-to-API communication
