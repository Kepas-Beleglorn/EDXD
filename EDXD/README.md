# EDXD · Elite Dangerous eXploration Dashboard

A cross-platform, real-time dashboard for explorers:

* **Planetary surface materials** – instantly see every deposit in a system.
* **Bio-signals & landability** – icons indicate biomasses and whether a body is landable.
* **Dual detail panes** – one for the selected row, one for your current in-game target.
* **System progress** – live counter of scanned / total bodies (belt clusters ignored).
* **Dark “ED” theme** – looks at home next to EDMC / EDSM.
* **100 % Python** – runs on Linux, macOS and Windows (no .NET, no exe).

Planned:

* EDSM API link to pull scan & map values.
* Bookmark-/route-helper pane.
* Optional journal replay exporter.

---

## Installation

```bash
python3 -m venv edxd-env
source edxd-env/bin/activate
pip install -r requirements.txt
python -m edxd --journals "/path/to/Saved Games/Frontier Developments/Elite Dangerous"

## Licence
EDXD is released under the Creative Commons Attribution-NonCommercial 4.0
International licence (CC BY-NC 4.0).  
That means you’re welcome to use, modify and share it for free-of-charge,
**but not sell it**.  See `LICENSE` for details.

https://creativecommons.org/licenses/by-nc/4.0/
