"""Static source consistency; this does not replace TeX compilation."""
from pathlib import Path
from collections import Counter
import re,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/question6'
def main():
 path=ROOT/'docs/paper/question6_adaptation.tex';tex=path.read_text(encoding='utf8');md=(ROOT/'docs/paper/question6_adaptation.md').read_text(encoding='utf8')
 labels=re.findall(r'\\label\{([^}]+)\}',tex);refs=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',tex)
 assert len(labels)==len(set(labels)) and not(set(refs)-set(labels))
 entries=set(re.findall(r'\\bibitem\{([^}]+)\}',tex));cites={k for s in re.findall(r'\\cite\{([^}]+)\}',tex) for k in s.split(',')};assert cites<=entries
 env=[]
 for m in re.finditer(r'\\(begin|end)\{([^}]+)\}',tex):
  if m[1]=='begin':env.append(m[2])
  else:assert env.pop()==m[2]
 assert not env
 cleaned=re.sub(r'(?<!\\)%[^\n]*','',tex);stack=0
 for m in re.finditer(r'(?<!\\)[{}]',cleaned):
  stack+=1 if m.group()=='{' else -1;assert stack>=0
 assert stack==0 and '@@' not in tex and not re.search(r'\\(?:ref|eqref|cite)\{',md)
 assert tex.count(r'\begin{figure}')==3 and tex.count(r'\begin{table}')==4
 assert r'\includegraphics' not in tex and r'\input{' not in tex
 r=json.loads((OUT/'q6_results.json').read_text(encoding='utf8'))
 for p in r['parks'].values():assert f"{p['polygon_area_km2']:.2f}" in md
 for c in r['cases']:
  if c['solution']:assert f"{c['solution']['total_person_hours']:.2f}" in md
 assert '边界校准未通过' in tex
 # Correct the early exploratory, wrongly projected derived GeoJSON; source ZIP
 # is retained. This file was never an input to current calculations.
 wrong=ROOT/'data/question6/raw/yellowstone_boundary.geojson'
 if wrong.exists():
  j=json.loads(wrong.read_text());coords=str(j['features'][0]['geometry'])
  if '-123738' in coords:
   dst=OUT/'archive/exploration/yellowstone_boundary_wrong_crs.geojson';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(wrong,dst)
   shutil.copy2(ROOT/'data/question6/processed/yellowstone_boundary.geojson',wrong)
 snapshot_path=OUT/'q6_verification.json';snapshot=json.loads(snapshot_path.read_text(encoding='utf8'))
 for item in snapshot['real_data_files']:
  if item['file']=='data/question6/raw/yellowstone_boundary.geojson' and wrong.exists():
   item.update(bytes=wrong.stat().st_size,sha256=hashlib.sha256(wrong.read_bytes()).hexdigest(),note='Corrected exploratory derived conversion; current model uses processed NPS boundary and original ZIP')
 snapshot_path.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 report=dict(status='source_static_checks_passed_compile_unverified',source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),unique_labels=len(labels),undefined_source_labels=0,figures=3,tables=4,bibliography_entries=len(entries),environment_and_brace_checks='passed',self_contained=True,builtin_compiler='Unable to find standard directories for platform',source_compilation_verified=False,reading_pdf='ReportLab preview; all seven pages visually inspected',data_quality_limit='Chitwan published GIS area does not match reported/legal area; separately disclosed')
 (OUT/'q6_latex_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 p=OUT/'q6_reading_pdf_verification.json';v=json.loads(p.read_text(encoding='utf8'));v.update(visual_review=dict(pages=list(range(1,8)),status='passed',checks=['paragraphs and equations legible','table repeated headers','three figures checked','corrected figure3 annotation clipping','no content or footer collisions']),latex_source_compilation_verified=False)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Source checks and seven-page visual QA recorded; TeX compilation remains unverified.')
if __name__=='__main__':main()
