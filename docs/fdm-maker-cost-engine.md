# Functional Design Model (FDM)
## Maker Product Cost & Show Analytics Engine

---

## 1. Purpose

This system provides an internal decision-support tool for a small-scale hybrid manufacturing workflow combining:

- FDM 3D printing
- Resin printing
- Laser fabrication
- Manual finishing and assembly

Primary goal:

> Determine profitability and pricing BEFORE manufacturing.

Secondary goal:

> Capture real-world sales data from craft/jewelry shows to improve future product decisions.

---

## 2. System Scope

### In Scope

- Product cost calculation
- Machine amortization tracking
- Labor valuation
- Material cost modeling
- Show performance analytics
- Design experiment tracking

### Out of Scope (V1)

- Ecommerce integration
- Inventory management
- Cloud multi-user sync
- Payment processing
- Customer accounts

---

## 3. Design Principles

1. Local-first operation
2. Offline capable
3. Minimal data entry
4. Deterministic calculations
5. Automation-friendly structure
6. Human-readable storage

---

## 4. Architecture Overview

```
Client (Browser)
    ↓
Local Web App (FastAPI)
    ↓
SQLite Database
    ↓
Calculation Engine
```

Runs locally on macOS and accessible via:

- MacBook
- iPad browser
- iPhone browser

---

## 5. Core Modules

---

### 5.1 Product Cost Engine (Primary Module)

#### Inputs

| Field | Type | Description |
|------|------|-------------|
| product_name | string | Unique identifier |
| version | string | Design iteration |
| material_list | array | Materials used |
| print_hours | float | Total machine runtime |
| machine_type | enum | FDM / Resin / Laser |
| labor_minutes | integer | Post-processing + assembly |
| hardware_cost | float | Purchased components |
| waste_factor | float | Failure allowance (default 1.1) |

---

#### Material Object

```yaml
material:
  name: string
  grams_used: float
  cost_per_gram: float
```

---

#### Calculation Formula

```
material_cost =
  SUM(grams_used * cost_per_gram) * waste_factor

machine_cost =
  print_hours * machine_hourly_rate

labor_cost =
  (labor_minutes / 60) * target_hourly_rate

true_unit_cost =
  material_cost + machine_cost + labor_cost + hardware_cost

suggested_retail_price =
  true_unit_cost * pricing_multiplier
```

---

#### Default Constants

```
pricing_multiplier = 2.7
waste_factor = 1.1
```

---

### 5.2 Machine Amortization Module

#### Machine Definition

| Field | Description |
|------|-------------|
| machine_name | Identifier |
| purchase_cost | USD |
| expected_lifetime_hours | float |
| maintenance_factor | percentage |

---

#### Calculation

```
machine_hourly_rate =
  (purchase_cost / expected_lifetime_hours)
  * (1 + maintenance_factor)
```

Example:

```
$800 printer / 800 hrs = $1/hr
```

---

### 5.3 Show Analytics Module

Captures real-world performance.

#### Inputs

| Field | Description |
|------|-------------|
| show_name | Event identifier |
| booth_cost | Total booth fee |
| travel_cost | Fuel + lodging |
| duration_hours | Show duration |
| products_brought | count |
| products_sold | count |
| total_revenue | USD |
| lighting_configuration | reference |

---

#### Calculations

```
total_show_cost = booth_cost + travel_cost

profit =
  total_revenue - total_show_cost

revenue_per_hour =
  total_revenue / duration_hours

break_even_units =
  total_show_cost / avg_product_profit
```

---

### 5.4 Design Experiment Tracker

Purpose: correlate design choices with sales outcomes.

#### Fields

| Field | Description |
|------|-------------|
| design_id | version reference |
| reflector_type | faceted / smooth / ribbed |
| material_combo | copper+CF / silk+PLA |
| light_temp | Kelvin |
| customer_comments | text |
| perceived_interest | 1–5 rating |

---

## 6. Database Schema (Conceptual)

```
machines
products
materials
product_materials
shows
show_sales
design_experiments
```

---

## 7. User Workflow

### Product Evaluation

```
Create Product →
Enter Materials →
Enter Print Time →
Enter Labor →
System Calculates Price →
Decision: Build or Iterate
```

---

### Show Feedback Loop

```
Attend Show →
Record Sales →
System Updates Profit Metrics →
Influences Next Design
```

---

## 8. MVP Screens (V1)

1. Machine Setup
2. New Product Calculator
3. Product History List
4. Show Entry Form
5. Profit Dashboard

---

## 9. Automation Interfaces

System must support:

- JSON import/export
- CLI-triggered calculations
- CSV export for analysis

Example endpoint:

```
POST /calculate_product_cost
```

Response:

```json
{
  "true_cost": 68.42,
  "suggested_price": 184.73,
  "profit_margin": 63.0
}
```

---

## 10. Future Extensions (V2+)

- STL metadata ingestion
- Print-time auto parsing from slicer files
- Material usage estimation
- Lighting configuration A/B comparison
- Predictive pricing suggestions

---

## 11. Success Criteria

System is successful when:

- New product viability determined in < 2 minutes
- Pricing becomes formula-driven
- Show performance trends visible after 3–5 events
- Manufacturing decisions become data-driven
