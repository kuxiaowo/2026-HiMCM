"""Extract all OSM highways around Etosha; preserve OSM connectivity and restrictions.

No geometry snapping, invented links, road speeds or access permissions are applied.
Degree-two vertices of the SAME OSM way are collapsed without changing length.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import osmium
import networkx as nx
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, LineString, Point, mapping
from shapely.ops import transform
from shapely.prepared import prep
from shapely import segmentize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/roads/raw'
OUT = ROOT / 'data/roads/processed'
FIG = ROOT / 'output/roads'
for p in (OUT, FIG): p.mkdir(parents=True, exist_ok=True)
PBF = RAW / 'namibia-261003.osm.pbf'
FWD = Transformer.from_crs(4326, 32733, always_xy=True)
REV = Transformer.from_crs(32733, 4326, always_xy=True)
TAGS = ['name','ref','highway','surface','tracktype','smoothness','width','maxspeed',
        'oneway','junction','access','vehicle','motor_vehicle','motorcar','bridge',
        'tunnel','layer','seasonal','ford','construction']
MOTOR = {'motorway','motorway_link','trunk','trunk_link','primary','primary_link',
         'secondary','secondary_link','tertiary','tertiary_link','unclassified',
         'residential','living_street','service','track','road'}

def dump(path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
def features(path, rows): dump(path, {'type':'FeatureCollection','features':rows})
def csvwrite(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
def lines(geom):
    if geom.is_empty: return
    if geom.geom_type == 'LineString': yield geom
    elif hasattr(geom, 'geoms'):
        for part in geom.geoms: yield from lines(part)

boundary_path = RAW / 'etosha_osm_boundary.geojson'
if not boundary_path.exists():
    factory = osmium.geom.GeoJSONFactory()
    class Boundary(osmium.SimpleHandler):
        def area(self, a):
            if a.tags.get('name') == 'Etosha National Park':
                features(boundary_path, [{'type':'Feature','properties':{'osm_relation_id':2982497},
                                         'geometry':json.loads(factory.create_multipolygon(a))}])
    Boundary().apply_file(str(PBF), locations=True)
boundary = shape(json.loads(boundary_path.read_text())['features'][0]['geometry'])
# A long constant-latitude OSM boundary becomes curved in UTM. Densify before
# projection: transforming only sparse vertices can wrongly exclude fence roads.
park = transform(FWD.transform, segmentize(boundary, max_segment_length=0.001))
buffer = park.buffer(5000)
buffer_ll = transform(REV.transform, buffer)
prepared = prep(buffer_ll)
bbox = buffer_ll.bounds

class Extract(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.ways=[]; self.controls={}
    def node(self, n):
        tags=dict(n.tags)
        if tags.get('barrier') or tags.get('highway') in ['traffic_signals','stop','give_way']:
            if bbox[0] <= n.lon <= bbox[2] and bbox[1] <= n.lat <= bbox[3]:
                self.controls[f'osm:{n.id}']={'lon':n.lon,'lat':n.lat,'tags':tags}
    def way(self, w):
        if not w.tags.get('highway') or len(w.nodes)<2: return
        xy=[(n.lon,n.lat) for n in w.nodes]
        xs,ys=zip(*xy)
        if max(xs)<bbox[0] or min(xs)>bbox[2] or max(ys)<bbox[1] or min(ys)>bbox[3]: return
        geom=LineString(xy)
        if not prepared.intersects(geom): return
        self.ways.append({'id':w.id,'nodes':[n.ref for n in w.nodes], 'xy':xy, 'tags':dict(w.tags)})

extract=Extract(); extract.apply_file(str(PBF), locations=True)
print('Extracted buffer ways',len(extract.ways),flush=True)
control_features=[]
control_rows=[]
for node,control in extract.controls.items():
    if not buffer_ll.covers(Point(control['lon'],control['lat'])):continue
    tags=control['tags']
    row={'node_id':node,'lon':control['lon'],'lat':control['lat'],
         'barrier':tags.get('barrier',''),'name':tags.get('name',''),
         'access':tags.get('access',''),'motor_vehicle':tags.get('motor_vehicle','')}
    control_rows.append(row)
    control_features.append({'type':'Feature','properties':row,'geometry':{'type':'Point','coordinates':[control['lon'],control['lat']]}})
features(OUT/'road_control_points.geojson',control_features)
csvwrite(OUT/'road_controls.csv',control_rows,['node_id','lon','lat','barrier','name','access','motor_vehicle'])

def motor_candidate(tags):
    return tags.get('highway') in MOTOR and tags.get('motor_vehicle') != 'no' and tags.get('motorcar') != 'no' and tags.get('vehicle') != 'no'
def road_group(tags):
    h=tags.get('highway'); s=tags.get('surface','')
    if h=='construction': return 'construction'
    if not motor_candidate(tags): return 'foot_or_nonmotor'
    if s in {'asphalt','paved','concrete','concrete:plates','concrete:lanes','paving_stones','sett','cobblestone'}: return 'paved'
    if s in {'gravel','fine_gravel','pebblestone'}: return 'gravel'
    if s in {'ground','dirt','earth','sand','mud'}: return 'earth_sand'
    if s in {'unpaved','compacted','grass','grass_paver'}: return 'other_unpaved'
    return 'surface_unknown'

road_features=[]; buffer_features=[]
for way in extract.ways:
    geometry=transform(FWD.transform,LineString(way['xy']))
    props={'osm_way_id':way['id'], **{tag:way['tags'].get(tag,'') for tag in TAGS},
           'motor_candidate':motor_candidate(way['tags']), 'road_group':road_group(way['tags']),
           'source':'OpenStreetMap / Geofabrik 2026-10-03'}
    for mask,target in [(park,road_features),(buffer,buffer_features)]:
        parts=list(lines(geometry.intersection(mask)))
        if not parts: continue
        from shapely.geometry import MultiLineString
        clipped=parts[0] if len(parts)==1 else MultiLineString(parts)
        p={**props,'length_km':clipped.length/1000}
        target.append({'type':'Feature','properties':p,'geometry':mapping(transform(REV.transform,clipped))})
features(OUT/'etosha_roads.geojson',road_features)
features(OUT/'etosha_roads_buffer_5km.geojson',buffer_features)
features(OUT/'park_boundary.geojson',json.loads(boundary_path.read_text())['features'])
csvwrite(OUT/'road_inventory.csv',[f['properties'] for f in road_features],['osm_way_id',*TAGS,'motor_candidate','road_group','length_km','source'])

def build_graph(mask, stem):
    rawgraph=nx.MultiGraph(); positions={}; serial=0
    prepared_mask=prep(mask)
    for way in extract.ways:
        if not motor_candidate(way['tags']): continue
        xx,yy=FWD.transform(*zip(*way['xy'])); points=list(zip(xx,yy))
        for index,(a,b) in enumerate(zip(points,points[1:])):
            segment=LineString([a,b])
            if segment.length<.001 or not prepared_mask.intersects(segment): continue
            clipped=segment if prepared_mask.covers(segment) else segment.intersection(mask)
            for part in lines(clipped):
                if part.length<.001: continue
                coords=list(part.coords)
                if segment.project(Point(coords[0]))>segment.project(Point(coords[-1])): coords.reverse()
                ids=[]
                for endpoint in [coords[0],coords[-1]]:
                    if Point(endpoint).distance(Point(a))<.001: node=f"osm:{way['nodes'][index]}"
                    elif Point(endpoint).distance(Point(b))<.001: node=f"osm:{way['nodes'][index+1]}"
                    else: node=f"clip:{way['id']}:{endpoint[0]:.3f}:{endpoint[1]:.3f}"
                    positions[node]=endpoint;ids.append(node)
                rawgraph.add_edge(ids[0],ids[1],key=serial,way=way,u=ids[0],v=ids[1],coords=coords,length_m=part.length)
                serial+=1
    stops=set()
    for node in rawgraph:
        incident=list(rawgraph.edges(node,keys=True,data=True))
        if rawgraph.degree(node)!=2 or len({d['way']['id'] for _,_,_,d in incident})>1 or node in extract.controls or node.startswith('clip:'):
            stops.add(node)
    for component in nx.connected_components(rawgraph):
        if not stops.intersection(component): stops.add(min(component))
    visited=set(); edge_rows=[]; graph=nx.MultiGraph(); edge_features=[]
    for start in sorted(stops):
        for _,neighbor,key,data in rawgraph.edges(start,keys=True,data=True):
            if key in visited: continue
            current=start; coords=[]; length=0.; count=0; origforward=(start==data['u']); first=data
            while True:
                visited.add(key); count+=1;length+=data['length_m']
                pts=data['coords'] if current==data['u'] else list(reversed(data['coords']))
                coords.extend(pts if not coords else pts[1:]); target=data['v'] if current==data['u'] else data['u']
                if target in stops: break
                options=[(v,k,d) for _,v,k,d in rawgraph.edges(target,keys=True,data=True) if k not in visited]
                if not options: break
                current=target;neighbor,key,data=options[0]
            tags=first['way']['tags']; edge_id=f'{stem}:{len(edge_rows)+1}'
            one=tags.get('oneway','')
            if not one and tags.get('junction')=='roundabout':one='yes'
            if one in ['yes','1','true']: forward,backward=origforward,not origforward
            elif one=='-1': forward,backward=not origforward,origforward
            else: forward,backward=True,True
            row={'edge_id':edge_id,'u':start,'v':target,'osm_way_id':first['way']['id'],
                 'length_m':length, **{tag:tags.get(tag,'') for tag in TAGS},
                 'allow_forward_by_oneway':forward,'allow_backward_by_oneway':backward,
                 'access_review':tags.get('access') in ['private','no','permit','forestry','agricultural','destination'] or tags.get('motor_vehicle') in ['private','permit','forestry','agricultural','destination'],
                 'road_group':road_group(tags),'original_vertex_segments':count}
            edge_rows.append(row);graph.add_edge(start,target,key=edge_id,length_m=length)
            lon,lat=REV.transform(*zip(*coords))
            edge_features.append({'type':'Feature','properties':row,'geometry':{'type':'LineString','coordinates':list(zip(lon,lat))}})
    assert len(visited)==rawgraph.number_of_edges(),(stem,len(visited),rawgraph.number_of_edges())
    assert abs(sum(r['length_m'] for r in edge_rows)-sum(d['length_m'] for *_,d in rawgraph.edges(data=True)))<.01
    components=sorted(nx.connected_components(graph),key=lambda c:sum(d['length_m'] for *_,d in graph.subgraph(c).edges(data=True)),reverse=True)
    component_index={n:i+1 for i,c in enumerate(components) for n in c}
    node_rows=[]
    for n in sorted(graph):
        x,y=positions[n];lon,lat=REV.transform(x,y)
        control=extract.controls.get(n,{}).get('tags',{})
        node_rows.append({'node_id':n,'osm_node_id':n[4:] if n.startswith('osm:') else '',
                         'lon':lon,'lat':lat,'x_m':x,'y_m':y,'degree':graph.degree(n),
                         'component_id':component_index[n],'boundary_clip':n.startswith('clip:'),
                         'barrier':control.get('barrier',''),'control_name':control.get('name',''),
                         'control_access':control.get('access',''),'control_motor_vehicle':control.get('motor_vehicle','')})
    for row in edge_rows:row['component_id']=component_index[row['u']]
    csvwrite(OUT/f'{stem}_nodes.csv',node_rows,list(node_rows[0]))
    csvwrite(OUT/f'{stem}_edges.csv',edge_rows,list(edge_rows[0]))
    features(OUT/f'{stem}_edges.geojson',edge_features)
    lengths=[sum(d['length_m'] for *_,d in graph.subgraph(c).edges(data=True))/1000 for c in components]
    summary={'nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),'components':len(components),
             'length_km':sum(lengths),'largest_component_km':lengths[0],
             'largest_component_length_fraction':lengths[0]/sum(lengths),
             'top_10_component_lengths_km':lengths[:10], 'original_vertex_segments':rawgraph.number_of_edges()}
    print(stem,json.dumps(summary),flush=True)
    return summary

summaries={'park_motor_candidate_graph':build_graph(park,'park'), 'buffer_5km_motor_candidate_graph':build_graph(buffer,'buffer_5km')}
inventory=[f['properties'] for f in road_features]
motor=[r for r in inventory if r['motor_candidate']]
def length_groups(rows,field):
    groups=defaultdict(float)
    for r in rows:groups[r.get(field) or 'UNKNOWN']+=r['length_km']
    return dict(sorted(groups.items(),key=lambda kv:-kv[1]))
report={'source_snapshot':'2026-10-03T20:20:50Z','boundary_osm_relation_id':2982497,
        'projected_crs':'EPSG:32733','park_area_km2':park.area/1e6,
        'all_highway_way_count':len(inventory),'all_highway_length_km':sum(r['length_km'] for r in inventory),
        'motor_candidate_way_count':len(motor),'motor_candidate_length_km':sum(r['length_km'] for r in motor),
        'motor_length_by_highway_km':length_groups(motor,'highway'),
        'motor_length_by_surface_km':length_groups(motor,'surface'),
        'motor_length_by_group_km':length_groups(motor,'road_group'),
        'motor_surface_unknown_length_fraction':sum(r['length_km'] for r in motor if not r['surface'])/sum(r['length_km'] for r in motor),
        'motor_access_review_way_count':sum(r['access'] in ['private','no','permit','forestry','agricultural','destination'] for r in motor),
        'motor_maxspeed_missing_way_count':sum(not r['maxspeed'] for r in motor),
        'graphs':summaries,
        'reference_3551km_length_ratio':sum(r['length_km'] for r in motor)/3551,
        'reference_length_is_not_a_completeness_test':True,
        'boundary_projection_note':'WGS84 boundary segmentized to <=0.001 degrees before UTM projection to retain near-boundary roads.',
        'topology_rule':'Shared OSM node IDs only. No geometric snapping or inferred missing roads.',
        'routing_status':'Candidate motor network; access, barriers, season and actual speed require modelling assumptions.'}
arcgis_path=RAW/'arcgis_etosha_roads.geojson'
if arcgis_path.exists():
    arc=json.loads(arcgis_path.read_text()); current={str(r['osm_way_id']) for r in inventory}
    ids={f['properties'].get('osm_id') for f in arc.get('features',[])}
    report['arcgis_crosscheck']={'features':len(arc.get('features',[])), 'osm_ids_also_in_current_park_extract':len(ids & current),
       'osm_ids_not_in_current_park_extract':sorted(ids-current),
       'source_is_also_osm':True,'license_and_method_not_documented':True}
dump(FIG/'quality_report.json',report)

colors={'paved':'#1b3c73','gravel':'#c17d16','earth_sand':'#a44c32','other_unpaved':'#71923b',
        'surface_unknown':'#747d86','foot_or_nonmotor':'#b8aaa4','construction':'#b15f9b'}
fig,ax=plt.subplots(figsize=(15,7.5),layout='constrained')
for group,color in colors.items():
    paths=[]
    for feat in road_features:
        if feat['properties']['road_group']!=group:continue
        paths.extend([np.asarray(l.coords) for l in lines(transform(FWD.transform,shape(feat['geometry'])))])
    if paths:ax.add_collection(LineCollection(paths,colors=color,linewidths=.7 if group!='foot_or_nonmotor' else .35,label=group.replace('_',' ')))
for poly in ([park] if park.geom_type=='Polygon' else park.geoms):
    xx,yy=poly.exterior.xy;ax.plot(xx,yy,color='#172f2b',lw=1.2)
ax.set_xlim(park.bounds[0]-3000,park.bounds[2]+3000);ax.set_ylim(park.bounds[1]-3000,park.bounds[3]+3000)
ax.set_aspect('equal');ax.set_facecolor('#f7f6ef');ax.set_xlabel('UTM 33S easting (m)');ax.set_ylabel('UTM 33S northing (m)')
ax.set_title('Etosha: all mapped roads and tracks | OpenStreetMap snapshot 2026-10-03',loc='left',fontsize=14)
ax.legend(loc='lower left',fontsize=9,ncol=2,framealpha=.95)
fig.text(.99,.005,'© OpenStreetMap contributors / ODbL 1.0. Geometry coverage is not certified complete.',ha='right',fontsize=8)
fig.savefig(FIG/'etosha_road_map.png',dpi=180);plt.close(fig)
import geopandas as gpd
for filename,layer in [('park_boundary.geojson','park_boundary'),('etosha_roads.geojson','all_mapped_roads'),
                       ('park_edges.geojson','motor_candidate_edges'),('road_control_points.geojson','road_controls')]:
    gpd.read_file(OUT/filename).to_file(FIG/'etosha_roads.gpkg',layer=layer,driver='GPKG',engine='pyogrio')
print(json.dumps(report,indent=2),flush=True)
