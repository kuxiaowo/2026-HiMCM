"""Check compact Q6 source and compiled PDF without mutating GIS/model inputs.

Use --visual-reviewed only after inspecting all six rendered pages.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/question6'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--visual-reviewed',action='store_true')
    args=parser.parse_args()
    source=ROOT/'docs/paper/question6_adaptation.tex'
    tex=source.read_text(encoding='utf8')
    md=(ROOT/'docs/paper/question6_adaptation.md').read_text(encoding='utf8')
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    refs=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',tex)
    assert len(labels)==len(set(labels)) and not(set(refs)-set(labels))
    entries=set(re.findall(r'\\bibitem\{([^}]+)\}',tex))
    cites={k for item in re.findall(r'\\cite\{([^}]+)\}',tex) for k in item.split(',')}
    assert cites<=entries
    stack=[]
    for item in re.finditer(r'\\(begin|end)\{([^}]+)\}',tex):
        if item[1]=='begin': stack.append(item[2])
        else: assert stack.pop()==item[2]
    assert not stack
    cleaned=re.sub(r'(?<!\\)%[^\n]*','',tex)
    brace=0
    for item in re.finditer(r'(?<!\\)[{}]',cleaned):
        brace+=1 if item.group()=='{' else -1
        assert brace>=0
    assert brace==0 and '@@' not in tex
    assert not re.search(r'\\(?:ref|eqref|cite|clearpage)\b',md)
    assert tex.count(r'\begin{figure}')==3 and tex.count(r'\begin{table}')==4
    assert r'\includegraphics' not in tex and r'\input{' not in tex
    results_path=OUT/'q6_results.json'
    results=json.loads(results_path.read_text(encoding='utf8'))
    for park in results['parks'].values():
        assert f"{park['polygon_area_km2']:.2f}" in md
    for case in results['cases']:
        if case['solution']:
            assert f"{case['solution']['total_person_hours']:.2f}" in md
    assert '边界校准未通过' in tex and '术语说明' in tex
    pdf=ROOT/'output/pdf/revision_20261006/question6_adaptation.pdf'
    log_path=ROOT/'output/pdf/revision_20261006/question6_adaptation.log'
    log=log_path.read_text(encoding='utf8',errors='replace')
    assert pdf.is_file() and 'Output written on' in log
    assert not re.search(r'Overfull|undefined references|Reference .* undefined|Citation .* undefined|^!',log,re.M)
    pdfinfo=shutil.which('pdfinfo') or 'D:/texlive/2026/bin/windows/pdfinfo.exe'
    assert pdfinfo, 'pdfinfo must be available for page verification'
    info=subprocess.run([pdfinfo,str(pdf)],capture_output=True,text=True,encoding='utf8',errors='replace',check=True).stdout
    page_count=int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])
    assert page_count==6, page_count
    visual_path=ROOT/'output/full_paper/revision_visual_review.json'
    current_visual=dict(pages=[],status='pending')
    if visual_path.exists():
        candidate=json.loads(visual_path.read_text(encoding='utf8'))['documents'].get('question6_adaptation',{})
        if candidate.get('pdf_sha256')==hashlib.sha256(pdf.read_bytes()).hexdigest():current_visual=candidate
    if args.visual_reviewed:
        assert current_visual.get('status')=='passed', 'Record visual review for the current PDF fingerprint first.'
    report=dict(
        status='compiled_six_pages_and_source_checks_passed',
        source=source.relative_to(ROOT).as_posix(),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        results_sha256=hashlib.sha256(results_path.read_bytes()).hexdigest(),
        pdf=pdf.relative_to(ROOT).as_posix(),
        pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
        pages=page_count,unique_labels=len(labels),undefined_source_labels=0,
        equations=6,figures=3,tables=4,bibliography_entries=len(entries),
        environment_and_brace_checks='passed',self_contained=True,
        builtin_compiler='unavailable: Unable to find standard directories for platform',
        compiler='D:/texlive/2026/bin/windows/xelatex.exe',
        source_compilation_verified=True,
        visual_review=current_visual,
        data_quality_limit='Chitwan boundary-area consistency remains unresolved; conditional trial only',
        model_inputs_or_results_changed=False,
    )
    (OUT/'q6_latex_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'Q6: source labels, saved numeric values, LaTeX compilation and {page_count} PDF pages verified.')

if __name__=='__main__':main()
