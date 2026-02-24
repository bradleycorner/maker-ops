# Milestone 6 — CAD Integration Foundations

## Purpose

Bridge the gap between parametric CAD models and economic evaluation by estimating costs directly from geometry data (volume, dimensions) before a G-code file exists.

Goal:
> Design Parameter → Geometric Estimation → Pre-Slice Costing.

---

## Design Principles

1. **Volume-based Estimation**
   - Use part volume and material density to calculate mass.
2. **Speed-based Time Estimation**
   - Use volume and a configurable "Volumetric Flow Rate" (mm³/s) to estimate print time.
3. **Parametric Metadata**
   - Store CAD parameters (length, width, height, volume) alongside the product.

---

## Data Model Changes

### Product Update

- Add `geometry_metadata` (JSON) to store volume, dimensions, and estimated density.

---

## API Endpoints

### Geometry Estimation

- `POST /products/estimate-from-geometry` — Calculate cost based on volume, density, and machine flow rate.

**Request Body:**
```json
{
  "name": "Parametric Bracket",
  "volume_mm3": 15000.0,
  "material_id": 1,
  "machine_id": 1,
  "infill_percentage": 20.0,
  "volumetric_flow_rate": 10.0
}
```

---

## Success Criteria

- Geometric estimation endpoint correctly calculates mass from volume and density.
- Print time is estimated using volumetric flow rate.
- Product results include geometric metadata.
- Verification script confirms geometry-based pricing accuracy.
