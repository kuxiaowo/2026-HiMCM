"""Independent graph/knapsack checks for the small Q6 LP prototypes."""
from pathlib import Path
import json, math, hashlib
import numpy as np
from build_question6 import solve

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question6'

def independent_route(park, stress):
    nodes=sorted(set(z for e in park['edges'] for z in e[:2])); n=len(nodes); ix={s:i for i,s in enumerate(nodes)}
    dist=np.full((n,n),np.inf); np.fill_diagonal(dist,0)
    for u,v,km,normal,bad in park['edges']:
        speed=bad if stress else normal
        if speed>0:dist[ix[u],ix[v]]=dist[ix[v],ix[u]]=km/speed
    # Floyd-Warshall is independent of build_question6's NetworkX Dijkstra.
    for k in range(n):dist=np.minimum(dist,dist[:,k,None]+dist[k,None,:])
    return ix,dist

def independent_knapsack(data, budget=None, target=None):
    p=data['config']; fixed=data['response_reserved_hours']+data['extra_ground_hours']; value=0.; cost=fixed; chunks=[]
    # There is only one candidate drone target, and its 16-h budget exceeds
    # all 24 checks x .3 h. No coupled fractional-technology allocation remains.
    for t in data['targets']:
        if not t['reachable']:continue
        unit=t['ground_hours_per_check']
        if t['drone_allowed']:
            assert data['drone_budget']>=t['checks']*t['flight_hours_per_check']-1e-10
            unit=min(unit,t['drone_operator_hours_per_check'])
        k=t['checks']*unit
        value+=100*t['weight']*p['service_floor'];cost+=k*p['service_floor']
        chunks.append((100*t['weight']/k,100*t['weight']*(1-p['service_floor']),k*(1-p['service_floor'])))
    if target is not None and target>data['geographic_cap']+1e-8:return None
    if budget is not None and cost>budget+1e-8:return None
    for _,dv,dc in sorted(chunks,reverse=True):
        if target is not None:f=min(1,max(0,(target-value)/dv))
        else:f=min(1,max(0,(budget-cost)/dc))
        cost+=f*dc;value+=f*dv
    return value,cost

def main():
    inputs=json.loads((ROOT/'data/modeling/q6_assumptions.json').read_text(encoding='utf-8'))
    results=json.loads((OUT/'q6_results.json').read_text(encoding='utf-8'))
    assert results['input_sha256']==hashlib.sha256((ROOT/'data/modeling/q6_assumptions.json').read_bytes()).hexdigest()
    parks={p['park']:p for p in inputs['parks']};checks=[]; differences=[]
    for case in results['cases']:
        d=case['data']; p=d['config']; ix,dist=independent_route(parks[d['park']],d['stress'])
        assert abs(sum(t['weight'] for t in d['targets'])-1)<1e-12
        for t in d['targets']:
            rt=min(dist[ix[b],ix[t['id']]] for b in d['bases']);walk=t['walk_km']/t['walk_speed']
            assert abs(rt-t['road_hours'])<1e-10
            assert abs(t['response_hours']-(rt+walk+p['dispatch_hours']))<1e-10
            assert abs(t['ground_hours_per_check']-2*(2*rt+2*walk+t['observation']+p['preparation_hours']))<1e-10
        for mode,res in [('fixed_budget_result',case['fixed_budget_result']),('target_result',case['target_result'])]:
            expected=independent_knapsack(d,budget=p['fixed_staff']*120 if mode=='fixed_budget_result' else None,
              target=p['target_score'] if mode=='target_result' else None)
            assert res['success']==(expected is not None),(case['id'],mode)
            if not res['success']:continue
            assert abs(expected[0]-res['score'])<1e-7
            assert abs(expected[1]-res['total_person_hours'])<1e-7
            differences.append(abs(expected[1]-res['total_person_hours']))
            x=np.array(res['x']);h=np.array(res['h']);s=np.array(res['s'])
            for j,t in enumerate(d['targets']):
                assert x[j]/t['ground_hours_per_check']+h[j]/t['flight_hours_per_check']+1e-8>=t['checks']*s[j]
                assert s[j]<=int(t['reachable'])+1e-8
                if not t['drone_allowed']:assert abs(h[j])<1e-10
            assert h.sum()<=d['drone_budget']+1e-8
            assert res['staff_integer']*120+1e-8>=res['total_person_hours']
            assert (res['staff_integer']-1)*120<res['total_person_hours']-1e-8
        # A large workforce cannot remove a response cap, and extra bases
        # must be charged their full 480-person-hour reserve.
        if d['geographic_cap']<p['target_score']:
            assert not solve(d,target=p['target_score'],budget=100000)['success']
        if d['forward']:assert d['response_reserved_hours']==1440
        for hbudget in [1440.,1800.,2400.]:
            r=solve(d,budget=hbudget)
            if r['success']:assert r['score']<=d['geographic_cap']+1e-7
        checks.append(dict(case=case['id'],routing='Floyd-Warshall verified',objective='independent fractional knapsack verified',constraints='passed'))
    c0,c1=results['cases'][:2]
    assert abs(c0['target_result']['total_person_hours']-c1['target_result']['total_person_hours']-21.6)<1e-8
    report=dict(status='passed',case_count=len(checks),case_checks=checks,
      max_independent_objective_difference_hours=max(differences),scope='numerical and structural verification; not local calibration or ecological validation',
      result_sha256=hashlib.sha256((OUT/'q6_results.json').read_bytes()).hexdigest())
    (OUT/'q6_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('All 7 cases: independent routing, objectives, constraints and staffing rounding passed.')

if __name__=='__main__':
    raise SystemExit('Historical synthetic prototype retired; use question6_real scripts. Original retained in output/question6/archive/synthetic_20261006/scripts.')
    main()
