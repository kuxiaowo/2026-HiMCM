"""Generate concise formal Q4/Q5 Markdown and self-contained LaTeX."""
from pathlib import Path
import hashlib
import json
import re
from write_question2_chapter import table, PREAMBLE

ROOT=Path(__file__).resolve().parents[2]
PAPER=ROOT/'docs/paper'
OUT=ROOT/'output/question4'
FIG=OUT/'paper_figures'

BODY4=r'''
\section{敏感性与情景分析}

第二、三题给出了基准部署和季节人员需求，本部分进一步检验资源或作业条件改变时，原策略能否维持既定服务。沿用需求权重、检查协议和区域底线，将第二题基准监测与第三题中档峰值月分别作为比较对象；后者包含额外火险检查和17处历史钻井水点样本运维。单人有效工时固定为120小时/月，目标保持\(\eta=P_2^*\approx57.26\)分。以下情景是规划条件的改变，不赋予发生概率。

\subsection{资源敏感性分析}

\subsubsection{人员减少对保护服务的影响}

保持当前机时预算1200及地理条件不变，改变保护岗位数，分别求固定人员下的最高服务与目标下的最少人工：
\begin{equation}
\begin{aligned}
P_t^*(N,U)&=\max_{\substack{\mathbf z_t\in\mathcal F_t(U)\\H_t(\mathbf z_t)\le120N}}100\sum_jw_js_{jt},\\
H_t^{\mathrm{crit}}(U)&=\min_{\substack{\mathbf z_t\in\mathcal F_t(U)\\100\sum_jw_js_{jt}\ge\eta}}H_t(\mathbf z_t).
\end{aligned}
\label{eq:resource}
\end{equation}
其中\(\mathcal F_t(U)\)沿用服务容量、技术适用性、区域底线及必要任务约束；第二题比较关闭新增季节任务。共享响应2880人时不随人员同比削减。低预算下若连必要任务与底线都无法完成，报告无解，不以零分代替。

图\ref{fig:resources}(a)显示两种工作范围的差别。在1200机时条件下，第二题基准服务的全局最少人工为@Q2_H@人时，按有效工时换算需@Q2_N@个同口径岗位；中档峰值月需@PEAK_H@人时，即@PEAK_N@人。峰值月减至56人时只有@N56_SCORE@分。新增工作使人员阈值提高，即使基准服务分相同，也不能将第二题剩余预算直接视为全年可减员空间。本节反求与修订后的第二题采用相同口径，均允许同分服务向量重新选择。

@FIG_RESOURCES@

\subsubsection{无人机减少与人力替代}

按每架每月40机时的设定，将机时上限由1200逐步降至0，保留无人机配套人工及地面响应。图\ref{fig:resources}(b)中，峰值所需人数依次随设备减少而增加：240机时需57人，160机时需58人，120机时需60人，设备停用需67人。其中120机时属于仅3架等价的低设备情景，需@U120_H@人时，比59人的7080人时预算略高；当前177人和1200机时基准则有充足余量。

这表明地面检查能够在技术不足时补充服务，但要付出更多人工；响应与水点运维仍不能由飞行机时替代。资源充足时，设备变化可能只增加工作量而不改变分数。因此同时报告服务分和所需人工，比只比较总分更能体现技术的作用。上述人数针对选定任务与既定响应范围，不代表公园实际编制。

\subsection{关键参数敏感性分析}

\subsubsection{通行与作业条件的影响}

道路速度改变同时影响响应可达性与往返成本，作业耗时增加则直接提高人工消耗。保持第二题基准评价权重，表\ref{tab:travel}汇总已有通行情景。道路速度由30降至20 km/h时，分数降至@ROAD20_SCORE@，且等于该条件下的地理上限；增加人员也不能修复现有驻点无法及时响应的区域。该情景总人工较少，是服务范围缩小的结果，不能解释为效率提高。

@TAB_TRAVEL@

相比之下，作业人工增加25\%后仍为57.26分，但最少人工升至@COST_H@人时，说明评分达到上限会遮盖成本变化。前者需改善通行或响应布局，后者需保留人工余量。速度和成本变化是明确的压力设定，并非本园实际运行速度或耗时的统计区间。

\subsubsection{季节服务要求的影响}

在中档峰值月分别改变额外火险检查频次、水点访问频次及现场耗时，每次只改变一项。表\ref{tab:standards}显示，火险检查加密对人员需求的影响较大，但这一比较只限表中所选幅度，不构成所有参数的普遍排序。水点工作量满足
\begin{equation}
W_t=f_tn_W\left[\sum_{\ell\in\mathcal L}T_\ell^{\mathrm{rt}}+
|\mathcal L|(\tau_t+t_p^W)\right].
\label{eq:water}
\end{equation}
其中\(f_t\)为每点月访问次数，\(n_W=2\)，\(\tau_t\)为现场小时数。对17处样本，保持每月4次访问时，现场时间由0.5增至1小时会增加68人时；人数由57增至58。不同工时变化可能得到同一取整人数，因此不能只看整数结果。

@TAB_STANDARDS@

同时改变服务要求的低、中、高档组合，正常季节峰值为51、57、71人；所设异常干旱运维压力下为53、62、77人。这些是不同管理规则下的结果，不能当置信区间。若只按样本平均成本把水点工作量增至2、3倍，中档峰值为61、64人；该检验揭示完整台账的重要性，不表示已查明新增水点数量和路线。赋权与格网对照另存计算附件，不能以不同评分口径的分数直接判断保护改善。

\subsection{情景分析与策略调整}

\subsubsection{巡护时间安排的比较}

月度点次相同不意味着服务在时间上同样连续。以中档旱季17处水点为代表，每点访问4次，比较相位错开的分散安排与全部集中在第1—4日的安排。分散方案在重复30日周期内采用相隔7、8、7、8日的日期，并逐点错开起始日；集中方案也按相同月周期重复。两者均为构造日程，任务数和独立往返成本保持一致。

@TAB_SCHEDULE@

表\ref{tab:schedule}中，两种方案均为68次、422.34人时，但集中执行使最长访问间隔达到27日，单日水点人工峰值也明显增加。分散安排的最长间隔为8日，这是整数日期下对7.5日理想均匀间隔的近似，尚不能证明严格满足7.5日规则。因而月度LP可评估工作总量，实际应用还应核验访问日期和分时容量。这里仅比较水点任务，不证明整套巡护、飞行与响应排班可行，也未改变每人120小时的月有效工时。

\subsubsection{联合压力下的部署调整}

图\ref{fig:joint}将人员与机时同时改变，并对每格重新优化中档峰值月服务。57人配200或240机时可以维持目标，配160机时仅为@N57_U160_SCORE@分；59人配120机时为@N59_U120_SCORE@分，而完全停用设备时降至@N59_U0_SCORE@分。相同设备减少幅度在不同人工预算下影响不同，不能用单项资源充足时的结果外推联合压力。

@FIG_JOINT@

为区分原部署的承受能力与重新配置的作用，以峰值基准服务向量\(\mathbf s^0\)为原空间规则。对正评价权重单元按同一比例缩减，零权重单元保持原底线服务，同时仍允许技术方式改变：
\begin{equation}
s_j^{\mathrm{ret}}=
\begin{cases}\lambda s_j^0,&w_j>0,\\s_j^0,&w_j=0,\end{cases}
\qquad 0\le\lambda\le1.
\label{eq:profile}
\end{equation}
额外火险及水点任务仍必须完成。通过比例搜索和原LP求出这一规则下可维持的最高服务，再与允许空间重新配置的解比较。该规则用于受限对照，不是已观测的公园制度。

@TAB_ADAPTATION@

表\ref{tab:adaptation}显示，55人情景下重新配置增加@GAIN55@分；异常干旱运维压力叠加120机时上限时增加@GAIN_DROUGHT@分，但仍未达到57.26分。部署调整可以缓解缺口，却不能保证所有资源压力下达标。管理上应根据重点月份的工作量保留人机余量，对地理缺口优先核验驻点和通行方案；这些建议仅覆盖已计算的条件，尚未验证实际生态减损。
'''

