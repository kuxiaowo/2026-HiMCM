"""Download public geographic evidence, with recorded provenance."""
from pathlib import Path
import requests, concurrent.futures, hashlib, json

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/question6/raw'
URLS={
 'chitwan_wdpca.json':'https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer/1/query?where=site_id%3D805&outFields=*&outSR=4326&f=json',
 'wdpca_meta.json':'https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer/1?f=pjson',
 'nepal-latest.osm.pbf':'https://download.geofabrik.de/asia/nepal-latest.osm.pbf',
 'yellowstone_tracts.zip':'https://irma.nps.gov/DataStore/DownloadFile/754059?Reference=2316784',
 'yellowstone_roads.geojson':"https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer/0/query?where=UNITCODE%3D%27YELL%27&outFields=*&outSR=4326&f=geojson&resultRecordCount=2000",
 'yellowstone_pois.geojson':"https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_POIs_Geographic/FeatureServer/0/query?where=UNITCODE%3D%27YELL%27&outFields=*&outSR=4326&f=geojson&resultRecordCount=2000",
 'roads_meta.json':'https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer/0?f=pjson',
 'pois_meta.json':'https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_POIs_Geographic/FeatureServer/0?f=pjson',
 'nps_services.json':'https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets?f=pjson',
 'chitwan_infrastructure.pdf':'https://giwmscdntwo.gov.np/media/pages/files/Final%20Report_GIS%20Database_v4olikj.pdf',
 'yellowstone_boundary.zip':'https://irma.nps.gov/DataStore/DownloadFile/754058?Reference=2316784',
 'ntnc_http.html':'http://geoportal.ntnc.org.np/layers/ntnc:Chitwan_National_Park/',
}
for tile in ['N27E081','N27E084','N42W114','N42W111','N45W114','N45W111']:
 name=f'ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
 URLS['worldcover/'+name]='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/'+name

def fetch(item):
 name,url=item
 try:
  if (RAW/name).exists() and (RAW/name).stat().st_size>1000:
   b=(RAW/name).read_bytes()
   return dict(file=name,url=url,status='cached',bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  r=requests.get(url,stream=True,timeout=(30,120)); r.raise_for_status()
  (RAW/name).parent.mkdir(parents=True,exist_ok=True); temp=RAW/(name+'.part');digest=hashlib.sha256();size=0
  with temp.open('wb') as f:
   for block in r.iter_content(1048576):f.write(block);digest.update(block);size+=len(block)
  if r.headers.get('Content-Length') and not r.headers.get('Content-Encoding'):assert size==int(r.headers['Content-Length'])
  temp.replace(RAW/name)
  return dict(file=name,url=url,status=r.status_code,bytes=size,sha256=digest.hexdigest(),type=r.headers.get('Content-Type'))
 except Exception as e: return dict(file=name,url=url,error=str(e))

if __name__=='__main__':
 results=list(concurrent.futures.ThreadPoolExecutor(6).map(fetch,URLS.items()))
 (RAW/'real_discovery_manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(results,ensure_ascii=False,indent=2))
