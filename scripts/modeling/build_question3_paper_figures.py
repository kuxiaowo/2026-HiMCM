"""Original Q3 paper figures; render identical primitives to PNG/SVG/TikZ.

Only reads saved inputs/solutions. Shares the Q2 drawing style, not its model.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from matplotlib import colors, pyplot as plt
from shapely.geometry import shape
from shapely.ops import transform
import build_question2_paper_figures as drawing
from build_question2 import FWD, load_geometry, polygons

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/question3/paper_figures'
Canvas = drawing.Canvas
BLUE, GOLD, RED, INK, GREY, PALE = drawing.BLUE, drawing.GOLD, drawing.RED, drawing.INK, drawing.GREY, drawing.PALE
TEAL = '#41988c'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def pipeline(result):
    c = Canvas(17, 6.05)
    boxes = [(.2,4.8,5.1,.9,BLUE,'第二题固定基线','权重、成本、响应范围与机队'),
             (.2,3.3,5.1,.9,TEAL,'月度附加服务','火险点次 + 水点地面运维'),
             (6.1,3.85,4.45,1.2,PALE,'共同可行范围','容量、机时与区域底线'),
             (11.4,4.8,5.4,.9,BLUE,f"固定{result['fixed_reference_staff']}人",'每月最高基准服务分'),
             (11.4,2.9,5.4,.9,GOLD,'固定57.26分目标','每月最少总人时')]
    for x,y,w,h,col,title,detail in boxes:
        c.rect(x,y,w,h,col)
        color = 'white' if col != PALE else INK
        c.text(x+w/2,y+h*.7,title,11,color,bold=True)
        c.text(x+w/2,y+h*.24,detail,9,color)
    c.line([(5.35,5.25),(5.7,5.25),(5.7,4.7),(6.02,4.7)],GREY,1,arrow=True)
    c.line([(5.35,3.75),(5.7,3.75),(5.7,4.2),(6.02,4.2)],GREY,1,arrow=True)
    c.line([(10.6,4.65),(10.98,4.65),(10.98,5.25),(11.33,5.25)],GREY,1,arrow=True)
    c.line([(10.6,4.2),(10.98,4.2),(10.98,3.35),(11.33,3.35)],GREY,1,arrow=True)
    c.rect(11.4,1.2,5.4,.9,PALE)
    c.text(14.1,1.84,'人时 ÷ 120并向上取整',10,bold=True)
    c.text(14.1,1.44,'全年固定人数取月度峰值',9)
    c.line([(14.1,2.84),(14.1,2.16)],GOLD,1,arrow=True)
    c.text(5.45,2.0,'季节变化改变必要工作量',10,c=TEAL)
    c.text(5.45,1.4,'全年评分口径与目标保持一致',10,c=BLUE)
    c.text(8.5,.4,'响应预留只计一次；两类模型共用同一人员与机时核算口径',9,c=GREY)
    c.save('fig1_monthly_model_pipeline')


def water_map(data, water, ass):
    points = [p for p in water['points'] if p['included']]
    p = ass['scenarios']['base']
    n, f, prep = ass['water_team_size'], p['water_dry_visits_month'], ass['water_preparation_hours_visit']
    rows = sorted(points,key=lambda r:r['round_travel_hours'],reverse=True)
    geom=load_geometry()
    xmin=min(g.bounds[0] for _,g in geom); xmax=max(g.bounds[2] for _,g in geom)
    ymin=min(g.bounds[1] for _,g in geom); ymax=max(g.bounds[3] for _,g in geom)
    scale=min(7.65/(xmax-xmin),4.85/(ymax-ymin))
    x0=.3; y0=2.7
    def xy(coords):
        return np.array([[x0+(x-xmin)*scale,y0+(y-ymin)*scale] for x,y in coords])
    c=Canvas(17,8.55)
    c.text(4.1,8.15,'(a) 历史钻井样本与候选驻点',11,bold=True)
    c.text(12.6,8.15,'(b) 旱季各水点月运维人时',11,bold=True)
    for rid,g in geom:
        for poly in polygons(g.simplify(400,preserve_topology=True)):
            if poly.area<2e5:continue
            rings=[xy(poly.exterior.coords)]+[xy(i.coords) for i in poly.interiors]
            c.poly(rings,'#e4e9ed' if rid=='PAN_MAIN' else '#f0f4f2','white',.35)
    roads=read('data/roads/processed/park_edges.geojson')['features']
    for road in roads:
        g=transform(FWD,shape(road['geometry'])).simplify(200)
        if g.geom_type=='LineString':c.line(xy(g.coords),'#a4b0b6',.17)
    for r in points:
        x,y=xy([FWD(r['longitude'],r['latitude'])])[0]
        hours=f*n*(r['round_travel_hours']+p['water_onsite_hours_visit']+prep)
        c.circle(x,y,.046+hours*.0012,TEAL,'white',.3)
    for b in data['bases']:
        x,y=xy([FWD(b['lon'],b['lat'])])[0];c.star(x,y,.11,BLUE)
    c.line([(.85,6.9),(.85,7.35)],INK,.8,arrow=True);c.text(.85,7.55,'N',8)
    c.line([(.55,2.15),(.55+50000*scale,2.15)],INK,1.2);c.text(.55+25000*scale,1.93,'50 km',8.5)
    c.circle(3.05,2.13,.075,TEAL);c.text(3.25,2.13,'17处BH钻井',9,ha='left')
    c.star(6.05,2.13,.11,BLUE);c.text(6.28,2.13,'候选驻点',9,ha='left')
    travel=sum(r['round_travel_hours'] for r in rows)
    total=f*n*(travel+len(rows)*(p['water_onsite_hours_visit']+prep))
    c.rect(.4,.75,7.4,.74,PALE)
    c.text(4.1,1.25,f'往返时间合计 {travel:.2f} h；每点4次/月',9.5)
    c.text(4.1,.94,f'两人运维 → 合计 {total:.2f} 人时/月',9.5,bold=True)
    left=12.0; width=4.25; mx=55
    for val in [0,20,40]:
        x=left+width*val/mx;c.line([(x,1.4),(x,7.72)],'#dce3e9',.35);c.text(x,1.15,str(val),8,c=GREY)
    for i,r in enumerate(rows):
        y=7.45-i*.35
        c.text(left-.14,y,r['name'],7.8,ha='right')
        vals=[f*n*r['round_travel_hours'],f*n*p['water_onsite_hours_visit'],f*n*prep]
        start=left
        for v,col in zip(vals,[BLUE,TEAL,GREY]):
            w=width*v/mx;c.rect(start,y-.11,w,.22,col);start+=w
        c.text(start+.08,y,f'{sum(vals):.1f}',7.5,ha='left')
    for i,(col,label) in enumerate([(BLUE,'往返'),(TEAL,'现场'),(GREY,'准备')]):
        x=9.65+i*2.13;c.rect(x,.66,.18,.13,col);c.text(x+.28,.725,label,8.5,ha='left')
    c.text(12.7,.30,'横轴：人时/月；每次两人、现场0.5 h',8.5,c=GREY)
    c.save('fig2_water_points_and_workload')
    return {'sample_count':len(rows),'round_travel_hours_sum':travel,'dry_water_hours':total,
            'point_rows':[{'name':r['name'],'dry_monthly_person_hours':f*n*(r['round_travel_hours']+.5+prep)} for r in rows]}


def monthly(result):
    c=Canvas(17,9.5); rows=result['monthly']
    left=1.7; right=16.4; width=right-left; bottom=4.25; height=3.35; ymax=8000
    c.text(8.5,9.1,'(a) 维持57.26分目标的月度人时构成',11,bold=True)
    cols=[GREY,BLUE,GOLD,TEAL]
    for i,(col,label) in enumerate(zip(cols,['共享响应','基准监测','额外火险检查','17处水点运维'])):
        x=1.6+i*3.85;c.rect(x,8.43,.2,.15,col);c.text(x+.32,8.505,label,9,ha='left')
    for val in [0,2000,4000,6000,8000]:
        y=bottom+height*val/ymax;c.line([(left,y),(right,y)],'#e0e6ea',.35);c.text(left-.17,y,str(val),8.5,ha='right',c=GREY)
    c.text(.3,6.0,'人时\n/月',8)
    ref=result['fixed_reference_staff']*120
    c.text(right,7.96,f"参考{result['fixed_reference_staff']}人预算：{ref:.0f}人时/月（高于图示范围）",9,c=RED,ha='right')
    centers=[]
    for i,r in enumerate(rows):
        x=left+width*(i+.5)/12;centers.append(x);start=bottom
        for key,col in zip(['response_hours','base_monitoring_person_hours','extra_fire_person_hours','water_hours'],cols):
            h=height*r[key]/ymax;c.rect(x-.35,start,.7,h,col);start+=h
        c.text(x,start+.15,f"{r['required_person_hours']:.0f}",7.8)
        c.text(x,bottom-.26,f'{i+1}',8.5)
    c.text(8.9,3.6,'(b) 月度所需人数与全年固定配置',11,bold=True)
    y0=1.0; h2=1.95
    fy=lambda v:y0+h2*(v-40)/22
    for val in [40,50,60]:
        y=fy(val);c.line([(left,y),(right,y)],'#e0e6ea',.35);c.text(left-.17,y,str(val),8.5,ha='right',c=GREY)
    for val,col in [(result['annual_fixed_staff_base_scenario'],BLUE)]:
        y=fy(val);c.line([(left,y),(right,y)],col,.8,dashed=True)
    c.text(right,3.03,f"参考配置{result['fixed_reference_staff']}人 / 常规全年需求{result['annual_fixed_staff_base_scenario']}人",8.5,ha='right',c=GREY)
    xy=[(x,fy(r['required_staff'])) for x,r in zip(centers,rows)]
    c.line(xy,BLUE,1.5)
    for i,((x,y),r) in enumerate(zip(xy,rows)):
        c.circle(x,y,.045,BLUE);c.text(x,y-.22,str(r['required_staff']),8.5,c=BLUE);c.text(x,.57,f'{i+1}月',8.5)
    c.text(.3,2.1,'人数',8)
    c.text(8.5,.15,'每月标准30天；月度人数由最少人时除以120并向上取整',8.5,c=GREY)
    c.save('fig3_monthly_hours_and_staff')


def drought(result):
    regular=result['full_monthly_solutions'][7]['inverse']
    item=next(v for v in result['full_sensitivity_solutions'] if v['name']=='base_drought')
    stress=next(v for v in item['solutions'] if v['period']['month']==8)
    rr=[regular,stress['inverse']]
    c=Canvas(17,6.7);c.text(4.7,6.31,'(a) 峰值月：保持目标所需人时',11,bold=True)
    c.text(12.9,6.31,f"(b) 峰值月：固定{result['fixed_reference_staff']}人的服务分",11,bold=True)
    left=1.6; width=6.7; mx=8000
    for y,label,r in [(4.65,'常规季节',rr[0]),(3.28,'异常干旱',rr[1])]:
        c.text(left-.17,y,label,9,ha='right');start=left
        vals=[r['response_hours'],r['base_ground_hours']+r['base_drone_operator_hours'],r['fire_ground_hours']+r['fire_drone_operator_hours'],r['water_hours']]
        for val,col in zip(vals,[GREY,BLUE,GOLD,TEAL]):
            w=width*val/mx;c.rect(start,y-.27,w,.54,col);start+=w
        c.text(left,y+.59,f"{r['total_person_hours']:.2f} 人时 → {r['required_staff']}人",9,ha='left')
    for val in [0,4000,8000]:
        x=left+width*val/mx;c.text(x,2.36,str(val),8,c=GREY)
    c.text(4.7,1.97,f"参考{result['fixed_reference_staff']}人预算{result['fixed_reference_staff']*120}人时，均有余量",9,c=RED)
    for i,(col,label) in enumerate([(GREY,'响应'),(BLUE,'监测'),(GOLD,'火险'),(TEAL,'水点')]):
        xx=.95+i*1.87;c.rect(xx,1.32,.18,.13,col);c.text(xx+.27,1.385,label,8,ha='left')
    base=52.; maximum=60.; bot=2.07; hh=3.25; xl=10.3; xr=16.4
    def yy(v):return bot+hh*(v-base)/(maximum-base)
    for v in [52,54,56,58,60]:
        y=yy(v);c.line([(xl,y),(xr,y)],'#e0e6ea',.35);c.text(xl-.17,y,str(v),8.5,ha='right',c=GREY)
    eta=result['target_score'];y=yy(eta);c.line([(xl,y),(xr,y)],GREY,.9,dashed=True)
    c.text(xr,5.65,f'目标 {eta:.2f}分',9,c=GREY,ha='right')
    scores=[result['monthly'][7]['fixed_reference_score'],stress['fixed_reference']['score']]
    for x,score,col,label in zip([11.8,14.9],scores,[BLUE,RED],['常规季节','异常干旱']):
        c.rect(x-.46,bot,.92,yy(score)-bot,col);c.text(x,yy(score)+.17,f'{score:.2f}',10,c=col,bold=True);c.text(x,bot-.32,label,9)
    c.text(13.2,1.4,'纵轴从52分起；虚线为目标',8.5,c=GREY)
    c.rect(.5,.35,16,.68,PALE)
    c.text(8.5,.68,'水点人时422.34 → 980.68；所需人数57 → 62；177人参考配置仍可维持目标',9.5)
    c.save('fig4_drought_workload_and_service')


def main():
    OUT.mkdir(parents=True,exist_ok=True);drawing.OUT=OUT
    paths=['output/question2/q2_model_inputs.json','output/question2/q2_results.json','output/question3/q3_results.json','data/question3/processed/water_points.json','data/modeling/q3_assumptions.json']
    before={p:sha(p) for p in paths}
    data=read(paths[0]); result=read(paths[2]); water=read(paths[3]); ass=read(paths[4])
    pipeline(result); evidence=water_map(data,water,ass);monthly(result);drought(result)
    assert before=={p:sha(p) for p in paths}
    manifest={'source_sha256':before,'water_evidence':evidence,'figures':[
        {'number':'3-1','name':'fig1_monthly_model_pipeline'},
        {'number':'3-2','name':'fig2_water_points_and_workload'},
        {'number':'3-3','name':'fig3_monthly_hours_and_staff'},
        {'number':'3-4','name':'fig4_drought_workload_and_service'}],
        'formats':['png','svg','tikz'],'same_primitives_for_all_formats':True,
        'references':['PAWS 2016 Figure 5: modular flow','Community patrol 2025 Figure 3: spatial and budget multipanel comparison']}
    (OUT/'figure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Wrote four PNG/SVG/TikZ figure sets; saved scientific inputs unchanged.')


if __name__=='__main__':main()
