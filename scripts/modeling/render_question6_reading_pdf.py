"""Reading PDF fallback from the synchronised draft, not a TeX compilation.

Run math-image stage with conda, then PDF stage with bundled ReportLab Python.
The LaTeX source remains the authoritative editable document.
"""
from pathlib import Path
import hashlib, json, re, sys, html

ROOT=Path(__file__).resolve().parents[2]
TMP=ROOT/'tmp/pdfs/question6_reading'
MD=ROOT/'docs/paper/question6_adaptation.md'
PDF=ROOT/'output/pdf/question6_adaptation_reading.pdf'
DISPLAY=[
 [r'P_t^{(p)}=100\sum_jw_j^{(p)}s_{jt}^{(p)},\qquad \sum_jw_j^{(p)}=1.'],
 [r'r_{jt}=\mathbf{1}\{\delta+T_{jt}^{+}+v_{jt}\leq\overline{T}_j\}',
  r'a_{jt}=n_j(T_{jt}^{+}+T_{jt}^{-}+2v_{jt}+\tau_j+\pi_j).'],
 [r'C_{jt}s_{jt}\leq x_{jt}/a_{jt}+h_{jt}/b_{jt}',
  r'0\leq s_{jt}\leq r_{jt},\qquad h_{jt}=0\quad(m_{jt}=0)',
  r'x_{jt},h_{jt}\geq0',
  r'\sum_jh_{jt}\leq U_t',
  r'H_t=H_{0t}+L_t+\sum_j(x_{jt}+\gamma_{jt}h_{jt})\leq H_t^{\max}.'],
 [r'H_0=2\times2\times8\times30=960,\qquad N_t=\lceil H_t^{\min}/120\rceil.'],
 [r'P_t^{\mathrm{geo}}=100\sum_jw_jr_{jt}.']
]

def render_math():
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.mathtext import math_to_image
    from matplotlib.font_manager import FontProperties
    from PIL import Image
    TMP.mkdir(parents=True,exist_ok=True);mapping={}
    formulas=re.findall(r'\\\((.*?)\\\)',MD.read_text(encoding='utf-8'),flags=re.S)
    formulas += [x for group in DISPLAY for x in group]
    for formula in dict.fromkeys(formulas):
        fixed=formula.replace(r'\le',r'\leq').replace(r'\ge',r'\geq').replace(r'\leqq',r'\leq').replace(r'\geqq',r'\geq')
        fixed=re.sub(r'\\overline\s+([A-Za-z])',r'\\overline{\1}',fixed)
        name=hashlib.sha256(formula.encode()).hexdigest()[:18]+'.png';path=TMP/name
        math_to_image('$'+fixed+'$',path,prop=FontProperties(size=12),dpi=300,format='png',color='#202f3c')
        with Image.open(path) as img:w,h=img.size
        mapping[formula]=dict(path=str(path),width=w*72/300,height=h*72/300)
    (TMP/'math_images.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Rendered',len(mapping),'formula images.')

