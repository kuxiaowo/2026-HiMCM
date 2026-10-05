"""Draw Q2 paper figures from saved inputs/results, with self-contained TikZ.

The same geometric primitives drive PNG/SVG and TikZ. No new observations,
weights or resource scenarios are introduced by this presentation script.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, font_manager, colors
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, PathPatch
from matplotlib.path import Path as MplPath
from shapely.geometry import shape
from shapely.ops import transform
from build_question2 import FWD, load_geometry, polygons

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question2/paper_figures'
BLUE='#235e83';GOLD='#d99736';RED='#a33b34';INK='#263746';GREY='#83919d';PALE='#eef3f6'
FONT=font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc').get_name()
plt.rcParams.update({'font.family':FONT,'axes.unicode_minus':False,'svg.fonttype':'path'})

def textext(s):
    repl={'\\':r'\textbackslash{}','{':r'\{','}':r'\}','$':r'\$','&':r'\&','#':r'\#','_':r'\_','%':r'\%'}
    def esc(z):return ''.join(repl.get(c,c) for c in z)
    return ''.join(z if z.startswith('$') else esc(z) for z in re.split(r'(\$[^$]+\$)',s)).replace('\n',r'\\')

def tc(c):
    r,g,b=colors.to_rgb(c)
    return '{rgb,1:red,%.5f;green,%.5f;blue,%.5f}'%(r,g,b)

class Canvas:
    def __init__(self,w,h):self.w=w;self.h=h;self.items=[]
    def text(self,x,y,s,size=10,c=INK,ha='center',va='center',bold=False):self.items.append(('text',x,y,s,size,c,ha,va,bold))
    def rect(self,x,y,w,h,fill=PALE,edge=None,lw=.6):self.items.append(('rect',x,y,w,h,fill,edge,lw))
    def line(self,xy,c=INK,lw=.8,dashed=False,arrow=False):self.items.append(('line',xy,c,lw,dashed,arrow))
    def circle(self,x,y,r,fill=BLUE,edge=None,lw=.5):self.items.append(('circle',x,y,r,fill,edge,lw))
    def poly(self,rings,fill,edge='white',lw=.45):self.items.append(('poly',rings,fill,edge,lw))
    def star(self,x,y,r=.15,fill=RED):
        # Draw a vector star instead of a Unicode glyph; Latin Modern lacks U+2605.
        angles=np.pi/2+np.arange(10)*np.pi/5
        radii=np.where(np.arange(10)%2==0,r,.42*r)
        ring=np.column_stack([x+radii*np.cos(angles),y+radii*np.sin(angles)])
        self.poly([np.vstack([ring,ring[0]])],fill,fill,.1)
    def save(self,name):
        fig,ax=plt.subplots(figsize=(self.w/2.54,self.h/2.54));fig.subplots_adjust(0,0,1,1)
        ax.set_xlim(0,self.w);ax.set_ylim(0,self.h);ax.set_aspect('equal');ax.axis('off')
        tikz=[r'\begin{tikzpicture}[x=1cm,y=1cm]',f'\\path[use as bounding box] (0,0) rectangle ({self.w},{self.h});']
        for z in self.items:
            kind=z[0]
            if kind=='text':
                _,x,y,s,fs,c,ha,va,bold=z
                ax.text(x,y,s,fontsize=fs,color=c,ha=ha,va=va,weight='bold' if bold else 'normal')
                anchor={'left':'west','right':'east','center':'center'}[ha]
                font='\\fontsize{%g}{%g}\\selectfont%s'%(fs,fs*1.18,r'\bfseries' if bold else '')
                tikz.append('\\node[anchor=%s,align=%s,text=%s,font={%s}] at (%.4f,%.4f) {%s};'%(anchor,ha,tc(c),font,x,y,textext(s)))
            elif kind=='rect':
                _,x,y,w,h,fill,edge,lw=z
                ax.add_patch(Rectangle((x,y),w,h,facecolor=fill,edgecolor=edge or 'none',linewidth=lw))
                tikz.append('\\path[fill=%s,draw=%s,line width=%gpt] (%.4f,%.4f) rectangle (%.4f,%.4f);'%(tc(fill),tc(edge) if edge else 'none',lw,x,y,x+w,y+h))
            elif kind=='circle':
                _,x,y,r,fill,edge,lw=z;ax.add_patch(Circle((x,y),r,facecolor=fill,edgecolor=edge or 'none',linewidth=lw))
                tikz.append('\\path[fill=%s,draw=%s,line width=%gpt] (%.4f,%.4f) circle (%.4f);'%(tc(fill),tc(edge) if edge else 'none',lw,x,y,r))
            elif kind=='line':
                _,xy,c,lw,dashed,arrow=z;xy=np.asarray(xy)
                ax.plot(xy[:,0],xy[:,1],color=c,lw=lw,ls='--' if dashed else '-')
                if arrow:ax.add_patch(FancyArrowPatch(xy[-2],xy[-1],arrowstyle='-|>',mutation_scale=9,color=c,lw=lw))
                opts=['draw='+tc(c),'line width=%gpt'%lw]
                if dashed:opts.append('dashed')
                if arrow:opts.append('-{Latex[length=1.7mm]}')
                tikz.append('\\draw[%s] %s;'%(','.join(opts),' -- '.join('(%.4f,%.4f)'%tuple(p) for p in xy)))
            elif kind=='poly':
                _,rings,fill,edge,lw=z;vertices=[];codes=[]
                for ring in rings:
                    vertices.extend(ring);codes.extend([MplPath.MOVETO]+[MplPath.LINETO]*(len(ring)-2)+[MplPath.CLOSEPOLY])
                ax.add_patch(PathPatch(MplPath(vertices,codes),facecolor=fill,edgecolor=edge,lw=lw))
                chunks=[' -- '.join('(%.4f,%.4f)'%tuple(p) for p in ring[:-1])+' -- cycle' for ring in rings]
                tikz.append('\\path[even odd rule,fill=%s,draw=%s,line width=%gpt] %s;'%(tc(fill),tc(edge),lw,' '.join(chunks)))
        tikz.append(r'\end{tikzpicture}')
        fig.savefig(OUT/(name+'.png'),dpi=240,facecolor='white');fig.savefig(OUT/(name+'.svg'),facecolor='white');plt.close(fig)
        (OUT/(name+'.tikz')).write_text('\n'.join(tikz)+'\n',encoding='utf-8')

def flow():
    c=Canvas(17,5.9)
    for x,title,detail in [(0.3,'空间与对象数据','17父区 · 599检查单元'),(6.15,'需求与作业参数','权重、成本、响应门槛'),(12,'配置与核验','人时、机时、服务完成率')]:
        c.rect(x,4.6,4.7,.95,BLUE);c.text(x+2.35,5.25,title,12,'white',bold=True);c.text(x+2.35,4.81,detail,9,'white')
    for xx in [(5.05,6.05),(10.9,11.9)]:c.line([(xx[0],5.1),(xx[1],5.1)],GREY,1,arrow=True)
    for x,y,text in [(0.3,3.05,'动物 / 生境责任数据'),(0.3,1.9,'道路与技术适用数据'),(6.15,3.05,'责任 × 进入条件 → 熵权'),(6.15,1.9,'路线 → 人时 / 机时成本')]:
        c.rect(x,y,4.7,.75,PALE);c.text(x+2.35,y+.375,text,10)
    for y in [3.425,2.275]:c.line([(5.05,y),(6.05,y)],GREY,.85,arrow=True)
    c.rect(12,2.48,4.7,1.05,'#f6e7cf');c.text(14.35,3.01,'线性规划：最大化服务分',10,bold=True)
    c.rect(12,.85,4.7,.8,PALE);c.text(14.35,1.25,'资源上限 + 区域服务底线',10)
    c.line([(10.85,3.425),(11.4,3.425),(11.4,3.2),(11.9,3.2)],GREY,.85,arrow=True)
    c.line([(10.85,2.275),(11.4,2.275),(11.4,2.8),(11.9,2.8)],GREY,.85,arrow=True)
    c.line([(14.35,1.7),(14.35,2.43)],GOLD,.9,arrow=True)
    c.text(8.5,.32,'目标：有限资源下的战略部署；服务评分需要地面响应支持',10,c=GREY)
    c.save('fig1_model_pipeline')

def weights(data,report):
    rows=sorted(report['regions'],key=lambda r:r['demand_weight'],reverse=True);alpha=data['management_weight_estimation']['weights']
    c=Canvas(17,10.1);left=3.1;width=11.9;top=8.9;dy=.46;maxv=.22
    c.text(8.5,9.73,'各区域需求权重的两分项构成',12,bold=True)
    for v in [0,.05,.10,.15,.20]:
        x=left+width*v/maxv;c.line([(x,.93),(x,9.05)],'#e0e5e9',.4);c.text(x,.58,f'{v*100:g}',9,c=GREY)
    for i,r in enumerate(rows):
        rid=r['region_id'];ts=[t for t in data['targets'] if t['region_id']==rid]
        a=alpha[0]*sum(t['animal_component_share'] for t in ts);f=alpha[1]*sum(t['habitat_component_share'] for t in ts)
        assert abs(a+f-r['demand_weight'])<1e-12
        y=top-i*dy;label=rid if rid.startswith('ENP') else ('盐沼*' if rid=='PAN_MAIN' else '调查外其他*')
        c.text(left-.23,y,label,9.5,ha='right')
        c.rect(left,y-.14,width*a/maxv,.28,BLUE);c.rect(left+width*a/maxv,y-.14,width*f/maxv,.28,GOLD)
        c.text(left+width*(a+f)/maxv+.18,y,f'{100*(a+f):.2f}',9,ha='left')
    c.rect(3.1,9.12,.27,.17,BLUE);c.text(3.5,9.205,'动物责任 × 进入条件',9.5,ha='left')
    c.rect(9.2,9.12,.27,.17,GOLD);c.text(9.6,9.205,'可燃生境责任',9.5,ha='left')
    c.text(8.5,.27,'需求权重 / %；*动物资料未知，未纳入动物分项',9,c=GREY)
    c.save('fig2_demand_composition')

def maps(data,report):
    geom=load_geometry();rows={r['region_id']:r for r in report['regions']}
    xmin=min(g.bounds[0] for _,g in geom);xmax=max(g.bounds[2] for _,g in geom)
    ymin=min(g.bounds[1] for _,g in geom);ymax=max(g.bounds[3] for _,g in geom)
    c=Canvas(17,5.65);cm=plt.get_cmap('Blues');scale=min(7.8/(xmax-xmin),4.75/(ymax-ymin))
    roads=json.loads((ROOT/'data/roads/processed/park_edges.geojson').read_text(encoding='utf-8'))['features']
    for panel,key,title,maxv in [(0,'demand_weight','(a) 区域需求权重',.20),(1,'service_completion_fraction','(b) 基准服务与响应条件',1.)]:
        x0=.45+8.45*panel;y0=1.55
        def xy(a):return np.array([[x0+(x-xmin)*scale,y0+(y-ymin)*scale] for x,y in a])
        c.text(x0+3.9,5.29,title,11,bold=True)
        c.line([(x0+.5,4.47),(x0+.5,4.85)],INK,.8,arrow=True);c.text(x0+.5,5.02,'N',7.5)
        for rid,g in geom:
            fill=colors.to_hex(cm(.08+.85*np.clip(rows[rid][key]/maxv,0,1)))
            for p in polygons(g.simplify(450,preserve_topology=True)):
                if p.area<2e5:continue
                rings=[xy(p.exterior.coords)]+[xy(interior.coords) for interior in p.interiors]
                c.poly(rings,fill,'white',.3)
        if panel==0:
            for f in roads:
                g=transform(FWD,shape(f['geometry'])).simplify(200)
                if g.geom_type=='LineString':c.line(xy(g.coords),'#7d8b95',.16)
        else:
            for t in data['targets']:
                if not t['response_eligible']:
                    x,y=xy([FWD(t['lon'],t['lat'])])[0];c.circle(x,y,.018,RED)
        for rid,g in geom:
            p=g.representative_point();x,y=xy([(p.x,p.y)])[0]
            label=rid.replace('ENP','').replace('PAN_MAIN','盐沼').replace('UNSURVEYED_OTHER','其他*')
            if rid=='ENP16':x-=.20;y-=.10
            c.text(x,y,label,7.5,c=INK)
        for b in data['bases']:
            x,y=xy([FWD(b['lon'],b['lat'])])[0];c.star(x,y)
        # A scale bar uses the same UTM coordinates as route planning.
        c.line([(x0+.3,1.02),(x0+.3+50000*scale,1.02)],INK,1.2);c.text(x0+.3+25000*scale,.81,'50 km',8.5)
        for i in range(8):c.rect(x0+2.8+i*.43,1.00,.43,.16,colors.to_hex(cm(.08+.85*i/7)))
        c.text(x0+2.8,.76,'0',8,c=GREY);c.text(x0+6.24,.76,f'{maxv*100:g}%',8,c=GREY)
    c.text(8.5,.32,'星号：六处候选驻点；红点：2小时响应不可达目标；道路/边界用于规划',9,c=GREY)
    c.save('fig3_demand_response_maps')

def costs(data):
    t=next(t for t in data['targets'] if t['drone_allowed']);p=data['config'];n=p['team_size'];nu=p['drone_team_size']
    obs=p['observation_hours'];prep=p['preparation_hours'];walk=2*t['offroad_km']/p['walking_speed_kmh'];fly=t['flight_hours_per_check']
    road=t['ground_hours_per_check']/n-walk-obs-prep
    ground=[n*road,n*walk,n*obs,n*prep];drone=[nu*road,0,nu*fly,nu*prep]
    assert abs(sum(ground)-t['ground_hours_per_check'])<1e-10 and abs(sum(drone)-t['operator_hours_per_check'])<1e-10
    c=Canvas(17,6.15);c.text(4.25,5.7,'(a) 人员与无人机作业结构',11,bold=True);c.text(12.9,5.7,'(b) 同一单元的单次人时',11,bold=True)
    # Simple original vector symbols: base, deployment point, target and drone.
    c.rect(.6,3.2,.7,.85,PALE,BLUE);c.line([(.48,4.05),(.95,4.45),(1.42,4.05)],BLUE,1);c.text(.95,2.85,'驻点',10)
    roadline=[(1.5,3.65),(2.55,3.65),(3.05,4.1),(4.2,4.1)];c.line(roadline,GREY,2,arrow=True)
    c.text(2.7,4.8,'道路往返',9,c=GREY)
    c.rect(4.22,3.82,.55,.55,GOLD);c.text(4.5,3.45,'部署点',9)
    c.circle(7.2,4.1,.1,RED);c.text(7.2,2.95,'检查点 j',9)
    c.line([(4.87,4.1),(7.03,4.1)],GOLD,1,dashed=True,arrow=True);c.text(5.95,3.72,'道路外步行',9,c=GOLD)
    c.line([(4.5,4.5),(5.55,5.1),(6.35,5.1),(7.2,4.45)],BLUE,1,arrow=True)
    for x,y in [(5.5,5.05),(5.8,5.05),(5.5,5.32),(5.8,5.32)]:c.circle(x,y,.06,BLUE)
    c.text(6.7,5.2,'飞行',9,c=BLUE)
    c.text(4.1,1.73,'人员始终承担出行、准备、操作与响应',9,c=GREY)
    c.text(4.1,1.10,'示意图不代表实际巡护轨迹',9,c=GREY)
    left=10;width=5.8;mx=5.5;palette=[BLUE,GOLD,'#76a5c3','#b9c5cf']
    for y,label,vals,total in [(4.55,'地面检查',ground,sum(ground)),(3.38,'无人机配套',drone,sum(drone))]:
        c.text(left-.18,y,label,9.5,ha='right');start=left
        for value,col in zip(vals,palette):c.rect(start,y-.2,width*value/mx,.4,col);start+=width*value/mx
        c.text(start+.15,y,f'{total:.3f}',9,ha='left')
    for k in [0,2,4]:x=left+width*k/mx;c.line([(x,2.75),(x,4.93)],'#dce3e9',.25);c.text(x,2.51,str(k),9,c=GREY)
    c.text(12.9,2.1,'人时 / 点次（2人作业组）',9)
    for i,(label,col) in enumerate(zip(['道路往返','道路外步行','观察 / 飞行操作','准备'],palette)):
        xx=9.1+(i%2)*3.6;yy=1.45-(i//2)*.45;c.rect(xx,yy-.07,.22,.14,col);c.text(xx+.33,yy,label,8.5,ha='left')
    c.text(12.9,.38,f"{t['target_id']}：另消耗 {fly:.3f} 机时/点次",9,c=GREY)
    c.save('fig4_route_and_cost')
    return {'target_id':t['target_id'],'ground_person_hours':sum(ground),'operator_person_hours':sum(drone),'flight_hours':fly,'ground_components':ground,'operator_components':drone}

def results(report):
    c=Canvas(17,7.8);c.text(4.4,7.35,'(a) 同预算部署的服务分',11,bold=True);c.text(12.7,7.35,'(b) 代表优化解的人时构成',11,bold=True)
    left=1.;bottom=1.45;height=4.8;ymax=70
    for v in [0,20,40,60]:y=bottom+height*v/ymax;c.line([(left,y),(7.85,y)],'#dee5eb',.4);c.text(left-.2,y,str(v),9,ha='right',c=GREY)
    for i,(b,s) in enumerate(zip(report['comparisons'],report['scarce_budget_comparisons'])):
        x=1.65+i*2.05
        for dx,result,col in [(-.35,b['result'],BLUE),(.35,s['result'],GOLD)]:
            val=result['score'];h=height*val/ymax;c.rect(x+dx-.25,bottom,.5,h,col);c.text(x+dx,bottom+h+.2,f'{val:.2f}',9)
        c.text(x,bottom-.38,b['name'],9)
    cap=report['optimum']['geographic_score_upper_bound'];y=bottom+height*cap/ymax
    c.line([(left,y),(7.85,y)],RED,.9,dashed=True);c.text(4.43,6.7,f'固定响应条件上限 {cap:.2f}',9,c=RED)
    c.rect(1.5,.46,.25,.16,BLUE);c.text(1.85,.54,'基准7080人时',9,ha='left');c.rect(4.7,.46,.25,.16,GOLD);c.text(5.05,.54,'紧缺4248人时',9,ha='left')
    maxh=7080.;xl=9.75;ww=6.4
    for y,label,r in [(5.3,'基准',report['optimum']),(3.67,'紧缺',report['scarce_budget_comparisons'][-1]['result'])]:
        fixed=r['response_reserved_hours'];mobile=r['ground_hours']+r['drone_operator_hours'];idle=max(0,r['human_budget']-fixed-mobile)
        c.text(xl-.2,y,label,10,ha='right');start=xl
        for val,col in [(fixed,GREY),(mobile,BLUE),(idle,'#e4eaf0')]:
            width=ww*val/maxh;c.rect(start,y-.28,width,.56,col)
            if width>1:c.text(start+width/2,y,f'{val:.0f}',9,'white' if col!= '#e4eaf0' else GREY)
            start+=width
        c.text(xl,y-.66,f"总预算 {r['human_budget']:.0f}；使用 {r['total_person_hours']:.1f} 人时",8.5,ha='left',c=GREY)
    for i,(label,col) in enumerate([('响应预留',GREY),('监测配套人工',BLUE),('未使用预算','#e4eaf0')]):
        yy=2.05-i*.44;c.rect(10.1,yy-.08,.25,.16,col);c.text(10.5,yy,label,9,ha='left')
    c.text(13.,.72,'机时单独核算，不与人时相加',9,c=GREY)
    c.save('fig5_score_and_budget')

def regional(report):
    rows=sorted(report['regions'],key=lambda r:-r['demand_weight']);scarce={r['region_id']:r for r in report['scarce_budget_regions']}
    c=Canvas(17,10.5);c.text(8.5,10.13,'分区需求、服务和监测人工的对应关系',12,bold=True)
    columns=[('需求权重\n%',lambda r:r['demand_weight']*100,20,BLUE),('基准服务\n%',lambda r:r['service_completion_fraction']*100,100,BLUE),('紧缺服务\n%',lambda r:scarce[r['region_id']]['service_completion_fraction']*100,100,GOLD),('基准人工\n人时',lambda r:r['allocated_monitoring_person_hours'],500,BLUE),('紧缺人工\n人时',lambda r:scarce[r['region_id']]['allocated_monitoring_person_hours'],500,GOLD)]
    x0=3.4;cell=2.45;top=8.88;dy=.46
    for j,(name,func,mx,col) in enumerate(columns):c.text(x0+j*cell+cell/2,9.53,name,9.5,bold=True)
    for i,r in enumerate(rows):
        y=top-i*dy;rid=r['region_id'];label=rid if rid.startswith('ENP') else ('盐沼*' if rid=='PAN_MAIN' else '调查外其他*')
        c.text(x0-.2,y,label,9.3,ha='right')
        for j,(name,func,mx,col) in enumerate(columns):
            value=func(r);ratio=min(1,value/mx);rgb=np.array(colors.to_rgb(col));fill=colors.to_hex(1-(1-rgb)*(.06+.84*ratio))
            c.rect(x0+j*cell,y-.205,cell-.08,.41,fill)
            label=('<0.1' if 0<value<.05 else f'{value:.1f}') if j else f'{value:.2f}'
            c.text(x0+j*cell+(cell-.08)/2,y,label,9.1,'white' if ratio>.7 else INK)
    c.text(8.5,.62,'颜色在各列内表示相对强度；数值保留原单位。人工不含共享响应预留。',8.8,c=GREY)
    c.text(8.5,.2,'*动物资料未知，未加入动物分项；区域通用服务仍按可响应面积要求。',8.8,c=GREY)
    c.save('fig6_regional_matrix')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    inputs=ROOT/'output/question2/q2_model_inputs.json';resultsfile=ROOT/'output/question2/q2_results.json'
    data=json.loads(inputs.read_text(encoding='utf-8'));report=json.loads(resultsfile.read_text(encoding='utf-8'))
    assert report['excluded_factors']==['water_supply','precipitation']
    flow();weights(data,report);maps(data,report);example=costs(data);results(report);regional(report)
    meta={'status':'drawn_from_saved_solver_results','figures':6,'formats':['png','svg','tikz'],'cost_example':example,
          'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [inputs,resultsfile]},
          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'notes':['map outlines simplified only for display; model geometry unchanged','weights remain information weights, not loss probabilities','TikZ embedded in the open standalone source; no external figures needed to compile','no new observations or resource scenarios']}
    (OUT/'figure_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'figures':6,'output':str(OUT),'cost_example':example},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
