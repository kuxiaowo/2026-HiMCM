"""Actual GIS inputs plus explicitly assumed service parameters for Q6.

This is a terrestrial-area service submodel, not a calibrated species score
or the actual staffing requirement of either park.
"""
from pathlib import Path
import json, math, hashlib, csv
import numpy as np
import networkx as nx
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize
from rasterio.windows import from_bounds, transform as window_transform
from shapely.geometry import shape,mapping,Point,LineString,box
from shapely.ops import transform,unary_union
from shapely import STRtree
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.optimize import linprog

ROOT=Path(__file__).resolve().parents[2]; RAW=ROOT/'data/question6/raw'; GEO=ROOT/'data/question6/processed';OUT=ROOT/'output/question6'
CONF=dict(effective_hours_month=120,vehicle_speed_kmh=30,walk_speed_kmh=4,dispatch_hours=1/6,observation_hours=1/6,preparation_hours=1/12,team_size=2,response_limit_hours=2,checks_per_100km2_month=8,service_floor=.15,baseline_target_fraction=.9,response_staff_per_site=2,hours_day=8,days_month=30,drone_budget=0,raster_resolution_m=100)
CRS={'chitwan':32645,'yellowstone':32612}
TILES={'chitwan':['N27E081','N27E084'],'yellowstone':['N42W114','N42W111','N45W114','N45W111']}
LABELS={'chitwan':'奇特旺','yellowstone':'黄石'}
def read(name):return json.loads((GEO/name).read_text(encoding='utf8'))['features']
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')

def cover(park,poly,epsg,res=100):
 p=GEO/f'{park}_worldcover_{res}m.tif'
 boundary_hash=hashlib.sha256(poly.wkb).hexdigest()
 if p.exists():
  with rasterio.open(p) as r:
   if r.tags().get('boundary_sha256')==boundary_hash:return r.read(1),r.transform
 x0,y0,x1,y1=poly.bounds;x0=math.floor(x0/res)*res;y1=math.ceil(y1/res)*res
 w=math.ceil((x1-x0)/res);h=math.ceil((y1-y0)/res);aff=rasterio.transform.from_origin(x0,y1,res,res)
 arr=np.zeros((h,w),dtype='uint8')
 for tile in TILES[park]:
  source=RAW/'worldcover'/f'ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
  with rasterio.open(source) as src:
   reproject(rasterio.band(src,1),arr,src_transform=src.transform,src_crs=src.crs,dst_transform=aff,dst_crs=epsg,src_nodata=0,dst_nodata=0,resampling=Resampling.nearest,init_dest_nodata=False,num_threads=2)
 mask=rasterize([(poly,1)],out_shape=arr.shape,transform=aff,fill=0,dtype='uint8')
 arr[mask==0]=0
 assert np.count_nonzero((mask==1)&(arr==0))==0,'Missing land-cover data inside boundary'
 with rasterio.open(p,'w',driver='GTiff',height=h,width=w,count=1,dtype='uint8',crs=epsg,transform=aff,nodata=0,compress='deflate') as dst:
  dst.write(arr,1);dst.update_tags(boundary_sha256=boundary_hash,source='ESA WorldCover 2021 v200',resampling='nearest')
 return arr,aff

