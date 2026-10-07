"""Reproducible revision checks and a historical Yellowstone priority scenario.

Reads saved real inputs. All technology parameters and priority shares below
are declared scenarios; no ecological effect or current population is fitted.
"""
from __future__ import annotations

import hashlib
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy.optimize import linprog
from shapely.geometry import box, shape
from shapely.ops import transform, unary_union

import build_question2 as q2
import build_question3 as q3
from revise_full_paper_presentation import weight_checks
from verify_question2 import audit

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/revision_feasibility/20261006'


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def yellowstone_priority_scenario():
    path = 'output/revision_feasibility/20261006/yellowstone_wolf_2022_territories.geojson'
    features = read(path)['features']
    fwd = Transformer.from_crs(4326, 32612, always_xy=True).transform
    park = transform(fwd, shape(read('data/question6/processed/yellowstone_boundary.geojson')['features'][0]['geometry']))
    polygons = [transform(fwd, shape(f['geometry'])) for f in features]
    assert len(polygons) == 10 and all(g.is_valid for g in polygons)
    # Union prevents double counting overlapping or duplicate historical MCPs.
    use = unary_union(polygons).intersection(park)
    original = next(c for c in read('output/question6/q6_results.json')['cases'] if c['id'] == 'Y0')
    targets = original['targets']
    size = read('output/question6/q6_results.json')['parks']['yellowstone']['grid_m']
    areas = []
    for t in targets:
        x, y = math.floor(t['x'] / size) * size, math.floor(t['y'] / size) * size
        piece = park.intersection(box(x, y, x + size, y + size))
        assert abs(piece.area / 1e6 - t['area_km2']) < 1e-6, t['id']
        land_fraction = t['land_area_km2'] / t['area_km2']
        areas.append(piece.intersection(use).area / 1e6 * land_fraction)
    wolf = np.array(areas)
    assert wolf.sum() > 0
    wolf /= wolf.sum()
    land = np.array([t['weight'] for t in targets])
    eligibility = np.array([float(t['eligible']) for t in targets])
    costs = np.array([t['checks'] * t['cost'] if t['eligible'] else 0 for t in targets])
    reference_s = np.array(original['solution']['s'])
    bounds = [(.15, 1) if t['eligible'] else (0, 0) for t in targets]
    rows = []
    for alpha in [0., .25, .5, .75]:
        weights = alpha * wolf + (1 - alpha) * land
        # Preserve the existing plan's service under the NEW priority rule.
        # Also report original land-weight evaluation, so a changed metric is
        # never presented as a comparable ecological improvement.
        target = float(100 * weights @ reference_s)
        res = linprog(costs, A_ub=[-100 * weights], b_ub=[-target], bounds=bounds,
                      method='highs', options={'primal_feasibility_tolerance': 1e-9})
        assert res.success
        score = float(100 * weights @ res.x)
        human = float(costs @ res.x + original['solution']['reserved_hours'])
        assert score >= target - 1e-7
        assert np.min(res.x) >= -1e-8 and np.max(res.x - eligibility) <= 1e-8
        assert all(res.x[j] >= .15 - 1e-8 for j, t in enumerate(targets) if t['eligible'])
        assert human <= original['solution']['total_person_hours'] + 1e-6
        if alpha == 0:
            assert abs(human - original['solution']['total_person_hours']) < 1e-5
        rows.append({'historical_wolf_share': alpha, 'target_under_new_weights': target,
                     'score_own_weights': score, 'score_original_land_weights': float(100 * land @ res.x),
                     'geographic_cap_own_weights': float(100 * weights @ eligibility),
                     'total_person_hours': human, 'conditional_staff_equivalent': human / 120,
                     'changed_service_units': int(np.count_nonzero(abs(res.x - reference_s) > 1e-6)),
                     's': res.x.tolist(), 'checks_passed': True})
    result = {'scope': 'historical 2022 wolf-use priority scenario, not current density or poaching risk',
              'source': path, 'input_feature_count': 10,
              'unique_projected_geometries': len({g.wkb for g in polygons}),
              'clipped_union_area_km2': use.area / 1e6,
              'land_adjusted_intersection_area_km2': float(sum(areas)),
              'cell_land_adjustment': 'historical overlap multiplied by the existing cell land fraction',
              'target_rule': 'retain Y0 reference service evaluated under each changed priority rule',
              'held_fixed': ['roads', 'response eligibility', 'task frequency', 'costs', 'readiness', 'service floors', 'no drones'],
              'cases': rows,
              'limitations': ['MCPs describe historical activity extent, not animal density',
                             'land fraction is a within-cell approximation',
                             'shares are team scenario choices, not official priorities',
                             'retaining a rate under new weights permits trade-offs in land-weighted service',
                             'public seasonal road rules do not establish staff emergency permissions']}
    q2.dump(OUT / 'yellowstone_historical_priority_scenario.json', result)
    return {k: v for k, v in result.items() if k != 'cases'} | {'cases': [{k: v for k, v in c.items() if k != 's'} for c in rows]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = read('output/question2/q2_model_inputs.json')
    report = read('output/question2/q2_results.json')
    optimum = report['optimum']
    data3 = q3.inputs()
    empty = q3.period(data3, 1)
    empty['water_hours'] = 0.
    empty['water_rows'] = []
    independent = q3.solve(data3, empty)
    assert independent['success']
    assert abs(independent['total_person_hours'] - optimum['total_person_hours']) < 1e-5
    assert abs(independent['score'] - optimum['score']) < 1e-7
    with zipfile.ZipFile(ROOT / 'output/full_paper/history/before_multispecies_revision_20261006.zip') as z:
        old = json.loads(z.read('output/question2/q2_results.json'))['optimum']
    old_pattern = q2.solve(data, fixed_service=old['s'], minimum_person=True)
    assert abs(old_pattern['total_person_hours'] - old['total_person_hours']) < 1e-5
    assert optimum['total_person_hours'] <= old_pattern['total_person_hours'] + 1e-7
    technologies = []
    for item in report['scenarios']:
        if 'drone_efficiency' in item or 'minimum_ground_share' in item:
            audit(data, item['result'])
            technologies.append({'name': item['name'], 'status': item['status'],
                                 **{k: item['result'][k] for k in ['score', 'total_person_hours', 'ground_hours', 'drone_flight_hours', 'drone_efficiency', 'minimum_ground_share']}})
    pressure = dict(data, human_budget=3600.)
    comparisons = [{'name': name, 'result': q2.heuristic(pressure, kind)}
                   for name, kind in [('Uniform', 'area'), ('Demand-based', 'demand')]]
    comparisons.append({'name': 'Optimized', 'result': q2.solve(pressure)})
    for item in comparisons:
        assert item['result']['success']
        audit(pressure, item['result'])
    assert comparisons[-1]['result']['score'] >= max(i['result']['score'] for i in comparisons) - 1e-6
    weight_rows = weight_checks(data, report)
    wolf = yellowstone_priority_scenario()
    inputs = ['output/question2/q2_results.json', 'output/question2/q2_model_inputs.json',
              'output/question3/q3_results.json', 'output/question4/q4_results.json',
              'output/question6/q6_results.json', 'output/full_paper/weight_sensitivity_supplement.json',
              'output/revision_feasibility/20261006/data_conflict_audit.json',
              'output/revision_feasibility/20261006/yellowstone_wolf_2022_territories.geojson',
              'data/question6/processed/yellowstone_boundary.geojson']
    payload = {'generated_at': datetime.now(timezone.utc).isoformat(), 'status': 'computed_and_independently_checked',
               'two_stage': {'old_fixed_pattern_person_hours': old['total_person_hours'],
                             'new_global_person_hours': optimum['total_person_hours'],
                             'independent_Q3_inverse_person_hours': independent['total_person_hours'],
                             'hours_saved': old['total_person_hours'] - optimum['total_person_hours'],
                             'score_unchanged': abs(old['score'] - optimum['score']) < 1e-7,
                             'human_saving_percent': 100 * (old['total_person_hours'] - optimum['total_person_hours']) / old['total_person_hours']},
               'technology_scenarios': technologies,
               'pressure_comparisons': [{'name': i['name'], **{k: i['result'][k] for k in ['score', 'total_person_hours', 'drone_flight_hours']}} for i in comparisons],
               'grid_sensitivity': [{'grid_km': data['config']['grid_km'], 'target_count': len(data['targets']), 'score': optimum['score'], 'total_person_hours': optimum['total_person_hours']}] +
                                   [{k: c[k] for k in ['grid_km', 'target_count']} | {k: c['result'][k] for k in ['score', 'total_person_hours']} for c in report['grid_sensitivity']],
               'weight_scenario_count': len(weight_rows), 'yellowstone': wolf,
               'input_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in inputs}}
    q2.dump(OUT / 'revision_results.json', payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
