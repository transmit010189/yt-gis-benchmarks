import os
import time

import requests
import geopandas as gpd
import mapbox_vector_tile
import mercantile
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union


def _fetch_tile(t, zoom):
    fn = f'wsf3d_{zoom}_{t.x}_{t.y}.mvt'
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        return open(fn, 'rb').read()
    params = {
        'SERVICE': 'WMTS', 'REQUEST': 'GetTile', 'VERSION': '1.0.0',
        'LAYER': 'WSF3D_90m', 'STYLE': '_empty', 'TILEMATRIXSET': 'EPSG:900913',
        'TILEMATRIX': f'EPSG:900913:{zoom}', 'TILEROW': str(t.y), 'TILECOL': str(t.x),
        'FORMAT': 'application/vnd.mapbox-vector-tile',
    }
    last = None
    for host in ['a', 'b', 'c', 'd']:
        urls = [
            f'https://{host}.tiles.geoservice.dlr.de/service/wmts/rest/WSF3D_90m/_empty/EPSG:900913/EPSG:900913:{zoom}/{t.y}/{t.x}?format=application/vnd.mapbox-vector-tile',
            f'https://{host}.tiles.geoservice.dlr.de/service/wmts',
        ]
        for url in urls:
            try:
                if url.endswith('service/wmts'):
                    r = requests.get(url, params=params, timeout=120, headers={'User-Agent': 'Mozilla/5.0'})
                else:
                    r = requests.get(url, timeout=120, headers={'User-Agent': 'Mozilla/5.0'})
                if r.status_code == 200 and len(r.content) > 100:
                    open(fn, 'wb').write(r.content)
                    return r.content
                last = f'{host} {r.status_code} {r.text[:80]}'
            except Exception as e:
                last = f'{host} {type(e).__name__}'
                time.sleep(1)
    print('tile fail', t, last)
    return None


def load_wsf3d(bbox, zoom=11):
    west, south, east, north = bbox
    clip = box(west, south, east, north)
    rows = []
    for t in mercantile.tiles(west, south, east, north, [zoom]):
        content = _fetch_tile(t, zoom)
        if not content:
            continue
        dec = mapbox_vector_tile.decode(content)
        layer = dec.get('wsf3d_90m')
        if not layer:
            continue
        ext = layer['extent']
        tb = mercantile.bounds(t)
        dx = (tb.east - tb.west) / ext
        dy = (tb.north - tb.south) / ext
        for feat in layer['features']:
            geom = feat['geometry']
            polys = []
            if geom['type'] == 'Polygon':
                rings = geom['coordinates']
                polys = [Polygon([(tb.west + px * dx, tb.south + py * dy) for px, py in rings[0]],
                                 holes=[[(tb.west + px * dx, tb.south + py * dy) for px, py in r] for r in rings[1:]])]
            elif geom['type'] == 'MultiPolygon':
                for poly in geom['coordinates']:
                    polys.append(Polygon([(tb.west + px * dx, tb.south + py * dy) for px, py in poly[0]],
                                         holes=[[(tb.west + px * dx, tb.south + py * dy) for px, py in r] for r in poly[1:]]))
            if not polys:
                continue
            g = unary_union(polys).intersection(clip)
            if g.is_empty:
                continue
            props = dict(feat.get('properties') or {})
            rows.append({**props, 'geometry': g})
    return gpd.GeoDataFrame(rows, geometry='geometry', crs='EPSG:4326')


if __name__ == '__main__':
    bbox = (121.50426756941486, 24.993707143379165, 121.5281345156801, 25.01529185011904)
    g = load_wsf3d(bbox)
    print('count', len(g), 'types', g.geom_type.value_counts().to_dict())
    print('cols', list(g.columns))
    print(g.head(3).drop(columns='geometry').to_string())
    gp = g.to_crs(3826)
    print('area sum m2', round(gp.area.sum(), 1), 'median', round(gp.area.median(), 2))
