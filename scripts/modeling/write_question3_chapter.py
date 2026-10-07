"""Write synchronized formal Q3 Markdown and standalone LaTeX from saved results.

The chapter has five subsections and thirteen subsubsections. This generator
does not rerun or modify the scientific model. Figures are embedded as TikZ.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from write_question2_chapter import table, PREAMBLE as Q2_PREAMBLE

ROOT=Path(__file__).resolve().parents[2]
PAPER=ROOT/'docs/paper'
FIGURES=ROOT/'output/question3/paper_figures'
PREAMBLE=Q2_PREAMBLE.replace(r'\setcounter{section}{1}',r'\setcounter{section}{2}').replace('2-\\arabic','3-\\arabic').replace('第二部分：有限资源下的人机协同保护资源配置模型','第三部分：季节需求下的保护服务评估与人员需求模型')
PREAMBLE=PREAMBLE.replace('12pt,a4paper','11pt,a4paper').replace(r'\maketitle',r'\noindent\textbf{第三题：六页精简稿}\par').replace(r'\vspace{-1.5em}',r'\vspace{0.2em}')

from q3_compact_body import BODY

REFERENCES=[
    ('season','Interplay of physical and social drivers of movement in male African savanna elephants，2024，原研究数据说明',
     'https://datadryad.org/dataset/doi:10.5061/dryad.4qrfj6qm3'),
    ('fire','Namibia Fire Management Strategy，2016，Etosha章节',
     'https://www.meft.gov.na/files/downloads/66c_Fire%20Management_Strategy%20Final%20Version.pdf'),
    ('water','Riddell等，Groundwater stable isotope profile of the Etosha National Park, Namibia，Koedoe，2016，58(1)，a1329',
     'https://koedoe.co.za/index.php/koedoe/article/view/1329/1890'),
    ('annual','MEFT Annual Report 2021/2022，水点系统改造记录',
     'https://www.meft.gov.na/files/downloads/MEFT%20Annual%20Report%202021-2022.pdf'),
    ('paws','Deploying PAWS: Field Optimization of the Protection Assistant for Wildlife Security，2016（图表表达参考）',
     'https://doi.org/10.1609/aaai.v30i2.19070'),
    ('community','Improving Community-Participated Patrol for Anti-Poaching，2025（图表表达参考）',
     'https://doi.org/10.1609/aaai.v39i27.35072')]


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def figure(name,label,caption):
    tikz=(FIGURES/(name+'.tikz')).read_text(encoding='utf-8')
    tex='\n'.join([r'\begin{figure}[htbp]',r'\centering',r'\resizebox{\linewidth}{!}{%',tikz.rstrip(),'}',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{figure}'])
    return tex,f'![{caption}](../../output/question3/paper_figures/{name}.png)\n\n'+caption


def markdown(body,labels):
    counters=[2,0,0]
    def heading(m):
        level=['section','subsection','subsubsection'].index(m.group(1));counters[level]+=1
        for k in range(level+1,3):counters[k]=0
        return '#'*(level+1)+' '+'.'.join(map(str,counters[:level+1]))+' '+m.group(2)
    body=re.sub(r'\\(section|subsection|subsubsection)\{([^{}]+)\}',heading,body)
    body=re.sub(r'\\eqref\{([^}]+)\}',lambda m:'（'+labels[m.group(1)]+'）',body)
    body=re.sub(r'\\ref\{([^}]+)\}',lambda m:labels[m.group(1)],body)
    body=re.sub(r'\\cite\{([^}]+)\}',lambda m:'['+'，'.join(m.group(1).split(','))+']',body)
    def eq(m):
        label=re.search(r'\\label\{([^}]+)\}',m.group(1)).group(1)
        return '\\[\n'+re.sub(r'\\label\{[^}]+\}','',m.group(1)).strip()+'\n\\tag{'+labels[label]+'}\n\\]'
    body=re.sub(r'\\begin\{equation\}(.*?)\\end\{equation\}',eq,body,flags=re.S)
    body=body.replace(r'\FloatBarrier','').replace(r'\clearpage','')
    chunks=re.split(r'(\\\[.*?\\\]|\\\(.*?\\\))',body,flags=re.S)
    for i in range(0,len(chunks),2):chunks[i]=chunks[i].replace(r'\%','%').replace(r'\_','_')
    return '\n'.join(line.rstrip() for line in ''.join(chunks).splitlines()).strip()+'\n'


def main():
    paths=['output/question2/q2_model_inputs.json','output/question2/q2_results.json','output/question3/q3_results.json','output/question3/q3_independent_verification.json','data/modeling/q3_assumptions.json','data/question3/processed/water_points.json']
    before={p:sha(p) for p in paths}; d,r,result,audit,ass,water=[read(p) for p in paths]
    assert audit['passed'] and result['verification_summary']['passed']
    peak=result['monthly'][7]; wet=result['monthly'][0]
    stress=next(v for v in result['full_sensitivity_solutions'] if v['name']=='base_drought')
    stress=next(v for v in stress['solutions'] if v['period']['month']==8)
    inv=stress['inverse']; fwd=stress['fixed_reference']
    fmt=lambda x:f'{x:.2f}'
    numbers={'FIRE_REACH':fmt(peak['extra_fire_checks']),'FIRE_OUT':fmt(peak['unreachable_extra_fire_checks']),
             'TRAVEL_SUM':f"{sum(v['round_travel_hours'] for v in water['points'] if v['included']):.5f}",
             'WATER_WET':fmt(wet['water_hours']),'WATER_DRY':fmt(peak['water_hours']),
             'FREE_BASE':fmt(result['verification_summary']['free_equal_score_baseline_person_hours']),
             'Q2_BASE':fmt(r['optimum']['total_person_hours']),
             'SAVE_BASE':fmt(result['verification_summary']['free_equal_score_reallocation_saves_person_hours']),
             'PEAK_HOURS':fmt(peak['required_person_hours']),'PEAK_SPARE':fmt(ass['fixed_reference_staff']*120-peak['required_person_hours']),
             'BASE_MONITOR':fmt(peak['base_monitoring_person_hours']),'FIRE_HOURS':fmt(peak['extra_fire_person_hours']),
             'ANNUAL_STAFF':str(result['annual_fixed_staff_base_scenario']),
             'FEWER_SCORE':fmt(result['verification_summary']['one_fewer_peak_staff_forward_score']),
             'WATER_STRESS':fmt(inv['water_hours']),'STRESS_HOURS':fmt(inv['total_person_hours']),
             'STRESS_STAFF':str(inv['required_staff']),'STRESS_SCORE':fmt(fwd['score']),
             'STRESS_GAP':fmt(result['target_score']-fwd['score'])}
    blocks={}
    blocks['TAB_SETTINGS']=table('tab:settings','继承输入与月度规划设置',
        ['设置','数值或定义','来源与用途'],[
        ['空间与服务基线','17父区、599单元；原权重与成本','继承第二题'],
        ['人数与有效工时','177人；120小时/人月',r'60\%可用比例为规划假设'],
        ['日间响应预留','2880人时/月','六候选驻点的共享响应'],
        ['无人机预算','30架，共1200机时/月','基准监测与火险共用'],
        ['规划时期','12个标准30天月','按月求解、允许重新配置'],
        ['人工水点样本','17处BH钻井','2013年历史样本，情景中假设需维护']],
        'p{3.0cm}p{5.8cm}X',
        '注：候选驻点及岗位参与比例为规划设定；历史水点样本不代表当前全园完整运行清单。')
    blocks['TAB_SEASON']=table('tab:season','中档季节窗口与新增服务规则',
        ['月份','水点规则','目标间隔/天',r'\(f_t\)/次',r'\(k_t\)/点次'],[
        ['1—4月、12月','湿季常规','15','2','0'],['5—7月','旱季、早期火窗口','7.5','4','2'],
        ['8—10月','旱季、晚期火窗口','7.5','4','4'],['11月','湿季、晚期火窗口','15','2','4']],
        'lp{4.2cm}rrr',
        r'注：\(f_t\)为每水点每月访问次数；\(k_t\)为每100 \(\mathrm{km}^2\)可燃生境每月额外检查点次。正常现场耗时均设为0.5小时/次。')
    blocks['TAB_VARIABLES']=table('tab:variables','月度线性规划的五组决策变量',
        ['符号','含义','单位'],[
        [r'\(x_{jt}\)','基准监测地面投入','人时/月'],[r'\(h_{jt}\)','基准监测无人机投入','机时/月'],
        [r'\(s_{jt}\)','基准规定检查完成率','无量纲，0至'+r'\(r_j\)'],
        [r'\(y_{jt}\)','额外火险检查地面投入','人时/月'],[r'\(v_{jt}\)','额外火险检查无人机投入','机时/月']],
        'p{2.2cm}Xp{4.0cm}',
        r'注：\(a_j,b_j,\gamma_j,C_j,D_{jt},W_t\)均为输入；\(N_t^{\mathrm{plan}}\)为求解后换算结果。')
    rows=[]
    for month,name in [(1,'1—4月、12月'),(5,'5—7月'),(8,'8—10月'),(11,'11月')]:
        v=result['monthly'][month-1]
        rows.append([name,fmt(v['required_person_hours']),str(v['required_staff']),fmt(v['flight_hours']),fmt(v['fixed_reference_score'])])
    blocks['TAB_RESULTS']=table('tab:results','维持同一服务目标的季节资源需求',
        ['月份','最少人时/月','规划人数','使用机时/月','177人服务分'],rows,
        note='注：最少人时含共享响应、监测配套人工、额外火险与水点运维；人数按120小时/人月向上取整。')
    blocks['TAB_DROUGHT']=table('tab:drought','常规与异常干旱的峰值资源对照',
        ['指标','常规季节','异常干旱'],[
        ['水点人时/月',fmt(peak['water_hours']),fmt(inv['water_hours'])],
        ['总人时/月',fmt(peak['required_person_hours']),fmt(inv['total_person_hours'])],
        ['全年规划人数',str(result['annual_fixed_staff_base_scenario']),str(inv['required_staff'])],
        ['飞行机时/月',fmt(peak['flight_hours']),fmt(inv['total_flight_hours'])],
        ['177人最高服务分',fmt(peak['fixed_reference_score']),fmt(fwd['score'])]],
        note='注：异常干旱仅提高旱季水点频次与现场耗时，不是观测事件或统计预测。')
    specs=[('FIG_WATER','fig2_water_points_and_workload','fig:water','17处历史钻井及旱季运维成本。圆点为钻井，星形为候选驻点；右图区分往返、现场与准备人时。点位和道路组成规划基线，不代表当前运行清单或实际维护轨迹。'),
           ('FIG_MONTHLY','fig3_monthly_hours_and_staff','fig:monthly','中档规则下的月度人时构成与人员需求。177人的21240人时预算高于图示范围；下图虚线为全年常规57人需求。')]
    for key,name,label,caption in specs:blocks[key]=figure(name,label,caption)
    design='图件由本项目固定输入与保存解原创绘制；建模模块思路参考PAWS，多面板地图及资源比较的呈现参考社区巡护研究。'
    texrefs=[design+r'\cite{paws,community}',r'\begingroup\footnotesize',r'\begin{thebibliography}{9}',r'\raggedright\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}']
    mdrefs=['**本部分资料与图表设计参考**\n']
    for key,title,url in REFERENCES:
        texrefs.append(r'\bibitem{'+key+'} '+title+r'。\url{'+url+'}。')
        mdrefs.append(f'- [{title}]({url}) [{key}]')
    texrefs.append(r'\end{thebibliography}\endgroup')
    blocks['REFERENCES']=('\n'.join(texrefs),'\n'.join(mdrefs)+'\n\n'+design)
    texbody=BODY;md_body=BODY
    for key,v in numbers.items():texbody=texbody.replace('@'+key+'@',v);md_body=md_body.replace('@'+key+'@',v)
    for key,(tex,md) in blocks.items():texbody=texbody.replace('@'+key+'@',tex);md_body=md_body.replace('@'+key+'@',md)
    labels={}
    eqs=re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}',texbody,flags=re.S)
    for i,eq in enumerate(eqs,1):labels.update({label:f'3-{i}' for label in re.findall(r'\\label\{([^}]+)\}',eq)})
    for kind in ['figure','table']:
        for i,block in enumerate(re.findall(r'\\begin\{'+kind+r'\}(.*?)\\end\{'+kind+r'\}',texbody,flags=re.S),1):
            label=re.search(r'\\label\{([^}]+)\}',block).group(1);labels[label]=f'3-{i}'
            token=next(k for k,v in blocks.items() if '\\label{'+label+'}' in v[0])
            md_block=blocks[token][1]
            if kind=='figure':pic,caption=md_block.split('\n\n',1);md_block=pic+'\n\n'+f'图3-{i}：'+caption
            else:md_block=f'表3-{i}：'+md_block
            md_body=md_body.replace(blocks[token][1],md_block)
    refs=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',texbody)
    assert all(k in labels for k in refs)
    assert not re.search(r'@[A-Z_]+@',texbody)
    tex=PREAMBLE+texbody+'\n\\end{document}\n'
    md='# 第三题正式正文\n\n'+markdown(md_body,labels)
    md+='\n计算附件：[完整月度结果](../../output/question3/q3_results.json)、[月表](../../output/question3/q3_monthly.csv)、[独立核验](../../output/question3/q3_independent_verification.json)、[参数假设](../../data/modeling/q3_assumptions.json)、[计算记录](../第三题模型实算.md)、[图表设计来源](../modeling_notes/q3_figure_design_references.md)。\n'
    PAPER.mkdir(parents=True,exist_ok=True)
    (PAPER/'question3_framework.tex').write_text(tex,encoding='utf-8')
    (PAPER/'question3_seasonal_staffing.md').write_text(md,encoding='utf-8')
    assert before=={p:sha(p) for p in paths}
    manifest={'status':'formal_chapter_written_compilation_pending','sections':5,'subsections':13,
              'equations':len(eqs),'figures':2,'tables':3,'labels':labels,'source_sha256':before,
              'tex_sha256':sha('docs/paper/question3_framework.tex'),
              'markdown_sha256':sha('docs/paper/question3_seasonal_staffing.md'),
              'notes':['same prose and values in Markdown and LaTeX','all TikZ inline; no additional compiler project files',
                       'synchronized to Q2 60 percent staff availability and 30 aircraft; Q3 model recomputed and independently audited', 'explicit page breaks group the chapter into six readable pages','sensitivity and evaluation remain in Q4/Q5']}
    (ROOT/'output/question3/q3_chapter_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ['status','sections','subsections','equations','figures','tables']},ensure_ascii=False))


if __name__=='__main__':main()
