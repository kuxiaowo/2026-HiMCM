"""Apply the requested presentation revision without regenerating the manuscript.

Saved baseline outputs remain unchanged. Supplementary weight scenarios are
stored separately, with fixed-baseline evaluation and constraint checks.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import re
import zipfile

import numpy as np
from matplotlib import colors, pyplot as plt

import build_question2 as model
import build_full_paper_figures as drawing

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/full_paper'
SOURCE = ROOT / 'docs/paper/full_paper.tex'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def weight_checks(data, report):
    baseline = report['optimum']
    targets = data['targets']
    w0 = np.array([t['objective_weight'] for t in targets])
    alpha0 = report['management_weight_estimation']['weights'][0]
    component_a = np.array([t['animal_component_share'] for t in targets])
    component_f = np.array([t['habitat_component_share'] for t in targets])
    cases = [('Entropy baseline', alpha0), ('Equal components', .5),
             ('Animal emphasis', .9), ('CRITIC alternative',
              report['management_weight_estimation']['CRITIC_alternative'][0])]
    rows = []
    for budget in [data['human_budget'], 3600.]:
        reference = model.solve(data, H=budget)
        assert reference['success']
        for name, alpha in cases:
            weights = alpha * component_a + (1-alpha) * component_f
            result = model.solve(data, H=budget, weights=weights)
            assert result['success']
            rows.append(checked_row(data, name, alpha, budget, weights,
                                    result, reference, w0))

    # Perturb the specially-protected category preference by +/-20%, keeping
    # reciprocity in the judgement matrix. Recalculate both component weights.
    base = read('output/regions/region_base_data.json')['regional_rows']
    survey = [r for r in base if r['region_kind'] == 'survey_stratum']
    species = [s for s in read('output/model1/species_region_counts_2015.json')['species']
               if s['adoption'] == 'core_with_flags']
    for factor in [.8, 1.2]:
        matrix = np.array(report['AHP']['judgement_matrix'], dtype=float)
        matrix[2, :2] *= factor
        matrix[:2, 2] /= factor
        ev, vec = np.linalg.eig(matrix)
        k = np.argmax(ev.real)
        q = np.abs(vec[:, k].real); q /= q.sum()
        cr = float((ev[k].real-3)/2/.58)
        assert cr < .1
        categories = {s['species_code']: 2 if s['law_class'] == 'specially_protected_game'
                      else 0 if s['law_class'] == 'huntable_game' else 1 for s in species}
        totals = {s: sum(r['candidate_count_'+s+'_2015'] for r in survey) for s in categories}
        sum_q = sum(q[c] for c in categories.values())
        animals = {r['region_id']: sum(q[c]*r['candidate_count_'+s+'_2015']/totals[s]
                    for s,c in categories.items())/sum_q for r in survey}
        changed = copy.deepcopy(targets)
        for t in changed:
            t['animal_component_raw'] = animals.get(t['region_id'], 0.) * t['within_region_area_share'] * t['entry_index']
        estimation = model.management_weights(changed, [r['region_id'] for r in survey])
        alpha = estimation['weights'][0]
        raw_a = np.array([t['animal_component_raw'] for t in changed])
        weights = alpha*raw_a/raw_a.sum() + (1-alpha)*component_f
        for budget in [data['human_budget'], 3600.]:
            reference = model.solve(data, H=budget)
            result = model.solve(data, H=budget, weights=weights)
            row = checked_row(data, f'Legal preference x{factor:g}', alpha, budget,
                              weights, result, reference, w0)
            row.update(judgement_matrix=matrix.tolist(), category_weights=q.tolist(),
                       consistency_ratio=cr)
            rows.append(row)
    payload = {'scope': 'Supplementary Q2 weight tests; baseline model files unchanged',
               'generated_at_utc': datetime.now(timezone.utc).isoformat(),
               'scarce_person_hour_budget': 3600.,
               'fixed_baseline_weights_used_for_comparison': True,
               'cases': rows,
               'input_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
                  for p in ['output/question2/q2_results.json', 'output/question2/q2_model_inputs.json',
                            'output/regions/region_base_data.json', 'output/model1/species_region_counts_2015.json']}}
    (OUT/'weight_sensitivity_supplement.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    return rows


def checked_row(data, name, alpha, budget, weights, result, reference, baseline_weights):
    assert result['success'] and abs(weights.sum()-1) < 1e-10
    x,h,s = (np.array(result[k]) for k in ['x','h','s'])
    ts = data['targets']
    f = np.array([t['planned_checks_month'] for t in ts])
    eligible = np.array([t['response_eligible'] for t in ts],dtype=float)
    allowed = np.array([t['drone_allowed'] for t in ts],dtype=float)
    g = np.array([1/(t['ground_hours_per_check'] or 1) for t in ts])
    u = np.array([1/(t['flight_hours_per_check'] or 1) for t in ts])
    gamma = np.array([t['operator_hours_per_check']/t['flight_hours_per_check']
                      if t['drone_allowed'] else 0 for t in ts])
    assert np.max(f*s-g*x-u*h) < 1e-6
    assert min(x.min(),h.min(),s.min()) > -1e-7 and np.max(s-eligible) < 1e-7
    assert np.max(x*(1-eligible)) < 1e-7 and np.max(h*(1-allowed)) < 1e-7
    assert x.sum()+gamma@h+data['response_reserved_hours'] <= budget+1e-6
    assert h.sum() <= data['drone_budget']+1e-6
    for rid in data['region_ids']:
        ii = [j for j,t in enumerate(ts) if t['region_id']==rid]
        mu=np.array([ts[j]['within_region_area_share'] for j in ii])
        assert mu@s[ii]+1e-7 >= .15*(mu@eligible[ii])
    region = model.regional_rows(data,result)
    reference_regions = model.regional_rows(data,reference)
    fixed_score=float(100*baseline_weights@s)
    return {'name':name,'animal_share':float(alpha),'human_budget':float(budget),
            'score_own_weights':result['score'],'score_baseline_weights':fixed_score,
            'baseline_weight_score_change':fixed_score-float(100*baseline_weights@np.array(reference['s'])),
            'person_hours':result['total_person_hours'],'flight_hours':result['drone_flight_hours'],
            'changed_service_units':int(np.count_nonzero(np.abs(s-np.array(reference['s']))>1e-8)),
            'max_regional_labor_change':max(abs(a['allocated_monitoring_person_hours']-b['allocated_monitoring_person_hours'])
                                              for a,b in zip(region,reference_regions)),
            'max_regional_flight_change':max(abs(a['drone_flight_hours']-b['drone_flight_hours'])
                                               for a,b in zip(region,reference_regions)),
            'regions':region,'independent_constraint_checks':'passed'}


def allocation_map(data, report):
    c=drawing.Canvas(16.8,6.2)
    geoms=model.load_geometry()
    rows={r['region_id']:r for r in report['regions']}
    xmin=min(g.bounds[0] for _,g in geoms); xmax=max(g.bounds[2] for _,g in geoms)
    ymin=min(g.bounds[1] for _,g in geoms); ymax=max(g.bounds[3] for _,g in geoms)
    scale=min(7.5/(xmax-xmin),4.05/(ymax-ymin))
    for panel,field,title,cmapname in [(0,'allocated_monitoring_person_hours','(a) Monitoring labor (h/month)','Blues'),
                                     (1,'drone_flight_hours','(b) Drone flight (h/month)','YlGnBu')]:
        x0=.35+8.3*panel
        xy=lambda coords:np.array([(x0+(x-xmin)*scale,2.15+(y-ymin)*scale) for x,y in coords])
        maximum=max(r[field] for r in rows.values()); cmap=plt.get_cmap(cmapname)
        c.text(x0+3.75,5.85,title,bold=True)
        labels=[]
        offsets={'ENP2':(-.1,-.15),'ENP3410':(0,.28),'ENP9':(-.08,.15),
                 'ENP11':(.1,.30),'ENP12':(.18,-.15),'ENP16':(-.42,0),
                 'UNSURVEYED_OTHER':(.12,1.05)}
        for rid,g in geoms:
            fill=colors.to_hex(cmap(.08+.85*rows[rid][field]/maximum))
            for polygon in model.polygons(g.simplify(600,preserve_topology=True)):
                if polygon.area<200000:continue
                c.poly([xy(polygon.exterior.coords)]+[xy(r.coords) for r in polygon.interiors],fill,'white',.35)
            point=g.representative_point(); px,py=xy([(point.x,point.y)])[0]
            dx,dy=offsets.get(rid,(0,0));x,y=px+dx,py+dy
            code=rid.removeprefix('ENP') if rid.startswith('ENP') else 'P' if rid=='PAN_MAIN' else 'O'
            if dx or dy:c.line([(px,py),(x,y)],drawing.INK,.45)
            labels.append((x,y,code,'white' if rows[rid][field]/maximum>.6 else drawing.INK))
        # Draw labels after all adjacent polygons, so neighbouring fills cannot
        # obscure glyphs extending beyond a small region.
        for x,y,rid,color in labels:c.text(x,y,rid,c=color)
        for base in data['bases']:
            x,y=xy([model.FWD(base['lon'],base['lat'])])[0];c.star(x,y,.11,drawing.GOLD)
        for i in range(8):c.rect(x0+3.2+i*.37,1.6,.37,.18,colors.to_hex(cmap(.08+.85*i/7)))
        c.text(x0+3.2,1.28,'0',ha='left');c.text(x0+6.16,1.28,f'{maximum:.2f}',ha='right')
        c.line([(x0+.25,1.6),(x0+.25+50000*scale,1.6)],drawing.INK,1.5)
        c.text(x0+.25+25000*scale,1.28,'50 km')
        c.line([(x0+.3,4.65),(x0+.3,5.00)],drawing.INK,1,arrow=True);c.text(x0+.3,5.23,'N')
    c.star(.55,.74,.105,drawing.GOLD)
    c.text(.78,.74,'Six candidate posts; 480 shared readiness hours each',ha='left')
    c.text(.5,.24,'Numbers: ENP regions; P: main pan; O: survey-external area',ha='left')
    c.save('fig7_optimal_resource_deployment')
    (OUT/'figures/deployment_figure_manifest.json').write_text(json.dumps(drawing.FIGURES[-1],indent=2)+'\n',encoding='utf-8')


def replace_equation(tex,label,body):
    pattern=r'\\begin\{equation\}(?:(?!\\end\{equation\}).)*?\\label\{'+re.escape(label)+r'\}\s*\\end\{equation\}'
    new='\\begin{equation}\n'+body.strip()+'\n\\label{'+label+'}\n\\end{equation}'
    tex,n=re.subn(pattern,lambda m:new,tex,flags=re.S)
    assert n==1,label
    return tex


def edit_source(rows):
    tex=SOURCE.read_text(encoding='utf-8')
    assert '% PRESENTATION_REVISION_20261006' not in tex,'Already revised; avoid duplicate authoring'
    abstract=r'''Protecting a large reserve requires a plan that links important locations, completed inspections and timely ground response. We study how Etosha National Park can allocate personnel and drones, maintain service through seasonal tasks, and adapt the framework to other parks.

\textbf{Method.} We divide Etosha into 17 reporting regions and 599 planning units. Historical animal surveys and burnable-habitat areas define relative priorities, while road routes and a two-hour response rule determine where inspections can receive effective follow-up. A linear allocation model maximizes weighted task completion. A monthly extension adds fire checks and maintenance of 17 historically documented boreholes, then finds the personnel needed to maintain the selected service target. The score measures inspection service, not wildlife survival.

\textbf{Allocation results.} The baseline assumes that 60\% of 295 reference employees are available: 177 person-months, or \textbf{21240} effective personnel-hours. Thirty proposed drones supply \textbf{1200} flight-hours per month. The best score is \textbf{57.26} out of 100; a representative solution uses \textbf{5379.02} personnel-hours, including response readiness, and \textbf{151.82} flight-hours. The remaining capacity shows that access and response locations limit service. Among three tested additional posts, the ENP5 candidate raises the score to \textbf{64.27} within the same total budgets.

\textbf{Seasonal demand and robustness.} Maintaining the target requires \textbf{57} personnel in the busiest normal month and \textbf{62} under the specified drought-maintenance scenario. These are conditional workload estimates. Tested animal--habitat weights change the scoring scale but leave the base deployment unchanged; tighter budgets make priorities matter more. Travel speed, response access and visit timing also affect service.

\textbf{Recommendation and transfer.} Prioritize verified response access and workable visit dates before adding equipment. Trials for Chitwan and Yellowstone use real spatial inputs and explicit local assumptions; Chitwan's boundary fails the area-consistency check, so its results remain conditional polygon trials. Actual staffing and ecological adequacy require field validation.

'''
    start=tex.index('Protecting a large reserve');end=tex.index(r'\noindent\textbf{Keywords:}',start)
    tex=tex[:start]+abstract+tex[end:]
    tex=tex.replace(r'\setlength{\abovedisplayskip}{7pt}\setlength{\belowdisplayskip}{7pt}',
                    r'\setlength{\abovedisplayskip}{8pt}\setlength{\belowdisplayskip}{8pt}'+'\n'+r'\setlength{\jot}{5pt}')
    bodies={
      'eq:protection':r'''\begin{aligned}
g_j^{\mathrm{service}}&=d_jr_j,\\
P&=100\sum_jw_jg_j^{\mathrm{service}},\\
L&=\sum_jw_j(1-g_j^{\mathrm{service}}).
\end{aligned}''',
      'eq:values':r'''\begin{aligned}
V_i^A&=\frac{\sum_m q_{\ell(m)}(N_{im}/\sum_{v\in\mathcal I_S}N_{vm})}{\sum_mq_{\ell(m)}},\\
V_i^F&=\frac{A_i^F}{\sum_vA_v^F}.
\end{aligned}''',
      'eq:ahp':r'''\begin{aligned}
\mathbf A&=\begin{pmatrix}1&1/2&1/3\\2&1&1/2\\3&2&1\end{pmatrix},\\
\mathbf q&=(0.163424,0.296961,0.539615)^{\mathsf T}.
\end{aligned}''',
      'eq:entropy':r'''\begin{aligned}
p_{ik}&=\frac{X_{ik}}{\sum_vX_{vk}},\\
e_k&=-\frac{\sum_i p_{ik}\ln p_{ik}}{\ln15},\\
\alpha_k&=\frac{1-e_k}{(1-e_A)+(1-e_F)}.
\end{aligned}''',
      'eq:response':r'''\begin{aligned}
t_d+d_{bj}^+/v_g+d_j^\perp/v_w&\le T_{\max},\\
r_j&=\mathbf1\{\text{at least one qualifying post}\}.
\end{aligned}''',
      'eq:costs':r'''\begin{aligned}
a_j&=n_g(D_j/v_g+2d_j^\perp/v_w+t_o+t_p),\\
b_j&=2d_j^\perp/v_u+t_o,\\
o_j&=n_u(D_j/v_g+t_p+b_j),\\
\gamma_j&=o_j/b_j.
\end{aligned}''',
      'eq:checks':r'''\begin{aligned}
C_j&=8A_j/100,\\
\sum_j C_j&=8\sum_j A_j/100.
\end{aligned}''',
      'eq:allocation':r'''\begin{aligned}
\max_{\mathbf x,\mathbf h,\mathbf s}\quad&100\sum_jw_js_j\\
\mathrm{s.t.}\quad&C_js_j\le g_jx_j+u_jh_j,\qquad j\in\mathcal J,\\
&\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j\le H-H_0,\\
&\sum_jh_j\le U,\\
&\sum_{j\in\mathcal J_i}\mu_js_j\ge0.15Q_i,\qquad i\in\mathcal I,\\
&0\le s_j\le r_j,\qquad j\in\mathcal J,\\
&x_j\ge0,\qquad j\in\mathcal J,\\
&h_j\ge0,\qquad j\in\mathcal J,\\
&x_j=0,\qquad r_j=0,\\
&h_j=0,\qquad j\notin\mathcal J_U.
\end{aligned}''',
      'eq:water':r'''\begin{aligned}
a_{\ell t}^{W}&=2(T_\ell^{\mathrm{rt}}+\tau_t+1/12),\\
W_t&=f_t\sum_{\ell\in\mathcal L}a_{\ell t}^{W}.
\end{aligned}''',
      'eq:staff':r'''\begin{aligned}
N_t&=\left\lceil\frac{H_t^{\min}}{120}\right\rceil,\\
N_{\mathrm{year}}&=\max_{t=1,\ldots,12}N_t.
\end{aligned}''',
      'eq:transfertarget':r'''\begin{aligned}
P_{\mathrm{geo}}^{(p)}&=100\sum_jw_j^{(p)}r_j^{(p)},\\
\eta^{(p)}&=0.90P_{\mathrm{geo,base}}^{(p)}.
\end{aligned}'''}
    for label,body in bodies.items():tex=replace_equation(tex,label,body)
    # Keep each display group numbered once, preserving all existing references.
    tex=tex.replace(r'\subsection{What the model supports}',r'\subsection{Strengths}')
    tex=tex.replace(r'\subsection{A practical calibration sequence}',r'\subsection{Weaknesses and Limitations}')
    old=r'''All inputs and saved allocations are traceable. Independent checks cover capacity, floors, prohibited technology use, budgets, response gates and totals. A second calculation reproduces the cross-park optimization results. These checks establish computational consistency; they do not establish measured ecological outcomes.'''
    new=old+'\n\n'+r'''\subsection{Weaknesses and Limitations}
The model depends on historical surveys, assumed task costs and unverified access conditions. Monthly pooled hours do not establish a feasible daily roster. Its service score also cannot confirm sufficient ecological protection. Table~\ref{tab:limits} identifies the main limits and the observations needed to address them.'''
    assert old in tex;tex=tex.replace(old,new)
    # The weakness heading belongs before the limitations table; retain the
    # existing calibration paragraphs under the same subsection.
    marker=r'\subsection{Weaknesses and Limitations}'
    second=tex.index(marker,tex.index(marker)+len(marker));tex=tex[:second]+tex[second+len(marker):]
    map_text=r'''
\begin{figure}[!htbp]
\centering
\input{output/full_paper/figures/fig7_optimal_resource_deployment.tikz}
\caption{Optimal resource deployment under fixed candidate posts: monthly monitoring labor and drone flight-hours. Shared response readiness is separate.}
\label{fig:deployment}
\end{figure}

Figure~\ref{fig:deployment} locates the resource totals for all 17 regions in Table~\ref{tab:regions}. The six candidate posts each reserve 480 response personnel-hours per month. Regional shading includes monitoring and operator support; it excludes those shared readiness hours. ENP9 receives no effective service because no unit meets the response rule. ENP11 has substantial demand but almost no reachable area. The map reports hours, not integer employees or aircraft stationed in each region. Post locations are fixed assumptions rather than an optimized station network.

'''
    insert=tex.index(r'\subsection{Geographic ceiling',tex.index(r'\label{tab:regions}')) if r'\subsection{Geographic ceiling' in tex else -1
    if insert<0:
        insert=tex.index(r'\subsection',tex.index(r'\label{tab:regions}'))
    tex=tex[:insert]+map_text+tex[insert:]
    base=[r for r in rows if r['human_budget']==21240 and not r['name'].startswith('Legal')]
    scarce=[r for r in rows if r['human_budget']==3600 and not r['name'].startswith('Legal')]
    body=r'''
\subsection{Weight sensitivity}
Weight tests ask whether a different definition of priority changes deployment. We replace the animal share while retaining roads, task requirements, technology eligibility and response rules, and solve each case again. Entropy uses differences among the 15 surveyed regions; CRITIC is an alternative based on variation and overlap between indicators. Neither method measures loss probabilities. The legal-category comparison remains a declared team judgement.

\begin{table}[!htbp]
\centering\normalsize
\caption{Weight sensitivity: scores under each case's weights and a common baseline evaluation.}
\label{tab:weights}
\begin{tabular}{lrrrr}
\toprule
Weight choice & Animal (\%) & Own score & Base score & Tight-budget base score \\
\midrule
'''
    for a,b in zip(base,scarce):
        body+=f"{a['name']} & {100*a['animal_share']:.2f} & {a['score_own_weights']:.2f} & {a['score_baseline_weights']:.2f} & {b['score_baseline_weights']:.2f} \\\\\n"
    body+=r'''\bottomrule
\end{tabular}
\end{table}

At the 21240-hour baseline, all four choices return identical unit service, regional labor and flight allocations. Their own scores differ because the scoring weights change; evaluating every solution with the original weights gives 57.26. The current budget meets positive-weight reachable demand, so changing priorities cannot remove the response gaps.

'''
    changed=max(r['changed_service_units'] for r in scarce)
    scoremin=min(r['score_baseline_weights'] for r in scarce);scoremax=max(r['score_baseline_weights'] for r in scarce)
    body+=f'''The tight-budget trial allows 3600 personnel-hours, including 2880 readiness hours, and retains 1200 flight-hours. It deliberately tests scarcity rather than the current staffing assumption. Across the four choices, fixed-baseline scores range from {scoremin:.2f} to {scoremax:.2f}; up to {changed} units change completion relative to the tight-budget entropy solution. This shows that priority choices can matter when inspection labor is limited.\n\n'''
    legal_base=[r for r in rows if r['human_budget']==21240 and r['name'].startswith('Legal')]
    legal_scarce=[r for r in rows if r['human_budget']==3600 and r['name'].startswith('Legal')]
    body+=f'''We also raise and lower the specially protected category's pairwise preference by 20\\%, preserve reciprocal comparisons, and recompute animal responsibility and entropy weights. Both matrices pass the consistency check. Base-budget deployment remains unchanged; under the tight budget, the fixed-baseline scores are {legal_scarce[0]['score_baseline_weights']:.2f} and {legal_scarce[1]['score_baseline_weights']:.2f}. All supplementary cases pass independent task-capacity, response, technology, regional-floor and budget checks. These finite perturbations support local robustness, not independence from every possible priority judgement.\n\n'''
    insert=tex.index(r'\clearpage\n\section{Strengths') if r'\clearpage\n\section{Strengths' in tex else tex.index(r'\section{Strengths')
    # Insert before the existing top-level page break.
    insert=tex.rfind(r'\clearpage',0,insert)
    tex=tex[:insert]+body+tex[insert:]
    tex=tex.replace('% CONTINUOUS_ENGLISH_LAYOUT_20261006','% CONTINUOUS_ENGLISH_LAYOUT_20261006\n% PRESENTATION_REVISION_20261006')
    assert r'\boxed' not in tex and r'\fbox' not in tex
    SOURCE.write_text(tex,encoding='utf-8')
    manifest=read('output/full_paper/full_paper_manifest.json')
    manifest.update(status='revision_pending_compilation',figures=7,tables=14,
                    source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    supplemental_weight_results='output/full_paper/weight_sensitivity_supplement.json',
                    revision_history='output/full_paper/history/before_presentation_revision_20261006.zip')
    manifest['input_sha256']['output/full_paper/weight_sensitivity_supplement.json']=hashlib.sha256((OUT/'weight_sensitivity_supplement.json').read_bytes()).hexdigest()
    (OUT/'full_paper_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    backup=OUT/'history/before_presentation_revision_20261006.zip'
    assert not backup.exists(),'Protect previous backup'
    backup.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in ['docs/paper/full_paper.tex','output/pdf/full_paper.pdf',
                  'output/full_paper/full_paper_manifest.json','output/full_paper/full_paper_validation.json',
                  'output/full_paper/full_paper_layout_validation.json']:
            archive.write(ROOT/p,p)
    data=read('output/question2/q2_model_inputs.json');report=read('output/question2/q2_results.json')
    rows=weight_checks(data,report)
    allocation_map(data,report)
    edit_source(rows)
    print(json.dumps([{k:r[k] for k in ['name','human_budget','score_baseline_weights','changed_service_units']}
                       for r in rows],indent=2))


if __name__=='__main__':main()
