"""Q6 adaptation prototypes: sourced mechanisms, explicitly synthetic networks.

No route, weight, staff count or monitoring rate here is a measured park value.
The exercise verifies adaptation of Q2/Q3, not either park's actual staffing.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import json, hashlib, csv, math
import networkx as nx
import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'output/question6'
INPUT = ROOT/'data/modeling/q6_assumptions.json'

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def defaults():
    # Each edge stores length, normal speed and stressed speed, all assumed.
    c = dict(park='chitwan', park_label='奇特旺', bases=['A','B'],
      targets=[dict(id='J1', label='林地重点对象', weight=.30, checks=24., walk_km=.5, walk_speed=3., observation=.25, drone=False),
               dict(id='J2', label='开阔草地对象', weight=.30, checks=24., walk_km=1., walk_speed=4., observation=.25, drone=True),
               dict(id='J3', label='社区边界核查', weight=.25, checks=20., walk_km=0., walk_speed=4., observation=.25, drone=False),
               dict(id='J4', label='河岸湿地核查', weight=.15, checks=12., walk_km=.4, walk_speed=3., observation=.25, drone=False)],
      edges=[['A','J1',12,20,10],['B','J1',20,20,10],['A','J2',20,25,10],['B','J2',12,25,12.5],
             ['A','J3',5,20,10],['B','J4',18,15,0],['J2','J4',25,20,7.142857142857143],['A','B',35,25,12.5]],
      ground_extra_normal=48., ground_extra_stress=72.)
    y = dict(park='yellowstone', park_label='黄石', bases=['A','B'],
      targets=[dict(id='J1', label='道路动物交互', weight=.35, checks=30., walk_km=0., walk_speed=4., observation=.25, drone=False),
               dict(id='J2', label='开阔谷地监测', weight=.25, checks=24., walk_km=.3, walk_speed=4., observation=.25, drone=False),
               dict(id='J3', label='游览节点核查', weight=.25, checks=16., walk_km=0., walk_speed=4., observation=.5, drone=False),
               dict(id='J4', label='偏远生境核查', weight=.15, checks=10., walk_km=1.2, walk_speed=3., observation=.5, drone=False)],
      edges=[['A','J1',24,40,30],['B','J1',30,40,12],['B','J2',28,35,12],['A','J3',8,30,20],
             ['B','J4',30,30,8],['J2','J4',10,15,10],['A','B',60,40,20]],
      ground_extra_normal=72., ground_extra_stress=72.)
    return dict(status='explicit_team_scenario_assumptions_not_local_calibration',
      scope='four task prototypes per park; no real park partition or GIS routing; no whole-park staff estimate',
      evidence_date='2026-10-06',
      common=dict(effective_hours_month=120., fixed_staff=11, response_limit_hours=2., dispatch_hours=1/6,
        preparation_hours=1/12, team_size=2., response_staff_per_site=2., hours_day=8., days_month=30.,
        service_floor=.15, target_score=95., conditional_drone_hours=16., drone_speed_kmh=40., drone_safe_flight_hours=.6),
      inherited_constants='120 effective hours, 2-person teams, 2-hour response and 15% floor are demonstration assumptions; none is a local official standard',
      source_support='primary sources support objects, habitats, season mechanisms and permissions ONLY; all numeric network edges, task weights, checks, speeds, extra work and budgets are synthetic',
      parks=[c,y])

def prepare(park, config, stress=False, forward=False, conditional_drone=False):
    graph=nx.Graph()
    for u,v,d,normal,stressed in park['edges']:
        speed=stressed if stress else normal
        if speed>0: graph.add_edge(u,v,weight=d/speed,km=d,speed=speed)
    bases=park['bases'] + (['J4'] if park['park']=='chitwan' else ['J2']) if forward else list(park['bases'])
    distances={b:nx.single_source_dijkstra_path_length(graph,b,weight='weight') for b in bases}
    targets=[]
    for target in park['targets']:
        t=deepcopy(target)
        road=min(distances[b].get(t['id'],math.inf) for b in bases)
        base=min(bases,key=lambda b:distances[b].get(t['id'],math.inf))
        walk=t['walk_km']/t['walk_speed']
        response=config['dispatch_hours']+road+walk
        flight=2*t['walk_km']/config['drone_speed_kmh']+t['observation']
        t.update(road_hours=road, nearest_base=base, response_hours=response,
          reachable=response<=config['response_limit_hours'],
          ground_hours_per_check=config['team_size']*(2*road+2*walk+t['observation']+config['preparation_hours']),
          flight_hours_per_check=flight,
          drone_operator_hours_per_check=config['team_size']*(2*road+config['preparation_hours']+flight),
          drone_allowed=bool(conditional_drone and t['drone'] and response<=config['response_limit_hours'] and flight<=config['drone_safe_flight_hours']))
        targets.append(t)
    reserved=len(bases)*config['response_staff_per_site']*config['hours_day']*config['days_month']
    return dict(park=park['park'],park_label=park['park_label'],stress=stress,forward=forward,bases=bases,
      targets=targets,config=config,response_reserved_hours=reserved,
      extra_ground_hours=park['ground_extra_stress' if stress else 'ground_extra_normal'],
      drone_budget=config['conditional_drone_hours'] if conditional_drone else 0.,
      drone_permission='conditional_written_authorisation_and_equivalent_task_protocol' if conditional_drone else 'not_assumed_available',
      geographic_cap=100*sum(t['weight'] for t in targets if t['reachable']))

def solve(data, target=None, budget=None):
    ts=data['targets']; n=len(ts); p=data['config']; rows=[]; rhs=[]
    a=np.array([t['ground_hours_per_check'] for t in ts]); b=np.array([t['flight_hours_per_check'] for t in ts])
    gamma=np.array([t['drone_operator_hours_per_check']/t['flight_hours_per_check'] for t in ts])
    w=np.array([t['weight'] for t in ts]); C=np.array([t['checks'] for t in ts])
    fixed=data['response_reserved_hours']+data['extra_ground_hours']
    for j in range(n):
        row=np.zeros(3*n); row[j]=-1/a[j]; row[n+j]=-1/b[j]; row[2*n+j]=C[j]; rows.append(row);rhs.append(0.)
    human=np.r_[np.ones(n),gamma,np.zeros(n)]
    if budget is not None:rows.append(human);rhs.append(budget-fixed)
    rows.append(np.r_[np.zeros(n),np.ones(n),np.zeros(n)]);rhs.append(data['drone_budget'])
    if target is not None:rows.append(np.r_[np.zeros(2*n),-100*w]);rhs.append(-target)
    bounds=[(0,None) if t['reachable'] else (0,0) for t in ts]
    bounds += [(0,None) if t['drone_allowed'] else (0,0) for t in ts]
    bounds += [(p['service_floor'],1) if t['reachable'] else (0,0) for t in ts]
    objective=human if target is not None else np.r_[np.zeros(2*n),-100*w]
    res=linprog(objective,A_ub=np.array(rows),b_ub=np.array(rhs),bounds=bounds,method='highs')
    if not res.success:
        reason='geographic_limit' if target is not None and target>data['geographic_cap']+1e-8 else 'fixed_work_exceeds_budget' if budget is not None and fixed>budget else 'resource_or_service_constraint'
        return dict(success=False,reason=reason,solver_status=int(res.status),message=res.message)
    if target is None:
        # Minimum-human representative among solutions with the same best score.
        best=100*w@res.x[2*n:]
        return solve(data,target=best,budget=budget)
    x=res.x[:n]; h=res.x[n:2*n]; s=res.x[2*n:]
    total=fixed+x.sum()+gamma@h
    return dict(success=True,score=float(100*w@s),total_person_hours=float(total),
      ground_hours=float(x.sum()),operator_hours=float(gamma@h),drone_hours=float(h.sum()),
      reserved_hours=fixed-data['extra_ground_hours'],extra_ground_hours=data['extra_ground_hours'],
      staff_equivalent=float(total/p['effective_hours_month']),staff_integer=math.ceil((total-1e-8)/p['effective_hours_month']),
      x=x.tolist(),h=h.tolist(),s=s.tolist(),max_residual=float(max(0,np.max(np.array(rows)@res.x-np.array(rhs)))))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if not INPUT.exists():dump(INPUT,defaults())
    params=json.loads(INPUT.read_text(encoding='utf-8'));p=params['common']; cases=[]
    definitions=[('C0','非季风、地面','chitwan',False,False,False),
                 ('C1','条件授权无人机','chitwan',False,False,True),
                 ('C2','季风通行压力','chitwan',True,False,False),
                 ('C3','季风＋前置驻点','chitwan',True,True,False),
                 ('Y0','常规道路','yellowstone',False,False,False),
                 ('Y1','冬季通行压力','yellowstone',True,False,False),
                 ('Y2','冬季＋前置驻点','yellowstone',True,True,False)]
    parks={z['park']:z for z in params['parks']}
    for code,label,park,stress,forward,drone in definitions:
        data=prepare(parks[park],p,stress,forward,drone)
        cases.append(dict(id=code,label=label,data=data,
          fixed_budget_result=solve(data,budget=p['fixed_staff']*p['effective_hours_month']),
          target_result=solve(data,target=p['target_score'])))
    result=dict(created_at=datetime.now(timezone.utc).isoformat(),evidence_date=params['evidence_date'],
      status='computed_conditional_adaptation_prototypes_not_field_validated',cases=cases,
      input_sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(),
      warning='95 is an illustrative service target; scores across parks are not ecological comparisons; forward cases add one 480-person-hour response station')
    dump(OUT/'q6_results.json',result)
    rows=[]
    for case in cases:
        d=case['data'];f=case['fixed_budget_result']; t=case['target_result']
        rows.append(dict(case=case['id'],park=d['park'],scenario=case['label'],geo_cap=d['geographic_cap'],
          fixed_staff=p['fixed_staff'],fixed_score=f.get('score'),fixed_feasible=f['success'],
          target=p['target_score'],target_feasible=t['success'],target_hours=t.get('total_person_hours'),
          target_staff=t.get('staff_integer'),target_drone_hours=t.get('drone_hours'),
          reason=t.get('reason',''),response_reserved_hours=d['response_reserved_hours']))
    with (OUT/'q6_summary.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    for row in rows:print(row)

if __name__=='__main__':
    raise SystemExit('Historical synthetic prototype retired; use question6_real scripts. Original retained in output/question6/archive/synthetic_20261006/scripts.')
    main()
