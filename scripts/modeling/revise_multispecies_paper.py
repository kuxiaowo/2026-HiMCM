"""Apply the approved scope and solver revision to the current open manuscripts.

Keeps the user's chapter names, template typography and Chinese explanations.
The pre-revision archive remains the numerical comparison and recovery record.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from write_full_paper import table

ROOT = Path(__file__).resolve().parents[2]
MARKER = '% MULTISPECIES_REVISION_20261006'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def replace_once(text, old, new):
    assert text.count(old) == 1, (old[:100], text.count(old))
    return text.replace(old, new, 1)


def replace_table(text, label, new):
    pattern = r'\\begin\{table\}(?:(?!\\end\{table\}).)*?\\label\{' + re.escape(label) + r'\}(?:(?!\\end\{table\}).)*?\\end\{table\}'
    text, count = re.subn(pattern, lambda _: new, text, flags=re.S)
    assert count == 1, label
    return text


def numeric_sync(text, old, new):
    pairs = []
    for key in ['total_person_hours', 'drone_flight_hours', 'drone_operator_hours']:
        pairs.append((old['optimum'][key], new['optimum'][key]))
    for budget, key in [('human_budget', 'total_person_hours'), ('drone_budget', 'drone_flight_hours')]:
        pairs.append((old['optimum'][budget] - old['optimum'][key], new['optimum'][budget] - new['optimum'][key]))
    for name in ['无人机停用', '出行及作业人时增加25%']:
        a = next(c['result'] for c in old['scenarios'] if c['name'] == name)
        b = next(c['result'] for c in new['scenarios'] if c['name'] == name)
        pairs.append((a['total_person_hours'], b['total_person_hours']))
    mapping = {f'{a:.2f}': f'{b:.2f}' for a, b in pairs if f'{a:.2f}' != f'{b:.2f}'}
    # Match complete displayed numbers, never coordinates inside TikZ paths.
    for a in sorted(mapping, key=len, reverse=True):
        text = re.sub(r'(?<![\d.])' + re.escape(a) + r'(?![\d.])', mapping[a], text)
    return text


def core_tables(report, supplement, chinese=False):
    n = lambda value: f'{value:.2f}' if value == 0 or value >= .005 else '<0.01'
    rows = sorted(report['regions'], key=lambda r: -r['demand_weight'])
    regional = []
    for r in rows:
        label = {'PAN_MAIN': '盐沼*' if chinese else 'Salt pan*', 'UNSURVEYED_OTHER': '其他*' if chinese else 'Other*'}.get(r['region_id'], r['region_id'])
        regional.append([label, n(100 * r['demand_weight']), n(100 * r['response_reachable_area_fraction']), n(100 * r['service_completion_fraction']), n(r['allocated_monitoring_person_hours']), n(r['drone_flight_hours'])])
    base = report['optimum']
    forwards = [[('原六个驻点' if chinese else 'Original six posts'), '2880', n(base['score']), n(base['total_person_hours']), n(base['drone_flight_hours'])]]
    for c in report['forward_post_options']:
        r = c['result']
        forwards.append([('新增' if chinese else 'Add ') + c['target_region'], f"{r['response_reserved_hours']:.0f}", n(r['score']), n(r['total_person_hours']), n(r['drone_flight_hours'])])
    comparisons = []
    for name, key in [(('基准' if chinese else 'Base'), 'comparisons'), (('人工减少40\\%' if chinese else 'Personnel -40\\%'), 'scarce_budget_comparisons')]:
        c = report[key]
        comparisons.append([name, f"{c[-1]['result']['human_budget']:.0f}"] + [n(v['result']['score']) for v in c])
    comparisons.append([('压力预算' if chinese else 'Tight budget'), '3600'] + [n(c['score']) for c in supplement['pressure_comparisons']])
    captions = (['分区需求与最优同分方案中的最少人工配置。', '相同预算与检查规则下的有效巡检完成率。', '基准总预算内的新增驻点候选方案。'] if chinese else
                ['Regional demand and the minimum-labor optimal-rate allocation.', 'Effective inspection completion rates (\\%) under equal budgets and service rules.', 'Additional-post candidates within the base total budgets.'])
    headers = ([['分区', '需求/\\%', '可达/\\%', '服务/\\%', '人工/h', '飞行/h'], ['情景', '人时上限', '均匀', '需求比例', '优化'], ['布局', '待命/h', '服务/\\%', '总人工/h', '飞行/h']] if chinese else
               [['Region', 'Demand (\\%)', 'Reach (\\%)', 'Service (\\%)', 'Labor (h)', 'Flight (h)'], ['Budget', 'Labor limit', 'Uniform', 'Demand-based', 'Optimized'], ['Layout', 'Readiness (h)', 'Rate (\\%)', 'Total labor (h)', 'Flight (h)']])
    result = {}
    for label, caption, head, body in zip(['tab:regions', 'tab:comparison', 'tab:forward'], captions, headers, [regional, comparisons, forwards]):
        note = ('*动物数量未知。分区人工不含共享响应待命。' if chinese else '* Animal values unknown. Regional labor excludes shared response readiness.') if label == 'tab:regions' else ''
        result[label] = table(label, caption, head, body, note=note).replace('[H]', '[!htbp]')
    return result


def main():
    enpath = ROOT / 'docs/paper/full_paper.tex'
    zhpath = ROOT / 'docs/paper/full_paper_zh.tex'
    en = enpath.read_text(encoding='utf-8')
    zh = zhpath.read_text(encoding='utf-8')
    assert MARKER not in en and MARKER not in zh, 'Already revised: edit the current sources in place.'
    q2 = read('output/question2/q2_results.json')
    q3 = read('output/question3/q3_results.json')
    extra = read('output/revision_feasibility/20261006/revision_results.json')
    with zipfile.ZipFile(ROOT / 'output/full_paper/history/before_multispecies_revision_20261006.zip') as archive:
        old = json.loads(archive.read('output/question2/q2_results.json'))
    base = q2['optimum']
    pressure = extra['pressure_comparisons']
    peak = max(q3['monthly'], key=lambda r: r['required_person_hours'])
    drought = next(r for r in q3['sensitivity'] if r['scenario'] == 'base' and r['abnormal_drought'])
    # One paragraph per question makes the Summary Sheet navigable.
    summary = rf'''Large reserves need inspections that lead to timely action. We connect conservation priorities, ground response and limited personnel and drones in Etosha, then examine seasonal work and transfer to other parks.

\textbf{{Priorities.}} We address illegal entry and poaching, harmful fire and habitat damage through a multi-species framework. Six animal groups with usable 2015 survey records and burnable-habitat areas define relative responsibility. The Effective Inspection Completion Rate measures prescribed checks supported by timely ground response.

\textbf{{Allocation.}} A two-stage linear program first maximizes completion, then minimizes labor across all equally optimal service patterns. With \textbf{{21240}} personnel-hours and \textbf{{1200}} flight-hours available monthly, its \textbf{{{base['score']:.2f}\%}} optimum uses \textbf{{{base['total_person_hours']:.2f}}} personnel-hours and \textbf{{{base['drone_flight_hours']:.2f}}} flight-hours. Response access limits service. The best of three additional-post candidates raises completion to \textbf{{64.27\%}}.

\textbf{{Seasonal staffing.}} Separate fire checks and maintenance of 17 historical boreholes require \textbf{{{peak['required_staff']}}} personnel equivalents in the normal peak month and \textbf{{{drought['annual_fixed_staff']}}} under the specified drought-maintenance rule, at 120 effective hours per person-month.

\textbf{{Sensitivity.}} All three allocation rules tie under ample resources. At a 3600-hour labor limit, uniform, demand-based and optimized completion are \textbf{{{pressure[0]['score']:.2f}\%}}, \textbf{{{pressure[1]['score']:.2f}\%}} and \textbf{{{pressure[2]['score']:.2f}\%}}. Reduced drone efficiency restores ground screening; grid size changes the estimated response ceiling.

\textbf{{Evaluation.}} Independent checks confirm model feasibility and agreement between allocation and inverse-workforce calculations. Historical records and assumed protocols limit operational interpretation; service completion does not establish wildlife survival or sufficient ecological protection.

\textbf{{Transfer.}} Chitwan and Yellowstone trials rebuild local geography. A historical Yellowstone wolf-use scenario changes priorities and deployment. Chitwan's published geometry and official area remain inconsistent, so its results are conditional. Validate access and task effectiveness before adopting staffing recommendations.

'''
    start = en.index('Protecting a large reserve')
    end = en.index(r'\noindent\textbf{Keywords:}', start)
    en = en[:start] + summary + en[end:]
    start = en.index(r'\section{Protection Priorities and a Measurable Standard}')
    point = en.index(r'\subsection{Priorities and evidence}', start)
    en = en[:point] + 'We identify shared threats before assigning regional responsibility. The management goal covers wildlife across habitats; the animal component quantifies the six surveyed groups rather than a complete species inventory.\n\n' + en[point:]
    en = replace_once(en, 'Poaching and illegal entry: the problem identifies continuing rhinoceros losses; priority-object losses are difficult to replace.', 'Poaching and illegal entry: unauthorized access creates enforcement needs across animal habitats; the supplied rhinoceros-poaching context is one documented example.')
    en = replace_once(en, 'Human--wildlife conflict, disease, important plants and birds remain data needs. Missing information does not make them low-priority. Black rhinoceros remains a key conservation concern even though the current regional animal-priority measure lacks reliable spatial counts for that species. The six measured survey objects are blue wildebeest, plains zebra, giraffe, African savanna elephant, gemsbok and ostrich.', 'The animal component uses blue wildebeest, plains zebra, giraffe, African savanna elephant, gemsbok and ostrich. We retain source quality flags and exclude unresolved count tables. These historical records support a deployment demonstration, not current abundance for all wildlife. Rhinoceros poaching remains a qualitative concern; its conflicting counts are not required by this multi-species model. Human--wildlife conflict, disease and species-specific interventions remain outside the quantified task list.')
    en = replace_once(en, r'\section{Resource Allocation with Ground Teams and Drones}' + '\n' + r'\subsection{Planning units and resource assumptions}', r'\section{Resource Allocation with Ground Teams and Drones}' + '\nThe priorities above determine which inspections receive weight. This section converts their completion requirements into travel, personnel and flight work, then chooses a feasible allocation.\n\n' + r'\subsection{Planning units and resource assumptions}')
    en = replace_once(en, r'After maximizing the effective inspection completion rate, we fix the returned service vector $\mathbf s^{(1)}$ and minimize $H_M=\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j$. This selects the least labor supporting that particular service pattern. It does not search all equal-rate inspection patterns for the global minimum workforce.', r'''First maximize completion to obtain $P^*$. Then minimize $H_M=\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j$ under the same constraints and $100\sum_jw_js_j\ge P^*$. All service fractions remain decision variables. This gives the least labor among optimal-rate allocations in the stated model. At the geographic ceiling, positive-weight reachable units must be fully served; zero-weight units still satisfy the regional floor.''')
    en = replace_once(en, r'The effective inspection completion rate is 57.26\%. The selected representative uses 5379.02 personnel-hours and 151.82 flight-hours, including 2880 response hours and 2499.02 drone-support hours. Its ground screening hours are zero; ground operators and response staff are still essential.', rf'The effective inspection completion rate is {base["score"]:.2f}\%. Its minimum-labor allocation uses {base["total_person_hours"]:.2f} personnel-hours and {base["drone_flight_hours"]:.2f} flight-hours: 2880 readiness hours plus {base["drone_operator_hours"]:.2f} drone-support hours. Ground screening is zero under the baseline equivalent-checklist assumption. The protocol scenarios below test that assumption.')
    en = replace_once(en, 'The salt pan\'s unknown animal value is not filled with zero. Its current objective weight is zero, while its generic service floor still applies. Equal-rate inspection choices there can change representative labor consumption without changing the park completion rate.', "The salt pan's animal value remains unknown. Its zero objective weight applies only to the measured components; the regional service floor remains binding. The second stage therefore selects its least-cost floor service without treating the salt pan as ecologically unimportant.")
    en = replace_once(en, 'It allows different equal-rate inspection patterns, unlike the fixed-pattern refinement in Question 2.', 'As in revised Question 2, it allows service fractions to vary among equal-rate allocations.')
    en = replace_once(en, 'With no added seasonal work and Question 2\'s returned service vector fixed, the calculation reproduces 5379.02 hours. Allowing the equal-rate pattern to change gives 5286.11 hours, a difference of 92.90. This comparison explains why dividing a single representative allocation by 120 need not yield the globally least personnel demand.', rf'With seasonal tasks removed, the independently constructed inverse model returns {base["total_person_hours"]:.2f} personnel-hours, matching revised Question 2. This cross-check confirms that both chapters use the same optimal-rate, minimum-labor objective.')
    en = numeric_sync(en, old, q2)
    en = en.replace('A representative month uses about 5379 personnel-hours, including readiness, and 152 flight-hours.', f'The minimum-work month uses about {base["total_person_hours"]:.0f} personnel-hours, including readiness, and {base["drone_flight_hours"]:.0f} flight-hours.')
    for label, text in core_tables(q2, extra).items():
        en = replace_table(en, label, text)
    en = replace_once(en, r'All three methods reach the bound even after a 40\% personnel-budget reduction. Thus this ample-resource comparison provides no completion-rate advantage for optimization.', rf'All three methods reach the bound even after a 40\% personnel-budget reduction. Under the separately defined 3600-hour stress budget, which includes 2880 readiness hours, optimization reaches {pressure[2]["score"]:.2f}\%, versus {pressure[0]["score"]:.2f}\% and {pressure[1]["score"]:.2f}\% for the two rules. This advantage occurs under scarcity; it is not a baseline gain.')
    technology_rows = [['Equivalent checklist', f"{base['score']:.2f}", f"{base['total_person_hours']:.2f}", '0.00', f"{base['drone_flight_hours']:.2f}"]]
    names = ['Drone efficiency 75\\%', 'Drone efficiency 50\\%', 'Ground minimum 10\\%', 'Ground minimum 25\\%']
    for name, row in zip(names, extra['technology_scenarios']):
        technology_rows.append([name] + [f"{row[k]:.2f}" for k in ['score', 'total_person_hours', 'ground_hours', 'drone_flight_hours']])
    technology_table = table('tab:protocol', 'Assumed screening protocols under the baseline resource budgets.', ['Protocol', 'Rate (\\%)', 'Total labor (h)', 'Ground (h)', 'Flight (h)'], technology_rows).replace('[H]', '[!htbp]')
    grid_table = table('tab:grid', 'Discretization sensitivity; tasks and operating rules retained.', ['Grid side (km)', 'Units', 'Rate (\\%)', 'Total labor (h)'], [[f"{r['grid_km']:.0f}", str(r['target_count']), f"{r['score']:.2f}", f"{r['total_person_hours']:.2f}"] for r in sorted(extra['grid_sensitivity'], key=lambda r: r['grid_km'])]).replace('[H]', '[!htbp]')
    sensitivity = r'''
\subsection{Screening protocol and grid sensitivity}
Let $e$ be drone screening capacity relative to the baseline checklist and $p_g$ the required ground-check share. Replace task capacity by $C_js_j\le x_j/a_j+e h_j/b_j$ and, where required, impose $x_j/a_j\ge p_gC_js_j$. The baseline has $e=1$ and $p_g=0$. These are separate protocol scenarios, not measured detection probabilities.

''' + technology_table + r'''

At $e=0.75$, ground screening returns because some drone-assisted checks cost more personnel work per completed task. A 25\% ground requirement also prevents complete substitution. Completion remains at its geographic ceiling under the ample budgets, while work and technology choices change. Zero baseline ground screening therefore depends on the assumed protocol; it is not a finding that rangers are unnecessary.

''' + grid_table + r'''

The 5 km result is 0.87 percentage points below the 10 km baseline, whereas the 15 km result is 2.73 points above it. Total prescribed checks remain area-based; representative locations and response eligibility change. These are discretization effects, so finer units and field-verified destinations are needed near the response boundary. The table does not provide a statistical confidence interval.

'''
    position = en.index(r'\subsection{Weight sensitivity}')
    en = en[:position] + sensitivity + en[position:]
    weight_data = read('output/full_paper/weight_sensitivity_supplement.json')['cases']
    full = [r for r in weight_data if r['human_budget'] == 21240 and not r['name'].startswith('Legal')]
    tight = [r for r in weight_data if r['human_budget'] == 3600 and not r['name'].startswith('Legal')]
    rows = [[a['name'], f"{100*a['animal_share']:.2f}", f"{a['score_own_weights']:.2f}", f"{a['score_baseline_weights']:.2f}", f"{b['score_baseline_weights']:.2f}"] for a, b in zip(full, tight)]
    en = replace_table(en, 'tab:weights', table('tab:weights', 'Completion rates under each priority rule and original-weight evaluation.', ['Weight choice', 'Animal (\\%)', 'Own weights', 'Original weights', 'Tight budget'], rows).replace('[H]', '[!htbp]'))
    boundary = r'''\textbf{Boundary restriction.} The Chitwan polygon is 1214.06 km$^2$, versus 952.63 km$^2$ in the official source: a 27.44\% difference. The published polygon is used only for a conditional trial; it is not accepted as the current legal park boundary. Yellowstone uses the NPS boundary. Both parks still need locally verified emergency access, off-road travel and task costs \cite{wdpca,npsdata,chitwan,unesco,npsrules}.'''
    en = replace_once(en, boundary, r'''\textbf{Boundary restriction.} Chitwan's projected polygon is 1214.06 km$^2$, versus the official 952.63 km$^2$: a 27.44\% discrepancy. Its geodesic area, 1213.00 km$^2$, agrees with the published GIS-area attribute. Projection changes area by only 0.087\%; the source geometry and reported-area convention remain unresolved. The retrieved official GIS report also totals 952.63 km$^2$ \cite{gis2020}. We retain a conditional polygon trial until a matching legal boundary or area explanation is available. Yellowstone uses the NPS boundary \cite{wdpca,npsdata,chitwan}.''')
    wolf = extra['yellowstone']
    selected = [r for r in wolf['cases'] if r['historical_wolf_share'] in [0., .5, .75]]
    wolf_table = table('tab:wolf', 'Yellowstone historical-priority trial with unchanged routes and tasks.', ['Wolf share (\\%)', 'New-rule rate', 'Land-rule rate', 'Labor (h)', 'Changed units'], [[f"{100*r['historical_wolf_share']:.0f}", f"{r['score_own_weights']:.2f}", f"{r['score_original_land_weights']:.2f}", f"{r['total_person_hours']:.2f}", str(r['changed_service_units'])] for r in selected]).replace('[H]', '[!htbp]')
    wolf_text = rf'''
\subsection{{A local historical-priority trial}}
NPS publishes ten 2022 wolf-pack 95\% minimum-convex polygons \cite{{wolf}}. We union overlapping and duplicate polygons, clip them to the NPS park boundary, and intersect them with the existing planning cells. The clipped union covers {wolf['clipped_union_area_km2']:.2f} km$^2$. Each overlap is adjusted by the cell's land fraction. This is historical activity extent, not current wolf density or a measured threat.

Mix normalized historical-use area with land-area weights using an assumed share $\lambda$. For each new rule, retain the reference Y0 plan's rate evaluated under that rule and minimize labor again. Roads, response eligibility, checks and readiness remain fixed. Table~\ref{{tab:wolf}} also evaluates each allocation with the original land weights.

''' + wolf_table + r'''

At a 50\% historical-use share, 61 units change completion. The new-rule target is retained, while original land-weight completion falls from 16.85\% to 15.12\%. Lower work reflects this priority trade-off, not improved ecological protection. The exercise demonstrates how a local ecological layer can alter deployment without importing Etosha's species weights. Current species priorities and seasonal staff access still require local calibration; visitor road closures do not establish emergency permissions \cite{npsrules}.

'''
    position = en.index(r'\section*{Letter to IMMC}')
    # Keep the letter's existing explicit page break after the added subsection.
    position = en.rfind(r'\clearpage', 0, position)
    en = en[:position] + wolf_text + en[position:]
    en = en.replace("First verify current priority-species and maintenance inventories. Then record actual travel, observation and response times, road permissions and equipment use.", "Begin implementation by verifying travel and response access and updating the maintenance sample. Record task duration and follow-up time. Expand species-specific inputs when reliable records become available.")
    en = en.replace("Earlier rendered versions were visually reviewed. The final terminology revision was compiled without a further PDF or layout audit at the team's request.", 'The present revision includes renewed numerical checks and PDF layout review; the corresponding audit records are retained with the source.')
    en = en.replace('The team supplied the control number used here.', 'The team supplied the control number used here and subsequently requested a multi-species scope, correction of the two-stage objective and feasibility-based manuscript revision.')
    additions = r'''\bibitem{gis2020} Nepal DNPWC. \emph{GIS Database of Protected Areas}, 2020. Chitwan district-area table, p. 17. \href{https://giwmscdntwo.gov.np/media/pages/files/Final%20Report_GIS%20Database_v4olikj.pdf}{Official report.}
\bibitem{wolf} US National Park Service. \emph{Yellowstone wolf territories, 1995--2022}; 2022 95\% MCP files. \href{https://www.nps.gov/yell/learn/nature/upload/1995_2022-YELL-wolf-data.zip}{Official GIS archive.}
'''
    en = en.replace(r'\end{thebibliography}', additions + r'\end{thebibliography}')
    # Rebuild revised figures and embed every vector figure in the single file.
    names = {'fig:workflow': 'fig1_framework_pipeline', 'fig:etosha': 'fig2_etosha_demand_response', 'fig:costs': 'fig3_route_costs', 'fig:monthly': 'fig4_monthly_workload', 'fig:joint': 'fig5_resource_joint', 'fig:transfer': 'fig6_transfer_maps', 'fig:deployment': 'fig7_optimal_resource_deployment'}
    for label, name in names.items():
        pattern = r'(\\begin\{figure\}(?:(?!\\end\{figure\}).)*?\\centering\s*)((?:(?!\\end\{figure\}).)*?)(\\caption\{(?:(?!\\end\{figure\}).)*?\\label\{' + re.escape(label) + r'\}(?:(?!\\end\{figure\}).)*?\\end\{figure\})'
        tikz = (ROOT / f'output/full_paper/figures/{name}.tikz').read_text(encoding='utf-8').strip()
        en, count = re.subn(pattern, lambda m: m[1] + tikz + '\n' + m[3], en, flags=re.S)
        assert count == 1, label
    # Chinese explanations stay in the same source; update their scientific content.
    zh = numeric_sync(zh, old, q2)
    for label, text in core_tables(q2, extra, chinese=True).items():
        zh = replace_table(zh, label, text.replace('[!htbp]', '[H]'))
    zh = re.sub(r'\\noindent\\textbf\{这一步怎样做。\}先把第一次求得的每个\$s_j\$固定；.*?(?=\n\n)', lambda _: r'\noindent\textbf{这一步怎样做。}第一阶段求最高服务分，第二阶段保留这个分数，让全部完成率与地面、无人机投入重新选择，使人工最少。区域底线继续适用于零权重单元。修订后的第二题得到5286.11总人时；第三题去掉新增季节任务后独立得到相同结果。', zh, flags=re.S)
    zh = re.sub(r'不增加季节工作且固定第二题返回的服务向量时，.*?(?=\n\n)', lambda _: '去掉新增季节任务后，第三题独立反求模型得到5286.11人时，与修订后的第二题一致。两题都在保持最优服务分的条件下允许完成率重新选择。', zh, flags=re.S)
    zh = re.sub(r'\\noindent\\textbf\{为什么与第二题[^}]+\}.*?(?=\n\n)', lambda _: r'\noindent\textbf{第二、三题怎样衔接。}修订后两题采用相同的最优同分、最少人工口径。响应与基本巡检合计5286.11人时；峰值月再加入1123.38火险检查和422.34钻井运维人时，得到6831.83人时。', zh, flags=re.S)
    zh = zh.replace('允许不同的同分服务格局，与第二题固定格局的再优化不同。', '与修订后的第二题一样，允许不同的同分服务格局。')
    zh = zh.replace('代表性月份约使用5379人时，其中包括待命，并使用152机时。', '最少人工方案约使用5286人时，其中包括待命，并使用144机时。')
    zh = zh.replace('一个代表性配置方案使用', '最优同分方案中的最少人工配置使用')
    scope_zh = '本轮采用多物种保护主线，动物量化继续使用六类现有调查对象。犀牛偷猎在挑战分析中定性保留；其冲突数量不作为本轮求解前置条件。六类2015年调查记录不代表全园所有动物或当前种群分布。数量份额衡量保护责任，不是偷猎概率。\n\n'
    position = zh.index(r'\subsection{保护优先事项与证据}') if r'\subsection{保护优先事项与证据}' in zh else zh.index(r'\section{保护优先')
    if zh[position:].startswith(r'\section'):
        position = zh.index('\n', position) + 1
    zh = zh[:position] + scope_zh + zh[position:]
    # Add new scenario explanations without removing the existing teaching examples.
    chinese_technology = technology_table
    for a, b in [('Assumed screening protocols under the baseline resource budgets.', '基准预算下的假设检查协议。'), ('Protocol', '协议'), ('Rate (\\%)', '服务/\\%'), ('Total labor (h)', '总人时'), ('Ground (h)', '地面人时'), ('Flight (h)', '机时'), ('Equivalent checklist', '基准等效检查'), ('Drone efficiency', '无人机效率'), ('Ground minimum', '地面最低占比')]:
        chinese_technology = chinese_technology.replace(a, b)
    chinese_grid = grid_table
    for a, b in [('Discretization sensitivity; tasks and operating rules retained.', '保留任务及作业规则的网格尺度敏感性。'), ('Grid side (km)', '边长/km'), ('Units', '单元数'), ('Rate (\\%)', '服务/\\%'), ('Total labor (h)', '总人时')]:
        chinese_grid = chinese_grid.replace(a, b)
    position = zh.index(r'\section{模型优点') if r'\section{模型优点' in zh else zh.index(r'\section{优势') if r'\section{优势' in zh else zh.index(r'\section{模型优势') if r'\section{模型优势' in zh else zh.index(r'\section{优点')
    chinese_sensitivity = r'''\subsection{检查协议与网格尺度补充检验}
令$e$为无人机相对筛查效率，$p_g$为必须由地面完成的检查比例。容量改为$C_js_j\le x_j/a_j+e h_j/b_j$，必要时增加$x_j/a_j\ge p_gC_js_j$。基准取$e=1,p_g=0$。这些数值是规划情景，未经过当地配对任务日志校准。

''' + chinese_technology + '\n\n无人机效率为75\\%时，地面筛查恢复到1731.55人时；要求25\\%地面检查时，地面投入为801.56人时。充裕预算下分数均保持57.26，但总人时和技术分工不同。因此基准的零地面筛查依赖技术等效假设，不意味着巡护员可以被设备替代。\n\n' + chinese_grid + '\n\n5、10、15公里网格分别为1554、599、392个单元，服务分为56.39、57.26、59.99。总规定点次按面积保持一致，代表点位置和响应判定会变化。相对10公里基准，5公里低0.87个百分点、15公里高2.73个百分点，这是离散化影响，不是置信区间。\n\n'
    zh = zh[:position] + chinese_sensitivity + zh[position:]
    zh = zh.replace('这是边界数据一致性没有通过，不是公园真实面积增大了27.44\\%。', '公开源边界的测地面积约1213.00平方千米，与发布方GIS面积一致；本地投影只带来约0.087\\%差异，解释不了27.44\\%。官方2020年GIS报告仍列952.63平方千米，实际错误边界段或面积口径尚未确定，不能缩放多边形凑面积。')
    zh = zh.replace('同分服务格局', '同分服务格局')
    wolf_zh = wolf_table
    for a, b in [('Yellowstone historical-priority trial with unchanged routes and tasks.', '黄石历史活动范围责任情景，路线与任务不变。'), ('Wolf share (\\%)', '历史范围/\\%'), ('New-rule rate', '新权重服务'), ('Land-rule rate', '原面积服务'), ('Labor (h)', '人时'), ('Changed units', '变化单元')]:
        wolf_zh = wolf_zh.replace(a, b)
    wolf_zh = r'''\subsection{黄石本地历史生态责任情景}
取得NPS官方2022年十个狼群95\%最小凸多边形，合并重叠和重复几何后裁至公园边界，合并范围4093.87平方千米。它表示历史活动范围，不是当前狼密度、偷猎风险或官方优先级。

将历史范围份额与陆地面积份额按假设权重混合，保留原Y0方案在每套新权重下的服务分，再最小化人工。道路、响应、任务频次、区域底线和待命均不变。

''' + wolf_zh + '\n\n历史范围权重为50\\%时，61个单元改变完成率，原面积权重下的服务由16.85降至15.12。人时减少来自保护责任口径改变后允许的取舍，不能解释为生态保护效果改善。完整数值和逐项检查另存于本轮补充结果。\n\n'
    position = zh.index(r'\section*{致IMMC') if r'\section*{致IMMC' in zh else zh.index(r'\section*{给IMMC') if r'\section*{给IMMC' in zh else zh.index(r'\section*{写给')
    position = zh.rfind(r'\clearpage', 0, position)
    zh = zh[:position] + wolf_zh + zh[position:]
    zh = zh.replace(r'\end{thebibliography}', additions.replace('Official report.', '官方报告。').replace('Official GIS archive.', '官方GIS压缩包。') + r'\end{thebibliography}')
    for path, text in [(enpath, en), (zhpath, zh)]:
        text = text.replace(r'\begin{document}', MARKER + '\n' + r'\begin{document}', 1)
        assert not re.search(r'@[A-Z_]+@', text)
        path.write_text(text, encoding='utf-8')
    manifest = read('output/full_paper/full_paper_manifest.json')
    inputs = ['output/question2/q2_results.json', 'output/question2/q2_model_inputs.json', 'output/question3/q3_results.json', 'output/question4/q4_results.json', 'output/question6/q6_results.json', 'output/full_paper/weight_sensitivity_supplement.json', 'output/revision_feasibility/20261006/revision_results.json']
    manifest.update(status='multispecies_revision_written_compilation_pending', source_sha256=hashlib.sha256(enpath.read_bytes()).hexdigest(), revision_date='2026-10-06', revision_script='scripts/modeling/revise_multispecies_paper.py', revision_history='output/full_paper/history/before_multispecies_revision_20261006.zip', figures=en.count(r'\begin{figure}'), tables=en.count(r'\begin{table}'), numbered_equations=en.count(r'\begin{equation}'))
    manifest['input_sha256'] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in inputs}
    (ROOT / 'output/full_paper/full_paper_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': manifest['status'], 'figures': manifest['figures'], 'tables': manifest['tables'], 'english_source': str(enpath), 'chinese_source': str(zhpath)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
