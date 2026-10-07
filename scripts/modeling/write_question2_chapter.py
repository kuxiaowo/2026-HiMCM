"""Write the formal Q2 chapter in place from saved, audited model results.

The open standalone .tex embeds its TikZ figures. This is a presentation
generator, not a new solver or a source of observations.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / 'docs/paper'
FIGURES = ROOT / 'output/question2/paper_figures'

PREAMBLE = r'''\documentclass[UTF8,fontset=fandol,12pt,a4paper]{ctexart}
\usepackage[margin=2cm]{geometry}
\usepackage{amsmath,amssymb,booktabs,tabularx,array}
\usepackage{graphicx,xcolor,tikz,caption,placeins,hyperref}
\usetikzlibrary{arrows.meta}
\hypersetup{hidelinks}
\captionsetup{font=small,labelfont=bf,labelsep=quad}
\setcounter{secnumdepth}{3}
\setcounter{section}{1}
\renewcommand{\theequation}{2-\arabic{equation}}
\renewcommand{\thefigure}{2-\arabic{figure}}
\renewcommand{\thetable}{2-\arabic{table}}
\allowdisplaybreaks
\setlength{\parskip}{0.25em}
\setlength{\textfloatsep}{12pt plus 2pt minus 2pt}
\setlength{\intextsep}{10pt plus 2pt minus 2pt}
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.15}
\emergencystretch=2em
\title{第二部分：有限资源下的人机协同保护资源配置模型}
\author{}
\date{}
\begin{document}
\maketitle
\vspace{-1.5em}
'''

from q2_compact_body import BODY

REFERENCES = [
    ('survey', '2015年埃托沙航空动物调查报告（本项目数量来源）',
     'https://rhinoresourcecenter.com/wp-content/uploads/2022/01/1642693511.pdf'),
    ('law', 'Nature Conservation Ordinance 4 of 1975，法规汇编',
     'https://namibiatradeportal.gov.na/application/files/3617/2986/2681/Nature_Conservation_Ordinance_4_of_1975.pdf'),
    ('worldcover', 'ESA WorldCover 2021，v200，数据与分类说明',
     'https://esa-worldcover.org/en/data-access'),
    ('osm', 'OpenStreetMap / Geofabrik，Namibia数据下载入口（使用项目固定快照）',
     'https://download.geofabrik.de/africa/namibia.html'),
    ('paws', 'Deploying PAWS: Field Optimization of the Protection Assistant for Wildlife Security，2016（图表表达参考）',
     'https://doi.org/10.1609/aaai.v30i2.19070'),
    ('community', 'Improving Community-Participated Patrol for Anti-Poaching，2025（图表表达参考）',
     'https://doi.org/10.1609/aaai.v39i27.35072'),
]


def table(label, caption, heads, rows, colspec=None, note=''):
    """Return matched LaTeX and Markdown table representations."""
    colspec = colspec or ('l' + 'r' * (len(heads)-1))
    tabular = 'tabularx' if 'X' in colspec else 'tabular'
    args = r'{\linewidth}{' + colspec + '}' if tabular == 'tabularx' else '{'+colspec+'}'
    tex = [r'\begin{table}[htbp]', r'\centering\small',
           r'\caption{'+caption+'}', r'\label{'+label+'}',
           r'\begin{'+tabular+'}'+args, r'\toprule',
           ' & '.join(heads)+r' \\', r'\midrule']
    tex += [' & '.join(row)+r' \\' for row in rows]
    tex += [r'\bottomrule', r'\end{'+tabular+'}']
    if note: tex += [r'\par\smallskip\begin{minipage}{\linewidth}\footnotesize '+note+r'\end{minipage}']
    tex += [r'\end{table}']
    md = ['| '+' | '.join(heads)+' |', '| '+' | '.join(['---']*len(heads))+' |']
    md += ['| '+' | '.join(row)+' |' for row in rows]
    return '\n'.join(tex), caption+'\n\n'+'\n'.join(md)+'\n\n'+note


def figure(name, label, caption):
    tikz = (FIGURES/(name+'.tikz')).read_text(encoding='utf-8')
    tex = '\n'.join([r'\begin{figure}[htbp]',r'\centering',r'\resizebox{\linewidth}{!}{%',
                    tikz.rstrip(),'}',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{figure}'])
    md = f'![{caption}](../../output/question2/paper_figures/{name}.png)\n\n'+caption
    return tex, md


def number(v, digits=2):
    if 0 < v < .5*10**(-digits): return '<'+f'{10**(-digits):.{digits}f}'
    return f'{v:.{digits}f}'


def residual_bound(v):
    if v<=0:return '0'
    exponent=math.floor(math.log10(v))
    mantissa=math.ceil(v/10**(exponent-1))/10
    return f'{mantissa:.1f}'+r'\times10^{'+str(exponent)+'}'


def markdown(body, labels):
    """Keep equations, convert the same prose/headings, resolve numbered refs."""
    counters=[1,0,0]
    def heading(m):
        kind, title=m.group(1),m.group(2)
        level=['section','subsection','subsubsection'].index(kind)
        counters[level]+=1
        for k in range(level+1,3):counters[k]=0
        return '#'*(level+1)+' '+'.'.join(str(k) for k in counters[:level+1])+' '+title
    body=re.sub(r'\\(section|subsection|subsubsection)\{([^{}]+)\}',heading,body)
    body=re.sub(r'\\eqref\{([^}]+)\}',lambda m:'（'+labels[m.group(1)]+'）',body)
    body=re.sub(r'\\ref\{([^}]+)\}',lambda m:labels[m.group(1)],body)
    body=re.sub(r'\\cite\{([^}]+)\}',lambda m:'['+'，'.join(m.group(1).split(','))+']',body)
    def numbered_equation(m):
        label=re.search(r'\\label\{([^}]+)\}',m.group(1)).group(1)
        return '\\[\n'+m.group(1).strip()+'\n\\tag{'+labels[label]+'}\n\\]'
    body=re.sub(r'\\begin\{equation\}(.*?)\\end\{equation\}',numbered_equation,body,flags=re.S)
    body=re.sub(r'\\label\{[^}]+\}', '', body)
    body=re.sub(r'\\texttt\{([^}]+)\}',lambda m:'`'+m.group(1).replace(r'\_','_')+'`',body)
    body=body.replace(r'\FloatBarrier','')
    # In prose and table cells, TeX escapes are not required. Preserve math escapes.
    chunks=re.split(r'(\\\[.*?\\\]|\\\(.*?\\\))',body,flags=re.S)
    for i in range(0,len(chunks),2):chunks[i]=chunks[i].replace(r'\%','%').replace(r'\_','_')
    return '\n'.join(line.rstrip() for line in ''.join(chunks).splitlines()).strip()+'\n'


def main():
    from q2_compact_writer import write_compact_chapter
    write_compact_chapter()


if __name__ == '__main__':
    main()