BODY5=r'''
\section{模型评价}

以下从工作量解释、计算核验和现场适用条件三个方面评价模型，明确其能支持的规划判断及仍需补充的证据。

\subsection{模型优点}

模型将地面监测、无人机飞行及其配套人工共同纳入预算，并以路网与响应期限约束有效服务，能够区分资源不足和地理不可达。当前21240人时、1200机时及减员40%情景下，三种配置均为57.26分，瓶颈在响应范围。第四题另在明确的低预算情景中比较保留规则和重新配置，不能沿用旧基准的提升幅度。第三、四题沿用相同服务定义，把季节任务转为人时并反求人力，便于解释为何峰值月份或技术减少会提高人员需求。

变量单位和工作量来源明确，保存的输入、解向量及独立核验使结论可复算。第四题@AUDITED@个保存可行方案均通过容量、必要任务、预算和汇总检查。上述证据支持所建模型内的资源规划与数值一致性。

\subsection{模型局限}

动物、生境和道路资料年份不同，重点对象及当前完整水点清单仍有缺失；区内均匀分布、服务频次及人机筛查等价也需要现场校准。因而人员结果只针对选定对象、既定响应范围和历史水点样本，不能视为全园真实最低编制。

月度连续工时与独立往返简化了整数派遣、岗位资格、驻点迁移和并发响应，工作总量足够不保证具体日程可行。服务分衡量规定监测能力，不等于动物存活率或生态损失下降；维持第二题最优分也不能证明原服务标准具有生态充分性。实际应用应先补齐现行台账与作业日志，再校准成本、频次和技术适用条件，并用独立成效资料检验保护效果。
'''