def render_pdf():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,KeepTogether
    from pypdf import PdfReader
    pdfmetrics.registerFont(TTFont('Q6Song','C:/Windows/Fonts/simsun.ttc',subfontIndex=0))
    pdfmetrics.registerFont(TTFont('Q6Hei','C:/Windows/Fonts/simhei.ttf'))
    pdfmetrics.registerFontFamily('Q6Song',normal='Q6Song',bold='Q6Hei',italic='Q6Song',boldItalic='Q6Hei')
    width=A4[0]-2*56.7
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Q6Body',fontName='Q6Song',fontSize=12,leading=19,wordWrap='CJK',spaceAfter=7))
    styles.add(ParagraphStyle(name='Q6Title',fontName='Q6Hei',fontSize=18,leading=26,alignment=TA_CENTER,spaceAfter=16))
    styles.add(ParagraphStyle(name='Q6H2',fontName='Q6Hei',fontSize=14,leading=22,spaceBefore=13,spaceAfter=8,keepWithNext=True))
    styles.add(ParagraphStyle(name='Q6H3',fontName='Q6Hei',fontSize=12,leading=20,spaceBefore=9,spaceAfter=6,keepWithNext=True))
    styles.add(ParagraphStyle(name='Q6Caption',fontName='Q6Song',fontSize=10.5,leading=15,alignment=TA_CENTER,spaceAfter=10))
    styles.add(ParagraphStyle(name='Q6Cell',fontName='Q6Song',fontSize=12,leading=17,wordWrap='CJK'))
    mapping=json.loads((TMP/'math_images.json').read_text(encoding='utf-8'))
    def inline(s):
        # Protect inline formulas before escaping the remaining prose.
        parts=re.split(r'(\\\(.*?\\\))',s)
        rendered=[]
        for part in parts:
            if part.startswith(r'\('):
                m=mapping[part[2:-2]]
                rendered.append('<img src="%s" width="%.2f" height="%.2f" valign="middle"/>'%(m['path'],m['width'],m['height']))
            else:
                z=html.escape(part)
                z=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',z)
                z=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<link href="\2" color="#235e83">\1</link>',z)
                rendered.append(z)
        return ''.join(rendered)
    doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=56.7,leftMargin=56.7,topMargin=55,bottomMargin=49,
      title='第六题：保护资源配置模型的跨大陆适配（阅读预览）',author='2026-HiMCM')
    story=[Paragraph('第六部分：保护资源配置模型的跨大陆适配',styles['Q6Title']),
      Paragraph('阅读预览；由同步正文排版。LaTeX源码为正式编辑文件，尚未通过TeX编译。',styles['Q6Caption'])]
    lines=MD.read_text(encoding='utf-8').splitlines();i=1;display_index=0;subsection=0;subsub=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith(r'\['):
            while i<len(lines) and r'\]' not in lines[i]:i+=1
            group=[]
            numbers=[['6-1'],['6-2','6-3'],['','','','','6-4'],['6-5'],['6-6']][display_index]
            for idx,formula in enumerate(DISPLAY[display_index]):
                m=mapping[formula];scale=min(1,(width-55)/m['width'])
                image=Image(m['path'],width=m['width']*scale,height=m['height']*scale)
                label=Paragraph('（'+numbers[idx]+'）' if numbers[idx] else '',styles['Q6Caption'])
                row=Table([[image,label]],colWidths=[width-55,55])
                row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(0,0),'CENTER'),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
                group.append(row);group.append(Spacer(1,4))
            story.append(KeepTogether(group));display_index+=1;i+=1;continue
        if line.startswith('### '):
            subsub+=1;story.append(Paragraph(f'6.{subsection}.{subsub} '+inline(line[4:]),styles['Q6H3']));i+=1;continue
        if line.startswith('## '):
            subsection+=1;subsub=0;story.append(Paragraph(f'6.{subsection} '+inline(line[3:]),styles['Q6H2']));i+=1;continue
        if line.startswith('!['):
            rel=re.search(r'\]\(([^)]+)\)',line).group(1);path=(MD.parent/rel).resolve()
            img=Image(str(path));scale=width/img.imageWidth
            story.append(Image(str(path),width=width,height=img.imageHeight*scale));i+=1;continue
        if line.startswith(('图6-','表6-')):
            story.append(Paragraph(inline(line),styles['Q6Caption']));i+=1;continue
        if line.startswith('| '):
            tablelines=[]
            while i<len(lines) and lines[i].strip().startswith('| '):tablelines.append(lines[i].strip());i+=1
            rows=[[v.strip() for v in s.strip('|').split('|')] for s in tablelines if not set(s.replace('|','').replace(' ',''))<=set('-:')]
            n=len(rows[0]);cw={3:[65,(width-65)/2,(width-65)/2],5:[55,42,width-55-42-55-95,55,95],6:[38,width-38-40-86-87-38,40,86,87,38]}[n]
            matrix=[[Paragraph(inline(cell),styles['Q6Cell']) for cell in row] for row in rows]
            table=Table(matrix,colWidths=cw,repeatRows=1,hAlign='CENTER')
            table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEABOVE',(0,0),(-1,0),1,colors.HexColor('#235e83')),
              ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#235e83')),('LINEBELOW',(0,-1),(-1,-1),1,colors.HexColor('#235e83')),
              ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf3f6'))]))
            story.append(table);story.append(Spacer(1,10));continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','![','| ',r'\[')):
            paragraph.append(lines[i].strip());i+=1
        story.append(Paragraph(inline(''.join(paragraph)),styles['Q6Body']))
    def footer(canvas,document):
        canvas.setFont('Q6Song',9);canvas.setFillColor(colors.HexColor('#657584'))
        canvas.drawString(56.7,27,'第六题阅读预览 · 情景人数不代表公园实际编制')
        canvas.drawRightString(A4[0]-56.7,27,str(document.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(PDF)
    report=dict(status='reading_pdf_created',pages=len(reader.pages),format='ReportLab reading preview, not LaTeX compilation',
      source_sha256=hashlib.sha256(MD.read_bytes()).hexdigest(),pdf_sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),
      extracted_text_contains_results=all(s in ''.join(p.extract_text() for p in reader.pages) for s in ['1265.01','1834.56','1740.58']),
      latex_compilation_status='unverified: built-in compiler platform directories error; local TeX installation lacks formats')
    (ROOT/'output/question6/q6_reading_pdf_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Reading PDF saved:',len(reader.pages),'pages.')

if __name__=='__main__':
    render_math() if sys.argv[1]=='math' else render_pdf()
