# `slef_loadout.json` — SLEF Loadout File

**Location:** `APP_DIR/slef_loadout.json`

**Purpose:** SLEF (Ship Loadout Exchange Format) file used for Spansh route plotting. Created when a `Loadout` journal event is received. The file wraps the raw Loadout event in a SLEF-compatible envelope with an EDXD header. Read by `SpanshRoutePlotter.galaxy_plotter()` to extract ship fuel capacity, mass, FSD modules, and jump boost for route calculation. Also read by `gui/route_plotter.py` to determine jump range.

**Written by:** `SpanshClient.extract_loadout_to_slef()` on `Loadout` journal events

**Read by:** `SpanshRoutePlotter.galaxy_plotter()`, `gui/route_plotter.py`

## Structure

```json
[
  {
    "header": {
      "appName": "EDXD",
      "appVersion": "0.6.0.0"
    },
    "data": {
      "timestamp": "2026-10-29T20:00:00Z",
      "event": "Loadout",
      "Ship": "Mandalay",
      "ShipID": 15,
      "ShipIdent": "KBS-01",
      "Callsign": "PlayerName",
      "FuelCapacity": {
        "Main": 40.0,
        "Reserve": 0.5
      },
      "FuelScoop": true,
      "Mass": 75.0,
      "UnladenMass": 50.0,
      "Modules": [
        {
          "Slot": "EngineModule",
          "Item": "hi-fsd045",
          "Priority": 1,
          "Group": 0,
          "Store": 0
        }
      ],
      ...
    }
  }
]
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| (array) | `array` | Top-level JSON array containing one ship loadout object |
| `header` | `object` | SLEF metadata envelope |
| `header.appName` | `str` | Always `"EDXD"` — identifies the generating application |
| `header.appVersion` | `str` | EDXD version string (e.g., `"0.6.0.0"`) |
| `data` | `object` | Full Elite Dangerous journal `Loadout` event payload |

## `data` Object

The `data` object contains the complete raw journal `Loadout` event. Key fields used by Spansh integration include:

| Field | Type | Description |
|-------|------|-------------|
| `Ship` | `str` | Ship class name |
| `ShipID` | `int` | Numeric ship ID |
| `ShipIdent` | `str` | Ship identification call sign |
| `FuelCapacity` | `object` | Fuel tank capacities |
| `FuelCapacity.Main` | `float` | Main fuel tank capacity in tonnes |
| `FuelCapacity.Reserve` | `float` | Reserve fuel tank capacity in tonnes |
| `FuelScoop` | `bool` | Whether the ship has a fuel scoop installed |
| `Mass` | `float` | Current ship mass in tonnes |
| `UnladenMass` | `float` | Ship unladen mass in tonnes |
| `Modules` | `array` | Array of installed module objects with slot, item, and priority |
| `Modules[].Slot` | `str` | Module slot name (e.g., `"EngineModule"`, `"PowerDistribution"`) |
| `Modules[].Item` | `str` | Module item identifier (e.g., `"hi-fsd045"`) |
| `Modules[].Priority` | `int` | Power priority level |

> **Note:** The full `Loadout` event contains many more fields (e.g., `Cargo`, `CargoCapacity`, `Commands`, `Modifications`). The complete event payload is preserved as-is in the `data` field.
