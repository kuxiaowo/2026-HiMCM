"""Independent inverse/forward Q3 LP, using saved Q2 costs without changing Q2.

Five blocks: base ground hours, base UAV flight hours, base completion,
additional fire ground hours, additional fire UAV flight hours. Water is
mandatory ground-only workload. All new frequencies are planning assumptions.
"""
from __future__ import annotations
import hashlib, json, math, platform
from datetime import datetime, timezone
from importlib.metadata import version
import numpy as np
from scipy.optimize import linprog
from scipy import sparse
from build_question2 import ROOT, dump, csvout

OUT=ROOT/'output/question3'

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def persons(hours,q=120):return math.ceil((hours-1e-7)/q)

def inputs():
    data=read('output/question2/q2_model_inputs.json');ass=read('data/modeling/q3_assumptions.json');water=read('data/question3/processed/water_points.json')
    base=read('output/regions/region_base_data.json')['regional_rows'];byid={r['region_id']:r for r in base}
    for t in data['targets']:
        reg=byid[t['region_id']]
        # Preserve the observed regional fuel FRACTION when applying it to
        # the Q2 densified-projection area. Original regional areas and Q2
        # target areas differ slightly; mixing denominators can exceed 100%.
        fuel_fraction=reg['fuel_proxy_baseline_area_wc2021_km2']/reg['geometry_area_km2']
        t['fuel_support_area_km2']=t['support_area_km2']*fuel_fraction
        assert 0<=t['fuel_support_area_km2']<=t['support_area_km2']+1e-5
    data['assumptions']=ass;data['water']=water;data['eta']=read('output/question2/q2_results.json')['optimum']['score']
    assert ass['effective_person_hours_month']==120 and data['config']['effective_hours_month']==120
    return data

def period(data,month,scenario='base',drought=False,water_multiplier=1.):
    ass=data['assumptions'];p=ass['scenarios'][scenario]
    dry=month in ass['dry_months'];early=month in ass['early_fire_months'];late=month in ass['late_fire_months'];stress=bool(drought and dry)
    v=p['water_drought_visits_month'] if stress else p['water_dry_visits_month'] if dry else p['water_wet_visits_month']
    onsite=p['water_drought_onsite_hours_visit'] if stress else p['water_onsite_hours_visit']
    water_rows=[]
    for r in data['water']['points']:
        if not r['included']:continue
        hours=ass['water_team_size']*(r['round_travel_hours']+onsite+ass['water_preparation_hours_visit'])
        water_rows.append({'name':r['name'],'region_id':r['region_id'],'base_name':r['base_name'],'visits_month':v,'round_travel_hours':r['round_travel_hours'],'onsite_hours_visit':onsite,'person_hours_visit':hours,'monthly_person_hours':v*hours*water_multiplier,'inventory_multiplier_scenario':water_multiplier})
    k=p['extra_fire_late_checks_per_100km2'] if late else p['extra_fire_early_checks_per_100km2'] if early else 0
    allfire=np.array([k*t['fuel_support_area_km2']/100 for t in data['targets']]);eligible=np.array([t['response_eligible'] for t in data['targets']],dtype=float)
    return {'month':month,'scenario':scenario,'drought':stress,'water_inventory_multiplier':water_multiplier,'season':'late_fire_dry' if late and dry else 'early_fire_dry' if early else 'late_fire_wet' if late else 'wet_regular','water_visits_month':v,'water_max_gap_days':30/v,'water_onsite_hours_visit':onsite,'water_hours':sum(r['monthly_person_hours'] for r in water_rows),'water_rows':water_rows,'extra_fire_rate':k,'fire_checks':(allfire*eligible).tolist(),'unreachable_fire_checks':float(allfire@(1-eligible)),'fire_full_area_planned_checks':float(allfire.sum())}

