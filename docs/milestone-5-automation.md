# Milestone 5 — Automation Interfaces

## Purpose

Enable external tools and scripts to interact with the Maker-Ops engine programmatically without using a browser.

Goal:
> Scripted Ingestion → Automated Evaluation → Batch Decision Support.

---

## Design Principles

1. **CLI-First**
   - Provide a standalone Python CLI tool for common operations (upload, list, calculate).
2. **Headless Integration**
   - Ensure all output is machine-readable (JSON).
3. **Macro-ready**
   - Provide examples for FreeCAD integration.

---

## Components

### 1. Maker-Ops CLI (`maker-ops-cli.py`)

A command-line interface that communicates with the running FastAPI server.

**Commands:**
- `maker-ops-cli upload <file.gcode> --machine-id <id> --material-cost <cost>`
- `maker-ops-cli calculate <product-id>`
- `maker-ops-cli compare <id_a> <id_b>`
- `maker-ops-cli list-products`

### 2. Batch Processing Endpoint

- `POST /automation/batch-calculate` — Accept a list of product IDs and return a summary JSON.

---

## Success Criteria

- CLI tool can successfully upload G-code and retrieve pricing.
- Batch endpoint returns results for multiple products in a single call.
- Sample FreeCAD macro demonstrates how to trigger a calculation from within CAD.
- Verification script confirms CLI functionality.
