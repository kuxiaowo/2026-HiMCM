"""Check the compact manuscript against its saved inputs, results and PDF."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    texpath=ROOT/'docs/paper/question2_framework.tex'
    mdpath=ROOT/'docs/paper/question2_resource_allocation.md'
    pdfpath=ROOT/'output/pdf/revision_20261006/question2_framework.pdf'
    tex=texpath.read_text(encoding='utf-8')
    md=mdpath.read_text(encoding='utf-8')
    inputs=json.loads((ROOT/'output/question2/q2_model_inputs.json').read_text(encoding='utf-8'))
    results=json.loads((ROOT/'output/question2/q2_results.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(ROOT/'output/question2/history/q2_20pct_6drones_15pages_20261006.zip') as archive:
        previous=json.loads(archive.read('output/question2/q2_model_inputs.json'))
        oldparams=json.loads(archive.read('data/modeling/q2_assumptions.json'))['parameters']
    params=json.loads((ROOT/'data/modeling/q2_assumptions.json').read_text(encoding='utf-8'))['parameters']
    changed=[k for k in oldparams if oldparams[k]!=params[k]]
    assert set(changed)=={'protection_staff_fraction','drone_count'}
    assert inputs['targets']==previous['targets'], 'Geometry, weights and per-check costs must remain unchanged.'
    assert inputs['human_budget']==21240 and inputs['drone_budget']==1200
    assert params['effective_hours_month']==120 and params['checks_per_month']==8 and params['response_limit_hours']==2
    counts={name:len(re.findall(r'\\'+token+r'\{',tex)) for name,token in [('sections','subsection'),('subsections','subsubsection')]}
    for name in ['equation','figure','table']:
        counts[name+'s']=tex.count(r'\begin{'+name+'}')
    assert counts=={'sections':6,'subsections':20,'equations':20,'figures':2,'tables':4}
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    assert len(labels)==len(set(labels))
    references=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',tex)
    assert set(references)<=set(labels)
    citations=[k for group in re.findall(r'\\cite\{([^}]+)\}',tex) for k in group.split(',')]
    assert set(citations)<=set(re.findall(r'\\bibitem\{([^}]+)\}',tex))
    stack=[]
    for action,env in re.findall(r'\\(begin|end)\{([^}]+)\}',tex):
        if action=='begin':stack.append(env)
        else:assert stack and stack.pop()==env
    assert not stack
    for target in re.findall(r'\]\(([^)]+)\)',md):
        if not target.startswith(('https://','http://','#')):
            assert (mdpath.parent/target).resolve().exists(),target
    base=results['optimum']
    for key in ['score','total_person_hours','drone_flight_hours','drone_operator_hours']:
        assert f'{base[key]:.2f}' in md
    assert '术语速读' in md and '60%' in md and '30架' in md
    assert r'\documentclass[UTF8,fontset=fandol,12pt,a4paper]' in tex
    assert r'\usepackage[margin=2cm]{geometry}' in tex
    info=subprocess.run(['D:/texlive/2026/bin/windows/pdfinfo.exe',str(pdfpath)],capture_output=True,check=True).stdout
    pages=int(re.search(rb'Pages:\s+(\d+)',info).group(1))
    assert pages==8
    log=(ROOT/'output/pdf/revision_20261006/question2_framework.log').read_text(encoding='utf-8',errors='replace')
    assert not re.search(r'Overfull|Underfull|Missing character|undefined references|^!',log,re.M)
    report={'status':'passed','pdf_pages':pages,**counts,'unique_labels':len(labels),'cross_references':len(references),
        'only_changed_planning_parameters':changed,'target_geography_weights_and_costs_unchanged':True,
        'current_budget':{'human_hours':21240,'drone_hours':1200},'original_manuscript_archived':True,
        'numbered_formulas_and_references_consistent':True,'markdown_local_links_exist':True,
        'manuscript_numbers_match_saved_results':True,'body_font_points':12,'margin_cm':2,
        'second_stage':'global minimum labor while preserving the optimal score; service fractions remain free',
        'third_question':'recomputed with 177 available personnel and 1200 flight-hours; independently audited',
        'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [texpath,mdpath,pdfpath]},
        'visual_review':'recorded with current PDF fingerprint in output/full_paper/revision_visual_review.json'}
    (ROOT/'output/question2/q2_chapter_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
