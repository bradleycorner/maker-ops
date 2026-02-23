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
