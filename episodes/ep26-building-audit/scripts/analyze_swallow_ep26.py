# -*- coding: utf-8 -*-
"""EP26 swallow analysis: recompute s08 stats + export worst-case polygon (s09 visual)."""
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union

D = Path(r"C:\Users\Administrator\Desktop\ep26_data")
OUT = Path(r"C:\Users\Administrator\Desktop\專案_YouTube與GIS\ep26_building_audit\06_assets_images")
OUT.mkdir(parents=True, exist_ok=True)

def load(name):
    return gpd.read_parquet(D / f"{name}.parquet")

results = {}
for site in ("yonghe", "lukang", "yilan"):
    t = load(f"truth_{site}")
    o = load(f"overture_{site}")
    if t.crs != o.crs:
        o = o.to_crs(t.crs)
    tc = t.copy(); tc["geometry"] = tc.representative_point()
    tc["tid"] = range(len(tc))
    j = gpd.sjoin(tc[["tid", "geometry"]], o[["geometry"]], how="inner", predicate="within")
    j = j.rename(columns={"index_right": "oid"})
    counts = j.groupby("oid").size()
    big = counts[counts >= 2]
    rows = []
    for oid, n in big.items():
        geoms = list(t.loc[j[j.oid == oid]["tid"].values, "geometry"])
        u = unary_union(geoms).buffer(0)
        parts = len(u.geoms) if u.geom_type.startswith("Multi") else 1
        poly = o.loc[oid, "geometry"]
        # hull cleanliness: polygon boundary must not cross any truth building interior
        crosses = sum(1 for g in geoms if poly.exterior.intersects(g.buffer(-0.15)))
        iou = poly.intersection(u).area / max(poly.union(u).area, 1e-9)
        rows.append(dict(oid=int(oid), n=n, parts=parts, crosses=crosses, iou=iou,
                         area=poly.area, u_area=u.area))
    df = pd.DataFrame(rows)
    single = (df.parts == 1).mean() * 100
    clean_cross = (df.crosses == 0).mean() * 100
    clean_iou90 = (df.iou >= 0.85).mean() * 100
    results[site] = dict(groups=int(len(df)), swallowed_buildings=int(df.n.sum()),
                         single_block_pct=round(single, 1), no_crossing_pct=round(clean_cross, 1),
                         iou85_pct=round(clean_iou90, 1), swallow_max=int(df.n.max()))
    print(site, results[site], flush=True)
    if site == "yonghe":
        worst = df.loc[df.n.idxmax()]
        wg = o.loc[[int(worst.oid)]]
        wg.to_file(OUT / "worst_polygon_yonghe.geojson", driver="GeoJSON")
        # save the swallowed buildings for plotting
        idxs = j[j.oid == int(worst.oid)]["tid"].values
        t.loc[idxs].to_file(OUT / "worst_swallowed_buildings_yonghe.geojson", driver="GeoJSON")
        results["worst"] = dict(oid=int(worst.oid), n=int(worst.n), parts=int(worst.parts),
                                crosses=int(worst.crosses), iou=round(float(worst.iou), 3),
                                area_m2=round(float(worst.area), 1))
        print("WORST", results["worst"], flush=True)

(D / "swallow_analysis.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
print("WROTE", D / "swallow_analysis.json")
