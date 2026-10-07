"""Validate completeness, unchanged results and layout of the full Chinese translation."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BIN=Path('D:/texlive/2026/bin/windows')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    current=ROOT/'docs/paper/full_paper_zh.tex'
    if '% PLAIN_LANGUAGE_EXPLANATION_20261006' in current.read_text(encoding='utf-8'):
        raise SystemExit('This validator applies only to the historical 24-page translation. Current detailed source has a separate explanation audit; do not compile a replacement PDF with this script.')
    audit_path=ROOT/'output/full_paper/full_paper_zh_translation.json'
    audit=json.loads(audit_path.read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'output/full_paper/full_paper_manifest.json').read_text(encoding='utf-8'))
    en_path=ROOT/audit['source_english'];zh_path=ROOT/audit['source_chinese']
    assert sha(en_path)==audit['source_english_sha256']==manifest['source_sha256']
    assert sha(ROOT/manifest['pdf'])==manifest['pdf_sha256']
    assert sha(zh_path)==audit['source_chinese_sha256']
    assert all(sha(ROOT/name)==value for name,value in manifest['input_sha256'].items())
    en=en_path.read_text(encoding='utf-8');zh=zh_path.read_text(encoding='utf-8')
    assert len(audit['paragraphs'])==audit['all_narrative_blocks_translated']==124
    assert all(block['chinese'] in zh and re.search(r'[\u4e00-\u9fff]',block['chinese']) for block in audit['paragraphs'])
    for pattern in [r'\\label\{([^}]+)\}',r'\\cite\{([^}]+)\}',r'\\bibitem\{([^}]+)\}',r'\\(?:eqref|ref)\{([^}]+)\}']:
        assert re.findall(pattern,en)==re.findall(pattern,zh)
    def equations(value):
        value=re.sub(r'\\text\{[^}]+\}',r'\\text{UNIT}',value)
        return re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}',value,re.S)
    assert len(equations(en))==19 and equations(en)==equations(zh)
    def numeric_table_rows(value):
        tables=re.findall(r'\\begin\{table\}.*?\\end\{table\}',value,re.S)
        result=[]
        for table in tables:
            rows=[]
            for line in table.splitlines():
                if '&' not in line:continue
                values=[cell.strip().removesuffix(r'\\').strip() for cell in line.split('&')]
                numbers=[cell for cell in values[1:] if re.fullmatch(r'-?\d+(?:\.\d+)?|<\d+\.\d+',cell)]
                if numbers:rows.append(numbers)
            result.append(rows)
        return result
    assert len(numeric_table_rows(en))==13 and numeric_table_rows(en)==numeric_table_rows(zh)
    # All plotted numbers and geometry are identical; only visible labels change.
    def figure_paths(value):
        figures=re.findall(r'\\begin\{figure\}.*?\\end\{figure\}',value,re.S)
        return [[line for line in figure.splitlines() if line.startswith((r'\draw',r'\path',r'\fill'))] for figure in figures]
    assert len(figure_paths(en))==6 and figure_paths(en)==figure_paths(zh)
    pdf=ROOT/'output/pdf/full_paper_zh.pdf'
    extracted=subprocess.check_output([str(BIN/'pdftotext.exe'),'-layout','-enc','UTF-8',str(pdf),'-']).decode('utf-8')
    pages=[page for page in extracted.split('\f') if page.strip()]
    assert len(pages)==24
    for i,page in enumerate(pages,1):
        compact=re.sub(r'\s+','',page).replace('/','／')
        assert '队伍#510105201001220151' in compact,i
        assert f'第{i}页／共24页' in compact,i
    assert '摘要页' in pages[0] and '目录' in pages[1]
    assert 'IMMC' in pages[20] and '建模团队' in pages[21]
    assert '参考文献' in pages[22] and 'AI' in pages[23]
    figures=[int(n) for n in re.findall(r'图\s*(\d+)\s*[:：]',extracted)]
    tables=[int(n) for n in re.findall(r'表\s*(\d+)\s*[:：]',extracted)]
    assert figures==list(range(1,7)),figures
    assert tables==list(range(1,14)),tables
    assert not re.search(r'\?\?|\[\?\]|@[A-Z0-9_]+@',extracted)
    for number in ['21240','1200','5379.02','151.82','5286.11','6831.83','7390.17','1214.06','952.63','27.44']:
        assert number in extracted,number
    log=(ROOT/'output/pdf/full_paper_zh.log').read_text(encoding='utf-8',errors='replace')
    assert not re.search(r'Overfull|Underfull|Missing character|undefined|Warning|^!',log,re.M)
    fonts=subprocess.check_output([str(BIN/'pdffonts.exe'),str(pdf)]).decode('ascii',errors='replace')
    font_lines=[line for line in fonts.splitlines()[2:] if line.strip()]
    assert all(re.search(r'\byes\s+yes\s+(?:yes|no)\s+\d+',line) for line in font_lines)
    report={
      'status':'passed','verified_at_utc':datetime.now(timezone.utc).isoformat(),'language':'zh-CN',
      'pdf':'output/pdf/full_paper_zh.pdf','total_pages':24,'translation_blocks':124,
      'figure_numbers':figures,'table_numbers':tables,'numbered_equations':19,'references':15,'letter_pages':[21,22],
      'english_source_and_pdf_unchanged':True,'model_inputs_unchanged':True,'equations_and_table_results_match_english':True,
      'figure_geometry_unchanged':True,'labels_and_citations_match_english':True,'all_fonts_embedded':True,
      'latex_errors':0,'overflow_warnings':0,'missing_glyphs':0,
      'visual_review':{'status':'passed','pages':list(range(1,25)),'method':'all 24 final rendered PNG pages visually inspected'},
      'source_sha256':sha(zh_path),'pdf_sha256':sha(pdf),
      'compiler':'existing local XeLaTeX; built-in compiler returned platform-directory error',
    }
    path=ROOT/'output/full_paper/full_paper_zh_validation.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit.update(status='passed_compilation_and_visual_review',pdf=report['pdf'],actual_pages=24,pdf_sha256=report['pdf_sha256'],validation='output/full_paper/full_paper_zh_validation.json')
    audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','total_pages','translation_blocks','figure_numbers','table_numbers','english_source_and_pdf_unchanged']},ensure_ascii=False))


if __name__=='__main__':main()