def graph_roads(park,poly,fwd):
 roads=[];skipped={};scope=poly.buffer(7000)
 for f in read(park+'_roads.geojson'):
  p=f['properties']
  if park=='chitwan':
   ok=p.get('highway') in ['motorway','trunk','primary','secondary','tertiary','unclassified','residential','service','track','living_street','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'] and p.get('access') not in ['no','private'] and p.get('motor_vehicle') not in ['no','private']
  else:ok=p.get('RDSTATUS')=='Existing' and p.get('RDCLASS')!='Private'
  if not ok:continue
  g=transform(fwd,shape(f['geometry']))
  if not g.intersects(scope):continue
  # Keep complete source polylines inside extraction extent. Traffic direction
  # is not imposed because authorised response travel directions are unknown.
  gs=list(g.geoms) if g.geom_type=='MultiLineString' else [g]
  roads.extend(gs)
 segments=[];nodes={};coords=[]
 def node(xy):
  k=(round(xy[0],1),round(xy[1],1))
  if k not in nodes:nodes[k]=len(coords);coords.append(k)
  return nodes[k]
 for line in roads:
  for a,b in zip(line.coords,list(line.coords)[1:]):
   u,v=node(a),node(b);length=math.dist(a,b)
   if u!=v and length>0:segments.append((u,v,length,LineString([a,b])))
 G=nx.Graph();G.add_nodes_from(range(len(coords)))
 for u,v,L,line in segments:
  if not G.has_edge(u,v) or L<G[u][v]['weight']:G.add_edge(u,v,weight=L)
 # Close sub-metre cartographic rounding gaps only, without bridging rivers
 # or adding long invented road links.
 pairs=cKDTree(coords).query_pairs(.5)
 for u,v in pairs:G.add_edge(u,v,weight=math.dist(coords[u],coords[v]))
 lengths=unary_union(roads).intersection(poly).length/1000
 return G,segments,STRtree([s[3] for s in segments]),coords,roads,dict(in_park_road_km=lengths,source_features_used=len(roads),graph_nodes=G.number_of_nodes(),graph_edges=G.number_of_edges(),components=nx.number_connected_components(G),cartographic_links_under_half_metre=len(pairs),direction='undirected response geometry scenario; permissions not locally calibrated')

def bases(park,fwd):
 fs=read(park+'_pois.geojson')
 if park=='yellowstone':names=['Norris Ranger Station','Lake Ranger Station','South Entrance Ranger Station']
 else:
  # Specific names are selected only from observed mapped point features.
  names=['Kasara','Sauraha','Amaltari']
 points=[]
 for name in names:
  if park=='yellowstone':found=[f for f in fs if f['properties'].get('POINAME')==name]
  else:
   found=[f for f in fs if name.lower() in (f['properties'].get('name','')+' '+f['properties'].get('name:en','')).lower()]
   found.sort(key=lambda f:0 if name.lower() in [f['properties'].get('name','').lower(),f['properties'].get('name:en','').lower()] else 1 if f['properties'].get('amenity') in ['ranger_station','police'] else 2)
  assert found,(park,name)
  f=found[0];p=transform(fwd,shape(f['geometry']))
  points.append(dict(name=name,source_name=f['properties'].get('POINAME',f['properties'].get('name')),source_id=f['properties'].get('OBJECTID',f['properties'].get('osm_id')),xy=list(p.coords)[0],lonlat=f['geometry']['coordinates'],role='existing mapped location used as candidate; active response staffing not assumed observed'))
 return points

def cells(poly,arr,aff,size):
 targets=[];res=aff.a;x0,y0,x1,y1=poly.bounds
 for x in np.arange(math.floor(x0/size)*size,x1,size):
  for y in np.arange(math.floor(y0/size)*size,y1,size):
   part=poly.intersection(box(x,y,x+size,y+size))
   if part.is_empty or part.area<1:continue
   win=from_bounds(*part.bounds,transform=aff).round_offsets().round_lengths()
   row0=max(0,int(win.row_off));col0=max(0,int(win.col_off));row1=min(arr.shape[0],row0+int(win.height));col1=min(arr.shape[1],col0+int(win.width))
   block=arr[row0:row1,col0:col1];sample=block
   if sample.size:
    mask=rasterize([(part,1)],out_shape=sample.shape,transform=aff*rasterio.Affine.translation(col0,row0),dtype='uint8')
    sample=sample[(mask>0)&(sample>0)]
   if not sample.size:continue
   land=np.count_nonzero(sample!=80)/len(sample)
   if land==0:continue
   p=part.representative_point()
   rr,cc=rasterio.transform.rowcol(aff,p.x,p.y)
   if not(0<=rr<arr.shape[0] and 0<=cc<arr.shape[1]) or arr[rr,cc] in [0,80]:
    indices=np.argwhere((mask>0)&(block>0)&(block!=80))
    if len(indices):
     xs,ys=rasterio.transform.xy(aff,indices[:,0]+row0,indices[:,1]+col0)
     idx=int(np.argmin((np.asarray(xs)-p.x)**2+(np.asarray(ys)-p.y)**2));p=Point(xs[idx],ys[idx])
   # Representative point is a geometric quadrature site, not an observed
   # animal or a patrol destination. Water cells receive no terrestrial demand.
   targets.append(dict(id=f'J{len(targets)+1:04d}',x=p.x,y=p.y,area_km2=part.area/1e6,land_area_km2=part.area/1e6*land,forest_fraction=float(np.mean(sample==10)),open_fraction=float(np.mean(np.isin(sample,[20,30,60])))))
 denominator=sum(t['land_area_km2'] for t in targets)
 for t in targets:t['weight']=t['land_area_km2']/denominator;t['checks']=CONF['checks_per_100km2_month']*t['land_area_km2']/100
 return targets

