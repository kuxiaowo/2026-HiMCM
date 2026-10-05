"""Download public road-source data; preserve URLs, timestamps and checksums."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data' / 'roads' / 'raw'
RAW.mkdir(parents=True, exist_ok=True)
SOURCES = [
    ('namibia-261003.osm.pbf', 'https://download.geofabrik.de/africa/namibia-261003.osm.pbf'),
    ('hdx_roads_metadata.json', 'https://production-raw-data-api.s3.amazonaws.com/ISO3/NAM/roads/hotosm_nam_roads_osm_metadata.json'),
    ('arcgis_etosha_roads_item.json', 'https://www.arcgis.com/sharing/rest/content/items/f9f78bd6acef4c44902431c929337817?f=json'),
    ('arcgis_etosha_roads_service.json', 'https://services7.arcgis.com/sLjbwe0PF2weuK4o/arcgis/rest/services/Etosha_Road_Clip/FeatureServer?f=json'),
]

def download(source):
    filename, url = source
    target = RAW / filename
    if not target.exists():
        partial = target.with_suffix(target.suffix + '.part')
        with requests.get(url, stream=True, timeout=(20, 120)) as response:
            response.raise_for_status()
            with partial.open('wb') as stream:
                for block in response.iter_content(1024 * 1024):
                    stream.write(block)
        partial.replace(target)
    digest = sha256(target.read_bytes()).hexdigest()
    result = {'file': filename, 'url': url, 'bytes': target.stat().st_size,
              'sha256': digest, 'retrieved_utc': datetime.now(timezone.utc).isoformat()}
    print(json.dumps(result), flush=True)
    return result

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(download, SOURCES))
    (RAW / 'download_manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
