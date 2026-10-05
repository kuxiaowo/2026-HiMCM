"""Independent audit of saved allocations, physical budgets and geographic gates."""
import json, math, re
from pathlib import Path
import numpy as np
from build_question2 import solve

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question2'

def audit(data,result, ground_factor=1., operator_factor=1.):
    if not result['success']:return
    ts=data['targets'];x=np.asarray(result['x']);h=np.asarray(result['h']);s=np.asarray(result['s'])
    checks=np.array([t['planned_checks_month'] for t in ts]);g=np.array([t['ground_hours_per_check'] or 1 for t in ts])*ground_factor
    u=np.array([t['flight_hours_per_check'] or 1 for t in ts]);op=np.array([t['operator_hours_per_check']/t['flight_hours_per_check'] if t['drone_allowed'] else 0 for t in ts])*operator_factor
    assert np.min(x)>-1e-7 and np.min(h)>-1e-7 and np.min(s)>-1e-7 and np.max(s)<=1+1e-7
    assert np.all(checks*s<=x/g+h/u+1e-6)
    for j,t in enumerate(ts):
        if not t['response_eligible']:assert abs(s[j])+abs(x[j])+abs(h[j])<1e-6
        if not t['drone_allowed']:assert abs(h[j])<1e-6
        if t['drone_allowed']:assert t['flight_hours_per_check']<=data['config']['safe_flight_hours']+1e-7
    human=float(x.sum()+op@h+result['response_reserved_hours'])
    assert human<=result['human_budget']+1e-5 and h.sum()<=result['drone_budget']+1e-6
    assert abs(human-result['total_person_hours'])<1e-5
    for rid in data['region_ids']:
        ii=[j for j,t in enumerate(ts) if t['region_id']==rid]
        mu=np.array([ts[j]['within_region_area_share'] for j in ii]);r=np.array([ts[j]['response_eligible'] for j in ii],dtype=float)
        assert abs(mu.sum()-1)<1e-7
        assert mu@s[ii]>=data['config']['minimum_reachable_service']*(mu@r)-1e-6

def main():
    data=json.loads((OUT/'q2_model_inputs.json').read_text(encoding='utf-8'));report=json.loads((OUT/'q2_results.json').read_text(encoding='utf-8'))
    audit(data,report['optimum'])
    for key in ['comparisons','scarce_budget_comparisons']:
        for item in report[key]:audit(data,item['result'])
    for item in report['scenarios']:
        if item.get('fixed_baseline_demand_weights'):continue
        multiplier=1.25 if item['name']=='出行及作业人时增加25%' else 1.
        audit(data,item['result'],multiplier,multiplier)
    rows=report['regions'];opt=report['optimum']
    assert abs(sum(r['allocated_monitoring_person_hours'] for r in rows)+opt['response_reserved_hours']-opt['total_person_hours'])<1e-6
    assert abs(sum(r['drone_flight_hours'] for r in rows)-opt['drone_flight_hours'])<1e-6
    assert all(r['animal_value_2015'] is None for r in rows if r['region_id'] in data['animal_unknown_regions'])
    assert solve(data,H=data['response_reserved_hours']-1)['success'] is False
    estimated=report['management_weight_estimation'];matrix=np.asarray(estimated['raw_region_matrix']);p=matrix/matrix.sum(axis=0)
    entropy=-(p*np.log(np.maximum(p,1e-300))).sum(axis=0)/np.log(len(matrix));weights=(1-entropy)/(1-entropy).sum()
    assert len(matrix)==15 and np.allclose(weights,estimated['weights'],rtol=0,atol=1e-12)
    assert report['excluded_factors']==['water_supply','precipitation']
    output={'status':'passed','targets':len(data['targets']),'audited':['independent per-target service capacity','no service credited without response','no prohibited drone allocation','flight endurance','total person and flight budgets','regional service floors','regional totals reconcile','unknown animal values remain null','below-response-budget infeasible','15-region entropy weights independently recalculated','water supply and precipitation excluded from current scope'],'not_verified':['actual incident loss reduction','real patrol access permissions and working speeds','full staffing/flight schedule','current unknown priority species and habitats']}
    (OUT/'q2_verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
