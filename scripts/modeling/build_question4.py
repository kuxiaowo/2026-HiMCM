"""Focused Q4 calculations; Q2/Q3 inputs and outputs remain unchanged.

Uses the existing Q3 forward/inverse LP. Schedule comparisons concern the
historical borehole sample, not a full ranger roster or observed operations.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from build_question2 import dump, csvout
from build_question3 import inputs, period, solve, verify_result, regional

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/question4'


def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def no_extra(data):
    per = period(data, 1)
    per.update(water_hours=0., water_rows=[], fire_checks=[0.]*len(data['targets']),
               extra_fire_rate=0, unreachable_fire_checks=0., fire_full_area_planned_checks=0.)
    return per


def schedule_comparison(per):
    """Same four visits and costs; integer dates in a repeating 30-day cycle."""
    assert per['water_visits_month'] == 4
    daily = np.zeros(30)
    dispersed = []
    # Greedy phase staggering minimises peak water-only daily workload.
    for row in sorted(per['water_rows'], key=lambda v: -v['person_hours_visit']):
        options = []
        for phase in range(30):
            days = (phase + np.array([0, 7, 15, 22])) % 30
            trial = daily.copy()
            trial[days] += row['person_hours_visit']
            options.append((trial.max(), float(trial@trial), phase, days, trial))
        _, _, phase, days, daily = min(options, key=lambda v: v[:3])
        dispersed.append({'name':row['name'], 'person_hours_visit':row['person_hours_visit'],
                          'visit_days':sorted((days+1).tolist())})
    clustered = [{'name':r['name'], 'person_hours_visit':r['person_hours_visit'],
                  'visit_days':[1,2,3,4]} for r in per['water_rows']]
    outputs = []
    for name, rows in [('dispersed',dispersed),('clustered',clustered)]:
        hours = np.zeros(30)
        gaps = []
        for row in rows:
            days = np.array(row['visit_days'])-1
            hours[days] += row['person_hours_visit']
            gaps.append(float(np.diff(np.r_[days, days[0]+30]).max()))
        outputs.append({'arrangement':name, 'total_visits':sum(len(r['visit_days']) for r in rows),
                        'total_water_hours':float(hours.sum()),
                        'maximum_visit_gap_days':max(gaps), 'peak_daily_water_hours':float(hours.max()),
                        'peak_water_crew_lower_bound':math.ceil((hours.max()-1e-8)/16),
                        'daily_water_hours':hours.tolist(), 'points':rows,
                        'interpretation':'constructed water-only dates, 8h/day and 2 people/crew; crew bound is necessary, not a feasible roster'})
    assert all(abs(v['total_water_hours']-per['water_hours'])<1e-7 for v in outputs)
    assert outputs[0]['total_visits']==outputs[1]['total_visits']==68
    assert outputs[0]['maximum_visit_gap_days']==8 and outputs[1]['maximum_visit_gap_days']==27
    return outputs


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = ['output/question2/q2_results.json','output/question2/q2_model_inputs.json',
               'output/question3/q3_results.json','data/modeling/q3_assumptions.json',
               'data/question3/processed/water_points.json',
               'scripts/modeling/build_question2.py','scripts/modeling/build_question3.py']
    before = {p:sha(p) for p in sources}
    data = inputs(); baseline = no_extra(data); peak = period(data,8)
    eta = data['eta']; q = data['assumptions']['effective_person_hours_month']
    cases=[]; solutions=[]; checks=[]; regional_rows=[]

    def add(key, per, mode, H=None, U=240, case_data=None, result=None, **parameters):
        d = data if case_data is None else case_data
        staff = None if H is None else H/q
        res = solve(d,per,mode,staff=staff,U=U) if result is None else result
        row = {'case_id':key,'mode':mode,'human_budget':H,'drone_budget':U,**parameters,
               'success':res['success']}
        if res['success']:
            for k in ['score','total_person_hours','required_staff','base_ground_hours',
                      'base_drone_operator_hours','fire_ground_hours','fire_drone_operator_hours',
                      'water_hours','response_hours','total_flight_hours']:
                row[k]=res[k]
            ver = verify_result(d,per,res,eta=eta if mode=='inverse' else None,staff=staff,U=U)
            if not ver['passed']: raise RuntimeError((key,ver))
            checks.append({'case_id':key,**ver})
            regional_rows.extend({'case_id':key,**r} for r in regional(d,per,res))
        else:
            row.update(reason=res['reason'],solver_status=res.get('status'))
            if res.get('status') not in (None,2): raise RuntimeError((key,res))
        cases.append(row);solutions.append({'case_id':key,'period':per,'result':res})
        return row, res

    resource=[]
    for scope,per in [('q2_monitoring',baseline),('q3_peak_base',peak)]:
        for N in [24,30,35,40,44,45,46,50,53,55,56,57,59]:
            row,_=add(f'{scope}_N{N}',per,'forward',H=N*q,scope=scope,staff=N)
            resource.append(row)
    technology=[]
    for scope,per in [('q2_monitoring',baseline),('q3_peak_base',peak)]:
        for U in [0,40,80,120,160,200,240]:
            row,_=add(f'{scope}_inverse_U{U}',per,'inverse',U=U,scope=scope)
            technology.append(row)

    parameters=[]
    for kind,values in [('fire_rate',[2.,4.,8.]),('water_visits',[2,4,8]),('water_onsite_hours',[.25,.5,1.])]:
        for value in values:
            modified=copy.deepcopy(data)
            spec=modified['assumptions']['scenarios']['base']
            field={'fire_rate':'extra_fire_late_checks_per_100km2',
                   'water_visits':'water_dry_visits_month','water_onsite_hours':'water_onsite_hours_visit'}[kind]
            spec[field]=value;per=period(modified,8)
            row,_=add(f'parameter_{kind}_{value}',per,'inverse',case_data=modified,
                      parameter=kind,value=value,scope='q3_peak_base')
            parameters.append(row)

    joint=[]
    for N in [45,50,55,57,59,62,67]:
        for U in [0,80,120,160,200,240]:
            row,_=add(f'joint_N{N}_U{U}',peak,'forward',H=N*q,U=U,scope='q3_peak_base',staff=N)
            joint.append(row)

    # Retain positive-weight spatial service ratios, keep zero-weight service
    # fixed, and still optimise technology; mandatory tasks remain unchanged.
    _,peak_ref = add('profile_reference_peak',peak,'inverse',scope='q3_peak_base')
    _,q2_ref = add('profile_reference_q2',baseline,'inverse',scope='q2_monitoring')
    weights=np.array([t['objective_weight'] for t in data['targets']])
    def retain_profile(per,ref,H,U):
        original=np.array(ref['s'])
        def attempt(factor):
            profile=np.where(weights>0,original*factor,original)
            return solve(data,per,'inverse',staff=H/q,U=U,
                         eta=float(100*weights@profile),fixed_service=profile)
        lo=data['config']['minimum_reachable_service'];hi=1.
        best=attempt(lo)
        if not best['success']:return best
        full=attempt(hi)
        if full['success']:return full
        for _ in range(25):
            mid=(lo+hi)/2;candidate=attempt(mid)
            if candidate['success']:lo=mid;best=candidate
            else:hi=mid
        best['profile_scale']=lo
        return best
    policy=[]
    for key,per,ref,H,U in [('q2_scarce',baseline,q2_ref,4248,240),
                           ('peak_N55',peak,peak_ref,6600,240),
                           ('peak_N59_U120',peak,peak_ref,7080,120),
                           ('drought_N59_U120',period(data,8,drought=True),peak_ref,7080,120)]:
        unrestricted,_=add(key+'_adaptive',per,'forward',H=H,U=U,scope=key,policy='adaptive')
        restricted=retain_profile(per,ref,H,U)
        old,_=add(key+'_retained',per,'forward',H=H,U=U,result=restricted,scope=key,policy='retained')
        gain=unrestricted['score']-old['score'] if unrestricted['success'] and old['success'] else None
        if gain is not None:assert gain>=-1e-6
        policy.append({'scenario':key,'human_budget':H,'drone_budget':U,'adaptive':unrestricted,
                       'retained':old,'gain_points':gain})

    # Fixed-resource monotonicity and inverse-resource monotonicity.
    monotone=[]
    for scope in ['q2_monitoring','q3_peak_base']:
        rows=[r for r in resource if r['scope']==scope and r['success']]
        monotone.append(all(b['score']>=a['score']-1e-6 for a,b in zip(rows,rows[1:])))
        rows=[r for r in technology if r['scope']==scope]
        monotone.append(all(b['total_person_hours']<=a['total_person_hours']+1e-6 for a,b in zip(rows,rows[1:])))
    for U in [0,80,120,160,200,240]:
        rows=[r for r in joint if r['drone_budget']==U and r['success']]
        monotone.append(all(b['score']>=a['score']-1e-6 for a,b in zip(rows,rows[1:])))
    assert all(monotone)
    assert before=={p:sha(p) for p in sources},'Q2/Q3 sources changed during calculation'
    old_q2=json.loads((ROOT/'output/question2/q2_results.json').read_text(encoding='utf-8'))
    old_q3=json.loads((ROOT/'output/question3/q3_results.json').read_text(encoding='utf-8'))
    assert abs(q2_ref['score']-old_q2['optimum']['score'])<1e-6
    assert abs(peak_ref['total_person_hours']-max(r['required_person_hours'] for r in old_q3['monthly']))<1e-6
    schedules=schedule_comparison(peak)
    result={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'target_score':eta,
            'effective_person_hours_month':q,'source_sha256':before,'script_sha256':sha('scripts/modeling/build_question4.py'),
            'resource_sensitivity':resource,'technology_sensitivity':technology,'single_parameter_sensitivity':parameters,
            'joint_peak_scenarios':joint,'policy_comparisons':policy,'water_schedule_comparison':schedules,
            'service_standard_combinations_from_q3':old_q3['sensitivity'],
            'q2_saved_scenarios':[{k:v for k,v in r.items() if k!='result'}|{'result':{k:v for k,v in r['result'].items() if k not in ['x','h','s']}} for r in old_q2['scenarios']],
            'scope':'conditional service/workload planning; integer-date water-only schedule; no observed ecological effects'}
    verification={'passed':all(c['passed'] for c in checks) and all(monotone),
                  'feasible_solution_checks':len(checks),'infeasible_cases':sum(not r['success'] for r in cases),
                  'all_monotonicity_checks_passed':all(monotone),'Q2_Q3_sources_preserved':True,
                  'peak_baseline_reproduced':True,'schedule_visits_and_hours_conserved':True,'checks':checks}
    dump(OUT/'q4_results.json',result);dump(OUT/'q4_solutions.json',solutions);dump(OUT/'q4_verification.json',verification)
    columns=list(dict.fromkeys(k for row in cases for k in row))
    csvout(OUT/'q4_case_summary.csv',[{k:row.get(k) for k in columns} for row in cases])
    csvout(OUT/'q4_regional_scenarios.csv',regional_rows)
    print(json.dumps({'cases':len(cases),'verified_feasible_cases':len(checks),
                      'infeasible_cases':verification['infeasible_cases'],'verification_passed':verification['passed'],
                      'q2_threshold_hours':q2_ref['total_person_hours'],'q2_threshold_staff':q2_ref['required_staff'],
                      'q3_peak_threshold_hours':peak_ref['total_person_hours'],'q3_peak_threshold_staff':peak_ref['required_staff'],
                      'schedule_summary':[{k:v for k,v in s.items() if k not in ['points','daily_water_hours','interpretation']} for s in schedules],
                      'policy_gains':[{k:p[k] for k in ['scenario','gain_points']} for p in policy]},ensure_ascii=True,indent=2))


if __name__=='__main__':main()
