"""Retrieve an additional public road source with spatial predicate pushdown."""
import json
import gzip
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import duckdb
from shapely import from_wkb
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/roads/raw'
OUT=ROOT/'data/roads/processed'
catalog=RAW/'overture_files.json'
if not catalog.exists():
    response=requests.get('https://overturemaps-us-west-2.s3.amazonaws.com/',
        params={'list-type':'2','prefix':'release/2026-09-23.1/theme=transportation/type=segment/'},timeout=30)
    response.raise_for_status();root=ET.fromstring(response.text)
    ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
    items=[{'key':x.find('s:Key',ns).text,'size':int(x.find('s:Size',ns).text)} for x in root.findall('s:Contents',ns)]
    catalog.write_text(json.dumps(items),encoding='utf-8')
items=json.loads(catalog.read_text())
paths=['https://overturemaps-us-west-2.s3.amazonaws.com/'+r['key'] for r in items if r['key'].endswith('.parquet')]
boundary=shape(json.loads((OUT/'park_boundary.geojson').read_text())['features'][0]['geometry'])
xmin,ymin,xmax,ymax=boundary.bounds
con=duckdb.connect()
extension_dir=ROOT/'tmp/roads_duckdb_extensions'
extension_dir.mkdir(parents=True,exist_ok=True)
con.execute("SET extension_directory='"+str(extension_dir).replace("'","''")+"'")
platform=con.execute('PRAGMA platform').fetchone()[0]
extension=extension_dir/'httpfs.duckdb_extension'
if not extension.exists():
    extension_url=f'https://extensions.duckdb.org/v{duckdb.__version__}/{platform}/httpfs.duckdb_extension.gz'
    response=requests.get(extension_url,timeout=(20,90))
    response.raise_for_status()
    extension.write_bytes(gzip.decompress(response.content))
con.execute("LOAD '"+str(extension).replace("'","''")+"'")
con.execute('SET threads=4')
con.execute("SET memory_limit='1GB'")
query=f"""SELECT id, class, subtype, geometry,
    to_json(sources) AS sources_json, to_json(connectors) AS connectors_json
    FROM read_parquet({repr(paths)}, union_by_name=true)
    WHERE bbox.xmin <= {xmax} AND bbox.xmax >= {xmin}
      AND bbox.ymin <= {ymax} AND bbox.ymax >= {ymin} AND subtype='road'
"""
print('Reading spatially filtered Overture data (128 remote partitions; not downloading the global dataset).',flush=True)
rows=con.execute(query).fetchall()
proj=Transformer.from_crs(4326,32733,always_xy=True).transform
park=transform(proj,boundary)
features=[]
for identity,roadclass,subtype,wkb,sources,connectors in rows:
    geom=from_wkb(bytes(wkb))
    if not geom.intersects(boundary):continue
    clipped=geom.intersection(boundary)
    if clipped.is_empty:continue
    length=transform(proj,clipped).length/1000
    if length<.00001:continue
    features.append({'type':'Feature','properties':{'overture_id':identity,'class':roadclass,'subtype':subtype,
       'length_km':length,'sources':json.loads(sources),'connectors':json.loads(connectors),
       'release':'2026-09-23.1'},'geometry':mapping(clipped)})
(RAW/'overture_etosha_roads.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features}),encoding='utf-8')
summary={'release':'2026-09-23.1','bbox_rows':len(rows),'park_features':len(features),
         'park_length_km':sum(f['properties']['length_km'] for f in features),'query':query}
(RAW/'overture_query_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='query'},indent=2),flush=True)
