import argparse
import os
import time

import duckdb
import geopandas as gpd
import pandas as pd
from shapely import wkb

from ep26_common import load_truth
from ep26_osm import fetch_osm, osm_polygons
from ep26_wsf3d import load_wsf3d
from ep26_metrics_lib import metrics

SITES = {
    'yonghe': {
        'name': '永和',
        'bbox': (121.50426756941486, 24.993707143379165, 121.5281345156801, 25.01529185011904),
        'pmtiles': 'nlsc-new-taipei.pmtiles',
    },
    'lukang': {
        'name': '鹿港',
        'bbox': (120.4696, 24.0744, 120.4934, 24.0960),
        'pmtiles': 'nlsc-changhua.pmtiles',
    },
    'yilan': {
        'name': '宜蘭市',
        'bbox': (121.7400, 24.7446, 121.7640, 24.7662),
        'pmtiles': 'nlsc-yilan.pmtiles',
    },
}


def overture(bbox):
    west, south, east, north = bbox
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
    q = f"""
    SELECT id, ST_AsWKB(geometry) AS geom_wkb, sources
    FROM read_parquet(
      's3://overturemaps-us-west-2/release/2026-10-21.0/theme=buildings/type=building/*',
      filename=true
    )
    WHERE bbox.xmin <= {east} AND bbox.xmax >= {west}
      AND bbox.ymin <= {north} AND bbox.ymax >= {south}
    """
    t0 = time.time()
    rows = con.execute(q).fetchall()
    print('overture rows', len(rows), 'sec', round(time.time() - t0, 1), flush=True)
    recs = []
    for rid, gw, src in rows:
        try:
            g = wkb.loads(gw)
        except Exception:
            continue
        recs.append({'id': rid, 'geometry': g, 'sources': src})
    return gpd.GeoDataFrame(recs, geometry='geometry', crs='EPSG:4326')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', required=True, choices=list(SITES))
    args = ap.parse_args()
    site = SITES[args.site]
    tag = args.site
    bbox = site['bbox']

    truth_path = f'truth_{tag}.parquet'
    if os.path.exists(truth_path):
        truth = gpd.read_parquet(truth_path)
    else:
        truth = load_truth(site['pmtiles'], bbox)
        truth.to_parquet(truth_path)
    print('truth', len(truth), flush=True)

    ov_path = f'overture_{tag}.parquet'
    if os.path.exists(ov_path):
        ov = gpd.read_parquet(ov_path)
    else:
        ov = overture(bbox)
        ov.to_parquet(ov_path)
    print('overture', len(ov), flush=True)

    osm_path = f'osm_{tag}.parquet'
    if os.path.exists(osm_path):
        osm = gpd.read_parquet(osm_path)
    else:
        osm = osm_polygons(fetch_osm(bbox), bbox)
        osm.to_parquet(osm_path)
    print('osm', len(osm), flush=True)

    wsf_path = f'wsf3d_{tag}.parquet'
    if os.path.exists(wsf_path):
        wsf = gpd.read_parquet(wsf_path)
    else:
        wsf = load_wsf3d(bbox)
        wsf.to_parquet(wsf_path)
    print('wsf', len(wsf), flush=True)

    rows = [metrics(truth, ov, 'Overture'), metrics(truth, osm, 'OSM'), metrics(truth, wsf, 'WSF3D')]
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    df.to_csv(f'metrics_{tag}.csv', index=False)


if __name__ == '__main__':
    main()