def point_route(point,segments,tree,distances,speed,walk_speed=4):
 idx=int(tree.nearest(point));u,v,L,line=segments[idx];s=line.project(point);off=line.distance(point)/1000
 d=min(distances.get(u,math.inf)+s,distances.get(v,math.inf)+L-s)/1000
 return d,off

def case(park,code,label,ts,G,segments,tree,basepoints,speed,target=None):
 ds=[];snaps=[]
 for base in basepoints:
  p=Point(base['xy']);idx=int(tree.nearest(p));u,v,L,line=segments[idx];s=line.project(p);off=line.distance(p)/1000
  # Virtual source permits entry at the actual projection of the observed base.
  D={};
  for node,initial in [(u,s+off*1000*speed/CONF['walk_speed_kmh']),(v,L-s+off*1000*speed/CONF['walk_speed_kmh'])]:
   vals=nx.single_source_dijkstra_path_length(G,node,weight='weight')
   for k,val in vals.items():D[k]=min(D.get(k,math.inf),val+initial)
  ds.append(D);snaps.append(off)
 targets=[]
 for t in ts:
  options=[point_route(Point(t['x'],t['y']),segments,tree,d,speed) for d in ds]
  b=min(range(len(ds)),key=lambda i:options[i][0]);d,off=options[b]
  travel=d/speed+off/CONF['walk_speed_kmh']
  response=CONF['dispatch_hours']+travel
  eligible=math.isfinite(travel) and response<=CONF['response_limit_hours']
  cost=CONF['team_size']*(2*travel+CONF['observation_hours']+CONF['preparation_hours'])
  targets.append(dict(t,base_index=b,road_km=d if math.isfinite(d) else None,offroad_km=off,response_hours=response if math.isfinite(response) else None,eligible=eligible,cost=cost if math.isfinite(cost) else None))
 cap=100*sum(t['weight'] for t in targets if t['eligible']);reserved=len(basepoints)*CONF['response_staff_per_site']*CONF['hours_day']*CONF['days_month']
 if target is None:target=CONF['baseline_target_fraction']*cap
 weights=np.array([t['weight'] for t in targets]);costs=np.array([t['cost']*t['checks'] if t['eligible'] else 0 for t in targets]);bounds=[(CONF['service_floor'],1) if t['eligible'] else (0,0) for t in targets]
 res=linprog(costs,A_ub=[-100*weights],b_ub=[-target],bounds=bounds,method='highs')
 solved=None
 if res.success:
  human=float(res.fun+reserved);solved=dict(score=float(100*weights@res.x),patrol_hours=float(res.fun),reserved_hours=reserved,total_person_hours=human,staff_equivalent=human/120,staff_integer=math.ceil((human-1e-8)/120),s=res.x.tolist(),max_residual=max(0,float(target-100*weights@res.x)))
 return dict(park=park,id=code,label=label,speed_kmh=speed,bases=basepoints,base_snap_km=snaps,target_score=target,geographic_cap=cap,eligible_land_km2=sum(t['land_area_km2'] for t in targets if t['eligible']),unreachable_component_land_km2=sum(t['land_area_km2'] for t in targets if t['road_km'] is None),targets=targets,solution=solved,solver_status=int(res.status),reason=None if res.success else 'target exceeds conditional geographic cap')

