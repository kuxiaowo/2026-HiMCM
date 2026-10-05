"""Q2: geographic planning LP. All resource/operation assumptions are explicit.

No water-point model, causal loss fitting, or claimed complete-park certification.
Point-level sorties avoid treating a regional centre as the whole region.
"""
from __future__ import annotations
import csv, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import networkx as nx
from scipy.optimize import linprog
from scipy import sparse
from scipy.stats import gamma, norm
from pyproj import Transformer
from shapely.geometry import shape, Point, box, mapping
from shapely.ops import transform
from shapely import STRtree
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, font_manager
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib.patches import Polygon

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question2'
SOURCE=ROOT/'data/roads/processed'
FWD=Transformer.from_crs(4326,32733,always_xy=True).transform
REV=Transformer.from_crs(32733,4326,always_xy=True).transform
DEFAULT={
    'grid_km':10., 'road_speed_kmh':30.,'walking_speed_kmh':4.,'entry_decay_hours':2.,
    'drone_speed_kmh':40.,'checks_per_month':8.,'service_reference_area_km2':100.,'team_size':2.,
    'drone_team_size':2.,'observation_hours':1/6,'preparation_hours':1/12,
    'dispatch_hours':1/6,'response_limit_hours':2.,'safe_flight_hours':.6,
    'minimum_open_share':.6,'minimum_reachable_service':.15,
    'staff_reference':295,'protection_staff_fraction':.2,'effective_hours_month':120.,
    'response_staff_per_site':2.,'response_hours_day':8.,'days_month':30.,
    'drone_count':6.,'flight_hours_per_drone_day':2.,'drone_days_month':20.,
    'animal_management_share':.7,
}
# Coordinates read from the project's fixed OSM snapshot. Sites are candidates,
# not evidence of current ranger posts or staffing at visitor facilities.
SITES=[
    ('Okaukuejo',2332811725,15.9193273,-19.1789091),
    ('Halali',259161898,16.4721626,-19.0355915),
    ('Namutoni',1030808189,16.9405408,-18.8058531),
    ('Olifantsrus',10837843488,14.8609827,-18.9711722),
    ('Galton Gate',5323219813,14.4824235,-19.313977),
    ('Nehale Gate',5418157935,16.7442325,-18.500941),
]

