import gzip
import json
import mercantile
from pmtiles.reader import Reader, MmapSource
import mapbox_vector_tile

path = 'nlsc-new-taipei.pmtiles'
with open(path, 'rb') as f:
    reader = Reader(MmapSource(f))
    header = reader.header()
    print('header', header)
    lon, lat = 121.5162, 25.0045
    t = mercantile.tile(lon, lat, 14)
    print('tile', t)
    data = reader.get(t.z, t.x, t.y)
    print('bytes', len(data), data[:4])
    try:
        raw = gzip.decompress(data)
        print('gzip ok', len(raw))
    except Exception as e:
        raw = data
        print('not gzip', e)
    decoded = mapbox_vector_tile.decode(raw)
    print('layers', list(decoded.keys()))
    for name, layer in decoded.items():
        print(name, 'features', len(layer['features']))
        for feat in layer['features'][:3]:
            print(feat['geometry']['type'], feat['properties'])
