# Milestone 4 — Design Comparison Engine

## Purpose

Enable economic comparison between design variants to drive manufacturing decisions.

Goal:
> Compare two print configurations → Identify most profitable strategy.

---

## Design Principles

1. **Side-by-side analysis**
   - Products are compared across all cost components.
2. **Efficiency-focused**
   - Introduces "Profit per Print Hour" as a key metric for FDM manufacturing.
3. **Delta-aware**
   - Clearly shows the cost/profit difference between Variant A and Variant B.

---

## New Metrics

### Profit per Print Hour

This metric helps decide between a fast, low-quality print and a slow, high-quality print.

```
profit_per_print_hour = (suggested_retail_price - true_unit_cost) / print_hours
```

---

## API Endpoints

### Comparison

- `POST /products/compare` — Compare two existing products.

**Request Body:**
```json
{
  "product_a_id": 1,
  "product_b_id": 2,
  "target_hourly_rate": 25.0,
  "pricing_multiplier": 2.7,
  "waste_factor": 1.1
}
```

**Response Body:**
```json
{
  "product_a": {
    "name": "Variant A",
    "true_cost": 15.00,
    "suggested_price": 40.50,
    "profit_per_print_hour": 5.10
  },
  "product_b": {
    "name": "Variant B",
    "true_cost": 12.00,
    "suggested_price": 32.40,
    "profit_per_print_hour": 6.80
  },
  "delta": {
    "true_cost": -3.00,
    "profit_per_print_hour": 1.70,
    "better_variant": "product_b"
  }
}
```

---

## Success Criteria

- Comparison endpoint accurately calculates deltas.
- `profit_per_print_hour` is correctly calculated for both products.
- Verification script confirms comparison logic.