def dump(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def csvout(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def polygons(g):
    if g.geom_type=='Polygon':yield g
    elif hasattr(g,'geoms'):
        for part in g.geoms:yield from polygons(part)

def load_geometry():
    ff=json.loads((ROOT/'data/regions/processed/model_regions.geojson').read_text(encoding='utf-8'))['features']
    return [(f['properties']['region_id'],transform(FWD,shape(f['geometry']).segmentize(.001))) for f in ff]

def ahp():
    # Team judgement based on legal categories; these numerical comparisons
    # are not prescribed by law and were not elicited from external experts.
    A=np.array([[1,.5,1/3],[2,1,.5],[3,2,1]],dtype=float)
    ev,vec=np.linalg.eig(A);k=int(np.argmax(ev.real));q=np.abs(vec[:,k].real);q/=q.sum()
    cr=float((ev[k].real-3)/2/.58)
    assert cr<.1 and np.all(q>0)
    return {'category_order':['huntable','protected','specially_protected'],'judgement_matrix':A.tolist(),'category_weights':q.tolist(),'lambda_max':float(ev[k].real),'CR':cr,'status':'explicit_team_judgement_not_statutory_or_expert_weights'}

def prepare(config,sites=None):
    sites=SITES if sites is None else sites
    region_geom=load_geometry(); base=json.loads((ROOT/'output/regions/region_base_data.json').read_text(encoding='utf-8'))['regional_rows']
    byid={r['region_id']:r for r in base};audit=json.loads((ROOT/'output/model1/species_region_counts_2015.json').read_text(encoding='utf-8'))
    core=[s for s in audit['species'] if s['adoption']=='core_with_flags'];survey=[r for r in base if r['region_kind']=='survey_stratum']
    aa=ahp();q=aa['category_weights']; species_weights={}
    for s in core:
        idx=2 if s['law_class']=='specially_protected_game' else 0 if s['law_class']=='huntable_game' else 1
        species_weights[s['species_code']]=q[idx]
    totalweight=sum(species_weights.values());totals={s:sum(r['candidate_count_'+s+'_2015'] for r in survey) for s in species_weights}
    animals={r['region_id']:sum(species_weights[s]*r['candidate_count_'+s+'_2015']/totals[s] for s in totals)/totalweight for r in survey}
    assert abs(sum(animals.values())-1)<1e-10
    nodes=list(csv.DictReader((SOURCE/'park_nodes.csv').open(encoding='utf-8-sig')))
    features=json.loads((SOURCE/'park_edges.geojson').read_text(encoding='utf-8'))['features']
    edgebyid={r['edge_id']:r for r in csv.DictReader((SOURCE/'park_edges.csv').open(encoding='utf-8-sig'))}
    lines=[];edges=[];graph=nx.DiGraph()
    for feat in features:
        e=edgebyid[feat['properties']['edge_id']];line=transform(FWD,shape(feat['geometry']))
        # Preserve direction and shortest parallel edges. Baseline assumes
        # authorised management access to otherwise restricted candidates.
        length=float(e['length_m'])/1000
        for u,v,allowed in [(e['u'],e['v'],e['allow_forward_by_oneway']),(e['v'],e['u'],e['allow_backward_by_oneway'])]:
            if allowed=='True' and (not graph.has_edge(u,v) or length<graph[u][v]['weight']):graph.add_edge(u,v,weight=length,access=e['access'])
        lines.append(line);edges.append(e)
    tree=STRtree(lines)
    def connect(point):
        k=int(tree.nearest(point));line=lines[k];e=edges[k];fraction=line.project(point)/line.length;d=line.distance(point)/1000;length=float(e['length_m'])/1000
        incoming=[];outgoing=[]
        if e['allow_forward_by_oneway']=='True':incoming.append((e['u'],fraction*length));outgoing.append((e['v'],(1-fraction)*length))
        if e['allow_backward_by_oneway']=='True':incoming.append((e['v'],(1-fraction)*length));outgoing.append((e['u'],fraction*length))
        return incoming,outgoing,d,k
    def distances(g,seeds):
        temp=g.copy();temp.add_node('__source__')
        for n,cost in seeds:temp.add_edge('__source__',n,weight=cost)
        d=nx.single_source_dijkstra_path_length(temp,'__source__');d.pop('__source__',None);return d
    bases=[];outdist=[];indist=[]
    for name,osm,lon,lat in sites:
        p=Point(*FWD(lon,lat));incoming,outgoing,d,k=connect(p)
        penalty=d/config['walking_speed_kmh']*config['road_speed_kmh']
        outdist.append(distances(graph,[(n,c+penalty) for n,c in outgoing]))
        indist.append(distances(graph.reverse(copy=False),[(n,c+penalty) for n,c in incoming]))
        bases.append({'name':name,'osm_node_id':osm,'lon':lon,'lat':lat,'road_connection_km':d,'candidate_not_confirmed_ranger_post':True})
    entries=[r['node_id'] for r in nodes if r['boundary_clip']=='True' and r['node_id'] in graph]
    # Road/boundary intersections are entry candidates, not proven poacher
    # entrances. Internal gates and waterholes are not used as entry sources.
    assert entries
    entrydist=nx.multi_source_dijkstra_path_length(graph,entries)
    targetrows=[];step=config['grid_km']*1000
    for rid,region in region_geom:
        x0,y0,x1,y1=region.bounds
        for x in np.arange(math.floor(x0/step)*step,x1,step):
            for y in np.arange(math.floor(y0/step)*step,y1,step):
                piece=region.intersection(box(x,y,x+step,y+step))
                for part in polygons(piece):
                    if part.area<1:continue
                    p=part.representative_point();incoming,outgoing,offroad,edgeidx=connect(p)
                    to=np.array([min((d.get(n,math.inf)+c for n,c in incoming),default=math.inf) for d in outdist])
                    back=np.array([min((d.get(n,math.inf)+c for n,c in outgoing),default=math.inf) for d in indist])
                    response=to/config['road_speed_kmh']+offroad/config['walking_speed_kmh']+config['dispatch_hours']
                    eligible=response<=config['response_limit_hours']
                    rounds=(to+back)/config['road_speed_kmh']
                    choices=np.where(eligible,rounds,math.inf);b=int(np.argmin(choices));canrespond=bool(np.isfinite(choices[b]))
                    roundtime=float(choices[b]) if canrespond else None
                    ground=config['team_size']*(roundtime+2*offroad/config['walking_speed_kmh']+config['observation_hours']+config['preparation_hours']) if canrespond else None
                    flight=2*offroad/config['drone_speed_kmh']+config['observation_hours']
                    openness=byid[rid]['grass_share_wc2021']+byid[rid]['shrub_share_wc2021']+byid[rid]['bare_sparse_share_wc2021']
                    droneallowed=bool(canrespond and flight<=config['safe_flight_hours'] and openness>=config['minimum_open_share'])
                    operator=config['drone_team_size']*(roundtime+flight+config['preparation_hours']) if droneallowed else None
                    entrykm=min((entrydist.get(n,math.inf)+c for n,c in incoming),default=math.inf)
                    entryhours=entrykm/config['road_speed_kmh']+offroad/config['walking_speed_kmh']
                    exposure=math.exp(-entryhours/config['entry_decay_hours']) if np.isfinite(entryhours) else 0.
                    lon,lat=REV(p.x,p.y)
                    targetrows.append({'target_id':f'{rid}_{len(targetrows):04d}','region_id':rid,'lon':lon,'lat':lat,'support_area_km2':part.area/1e6,'planned_checks_month':config['checks_per_month']*(part.area/1e6)/config['service_reference_area_km2'],'within_region_area_share':part.area/region.area,'offroad_km':offroad,'entry_time_hours':float(entryhours) if np.isfinite(entryhours) else None,'entry_index':exposure,'minimum_response_hours':float(response.min()) if np.isfinite(response.min()) else None,'response_eligible':canrespond,'base_name':bases[b]['name'] if canrespond else None,'ground_hours_per_check':ground,'drone_allowed':droneallowed,'flight_hours_per_check':flight if droneallowed else None,'operator_hours_per_check':operator,'open_share':openness})
    for rid,_ in region_geom:assert abs(sum(t['within_region_area_share'] for t in targetrows if t['region_id']==rid)-1)<1e-7
    fuel_total=sum(r['fuel_proxy_baseline_area_wc2021_km2'] for r in base)
    for t in targetrows:
        rid=t['region_id']; t['animal_component_raw']=animals.get(rid,0.)*t['within_region_area_share']*t['entry_index']
        # Zero here is outside this measured-object objective component, not
        # an imputed zero animal value; retain unknown status at regional level.
        t['habitat_component_raw']=byid[rid]['fuel_proxy_baseline_area_wc2021_km2']/fuel_total*t['within_region_area_share']
    av=sum(t['animal_component_raw'] for t in targetrows);hv=sum(t['habitat_component_raw'] for t in targetrows)
    for t in targetrows:
        t['animal_component_share']=t['animal_component_raw']/av;t['habitat_component_share']=t['habitat_component_raw']/hv
        t['objective_weight']=config['animal_management_share']*t['animal_component_share']+(1-config['animal_management_share'])*t['habitat_component_share']
    H=config['staff_reference']*config['protection_staff_fraction']*config['effective_hours_month']
    H0=len(sites)*config['response_staff_per_site']*config['response_hours_day']*config['days_month']
    U=config['drone_count']*config['flight_hours_per_drone_day']*config['drone_days_month']
    result={'config':config,'AHP':aa,'bases':bases,'candidate_entry_count':len(entries),'graph_nodes':graph.number_of_nodes(),'graph_directed_arcs':graph.number_of_edges(),'targets':targetrows,'region_ids':[r for r,g in region_geom],'animal_values_15_regions':animals,'animal_unknown_regions':[r['region_id'] for r in base if r['region_kind']!='survey_stratum'],'human_budget':H,'response_reserved_hours':H0,'drone_budget':U,'scope':'daytime strategic monitoring of measured six taxa and fuel habitat; not complete park conservation certification','checks':{'region_area_shares_sum_to_one':True,'animal_values_sum_to_one':True,'objective_weights_sum_to_one':bool(abs(sum(t['objective_weight'] for t in targetrows)-1)<1e-9),'AHP_consistency_pass':True},'limitations':['Historical counts and assumed uniform within-region animal distribution','All management access to candidate roads assumed; signs, gates and seasonal closures need verification','Four camps and two gates are proposed sites, not observed ranger deployment','Area-grid representatives are inspection targets, not complete spatial coverage','Ground sorties independently return to a base; route chaining not optimised','Drone observation protocol is assumed equivalent only for screening; not arrest, firefighting or habitat restoration','Fire baseline assumes uniform exposure on fuel habitat; no multi-year fire probability estimated','Unknown rhino/bird/plant values remain outside measured objective; all reachable regions have a generic service floor','Only specified daytime response window is modelled; no 24-hour protection claim']}
    return result

def solve(data, H=None,U=None,weights=None,fixed_service=None,minimum_person=False,ground_factor=1.,operator_factor=1.):
    ts=data['targets'];n=len(ts);p=data['config'];F=np.array([t['planned_checks_month'] for t in ts])
    H=data['human_budget'] if H is None else H;U=data['drone_budget'] if U is None else U
    objective=np.zeros(3*n)
    weights=np.asarray([t['objective_weight'] for t in ts]) if weights is None else weights
    gh=np.array([t['ground_hours_per_check'] or 1 for t in ts])*ground_factor
    uh=np.array([t['flight_hours_per_check'] or 1 for t in ts])
    gamma_i=np.array([(t['operator_hours_per_check']/t['flight_hours_per_check']) if t['drone_allowed'] else 0 for t in ts])*operator_factor
    # x_j and h_j are resource hours; s_j is the completion of F planned checks.
    rows=[];cols=[];vals=[];rhs=[]
    def row(items,b):
        r=len(rhs)
        for j,v in items:rows.append(r);cols.append(j);vals.append(v)
        rhs.append(b)
    for j,t in enumerate(ts):row([(j,-1/gh[j]),(n+j,-1/uh[j]),(2*n+j,F[j])],0)
    row([(j,1.) for j in range(n)]+[(n+j,gamma_i[j]) for j in range(n)],H-data['response_reserved_hours'])
    row([(n+j,1.) for j in range(n)],U)
    for rid in data['region_ids']:
        indexes=[j for j,t in enumerate(ts) if t['region_id']==rid]
        reachable=sum(ts[j]['within_region_area_share'] for j in indexes if ts[j]['response_eligible'])
        row([(2*n+j,-ts[j]['within_region_area_share']) for j in indexes],-p['minimum_reachable_service']*reachable)
    bounds=[]
    for j,t in enumerate(ts):bounds.append((0,F[j]*gh[j] if t['response_eligible'] else 0))
    for j,t in enumerate(ts):bounds.append((0,F[j]*uh[j] if t['drone_allowed'] else 0))
    for j,t in enumerate(ts):
        bound=float(t['response_eligible'])
        bounds.append((float(fixed_service[j]),float(fixed_service[j])) if fixed_service is not None else (0,bound))
    if minimum_person:objective[:n]=1.;objective[n:2*n]=gamma_i
    else:objective[2*n:]=-weights
    mat=sparse.coo_matrix((vals,(rows,cols)),shape=(len(rhs),3*n)).tocsr()
    res=linprog(objective,A_ub=mat,b_ub=np.asarray(rhs),bounds=bounds,method='highs')
    if not res.success:return {'success':False,'status':res.status,'message':res.message}
    raw=res.x.copy();residual=float(np.max(mat@raw-np.asarray(rhs)))
    assert residual<1e-6
    x=raw[:n];h=raw[n:2*n];s=raw[2*n:]
    # Remove resource slack exactly while preserving the chosen service and
    # best score. This selects a minimum-human representative of tied optima.
    if not minimum_person and fixed_service is None:
        refined=solve(data,H,U,weights,s,True,ground_factor,operator_factor)
        if refined['success']:return refined
    return {'success':True,'status':int(res.status),'message':res.message,'score':float(100*weights@s),'ground_hours':float(x.sum()),'drone_flight_hours':float(h.sum()),'drone_operator_hours':float(gamma_i@h),'response_reserved_hours':float(data['response_reserved_hours']),'total_person_hours':float(x.sum()+gamma_i@h+data['response_reserved_hours']),'human_budget':float(H),'drone_budget':float(U),'geographic_score_upper_bound':float(100*sum(w for w,t in zip(weights,ts) if t['response_eligible'])),'constraint_max_residual':residual,'x':x.tolist(),'h':h.tolist(),'s':s.tolist()}

def heuristic(data,kind):
    ts=data['targets'];p=data['config'];eligible=np.array([t['response_eligible'] for t in ts],dtype=float)
    if kind=='area':ratio=np.ones(len(ts))
    else:
        weights={rid:sum(t['objective_weight'] for t in ts if t['region_id']==rid) for rid in data['region_ids']}
        areas={rid:sum(t['support_area_km2'] for t in ts if t['region_id']==rid) for rid in data['region_ids']}
        ratio=np.array([weights[t['region_id']]/areas[t['region_id']] for t in ts]);ratio/=max(ratio)
    lo=0.;hi=100.;best=None
    for _ in range(32):
        scale=(lo+hi)/2;service=np.maximum(p['minimum_reachable_service'],np.minimum(1,scale*ratio))*eligible
        result=solve(data,fixed_service=service,minimum_person=True)
        if result['success']:lo=scale;best=result
        else:hi=scale
    return best or {'success':False,'message':'even baseline floor infeasible'}

def regional_rows(data,result):
    rows=[];p=data['config'];ts=data['targets']
    for rid in data['region_ids']:
        ii=[j for j,t in enumerate(ts) if t['region_id']==rid];area=sum(ts[j]['support_area_km2'] for j in ii)
        s=sum(ts[j]['within_region_area_share']*result['s'][j] for j in ii)
        r=sum(ts[j]['within_region_area_share'] for j in ii if ts[j]['response_eligible'])
        op=sum(result['h'][j]*ts[j]['operator_hours_per_check']/ts[j]['flight_hours_per_check'] for j in ii if ts[j]['drone_allowed'])
        rows.append({'region_id':rid,'target_count':len(ii),'support_area_km2':area,'animal_value_2015':data['animal_values_15_regions'].get(rid),'animal_status':'unknown_not_imputed' if rid in data['animal_unknown_regions'] else 'historical_six_taxa','demand_weight':sum(ts[j]['objective_weight'] for j in ii),'response_reachable_area_fraction':r,'service_completion_fraction':s,'reachable_service_completion_fraction':s/r if r>0 else None,'ground_person_hours':sum(result['x'][j] for j in ii),'drone_flight_hours':sum(result['h'][j] for j in ii),'drone_operator_person_hours':op,'allocated_monitoring_person_hours':sum(result['x'][j] for j in ii)+op})
    return rows

def figures(data,result,comparisons,scenarios,rows):
    for name in ['msyh.ttc','simhei.ttf']:
        path=Path('C:/Windows/Fonts')/name
        if path.exists():plt.rcParams['font.family']=font_manager.FontProperties(fname=str(path)).get_name();break
    plt.rcParams['axes.unicode_minus']=False;plt.rcParams['svg.fonttype']='none'
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    def save(fig,name):
        fig.savefig(OUT/(name+'.png'),dpi=240,bbox_inches='tight',facecolor='white');fig.savefig(OUT/(name+'.svg'),bbox_inches='tight');plt.close(fig)
    geometries=load_geometry();lookup={r['region_id']:r for r in rows}
    fig,axs=plt.subplots(1,2,figsize=(14,5.5),layout='constrained')
    for ax,column,title in zip(axs,['demand_weight','service_completion_fraction'],['已知对象的规划需求权重','优化后的规定监测服务完成率']):
        patches=[];values=[]
        for rid,g in geometries:
            for poly in polygons(g):patches.append(Polygon(np.asarray(poly.exterior.coords)/1000,closed=True));values.append(lookup[rid][column]*100)
        coll=PatchCollection(patches,cmap='YlGnBu',edgecolor='white',linewidth=.6);coll.set_array(np.asarray(values));
        if column=='service_completion_fraction':coll.set_clim(0,100)
        ax.add_collection(coll);ax.autoscale_view();ax.set_aspect('equal');ax.set_title(title)
        fig.colorbar(coll,ax=ax,fraction=.035,pad=.02,label='%')
        for rid,g in geometries:
            xy=g.representative_point();label=rid.replace('ENP','').replace('PAN_MAIN','盐沼').replace('UNSURVEYED_OTHER','未调查')
            ax.text(xy.x/1000,xy.y/1000,label,ha='center',va='center',fontsize=7)
        for b in data['bases']:
            x,y=FWD(b['lon'],b['lat']);ax.scatter(x/1000,y/1000,marker='*',s=60,c='#a62d24',zorder=4)
        ax.set_xlabel('UTM东向 / km');ax.set_ylabel('UTM北向 / km')
    bad=[t for t in data['targets'] if not t['response_eligible']]
    axs[1].scatter([FWD(t['lon'],t['lat'])[0]/1000 for t in bad],[FWD(t['lon'],t['lat'])[1]/1000 for t in bad],s=6,color='#9c2626',alpha=.65,label='2小时响应不可达检查点')
    axs[1].legend(loc='upper right',fontsize=7)
    fig.suptitle('六处候选驻点、日间响应与有限资源的条件性规划结果',fontsize=13)
    save(fig,'q2_allocation_map')
    ordered=sorted(rows,key=lambda r:r['allocated_monitoring_person_hours'],reverse=True)
    fig,axs=plt.subplots(1,2,figsize=(13,5.5),layout='constrained')
    labs=[r['region_id'].replace('UNSURVEYED_OTHER','未调查').replace('PAN_MAIN','盐沼') for r in ordered]
    xx=np.arange(len(ordered));ground=np.array([r['ground_person_hours'] for r in ordered]);op=np.array([r['drone_operator_person_hours'] for r in ordered])
    axs[0].barh(xx,ground,color='#235e83',label='地面监测');axs[0].barh(xx,op,left=ground,color='#e5a34d',label='无人机配套人工')
    axs[0].set_yticks(xx,labs);axs[0].invert_yaxis();axs[0].set_xlabel('人时 / 月（另共享预留响应人时）');axs[0].legend(fontsize=8);axs[0].set_title('分区人工投入，机时另见结果表')
    names=[x['name'] for x in comparisons];scores=[x['result']['score'] for x in comparisons]
    bars=axs[1].bar(names,scores,color=['#b2b8bf','#7e9db6','#235e83'])
    for b,v in zip(bars,scores):axs[1].text(b.get_x()+b.get_width()/2,v+.7,f'{v:.2f}',ha='center')
    cap=result['geographic_score_upper_bound'];axs[1].axhline(cap,color='#a62d24',linestyle='--',label=f'固定驻点/响应条件上限 {cap:.2f}')
    axs[1].set_ylim(0,min(105,cap+12));axs[1].set_ylabel('已知对象的需求加权服务完成分');axs[1].set_title('同一资源预算下的部署比较');axs[1].legend(fontsize=8)
    save(fig,'q2_resources_and_comparison')
    feasible=[s for s in scenarios if s['result']['success']]
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained');yy=np.arange(len(feasible));v=[s['result']['score'] for s in feasible]
    ax.barh(yy,v,color='#235e83');ax.set_yticks(yy,[s['name'] for s in feasible]);ax.invert_yaxis();ax.set_xlim(0,max(v)*1.15);ax.set_xlabel('各情景自身需求权重下的规划服务分')
    for i,value in enumerate(v):ax.text(value+.5,i,f'{value:.2f}',va='center')
    ax.set_title('资源和作业假设敏感性（不同需求权重的分数不作因果比较）');save(fig,'q2_sensitivity')
    rainfall=ROOT/'output/rainfall/gpcc_regional_monthly_1971_2024.json'
    if rainfall.exists():
        rain=json.loads(rainfall.read_text(encoding='utf-8'));series=np.asarray(rain['park_monthly_mm']);years=np.arange(1972,2025)
        wet=np.array([series[(y-1971)*12-2:(y-1971)*12+4].sum() for y in years]);a,_,scale=gamma.fit(wet[:49],floc=0);spi=norm.ppf(np.clip(gamma.cdf(wet,a,scale=scale),1e-6,1-1e-6))
        fig,axs=plt.subplots(1,2,figsize=(12,3.5),layout='constrained')
        clim=np.array([series[:600][np.arange(600)%12==m].mean() for m in range(12)])
        axs[0].bar(np.arange(1,13),clim,color=['#235e83' if m in [1,2,3,4,11,12] else '#aeb9c0' for m in range(1,13)])
        axs[0].set_xticks(range(1,13));axs[0].set_xlabel('月份');axs[0].set_ylabel('全园面积加权月降水 / mm');axs[0].set_title('1971—2020固定气候基准')
        axs[1].bar(years,spi,color=np.where(spi<0,'#bf7745','#235e83'));axs[1].axhline(0,color='black',linewidth=.6);axs[1].axhline(-1,color='#a62d24',linestyle='--',linewidth=.8);axs[1].set_xlabel('完整雨季结束年份');axs[1].set_ylabel('雨季SPI-6');axs[1].set_title('降水背景；不自动增加巡护需求')
        save(fig,'q2_rainfall_context')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    configpath=ROOT/'data/modeling/q2_assumptions.json';configpath.parent.mkdir(parents=True,exist_ok=True)
    if not configpath.exists():dump(configpath,{'status':'team_planning_assumptions_not_park_observations','parameters':DEFAULT})
    config=dict(DEFAULT,**json.loads(configpath.read_text(encoding='utf-8'))['parameters'])
    dump(configpath,{'status':'team_planning_assumptions_not_park_observations','parameters':config})
    print('preparing graph and multi-point geography',flush=True);data=prepare(config);dump(OUT/'q2_model_inputs.json',data)
    csvout(OUT/'q2_targets.csv',data['targets'])
    print(f"solving {len(data['targets'])} targets; H={data['human_budget']}, U={data['drone_budget']}",flush=True)
    optimum=solve(data)
    if not optimum['success']:raise RuntimeError(json.dumps(optimum,ensure_ascii=False))
    comparisons=[{'name':'面积均衡','result':heuristic(data,'area')},{'name':'需求比例','result':heuristic(data,'demand')},{'name':'优化部署','result':optimum}]
    assert all(x['result']['success'] for x in comparisons)
    assert optimum['score']>=max(x['result']['score'] for x in comparisons)-1e-5
    scarce_H=.6*data['human_budget'];scarce_optimum=solve(data,H=scarce_H)
    scarce_data=dict(data,human_budget=scarce_H)
    scarce_comparisons=[{'name':'面积均衡','result':heuristic(scarce_data,'area')},{'name':'需求比例','result':heuristic(scarce_data,'demand')},{'name':'优化部署','result':scarce_optimum}]
    assert all(o['result']['success'] for o in scarce_comparisons)
    assert scarce_optimum['score']>=max(o['result']['score'] for o in scarce_comparisons)-1e-5
    scarce_rows=regional_rows(scarce_data,scarce_optimum);csvout(OUT/'q2_scarce_regional_allocation.csv',scarce_rows)
    scenarios=[{'name':'基准','result':optimum},
        {'name':'保护人时减少20%','result':solve(data,H=.8*data['human_budget'])},
        {'name':'保护人时减少40%','result':scarce_optimum},
        {'name':'机时减少50%','result':solve(data,U=.5*data['drone_budget'])},
        {'name':'无人机停用','result':solve(data,U=0)},
        {'name':'人时减少40%且无人机停用','result':solve(data,H=scarce_H,U=0)},
        {'name':'出行及作业人时增加25%','result':solve(data,ground_factor=1.25,operator_factor=1.25)}]
    for share in [.5,.9]:
        weights=np.array([share*t['animal_component_share']+(1-share)*t['habitat_component_share'] for t in data['targets']]);scenarios.append({'name':f'动物管理权重{share:.0%}','result':solve(data,weights=weights),'animal_management_share':share})
    geographic_scenarios=[]
    fixed_weights=np.array([t['objective_weight'] for t in data['targets']])
    for title,key,value in [('道路速度20km/h','road_speed_kmh',20.),('道路速度40km/h','road_speed_kmh',40.),('响应期限3小时','response_limit_hours',3.)]:
        print('geographic scenario '+title,flush=True)
        alt=prepare(dict(config,**{key:value}));assert [t['target_id'] for t in alt['targets']]==[t['target_id'] for t in data['targets']]
        rr=solve(alt,weights=fixed_weights);item={'name':title,'parameter':key,'value':value,'fixed_baseline_demand_weights':True,'result':rr}
        scenarios.append(item);geographic_scenarios.append(item)
    grid_sensitivity=[]
    for size in [5.,15.]:
        print(f'grid sensitivity {size}km',flush=True)
        alt=prepare(dict(config,grid_km=size));rr=solve(alt)
        grid_sensitivity.append({'grid_km':size,'target_count':len(alt['targets']),'result':rr,'scope':'discretisation sensitivity; targets differ'})
    # Enumerate three hypothetical road-node forward posts in the largest
    # unserved demand regions. Each adds reserved human hours; no free posts.
    nodes=list(csv.DictReader((SOURCE/'park_nodes.csv').open(encoding='utf-8-sig')))
    xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in nodes])
    gaps={rid:sum(t['objective_weight'] for t in data['targets'] if t['region_id']==rid and not t['response_eligible']) for rid in data['region_ids']}
    forward_options=[]
    for rid in sorted(gaps,key=gaps.get,reverse=True)[:3]:
        ts=[t for t in data['targets'] if t['region_id']==rid and not t['response_eligible']]
        if not ts:continue
        tt=max(ts,key=lambda t:t['objective_weight']);px,py=FWD(tt['lon'],tt['lat']);k=int(np.argmin(((xy-[px,py])**2).sum(axis=1)));node=nodes[k]
        newsite=('Forward_'+rid,node['node_id'],float(node['lon']),float(node['lat']))
        print('forward-post candidate '+rid,flush=True)
        alt=prepare(config,SITES+[newsite]);rr=solve(alt,weights=fixed_weights)
        forward_options.append({'target_region':rid,'candidate_region':rid,'proposed_road_node':node['node_id'],'lon':float(node['lon']),'lat':float(node['lat']),'new_reserved_person_hours':alt['response_reserved_hours']-data['response_reserved_hours'],'result':rr,'regions':regional_rows(alt,rr) if rr['success'] else None})
    successful_forward=[o for o in forward_options if o['result']['success']]
    best_forward=max(successful_forward,key=lambda o:o['result']['score']) if successful_forward else None
    rows=regional_rows(data,optimum);csvout(OUT/'q2_regional_allocation.csv',rows)
    sourcefiles=[ROOT/'output/regions/region_base_data.json',ROOT/'output/model1/species_region_counts_2015.json',SOURCE/'park_edges.csv',SOURCE/'park_edges.geojson',SOURCE/'park_nodes.csv',ROOT/'data/regions/processed/model_regions.geojson',configpath]
    report={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'scope':data['scope'],'model':'continuous LP; fixed daytime response posts; independent person/flight hours; area-weighted target service','optimum':optimum,'comparisons':comparisons,'scarce_budget_comparisons':scarce_comparisons,'scarce_budget_regions':scarce_rows,'scenarios':scenarios,'grid_sensitivity':grid_sensitivity,'forward_post_options':forward_options,'best_forward_post':best_forward,'regions':rows,'assumptions':config,'AHP':data['AHP'],'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sourcefiles},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':{'LP_optimal':True,'same_budget_baselines_feasible':True,'optimal_not_worse_than_baselines':True,'physical_resource_constraints_verified':True,'unknown_animal_values_remain_null':True,'rainfall_not_automatically_mapped_to_staff':True},'limitations':data['limitations']}
    dump(OUT/'q2_results.json',report);figures(data,optimum,comparisons,scenarios,rows)
    # Dedicated figures use the identical model with less human capacity.
    # Preserve filenames from the full-budget case and mark the scenario.
    scarce_figs=OUT/'scarce_budget';scarce_figs.mkdir(exist_ok=True)
    original_out=globals()['OUT'];globals()['OUT']=scarce_figs
    figures(scarce_data,scarce_optimum,scarce_comparisons,scenarios,scarce_rows)
    globals()['OUT']=original_out
    dump(OUT/'q2_targets_allocated.geojson',{'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[t['lon'],t['lat']]},'properties':dict(t,ground_person_hours=optimum['x'][j],drone_flight_hours=optimum['h'][j],service_completion=optimum['s'][j])} for j,t in enumerate(data['targets'])]})
    print(json.dumps({'target_count':len(data['targets']),'AHP_CR':data['AHP']['CR'],'budget':[data['human_budget'],data['drone_budget']],'geographic_limit':optimum['geographic_score_upper_bound'],'score':optimum['score'],'comparisons':{x['name']:x['result']['score'] for x in comparisons},'resources':{k:optimum[k] for k in ['ground_hours','drone_flight_hours','drone_operator_hours','response_reserved_hours','total_person_hours']},'scenarios':{x['name']:x['result'].get('score',x['result'].get('message')) for x in scenarios}},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
