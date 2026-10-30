# `edxd_ship_status.json` — Ship Status

**Location:** `APP_DIR/edxd_ship_status.json`

**Purpose:** Tracks the current ship's identity, fuel characteristics, mass properties, and FSD modifiers. Written when the journal emits ship-related events (`ShipIdentified`, `Loadout`, `JetConeBoost`, `FsdInjected`, `Cargo`). Used by the dashboard to display ship info and by Spansh to calculate jump range.

**Written by:** `JournalController` on ship-related journal events, via `data_helper.update_ship_status()`

**Read by:** `JournalController` on startup, `Model` for display, Spansh route calculation

## Structure

```json
{
  "ship_type": "mandalay",
  "ship_id": 15,
  "ship_name": "Cerritos",
  "ship_ident": "KBS-01",
  "fuel_capacity": {
    "main": 40.0,
    "reserve": 0.5
  },
  "max_jump_range": null,
  "mass_unladen": null,
  "mass_fsd_optimal": null,
  "cargo": null,
  "cargo_capacity": null,
  "jet_cone_boost_factor": 4.0,
  "fsd_injection_factor": null
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `ship_type` | `str \| null` | Ship class name (lowercase), e.g., `"mandalay"`, `"type-9"` |
| `ship_id` | `int \| null` | Numeric ship ID from the journal |
| `ship_name` | `str \| null` | Player-assigned ship name |
| `ship_ident` | `str \| null` | Ship identification call sign |
| `fuel_capacity` | `object` | Fuel tank capacities (see sub-table below) |
| `fuel_capacity.main` | `float` | Main fuel tank capacity in tonnes |
| `fuel_capacity.reserve` | `float` | Reserve (internal) fuel tank capacity in tonnes |
| `max_jump_range` | `float \| null` | Maximum jump range in light years (calculated by Spansh) |
| `mass_unladen` | `float \| null` | Ship unladen mass in tonnes |
| `mass_fsd_optimal` | `float \| null` | FSD optimal mass in tonnes |
| `cargo` | `int \| null` | Current cargo count (number of items) |
| `cargo_capacity` | `int \| null` | Total cargo capacity in tonnes |
| `jet_cone_boost_factor` | `float \| null` | Jet cone boost multiplier (e.g., `4.0` for a +300% boost) |
| `fsd_injection_factor` | `float \| null` | FSD injection multiplier: `0.25` (Basic), `0.5` (Standard), `1.0` (Premium), or `null` (none) |