def solve(data,per,mode='inverse',staff=None,eta=None,U=None,score_floor=None,fixed_service=None):
    ts=data['targets'];n=len(ts);eta=data['eta'] if eta is None else eta;U=data['drone_budget'] if U is None else U
    w=np.array([t['objective_weight'] for t in ts]);r=np.array([float(t['response_eligible']) for t in ts]);cap=float(100*w@r)
    if mode=='inverse' and eta>cap+1e-8:return {'success':False,'reason':'target_above_geographic_cap','geographic_cap':cap}
    F=np.array([t['planned_checks_month'] for t in ts]);E=np.array(per['fire_checks'])
    a=np.array([t['ground_hours_per_check'] or 1 for t in ts]);b=np.array([t['flight_hours_per_check'] or 1 for t in ts]);gamma=np.array([t['operator_hours_per_check']/t['flight_hours_per_check'] if t['drone_allowed'] else 0 for t in ts])
    human=np.zeros(5*n);human[:n]=1;human[n:2*n]=gamma;human[3*n:4*n]=1;human[4*n:]=gamma
    obj=human.copy() if mode=='inverse' else np.zeros(5*n)
    if mode=='forward':obj[2*n:3*n]=-1e4*w
    ii=[];jj=[];vv=[];rhs=[]
    def row(items,upper):
        i=len(rhs)
        for j,v in items:ii.append(i);jj.append(j);vv.append(v)
        rhs.append(upper)
    for j,t in enumerate(ts):
        row([(j,-1/a[j]),(n+j,-1/b[j]),(2*n+j,F[j])],0)
        row([(3*n+j,-1/a[j]),(4*n+j,-1/b[j])],-E[j])
    row([(n+j,1) for j in range(n)]+[(4*n+j,1) for j in range(n)],U)
    for rid in data['region_ids']:
        ids=[j for j,t in enumerate(ts) if t['region_id']==rid]
        reachable=sum(ts[j]['within_region_area_share']*r[j] for j in ids)
        row([(2*n+j,-ts[j]['within_region_area_share']) for j in ids],-data['config']['minimum_reachable_service']*reachable)
    at_cap=False
    if mode=='inverse' or score_floor is not None:
        floor=eta if score_floor is None else score_floor
        at_cap=abs(floor-cap)<1e-8
        # At the cap, every positively weighted reachable target must have
        # s=1; fixing those bounds is algebraically equivalent and prevents
        # HiGHS from dropping tiny fragment weights below its matrix cutoff.
        if not at_cap:row([(2*n+j,-1e4*w[j]) for j in range(n)],-1e4*floor/100)
    H0=data['response_reserved_hours'];water=per['water_hours']
    if staff is not None:
        H=staff*data['assumptions']['effective_person_hours_month']
        row([(j,v) for j,v in enumerate(human) if v],H-H0-water)
    bounds=[(0,F[j]*a[j] if t['response_eligible'] else 0) for j,t in enumerate(ts)]
    bounds +=[(0,F[j]*b[j] if t['drone_allowed'] else 0) for j,t in enumerate(ts)]
    bounds +=[(float(fixed_service[j]),float(fixed_service[j])) if fixed_service is not None else (r[j],r[j]) if at_cap and w[j]>0 else (0,r[j]) for j in range(n)]
    bounds +=[(0,E[j]*a[j] if t['response_eligible'] else 0) for j,t in enumerate(ts)]
    bounds +=[(0,E[j]*b[j] if t['drone_allowed'] else 0) for j,t in enumerate(ts)]
    mat=sparse.coo_matrix((vv,(ii,jj)),shape=(len(rhs),5*n)).tocsr()
    res=linprog(obj,A_ub=mat,b_ub=np.array(rhs),bounds=bounds,method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    if not res.success:return {'success':False,'reason':'LP_infeasible_or_failure','status':int(res.status),'message':res.message}
    z=res.x;score=float(100*w@z[2*n:3*n]);total=float(human@z+H0+water)
    # Reoptimise all service fractions at the optimal score, using the same
    # two-stage objective as the revised Q2 rather than a fixed allocation.
    if mode=='forward':
        floor=cap if abs(score-cap)<1e-8 else score-1e-9
        refined=solve(data,per,'inverse',staff=staff,U=U,score_floor=floor)
        if not refined['success']:raise RuntimeError(f'Forward score refinement failed: month={per["month"]}, score={score}, cap={cap}, {refined}')
        return refined
    return {'success':True,'score':score,'geographic_cap':cap,'eta':eta,'total_person_hours':total,'required_staff':persons(total),'response_hours':float(H0),'water_hours':float(water),'base_ground_hours':float(z[:n].sum()),'base_drone_operator_hours':float(gamma@z[n:2*n]),'base_flight_hours':float(z[n:2*n].sum()),'fire_ground_hours':float(z[3*n:4*n].sum()),'fire_drone_operator_hours':float(gamma@z[4*n:]),'fire_flight_hours':float(z[4*n:].sum()),'total_flight_hours':float(z[n:2*n].sum()+z[4*n:].sum()),'drone_budget':float(U),'constraint_max_residual':float(np.max(mat@z-np.array(rhs))),'x_base':z[:n].tolist(),'h_base':z[n:2*n].tolist(),'s':z[2*n:3*n].tolist(),'x_fire':z[3*n:4*n].tolist(),'h_fire':z[4*n:].tolist(),'staff_budget':staff}

def verify_result(data,per,result,eta=None,staff=None,U=None):
    if not result['success']:return {'passed':False,'failure':result}
    ts=data['targets'];a=np.array([t['ground_hours_per_check'] or 1 for t in ts]);b=np.array([t['flight_hours_per_check'] or 1 for t in ts]);gamma=np.array([t['operator_hours_per_check']/t['flight_hours_per_check'] if t['drone_allowed'] else 0 for t in ts])
    x=np.array(result['x_base']);h=np.array(result['h_base']);s=np.array(result['s']);xf=np.array(result['x_fire']);hf=np.array(result['h_fire']);F=np.array([t['planned_checks_month'] for t in ts]);E=np.array(per['fire_checks'])
    score=100*np.array([t['objective_weight'] for t in ts])@s
    labor=x.sum()+xf.sum()+gamma@(h+hf)+data['response_reserved_hours']+per['water_hours']
    gaps={rid:sum(t['within_region_area_share']*(s[j]-data['config']['minimum_reachable_service']*float(t['response_eligible'])) for j,t in enumerate(ts) if t['region_id']==rid) for rid in data['region_ids']}
    tests={'base_capacity':bool(np.min(x/a+h/b-F*s)>=-1e-6),'mandatory_fire_capacity':bool(np.min(xf/a+hf/b-E)>=-1e-6),'service_bounds':bool(min(s)>=-1e-8 and all(s[j]<=float(t['response_eligible'])+1e-8 for j,t in enumerate(ts))),'nonnegative_hours':bool(min(np.concatenate([x,h,xf,hf]))>=-1e-8),'forbidden_drone_zero':bool(all(abs(h[j])+abs(hf[j])<1e-7 for j,t in enumerate(ts) if not t['drone_allowed'])),'unreachable_ground_zero':bool(all(abs(x[j])+abs(xf[j])<1e-7 for j,t in enumerate(ts) if not t['response_eligible'])),'regional_floors':min(gaps.values())>=-1e-7,'UAV_budget':float((h+hf).sum())<=(data['drone_budget'] if U is None else U)+1e-6,'score_recalculation':abs(score-result['score'])<1e-7,'labor_recalculation':abs(labor-result['total_person_hours'])<1e-6,'integer_staff_suffices':result['required_staff']*120>=labor-1e-6,'one_fewer_staff_insufficient_for_THIS_labor':(result['required_staff']-1)*120<labor-1e-6}
    if eta is not None:tests['target_met']=score>=eta-1e-6
    if staff is not None:tests['staff_budget']=labor<=120*staff+1e-6
    tests={k:bool(v) for k,v in tests.items()}
    return {'passed':all(tests.values()),'checks':tests,'maximum_base_check_shortfall':float(max(0,np.max(F*s-x/a-h/b))),'maximum_fire_check_shortfall':float(max(0,np.max(E-xf/a-hf/b))),'minimum_region_floor_margin':min(gaps.values())}

def regional(data,per,res):
    rows=[];ts=data['targets']
    for rid in data['region_ids']:
        ids=[j for j,t in enumerate(ts) if t['region_id']==rid]
        basehuman=sum(res['x_base'][j]+res['h_base'][j]*(ts[j]['operator_hours_per_check']/ts[j]['flight_hours_per_check'] if ts[j]['drone_allowed'] else 0) for j in ids)
        firehuman=sum(res['x_fire'][j]+res['h_fire'][j]*(ts[j]['operator_hours_per_check']/ts[j]['flight_hours_per_check'] if ts[j]['drone_allowed'] else 0) for j in ids)
        water=sum(r['monthly_person_hours'] for r in per['water_rows'] if r['region_id']==rid)
        rows.append({'month':per['month'],'region_id':rid,'reachable_area_share':sum(ts[j]['within_region_area_share'] for j in ids if ts[j]['response_eligible']),'base_service_area_fraction':sum(ts[j]['within_region_area_share']*res['s'][j] for j in ids),'base_person_hours':basehuman,'extra_fire_checks':sum(per['fire_checks'][j] for j in ids),'extra_fire_person_hours':firehuman,'water_person_hours':water,'total_field_person_hours':basehuman+firehuman+water,'flight_hours':sum(res['h_base'][j]+res['h_fire'][j] for j in ids),'shared_response_hours_not_split':True})
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True);data=inputs();eta=data['eta'];fixed=data['assumptions']['fixed_reference_staff']
    fingerprints={p:sha(p) for p in ['output/question2/q2_results.json','output/question2/q2_model_inputs.json','output/question2/q2_verification.json','data/modeling/q2_assumptions.json','data/modeling/q3_assumptions.json','data/question3/processed/water_points.json','scripts/modeling/build_question3.py','scripts/modeling/prepare_question3.py']}
    monthly=[];full=[];regrows=[];checks=[];cache={}
    for month in range(1,13):
        per=period(data,month);key=(per['extra_fire_rate'],per['water_hours'])
        if key not in cache:cache[key]=(solve(data,per),solve(data,per,'forward',staff=fixed))
        inv,fwd=cache[key];assert inv['success'] and fwd['success']
        checks +=[{'month':month,'mode':'inverse',**verify_result(data,per,inv,eta=eta)},{'month':month,'mode':'fixed_reference',**verify_result(data,per,fwd,staff=fixed)}]
        row={'month':month,'season':per['season'],'water_visits_month':per['water_visits_month'],'water_hours':per['water_hours'],'extra_fire_rate':per['extra_fire_rate'],'extra_fire_checks':sum(per['fire_checks']),'unreachable_extra_fire_checks':per['unreachable_fire_checks'],'response_hours':inv['response_hours'],'base_monitoring_person_hours':inv['base_ground_hours']+inv['base_drone_operator_hours'],'extra_fire_person_hours':inv['fire_ground_hours']+inv['fire_drone_operator_hours'],'required_person_hours':inv['total_person_hours'],'required_staff':inv['required_staff'],'flight_hours':inv['total_flight_hours'],'fixed_reference_staff':fixed,'fixed_reference_score':fwd['score'],'target_score':eta,'staff_gap_to_reference':max(0,inv['required_staff']-fixed)}
        monthly.append(row);full.append({'period':per,'inverse':inv,'fixed_reference':fwd});regrows +=regional(data,per,inv)
    plan=max(r['required_staff'] for r in monthly)
    for item in full:
        per=item['period'];forward=solve(data,per,'forward',staff=plan);item['fixed_plan']=forward
        checks.append({'month':per['month'],'mode':'fixed_annual_plan',**verify_result(data,per,forward,eta=eta,staff=plan)})
    # Meaningful behavioural/edge cases; no tests merely mirroring code.
    baselineper=period(data,1);baselineper['water_hours']=0;baselineper['water_rows']=[]
    q2=read('output/question2/q2_results.json')['optimum'];recovery=solve(data,baselineper,fixed_service=q2['s'])
    free_baseline=solve(data,baselineper)
    baseline_error=abs(recovery['total_person_hours']-q2['total_person_hours'])
    above=solve(data,period(data,8),eta=eta+.01)
    too_low=solve(data,period(data,8),'forward',staff=20)
    below=solve(data,period(data,8),'forward',staff=plan-1)
    lower=solve(data,period(data,8),eta=eta*.9)
    no_uav=solve(data,period(data,8),U=0)
    behaviors={'recover_Q2_when_its_service_pattern_is_fixed':baseline_error<1e-5,'independent_inverse_LP_matches_Q2_global_minimum':abs(free_baseline['total_person_hours']-q2['total_person_hours'])<1e-5,'free_equal_score_baseline_no_more_labor':free_baseline['total_person_hours']<=q2['total_person_hours']+1e-6,'unreachable_target_rejected':not above['success'] and above['reason']=='target_above_geographic_cap','insufficient_fixed_response_budget_infeasible':not too_low['success'],'one_fewer_peak_staff_loses_target':not below['success'] or below['score']<eta-1e-6,'lower_target_no_more_labor':lower['success'] and lower['total_person_hours']<=max(r['required_person_hours'] for r in monthly)+1e-6,'no_UAV_requires_more_labor':no_uav['success'] and no_uav['total_person_hours']>=max(r['required_person_hours'] for r in monthly)-1e-6}
    sensitivities=[];sensfull=[]
    for scenario in ['low','base','high']:
        for drought in [False,True]:
            sols=[]
            for month in [1,5,8,11]:
                per=period(data,month,scenario,drought);res=solve(data,per);assert res['success']
                assert verify_result(data,per,res,eta=eta)['passed'];sols.append((per,res))
            per,res=max(sols,key=lambda t:t[1]['total_person_hours']);sensitivities.append({'scenario':scenario,'abnormal_drought':drought,'peak_month_example':per['month'],'peak_person_hours':res['total_person_hours'],'annual_fixed_staff':res['required_staff'],'peak_water_hours':per['water_hours'],'peak_flight_hours':res['total_flight_hours'],'interpretation':'assumed service standards, not confidence bounds or observed drought'})
            sensitivity_solutions=[]
            for p,r in sols:
                fwd=solve(data,p,'forward',staff=fixed)
                if fwd['success']:assert verify_result(data,p,fwd,staff=fixed)['passed']
                sensitivity_solutions.append({'period':p,'inverse':r,'fixed_reference':fwd})
            sensfull.append({'name':scenario+('_drought' if drought else ''),'solutions':sensitivity_solutions})
    inventory=[]
    for mult in [1,2,3]:
        per=period(data,8,water_multiplier=mult);res=solve(data,per);assert res['success']
        inventory.append({'assumed_identical_inventory_multiplier':mult,'equivalent_BH_count':mult*data['water']['modelled_BH_count'],'required_staff':res['required_staff'],'required_person_hours':res['total_person_hours'],'water_hours':per['water_hours'],'interpretation':'workload replication only, NOT actual park borehole counts or geographically valid expansion'})
    # Audit every original scientific Q2 output remains byte-for-byte unchanged.
    preserved=all(sha(p)==fingerprints[p] for p in fingerprints if 'question2/' in p or 'q2_assumptions' in p)
    static={'Q2_files_preserved':preserved,'water_table_BH_only':data['water']['BH_count']==17 and data['water']['modelled_BH_count']==17,'water_points_routable':all(r.get('road_reachable') for r in data['water']['points'] if r['included']),'effective_hours_fixed_120':data['assumptions']['effective_person_hours_month']==120,'response_counted_once':data['response_reserved_hours']==2880,'year_uses_month_max_not_sum':plan==max(r['required_staff'] for r in monthly),'reference_staff_matches_Q2_monthly_availability':fixed==data['config']['staff_reference']*data['config']['protection_staff_fraction'],'response_only_staff_equivalent':plan>=persons(data['response_reserved_hours'])}
    longest=max(r['round_travel_hours'] for r in data['water']['points'] if r['included'])+data['assumptions']['scenarios']['base']['water_onsite_hours_visit']+data['assumptions']['water_preparation_hours_visit']
    verification={'passed':all(c['passed'] for c in checks) and all(behaviors.values()) and all(static.values()),'per_month':checks,'behavior_checks':behaviors,'static_checks':static,'baseline_recovery_person_hour_error':baseline_error,'one_fewer_peak_staff_forward_score':below.get('score'),'no_UAV_peak_staff':no_uav.get('required_staff'),'lower_target_90percent_staff':lower.get('required_staff'),'longest_water_visit_elapsed_hours':longest,'water_visits_fit_8h_window':longest<=8,'concurrency_scope':{'response_posts_people_in_daytime_window':len(data['bases'])*data['config']['response_staff_per_site'],'aircraft_inventory':data['config']['drone_count'],'UAV_people_per_active_crew':data['config']['drone_team_size'],'water_people_per_active_crew':data['assumptions']['water_team_size'],'simultaneously_active_UAV_crews':None,'interpretation':'Inventory is not concurrent sorties. Monthly hours determine task labor; no detailed roster or every-site concurrency is proved, and all aircraft are not required to fly at once.'},'limitations':['Historical sample of 17 boreholes, not complete current inventory','New service frequencies and durations assumed; low/base/high are planning scenarios','Monthly time budget is continuous, task fractions not integer dispatch schedules','Fixed geographic response gap remains; extra fire demand outside reachable targets recorded unserved','No measured ecological improvement, prescribed burning, suppression, water volumes, emergency pumping or multi-day repair model']}
    dump(OUT/'q3_verification.json',verification)
    verification['free_equal_score_baseline_person_hours']=free_baseline['total_person_hours']
    verification['free_equal_score_reallocation_saves_person_hours']=q2['total_person_hours']-free_baseline['total_person_hours']
    assert verification['passed'],json.dumps({k:v for k,v in verification.items() if k!='per_month'},ensure_ascii=False)
    output={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'model':'forward and inverse continuous LP, 599 targets, separate mandatory fire tasks, constant ground-only water work','target_score':eta,'fixed_reference_staff':fixed,'annual_fixed_staff_base_scenario':plan,'scope':'Q2 monitoring/responses plus 17 historical borehole sample operations; conditional personnel planning only','monthly':monthly,'sensitivity':sensitivities,'water_inventory_workload_sensitivity':inventory,'full_monthly_solutions':full,'full_sensitivity_solutions':sensfull,'source_and_code_sha256':fingerprints,'runtime':{'python':platform.python_version(),'packages':{p:version(p) for p in ['numpy','scipy','matplotlib','networkx','shapely','pyproj','osmium','requests','beautifulsoup4']}},'verification_summary':{k:v for k,v in verification.items() if k!='per_month'}}
    dump(OUT/'q3_results.json',output);dump(OUT/'q3_verification.json',verification);csvout(OUT/'q3_monthly.csv',monthly);csvout(OUT/'q3_regions_by_month.csv',regrows);csvout(OUT/'q3_sensitivity.csv',sensitivities)
    csvout(OUT/'q3_water_visits_base.csv',[{**r,'period':'wet_regular'} for r in period(data,1)['water_rows']]+[{**r,'period':'dry'} for r in period(data,8)['water_rows']]+[{**r,'period':'abnormal_drought'} for r in period(data,8,drought=True)['water_rows']])
    print(json.dumps({'annual_fixed_staff':plan,'monthly':monthly,'sensitivity':sensitivities,'verification_passed':verification['passed'],'longest_water_visit_hours':longest,'inventory_sensitivity':inventory},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
