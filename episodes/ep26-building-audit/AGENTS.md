# AGENTS.md — how an agent reproduces EP26 in one pass

You are an AI agent asked to "reproduce this benchmark". Do these steps in order.
Stop and report if a step fails — do not invent numbers.

## 0. What you are checking

Claim: on three 2.4 × 2.2 km boxes in Taiwan (Yonghe / Lukang / Yilan), the best free
building-footprint layer (Overture) matches only **23–32 %** of official buildings one-to-one,
with **33–40 %** ghost polygons; OSM covers **2.2–16 %**; the WSF3D 90 m layer is not a
building layer (area 1.9–4.2× official, single polygon swallows up to 157 buildings).

## 1. Cheap path (no datasets, ~10 s)

```bash
cd episodes/ep26-building-audit
python verify.py --verbose     # exit 0 and "PASS" = published numbers match results/
```

This re-checks all 126 published values against `results/metrics_*.csv`, recomputes
`count_ratio_pct` from raw counts, and asserts no layer claims more matches than polygons.
If it fails, the repository is broken — report the failing lines verbatim.

## 2. Full path (needs several GB, ~30–60 min)

```bash
pip install -r requirements.txt
# ground truth mirror (~7 M NLSC buildings, PMTiles) — see DATA.md for URL + licence
python scripts/ep26_site_runner.py --site yonghe   # repeat for lukang, yilan
python verify.py                                   # numbers must still match
```

Allowed deviations: newer Overture/OSM releases change candidate layers, so coverage may move
by a few points. Report the release tag you used. **Do not** overwrite `results/` — write your
own output next to it and diff.

## 3. What to report back

- which path you ran, wall-clock time, and the exact commands
- the PASS/FAIL of `verify.py`
- any metric that moved >1 percentage point vs `results/summary.json`, with the layer version
- the licence obligations you accepted (NLSC attribution / non-commercial; ODbL share-alike)

## Hard rules

- Never fabricate or "round up" a number; every figure must come from a file this run produced.
- Do not commit raw datasets, videos, or API keys into the repo.
- If a dataset is gated or gone, say so and stop that branch — do not substitute another source
  silently.
