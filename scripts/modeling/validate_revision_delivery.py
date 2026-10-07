"""Audit the delivered revision against current results, sources, renders and visual records.

This verifies artifacts and numerical consistency, not field effectiveness or contest eligibility.
Run with the bundled document Python. Original inputs and model results are read-only.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/full_paper'
PDF_DIR = 'output/pdf/skill_checked_20261007/'
DOCS = {
    'full_paper': ('full_paper', 24, 7, 17, 19),
    'full_paper_zh_explained': ('full_paper_zh', None, 6, 17, 19),
    'question1_protection_definition': ('question1_protection_definition', 1, 0, 0, 2),
    'question2_framework': ('question2_framework', 8, 2, 4, 20),
    'question3_framework': ('question3_framework', 6, 2, 3, 12),
    'question4_sensitivity': ('question4_sensitivity', 4, 2, 4, 3),
    'question5_evaluation': ('question5_evaluation', 1, 0, 0, 0),
    'question6_adaptation': ('question6_adaptation', 6, 3, 4, 6),
}


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def write(name, value):
    (ROOT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    render = read('tmp/pdfs/skill_checked_20261007/render_measurements.json')['documents']
    visual = read('output/full_paper/revision_visual_review.json')['documents']
    documents = {}
    for name, (stem, expected_pages, figures, tables, equations) in DOCS.items():
        source = f'docs/paper/{stem}.tex'
        pdf = PDF_DIR + name + '.pdf'
        log_path = PDF_DIR + name + '.log'
        tex = (ROOT/source).read_text(encoding='utf-8')
        log = (ROOT/log_path).read_text(encoding='utf-8', errors='replace')
        pages = PdfReader(ROOT/pdf).pages
        if expected_pages is not None:
            assert len(pages) == expected_pages, (name, len(pages), expected_pages)
        else:
            assert 30 <= len(pages) <= 45, (name, len(pages), 'Explanation pagination')
        assert all(abs(float(p.mediabox.width)-595.28)<.2 and abs(float(p.mediabox.height)-841.89)<.2 for p in pages)
        extracted = subprocess.run(['D:/texlive/2026/bin/windows/pdftotext.exe', '-layout', '-enc', 'UTF-8',
                                    str(ROOT/pdf), '-'], capture_output=True, check=True).stdout.decode('utf-8')
        assert not re.search(r'[\ufffd\u25a1\u25a0]|\?\?|@[A-Z_]+@', extracted), name
        assert not re.search(r'Overfull|Missing character|Glyph missing|undefined|multiply defined|^!', log, re.M), name
        assert 'Output written on' in log
        labels = re.findall(r'\\label\{([^}]+)\}', tex)
        refs = re.findall(r'\\(?:ref|eqref)\{([^}]+)\}', tex)
        assert len(labels) == len(set(labels)) and set(refs)-{'LastPage'} <= set(labels), name
        bib = re.findall(r'\\bibitem\{([^}]+)\}', tex)
        citations = [k for v in re.findall(r'\\cite\{([^}]+)\}', tex) for k in v.split(',')]
        assert len(bib) == len(set(bib)) and set(citations) <= set(bib)
        stack = []
        for action, env in re.findall(r'\\(begin|end)\{([^}]+)\}', tex):
            if action == 'begin': stack.append(env)
            else: assert stack and stack.pop() == env, (name, env)
        assert not stack and not re.search(r'@[A-Z_]+@', tex)
        assert [tex.count(r'\begin{'+env+'}') for env in ['figure','table']] == [figures,tables], name
        aux = (ROOT/(PDF_DIR+name+'.aux')).read_text(encoding='utf-8')
        # align may number more than one row; count compiled equation labels.
        numbered = re.findall(r'\\newlabel\{eq:[^}]+\}\{\{([^}]+)\}', aux)
        assert len(numbered) == equations and len(numbered) == len(set(numbered)), (name,numbered)
        assert r'\input{' not in tex and r'\includegraphics' not in tex, (name, 'External figure dependency')
        r = render[name]
        v = visual[name]
        assert r['pdf_sha256'] == sha(pdf) and r['page_count'] == len(pages) and r['all_pages_rendered']
        assert v['pdf_sha256'] == sha(pdf) and v['status'] == 'passed'
        assert v['reviewed_pages'] == list(range(1, len(pages)+1)), name
        fonts = subprocess.run(['D:/texlive/2026/bin/windows/pdffonts.exe', str(ROOT/pdf)],
                               capture_output=True, check=True).stdout.decode('ascii', errors='replace')
        font_lines = [line for line in fonts.splitlines()[2:] if line.strip()]
        assert font_lines and all(re.search(r'\byes\s+yes\s+(?:yes|no)\s+\d+', line) for line in font_lines), name
        if name.startswith('full_paper'):
            compact_pages = [p for p in extracted.split('\f') if p.strip()]
            for n, page in enumerate(compact_pages, 1):
                if name == 'full_paper':
                    assert re.search(r'Page\s+'+str(n)+r'\s+of\s+'+str(len(pages))+r'\b', page)
                else:
                    assert re.search(r'第\s*'+str(n)+r'\s*页\s*[/／]\s*共\s*'+str(len(pages))+r'\s*页', page), (name,n,page[:100])
        documents[name] = dict(source=source, source_sha256=sha(source), pdf=pdf, pdf_sha256=sha(pdf),
                               pages=len(pages), figures=figures, tables=tables, numbered_equations=equations,
                               bibliography_entries=len(bib), cross_references_resolved=True,
                               all_fonts_embedded=True, overflow_warnings=0,
                               underfull_warnings=len(re.findall('Underfull', log)), visual_review=v,
                               text_compact=re.sub(r'\s+', '', extracted).replace(',', ''))
    q2 = read('output/question2/q2_results.json')['optimum']
    q3 = read('output/question3/q3_results.json')
    supplement = read('output/revision_feasibility/20261006/revision_results.json')
    assert all(sha(p) == fingerprint for p, fingerprint in supplement['input_sha256'].items())
    assert abs(q2['score']-57.260161284231835) < 1e-7
    assert abs(q2['total_person_hours']-supplement['two_stage']['independent_Q3_inverse_person_hours']) < 1e-6
    assert q3['annual_fixed_staff_base_scenario'] == 57
    peak = max(q3['monthly'], key=lambda x:x['required_person_hours'])
    drought = next(x for x in q3['sensitivity'] if x['scenario']=='base' and x['abnormal_drought'])
    assert peak['required_staff'] == 57 and drought['annual_fixed_staff'] == 62
    values = [q2['score'], q2['total_person_hours'], q2['drone_flight_hours'],
              peak['required_person_hours'], drought['peak_person_hours']]
    values += [case['total_person_hours'] for case in supplement['technology_scenarios']]
    values += [case['score'] for case in supplement['pressure_comparisons']]
    values += [case['score'] for case in supplement['grid_sensitivity']]
    values += [supplement['yellowstone']['cases'][2]['total_person_hours']]
    for name in ['full_paper', 'full_paper_zh_explained']:
        for value in values:
            assert f'{value:.2f}' in documents[name]['text_compact'], (name, value)
    q4 = read('output/question4/q4_independent_verification.json')
    assert q4['passed'] and q4['independently_checked_feasible_solutions'] == 127 and q4['saved_cases'] == 131
    assert read('output/question3/q3_independent_verification.json')['passed']
    for item in documents.values():item.pop('text_compact')
    report = dict(status='passed_numerical_source_compilation_and_visual_checks',
                  verified_at_utc=datetime.now(timezone.utc).isoformat(), documents=documents,
                  results=dict(baseline_rate=q2['score'], minimum_labor_hours=q2['total_person_hours'],
                               flight_hours=q2['drone_flight_hours'], normal_peak_staff=57, drought_peak_staff=62,
                               Q2_Q3_inverse_agree=True, Q4_feasible_solutions_checked=127),
                  limitations=['Planning protocols and technology efficiency remain assumptions',
                               'Six historical surveyed groups do not cover all animals or current abundance',
                               'Chitwan legal boundary and reported-area convention remain uncalibrated',
                               'Monthly personnel equivalents do not certify rosters or ecological effects',
                               'Mathematical subscript sizes are smaller than prose by standard typesetting; normal body, captions, symbols, headers and cover labels use at least 12pt'],
                  compiler='Existing TeX Live 2026 XeLaTeX, two passes; built-in compiler has a platform-directory error')
    write('output/full_paper/revision_delivery_validation.json', report)
    zh = dict(status=report['status'], document_role='Chinese learning explanation; separate from competition page count',
              **documents['full_paper_zh_explained'], question_stage_guides=6,
              current_model_numbers_checked=True, historical_translation='output/full_paper/history/pre_plain_explanation_20261006')
    write('output/full_paper/full_paper_zh_explanation_validation.json', zh)
    full = read('output/full_paper/full_paper_validation.json')
    full['visual_review'] = visual['full_paper']
    full['status'] = report['status']
    full['body_and_letter_end_page'] = full['letter_pages'][-1]
    full['contest_counting_note'] = 'Original 24-page limit excludes references, appendices and AI report; this edition also satisfies the current user 25-page total-PDF limit.'
    write('output/full_paper/full_paper_validation.json', full)
    layout = dict(status='passed_visual_review', current_pdf=PDF_DIR+'full_paper.pdf',
                  pdf_sha256=sha(PDF_DIR+'full_paper.pdf'), total_pages=documents['full_paper']['pages'],
                  measurements=render['full_paper']['pages'], visual_review=visual['full_paper'],
                  whitespace_note='Section-end whitespace is permitted; intro and model pages inspected; no arbitrary 6 mm gap assertion')
    write('output/full_paper/full_paper_layout_validation.json', layout)
    for name, folder, manifest_name in [('question2_framework','question2','q2'), ('question3_framework','question3','q3'),
                                       ('question6_adaptation','question6','q6')]:
        manifest = read(f'output/{folder}/{manifest_name}_chapter_manifest.json')
        manifest.update(status='revision_compiled_and_verified', pdf=documents[name]['pdf'],
                        pdf_pages=documents[name]['pages'], pdf_sha256=documents[name]['pdf_sha256'],
                        validation='output/full_paper/revision_delivery_validation.json', visual_review=visual[name])
        write(f'output/{folder}/{manifest_name}_chapter_manifest.json', manifest)
    for name, target in [('question1_protection_definition','output/question1/q1_latex_compile_verification.json'),
                         ('question2_framework','output/question2/q2_latex_compile_verification.json')]:
        write(target, dict(status=report['status'], **documents[name], compiler=report['compiler']))
    write('output/question4/q45_chapter_validation.json', dict(status=report['status'],
          chapters={k:documents[k] for k in ['question4_sensitivity','question5_evaluation']}))
    write('output/question4/q45_pdf_validation.json', dict(status=report['status'],
          chapters={k:documents[k] for k in ['question4_sensitivity','question5_evaluation']}))
    q45_manifest = read('output/question4/q45_chapter_manifest.json')
    q45_manifest.update(status=report['status'], pdf_compilation_confirmed=True,
                        pdfs={k:documents[k]['pdf'] for k in ['question4_sensitivity','question5_evaluation']},
                        validation='output/full_paper/revision_delivery_validation.json')
    write('output/question4/q45_chapter_manifest.json', q45_manifest)
    manifest = read('output/full_paper/full_paper_manifest.json')
    manifest.update(status=report['status'], pdf=PDF_DIR+'full_paper.pdf', actual_total_pages=documents['full_paper']['pages'],
                    source_sha256=documents['full_paper']['source_sha256'], pdf_sha256=documents['full_paper']['pdf_sha256'],
                    numerical_model_changed=False, numerical_revision_20261006=True,
                    post_compile_validation='completed_for_current_skill_audit',
                    bibliography_entries=17, letter_pages_actual=full['letter_pages'],
                    revision_validation='output/full_paper/revision_delivery_validation.json',
                    visual_review='output/full_paper/revision_visual_review.json',
                    revision_date='2026-10-07', last_audited_at_utc=report['verified_at_utc'],
                    main_solution_pages=18, main_solution_page_range=[3,20], appendix_pages=[21],
                    contest_counted_pages=21, letter_pages_planned=1,
                    references_pages=[23], AI_report_pages=[24],
                    implementation_report='docs/modeling_notes/skill_full_audit_20261007.md',
                    review='output/full_paper/skill_audit_20261007/scored_review.json',
                    support_archive='output/full_paper/skill_audit_20261007/review_support.zip')
    write('output/full_paper/full_paper_manifest.json', manifest)
    print(json.dumps({'status':report['status'], 'PDF_pages':{k:v['pages'] for k,v in documents.items()},
                      'results':report['results']}, ensure_ascii=False))


if __name__ == '__main__':main()