def figure(name,label,caption):
    tikz=(FIG/(name+'.tikz')).read_text(encoding='utf-8')
    tex='\n'.join([r'\begin{figure}[htbp]',r'\centering',r'\resizebox{\linewidth}{!}{%',
                    tikz.rstrip(),'}',r'\caption{'+caption+'}',r'\label{'+label+'}',r'\end{figure}'])
    return tex,f'![{caption}](../../output/question4/paper_figures/{name}.png)\n\n'+caption


def markdown(body,labels,number):
    counters=[number-1,0,0]
    def heading(m):
        kind,title=m.group(1),m.group(2);level=['section','subsection','subsubsection'].index(kind)
        counters[level]+=1
        for k in range(level+1,3):counters[k]=0
        return '#'*(level+1)+' '+'.'.join(str(v) for v in counters[:level+1])+' '+title
    body=re.sub(r'\\(section|subsection|subsubsection)\{([^{}]+)\}',heading,body)
    body=re.sub(r'\\eqref\{([^}]+)\}',lambda m:'（'+labels[m[1]]+'）',body)
    body=re.sub(r'\\ref\{([^}]+)\}',lambda m:labels[m[1]],body)
    def equation(m):
        label=re.search(r'\\label\{([^}]+)\}',m[1])[1]
        return '\\[\n'+m[1].strip()+'\n\\tag{'+labels[label]+'}\n\\]'
    body=re.sub(r'\\begin\{equation\}(.*?)\\end\{equation\}',equation,body,flags=re.S)
    body=re.sub(r'\\label\{[^}]+\}','',body)
    chunks=re.split(r'(\\\[.*?\\\]|\\\(.*?\\\))',body,flags=re.S)
    for i in range(0,len(chunks),2):chunks[i]=chunks[i].replace(r'\%','%').replace(r'\_','_')
    return '\n'.join(v.rstrip() for v in ''.join(chunks).splitlines()).strip()+'\n'


