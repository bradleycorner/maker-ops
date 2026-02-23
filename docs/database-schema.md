# Database Schema Specification
## Maker Ops Cost Engine

---

## Overview

SQLite database designed for local-first operation.

All tables use integer primary keys and ISO timestamps.

---

## machines

Stores manufacturing equipment data.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | Unique |
| machine_type | TEXT | FDM / Resin / Laser |
| purchase_cost | REAL | USD |
| lifetime_hours | REAL | Expected usable hours |
| maintenance_factor | REAL | e.g. 0.15 |
| created_at | TEXT | ISO timestamp |

---

## materials

| Column | Type |
|---|---|
| id | INTEGER PK |
| name | TEXT |
| cost_per_gram | REAL |
| supplier | TEXT |

---

## products

| Column | Type |
|---|---|
| id | INTEGER PK |
| name | TEXT |
| version | TEXT |
| print_hours | REAL |
| labor_minutes | INTEGER |
| hardware_cost | REAL |
| machine_id | INTEGER FK |
| created_at | TEXT |

---

## product_materials

Join table between products and materials.

| Column | Type |
|---|---|
| id | INTEGER PK |
| product_id | INTEGER FK |
| material_id | INTEGER FK |
| grams_used | REAL |

---

## shows

| Column | Type |
|---|---|
| id | INTEGER PK |
| name | TEXT |
| booth_cost | REAL |
| travel_cost | REAL |
| duration_hours | REAL |
| date | TEXT |

---

## show_sales

| Column | Type |
|---|---|
| id | INTEGER PK |
| show_id | INTEGER FK |
| product_id | INTEGER FK |
| quantity_sold | INTEGER |
| sale_price | REAL |

---

## design_experiments

| Column | Type |
|---|---|
| id | INTEGER PK |
| product_id | INTEGER FK |
| reflector_type | TEXT |
| material_combo | TEXT |
| light_temperature | INTEGER |
| perceived_interest | INTEGER |
| notes | TEXT |
