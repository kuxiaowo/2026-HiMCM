"""Compare Overture roads against the OSM extract; do not auto-merge gaps."""
from pathlib import Path
from collections import Counter, defaultdict
import json
from shapely.geometry import shape
from shapely.ops import transform, unary_union
from pyproj import Transformer
import geopandas as gpd

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/roads'
OUT=ROOT/'output/roads'
source=json.loads((DATA/'raw/overture_etosha_roads.geojson').read_text())
osm=json.loads((DATA/'processed/etosha_roads.geojson').read_text())
project=Transformer.from_crs(4326,32733,always_xy=True).transform
union=unary_union([transform(project,shape(r['geometry'])) for r in osm['features']])
buffers={m:union.buffer(m) for m in (20,50)}
classes=defaultdict(float);datasets=Counter();licenses=Counter();candidates=[];different={m:0.0 for m in buffers}
for row in source['features']:
    prop=row['properties'];classes[prop.get('class')]+=prop['length_km']
    for item in prop.get('sources',[]):
        datasets[item.get('dataset','UNKNOWN')]+=1;licenses[item.get('license','UNKNOWN')]+=1
    line=transform(project,shape(row['geometry']))
    for width,buffer in buffers.items():
        gap=line.difference(buffer);different[width]+=gap.length/1000
        if width==50 and gap.length>100:
            candidates.append({'type':'Feature','properties':prop|{'nonoverlap_50m_km':gap.length/1000},'geometry':row['geometry']})
report={'overture_release':'2026-09-23.1','overture_road_features':len(source['features']),
    'overture_total_road_length_km':sum(r['properties']['length_km'] for r in source['features']),
    'overture_length_by_class_km':dict(classes),'source_dataset_feature_mentions':dict(datasets),
    'licenses_in_feature_sources':dict(licenses),'nonoverlap_with_osm_all_highways_km':different,
    'segments_with_more_than_100m_nonoverlap_at_50m':len(candidates),
    'nonoverlap_is_review_candidate_not_certified_missing_road':True,
    'independence_note':'Most local Overture sources are also OpenStreetMap; not independent proof of completeness.'}
(DATA/'processed/overture_roads.geojson').write_text(json.dumps(source),encoding='utf-8')
(DATA/'processed/overture_review_candidates.geojson').write_text(json.dumps({'type':'FeatureCollection','features':candidates}),encoding='utf-8')
(OUT/'overture_crosscheck.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for filename,layer in [('overture_roads.geojson','overture_crosscheck_roads'),('overture_review_candidates.geojson','overture_review_candidates')]:
    rows=json.loads((DATA/'processed'/filename).read_text())['features']
    cleaned=[]
    for row in rows:
        prop=dict(row['properties']);parts=prop.pop('sources',[]);prop.pop('connectors',None)
        prop['source_datasets']=';'.join(sorted({s.get('dataset','UNKNOWN') for s in parts}))
        prop['source_licenses']=';'.join(sorted({s.get('license','UNKNOWN') for s in parts}))
        cleaned.append({'type':'Feature','properties':prop,'geometry':row['geometry']})
    if cleaned:gpd.GeoDataFrame.from_features(cleaned,crs=4326).to_file(OUT/'etosha_roads.gpkg',layer=layer,driver='GPKG',engine='pyogrio')
print(json.dumps(report,indent=2),flush=True)
