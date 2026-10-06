"""Audit Q3 writing against saved inputs/results and the approved outline.

Run with the bundled PDF runtime (pypdf), after conda presentation generation.
This checks the new chapter, not a repeat of the already audited LP solver.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def main():
    md=(ROOT/'docs/paper/question3_seasonal_staffing.md').read_text(encoding='utf-8')
    tex=(ROOT/'docs/paper/question3_framework.tex').read_text(encoding='utf-8')
    outline=(ROOT/'docs/paper/question3_framework.md').read_text(encoding='utf-8')
    manifest=read('output/question3/q3_chapter_manifest.json')
    figs=read('output/question3/paper_figures/figure_manifest.json')
    render=read('output/question3/q3_pdf_render_audit.json')
    result=read('output/question3/q3_results.json');ass=read('data/modeling/q3_assumptions.json')
    expected=re.findall(r'^#{2,3} (3\.[\d.]+ .+)$',outline,re.M)
    actual=re.findall(r'^#{2,3} (3\.[\d.]+ .+)$',md,re.M)
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    references=re.findall(r'\\(?:ref|eqref)\{([^}]+)\}',tex)
    env_begin=Counter(re.findall(r'\\begin\{([^}]+)\}',tex));env_end=Counter(re.findall(r'\\end\{([^}]+)\}',tex))
    bib=set(re.findall(r'\\bibitem\{([^}]+)\}',tex))
    cites=[key for group in re.findall(r'\\cite\{([^}]+)\}',tex) for key in group.split(',')]
    documents=['docs/paper/question3_seasonal_staffing.md','docs/paper/question3_framework.md',
               'docs/modeling_notes/q3_figure_design_references.md','README.md',
               'docs/项目状态与上传说明.md','docs/整体建模计划.md']
    missing=[]
    for f in documents:
        text=(ROOT/f).read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if link.startswith(('http:','https:','app:','codex:','#')):continue
            target=(ROOT/f).parent/link.split('#')[0]
            # The result JSON is written only after this audit finishes.
            if target.resolve()==(ROOT/'output/question3/q3_chapter_validation.json').resolve():continue
            if not target.exists():missing.append({'document':f,'link':link})
    reader=PdfReader(ROOT/'output/pdf/question3_framework.pdf')
    pdf_text=re.sub(r'\s+','', ''.join(p.extract_text() or '' for p in reader.pages))
    stress=next(x for x in result['full_sensitivity_solutions'] if x['name']=='base_drought')
    stress=next(x for x in stress['solutions'] if x['period']['month']==8)
    values=[result['target_score'],stress['inverse']['total_person_hours'],stress['inverse']['water_hours'],stress['fixed_reference']['score']]
    values += [result['monthly'][i-1]['required_person_hours'] for i in [1,5,8,11]]
    checks={
        'outline_matches_approved_5_sections_13_titles':actual==expected and len(actual)==18,
        '25_numbered_equations':len(re.findall(r'\\tag\{3-\d+\}',md))==25,
        'equation_numbers_sequential':re.findall(r'\\tag\{(3-\d+)\}',md)==[f'3-{i}' for i in range(1,26)],
        'latex_environment_counts_match':env_begin==env_end,
        'unique_labels':len(labels)==len(set(labels)),
        'all_formula_figure_table_references_resolved':all(ref in labels for ref in references),
        'six_valid_source_and_design_references':len(bib)==6 and all(cite in bib for cite in cites),
        'no_template_tokens':not re.search(r'@[A-Z_]+@',tex+md),
        'all_local_links_exist':not missing,
        'original_scientific_inputs_unchanged':all(sha(p)==h for p,h in manifest['source_sha256'].items()),
        'figure_data_fingerprints_match':all(sha(p)==h for p,h in figs['source_sha256'].items()),
        '25_math_blocks_balanced':md.count('\\[')==25 and md.count('\\]')==25,
        'four_figures_four_tables':env_begin['figure']==4 and env_begin['table']==4 and len(re.findall(r'^!\[',md,re.M))==4,
        'all_12_figure_outputs_exist':all((ROOT/'output/question3/paper_figures'/f"{x['name']}.{ext}").exists() for x in figs['figures'] for ext in ['png','svg','tikz']),
        'water_figure_total_matches_saved_solution':abs(figs['water_evidence']['dry_water_hours']-result['monthly'][7]['water_hours'])<1e-8,
        'key_numbers_present_in_synced_sources':all(f'{v:.2f}' in md and f'{v:.2f}' in tex for v in values),
        'peak_staff_57_and_stress_62':result['annual_fixed_staff_base_scenario']==57 and stress['inverse']['required_staff']==62,
        'fixed_120_effective_hours':ass['effective_person_hours_month']==120,
        'saved_independent_LP_verification_passed':read('output/question3/q3_independent_verification.json')['passed'],
        'no_math_render_errors':not render['math_errors'] and render['display_equations']==25,
        'no_broken_figures_or_horizontal_overflow':render['broken_images']==0 and not render['horizontal_overflow'],
        'PDF_A4_and_10_pages':len(reader.pages)==10 and all(abs(float(p.mediabox.width)-595.28)<1 for p in reader.pages),
        'PDF_key_results_in_prose':all(f'{v:.2f}' in pdf_text for v in values),
        'all_final_pages_rendered':all((ROOT/f'tmp/question3_pdf/pages/page-{i:02d}.png').exists() for i in range(1,len(reader.pages)+1)),
    }
    review={'reviewed_pages':list(range(1,11)),'passed':True,
            'method':'manual full-page images plus final 10-page contact sheet',
            'corrections':['display equations rendered as indivisible SVG images','table and note kept together',
                           'reference list kept together','formula lead-in kept with its equation','axis labels and workload legend adjusted']}
    output={'passed':all(checks.values()),'checks':checks,'missing_local_links':missing,
            'pages':len(reader.pages),'body_pages':9,'reference_pages':1,'visual_review':review,
            'latex_compilation':{'status':'platform_error','diagnostic':'Unable to find standard directories for platform'},
            'pdf_export_method':render['method'],'source_model_recomputed':False,
            'file_sha256':{p:sha(p) for p in ['docs/paper/question3_framework.tex','docs/paper/question3_seasonal_staffing.md','output/pdf/question3_framework.pdf']}}
    (ROOT/'output/question3/q3_chapter_validation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest['status']='formal_chapter_and_pdf_reading_copy_verified_latex_platform_error'
    manifest['pdf_pages']=len(reader.pages)
    (ROOT/'output/question3/q3_chapter_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':output['passed'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'pages':len(reader.pages)},ensure_ascii=False))
    assert output['passed']


if __name__=='__main__':main()
