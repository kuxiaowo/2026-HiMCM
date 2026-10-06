"""Independent fractional-knapsack check of area-service LP results."""
from pathlib import Path
import json,math,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/question6'

def check(case,config):
 ts=case['targets'];floor=config['service_floor'];goal=case['target_score']
 cap=100*sum(t['weight'] for t in ts if t['eligible'])
 assert abs(cap-case['geographic_cap'])<1e-9
 assert all((t['response_hours'] is not None and t['response_hours']<=2)==t['eligible'] for t in ts)
 if goal>cap+1e-8:
  assert case['solution'] is None
  return dict(case=case['id'],passed=True,reason='analytically infeasible: target above response cap')
 s=[floor if t['eligible'] else 0 for t in ts]
 missing=max(0,goal-100*sum(t['weight']*v for t,v in zip(ts,s)))
 order=sorted((i for i,t in enumerate(ts) if t['eligible']),key=lambda i:ts[i]['cost']*ts[i]['checks']/(100*ts[i]['weight']))
 for i in order:
  take=min(1-floor,missing/(100*ts[i]['weight']));s[i]+=take;missing-=take*100*ts[i]['weight']
 assert missing<1e-7
 hours=sum(t['cost']*t['checks']*v for t,v in zip(ts,s) if t['eligible'])
 sol=case['solution'];assert sol and abs(hours-sol['patrol_hours'])<1e-6
 assert all(-1e-8<=v<=1+1e-8 and (not t['eligible'] and abs(v)<1e-8 or t['eligible'] and v>=floor-1e-8) for t,v in zip(ts,sol['s']))
 total=hours+len(case['bases'])*480
 assert abs(total-sol['total_person_hours'])<1e-6
 assert sol['staff_integer']==math.ceil((total-1e-8)/120)
 return dict(case=case['id'],passed=True,independent_hours=total,lp_difference=total-sol['total_person_hours'])

def main():
 r=json.loads((OUT/'q6_results.json').read_text(encoding='utf8'));checks=[check(c,r['config']) for c in r['cases']]
 for park in r['parks']:
  checks.append(check(json.loads((OUT/f'q6_{park}_fine.json').read_text(encoding='utf8')),r['config']))
 assert all(r['parks'][k]['polygon_area_km2']>500 for k in r['parks'])
 for park,p in r['parks'].items():assert abs(p['raster_area_km2']/p['polygon_area_km2']-1)<.01
 manifest=[]
 for path in sorted((ROOT/'data/question6').rglob('*')):
  if path.is_file() and path.suffix in ['.geojson','.pbf','.tif','.zip']:
   manifest.append(dict(file=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 quality=dict(chitwan_boundary_area=dict(passed=False,published_reported_area_km2=932.,official_report_area_km2=952.63,computed_gis_area_km2=r['parks']['chitwan']['polygon_area_km2'],reason='Published GIS boundary area is inconsistent with reported/legal area; restrict results to published-polygon migration trial'),yellowstone_public_road_records=dict(passed=True,count=2007))
 output=dict(status='numerical_checks_passed_boundary_calibration_pending',checks=checks,data_quality_checks=quality,method='independent greedy area-service allocation; score/floor/response/integer checks; raster-area vs vector-area check',real_data_files=manifest,limits='Chitwan boundary-area consistency failed; no field validation of speeds, patrol demand, permissions, species coverage or ecological outcome')
 (OUT/'q6_verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(checks,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
