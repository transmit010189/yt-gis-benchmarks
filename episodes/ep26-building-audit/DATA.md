# DATA — sources, licences, how to get the data yourself

No raw dataset is committed to this repository. Everything below is fetched by the scripts or
by you; `results/` only holds derived numbers.

## Ground truth — NLSC building footprints (Taiwan)

- Mirror used: <https://huggingface.co/datasets/yhzkiki/taiwan-nlsc-buildings> (PMTiles, I3S harvest,
  22 counties, ~7.06 M buildings with height)
- Original publisher: 內政部國土測繪中心 (NLSC), 國土資訊圖資服務平台
- Licence: 政府資料開放授權條款第 1 版 (Government Open Data TW 1.0) — **attribution required,
  commercial use restricted**; check NLSC's terms before reuse in a product.
- Fidelity check done for EP26 (Taichung sample): official SHP 16,695 vs mirror 16,734 (+0.39 %),
  median centroid shift 0.62 m, median area −1.8 %.
- ⚠️ The I3S-to-PMTiles harvest is a community mirror; if NLSC changes its I3S service the mirror
  may drift. Re-run the fidelity check before trusting new numbers.

## Candidate layers

| layer | version used | source | licence |
|---|---|---|---|
| Overture buildings | release 2026-10-21.0 | <https://overturemaps.org> / `overturemaps` CLI or S3 parquet | ODbL |
| OpenStreetMap | Overpass snapshot at run time | <https://overpass-api.de> | ODbL (attribution + share-alike) |
| WSF3D 90 m | DLR World Settlement Footprint 3D | <https://geoservice.dlr.de/web/maps/eoc:wsf3d> | DLR terms — cite the DOI |

## Rules when you publish derived results

- Attribute NLSC and OSM/Overture in any figure or table you publish.
- Do not redistribute NLSC raw geometry; publish counts/ratios only (that is what this repo does).
- If you add a new site, record the exact bbox and the layer release tag in `results/summary.json`.