def run():
 OUT.mkdir(parents=True,exist_ok=True);allcases=[];parks={};verification={}
 for park in CRS:
  fwd=Transformer.from_crs(4326,CRS[park],always_xy=True).transform
  poly=transform(fwd,shape(read(park+'_boundary.geojson')[0]['geometry']))
  arr,aff=cover(park,poly,CRS[park]);counts={str(v):int(np.count_nonzero(arr==v)) for v in np.unique(arr) if v}
  area=sum(counts.values())*aff.a**2/1e6;forest=counts.get('10',0)/sum(counts.values());water=counts.get('80',0)/sum(counts.values());op=sum(counts.get(str(k),0) for k in [20,30,60])/sum(counts.values())
  finecover,_=cover(park,poly,CRS[park],50);finecount=np.count_nonzero(finecover)
  covercheck=dict(resolution_m=50,forest_share=float(np.count_nonzero(finecover==10)/finecount),water_share=float(np.count_nonzero(finecover==80)/finecount),area_km2=finecount*.0025,forest_difference_pp=float(100*(np.count_nonzero(finecover==10)/finecount-forest)))
  G,segments,tree,coords,roads,meta=graph_roads(park,poly,fwd);bp=bases(park,fwd)
  size=1000 if park=='chitwan' else 2500;ts=cells(poly,arr,aff,size)
  prefix='C' if park=='chitwan' else 'Y';normal=case(park,prefix+'0','两处候选驻点，30 km/h',ts,G,segments,tree,bp[:2],30);target=normal['target_score']
  cases=[normal,case(park,prefix+'1','速度压力20 km/h',ts,G,segments,tree,bp[:2],20,target),case(park,prefix+'2','增加第三处候选驻点',ts,G,segments,tree,bp,30,target),case(park,prefix+'3','速度40 km/h',ts,G,segments,tree,bp[:2],40,target)]
  fine=case(park,prefix+'fine','半网格尺度复核',cells(poly,arr,aff,size/2),G,segments,tree,bp[:2],30,target)
  parks[park]=dict(label=LABELS[park],epsg=CRS[park],polygon_area_km2=poly.area/1e6,raster_area_km2=area,counts_100m=counts,forest_share=forest,open_share=op,water_share=water,grid_m=size,cell_count=len(ts),land_area_km2=sum(t['land_area_km2'] for t in ts),bases=bp,road_metadata=meta,landcover_resolution_check=covercheck)
  verification[park]=dict(fine_grid_m=size/2,coarse_cap=normal['geographic_cap'],fine_cap=fine['geographic_cap'],cap_difference_pp=fine['geographic_cap']-normal['geographic_cap'],fine_solution=fine['solution'],fine_target=target)
  allcases+=cases
  print(park,'area',poly.area/1e6,'forest',forest,'roads',meta,'grid',len(ts),'cases',[(c['id'],c['geographic_cap'],c['solution']['total_person_hours'] if c['solution'] else None) for c in cases],flush=True)
  dump(OUT/f'q6_{park}_fine.json',fine)
 dump(OUT/'q6_results.json',dict(status='real_geographic_inputs_with_explicit_service_assumptions',scope='terrestrial habitat service submodel; conditional geometric response bound, not calibrated park headcount',config=CONF,parks=parks,cases=allcases,grid_verification=verification))
 dump(ROOT/'data/modeling/q6_real_assumptions.json',dict(config=CONF,actual_inputs=['NPS Yellowstone boundary, roads and POIs','UNEP-WCMC WDPCA October2026 Chitwan polygon; OSM roads and mapped place anchors','ESA WorldCover 2021 v200'],assumed_inputs=['service frequency','travel speeds','dispatch and observation times','response deadline','two or three candidate bases','base reserve','service target and floor'],limitations=['Chitwan published GIS area differs materially from reported/legal area: geographic boundary calibration failed','no species distribution weights invented','no measured patrol speeds or local authorised response graph','Euclidean off-road travel ignores terrain and river detours','NPS public roads exclude operational roads; OSM incomplete','100m nearest-neighbour sampling of 10m land cover; sensitivity evaluated'],archive='output/question6/archive/synthetic_20261006'))
 with (OUT/'q6_summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['case','park','speed_kmh','bases','conditional_cap_percent','target_score','total_person_hours','conditional_staff'])
  for c in allcases:w.writerow([c['id'],c['park'],c['speed_kmh'],len(c['bases']),c['geographic_cap'],c['target_score'],c['solution']['total_person_hours'] if c['solution'] else '',c['solution']['staff_integer'] if c['solution'] else ''])
if __name__=='__main__':run()
