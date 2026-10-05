"""Collect cited Q3 sources and audit historical boreholes against the Q2 road graph.

Run with the dedicated conda runtime. No writes to Q2 files. Source refresh is optional.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import requests
import osmium
import networkx as nx
from shapely import STRtree
from shapely.geometry import Point, shape
from shapely.ops import transform, unary_union
from build_question2 import ROOT, FWD, SITES, dump, csvout, load_geometry

RAW=ROOT/'data/question3/raw'
PROCESSED=ROOT/'data/question3/processed'
SOURCES=[
 ('koedoe_2016.html','https://koedoe.co.za/index.php/koedoe/article/view/1329/1890','2016 paper; 2013 field observations; coordinate/type table'),
 ('koedoe_table1.png','https://koedoe.co.za/index.php/koedoe/article/viewFile/1329/1890/9949','Table1; BH borehole, A artesian spring, C contact spring'),
 ('fire_strategy_2016.pdf','https://www.meft.gov.na/files/downloads/66c_Fire%20Management_Strategy%20Final%20Version.pdf','Etosha section: early dry May-July, late dry August-November; NOT staffing rates'),
 ('meft_annual_2021_2022.pdf','https://www.meft.gov.na/files/downloads/MEFT%20Annual%20Report%202021-2022.pdf','Named Etosha waterhole solar conversion; supports pump maintenance rather than assumed water trucking'),
 ('dryad_season_2024.html','https://datadryad.org/dataset/doi:10.5061/dryad.4qrfj6qm3','Primary study defines dry May-Oct/wet Nov-Apr; only NE study area, coordinates not used')
]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def collect(refresh=False):
    def fetch(item):
        name,url,use=item; p=RAW/name
        r={'path':str(p.relative_to(ROOT)).replace('\\','/'),'url':url,'use':use}
        try:
            if refresh or not p.exists():
                headers={'Referer':'https://koedoe.co.za/index.php/koedoe/article/view/1329/1890'} if name.endswith('.png') else {}
                response=requests.get(url,headers=headers,timeout=45);response.raise_for_status()
                if name.endswith('.pdf') and not response.content.startswith(b'%PDF'): raise ValueError('Not a PDF')
                p.write_bytes(response.content)
            r.update(status='saved',bytes=p.stat().st_size,sha256=sha(p))
        except Exception as e: r.update(status='failed',error=str(e))
        return r
    with ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(fetch,SOURCES))
    p=ROOT/'data/roads/raw/namibia-261003.osm.pbf'
    rows.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'url':'https://download.geofabrik.de/africa/namibia-261003.osm.pbf','use':'Existing Q2 fixed OSM snapshot; water candidates only, not operational inventory','status':'existing','sha256':sha(p),'bytes':p.stat().st_size})
    dump(RAW/'source_manifest.json',{'checked_at_utc':datetime.now(timezone.utc).isoformat(),'sources':rows,'table_transcription':'koedoe_water_points_2013.csv: names, BH/A/C, lat/lon from Table1 image; all 42 rows; 17 BH. No chemical values used.'})
    return rows

def osm_candidates():
    regions=load_geometry(); park=unary_union([g for _,g in regions])
    class Handler(osmium.SimpleHandler):
        def __init__(self): super().__init__(); self.rows=[]
        def candidate(self,tags):
            return tags.get('natural')=='water' or tags.get('water')=='waterhole' or tags.get('man_made') in ('water_well','water_tank','reservoir_covered') or tags.get('amenity')=='watering_place'
        def add(self,typ,oid,lon,lat,tags):
            if not (13.5<lon<17.5 and -19.8<lat<-18.0):return
            if not park.covers(Point(*FWD(lon,lat))):return
            self.rows.append({'osm_type':typ,'osm_id':oid,'name':tags.get('name',''),'lon':lon,'lat':lat,'tags':tags,'operating_state':'unknown','pump_type':'unknown_without_explicit_tags'})
        def node(self,n):
            tags=dict(n.tags)
            if self.candidate(tags) and n.location.valid():self.add('node',n.id,n.location.lon,n.location.lat,tags)
        def way(self,w):
            tags=dict(w.tags)
            if self.candidate(tags):
                points=[(n.lon,n.lat) for n in w.nodes if n.location.valid()]
                if points:self.add('way',w.id,sum(x for x,y in points)/len(points),sum(y for x,y in points)/len(points),tags)
    h=Handler();h.apply_file(str(ROOT/'data/roads/raw/namibia-261003.osm.pbf'),locations=True)
    dump(PROCESSED/'osm_water_candidates.json',{'scope':'Candidate features; area centroids approximate; duplicate/natural/operational status unverified, not blindly counted as artificial pumps','features':h.rows})
    return h.rows

def router(config):
    src=ROOT/'data/roads/processed'
    edgebyid={r['edge_id']:r for r in csv.DictReader((src/'park_edges.csv').open(encoding='utf-8-sig'))}
    lines=[];edges=[];g=nx.DiGraph()
    for f in json.loads((src/'park_edges.geojson').read_text(encoding='utf-8'))['features']:
        e=edgebyid[f['properties']['edge_id']]; lines.append(transform(FWD,shape(f['geometry'])));edges.append(e)
        length=float(e['length_m'])/1000
        for u,v,allowed in [(e['u'],e['v'],e['allow_forward_by_oneway']),(e['v'],e['u'],e['allow_backward_by_oneway'])]:
            if allowed=='True' and (not g.has_edge(u,v) or length<g[u][v]['weight']):g.add_edge(u,v,weight=length)
    tree=STRtree(lines)
    def connect(p):
        i=int(tree.nearest(p));e=edges[i];line=lines[i];f=line.project(p)/line.length;length=float(e['length_m'])/1000
        ins=[];outs=[]
        if e['allow_forward_by_oneway']=='True':ins.append((e['u'],f*length));outs.append((e['v'],(1-f)*length))
        if e['allow_backward_by_oneway']=='True':ins.append((e['v'],(1-f)*length));outs.append((e['u'],f*length))
        return ins,outs,line.distance(p)/1000,i
    def distances(graph,seeds):
        temp=graph.copy();temp.add_node('__q3_source__')
        for n,c in seeds:temp.add_edge('__q3_source__',n,weight=c)
        d=nx.single_source_dijkstra_path_length(temp,'__q3_source__');d.pop('__q3_source__',None);return d
    posts=[]
    for name,oid,lon,lat in SITES:
        ins,outs,off,i=connect(Point(*FWD(lon,lat)));pen=off/config['walking_speed_kmh']*config['road_speed_kmh']
        posts.append((name,distances(g,[(n,c+pen) for n,c in outs]),distances(g.reverse(copy=False),[(n,c+pen) for n,c in ins]),i,lines[i].project(Point(*FWD(lon,lat)))/lines[i].length,off))
    def route(lon,lat):
        p=Point(*FWD(lon,lat));ins,outs,off,i=connect(p);options=[]
        for name,dout,din,bi,bfraction,boff in posts:
            to=min((dout.get(n,math.inf)+c for n,c in ins),default=math.inf)
            back=min((din.get(n,math.inf)+c for n,c in outs),default=math.inf)
            # Same-edge direct travel must also be considered; routing only via
            # endpoints can create a fictitious whole-edge detour at Olifantsrus.
            if i==bi:
                frac=lines[i].project(p)/lines[i].length;length=float(edges[i]['length_m'])/1000;e=edges[i]
                if (frac>=bfraction and e['allow_forward_by_oneway']=='True') or (frac<=bfraction and e['allow_backward_by_oneway']=='True'):to=min(to,abs(frac-bfraction)*length+boff/config['walking_speed_kmh']*config['road_speed_kmh'])
                if (bfraction>=frac and e['allow_forward_by_oneway']=='True') or (bfraction<=frac and e['allow_backward_by_oneway']=='True'):back=min(back,abs(frac-bfraction)*length+boff/config['walking_speed_kmh']*config['road_speed_kmh'])
            time=(to+back)/config['road_speed_kmh']+2*off/config['walking_speed_kmh']
            options.append((time,name,to,back))
        time,name,to,back=min(options)
        return {'base_name':name if math.isfinite(time) else None,'round_travel_hours':time if math.isfinite(time) else None,'outward_road_equivalent_km':to if math.isfinite(to) else None,'return_road_equivalent_km':back if math.isfinite(back) else None,'offroad_km':off,'road_edge_id':edges[i]['edge_id'],'road_reachable':math.isfinite(time)}
    return route

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true');args=parser.parse_args()
    RAW.mkdir(parents=True,exist_ok=True);PROCESSED.mkdir(parents=True,exist_ok=True)
    sources=collect(args.refresh);candidates=osm_candidates()
    q2=json.loads((ROOT/'output/question2/q2_model_inputs.json').read_text(encoding='utf-8'));route=router(q2['config']);regions=load_geometry()
    rows=list(csv.DictReader((RAW/'koedoe_water_points_2013.csv').open(encoding='utf-8-sig')))
    assert len(rows)==42 and sum(r['type']=='BH' for r in rows)==17
    processed=[]
    for r in rows:
        if not r['latitude']:
            processed.append({**r,'included':False,'exclusion':'source_coordinate_missing'});continue
        lon=float(r['longitude']);lat=float(r['latitude']);p=Point(*FWD(lon,lat))
        rid=next((rid for rid,g in regions if g.covers(p)),None)
        nearest=min(candidates,key=lambda c:p.distance(Point(*FWD(c['lon'],c['lat'])))) if candidates else None
        near_km=p.distance(Point(*FWD(nearest['lon'],nearest['lat'])))/1000 if nearest else None
        rr=route(lon,lat) if r['type']=='BH' and rid else {}
        processed.append({**r,'longitude':lon,'latitude':lat,'region_id':rid,**rr,'included':bool(r['type']=='BH' and rid and rr['road_reachable']),'exclusion':None if r['type']=='BH' and rid and rr['road_reachable'] else 'not_BH_or_outside_or_unroutable','nearest_osm_name':nearest['name'] if nearest else None,'nearest_osm_type':nearest['osm_type'] if nearest else None,'nearest_osm_id':nearest['osm_id'] if nearest else None,'nearest_osm_distance_km':near_km,'coordinate_year':2013,'current_pump_status':'unknown_assumed_operating_in_scenario'})
    included=[r for r in processed if r['included']]
    dump(PROCESSED/'water_points.json',{'source_doi':'10.4102/koedoe.v58i1.1329','source_year':2013,'table_count':42,'BH_count':17,'modelled_BH_count':len(included),'complete_park_inventory':False,'transcription_sha256':sha(RAW/'koedoe_water_points_2013.csv'),'source_image_sha256':sha(RAW/'koedoe_table1.png'),'route_rule':'Q2 directed road graph; independent trips; no response deadline for scheduled maintenance; same-edge correction used for NEW water trips only','points':processed})
    csvout(PROCESSED/'water_visit_routes.csv',[{k:r.get(k) for k in ['name','latitude','longitude','region_id','base_name','round_travel_hours','offroad_km','outward_road_equivalent_km','return_road_equivalent_km','nearest_osm_name','nearest_osm_distance_km','coordinate_year','current_pump_status']} for r in included])
    print(json.dumps({'source_downloads':[{k:r.get(k) for k in ['path','status','bytes','error']} for r in sources],'water_rows':len(rows),'BH':17,'modelled':len(included),'osm_candidate_features':len(candidates),'sum_round_travel_hours':sum(r['round_travel_hours'] for r in included),'max_offroad_km':max(r['offroad_km'] for r in included)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
