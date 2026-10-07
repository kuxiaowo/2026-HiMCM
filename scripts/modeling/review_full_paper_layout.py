"""Measure and render the final English PDF for page-by-page layout review."""
from pathlib import Path
import json
import re
import subprocess
from statistics import median
import pdfplumber
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'tmp/pdfs/full_paper_continuous_final_20261006'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pdf=ROOT/'output/pdf/full_paper.pdf'
    pages=[]
    with pdfplumber.open(pdf) as document:
        assert len(document.pages)<=25
        for number,page in enumerate(document.pages,1):
            text=page.extract_text() or ''
            if number>2:
                assert len(re.sub(r'\s','',text))>200,('Nearly empty page',number)
                orphan_heading=[c for c in page.chars if 15<c['size']<17
                                and c['top']>page.height-1.5/2.54*72-24]
                assert not orphan_heading,('Subsection heading stranded at page end',number)
            objects=[o for o in page.chars+page.lines+page.curves+page.rects
                     if o.get('top',0)>40 and o.get('bottom',10000)<803]
            bottom=max(o['bottom'] for o in objects)
            top_heading=''.join(c['text'] for c in page.chars
                               if 21<c['size']<23 and 40<c['top']<100)
            if 'ReportonUseofAI' in re.sub(r'\s','',text.splitlines()[1]):
                top_heading='Report on Use of AI'
            pages.append({'page':number,'top_level_heading':top_heading,
                          'body_bottom_bp':round(bottom,3),
                          'bottom_gap_mm':round((page.height-1.5/2.54*72-bottom)*25.4/72,2),
                          'first_lines':text.splitlines()[1:4],
                          'last_lines':text.splitlines()[-3:]})
        intro=document.pages[2]
        body_bottom=pages[2]['body_bottom_bp']
        available=intro.height-3/2.54*72
        intro_fraction=(body_bottom-1.5/2.54*72)/available
        assert 0.75<=intro_fraction<=1.01,intro_fraction
    for i,page in enumerate(pages):
        page['ends_at_section_boundary']=(i==len(pages)-1 or bool(pages[i+1]['top_level_heading']))
        # One normal baseline, including the caption/float's trailing space, is
        # ordinary typography rather than an unused block of the page.
        page['bottom_gap_allowed']=(page['page']<=2 or page['ends_at_section_boundary'] or page['bottom_gap_mm']<=6)
        assert page['bottom_gap_allowed'],page
    result={'status':'measurements_passed_visual_review_pending','total_pages':len(pages),
            'introduction_page':3,'introduction_fraction_of_writable_height':round(intro_fraction,4),
            'internal_page_bottom_gap_limit_mm':6,
            'section_end_whitespace_allowed':True,'pages':pages}
    (OUT/'layout_measurements.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    subprocess.run(['D:/texlive/2026/bin/windows/pdftoppm.exe','-scale-to','1500','-png',str(pdf),str(OUT/'page')],
                   check=True,capture_output=True)
    files=sorted(file for file in OUT.glob('page-*.png') if int(file.stem.split('-')[1])<=len(pages))
    assert len(files)==len(pages)
    for start in range(0,len(files),8):
        contact=Image.new('RGB',(1500,4*565),'#dddddd');draw=ImageDraw.Draw(contact)
        for j,file in enumerate(files[start:start+8]):
            picture=Image.open(file).convert('RGB');picture.thumbnail((735,535))
            x=(j%2)*750+(750-picture.width)//2;y=(j//2)*565+25
            contact.paste(picture,(x,y));draw.text(((j%2)*750+10,(j//2)*565+6),str(start+j+1),fill='black')
        contact.save(OUT/f'contact-{start//8+1}.png')
    print(json.dumps({key:result[key] for key in ['status','total_pages','introduction_fraction_of_writable_height']}))
    print(json.dumps([{'page':p['page'],'gap_mm':p['bottom_gap_mm'],'section_end':p['ends_at_section_boundary']}
                      for p in pages]))


if __name__=='__main__':main()
