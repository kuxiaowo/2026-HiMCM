from pathlib import Path
import requests,json,time,hashlib
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/question6/raw'
query='''[out:json][timeout:60];(relation["name"~"Chitwan|Chitawan",i](27.25,83.75,27.85,84.85);way["highway"](27.3,83.8,27.8,84.8);node["name"~"Kasara|Sauraha|Amaltari",i](27.25,83.75,27.85,84.85););out geom;'''
for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
 try:
  r=requests.get(endpoint,params={'data':query},timeout=(20,100));r.raise_for_status();j=r.json()
  assert 'elements' in j
  (RAW/'chitwan_osm.json').write_bytes(r.content)
  (RAW/'chitwan_osm_manifest.json').write_text(json.dumps(dict(endpoint=endpoint,query=query,osm_base=j.get('osm3s'),elements=len(j['elements']),sha256=hashlib.sha256(r.content).hexdigest()),indent=2),encoding='utf8')
  print('Downloaded',len(j['elements']),len(r.content),flush=True)
  print([(e['type'],e['id'],e.get('tags')) for e in j['elements'] if e['type']!='way' or 'highway' not in e.get('tags',{})][:60]);break
 except Exception as e: print(endpoint,type(e).__name__,str(e)[:120],flush=True)
else: raise RuntimeError('No Overpass endpoint responded')
