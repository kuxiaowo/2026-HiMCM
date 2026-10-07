"""Translate the current verified English manuscript without rewriting its results."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from full_paper_body import BODY
from full_paper_zh_text import ZH_NARRATIVES
from write_full_paper import REFERENCES

ROOT=Path(__file__).resolve().parents[2]

HEADINGS={
'Introduction':'引言',
'Basic Assumptions and Justifications':'基本假设与理由',
'Data Description and Symbol Definitions':'数据说明与符号定义',
'Protection Priorities and a Measurable Standard':'保护优先事项与可测量标准',
'Priorities and evidence':'优先事项与证据',
'What the service score measures':'服务评分衡量什么',
'Resource Allocation with Ground Teams and Drones':'地面队伍与无人机的资源配置',
'Planning units and resource assumptions':'规划单元与资源假设',
'Animal responsibility, habitat and access':'动物责任、生境与进入条件',
'Weights, routes and response eligibility':'权重、路线与响应资格',
'Service capacity and the allocation model':'服务容量与配置模型',
'Solution checks and regional allocation':'求解核验与分区配置',
'Strategic comparisons and response posts':'方案比较与响应驻点',
'Seasonal Service and Workforce Requirements':'季节性服务与人员需求',
'Target, months and additional tasks':'目标、月份与额外任务',
'Borehole maintenance as ground-only work':'只能由地面完成的钻井运维',
'Shared monthly constraints':'月度共享约束',
'Forward service and inverse workforce models':'正向服务模型与反向人力模型',
'Normal-season results and feasibility':'常规季节结果与可行性',
'Drought work and service-standard sensitivity':'干旱工作与服务标准敏感性',
'Sensitivity and Scenario Analysis':'敏感性与情景分析',
'Strengths, Limitations and Practical Use':'模型优势、限制与实际使用',
'What the model supports':'模型能够支持什么',
'A practical calibration sequence':'实用的校准步骤',
'Adaptation to Parks on Other Continents':'向其他洲公园的迁移',
'Shared structure and local data':'共享结构与当地数据',
'Conditional trials and expected deployment changes':'条件试算与预期配置变化',
'Letter to IMMC':'致IMMC的信件',
'Report on Use of AI':'AI使用报告',
'Main symbols and their meanings.':'主要符号及含义。',
'Provisional management priorities.':'暂定管理优先顺序。',
'Etosha operating assumptions and resource settings.':'埃托沙运行假设与资源设定。',
'Etosha demand and base area service; stars are candidate posts, red dots fail the response rule.':'埃托沙需求与基准面积服务；星号为候选驻点，红点不满足响应规则。',
r'Personnel work per check at ENP1\_0000; drone flight time is a separate resource.':r'ENP1\_0000单次检查的人工；无人机飞行时间单独计量。',
'Regional demand and the representative base allocation.':'分区需求与代表性基准配置。',
'Scores under equal budgets and service rules.':'相同预算与服务规则下的评分。',
'Additional-post candidates within the base total budgets.':'基准总预算内的新增驻点候选方案。',
'Medium service rules by month.':'各月中档服务规则。',
'Historical-sample maintenance scenarios.':'历史样本运维情景。',
'How priorities and task work connect to deployment and workforce.':'优先事项及任务工作量如何连接配置与人力需求。',
'Medium-rule monthly workload and personnel equivalents; reference availability is 177 people.':'中档规则下的月度工作量与折算人员；参考可用量为177人。',
'Minimum work and workforce for the medium service target.':'维持中档服务目标的最少工作量与人力。',
'Workforce under different assumed service rules.':'不同假设服务规则下的人力需求。',
'Peak-month service under joint personnel and flight limits; each cell is reoptimized.':'人工与飞行联合限制下的高峰月服务；每格均重新优化。',
'Limits that affect interpretation and deployment.':'影响解释与部署的限制。',
'Published spatial inputs and candidate locations; Chitwan boundary consistency remains unresolved.':'公开空间输入与候选位置；奇特旺边界一致性仍未解决。',
'Spatial trial inputs; Chitwan polygon remains uncalibrated.':'空间试算输入；奇特旺多边形仍未校准。',
'Conditional land-inspection trials; not actual park staffing.':'陆地巡检条件试算，并非实际公园编制。',
}

TABLE_TEXT={
'Symbol':'符号','Definition':'定义',
'Reporting region, inspection unit and month.':'统计分区、巡检单元与月份。',
'Unit area and prescribed monthly checks.':'单元面积与规定月度检查次数。',
'Relative inspection importance and completion fraction.':'巡检相对重要性与完成比例。',
'1 when ground staff can arrive within the time limit; 0 otherwise.':'地面人员能在时限内到达时为1，否则为0。',
'Ground screening personnel-hours and drone flight-hours.':'地面筛查人时与无人机机时。',
'Personnel limit, flight limit and reserved response work.':'人工上限、飞行上限与响应预留工作量。',
'Priority':'优先级','Challenge and evidence':'问题与证据',
'Poaching and illegal entry: the problem identifies continuing rhinoceros losses; priority-object losses are difficult to replace.':'偷猎和非法进入：题目指出犀牛持续损失；重点对象的损失难以弥补。',
'Harmful wildfire and habitat damage: potentially widespread effects on animals and habitats; distinguish prescribed fire.':'有害野火和生境损害：可能广泛影响动物与生境；应与计划性燃烧区分。',
'Item':'项目','Setting':'设定','Travel speed':'出行速度','Task time / team':'任务时间／小组',
'Service / response':'服务／响应','Technology eligibility':'技术适用条件','Access / service floor':'进入／服务下限',
'Personnel':'人员','Drones':'无人机','Readiness':'待命',
'Road 30, walking 4, drone flight 40 km/h.':'道路30、步行4、无人机飞行40千米/小时。',
'Observation 10, preparation 5, dispatch 10 minutes; two people per team.':'观测10、准备5、调度10分钟；每组两人。',
r'8 checks per 100 km$^2$/month; ground arrival within 2 hours.':r'每100 km$^2$每月8次检查；地面队伍两小时内到达。',
r'At most 0.6 flight-hours/check; regional openness at least 60\%.':r'每次检查最多0.6机时；分区开阔度至少60\%。',
r'Entry-index decay scale 2 hours; reachable-area service floor 15\%.':r'进入指数衰减尺度2小时；可达面积服务下限15\%。',
r'295 reference employees; 60\% availability; 120 hours/person-month.':r'295名参考员工；60\%可用；每人每月120小时。',
'30 aircraft; 2 flight-hours/day for 20 flyable days/month.':'30架；每天2机时，每月20个可飞行日。',
'Six candidate posts, two people each, 8 hours/day for 30 days.':'六个候选驻点，每点两人，每天8小时，共30天。',
'Region':'分区',r'Demand (\%)':r'需求（\%）',r'Reach (\%)':r'可达（\%）',r'Service (\%)':r'服务（\%）',
'Labor (h)':'人工（h）','Flight (h)':'飞行（h）','Other*':'其他*','Salt pan*':'盐沼*',
r'* Animal values unknown. Regional labor excludes shared readiness. Small positive values below reporting precision are marked $<0.01$.':r'* 动物价值未知。分区人工不含共享待命。低于报告精度的小正值记为$<0.01$。',
'Budget':'预算','Labor limit':'人工上限','Uniform':'均匀','Demand-based':'按需求','Optimized':'优化','Base':'基准',
r'Personnel budget -40\%':r'人员预算减少40\%',
'Layout':'布局','Readiness (h)':'待命（h）','Score':'评分','Total labor (h)':'总人工（h）',
'Original six posts':'原六个驻点','ENP11 added':'新增ENP11','ENP3410 added':'新增ENP3410','ENP5 added':'新增ENP5',
'Months':'月份','Water visits/point':'每处水点巡访',r'Extra fire checks$^*$':r'额外火险检查$^*$',
'Jan--Apr, Dec':'1至4月、12月','May--Jul':'5至7月','Aug--Oct':'8至10月','Nov':'11月',
r'$^*$Checks per 100 km$^2$ of burnable habitat per month; on-site maintenance is 0.5 hour/visit in normal months.':r'$^*$每100 km$^2$可燃生境每月检查次数；常规月份每次现场运维0.5小时。',
'Rule':'规则','Visits/point':'每处巡访次数','On-site hours':'现场小时','Monthly labor':'月度人工',
'Wet regular':'常规湿季','Dry regular':'常规旱季','Drought pressure':'干旱压力',
'Personnel-hours':'人时','People':'人数','Flight-hours':'机时','177-person score':'177人评分',
'Normal people':'常规人数','Normal hours':'常规人时','Drought people':'干旱人数','Drought hours':'干旱人时',
'Low':'低档','Medium':'中档','High':'高档',
'Limit':'限制','Consequence and data needed':'影响与所需数据','Historical / missing objects':'历史／缺测对象',
'Current priority-species locations and surveys are needed; six measured groups do not certify all wildlife.':'需要当前重点物种位置和调查；六类已有数据的对象不能证明所有野生动植物受保护。',
'Service proxies and assumptions':'服务替代指标与假设',
'Calibrate check frequency, category priorities, fire exposure and ground/drone checklist equivalence.':'校准检查频次、类别优先程度、火险暴露和地面／无人机检查清单等效性。',
'Maps and permissions':'地图与许可',
'Verify roads, barriers, seasons and emergency access; a mapped route is not confirmed permission.':'核实道路、障碍、季节和应急通行；地图上的路线不代表已确认许可。',
'Monthly pooled work':'月度汇总工作',
'Check dates, qualifications, integer visits and concurrent incidents before calling a roster feasible.':'宣称排班可行前，应检查日期、资质、整数巡访次数和同时发生事件。',
'Incomplete maintenance inventory':'运维清单不完整',
'Update borehole status, tasks and repair duration; the 17-point sample cannot define all current work.':'更新钻井状态、任务和维修时长；17处样本不能代表当前全部工作。',
'Service versus ecological outcomes':'服务与生态结果',
'Validate loss, habitat and population outcomes independently; optimal service does not prove adequate protection.':'独立检验损失、生境和种群结果；服务最优不证明保护充分。',
'Input':'输入','Chitwan polygon':'奇特旺多边形','Yellowstone NPS':'黄石NPS边界',
r'Land service area (km$^2$)':r'陆地服务面积（km$^2$）',r'Forest share (\%)':r'森林占比（\%）',
'Mapped park roads (km)':'园内已绘制道路（km）','Units / grid side':'单元数／网格边长',
'Case':'案例','Ceiling':'上限','Target':'目标','Two posts, 30 km/h':'两驻点，30 km/h','Third post added':'新增第三驻点','Infeasible':'不可行',
}

FIGURE_TEXT={
'(a) Regional demand weight':'（a）分区需求权重','(b) Area-weighted service':'（b）面积加权服务',
'Response-post candidates':'候选响应驻点','Outside the two-hour ground-response limit':'超出地面两小时响应范围',
r'ENP1\_0000: personnel time for one check':r'ENP1\_0000：单次检查所需人工',
'Ground crew':'地面队伍','Drone crew':'无人机队伍','Road travel':'道路出行','Off-road walk':'离路步行',
'Observe / fly':'观测／飞行','Preparation':'准备',
'Two-person teams; drone flight adds 0.206 flight-hours per check.':'两人小组；每次无人机检查另需0.206机时。',
'Person-hours and flight-hours use separate budgets.':'人时与机时使用独立预算。',
'Priorities':'优先事项','Animals + habitat':'动物＋生境','Routes + response':'路线＋响应','Travel time':'出行时间',
'Deployment':'配置','People + drones':'人员＋无人机','Seasonal tasks':'季节任务','Fire + water tasks':'火险＋水点任务',
'Service target':'服务目标','57.26 points':'57.26分','Monthly staff':'月度人员','Minimum hours / 120':'最少工时／120',
'Checks receive service credit only where a ground team can respond.':'只有地面队伍能够响应的检查才计入服务评分。',
'Monthly work to maintain 57.26 service points':'维持57.26分服务的月度工作量','Response':'响应','Monitoring':'监测',
'Fire checks':'火险检查','Water points':'水点','Person-hours / month':'人时／月',
'Jan':'1月','Feb':'2月','Mar':'3月','Apr':'4月','May':'5月','Jun':'6月',
'Jul':'7月','Aug':'8月','Sep':'9月','Oct':'10月','Nov':'11月','Dec':'12月','Staff':'人数',
'Annual team: 57; reference: 177 staff (21,240 h/month, off scale).':'全年团队57人；参考177人（21,240人时/月，超出图中尺度）。',
'Mid-level seasonal peak: joint personnel and flight capacity':'中档季节高峰：人员与飞行容量的共同影响',
'Columns: flight-hours available per month; cells: service score.':'各列为月度可用机时；单元格为服务评分。',
'Target 57.26; 177 staff and 1200 flight-hours are the reference.':'目标57.26分；参考配置177人、1200机时。',
'Chitwan (boundary unresolved)':'奇特旺（边界未解决）','Yellowstone (NPS boundary)':'黄石（NPS边界）',
'Kasara':'卡萨拉','Sauraha':'索拉哈','Amaltari':'阿马尔塔里',
'Norris':'诺里斯','Lake':'湖区','South':'南入口','N':'北',
'Roads':'道路','Base candidates':'基准候选点','Extra candidate':'新增候选点',
'50 km':'50千米','10 km':'10千米','20 km':'20千米',
}

ZH_REFERENCES=[
r'IM$^2$C。《大尺度野生动物保护》（Protecting Wildlife at Scale），2026年题目及提供给团队的提交规则。',
r'《埃托沙航空野生动物调查报告》，2015年。分区动物数量来源。',
r'纳米比亚。《1975年第4号自然保护条例》，汇编后的法律保护类别。',
r'欧洲航天局（ESA）。WorldCover 2021，v200。土地覆盖数据与分类。',
r'OpenStreetMap贡献者／Geofabrik。纳米比亚数据快照，2026年10月3日；尼泊尔来源记录保存在项目中。',
r'纳米比亚环境与旅游部。《火管理策略》，2016年，提供埃托沙运行时段。',
r'Riddell, E. S., Kilian, W., Versfeld, W., Kosoana, M.《纳米比亚埃托沙国家公园地下水稳定同位素特征》。Koedoe，58(1)，2016年。表1记录2013年样本。',
r'纳米比亚MEFT。《2021/2022年度报告》。人工水点设备的证据。',
r'Dryad。埃托沙研究数据集，2024年；研究区旱季与湿季分类。',
r'联合国教科文组织世界遗产中心。《奇特旺国家公园》及相关保护记录。',
r'尼泊尔国家公园与野生动物保护局（DNPWC）。《奇特旺国家公园2013至2017年管理计划》及官方UNESCO报告；边界面积参考值952.63 km$^2$。',
r'联合国环境规划署世界保护监测中心（UNEP-WCMC）。WDPCA／Protected Planet，2026年10月，805号地点公开多边形。面积不一致被保留为未通过的校准检查。',
r'美国国家公园管理局（NPS）。黄石边界、公共道路和位置数据；项目保留来源查询与指纹。',
r'美国国家公园管理局（NPS）。黄石游客活动、当前状况，以及法律与政策。',
r'OpenAI。Codex，2026年10月工作会话使用的AI编程助手；基于GPT-6模型系列，准确部署版本不可获得。用途和核验见AI使用报告。',
]


def narratives():
    inside=False;out=[]
    for line in BODY.splitlines():
        if line.startswith(r'\begin{equation}'):inside=True
        if not inside and (re.match(r'^[A-Za-z]',line) or line.startswith((r'\textbf{',r'\noindent\textbf{',r'\noindent To'))):out.append(line)
        if line.startswith(r'\end{equation}'):inside=False
    return out


def main():
    current=ROOT/'docs/paper/full_paper_zh.tex'
    if current.exists() and '% PLAIN_LANGUAGE_EXPLANATION_20261006' in current.read_text(encoding='utf-8'):
        raise SystemExit('Current Chinese source contains detailed explanations. Do not overwrite it with the old translation generator; edit the open source in place.')
    source=ROOT/'docs/paper/full_paper.tex'
    original=source.read_text(encoding='utf-8');tex=original
    en=narratives();assert len(en)==len(ZH_NARRATIVES)==124
    blocks=[]
    for i,(a,b) in enumerate(zip(en,ZH_NARRATIVES)):
        assert sorted(re.findall(r'@[A-Z0-9_]+@',a))==sorted(re.findall(r'@[A-Z0-9_]+@',b)),i
        assert [m for m in re.findall(r'\$[^$]+\$',a) if m!='$^2$']==[m for m in re.findall(r'\$[^$]+\$',b) if m!='$^2$'],i
        parts=re.split(r'(@[A-Z0-9_]+@)',a);pattern='';names=[]
        for part in parts:
            if re.fullmatch(r'@[A-Z0-9_]+@',part):
                name=part.strip('@')
                if name in names:pattern+=f'(?P={name})'
                else:pattern+=f'(?P<{name}>[^\n]+?)';names.append(name)
            else:pattern+=re.escape(part)
        matches=list(re.finditer(pattern,tex));assert len(matches)==1,(i,len(matches),a)
        matched=matches[0];replacement=b
        for name in names:replacement=replacement.replace('@'+name+'@',matched.group(name))
        tex=tex[:matched.start()]+replacement+tex[matched.end():]
        blocks.append({'index':i,'english':matched.group(0),'chinese':replacement})
    def heading(m):
        assert m.group(2) in HEADINGS,m.group(2)
        return m.group(1)+HEADINGS[m.group(2)]+'}'
    tex=re.sub(r'(\\(?:section\*?|subsection|caption)\{)([^}]+)\}',heading,tex)
    for key in ['Letter to IMMC','Report on Use of AI']:
        tex=tex.replace(r'\addcontentsline{toc}{section}{'+key+'}',r'\addcontentsline{toc}{section}{'+HEADINGS[key]+'}')
    tex=tex.replace(r'\addcontentsline{toc}{section}{References}',r'\addcontentsline{toc}{section}{参考文献}')
    def tables(m):
        block=m.group(0)
        # Cell and note text are replaced only inside tables; URLs and other
        # LaTeX commands elsewhere cannot be accidentally translated.
        for key in sorted(TABLE_TEXT,key=len,reverse=True):
            if len(key)>30:block=block.replace(key,TABLE_TEXT[key])
        lines=[]
        for line in block.splitlines():
            if '&' in line:
                cells=line.removesuffix(r' \\').split(' & ')
                line=' & '.join(TABLE_TEXT.get(cell.strip(),cell.strip()) for cell in cells)+r' \\'
            lines.append(line)
        return '\n'.join(lines)
    tex=re.sub(r'\\begin\{table\}.*?\\end\{table\}',tables,tex,flags=re.S)
    def node(m):
        label=m.group(2)
        if re.search(r'[A-Za-z]',label):assert label in FIGURE_TEXT,label
        return m.group(1)+FIGURE_TEXT.get(label,label)+m.group(3)
    tex=re.sub(r'(\\node[^\n]* at [^\n]*?\{)([^{}]*)(\};)',node,tex)
    assert len(REFERENCES)==len(ZH_REFERENCES)==15
    for (key,text,url),zh in zip(REFERENCES,ZH_REFERENCES):
        old=r'\bibitem{'+key+'} '+text
        assert old in tex,key
        tex=tex.replace(old,r'\bibitem{'+key+'} '+zh)
    tex=tex.replace('{Online source.}','{在线来源。}')
    cover={
      'Team Control Number':'队伍控制编号','Problem Chosen':'所选题目','Wildlife Protection':'野生动物保护',
      'Summary Sheet':'摘要页','Planning Wildlife Protection under Geographic and Resource Constraints':'地理与资源约束下的野生动物保护规划',
    }
    for key in sorted(cover,key=len,reverse=True):tex=tex.replace(key,cover[key])
    tex=tex.replace(r'\usepackage{fontspec}',r'\usepackage{fontspec}'+'\n'+r'\usepackage[UTF8,scheme=plain,fontset=none]{ctex}')
    tex=tex.replace(r'\newcommand{\TeamNumber}',r'\setCJKmainfont{SimSun}[BoldFont=SimHei,ItalicFont=KaiTi]'+'\n'+r'\setCJKsansfont{SimHei}'+'\n'+r'\setCJKfamilyfont{hei}{SimHei}'+'\n'+r'\renewcommand{\contentsname}{目录}'+'\n'+r'\renewcommand{\refname}{参考文献}'+'\n'+r'\renewcommand{\figurename}{图}'+'\n'+r'\renewcommand{\tablename}{表}'+'\n'+r'\newcommand{\TeamNumber}')
    tex=tex.replace(r'\selectfont Team \#\TeamNumber',r'\selectfont 队伍 \#\TeamNumber')
    tex=tex.replace(r'Page \thepage\ of \pageref{LastPage}',r'第\thepage 页／共\pageref{LastPage}页')
    tex=tex.replace(r'\fontspec{Arial}\fontsize',r'\fontspec{Arial}\CJKfamily{hei}\fontsize')
    # Translate equation units and explanatory text, keeping all mathematics.
    equation_words={'personnel-hours/month':'人时/月','flight-hours/month':'机时/月','personnel-hours':'人时','at least one qualifying post':'至少一个合格驻点'}
    for a,b in equation_words.items():tex=tex.replace(r'\text{'+a+'}',r'\text{'+b+'}')
    def normalized_equations(value):
        value=re.sub(r'\\text\{[^}]+\}',r'\\text{UNIT}',value)
        return re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}',value,re.S)
    assert normalized_equations(tex)==normalized_equations(original)
    assert re.findall(r'\\label\{([^}]+)\}',tex)==re.findall(r'\\label\{([^}]+)\}',original)
    assert re.findall(r'\\cite\{([^}]+)\}',tex)==re.findall(r'\\cite\{([^}]+)\}',original)
    assert tex.count(r'\begin{figure}')==6 and tex.count(r'\begin{table}')==13
    assert tex.count(r'\clearpage')==23
    assert not re.search(r'@[A-Z0-9_]+@',tex)
    out=ROOT/'docs/paper/full_paper_zh.tex';out.write_text(tex,encoding='utf-8')
    audit={
      'status':'translation_written_compilation_pending','language':'zh-CN','source_english':'docs/paper/full_paper.tex',
      'source_english_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'source_chinese':'docs/paper/full_paper_zh.tex','source_chinese_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
      'all_narrative_blocks_translated':len(blocks),'figures':6,'tables':13,'numbered_equations':19,'references':15,
      'equations_unchanged_except_translated_units':True,'labels_and_citations_unchanged':True,
      'numerical_results_copied_from_verified_english':True,'paragraphs':blocks,
    }
    (ROOT/'output/full_paper/full_paper_zh_translation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:audit[k] for k in ['status','all_narrative_blocks_translated','figures','tables','numbered_equations','references']},ensure_ascii=False))


if __name__=='__main__':main()
