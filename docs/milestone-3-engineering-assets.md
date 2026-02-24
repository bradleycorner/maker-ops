# Milestone 3 — Engineering Asset System

## Purpose

This milestone treats reusable CAD components (mounts, hubs, reflectors) as **amortized engineering capital**.

Reusable design reduces future labor costs. By tracking the time spent designing a part and how many times it is reused, Maker-Ops can distribute design costs across multiple products.

Goal:

> Design once → Reuse many times → Reduce per-unit cost.

---

## Design Principles

1. **Asset-centric**
   - Parts are treated as individual engineering units.
2. **Amortization-based**
   - Design time is recovered through reuse.
3. **Product integration**
   - Engineering assets are "attached" to products similar to materials.
4. **Deterministic**
   - Asset costs are calculated using fixed formulas.

---

## Data Model

### Engineering Asset

| Field | Description |
|---|---|
| name | Unique identifier for the part |
| design_hours | Time spent creating the parametric model |
| labor_rate | Hourly rate for engineering design |
| target_uses | Expected number of times this asset will be reused |

### Formula

```
asset_unit_cost = (design_hours * labor_rate) / target_uses
```

---

## Schema Changes

Add a new table: `engineering_assets`.

Update `products` to support a relationship with `engineering_assets` via a join table `product_assets`.

---

## API Endpoints

### Engineering Assets

- `POST /assets/` — Create an engineering asset
- `GET /assets/` — List all assets
- `GET /assets/{id}` — Get asset details

### Product Integration

- `POST /products/{id}/assets` — Attach an asset to a product
- `GET /products/{id}/assets` — List assets attached to a product

---

## Cost Engine Integration

The `compute_product_cost` service must be updated to include `engineering_asset_cost` in the `true_unit_cost`.

```
true_unit_cost = material_cost + machine_cost + labor_cost + hardware_cost + asset_cost
```

---

## Success Criteria

- Assets can be created and tracked.
- Assets can be associated with products.
- Product cost calculations include the amortized cost of all attached assets.
- Verification script confirms asset cost inclusion in pricing results.
