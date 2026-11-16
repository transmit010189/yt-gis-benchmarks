import time
import duckdb
import geopandas as gpd
import pandas as pd
from shapely import wkb

bbox = (121.50426756941486, 24.993707143379165, 121.5281345156801, 25.01529185011904)
west, south, east, north = bbox
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;")
t0 = time.time()
q = f"""
SELECT id, ST_AsWKB(geometry) AS geom_wkb, sources
FROM read_parquet(
  's3://overturemaps-us-west-2/release/2026-10-21.0/theme=buildings/type=building/*',
  filename=true
)
WHERE bbox.xmin <= {east} AND bbox.xmax >= {west}
  AND bbox.ymin <= {north} AND bbox.ymax >= {south}
"""
print('query start')
rows = con.execute(q).fetchall()
print('rows', len(rows), 'sec', round(time.time() - t0, 1))
recs = []
for rid, gw, src in rows:
    try:
        g = wkb.loads(gw)
    except Exception:
        continue
    recs.append({'id': rid, 'geometry': g, 'sources': src})
gdf = gpd.GeoDataFrame(recs, geometry='geometry', crs='EPSG:4326')
print('gdf', len(gdf), 'types', gdf.geom_type.value_counts().to_dict())
print('bounds', gdf.total_bounds)
gdf.to_parquet('overture_yonghe.parquet')
print('saved overture_yonghe.parquet')
