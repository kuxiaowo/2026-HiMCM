"""Check final page limits, numbering, provenance and current model values."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import argparse
from pathlib import Path
from datetime import datetime,timezone
from statistics import median

ROOT=Path(__file__).resolve().parents[2]


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def verify_pdf_typography(pdf):
    """Check selected rendered glyphs, rather than trusting source declarations."""
    import pdfplumber
    specifications=[
      ('cover_label',1,'Team Control Number',12,'TimesNewRoman'),
      ('cover_number',1,'510105201001220151',18,'TimesNewRoman'),
      ('cover_title',1,'Planning Wildlife Protection under Geographic and Resource Constraints',14,'TimesNewRoman'),
      ('cover_year',1,'2026',14,'TimesNewRoman'),
      ('contents_heading',2,'Contents',22,'TimesNewRoman'),
      ('section_heading',3,'Introduction',22,'TimesNewRoman'),
      ('body_text',3,'Large wildlife reserves are difficult to protect',12,'TimesNewRoman'),
      ('subsection_heading',4,'Priorities and evidence',16,'TimesNewRoman'),
      ('symbol_table',3,'Symbol',12,'TimesNewRoman'),
      ('caption_label',3,'Table 1:',12,'Arial'),
      ('caption_text',3,'Main symbols and units used in the protection-planning model.',12,'Arial'),
      ('page_header',3,'Team #510105201001220151',12,'TimesNewRoman'),
      ('references_heading',23,'References',22,'TimesNewRoman'),
      ('AI_heading',24,'Report on Use of AI',16,'TimesNewRoman'),
    ]
    samples={}
    with pdfplumber.open(pdf) as document:
        assert all(abs(p.width-210/25.4*72)<0.1 and abs(p.height-297/25.4*72)<0.1 for p in document.pages)
        for label,page,text,nominal,family in specifications:
            needle=re.sub(r'\s+','',text)
            # Normal prose glyphs are single characters; there can be two copies of
            # the control number (header and cover). Select its cover-sized copy.
            matches=[]
            for number,candidate in enumerate(document.pages,1):
                chars=[c for c in candidate.chars if not c['text'].isspace()]
                compact=''.join(c['text'] for c in chars)
                for found in re.finditer(re.escape(needle),compact):
                    group=chars[found.start():found.end()]
                    if group and abs(median(c['size'] for c in group)-nominal*72/72.27)<0.15:
                        matches.append((number,group))
            assert matches,(label,page,text,'missing or wrong font size')
            page,group=matches[0]
            assert all(family in c['fontname'].replace(' ','') for c in group),(label,{c['fontname'] for c in group})
            physical=median(c['size'] for c in group)
            assert all(abs(c['size']-nominal*72/72.27)<0.15 for c in group),(label,'mixed sizes')
            samples[label]={'page':page,'nominal_tex_pt':nominal,'measured_pdf_bp':round(physical,4),'font_family':family}
        # Section-first prose uses the same 24 pt indent as later paragraphs.
        page=document.pages[2]
        first=next(c for c in page.chars if c['text']=='L' and c['top']>65 and 11.8<c['size']<12.1)
        expected=1.5/2.54*72+24*72/72.27
        assert abs(first['x0']-expected)<0.25,(first['x0'],expected)
        samples['section_first_paragraph_indent']={'nominal_tex_pt':24,'measured_x0_bp':round(first['x0'],4)}
    return samples


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pdf',default='output/pdf/skill_checked_20261007/full_paper.pdf')
    parser.add_argument('--log',default='output/pdf/skill_checked_20261007/full_paper.log')
    parser.add_argument('--report',default='output/full_paper/full_paper_validation.json')
    args=parser.parse_args()
    source=ROOT/'docs/paper/full_paper.tex';pdf=ROOT/args.pdf
    tex=source.read_text(encoding='utf-8')
    manifest=read('output/full_paper/full_paper_manifest.json')
    extracted=subprocess.run(['D:/texlive/2026/bin/windows/pdftotext.exe','-layout','-enc','UTF-8',str(pdf),'-'],
        capture_output=True,check=True).stdout.decode('utf-8')
    pages=[page for page in extracted.split('\f') if page.strip()]
    count=len(pages)
    assert 1<=count<=25
    for i,page in enumerate(pages,1):
        assert re.search(r'Team\s+#\s*510105201001220151',page)
        assert re.search(r'Page\s+'+str(i)+r'\s+of\s+'+str(count)+r'\b',page)
    assert 'Summary Sheet' in pages[0] and 'Contents' in pages[1]
    find_page=lambda text:next(i for i,page in enumerate(pages,1) if text in page and i>2)
    letter_first=find_page('Letter to IMMC');letter_last=find_page('The Modeling Team')
    letter_pages=list(range(letter_first,letter_last+1))
    refs_page=find_page('References');ai_page=find_page('Report on Use of AI')
    assert letter_last<refs_page<ai_page and ai_page==count
    assert not re.search(r'\?\?|\[\?\]|@[A-Z_]+@',extracted)
    assert not re.search(r'[\u4e00-\u9fff]',extracted)
    figures=[int(v) for v in re.findall(r'\bFigure\s+(\d+):',extracted)]
    tables=[int(v) for v in re.findall(r'\bTable\s+(\d+):',extracted)]
    assert figures==list(range(1,8)),figures
    assert tables==list(range(1,18)),tables
    assert tex.count(r'\begin{equation}')==19
    assert r'\boxed' not in tex and r'\fbox' not in tex
    assert r'\subsection{Strengths}' in tex and r'\subsection{Weaknesses and Limitations}' in tex
    assert r'\subsection{Weight sensitivity}' in tex
    assert r'\label{fig:deployment}' in tex and r'\label{tab:weights}' in tex
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    assert len(labels)==len(set(labels))
    refs=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',tex)
    assert set(refs)-{'LastPage'}<=set(labels)
    bib=re.findall(r'\\bibitem\{([^}]+)\}',tex)
    citations=[k for x in re.findall(r'\\cite\{([^}]+)\}',tex) for k in x.split(',')]
    assert set(citations)<=set(bib) and len(bib)==17
    assert 'codex' in citations and 'codex' in bib
    expected_sections=[
      'Introduction','Basic Assumptions and Justifications','Data Description and Symbol Definitions',
      'Protection Priorities and a Measurable Standard','Resource Allocation with Ground Teams and Drones',
      'Seasonal Service and Workforce Requirements','Sensitivity and Scenario Analysis',
      'Strengths, Limitations and Practical Use','Adaptation to Parks on Other Continents']
    assert re.findall(r'\\section\{([^}]+)\}',tex)==expected_sections
    for number,title in enumerate(expected_sections,1):
        assert re.search(str(number)+r'\.?\s+'+r'\s+'.join(map(re.escape,title.split())),pages[1]),(number,title)
    stack=[]
    for action,env in re.findall(r'\\(begin|end)\{([^}]+)\}',tex):
        if action=='begin':stack.append(env)
        else:assert stack and stack.pop()==env
    assert not stack
    log=(ROOT/args.log).read_text(encoding='utf-8',errors='replace')
    assert not re.search(r'Overfull|Missing character|undefined|Font Warning|^!',log,re.M)
    assert '\\documentclass[12pt,a4paper]' in tex and 'left=1.5cm,right=1.5cm,top=1.5cm,bottom=1.5cm' in tex
    assert r'\titlespacing{\section}' in tex and r'\usepackage{indentfirst}' in tex
    assert 'labelfont=referencecaption,labelsep=colon' in tex
    assert not re.search(r'\\(?:footnotesize|scriptsize|tiny)\b',tex)
    typography=verify_pdf_typography(pdf)
    assert manifest['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in manifest['input_sha256'].items())
    q2=read('output/question2/q2_results.json');q3=read('output/question3/q3_results.json')
    q4=read('output/question4/q4_results.json');q6=read('output/question6/q6_results.json')
    peak=max(q3['monthly'],key=lambda v:v['required_person_hours'])
    drought=next(v for v in q3['sensitivity'] if v['scenario']=='base' and v['abnormal_drought'])
    assert q2['optimum']['human_budget']==21240 and q2['optimum']['drone_budget']==1200
    assert q3['fixed_reference_staff']==177 and peak['required_staff']==57 and drought['annual_fixed_staff']==62
    for value in [q2['optimum']['score'],q2['optimum']['total_person_hours'],q2['optimum']['drone_flight_hours'],
                  peak['required_person_hours'],drought['peak_person_hours']]:
        assert f'{value:.2f}' in extracted
    transfer='\n'.join(pages[find_page('9. Adaptation')-1:letter_first-1])
    assert all(value in transfer for value in ['1214.06','952.63','27.44%'])
    transfer_words=re.sub(r'\s+',' ',re.sub(r'(?<=\w)-\s*\n(?=\w)','',transfer)).lower()
    assert 'conditional' in transfer_words and 'actual park staffing' in transfer_words
    assert q6['status']=='real_geographic_inputs_with_explicit_service_assumptions'
    assert q4['current_reference_staff']==177 and q4['current_drone_budget']==1200
    standalone={}
    for label,path in [('question3','output/pdf/skill_checked_20261007/question3_framework.pdf'),('question6','output/pdf/skill_checked_20261007/question6_adaptation.pdf')]:
        info=subprocess.run(['D:/texlive/2026/bin/windows/pdfinfo.exe',str(ROOT/path)],capture_output=True,check=True).stdout
        chapter_count=int(re.search(rb'Pages:\s+(\d+)',info).group(1));assert chapter_count==6
        standalone[label]={'pages':chapter_count,'pdf':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
    info=subprocess.run(['D:/texlive/2026/bin/windows/pdffonts.exe',str(pdf)],capture_output=True,check=True).stdout.decode('ascii',errors='replace')
    fontlines=[line for line in info.splitlines()[2:] if line.strip()]
    assert all(re.search(r'\byes\s+yes\s+(?:yes|no)\s+\d+',line) for line in fontlines)
    head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip()
    assert subprocess.check_output(['git','branch','--show-current']).decode().strip()=='developing'
    assert not subprocess.check_output(['git','diff','--name-only','--diff-filter=U']).strip()
    report={'status':'passed','verified_at_utc':datetime.now(timezone.utc).isoformat(),'team_control_number':'510105201001220151',
      'language':'English','total_pdf_pages':count,'page_limit':25,'count_includes_summary_contents_letter_references_AI':True,
      'letter_pages':letter_pages,'references_page':refs_page,'AI_report_page':ai_page,'body_font_points':12,'margin_cm':1.5,'figure_numbers':figures,'table_numbers':tables,
      'heading_font_points':22,'subheading_font_points':16,'caption_font_points':12,'symbol_table_font_points':12,
      'rendered_typography_samples':typography,'opening_sections':expected_sections[:3],'numbered_sections':9,
      'template_authority':'output/full_paper/caption_revision_20261007/style_contract.json' if '% USER_SHORT_CAPTIONS_20261007' in tex else 'output/full_paper/template_style_contract.json',
      'numbered_equations':19,'bibliography_entries':17,'all_page_headers_numbered':True,'cross_references_resolved':True,
      'environment_pairing_passed':True,'current_model_numbers_checked':True,'input_fingerprints_match':True,
      'all_fonts_embedded':True,'embedded_font_count':len(fontlines),'latex_errors':0,'overflow_warnings':0,
      'underfull_warnings':len(re.findall('Underfull',log)),'visual_review':{'pages':[],'status':'pending',
        'method':'Numerical/source check only; rendered final pages require a separate visual review'},
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
      'standalone_chapters':standalone,'remote_commit_integrated':head,'working_branch':'developing',
      'builtin_compiler':'unavailable: Unable to find standard directories for platform; existing XeLaTeX used',
      'limitations_retained':['Chitwan published boundary does not match official area','personnel estimates are conditional pooled workloads','service score is not ecological outcome',
        'Field effectiveness and operational staffing remain uncalibrated; caption and symbol sizes raised to 12pt under user instruction']}
    (ROOT/args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest.update(status='passed_compilation_numerical_checks_visual_review_pending',actual_total_pages=count,pdf=args.pdf,
                    pdf_sha256=report['pdf_sha256'],validation=args.report,letter_pages_actual=letter_pages)
    (ROOT/'output/full_paper/full_paper_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','total_pdf_pages','letter_pages','figure_numbers','table_numbers','current_model_numbers_checked']},ensure_ascii=False))


if __name__=='__main__':main()
