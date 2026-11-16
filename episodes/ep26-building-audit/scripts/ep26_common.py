import gzip
import json
from pathlib import Path

import geopandas as gpd
import mapbox_vector_tile
import mercantile
from pmtiles.reader import MmapSource, Reader
from shapely.geometry import Polygon, MultiPolygon, box, shape
from shapely.ops import unary_union


def _flat(coords):
    if isinstance(coords[0], (int, float)):
        yield coords
    else:
        for c in coords:
            yield from _flat(c)


def load_truth(path, bbox, zoom=14):
    west, south, east, north = bbox
    clip = box(west, south, east, north)
    rows = []
    with open(path, 'rb') as f:
        reader = Reader(MmapSource(f))
        for t in mercantile.tiles(west, south, east, north, [zoom]):
            data = reader.get(t.z, t.x, t.y)
            if not data:
                continue
            raw = gzip.decompress(data)
            decoded = mapbox_vector_tile.decode(raw)
            layer = decoded.get('building')
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
                g = unary_union(polys)
                if not g.intersects(clip):
                    continue
                g = g.intersection(clip)
                if g.is_empty:
                    continue
                props = dict(feat.get('properties') or {})
                rows.append({**props, 'geometry': g})
    return gpd.GeoDataFrame(rows, geometry='geometry', crs='EPSG:4326')


if __name__ == '__main__':
    bbox = (121.50426756941486, 24.993707143379165, 121.5281345156801, 25.01529185011904)
    g = load_truth('nlsc-new-taipei.pmtiles', bbox)
    print('count', len(g), 'crs', g.crs)
    print('geom types', g.geom_type.value_counts().to_dict())
    print('hull share', (g.get('hull') == 1).mean() if 'hull' in g else None)
    print('height median', g['h'].median() if 'h' in g else None)
    gp = g.to_crs(3826)
    print('area sum m2', round(gp.area.sum(), 1), 'median', round(gp.area.median(), 2))
    print('bounds', g.total_bounds)
