# FDM Addendum
## Print Process Normalization Layer
### Version: FDM v1.1 (Subversion Amendment)

---

## 1. Purpose of This Addendum

This document amends the Functional Design Model (FDM) to introduce a
required architectural layer between **geometry sources** and the
**Product Cost Engine**.

This change formalizes behavior discovered during real-world CAD and slicer
validation testing.

The original FDM remains valid.  
This addendum clarifies how `grams_used` and manufacturing quantities are derived.

---

## 2. Problem Statement

The original FDM assumes the existence of reliable manufacturing inputs:

```
grams_used
print_hours
material_cost
```

However, geometry-based systems (CAD) and execution-based systems (slicers)
do not produce equivalent data.

CAD models describe **ideal mathematical geometry**.

FDM manufacturing produces **extrusion-constrained geometry** governed by:

- nozzle diameter
- extrusion width
- layer height
- wall enforcement rules
- infill strategies
- purge and transition waste

Therefore:

> CAD geometry is design intent, not manufacturing fact.

A normalization layer is required.

---

## 3. Architectural Amendment

### Previous Flow (Implicit)

```
Geometry Source
    ↓
Cost Engine
```

### Updated Flow (Authoritative)

```
Geometry Source
    ↓
Print Process Normalization   ← NEW REQUIRED LAYER
    ↓
Normalized PrintEstimate
    ↓
Cost Engine
```

This aligns CAD ingestion with existing slicer ingestion architecture.

---

## 4. Definition: Print Process Normalization

Print Process Normalization converts design geometry into estimated
manufacturing execution using printer process constraints.

Output from this layer represents **manufacturing-equivalent data**.

---

## 5. Responsibilities of the Normalization Layer

The normalization system MUST:

1. Translate ideal geometry into printable geometry.
2. Apply extrusion quantization rules.
3. Estimate perimeter extrusion behavior.
4. Estimate infill material usage.
5. Account for top and bottom layer solids.
6. Model purge and transition waste.
7. Produce deterministic material estimates.

The normalization layer MUST NOT perform pricing calculations.

---

## 6. Normalized Output Object

All geometry integrations MUST produce:

```json
PrintEstimate {
  estimated_mass_grams,
  estimated_print_time_hours,
  purge_waste_grams,
  confidence_level
}
```

This object becomes the authoritative input to the Cost Engine.

---

## 7. Print Profile (New Core Entity)

Manufacturing estimation requires explicit printer configuration.

### Definition

```
print_profile:
    nozzle_diameter_mm
    filament_diameter_mm
    layer_height_mm
    wall_count
    infill_percentage
    top_layers
    bottom_layers
    extrusion_width_factor
    purge_mass_per_change_g
```

A product or estimation session references exactly one print profile.

---

## 8. Geometry Quantization Principle

FDM printing cannot reproduce arbitrary wall thickness.

Printable thickness is defined as:

```
printable_wall =
    ceil(design_wall / extrusion_width)
        × extrusion_width
```

Where:

```
extrusion_width ≈ nozzle_diameter × width_factor
```

This transformation converts ideal geometry into manufacturable geometry.

---

## 9. Material Estimation Model

Material usage SHALL be decomposed into components:

```
total_material =
    perimeter_material
  + infill_material
  + top_bottom_material
  + purge_material
```

### 9.1 Perimeter Material

Derived from:

- external surface perimeter
- wall count
- layer count

---

### 9.2 Infill Material

```
internal_volume × infill_percentage
```

---

### 9.3 Top and Bottom Layers

```
surface_area × solid_layer_count × layer_height
```

---

### 9.4 Purge Waste

```
color_changes × purge_mass_per_change
```

Purge waste is considered manufacturing overhead.

---

## 10. Relationship to Existing Milestones

This amendment does NOT replace Milestone 6.

Instead:

| Milestone | Updated Interpretation |
|---|---|
| Milestone 2 | Observed manufacturing normalization (G-code) |
| Milestone 6 | Predicted manufacturing normalization (CAD) |

Both now produce the same normalized object type.

---

## 11. Determinism Requirement

Normalization calculations MUST be deterministic.

The system MUST avoid heuristic multipliers when process parameters
are available.

Multipliers are permitted only as fallback when geometry features
cannot be extracted.

---

## 12. Non-Goals

This layer is NOT a slicer.

It MUST NOT:

- generate toolpaths
- simulate motion planning
- replicate slicer UI behavior
- depend on specific slicer implementations

The goal is estimation, not execution.

---

## 13. Architectural Outcome

After this amendment:

- CAD integrations produce predicted manufacturing facts.
- Slicer integrations produce observed manufacturing facts.
- The Cost Engine consumes both identically.

This preserves the core Maker-Ops principle:

> Economic decisions operate on normalized manufacturing reality.

---

## 14. Versioning

This document represents:

```
FDM Version 1.1 (Subversion Amendment)
```

No breaking schema changes are introduced.

Existing implementations remain valid but incomplete
until normalization is implemented.
