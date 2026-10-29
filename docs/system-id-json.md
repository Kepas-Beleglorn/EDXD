# `<systemID>.json` — System Cache Files

**Location:** `APP_DIR/system-data/<systemID>.json` (configurable via `config.json` `cache_dir` key)

**Filename:** The FSS system address (integer), e.g., `126667922274.json`

**Purpose:** Per-system cache of scanned body data, populated by the Spansh/EDSM helpers and the Journal Controller. Each file contains all known bodies in a system with their scan state, bio/geosignals, materials, rings, atmosphere, and estimated mapping value. Read on system change to restore previously scanned data.

**Written by:** `SpanshClient.update_system_data()`, `JournalController` (on FSS body/scan events)

**Read by:** `Model.read_data_from_cache()` on system change

## Structure

```json
{
  "system_addr": 126667922274,
  "system_name": "Proo Phoea TO-K c11-0",
  "total_bodies": 1,
  "bodies": {
    "body_0": {
      "body_name": "Proo Phoea TO-K c11-0",
      "body_type": "K",
      "is_star": true,
      "scoopable": true,
      "landable": false,
      "g_force": 31.03,
      "radius": 493671712.0,
      "mapped": false,
      "distance": 0,
      "biosignals": 0,
      "bio_scanned": 0,
      "bio_complete": false,
      "geosignals": 0,
      "geo_scanned": 0,
      "geo_complete": false,
      "materials": {},
      "first_discovered": 2,
      "first_mapped": 0,
      "first_footfalled": 0,
      "bio_found": {},
      "geo_found": {},
      "estimated_value": 1200,
      "has_rings": false,
      "rings": {},
      "atmosphere": null,
      "mean_temp": 4395.0,
      "luminosity": "V",
      "raw_luminosity": "Va",
      "volcanism": "",
      "present_life": "",
      "parents": [],
      "parent_distance": 0.0,
      "pressure": 0.0
    }
  }
}
```

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `system_addr` | `int` | FSS system address (unique numeric identifier) |
| `system_name` | `str` | Human-readable system name |
| `total_bodies` | `int` | Total number of bodies in the system (from Spansh/EDSM) |
| `bodies` | `dict` | Map of body IDs (`"body_0"`, `"body_1"`, …) to body data objects |

## Body Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `body_name` | `str` | Name of the body |
| `body_type` | `str` | Body classification (e.g., star class `"K"`, planet type `"Terrestrial"`) |
| `is_star` | `bool` | `true` if the body is a star |
| `scoopable` | `bool` | `true` if fuel can be scooped from this body |
| `landable` | `bool` | `true` if the body can be landed on |
| `g_force` | `float` | Surface gravity in m/s² (0 for stars) |
| `radius` | `float` | Body radius in meters |
| `mapped` | `bool` | `true` if the body has been fully mapped (Class A) |
| `distance` | `float` | Distance from system entry point in light seconds |
| `biosignals` | `int` | Number of biosignature hotspots detected |
| `bio_scanned` | `int` | Number of biosignature hotspots scanned |
| `bio_complete` | `bool` | `true` if all biosignatures have been scanned |
| `geosignals` | `int` | Number of geosignature hotspots detected |
| `geo_scanned` | `int` | Number of geosignature hotspots scanned |
| `geo_complete` | `bool` | `true` if all geosignatures have been scanned |
| `materials` | `dict` | Map of material names to quantities found on the body surface |
| `first_discovered` | `int` | Discovery rank/flag for this body |
| `first_mapped` | `int` | First-mapped flag |
| `first_footfalled` | `int` | First-footfall flag |
| `bio_found` | `dict` | Map of genus names to discovered biocode entries |
| `geo_found` | `dict` | Map of codex entry names to discovered geology entries |
| `estimated_value` | `int` | Estimated credits value of scanning/mapping this body |
| `has_rings` | `bool` | `true` if the body has rings |
| `rings` | `dict` | Ring system data (inner radius, outer radius, material composition, etc.) |
| `atmosphere` | `str \| null` | Atmosphere type string (e.g., `"CO2"`, `"N2"`) or `null` |
| `mean_temp` | `float` | Mean surface/effective temperature in Kelvin |
| `luminosity` | `str` | Stellar luminosity class (e.g., `"V"`, `"III"`) |
| `raw_luminosity` | `str` | Raw luminosity string from the game (e.g., `"Va"`, `"Vb"`) |
| `volcanism` | `str` | Volcanism type (e.g., `"Water"`, `"Molten rock"`) |
| `present_life` | `str` | Present life classification (e.g., `"Radicoida"`, `"Final"`) |
| `parents` | `list` | List of parent body IDs this body orbits |
| `parent_distance` | `float` | Distance from parent body in light seconds |
| `pressure` | `float` | Atmospheric pressure in pascals |
