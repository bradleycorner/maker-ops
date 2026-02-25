# Milestone 7 — Print Process Normalization

## Purpose

Implement the Print Process Normalization layer defined in the FDM v1.1 addendum
and integrate it into both the backend estimation pipeline and the FreeCAD workbench.

M6 established geometry-based cost estimation using a simple volumetric flow rate.
That model treats all volume equally. Real FDM printing does not.

M7 replaces the approximation with a physics-grounded model driven by actual printer
process parameters — wall count, layer height, infill strategy, purge behaviour —
producing estimates that match manufacturing reality.

Goal:
> CAD Geometry + Print Profile → Normalized Manufacturing Facts → Cost Engine.

---

## Context: FDM v1.1 Addendum

The `docs/fdm-addendum-print-process-normalization.md` document defines this layer
in full. This milestone is the implementation of that specification.

Key architectural mandate from the addendum:

```
Geometry Source
    ↓
Print Process Normalization   ← implemented in this milestone
    ↓
Normalized PrintEstimate
    ↓
Cost Engine
```

Both CAD and slicer paths now converge to the same `PrintEstimate` object.

---

## Design Principles

1. **Profile-driven, not parameter-driven**
   - Printer process parameters live in a `print_profiles` table, not in request bodies.
   - Estimation requests reference a profile by ID.

2. **Decomposed material accounting**
   - Material usage is broken into: perimeter, infill, top/bottom solids, purge waste.
   - Each component is calculated independently and summed.

3. **Deterministic**
   - Identical geometry + identical profile = identical estimate, always.
   - No heuristic multipliers when process parameters are available.

4. **Confidence signalling**
   - The normalization layer reports a `confidence_level` reflecting how much
     geometry detail was available for the estimate.

5. **No slicer emulation**
   - This layer estimates, it does not generate toolpaths.

---

## Data Model Changes

### New Table: `print_profiles`

```
print_profiles
├── id                        INTEGER PRIMARY KEY
├── name                      TEXT NOT NULL
├── nozzle_diameter_mm        REAL NOT NULL      -- e.g. 0.4
├── filament_diameter_mm      REAL DEFAULT 1.75
├── layer_height_mm           REAL NOT NULL      -- e.g. 0.2
├── wall_count                INTEGER DEFAULT 3
├── infill_percentage         REAL DEFAULT 20.0
├── top_layers                INTEGER DEFAULT 4
├── bottom_layers             INTEGER DEFAULT 4
├── extrusion_width_factor    REAL DEFAULT 1.2   -- multiplier on nozzle diameter
├── volumetric_flow_rate_mm3s REAL DEFAULT 10.0  -- mm³/s at rated speed
├── purge_mass_per_change_g   REAL DEFAULT 3.0
└── created_at                TEXT NOT NULL
```

### Update: `products`

- No schema changes required.
- `geometry_metadata` JSON field (added in M6) may store `print_profile_id` used
  during estimation for traceability.

---

## New Service: `app/services/print_normalizer.py`

All normalization logic lives here. Pure functions, no database access.

### Output Object

```python
@dataclass
class PrintEstimate:
    estimated_mass_grams: float
    estimated_print_hours: float
    purge_waste_grams: float
    confidence_level: str          # "high" | "medium" | "low"
    breakdown: MaterialBreakdown

@dataclass
class MaterialBreakdown:
    perimeter_g: float
    infill_g: float
    top_bottom_g: float
    purge_g: float
```

### Core Calculations

**Extrusion width (geometry quantization)**

```
extrusion_width = nozzle_diameter_mm * extrusion_width_factor
```

**Layer count**

```
layer_count = floor(height_mm / layer_height_mm)
```

**Perimeter material**

Estimated from surface area, wall count, layer geometry, and material density:

```
wall_volume = surface_area_mm2 * wall_count * extrusion_width * layer_height / height
perimeter_g = wall_volume * density_g_per_cm3 / 1000
```

**Infill material**

```
internal_volume = total_volume - wall_volume - top_bottom_volume
infill_g = internal_volume * (infill_percentage / 100) * density_g_per_cm3 / 1000
```

**Top and bottom solid layers**

```
top_bottom_volume = footprint_area_mm2 * (top_layers + bottom_layers) * layer_height_mm
top_bottom_g = top_bottom_volume * density_g_per_cm3 / 1000
```

**Purge waste**

```
purge_g = color_changes * purge_mass_per_change_g
```
Default `color_changes = 0` unless specified in request.

