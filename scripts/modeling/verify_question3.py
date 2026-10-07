"""Independently audit saved Q3 solutions, with no import of its solver/model.

Checks original Q2 inputs, manually transcribed water evidence, workload units,
all saved solutions, CSV region totals and source/code fingerprints.
"""
import csv, hashlib, json, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def main():
    out=ROOT/'output/question3';result=read('output/question3/q3_results.json');q2=read('output/question2/q2_model_inputs.json');ass=read('data/modeling/q3_assumptions.json');water=read('data/question3/processed/water_points.json');regs=read('output/regions/region_base_data.json')['regional_rows']
    byid={r['region_id']:r for r in regs};ts=q2['targets'];w=np.array([t['objective_weight'] for t in ts]);eligible=np.array([t['response_eligible'] for t in ts],dtype=float)
    a=np.array([t['ground_hours_per_check'] or 1 for t in ts]);b=np.array([t['flight_hours_per_check'] or 1 for t in ts]);gamma=np.array([t['operator_hours_per_check']/t['flight_hours_per_check'] if t['drone_allowed'] else 0 for t in ts]);F=np.array([t['planned_checks_month'] for t in ts]);fuel=np.array([t['support_area_km2']*byid[t['region_id']]['fuel_proxy_baseline_area_wc2021_km2']/byid[t['region_id']]['geometry_area_km2'] for t in ts])
    source=list(csv.DictReader((ROOT/'data/question3/raw/koedoe_water_points_2013.csv').open(encoding='utf-8-sig')))
    points=[r for r in water['points'] if r['included']]
    checks={'all_input_code_hashes_current':all(sha(p)==v for p,v in result['source_and_code_sha256'].items()),'source_transcription_unchanged':sha('data/question3/raw/koedoe_water_points_2013.csv')==water['transcription_sha256'],'source_image_unchanged':sha('data/question3/raw/koedoe_table1.png')==water['source_image_sha256'],'17_BH_only':len(points)==17 and {r['name'] for r in source if r['type']=='BH'}=={r['name'] for r in points},'120h_fixed':ass['effective_person_hours_month']==120,'target_equals_saved_Q2_optimum':abs(result['target_score']-read('output/question2/q2_results.json')['optimum']['score'])<1e-10,'weights_sum_one':abs(w.sum()-1)<1e-10}
    audits=[]
    def audit(label,p,res,staff=None,needs_target=False):
        if not res['success']:return
        month=p['month'];params=ass['scenarios'][p['scenario']];dry=month in ass['dry_months'];stress=bool(p['drought'] and dry)
        visits=params['water_drought_visits_month'] if stress else params['water_dry_visits_month'] if dry else params['water_wet_visits_month'];onsite=params['water_drought_onsite_hours_visit'] if stress else params['water_onsite_hours_visit']
        W=sum(visits*ass['water_team_size']*(r['round_travel_hours']+onsite+ass['water_preparation_hours_visit'])*p['water_inventory_multiplier'] for r in points)
        k=params['extra_fire_late_checks_per_100km2'] if month in ass['late_fire_months'] else params['extra_fire_early_checks_per_100km2'] if month in ass['early_fire_months'] else 0
        E=k*fuel*eligible/100
        x,h,s,y,v=[np.array(res[k]) for k in ['x_base','h_base','s','x_fire','h_fire']]
        H=float(x.sum()+y.sum()+gamma@(h+v)+q2['response_reserved_hours']+W);score=float(100*w@s)
        floor=min(sum(t['within_region_area_share']*(s[j]-q2['config']['minimum_reachable_service']*eligible[j]) for j,t in enumerate(ts) if t['region_id']==rid) for rid in q2['region_ids'])
        passed=bool(abs(W-p['water_hours'])<1e-6 and np.max(np.abs(E-np.array(p['fire_checks'])))<1e-7 and np.min(x/a+h/b-F*s)>=-1e-6 and np.min(y/a+v/b-E)>=-1e-6 and floor>=-1e-7 and s.min()>=-1e-7 and (s-eligible).max()<=1e-7 and min(np.concatenate([x,h,y,v]))>=-1e-7 and (h+v).sum()<=q2['drone_budget']+1e-6 and abs(H-res['total_person_hours'])<1e-6 and abs(score-res['score'])<1e-7 and res['required_staff']==math.ceil((H-1e-7)/120) and all(abs(h[j])+abs(v[j])<1e-7 for j,t in enumerate(ts) if not t['drone_allowed']))
        if staff is not None:passed=passed and H<=120*staff+1e-6
        if needs_target:passed=passed and score>=result['target_score']-1e-6
        audits.append({'name':label,'passed':bool(passed),'score':score,'person_hours':H,'flight_hours':float((h+v).sum())})
    for item in result['full_monthly_solutions']:
        p=item['period'];m=p['month']
        audit(f'month{m}_inverse',p,item['inverse'],needs_target=True)
        audit(f'month{m}_fixed{ass["fixed_reference_staff"]}',p,item['fixed_reference'],staff=ass['fixed_reference_staff'])
        audit(f'month{m}_fixed_plan',p,item['fixed_plan'],staff=result['annual_fixed_staff_base_scenario'],needs_target=True)
    for group in result['full_sensitivity_solutions']:
        for item in group['solutions']:
            p=item['period'];audit(f'{group["name"]}_month{p["month"]}_inverse',p,item['inverse'],needs_target=True);audit(f'{group["name"]}_month{p["month"]}_fixed{ass["fixed_reference_staff"]}',p,item['fixed_reference'],staff=ass['fixed_reference_staff'])
    regionrows=list(csv.DictReader((out/'q3_regions_by_month.csv').open(encoding='utf-8-sig')))
    for row in result['monthly']:
        Hreg=sum(float(r['total_field_person_hours']) for r in regionrows if int(r['month'])==row['month'])
        checks[f'month{row["month"]}_CSV_region_labor_totals']=abs(Hreg+q2['response_reserved_hours']-row['required_person_hours'])<1e-6
    checks['year_plan_max_not_sum']=result['annual_fixed_staff_base_scenario']==max(r['required_staff'] for r in result['monthly'])
    checks['saved_model_verification_passed']=read('output/question3/q3_verification.json')['passed']
    checks={k:bool(v) for k,v in checks.items()}
    final={'passed':all(checks.values()) and all(a['passed'] for a in audits),'checks':checks,'saved_solutions_audited':len(audits),'solutions':audits,'limits':'Checks saved feasibility, units and totals; relies on HiGHS optimal status for LP optimality; does not validate assumed frequencies or detailed schedules.'}
    (out/'q3_independent_verification.json').write_text(json.dumps(final,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'passed':final['passed'],'solutions_audited':len(audits),'failed_checks':[k for k,v in checks.items() if not v]},ensure_ascii=False));assert final['passed']

if __name__=='__main__':main()
