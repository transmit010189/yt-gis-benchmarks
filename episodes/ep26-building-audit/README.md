# EP26 — Free building footprints vs 38,037 official Taiwan buildings

**Question:** how much of the real building stock do free global footprint layers actually cover — not "does it look like a map", but one-to-one matching against official data?

**Answer in one line:** the best free layer (Overture) covers **23–32 %** of official buildings one-to-one and is **33–40 %** ghost polygons; OSM is far worse outside cities (Yilan: 472 polygons for 13,379 buildings = 3.5 %); the 90 m global layer is not a building layer at all — one polygon swallows up to **157** official buildings.

## Test design

| | |
|---|---|
| Ground truth | NLSC building footprints (I3S harvest mirror, ~7.06 M buildings, 22 counties) |
| Truth fidelity check | Taichung sample: official SHP **16,695** vs mirror **16,734** (+0.39 %), median centroid shift **0.62 m**, median area −1.8 % |
| Candidate layers | Overture 2026-10-21.0 (ODbL), OpenStreetMap via Overpass (ODbL), WSF3D 90 m (DLR) |
| Sites | Yonghe (New Taipei), Lukang (Changhua), Yilan City — each a 2.4 × 2.2 km box |
| Buildings tested | 18,650 + 5,008 + 13,379 = **38,037** |

## Results (from `results/metrics_*.csv`)

| site | truth | layer | features | count % | area % | 1:1 coverage % | precision % | ghost % | max swallowed | median shift (m) |
|---|---|---|---|---|---|---|---|---|---|---|
| Yonghe | 18650 | Overture | 6547 | 35.1 | 51.26 | 29.58 | 92.1 | 39.58 | 37 | 4.34 |
| Yonghe | 18650 | OSM | 2861 | 15.34 | 31.6 | 12.02 | 89.51 | 26.98 | 37 | 2.99 |
| Yonghe | 18650 | WSF3D | 885 | 4.75 | 191.73 | 3.07 | 64.97 | 6.1 | 112 | 6.55 |
| Lukang | 5008 | Overture | 2011 | 40.16 | 66.54 | 31.55 | 83.09 | 39.33 | 26 | 5.21 |
| Lukang | 5008 | OSM | 889 | 17.75 | 36.5 | 15.89 | 92.01 | 12.37 | 26 | 1.79 |
| Lukang | 5008 | WSF3D | 628 | 12.54 | 420.76 | 3.31 | 26.75 | 10.19 | 62 | 7.02 |
| Yilan | 13379 | Overture | 3688 | 27.57 | 59.31 | 22.95 | 86.06 | 32.62 | 33 | 3.74 |
| Yilan | 13379 | OSM | 472 | 3.53 | 15.41 | 2.19 | 66.31 | 40.25 | 15 | 3.65 |
| Yilan | 13379 | WSF3D | 694 | 5.19 | 253.64 | 2.32 | 45.24 | 8.36 | 157 | 6.21 |


> If a cell here disagrees with `results/metrics_*.csv`, the CSV wins — run `python verify.py`.

## How to reproduce

```bash
pip install -r requirements.txt          # geopandas, shapely, pyproj, requests
python scripts/ep26_site_runner.py --site yonghe   # downloads candidates + computes metrics
python verify.py                                   # checks the published numbers
```

`verify.py` needs **no** datasets: it re-checks every published value against `results/`, recomputes `count_ratio_pct` from raw counts, and asserts no layer claims more matches than polygons.

Full re-run from scratch needs the ground-truth mirror (several GB) — see `DATA.md` for the exact URLs, licences and checksums. The raw data is **not** committed here.

## What this does not tell you

- Three urban boxes in Taiwan only; rural/township coverage will differ.
- One-to-one matching uses an IoU-style rule (see `scripts/ep26_metrics_lib.py`); other thresholds shift coverage by a few points.
- Overture's own release notes may have changed since 2026-10-21.0.

## Licence

Code: MIT (see `../../LICENSE`). Data: see `DATA.md` — NLSC open data requires attribution and is non-commercial; OSM/Overture are ODbL.
