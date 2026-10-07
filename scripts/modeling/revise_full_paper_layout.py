"""Revise the existing English manuscript's introduction and continuous layout."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MARKER = '% CONTINUOUS_ENGLISH_LAYOUT_20261006'

INTRODUCTION = r'''Large wildlife reserves face a practical protection problem: important locations are spread across a wide area, while staff, equipment and travel time are limited. An observation becomes useful only when an appropriate team can follow it up. More patrol hours or more drones may increase monitoring activity without making distant locations easier to reach. The problem therefore asks how conservation priorities should be defined, how ground teams and drones should be allocated, and how the workforce should change as seasonal tasks increase. Etosha National Park provides the starting case, with a reported area of about 22,935 km$^2$ and a reference workforce of 295 employees \cite{problem}.

We address the six questions through one connected planning framework. First, we define a measurable inspection service and identify the conservation concerns supported by the available evidence. We then allocate ground and drone work subject to travel, response and resource limits. A monthly extension estimates the personnel needed to maintain the same basic service while completing additional fire checks and borehole maintenance. Sensitivity tests examine reduced resources, altered travel conditions and different visit dates. Finally, we assess the model's limitations and test how its structure can be adapted to parks in Asia and North America. The purpose is to support transparent deployment decisions with a clear account of what the results mean.

Our spatial method organizes Etosha into 17 reporting regions and 599 inspection units. Historical animal counts, legal protection categories and burnable-habitat areas establish relative task priorities; mapped roads and candidate response posts determine travel time. Each unit has a representative location and a prescribed monthly inspection demand. A task receives effective service only if its screening is completed and a qualified ground team can arrive within two hours. We combine these completion levels using normalized importance weights to produce a score from 0 to 100. This score measures delivery of the selected tasks, rather than wildlife survival or a measured reduction in ecological losses.

A linear program chooses the ground personnel-hours, drone flight-hours and completion level for each unit. Its constraints account for inspection capacity, drone suitability, operating personnel, shared response readiness and a minimum service requirement for the reachable part of every region. The baseline assumes that 60\% of the reference workforce is available for these tasks at 120 effective hours per person-month, providing 21240 personnel-hours. Thirty proposed drones provide 1200 flight-hours per month. These are planning conditions rather than verified operating rules. By treating personnel and flight time as separate resources, the model also makes explicit that drone observations still require people for transport, operation and follow-up.

The seasonal model retains the basic inspection target and adds month-specific fire screening and maintenance visits to 17 historically documented boreholes. It first calculates the extra workload, then minimizes total personnel-hours needed to meet the target under the shared flight budget. Dividing that workload by 120 and rounding upward gives a monthly personnel requirement; the largest month determines a fixed available team size. The drought case changes maintenance frequency and on-site time, rather than forecasting rainfall, animal populations or water-delivery volumes. We separately check whether pooled monthly work can conceal long gaps between visits.

The baseline reaches 57.26 points. A representative allocation uses 5379.02 personnel-hours and 151.82 flight-hours, leaving substantial resources unused because the existing response layout limits credited service. Of three additional-post candidates, ENP5 raises the score to 64.27 under unchanged total resource limits. Maintaining the baseline target requires 57 available personnel in the normal peak month and 62 in the specified drought-maintenance case. Both estimates are conditional on the tasks included. Trials for Chitwan and Yellowstone retain the task, route and response structure while rebuilding local inputs; Chitwan's boundary-area mismatch prevents treating its result as calibrated park staffing. The main conclusion is that personnel, equipment and access should be planned together, with field validation preceding operational recommendations.'''

LAYOUT = r'''
% Continuous body pages: breaks belong to top-level sections, not subsections.
\flushbottom
\setcounter{topnumber}{3}\setcounter{bottomnumber}{3}\setcounter{totalnumber}{4}
\renewcommand{\topfraction}{0.90}\renewcommand{\bottomfraction}{0.85}
\renewcommand{\textfraction}{0.08}\renewcommand{\floatpagefraction}{0.85}
\setlength{\textfloatsep}{9pt plus 2pt minus 2pt}
\setlength{\floatsep}{8pt plus 2pt minus 2pt}
\setlength{\intextsep}{8pt plus 2pt minus 2pt}
\widowpenalty=10000\clubpenalty=10000
'''


def main():
    source = ROOT/'docs/paper/full_paper.tex'
    original = source.read_text(encoding='utf-8')
    if MARKER in original:
        raise SystemExit('Continuous layout already applied; edit current source in place.')
    history = ROOT/'output/full_paper/history/before_continuous_layout_20261006.zip'
    history.parent.mkdir(parents=True, exist_ok=True)
    names = ['docs/paper/full_paper.tex','output/pdf/full_paper.pdf','output/pdf/full_paper.log',
             'output/full_paper/full_paper_manifest.json','output/full_paper/full_paper_validation.json',
             'scripts/modeling/full_paper_body.py','scripts/modeling/write_full_paper.py',
             'scripts/modeling/validate_full_paper.py']
    if history.exists():
        with zipfile.ZipFile(history) as archive:
            assert archive.read('docs/paper/full_paper.tex') == source.read_bytes()
    else:
        with zipfile.ZipFile(history,'w',zipfile.ZIP_DEFLATED) as archive:
            for name in names:
                path=ROOT/name
                if path.exists():archive.write(path,name)
    text=original
    intro_pattern=r'(\\section\{Introduction\}\n)(.*?)(?=\\section\{Basic Assumptions and Justifications\})'
    text,count=re.subn(intro_pattern,lambda m:m.group(1)+INTRODUCTION+'\n\n',text,flags=re.S)
    assert count==1
    text=text.replace("within this document's 24-page ceiling", "within this document's 25-page ceiling")
    text=re.sub(r'^% PAGE \d+\s*$', '', text, flags=re.M)
    # Remove the former one-subsection-per-page plan; keep opening front matter pages.
    begin_body=text.index(r'\section{Introduction}')
    front=text[:begin_body]
    body=text[begin_body:].replace('\\clearpage\n','')
    body=re.sub(r'(^\\section\*?\{)',lambda m:'\\clearpage\n'+m.group(1),body,flags=re.M)
    body=body.removeprefix('\\clearpage\n')
    # References use their own heading supplied by thebibliography.
    ref_anchor='\\begingroup\n\\titleformat{\\section}{\\fontsize{22}{33}\\selectfont}'
    assert body.count(ref_anchor)==1
    body=body.replace(ref_anchor,'\\clearpage\n'+ref_anchor)
    # For AI, keep its local title style on the same page as the heading.
    body=body.replace('\\clearpage\n\\section*{Report on Use of AI}',r'\section*{Report on Use of AI}')
    ai_anchor='\\begingroup\n\\titleformat{\\section}{\\fontsize{16}{24}\\selectfont\\bfseries}{}{0pt}{}'
    assert body.count(ai_anchor)==1
    body=body.replace(ai_anchor,'\\clearpage\n'+ai_anchor)
    text=front+body
    text=text.replace(r'\begin{figure}[H]',r'\begin{figure}[!htbp]')
    text=text.replace(r'\begin{table}[H]',r'\begin{table}[!htbp]')
    text=text.replace(r'\begin{document}',MARKER+'\n'+LAYOUT+'\n'+r'\begin{document}',1)
    # Preserve all mathematics and table/figure bodies; placement alone may differ.
    equations=lambda s:re.findall(r'\\begin\{equation\}.*?\\end\{equation\}',s,re.S)
    assert equations(text)==equations(original)
    for env in ['table','figure']:
        block=lambda s:re.findall(r'\\begin\{'+env+r'\}(?:\[[^]]*\])?(.*?)\\end\{'+env+r'\}',s,re.S)
        assert block(text)==block(original),env
    assert re.findall(r'\\label\{([^}]+)\}',text)==re.findall(r'\\label\{([^}]+)\}',original)
    source.write_text(text,encoding='utf-8')
    manifest_path=ROOT/'output/full_paper/full_paper_manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest.update(status='revised_source_compilation_pending',planned_total_pages=25,
                    page_limit=25,letter_pages_planned=None,
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    introduction_words=len(re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*",INTRODUCTION)),
                    layout='Continuous within top-level sections; flexible figure/table placement',
                    revision_history=str(history.relative_to(ROOT)).replace('\\','/'))
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'introduction_words':manifest['introduction_words'],
                     'forced_page_breaks':text.count(r'\clearpage'),
                     'all_equations_and_figure_table_content_unchanged':True},ensure_ascii=False))


if __name__=='__main__':main()
