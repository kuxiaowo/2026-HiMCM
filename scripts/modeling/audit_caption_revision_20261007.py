"""Verify the concise-caption edition without changing model inputs or results."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile
import audit_full_skill_20261007 as audit

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/full_paper/caption_revision_20261007'
PDF = 'output/pdf/caption_revision_20261007/full_paper.pdf'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'docs/paper/full_paper.tex'
    tex = source.read_text(encoding='utf-8')
    log = (ROOT / PDF).with_suffix('.log').read_text(encoding='utf-8', errors='replace')
    assert '% USER_SHORT_CAPTIONS_20261007' in tex
    assert not re.search(r'Overfull|Missing character|Glyph missing|undefined|Font Warning|multiply defined|^!', log, re.M)
    revision = json.loads((OUT / 'source_revision.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(ROOT / revision['backup']) as z:
        before = z.read('docs/paper/full_paper.tex').decode('utf-8')
    from revise_short_captions_20261007 import signatures, FLOAT, CAP
    assert signatures(before) == signatures(tex)
    equations = lambda text: re.findall(r'\\begin\{equation\}.*?\\end\{equation\}', text, re.S)
    assert equations(before) == equations(tex) and len(equations(tex)) == 19
    for m in FLOAT.finditer(tex):
        caption = CAP.search(m[0])[1]
        assert caption.count('.') == 1 and caption.endswith('.')
    bib = set(re.findall(r'\\bibitem\{([^}]+)\}', tex))
    cites = {k for group in re.findall(r'\\cite\{([^}]+)\}', tex) for k in group.split(',')}
    assert cites <= bib and len(bib) == 17
    audit.OUT = OUT
    shutil.copyfile(ROOT / 'output/full_paper/skill_audit_20261007/original_check_layout.py', OUT / 'original_check_layout.py')
    numerical = audit.numerical_audit()
    layout = audit.layout_audit(tex, PDF)
    doc = audit.pymupdf.open(ROOT / PDF)
    pages = [p.get_text() for p in doc]
    find = lambda needle: next(i for i, text in enumerate(pages, 1) if needle in text and i > 2)
    appendix = find('Appendix: supplementary results')
    letter = find('Letter to IMMC')
    references = find('References')
    ai_report = find('Report on Use of AI')
    solution_pages = appendix - 3
    counted_pages = len(pages) - 3  # one appendix, one references, one AI page
    assert solution_pages <= 20 and counted_pages <= 24 and len(pages) <= 25
    assert letter < references < ai_report == len(pages)
    compact = re.sub(r'\s+', '', '\n'.join(pages)).replace(',', '')
    results = json.loads((ROOT / 'output/question2/q2_results.json').read_text(encoding='utf-8'))['optimum']
    for key in ['score', 'total_person_hours', 'drone_flight_hours']:
        assert f'{results[key]:.2f}' in compact
    report = dict(status='passed_source_numerical_and_automatic_layout_checks_visual_pending',
                  authority='User requested one concise sentence per figure/table caption, detailed explanations in adjacent body prose; overrides generic 100--150 caption tokens.',
                  source=source.relative_to(ROOT).as_posix(), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  pdf=PDF, pdf_sha256=hashlib.sha256((ROOT / PDF).read_bytes()).hexdigest(),
                  pages=len(pages), main_solution_pages=solution_pages, contest_counted_pages=counted_pages,
                  appendix_page=appendix, letter_page=letter, references_page=references, AI_report_page=ai_report,
                  captions=len(layout['objects']), captions_one_sentence=True, tables_and_TikZ_unchanged=True,
                  all_19_numbered_equations_unchanged=True, bibliography_entries=17,
                  numerical_checks_passed=numerical['passed'], figures=7, tables=17,
                  max_graphic_ratio=layout['max_graphic_ratio'],
                  previous_full_review='output/full_paper/skill_audit_20261007/scored_review.json (before this user override)',
                  numerical_model_changed=False, visual_review='pending',
                  compiler='Two-pass installed XeLaTeX succeeded; built-in compiler platform-directory error remains.',
                  limitations_retained=['Historical and incomplete inputs', 'Conditional Chitwan polygon trial',
                                        'Pooled monthly personnel equivalents, not a roster', 'No demonstrated ecological sufficiency'])
    (OUT / 'caption_revision_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['status', 'pages', 'captions', 'main_solution_pages', 'tables_and_TikZ_unchanged', 'max_graphic_ratio']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
