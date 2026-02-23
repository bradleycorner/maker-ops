# Maker-Ops Project Definition

## Overview

Maker-Ops is a **local-first manufacturing decision system** designed to evaluate the economic viability of physical products before and during production.

It integrates:

- Parametric CAD workflows
- 3D printing (FDM + Resin)
- Laser fabrication
- Manual finishing
- Real-world craft/jewelry show sales feedback

The system converts manufacturing data into actionable economic decisions.

Maker-Ops is NOT a SaaS platform and is intentionally designed to remain:

- local-first
- deterministic
- open
- extensible
- tooling-oriented

---

## Core Philosophy

Maker-Ops consumes **manufacturing facts**, not tool-specific formats.

The system separates concerns into three layers:

```
Design Tools (FreeCAD, slicers)
        ↓
Data Normalization (parsers)
        ↓
Economic Decision Engine (cost system)
```

All integrations must normalize external data before entering the cost engine.

---

## Long-Term Vision

Maker-Ops evolves toward a unified workflow where:

```
Design → Slice → Economic Evaluation → Production → Sales Feedback → Design Improvement
```

The system ultimately supports:

- reusable engineering assets
- CAD-aware costing
- rapid profitability evaluation
- data-driven product iteration

---

## Development Principles

1. Local-first operation
2. Deterministic calculations
3. Minimal dependencies
4. Open integration architecture
5. Incremental milestones
6. Real manufacturing workflows drive development

Features must support decision-making, not software complexity.

System health and regression verification are tracked in `docs/TEST_STATUS.md`.

---

## Milestone Roadmap

Development progresses through defined milestones.

Each milestone has its own detailed specification document in `/docs`.

---

### ✅ Milestone 1 — Core Cost Engine (Completed)

**Goal:** Establish deterministic manufacturing economics.
**Closed:** 2026-02-23 — PR #1 merged to `main`

Delivered:

- FastAPI backend
- SQLite schema
- Machine amortization
- Pricing formula implementation
- Product cost calculation endpoint
- Show analytics
- README and project documentation
- Regression test baseline (51/51 verified)

Reference:
```
docs/fdm-maker-cost-engine.md
docs/TEST_STATUS.md
```

---

### 🚧 Milestone 2 — Open Slicer Ingestion

**Goal:** Eliminate manual data entry.

Capabilities:

- Upload G-code
- Automatic slicer detection
- Parser-based ingestion
- Normalized print estimate model
- Automatic pricing calculation

Reference:
```
docs/milestone-2-slicer-ingestion.md
```

Outcome:

```
Slice → Upload → Profitability
```

---

### 🔜 Milestone 3 — Engineering Asset System

**Goal:** Treat reusable CAD components as amortized engineering capital.

Concept:

Reusable parametric parts (mounts, hubs, reflectors) reduce future labor costs.

Capabilities:

- Engineering asset tracking
- Design-time amortization
- Asset reuse accounting
- Integration into product costing

Planned document:
```
docs/milestone-3-engineering-assets.md
```

---

### 🔜 Milestone 4 — Design Comparison Engine

**Goal:** Enable economic comparison between design variants.

Capabilities:

- Compare two print configurations
- Profit-per-print-hour analysis
- Material strategy evaluation
- Rapid iteration feedback

Example:

```
Design A vs Design B → profitability delta
```

Planned document:
```
docs/milestone-4-design-comparison.md
```

---

### 🔜 Milestone 5 — Automation Interfaces

**Goal:** Allow external tools to query Maker-Ops programmatically.

Targets:

- CLI access
- FreeCAD macro integration
- Batch estimation workflows
- Script-driven analysis

Planned document:
```
docs/milestone-5-automation.md
```

---

### 🔜 Milestone 6 — CAD Integration Foundations

**Goal:** Bridge parametric design and economic evaluation.

Possible features:

- parameter export ingestion
- CAD metadata costing
- geometry-aware estimation

This milestone prepares for future FreeCAD tooling.

Planned document:
```
docs/milestone-6-cad-integration.md
```

---

### 🔜 Milestone 7 — FreeCAD Workbench Exploration (Long-Term)

**Goal:** Provide design-time manufacturing intelligence.

Potential capabilities:

- lighting component generators
- engineering asset insertion
- print-aware geometry guidance
- manual support design tools

This milestone is exploratory and follows stable backend maturity.

---

## Non-Goals (Permanent)

Maker-Ops will NOT become:

- a hosted SaaS product
- an ecommerce system
- an inventory manager
- a print farm controller
- a generic ERP system

The system remains an engineering decision tool.

---

## Decision Rule

When adding functionality, ask:

> Does this improve manufacturing decision accuracy or workflow efficiency?

If not, it does not belong in Maker-Ops.

---

## Repository Structure

```
docs/
    PROJECT.md
    milestone-*.md

app/
    backend implementation
```

Each milestone document defines implementation requirements and success criteria.

---

## Development Workflow

All development follows a structured branch and review process.

### Branch Strategy

```
feature/<name>   →   develop   →   main
```

- **Feature branches** — one branch per milestone subsection or discrete unit of work
- **`develop`** — integration branch; receives PRs from feature branches
- **`main`** — milestone-gated; only receives PRs at milestone completion

### Process per Milestone Subsection

1. Create a feature branch from `develop`
2. Implement the subsection
3. Verify locally using the regression test script
4. Open a PR to `develop`
5. Merge when verified

### Process at Milestone Completion

1. All subsection PRs are merged to `develop`
2. Full regression suite is run against `develop`
3. `TEST_STATUS.md` is updated with results
4. PR opened from `develop` to `main`
5. Milestone marked closed in `PROJECT.md` and `TEST_STATUS.md`

### CI

GitHub Actions runs on all PRs via Claude Code integration.

---

## How Claude Should Work With This File

Claude must:

1. Treat milestones as ordered development stages.
2. Implement only the active milestone.
3. Avoid introducing future milestone functionality early.
4. Preserve architectural constraints defined in CLAUDE.md.
5. Use milestone documents as authoritative implementation guides.
6. Create feature branches from `develop` for each subsection.
7. Open PRs to `develop` after local verification; open PRs to `main` only at milestone completion.