**Total mass**

```
estimated_mass_grams = perimeter_g + infill_g + top_bottom_g + purge_g
```

**Print time**

```
total_extruded_volume = estimated_mass_grams / (density_g_per_cm3 / 1000)
estimated_print_hours = total_extruded_volume / volumetric_flow_rate_mm3s / 3600
```

**Confidence level**

| Geometry available | Confidence |
|---|---|
| Volume + surface area + footprint | `high` |
| Volume + bounding box only | `medium` |
| Volume only | `low` |

---

## API Changes

### New Endpoints: Print Profile CRUD

```
POST   /print-profiles          Create a profile
GET    /print-profiles          List all profiles
GET    /print-profiles/{id}     Retrieve a profile
```

**Create request body:**
```json
{
  "name": "0.4mm Standard PLA",
  "nozzle_diameter_mm": 0.4,
  "layer_height_mm": 0.2,
  "wall_count": 3,
  "infill_percentage": 20.0,
  "top_layers": 4,
  "bottom_layers": 4,
  "extrusion_width_factor": 1.2,
  "volumetric_flow_rate_mm3s": 10.0,
  "purge_mass_per_change_g": 3.0
}
```

### Updated Endpoint: `POST /products/estimate-from-geometry`

Add optional `print_profile_id` parameter. When provided, the normalization
layer runs. When absent, falls back to M6 volumetric flow rate behaviour.

**Updated request body:**
```json
{
  "name": "Parametric Bracket",
  "volume_mm3": 15000.0,
  "material_id": 1,
  "machine_id": 1,
  "dimensions_mm": {"x": 50.0, "y": 30.0, "z": 20.0},
  "print_profile_id": 1,
  "color_changes": 0,
  "save": false
}
```

**Updated response (with profile):**
```json
{
  "estimated_mass_g": 19.14,
  "estimated_print_hours": 0.53,
  "print_profile_id": 1,
  "normalization": {
    "perimeter_g": 8.20,
    "infill_g": 7.40,
    "top_bottom_g": 3.54,
    "purge_g": 0.0,
    "confidence_level": "medium"
  },
  "calculation": {
    "true_cost": 4.87,
    "suggested_price": 13.15,
    "profit_margin": 62.9,
    "profit_per_print_hour": 15.64
  }
}
```

---

## FreeCAD Workbench Updates

### Profile Selection

The workbench Estimate command gains a print profile selector.

- On first run with no profiles defined, falls back to M6 volumetric estimate.
- When profiles exist, user selects a profile ID; it is sent with the request.
- Selected profile ID is remembered for the session.

### Dialog: Normalization Breakdown

The cost estimate dialog gains a normalization section when a profile is used:

```
────────────────────────────────────────────
  BracketBody
────────────────────────────────────────────
  Profile:       0.4mm Standard PLA
  Volume:              15,000.0 mm³
  Dimensions:    50.0 × 30.0 × 20.0 mm
  Confidence:          medium

  Material Breakdown
  ─ Perimeter:            8.20 g
  ─ Infill (20%):         7.40 g
  ─ Top/Bottom:           3.54 g
  ─ Purge:                0.00 g
  Total Mass:            19.14 g

  Print Time:             0.53 hrs
  True Cost:             $4.87
  SRP (2.7×):           $13.15
  Margin:                62.9%
════════════════════════════════════════════
  SUMMARY — 1 body
...
```

### Live Mode

Live mode console line gains profile name and confidence when a profile is active:

```
⚡ Live | BracketBody | 15,000 mm³  50.0×30.0×20.0 mm | 19.14 g (med)  0.53 h | Cost $4.87  SRP $13.15
```

---

## File Layout Changes

```
app/
├── routers/
│   └── print_profiles.py     ← new
└── services/
    └── print_normalizer.py   ← new

freecad/Mod/MakerOps/
└── InitGui.py                ← updated (profile selector + breakdown in dialog)
```

---

## Success Criteria

- `print_profiles` table created and managed via CRUD endpoints.
- `POST /products/estimate-from-geometry` returns normalization breakdown when
  `print_profile_id` is supplied.
- Normalization service functions are pure and deterministic.
- Estimate falls back gracefully to M6 behaviour when no profile is provided.
- FreeCAD workbench dialog shows material breakdown and confidence level.
- Verification script confirms normalization accuracy against known inputs.
- All prior regression tests continue to pass.
