"""Preserve actual vector geometry; never synthesise roads or boundaries."""
from pathlib import Path
import json, requests, osmium, pyogrio
from shapely import from_wkb, to_geojson
from shapely.geometry import shape, mapping, LineString, Point
from shapely.ops import transform, unary_union, polygonize
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[2]; RAW=ROOT/'data/question6/raw';OUT=ROOT/'data/question6/processed'
OUT.mkdir(parents=True,exist_ok=True)
def save(name,fs):
 (OUT/name).write_text(json.dumps(dict(type='FeatureCollection',features=fs),ensure_ascii=False),encoding='utf8')
def feature(g,p): return dict(type='Feature',geometry=mapping(g),properties=p)

def yellowstone():
 m,f,g,fields=pyogrio.raw.read(RAW/'yellowstone_boundary/YELL_Tract_Boundary.gdb',layer='YELL_Boundary')
 poly=transform(Transformer.from_crs(m['crs'],4326,always_xy=True).transform,from_wkb(g[0]))
 save('yellowstone_boundary.geojson',[feature(poly,dict(source='NPS YELL_Boundary, IRMA 754058'))])
 roads=json.loads((RAW/'yellowstone_roads.geojson').read_text())['features']
 url='https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer/0/query'
 count=requests.get(url,params=dict(where="UNITCODE='YELL'",returnCountOnly='true',f='json'),timeout=45).json()['count']
 for offset in range(2000,count,2000):
  name=RAW/f'yellowstone_roads_page{offset//2000+1}.geojson'
  if not name.exists():
   r=requests.get(url,params=dict(where="UNITCODE='YELL'",outFields='*',outSR='4326',f='geojson',resultRecordCount=2000,resultOffset=offset),timeout=60)
   r.raise_for_status();name.write_bytes(r.content)
  roads+=json.loads(name.read_text())['features']
 assert len(roads)==count and len({f['properties']['OBJECTID'] for f in roads})==count
 save('yellowstone_roads.geojson',roads)
 pois=json.loads((RAW/'yellowstone_pois.geojson').read_text())['features']
 visitor=[f for f in pois if 'Visitor Center' in str(f['properties']['POINAME'])]
 save('yellowstone_pois.geojson',pois)
 print('YELL',poly.bounds,'roads',count,'visitor centres',[(f['properties']['POINAME'],f['geometry']) for f in visitor],flush=True)

class Nepal(osmium.SimpleHandler):
 def __init__(self):
  super().__init__();self.factory=osmium.geom.GeoJSONFactory();self.roads=[];self.areas=[];self.pois=[]
 def area(self,a):
  tags=dict(a.tags);name=tags.get('name','')+' '+tags.get('name:en','')
  if 'chit' in name.lower() and any(x in tags for x in ['boundary','leisure','protect_class']):
   try:
    g=shape(json.loads(self.factory.create_multipolygon(a)));self.areas.append(feature(g,dict(tags,osm_id=a.orig_id())))
   except Exception as e: print('area parse',str(e))
 def way(self,w):
  tags=dict(w.tags)
  if 'highway' not in tags:return
  try:
   coords=[(n.lon,n.lat) for n in w.nodes]
   if any(83.8<=x<=84.85 and 27.25<=y<=27.85 for x,y in coords):
    self.roads.append(feature(LineString(coords),dict(tags,osm_id=w.id,node_ids=[n.ref for n in w.nodes])))
  except osmium.InvalidLocationError:pass
 def node(self,n):
  if not(83.8<=n.lon<=84.85 and 27.25<=n.lat<=27.85):return
  tags=dict(n.tags);name=tags.get('name','')+' '+tags.get('name:en','')
  if 83.8<=n.lon<=84.85 and 27.25<=n.lat<=27.85 and ('kasara' in name.lower() or 'sauraha' in name.lower() or 'amaltari' in name.lower() or tags.get('amenity') in ['ranger_station','police']):
   self.pois.append(feature(Point(n.lon,n.lat),dict(tags,osm_id=n.id)))

def chitwan():
 h=Nepal()
 if all((OUT/n).exists() for n in ['chitwan_osm_boundaries.geojson','chitwan_roads.geojson','chitwan_pois.geojson']):
  h.areas=json.loads((OUT/'chitwan_osm_boundaries.geojson').read_text(encoding='utf8'))['features']
  h.roads=json.loads((OUT/'chitwan_roads.geojson').read_text(encoding='utf8'))['features']
  h.pois=json.loads((OUT/'chitwan_pois.geojson').read_text(encoding='utf8'))['features']
 else:
  h.apply_file(str(RAW/'nepal-latest.osm.pbf'),locations=True,idx='flex_mem')
  save('chitwan_osm_boundaries.geojson',h.areas);save('chitwan_roads.geojson',h.roads);save('chitwan_pois.geojson',h.pois)
 print('CNP',len(h.roads),'road features;',len(h.areas),'named area features;',len(h.pois),'candidate POIs',flush=True)
 parks=[f for f in h.areas if ('national park' in (f['properties'].get('name','')+' '+f['properties'].get('name:en','')).lower()) and 'buffer' not in f['properties'].get('name','').lower()]
 assert len(parks)==1,[(f['properties']) for f in parks]
 save('chitwan_boundary.geojson',parks)
 save('chitwan_osm_boundary.geojson',parks)
 # Use the primary UNEP-WCMC published geometry for current calculations.
 # Its reported/GIS/legal area discrepancy is retained, never normalised away.
 url='https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer/1/query'
 path=RAW/'chitwan_wdpca.json'
 if not path.exists():
  r=requests.get(url,params=dict(where='site_id=805',outFields='*',outSR=4326,f='json'),timeout=45);r.raise_for_status();path.write_bytes(r.content)
 source=json.loads(path.read_text(encoding='utf8'));m,f,g,a=pyogrio.raw.read(path)
 assert len(g)==1 and source['features'][0]['attributes']['desig_eng']=='National Park'
 save('chitwan_boundary.geojson',[feature(from_wkb(g[0]),dict(source['features'][0]['attributes'],source='UNEP-WCMC WDPCA October2026 site805; boundary-area discrepancy retained'))])

if __name__=='__main__':
 import sys
 yellowstone() if sys.argv[1]=='yellowstone' else chitwan()
