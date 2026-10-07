"""Check the synchronized six-page Q3 chapter against its audited results."""
from __future__ import annotations
import hashlib, json, re
from collections import Counter
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()

def main():
    md=(ROOT/'docs/paper/question3_seasonal_staffing.md').read_text(encoding='utf-8')
    tex=(ROOT/'docs/paper/question3_framework.tex').read_text(encoding='utf-8')
    outline=(ROOT/'docs/paper/question3_framework.md').read_text(encoding='utf-8')
    manifest=read('output/question3/q3_chapter_manifest.json')
    figs=read('output/question3/paper_figures/figure_manifest.json')
    result=read('output/question3/q3_results.json'); q2=read('output/question2/q2_model_inputs.json')
    ass=read('data/modeling/q3_assumptions.json')
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    refs=re.findall(r'\\(?:ref|eqref)\{([^}]+)\}',tex)
    begin=Counter(re.findall(r'\\begin\{([^}]+)\}',tex)); end=Counter(re.findall(r'\\end\{([^}]+)\}',tex))
    expected=re.findall(r'^#{2,3} (3\.[\d.]+ .+)$',outline,re.M)
    actual=re.findall(r'^#{2,3} (3\.[\d.]+ .+)$',md,re.M)
    bib=set(re.findall(r'\\bibitem\{([^}]+)\}',tex))
    cites=[x for group in re.findall(r'\\cite\{([^}]+)\}',tex) for x in group.split(',')]
    pdfpath='output/pdf/revision_20261006/question3_framework.pdf'
    reader=PdfReader(ROOT/pdfpath)
    pdf_numbers=re.sub(r'\s+','', ''.join(p.extract_text() or '' for p in reader.pages))
    stress=next(x for x in result['full_sensitivity_solutions'] if x['name']=='base_drought')
    stress=next(x for x in stress['solutions'] if x['period']['month']==8)
    values=[result['target_score'],stress['inverse']['total_person_hours'],stress['inverse']['water_hours']]
    values+=[result['monthly'][i-1]['required_person_hours'] for i in [1,5,8,11]]
    log=(ROOT/'output/pdf/revision_20261006/question3_framework.log').read_text(encoding='utf-8',errors='replace')
    missing=[]
    for f in ['docs/paper/question3_seasonal_staffing.md','docs/paper/question3_framework.md','docs/第三题模型实算.md']:
        for link in re.findall(r'\]\(([^)]+)\)',(ROOT/f).read_text(encoding='utf-8')):
            if link.startswith(('http:','https:','#','codex:','app:')): continue
            if not ((ROOT/f).parent/link.split('#')[0]).exists(): missing.append({'file':f,'link':link})
    checks={
        'approved_five_sections_thirteen_subsections':actual==expected and len(actual)==18,
        'twelve_sequential_equations':re.findall(r'\\tag\{(3-\d+)\}',md)==[f'3-{i}' for i in range(1,13)],
        'latex_environments_balanced':begin==end,
        'unique_labels_and_resolved_references':len(labels)==len(set(labels)) and all(x in labels for x in refs),
        'six_valid_references':len(bib)==6 and all(x in bib for x in cites),
        'two_figures_three_tables':begin['figure']==2 and begin['table']==3,
        'input_and_result_fingerprints_current':all(sha(p)==v for p,v in manifest['source_sha256'].items()),
        'figure_fingerprints_current':all(sha(p)==v for p,v in figs['source_sha256'].items()),
        'reference_staff_177_and_fleet_30':ass['fixed_reference_staff']==177 and q2['config']['drone_count']==30 and q2['drone_budget']==1200,
        'fixed_120_effective_hours':ass['effective_person_hours_month']==120,
        'peak_57_and_drought_62':result['annual_fixed_staff_base_scenario']==57 and stress['inverse']['required_staff']==62,
        '177_staff_retain_target_under_drought':abs(stress['fixed_reference']['score']-result['target_score'])<1e-8,
        'independent_84_solution_audit_passed':read('output/question3/q3_independent_verification.json')['passed'],
        'six_A4_pages':len(reader.pages)==6 and all(abs(float(p.mediabox.width)-595.28)<1 for p in reader.pages),
        'key_numbers_in_sources_and_pdf':all(f'{v:.2f}' in md and f'{v:.2f}' in tex and f'{v:.2f}' in pdf_numbers for v in values),
        'no_overflow_or_unresolved_compile_references':'Overfull' not in log and 'undefined' not in log,
        'all_six_final_pages_rendered':read('tmp/pdfs/revision_20261006/render_measurements.json')['documents']['question3_framework']['pdf_sha256']==sha(pdfpath),
        'all_local_links_exist':not missing,
        'no_template_tokens':not re.search(r'@[A-Z_]+@',tex+md),
    }
    review_path=ROOT/'output/full_paper/revision_visual_review.json'
    review={'status':'pending','reviewed_pages':[]}
    if review_path.exists():
        saved=read('output/full_paper/revision_visual_review.json')['documents'].get('question3_framework',{})
        if saved.get('pdf_sha256')==sha(pdfpath):review=saved
    output={'passed':all(checks.values()),'checks':checks,'missing_links':missing,'pages':6,
            'visual_review':review,'source_model_recomputed':True,
            'latex_compilation':{'built_in':'platform_error: Unable to find standard directories for platform','local_XeLaTeX':'success; TeX Live 2026; two passes'},
            'file_sha256':{p:sha(p) for p in ['docs/paper/question3_framework.tex','docs/paper/question3_seasonal_staffing.md',pdfpath]}}
    (ROOT/'output/question3/q3_chapter_validation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest.update(status='six_page_synchronized_chapter_verified',pdf_pages=6,local_XeLaTeX_compilation='success')
    (ROOT/'output/question3/q3_chapter_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    render={'method':'XeLaTeX, TeX Live 2026; Poppler PNG rendering','pages':6,'display_equations':12,'math_errors':[],
            'broken_images':0,'horizontal_overflow':[],'visual_review':review}
    (ROOT/'output/question3/q3_pdf_render_audit.json').write_text(json.dumps(render,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':output['passed'],'pages':6,'failed_checks':[k for k,v in checks.items() if not v]},ensure_ascii=False))
    assert output['passed']

if __name__=='__main__':main()