def chapter(number,title,body,numbers,blocks,stem):
    texbody=body;md_body=body
    for key,value in numbers.items():
        texbody=texbody.replace('@'+key+'@',str(value));md_body=md_body.replace('@'+key+'@',str(value))
    for key,(tex,md) in blocks.items():
        texbody=texbody.replace('@'+key+'@',tex);md_body=md_body.replace('@'+key+'@',md)
    assert not re.search(r'@[A-Z0-9_]+@',texbody)
    labels={}
    for kind in ['equation','figure','table']:
        for i,block in enumerate(re.findall(r'\\begin\{'+kind+r'\}(.*?)\\end\{'+kind+r'\}',texbody,flags=re.S),1):
            label=re.search(r'\\label\{([^}]+)\}',block)[1];labels[label]=f'{number}-{i}'
            if kind!='equation':
                key=next(k for k,v in blocks.items() if '\\label{'+label+'}' in v[0])
                old=blocks[key][1]
                if kind=='figure':
                    picture,caption=old.split('\n\n',1);new=picture+'\n\n'+f'图{number}-{i}：'+caption
                else:new=f'表{number}-{i}：'+old
                md_body=md_body.replace(old,new)
    assert all(v in labels for v in re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',texbody))
    pre=PREAMBLE.split(r'\title{',1)[0].replace(r'\setcounter{section}{1}',r'\setcounter{section}{'+str(number-1)+'}')
    pre=pre.replace('2-',str(number)+'-')
    pre+=r'\begin{document}'+'\n'
    tex=pre+texbody+'\n\\end{document}\n'
    md=f'# 第{["","","","","四","五"][number]}题正式正文\n\n'+markdown(md_body,labels,number)
    if number==4:
        md+='\n计算附件：[情景结果](../../output/question4/q4_results.json)、[完整解](../../output/question4/q4_solutions.json)、[独立核验](../../output/question4/q4_independent_verification.json)。\n'
    (PAPER/(stem+'.md')).write_text(md,encoding='utf-8')
    (PAPER/(stem+'.tex')).write_text(tex,encoding='utf-8')
    return {'chapter':number,'sections':len(re.findall(r'\\subsection\{',texbody)),
            'subsections':len(re.findall(r'\\subsubsection\{',texbody)),
            'equations':sum(k.startswith('eq:') for k in labels),'figures':sum(k.startswith('fig:') for k in labels),
            'tables':sum(k.startswith('tab:') for k in labels),'labels':labels,
            'md_sha256':hashlib.sha256(md.encode()).hexdigest(),'tex_sha256':hashlib.sha256(tex.encode()).hexdigest()}


def main():
    r=json.loads((OUT/'q4_results.json').read_text(encoding='utf-8'))
    audit=json.loads((OUT/'q4_independent_verification.json').read_text(encoding='utf-8'))
    assert audit['passed']
    inverse={(v['scope'],v['drone_budget']):v for v in r['technology_sensitivity']}
    resource={(v['scope'],v['staff']):v for v in r['resource_sensitivity']}
    joint={(v['staff'],v['drone_budget']):v for v in r['joint_peak_scenarios']}
    old={v['name']:v['result'] for v in r['q2_saved_scenarios']}
    policy={v['scenario']:v for v in r['policy_comparisons']}
    f=lambda v:f'{v:.2f}'
    numbers={'AUDITED':audit['independently_checked_feasible_solutions'],'Q2_H':f(inverse['q2_monitoring',1200]['total_person_hours']),
             'Q2_N':inverse['q2_monitoring',1200]['required_staff'],
             'PEAK_H':f(inverse['q3_peak_base',1200]['total_person_hours']),
             'PEAK_N':inverse['q3_peak_base',1200]['required_staff'],
             'N56_SCORE':f(resource['q3_peak_base',56]['score']),
             'U120_H':f(inverse['q3_peak_base',120]['total_person_hours']),
             'ROAD20_SCORE':f(old['道路速度20km/h']['score']),
             'COST_H':f(old['出行及作业人时增加25%']['total_person_hours']),
             'N57_U160_SCORE':f(joint[57,160]['score']),'N59_U120_SCORE':f(joint[59,120]['score']),
             'N59_U0_SCORE':f(joint[59,0]['score']),
             'GAIN55':f(policy['peak_N55']['gain_points']),
             'GAIN_DROUGHT':f(policy['drought_N59_U120']['gain_points'])}
    blocks={
        'FIG_RESOURCES':figure('fig1_resource_sensitivity','fig:resources','人员资源、机时资源与服务目标的关系。两类工作范围分别求解；点为已算情景，连线仅辅助阅读。'),
        'FIG_JOINT':figure('fig2_joint_resources','fig:joint','中档峰值月的人员与机时联合情景。数字为最高服务分，金框表示维持目标；各格预算和硬性任务均已核验。')}
    travel=[]
    for label,key in [('道路20 km/h','道路速度20km/h'),('道路30 km/h','基准'),('道路40 km/h','道路速度40km/h'),('作业人工增加25\\%','出行及作业人时增加25%')]:
        v=old[key];travel.append([label,f(v['score']),f(v['geographic_score_upper_bound']),f(v['total_person_hours'])])
    blocks['TAB_TRAVEL']=table('tab:travel','通行与作业成本情景（第二题工作范围）',
                              ['情景','服务分','地理上限','使用人时'],travel,
                              note='注：各情景先求最优总分，再在保持该分数的方案中最小化总人工；道路情景保持基准评价权重。')
    names={'fire_rate':r'额外火险频次 \(k_t\)','water_visits':r'水点月访问次数 \(f_t\)',
           'water_onsite_hours':r'现场耗时 \(\tau_t\)/小时'}
    rows=[]
    for kind in names:
        items=[v for v in r['single_parameter_sensitivity'] if v['parameter']==kind]
        rows.append([names[kind],' / '.join(f'{v["value"]:g}' for v in items),
                     ' / '.join(str(v['required_staff']) for v in items)])
    blocks['TAB_STANDARDS']=table('tab:standards','单独改变服务要求时的峰值人数',
        ['变化因素','测试取值','对应人数'],rows,'Xrr',
        note=r'注：每行其余条件保持中档峰值基准；\(k_t\)单位为每100平方公里可燃生境每月额外点次。')
    rows=[]
    for v in r['water_schedule_comparison']:
        rows.append(['分散并错开' if v['arrangement']=='dispersed' else '集中第1—4日',
                     str(v['total_visits']),f(v['total_water_hours']),f'{v["maximum_visit_gap_days"]:g}',f(v['peak_daily_water_hours'])])
    blocks['TAB_SCHEDULE']=table('tab:schedule','同月任务量下的水点访问时间对照',
        ['安排','访问次数','月人时','最长间隔/日','单日峰值人时'],rows,
        note='注：整数日期、重复30日周期；分散相位采用逐点降低当前峰值的启发式，不称全局最优日程。')
    rows=[]
    for label,key in [('中档：55人、240机时','peak_N55'),('中档：59人、120机时','peak_N59_U120'),('干旱运维：59人、120机时','drought_N59_U120')]:
        p=policy[key];rows.append([label,f(p['retained']['score']),f(p['adaptive']['score']),f(p['gain_points'])])
    blocks['TAB_ADAPTATION']=table('tab:adaptation','保留空间规则与重新配置的服务对照',
        ['情景','保留规则','重新配置','增加分数'],rows,
        note='注：同一情景采用相同预算、权重和必要任务；技术方式在两种方案中均允许改变。')
    manifests=[chapter(4,'敏感性与情景分析',BODY4,numbers,blocks,'question4_sensitivity'),
               chapter(5,'模型评价',BODY5,numbers, {},'question5_evaluation')]
    manifest={'chapters':manifests,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'q4_results.json',OUT/'q4_independent_verification.json']},
              'notes':['compact approved hierarchy retained','all figures inline TikZ in standalone sources','no external ecological validation claimed'],
              'pdf_compilation_confirmed':False}
    (OUT/'q45_chapter_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'chapters':[{k:v for k,v in m.items() if k not in ['labels','md_sha256','tex_sha256']} for m in manifests]},ensure_ascii=True))


if __name__=='__main__':main()
