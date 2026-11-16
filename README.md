# yt-gis-benchmarks — reproducible GIS benchmarks from the YITU channel

Every episode here is a **small, runnable package**: the claim, the numbers as machine-readable
JSON/CSV, the scripts that produced them, and a verifier that fails if the published numbers stop
matching the data. Point an AI agent at `AGENTS.md` in an episode folder and it can reproduce or
audit the result without asking a human.

## Episodes

| EP | topic | one-line finding | verify |
|---|---|---|---|
| 26 | Free building footprints vs official NLSC buildings (38,037 tested) | best free layer covers 23–32 % one-to-one; 33–40 % ghosts | `cd episodes/ep26-building-audit && python verify.py` |

## Why this layout

- `results/summary.json` — every number with its definition, source URL and licence
- `results/metrics_*.csv` — the raw table the video's charts were drawn from
- `scripts/` — the code that made them (no notebooks, no hidden steps)
- `verify.py` — re-checks published values against the files; exits non-zero on drift
- `AGENTS.md` — instructions written for an AI agent: cheap path (~10 s), full path (~1 h), what to report
- `DATA.md` — where each dataset comes from, its licence, and what may not be redistributed

## Conventions

- Numbers are rounded to 2 decimals; `verify.py` tolerates ±0.02.
- No raw datasets, videos, audio or keys in git. Big artefacts live on the channel's OneDrive and
  are linked, not committed.
- If a re-run disagrees with the published value by more than one percentage point, open an issue —
  that is a finding, not a nuisance.

## Licence

Code MIT (`LICENSE`). Derived numbers free to reuse with attribution to the YITU channel and to the
underlying data providers listed in each episode's `DATA.md`.
