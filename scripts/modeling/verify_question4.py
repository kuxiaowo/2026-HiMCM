"""Recalculate Q4 saved solutions from arrays and fixed source data."""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question4'


def main():
    results=json.loads((OUT/'q4_results.json').read_text(encoding='utf-8'))
    saved=json.loads((OUT/'q4_solutions.json').read_text(encoding='utf-8'))
    data=json.loads((ROOT/'output/question2/q2_model_inputs.json').read_text(encoding='utf-8'))
    ts=data['targets'];n=len(ts)
    w=np.array([t['objective_weight'] for t in ts])
    r=np.array([float(t['response_eligible']) for t in ts])
    F=np.array([t['planned_checks_month'] for t in ts])
    a=np.array([t['ground_hours_per_check'] or 1 for t in ts])
    b=np.array([t['flight_hours_per_check'] or 1 for t in ts])
    g=np.array([t['operator_hours_per_check']/t['flight_hours_per_check'] if t['drone_allowed'] else 0 for t in ts])
    regions=json.loads((ROOT/'output/regions/region_base_data.json').read_text(encoding='utf-8'))['regional_rows']
    by_region={v['region_id']:v for v in regions}
    fuel=np.array([t['support_area_km2']*by_region[t['region_id']]['fuel_proxy_baseline_area_wc2021_km2']/by_region[t['region_id']]['geometry_area_km2'] for t in ts])
    cases={v['case_id']:v for v in results['resource_sensitivity']+results['technology_sensitivity']+results['single_parameter_sensitivity']+results['joint_peak_scenarios']}
    for p in results['policy_comparisons']:
        for policy in ['adaptive','retained']:cases[p[policy]['case_id']]=p[policy]
    checks=[];lookup={v['case_id']:v for v in saved}
    for record in saved:
        sol=record['result'];per=record['period']
        if not sol['success']:
            assert sol.get('status')==2
            continue
        x,h,s,xf,hf=(np.array(sol[k]) for k in ['x_base','h_base','s','x_fire','h_fire'])
        assert all(len(z)==n for z in [x,h,s,xf,hf])
        assert min(np.r_[x,h,s,xf,hf])>=-1e-8
        E=per['extra_fire_rate']*fuel/100*r
        assert np.max(np.abs(E-np.array(per['fire_checks'])))<1e-7
        assert np.min(x/a+h/b-F*s)>=-1e-6
        assert np.min(xf/a+hf/b-E)>=-1e-6
        assert np.max(s-r)<=1e-8
        assert all(abs(h[j])+abs(hf[j])<1e-7 for j,t in enumerate(ts) if not t['drone_allowed'])
        assert all(abs(x[j])+abs(xf[j])<1e-7 for j,t in enumerate(ts) if not t['response_eligible'])
        for rid in data['region_ids']:
            ids=[j for j,t in enumerate(ts) if t['region_id']==rid]
            mu=np.array([ts[j]['within_region_area_share'] for j in ids])
            assert mu@s[ids]>=data['config']['minimum_reachable_service']*(mu@r[ids])-1e-7
        water=sum(v['visits_month']*v['person_hours_visit'] for v in per['water_rows'])
        assert abs(water-per['water_hours'])<1e-7
        labor=x.sum()+xf.sum()+g@(h+hf)+water+data['response_reserved_hours']
        assert abs(labor-sol['total_person_hours'])<1e-6
        assert abs(100*w@s-sol['score'])<1e-7
        assert (h+hf).sum()<=sol['drone_budget']+1e-6
        if sol['staff_budget'] is not None:assert labor<=120*sol['staff_budget']+1e-6
        assert sol['required_staff']*120>=labor-1e-6
        case=cases.get(record['case_id'])
        if case and case['mode']=='inverse':assert sol['score']>=results['target_score']-1e-6
        checks.append(record['case_id'])
    for p in results['policy_comparisons']:
        if not p['retained']['success']:continue
        scope='profile_reference_q2' if p['scenario']=='q2_scarce' else 'profile_reference_peak'
        profile=np.array(lookup[scope]['result']['s'])
        retained=np.array(lookup[p['retained']['case_id']]['result']['s'])
        ratios=retained[w>0]/profile[w>0].clip(1e-100)
        active=(w>0)&(profile>0)
        scale=float(np.median(retained[active]/profile[active]))
        assert np.max(np.abs(retained[active]-scale*profile[active]))<1e-7
        assert np.max(np.abs(retained[w==0]-profile[w==0]))<1e-7
        assert p['adaptive']['score']>=p['retained']['score']-1e-6
    for item in results['water_schedule_comparison']:
        hours=np.zeros(30);gaps=[]
        for point in item['points']:
            days=np.array(point['visit_days'])-1
            assert len(days)==4 and len(set(days))==4
            hours[days]+=point['person_hours_visit']
            gaps.append(float(np.diff(np.r_[days,days[0]+30]).max()))
        assert np.max(np.abs(hours-np.array(item['daily_water_hours'])))<1e-7
        assert abs(hours.sum()-item['total_water_hours'])<1e-7
        assert max(gaps)==item['maximum_visit_gap_days']
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==s for p,s in results['source_sha256'].items())
    audit={'passed':True,'independently_checked_feasible_solutions':len(checks),
           'saved_cases':len(saved),'source_fingerprints_unchanged':True,
           'policy_profiles_checked':True,'water_dates_and_workload_checked':True,
           'scope':'numerical consistency and model feasibility; not external ecological or roster validation'}
    (OUT/'q4_independent_verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=True))


if __name__=='__main__':main()
