import requests
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union

OVERPASS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
]


def fetch_osm(bbox):
    west, south, east, north = bbox
    q = f"""[out:json][timeout:90];
(
  way["building"]({south},{west},{north},{east});
  relation["building"]({south},{west},{north},{east});
);
out geom;"""
    last = None
    for url in OVERPASS:
        try:
            r = requests.post(url, data={'data': q}, timeout=120, headers={'User-Agent': 'YITU-EP26/1.0'})
            print('endpoint', url, r.status_code, len(r.content))
            if r.status_code == 200:
                return r.json()
            last = r.text[:300]
        except Exception as e:
            last = f'{type(e).__name__}: {e}'
            print('fail', url, last[:150])
    raise RuntimeError(last)


def rings_from_members(members, role):
    rings = []
    for m in members:
        if m.get('type') != 'way' or m.get('role') != role:
            continue
        geom = m.get('geometry') or []
        pts = [(p['lon'], p['lat']) for p in geom]
        if len(pts) >= 4 and pts[0] == pts[-1]:
            rings.append(pts)
    return rings


def osm_polygons(data, bbox):
    clip = box(*bbox)
    rows = []
    for el in data.get('elements', []):
        tags = el.get('tags') or {}
        if el['type'] == 'way':
            geom = el.get('geometry') or []
            pts = [(p['lon'], p['lat']) for p in geom]
            if len(pts) < 4 or pts[0] != pts[-1]:
                continue
            g = Polygon(pts)
        elif el['type'] == 'relation':
            outers = rings_from_members(el.get('members', []), 'outer')
            inners = rings_from_members(el.get('members', []), 'inner')
            polys = []
            for i, outer in enumerate(outers):
                holes = inners if len(outers) == 1 else []
                polys.append(Polygon(outer, holes=holes))
            if not polys:
                continue
            g = unary_union(polys)
        else:
            continue
        if not g.is_valid:
            g = g.buffer(0)
        if g.is_empty or not g.intersects(clip):
            continue
        g = g.intersection(clip)
        if g.is_empty:
            continue
        rows.append({
            'osm_id': f"{el['type'][0]}{el['id']}",
            'building': tags.get('building'),
            'name': tags.get('name'),
            'geometry': g,
        })
    return gpd.GeoDataFrame(rows, geometry='geometry', crs='EPSG:4326')


if __name__ == '__main__':
    bbox = (121.50426756941486, 24.993707143379165, 121.5281345156801, 25.01529185011904)
    data = fetch_osm(bbox)
    print('elements', len(data.get('elements', [])))
    g = osm_polygons(data, bbox)
    print('polygons', len(g), 'types', g.geom_type.value_counts().to_dict())
    print('building tags', g['building'].value_counts().head(10).to_dict())
    gp = g.to_crs(3826)
    print('area sum m2', round(gp.area.sum(), 1), 'median', round(gp.area.median(), 2))
    g.to_parquet('osm_yonghe.parquet')
    print('saved osm_yonghe.parquet')
