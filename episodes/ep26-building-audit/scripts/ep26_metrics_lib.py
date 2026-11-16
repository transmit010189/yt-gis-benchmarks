import geopandas as gpd
import pandas as pd
from shapely import STRtree
from shapely.geometry import box


def metrics(truth, chal, label, match_m=12.0):
    t = truth.to_crs(3826)
    c = chal.to_crs(3826)
    tp = gpd.GeoDataFrame({'tid': range(len(t)), 'geometry': t.geometry.centroid}, crs=3826)
    cp = gpd.GeoDataFrame({'cid': range(len(c)), 'geometry': c.geometry.centroid}, crs=3826)

    # gross: how many official buildings fall inside any challenger polygon
    j = gpd.sjoin(tp, c[['geometry']], predicate='within', how='left')
    gross_matched = int(j['index_right'].notna().sum())
    per_chal = j[j['index_right'].notna()].groupby('index_right').size()
    swallow_max = int(per_chal.max()) if len(per_chal) else 0
    real_chal = int(len(per_chal))
    ghost = len(c) - real_chal

    # one-to-one: each challenger centroid may claim at most one official building within match_m
    tree = STRtree(list(tp.geometry))
    pairs = []
    for i, pt in enumerate(cp.geometry):
        idx = tree.nearest(pt)
        d = pt.distance(tp.geometry.iloc[idx])
        if d <= match_m:
            pairs.append((i, int(idx), float(d)))
    uniq_truth = len({p[1] for p in pairs})
    shifts = [p[2] for p in pairs]

    return {
        'layer': label,
        'features': len(c),
        'count_ratio_pct': round(100 * len(c) / len(t), 2),
        'area_ratio_pct': round(100 * c.area.sum() / t.area.sum(), 2),
        'gross_truth_inside_pct': round(100 * gross_matched / len(t), 2),
        'one2one_matched': len(pairs),
        'one2one_coverage_pct': round(100 * uniq_truth / len(t), 2),
        'one2one_precision_pct': round(100 * len(pairs) / len(c), 2) if len(c) else None,
        'ghost_features': int(ghost),
        'ghost_pct': round(100 * ghost / len(c), 2) if len(c) else None,
        'swallow_max': swallow_max,
        'shift_median_m': round(float(pd.Series(shifts).median()), 2) if shifts else None,
        'area_sum_m2': round(float(c.area.sum()), 1),
    }
