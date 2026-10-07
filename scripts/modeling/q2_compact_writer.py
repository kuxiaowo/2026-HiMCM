"""Generate the synchronized eight-page Q2 source and Markdown manuscript."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

from q2_compact_body import BODY
from write_question2_chapter import PREAMBLE, REFERENCES, table, figure, number, markdown

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / 'docs/paper'
FIGURES = ROOT / 'output/question2/paper_figures'


def compact_table(*args, **kwargs):
    tex, md = table(*args, **kwargs)
    tex = tex.replace(r'\begin{table}[htbp]', r'\begin{table}[H]')
    tex = tex.replace(r'\centering\small', r'\centering\normalsize')
    tex = tex.replace(r'\footnotesize ', r'\normalsize ')
    return tex, md


def compact_figure(*args):
    tex, md = figure(*args)
    return tex.replace(r'\begin{figure}[htbp]', r'\begin{figure}[H]'), md


def write_compact_chapter():
    rp = ROOT / 'output/question2/q2_results.json'
    ip = ROOT / 'output/question2/q2_model_inputs.json'
    r = json.loads(rp.read_text(encoding='utf-8'))
    d = json.loads(ip.read_text(encoding='utf-8'))
    verification = json.loads((ROOT/'output/question2/q2_verification.json').read_text(encoding='utf-8'))
    assert verification['status'] == 'passed'
    assert r['excluded_factors'] == ['water_supply', 'precipitation']
    assert d['config']['protection_staff_fraction'] == 0.6 and d['config']['drone_count'] == 30
    base = r['optimum']
    reduced = r['scarce_budget_comparisons'][-1]['result']
    no_drone = next(v['result'] for v in r['scenarios'] if v['name'] == '无人机停用')
    best_forward = r['best_forward_post']['result']
    rows = sorted(r['regions'], key=lambda v: -v['demand_weight'])
    by = {v['region_id']:v for v in rows}
    example = json.loads((FIGURES/'figure_manifest.json').read_text(encoding='utf-8'))['cost_example']
    area = sum(t['support_area_km2'] for t in d['targets'])
    reach = sum(t['support_area_km2'] for t in d['targets'] if t['response_eligible'])
    ent = r['management_weight_estimation']
    values = {
        'TARGETS':str(len(d['targets'])), 'VARIABLES':str(3*len(d['targets'])),
        'ENTRIES':str(d['candidate_entry_count']),
        'REACHABLE':str(sum(t['response_eligible'] for t in d['targets'])),
        'DRONE_ELIGIBLE':str(sum(t['drone_allowed'] for t in d['targets'])),
        'REACH_AREA':f'{reach:.2f}', 'REACH_SHARE':f'{reach/area*100:.2f}',
        'AHP_WEIGHTS':','.join(f'{v:.6f}' for v in r['AHP']['category_weights']),
        'AHP_CR':f"{r['AHP']['CR']:.6f}",
        'ALPHA_A':f"{ent['weights'][0]:.6f}", 'ALPHA_F':f"{ent['weights'][1]:.6f}",
        'COST_TARGET':example['target_id'].replace('_',r'\_'),
        'GROUND_EXAMPLE':f"{example['ground_person_hours']:.3f}",
        'OPERATOR_EXAMPLE':f"{example['operator_person_hours']:.3f}",
        'FLIGHT_EXAMPLE':f"{example['flight_hours']:.3f}",
        'CHECKS':f"{sum(t['planned_checks_month'] for t in d['targets']):.2f}",
        'HUMAN_BUDGET':f"{base['human_budget']:.0f}", 'DRONE_BUDGET':f"{base['drone_budget']:.0f}",
        'MONITORING_BUDGET':f"{base['human_budget']-base['response_reserved_hours']:.0f}",
        'BASE_SCORE':f"{base['score']:.2f}", 'BASE_FLIGHT':f"{base['drone_flight_hours']:.2f}",
        'BASE_OPERATOR':f"{base['drone_operator_hours']:.2f}", 'BASE_HUMAN':f"{base['total_person_hours']:.2f}",
        'HUMAN_IDLE':f"{base['human_budget']-base['total_person_hours']:.2f}",
        'DRONE_IDLE':f"{base['drone_budget']-base['drone_flight_hours']:.2f}",
        'ENP1_HOURS':f"{by['ENP1']['allocated_monitoring_person_hours']:.2f}",
        'ENP12_HOURS':f"{by['ENP12']['allocated_monitoring_person_hours']:.2f}",
        'PAN_SERVICE':f"{100*by['PAN_MAIN']['service_completion_fraction']:.2f}",
        'NODRONE_SCORE':f"{no_drone['score']:.2f}", 'NODRONE_HUMAN':f"{no_drone['total_person_hours']:.2f}",
        'FORWARD_SCORE':f"{best_forward['score']:.2f}",
        'FORWARD_GAIN':f"{best_forward['score']-base['score']:.2f}",
        'MOBILE_NOTE':f"在同一最优服务分下，两种方案均全局最小化人时，协同方案少{no_drone['total_person_hours']-base['total_person_hours']:.2f}人时；该差异限于当前任务与技术等效假设。",
    }
    blocks = {}
    blocks['TAB_PARAMETERS'] = compact_table('tab:parameters','主要规划参数', ['项目','数值与口径'],[
        ['空间及频次',r'10 km格网；每100 km\(^2\)每月8点次'],
        ['移动速度','道路30、步行4、飞行40 km/h'],
        ['作业时长','观察10、准备5、调度10分钟；两类队伍各2人'],
        ['响应安排','2小时内到场；六处各2人，每日8小时、每月30天'],
        ['无人机适用',r'单次飞行不超过0.6小时；父区开阔比例至少60\%'],
        ['需求及底线',r'进入衰减尺度2小时；可响应部分最低服务15\%'],
        ['人员资源',r'295人参考，60\%可用；120小时/人月'],
        ['无人机资源','30架；每架每日2小时，每月20个可飞行日'],
    ],'p{3.1cm}X')
    regional = []
    for v in rows:
        label = {'PAN_MAIN':'主盐沼*','UNSURVEYED_OTHER':'调查外其他*'}.get(v['region_id'],v['region_id'])
        regional.append([label,number(100*v['demand_weight']),number(100*v['response_reachable_area_fraction']),
                        number(100*v['service_completion_fraction']),number(v['allocated_monitoring_person_hours']),
                        number(v['drone_flight_hours'])])
    blocks['TAB_REGIONS'] = compact_table('tab:regions','17区需求与基准配置',
        ['父区',r'需求/\%',r'可响应/\%',r'服务/\%','人工/人时','飞行/机时'],regional,
        note='注：人工不含共享响应预留。*动物资料未知；低于显示精度的小正值写作“<0.01”。')
    comparison = []
    for label,key in [('基准','comparisons'),(r'人员减少40\%','scarce_budget_comparisons')]:
        items = r[key]
        comparison.append([label,f"{items[-1]['result']['human_budget']:.0f}"]+[number(v['result']['score']) for v in items])
    blocks['TAB_COMPARISON'] = compact_table('tab:comparison','同预算配置的服务分',
        ['情景','人时上限','面积均衡','需求比例','优化'],comparison)
    forward = [['原布局','2880',number(base['score']),number(base['total_person_hours']),number(base['drone_flight_hours'])]]
    for v in r['forward_post_options']:
        rr=v['result']
        forward.append(['新增'+v['target_region'],f"{rr['response_reserved_hours']:.0f}",number(rr['score']),
                        number(rr['total_person_hours']),number(rr['drone_flight_hours'])])
    blocks['TAB_FORWARD'] = compact_table('tab:forward','相同总预算下的新增驻点比较',
        ['布局','响应人时','服务分','总人时','机时'],forward)
    blocks['FIG_COSTS'] = compact_figure('fig4_route_and_cost','fig:costs','检查路线与单次人时；机时单独核算。')
    blocks['FIG_MAPS'] = compact_figure('fig3_demand_response_maps','fig:maps',
        '需求与服务地图。星形为驻点，红点为2小时内不可响应单元；图形仅作显示简化。')
    reference_titles = {'survey':'埃托沙航空动物调查，2015。','law':'Nature Conservation Ordinance 4 of 1975，法规汇编。',
                        'worldcover':'ESA WorldCover 2021，v200。','osm':'OpenStreetMap / Geofabrik，Namibia固定快照。'}
    tx=[r'\begin{thebibliography}{9}',r'\raggedright\setlength{\itemsep}{0pt}']
    md=['**资料来源**\n']
    for key,title,url in REFERENCES:
        if key not in reference_titles: continue
        tx.append(r'\bibitem{'+key+'} '+reference_titles[key]+r'\url{'+url+'}')
        md.append(f'- [{reference_titles[key]}]({url}) [{key}]')
    tx.append(r'\end{thebibliography}')
    blocks['REFERENCES']=('\n'.join(tx),'\n'.join(md))
    texbody=BODY
    mdbody=BODY
    for key,value in values.items():
        texbody=texbody.replace('@'+key+'@',value)
        mdbody=mdbody.replace('@'+key+'@',value)
    for key,(tx,md) in blocks.items():
        texbody=texbody.replace('@'+key+'@',tx)
        mdbody=mdbody.replace('@'+key+'@',md)
    assert not re.search(r'@[A-Z_]+@',texbody)
    labels={}
    eqs=re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}',texbody,re.S)
    for i,eq in enumerate(eqs,1):
        for label in re.findall(r'\\label\{([^}]+)\}',eq):labels[label]=f'2-{i}'
    for kind in ['figure','table']:
        for i,block in enumerate(re.findall(r'\\begin\{'+kind+r'\}(.*?)\\end\{'+kind+r'\}',texbody,re.S),1):
            label=re.search(r'\\label\{([^}]+)\}',block).group(1)
            labels[label]=f'2-{i}'
            token=next(k for k,v in blocks.items() if '\\label{'+label+'}' in v[0])
            mdblock=blocks[token][1]
            if kind=='figure':
                pic,caption=mdblock.split('\n\n',1)
                numbered=pic+'\n\n'+f'图2-{i}：'+caption
            else:numbered=f'表2-{i}：'+mdblock
            mdbody=mdbody.replace(mdblock,numbered)
    refs=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',texbody)
    assert all(v in labels for v in refs)
    pre=PREAMBLE.replace(r'\usetikzlibrary',r'\usepackage{float}'+'\n'+r'\usetikzlibrary')
    pre=pre.replace(r'\maketitle'+'\n'+r'\vspace{-1.5em}',
        r'''\pagestyle{plain}
\linespread{1.05}\selectfont
\ctexset{section={format=\Large\bfseries,beforeskip=6pt,afterskip=5pt},
subsection={format=\large\bfseries,beforeskip=6pt,afterskip=3pt},
subsubsection={format=\normalsize\bfseries,beforeskip=4pt,afterskip=2pt}}
\setlength{\abovedisplayskip}{6pt}\setlength{\belowdisplayskip}{6pt}
\setlength{\abovedisplayshortskip}{4pt}\setlength{\belowdisplayshortskip}{4pt}
\setlength{\parskip}{2pt}''')
    pre=pre.replace('font=small,labelfont','font=normalsize,labelfont').replace(r'\arraystretch}{1.15}',r'\arraystretch}{1.08}')
    pre=pre.replace(r'\setlength{\textfloatsep}{12pt plus 2pt minus 2pt}',r'\setlength{\textfloatsep}{8pt}')
    pre=pre.replace(r'\setlength{\intextsep}{10pt plus 2pt minus 2pt}',r'\setlength{\intextsep}{8pt}')
    tex=pre+texbody+'\n\\end{document}\n'
    md='# 第二题正式正文（8页精简版）\n\n'+markdown(mdbody.replace(r'\clearpage',''),labels)
    md=re.sub(r'\\textbf\{([^{}]+)\}',r'**\1**',md).replace(r'\noindent','')
    md+='\n计算附件：[输入](../../output/question2/q2_model_inputs.json)、[结果](../../output/question2/q2_results.json)、[核验](../../output/question2/q2_verification.json)、[图件来源](../modeling_notes/q2_figure_design_references.md)。旧版已归档，不作为本轮结果。\n'
    (PAPER/'question2_framework.tex').write_text(tex,encoding='utf-8')
    (PAPER/'question2_resource_allocation.md').write_text(md,encoding='utf-8')
    manifest={'status':'compact_chapter_written_pdf_compilation_pending','target_pages':8,
        'sections':len(re.findall(r'\\subsection\{',texbody)),'subsections':len(re.findall(r'\\subsubsection\{',texbody)),
        'equations':len(eqs),'figures':2,'tables':4,'labels':labels,
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [rp,ip]},
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'tex_sha256':hashlib.sha256((PAPER/'question2_framework.tex').read_bytes()).hexdigest(),
        'parameters':{'protection_staff_fraction':0.6,'drone_count':30,'effective_hours_month':120,'checks_per_month':8,'response_limit_hours':2},
        'notes':['original source edited in place; TikZ figures embedded','glossary added at start; repeated prose and equations merged',
                 'only staff availability and drone count changed; all Q2 scenarios recalculated','third-question saved results retain the earlier baseline; not recalculated']}
    assert manifest['sections']==6 and manifest['subsections']==20 and len(eqs)==20
    (ROOT/'output/question2/q2_chapter_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ['status','target_pages','sections','subsections','equations','figures','tables']},ensure_ascii=False))
