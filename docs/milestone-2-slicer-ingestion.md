# Milestone 2 — Open Slicer Ingestion Architecture

## Purpose

This milestone introduces **automatic manufacturing data ingestion** from slicer output files while keeping Maker-Ops fully open and slicer-agnostic.

The system must NOT depend on any specific slicer implementation.

Instead, slicer outputs are translated into a normalized internal format before being processed by the cost engine.

Goal:

> Slice → Upload file → Instantly calculate profitability.

---

## Design Principles

1. **Slicer-agnostic**
   - No business logic tied to Creality, Prusa, Bambu, Orca, etc.
2. **Open architecture**
   - New slicers added via parsers without modifying core logic.
3. **Normalization first**
   - Convert all slicer outputs into a common internal structure.
4. **Deterministic**
   - Parsing produces predictable results.
5. **Minimal implementation**
   - Only one fully implemented parser required initially.

---

## High-Level Flow

```
Upload G-code file
        ↓
Parser Registry
        ↓
Matching Parser
        ↓
Normalized PrintEstimate
        ↓
Cost Engine
        ↓
Pricing Result
```

---

## Normalized Data Model

All slicer parsers must output the same structure.

```json
{
  "filament_grams": 0.0,
  "print_time_seconds": 0,
  "layer_height": null,
  "nozzle_diameter": null,
  "slicer_name": "unknown",
  "source": "gcode"
}
```

### Required Fields

| Field | Description |
|---|---|
| filament_grams | Total filament usage |
| print_time_seconds | Estimated print duration |
| slicer_name | Parser identifier |

Optional values may be null.

---

## Folder Structure

Create a new parsing subsystem:

```
app/
└── parsers/
    ├── base.py
    ├── registry.py
    ├── creality.py
    └── generic.py
```

---

## Base Parser Interface

All parsers must inherit from a common interface.

```python
class BaseParser:
    def can_parse(self, text: str) -> bool:
        """Return True if parser recognizes file format."""

    def extract(self, text: str) -> dict:
        """Return normalized PrintEstimate."""
```

Rules:

- No database access
- No pricing calculations
- Pure text parsing only

---

## Parser Registry

The registry selects the appropriate parser automatically.

Responsibilities:

1. Maintain ordered list of parsers
2. Attempt detection using `can_parse()`
3. Use first matching parser
4. Raise error if no parser matches

Example flow:

```
for parser in parsers:
    if parser.can_parse(text):
        return parser.extract(text)
```

---

## Initial Parser Implementation

### 1. CrealityGcodeParser (Required)

Detect using common header markers such as:

```
Creality
Estimated printing time
Filament used
```

Extract:

- filament grams
- print time

Expected header examples:

```
;Filament used: 486.9g
;Estimated printing time (normal mode): 9h5m
```

Convert time into seconds.

---

### 2. GenericGcodeParser (Fallback)

Purpose:

Provide compatibility with multiple slicers using common comment patterns.

Search for typical metadata lines:

```
;Filament used:
;Material:
;Estimated printing time:
```

This parser acts as a safety net.

---

## API Endpoint

Add new endpoint:

```
POST /calculate/from-gcode
```

### Request

Multipart file upload:

```
file: <gcode>
machine_id: int
labor_minutes: int
hardware_cost: float
material_cost_per_gram: float
```

### Behavior

1. Read first portion of file (header text)
2. Pass text to parser registry
3. Receive normalized estimate
4. Call existing cost_engine functions
5. Return pricing response

---

## Response Format

Same output as existing calculation endpoints:

```json
{
  "true_cost": 72.10,
  "suggested_price": 194.67,
  "profit_margin": 62.9
}
```

---

## Implementation Constraints

- MUST reuse existing cost_engine logic
- MUST NOT duplicate pricing formulas
- MUST NOT add slicer logic to services or routers
- Parsers remain isolated translators

---

## Error Handling

Return clear errors when:

- file contains no recognizable metadata
- required fields cannot be extracted

Example:

```
400 Bad Request
"Unable to detect slicer format"
```

---

## Success Criteria

Milestone is complete when:

- Uploading a Creality G-code file returns pricing automatically
- System remains functional without specifying slicer type
- Adding a new parser requires only a new file in `/parsers`
- No existing endpoints or formulas were modified

---

## Future Extensions (Not Part of This Milestone)

- 3MF archive parsing
- Multiple material support
- Automatic machine detection
- FreeCAD macro integration
- Batch file ingestion

These must NOT be implemented yet.

---

## Guiding Rule

Maker-Ops consumes **manufacturing facts**, not slicer formats.

Parsers translate slicer outputs into normalized manufacturing data.
