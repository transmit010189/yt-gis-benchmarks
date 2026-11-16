import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from ep26_common import load_truth
from ep26_wsf3d import load_wsf3d

BBOX = (121.50426756941486, 24.993707143379165, 121.5281345156801, 25.01529185011904)


def metrics(truth, chal, label):
    t = truth.to_crs(3826)
    c = chal.to_crs(3826)
    tp = gpd.GeoDataFrame({'tid': range(len(t)), 'geometry': t.geometry.centroid}, crs=3826)
    cp = gpd.GeoDataFrame({'cid': range(len(c)), 'geometry': c.geometry.centroid}, crs=3826)
    # truth centroid inside challenger polygon
    j = gpd.sjoin(tp, c[['geometry']], predicate='within', how='left')
    matched_truth = j['index_right'].notna().sum()
    per_chal = j[j['index_right'].notna()].groupby('index_right').size()
    swallow_max = int(per_chal.max()) if len(per_chal) else 0
    real_chal = len(per_chal)
    ghost = len(c) - real_chal
    # nearest distances both ways
    n1 = gpd.sjoin_nearest(tp, cp, how='left', distance_col='d_t2c')
    n2 = gpd.sjoin_nearest(cp, tp, how='left', distance_col='d_c2t')
    return {
        'layer': label,
        'features': len(c),
        'truth_matched': int(matched_truth),
        'truth_coverage_pct': round(100 * matched_truth / len(t), 2),
        'real_features': int(real_chal),
        'precision_pct': round(100 * real_chal / len(c), 2) if len(c) else None,
        'ghost_features': int(ghost),
        'ghost_pct': round(100 * ghost / len(c), 2) if len(c) else None,
        'swallow_max': swallow_max,
        'shift_median_m_t2c': round(float(n1['d_t2c'].median()), 2),
        'shift_median_m_c2t': round(float(n2['d_c2t'].median()), 2),
        'area_sum_m2': round(float(c.area.sum()), 1),
    }


if __name__ == '__main__':
    import os
    truth = load_truth('nlsc-new-taipei.pmtiles', BBOX)
    print('truth', len(truth), flush=True)
    if os.path.exists('wsf3d_yonghe.parquet'):
        wsf = gpd.read_parquet('wsf3d_yonghe.parquet')
    else:
        wsf = load_wsf3d(BBOX)
        wsf.to_parquet('wsf3d_yonghe.parquet')
    print('wsf', len(wsf), flush=True)
    layers = {
        'Overture': gpd.read_parquet('overture_yonghe.parquet'),
        'OSM': gpd.read_parquet('osm_yonghe.parquet'),
        'WSF3D': wsf,
    }
    rows = []
    for label, chal in layers.items():
        print('computing', label, len(chal))
        rows.append(metrics(truth, chal, label))
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    df.to_csv('yonghe_metrics.csv', index=False)
