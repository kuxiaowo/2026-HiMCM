"""Archive the primary sources used in Q6; all outputs stay in the project."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/question6/raw'
SOURCES = [
    ('chitwan_unesco.html', 'https://whc.unesco.org/en/list/284', 'UNESCO', 'Protected objects and habitats; no numerical planning weights'),
    ('chitwan_management_2013_2017.pdf', 'https://faolex.fao.org/docs/pdf/nep220147.pdf', 'Chitwan National Park; FAO FAOLEX archive', 'Historical management plan, 2013-2017; monsoon, threats and management'),
    ('chitwan_unesco_decision_2025.html', 'https://whc.unesco.org/en/decisions/8736/', 'UNESCO', '2025 decision: anti-poaching and causes of rhino mortality'),
    ('yellowstone_rules.html', 'https://www.nps.gov/yell/learn/management/lawsandpolicies.htm', 'US National Park Service', 'Written approval exception for UAS; public and official road access differ'),
    ('yellowstone_conditions.html', 'https://www.nps.gov/yell/planyourvisit/conditions.htm', 'US National Park Service', 'Seasonal public road access and snow travel; not a ranger mobility log'),
    ('yellowstone_visitor_use.html', 'https://www.nps.gov/yell/learn/management/visitor-use.htm', 'US National Park Service', 'Spatial concentration of visitation and monitoring evidence'),
    ('yellowstone_reports.html', 'https://www.nps.gov/yell/learn/science-publications-reports.htm', 'US National Park Service', 'Calibration sources: wildlife monitoring, GIS and visitor use reports'),
    ('yellowstone_wolf.html', 'https://www.nps.gov/yell/learn/management/wolf.htm', 'US National Park Service', 'Species-specific monitoring and visitor interaction'),
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for filename, url, owner, use in SOURCES:
        path = OUT / filename
        record = dict(file=path.relative_to(ROOT).as_posix(), url=url, publisher=owner, use=use)
        try:
            response = requests.get(url, timeout=45, headers={'User-Agent': 'HiMCM research source archive/1.0'})
            response.raise_for_status()
            if filename.endswith('.pdf') and not response.content.startswith(b'%PDF'):
                raise ValueError('Response is not a PDF')
            path.write_bytes(response.content)
            record.update(status='archived', sha256=hashlib.sha256(response.content).hexdigest(), bytes=len(response.content), final_url=response.url)
        except Exception as exc:
            record.update(status='download_failed', error=str(exc))
        records.append(record)
        print(filename, record['status'], flush=True)
    (OUT / 'source_manifest.json').write_text(json.dumps(dict(retrieved_at=datetime.now(timezone.utc).isoformat(), sources=records), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
