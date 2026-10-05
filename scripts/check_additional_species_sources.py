"""Retrieve primary-source cross-checks without replacing existing downloads."""
import hashlib
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "species" / "raw"
SOURCES = [
    ("namibia_elephant_cites_cop20_2025_query", "https://cites.org/sites/default/files/documents/COP/20/prop/E-CoP20-Prop-13.pdf?gtranslate=zh-CN"),
    ("nature_conservation_regulations_gn115_2026", "https://www.lac.org.na/laws/2026/8877.pdf"),
    ("african_elephant_database_etosha_2015", "https://forest.africanelephantdatabase.org/population_submissions/722"),
]

def retrieve(source):
    name, url = source
    item = {"name": name, "url": url}
    try:
        response = requests.get(url, timeout=22)
        item.update(status=response.status_code, final_url=response.url,
                    content_type=response.headers.get("Content-Type", ""), bytes=len(response.content))
        if response.status_code == 200:
            suffix = ".pdf" if response.content.startswith(b"%PDF") else ".html"
            target = RAW / (name + suffix)
            target.write_bytes(response.content)
            item.update(local_file=str(target), sha256=hashlib.sha256(response.content).hexdigest())
    except requests.RequestException as error:
        item["error"] = str(error)
    return item

with ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(retrieve, SOURCES))
(ROOT / "output" / "model1" / "additional_species_source_checks.json").write_text(
    json.dumps({"date": "2026-10-05", "files": results}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))
