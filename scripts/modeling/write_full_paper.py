"""Build the English competition manuscript from current verified model outputs."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from full_paper_body import BODY

ROOT=Path(__file__).resolve().parents[2]
PAPER=ROOT/'docs/paper'
OUT=ROOT/'output/full_paper'
FIG=OUT/'figures'

PREAMBLE=r'''\RequirePackage{fix-cm}
\documentclass[12pt,a4paper]{article}
\usepackage[left=1.5cm,right=1.5cm,top=1.5cm,bottom=1.5cm,headheight=12bp,headsep=4bp,footskip=22bp]{geometry}
\usepackage{fontspec}
\IfFontExistsTF{Times New Roman}{\setmainfont{Times New Roman}}{\setmainfont{TeX Gyre Termes}}
\usepackage{amsmath,amssymb,booktabs,tabularx,array,graphicx,xcolor,tikz}
\usepackage{float,caption,fancyhdr,lastpage,titlesec,hyperref}
\usepackage{indentfirst}
\usetikzlibrary{arrows.meta}
\hypersetup{hidelinks,pdftitle={Planning Wildlife Protection under Geographic and Resource Constraints},pdfauthor={Team 510105201001220151}}
\newcommand{\TeamNumber}{510105201001220151}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\fontsize{9}{10.8}\selectfont Team \#\TeamNumber}
\fancyhead[R]{\fontsize{9}{10.8}\selectfont Page \thepage\ of \pageref{LastPage}}
\renewcommand{\headrulewidth}{0.4pt}
\setcounter{tocdepth}{2}\setcounter{secnumdepth}{2}
\numberwithin{equation}{section}
\titleformat{\section}{\fontsize{22}{33}\selectfont\bfseries}{\thesection.}{0.55em}{}
\titleformat{\subsection}{\fontsize{16}{24}\selectfont\bfseries}{\thesubsection}{0.6em}{}
\titlespacing{\section}{0pt}{6pt}{5pt}
\titlespacing{\subsection}{0pt}{5pt}{4pt}
\DeclareCaptionFont{referencecaption}{\fontspec{Arial}\fontsize{10}{12}\selectfont}
\captionsetup{font=referencecaption,labelfont=referencecaption,labelsep=colon,skip=3pt,justification=centering}
\setlength{\parindent}{24pt}\setlength{\parskip}{1.2pt}
\setlength{\abovedisplayskip}{7pt}\setlength{\belowdisplayskip}{7pt}
\setlength{\abovedisplayshortskip}{4pt}\setlength{\belowdisplayshortskip}{4pt}
\setlength{\intextsep}{8pt}\setlength{\textfloatsep}{8pt}
\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.08}
\emergencystretch=2em
\begin{document}
'''


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def f(v,digits=2):
    if 0<v<0.5*10**(-digits):return '<'+f'{10**(-digits):.{digits}f}'
    return f'{v:.{digits}f}'


def table(label,caption,headers,rows,spec=None,note=''):
    spec=spec or 'l'+'r'*(len(headers)-1)
    env='tabularx' if 'X' in spec else 'tabular'
    spec=re.sub(r'p\{([^}]+)\}',lambda m:r'>{\raggedright\arraybackslash}p{'+m.group(1)+'}',spec)
    spec=spec.replace('X',r'>{\raggedright\arraybackslash}X')
    args=r'{\linewidth}{'+spec+'}' if env=='tabularx' else '{'+spec+'}'
    lines=[r'\begin{table}[H]',r'\centering\normalsize',r'\caption{'+caption+'}',r'\label{'+label+'}',
           r'\begin{'+env+'}'+args,r'\toprule',' & '.join(headers)+r' \\',r'\midrule']
    lines+=[' & '.join(map(str,row))+r' \\' for row in rows]
    lines += [r'\bottomrule',r'\end{'+env+'}']
    if note:lines += [r'\par\smallskip\begin{minipage}{\linewidth}'+note+r'\end{minipage}']
    lines += [r'\end{table}']
    return '\n'.join(lines).replace(r'\centering\normalsize',r'\centering\fontsize{11}{13.2}\selectfont') if label=='tab:terms' else '\n'.join(lines)


def figure(name,label,caption):
    tikz=(FIG/(name+'.tikz')).read_text(encoding='utf-8')
    # Draw at the reference 16.8 cm width to preserve the 12 pt figure labels.
    return '\n'.join([r'\begin{figure}[H]',r'\centering',tikz.strip(),r'\caption{'+caption+'}',
                       r'\label{'+label+'}',r'\end{figure}'])


REFERENCES=[
 ('problem',r'IM$^2$C. \emph{Protecting Wildlife at Scale}, 2026 problem statement and submission rules supplied to the team.',None),
 ('survey',r'\emph{Etosha aerial wildlife survey report}, 2015. Regional abundance source.',
  'https://rhinoresourcecenter.com/wp-content/uploads/2022/01/1642693511.pdf'),
 ('law',r'Namibia. \emph{Nature Conservation Ordinance 4 of 1975}, consolidated legal categories.',
  'https://namibiatradeportal.gov.na/application/files/3617/2986/2681/Nature_Conservation_Ordinance_4_of_1975.pdf'),
 ('worldcover',r'ESA. \emph{WorldCover 2021}, v200. Land-cover data and classification.',
  'https://esa-worldcover.org/en/data-access'),
 ('osm',r'OpenStreetMap contributors / Geofabrik. Namibia snapshot, 3 October 2026; Nepal source records documented in the project.',
  'https://download.geofabrik.de/africa/namibia.html'),
 ('fire',r'Namibia Ministry of Environment and Tourism. \emph{Fire Management Strategy}, 2016, Etosha operating windows.',
  'https://www.meft.gov.na/files/downloads/66c_Fire%20Management_Strategy%20Final%20Version.pdf'),
 ('water',r'Riddell, E. S., Kilian, W., Versfeld, W., and Kosoana, M. Groundwater stable isotope profile of the Etosha National Park, Namibia. \emph{Koedoe}, 58(1), 2016. Table 1 records the 2013 sample.',
  'https://koedoe.co.za/index.php/koedoe/article/view/1329/1890'),
 ('annual',r'Namibia MEFT. \emph{Annual Report 2021/2022}. Artificial-water-point equipment evidence.',
  'https://www.meft.gov.na/files/downloads/MEFT%20Annual%20Report%202021-2022.pdf'),
 ('season',r'Dryad. Etosha study dataset, 2024; study-area dry/wet-season classification.',
  'https://datadryad.org/dataset/doi:10.5061/dryad.4qrfj6qm3'),
 ('unesco',r'UNESCO World Heritage Centre. \emph{Chitwan National Park} and associated conservation records.',
  'https://whc.unesco.org/en/list/284'),
 ('chitwan',r'Nepal DNPWC. \emph{Chitwan National Park Management Plan 2013--2017} and official UNESCO report; boundary-area reference 952.63 km$^2$.',
  'https://dnpwc.gov.np/media/files/UNESCO_Report_of_Chitwan_National_Park.pdf'),
 ('wdpca',r'UNEP-WCMC. \emph{WDPCA / Protected Planet}, October 2026, site 805 published polygon. Its area mismatch is retained as a failed calibration check.',
  'https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer/1'),
 ('npsdata',r'US National Park Service. Yellowstone boundary, public roads and location datasets; source queries and fingerprints retained.',
  'https://irma.nps.gov/DataStore/Reference/Profile/2316784'),
 ('npsrules',r'US National Park Service. Yellowstone visitor use, current conditions, and laws and policies.',
  'https://www.nps.gov/yell/learn/management/lawsandpolicies.htm'),
 ('codex',r'OpenAI. \emph{Codex}, AI coding assistant used in the October 2026 work session; GPT-6 model family, exact deployed version unavailable. Uses and verification are described in the AI-use report.',
  'https://openai.com/codex/'),
]


def main():
    existing=PAPER/'full_paper.tex'
    if existing.exists() and '% CONTINUOUS_ENGLISH_LAYOUT_20261006' in existing.read_text(encoding='utf-8'):
        raise SystemExit('The English manuscript has an expanded introduction and continuous layout. Edit the current source in place; this older generator would overwrite those revisions.')
    q2=read('output/question2/q2_results.json');d=read('output/question2/q2_model_inputs.json')
    q3=read('output/question3/q3_results.json');q4=read('output/question4/q4_results.json');q6=read('output/question6/q6_results.json')
    assert d['human_budget']==21240 and d['drone_budget']==1200
    assert q3['fixed_reference_staff']==177 and q3['verification_summary']['passed']
    assert read('output/question4/q4_independent_verification.json')['passed']
    assert q6['status']=='real_geographic_inputs_with_explicit_service_assumptions'
    base=q2['optimum'];fw=q2['best_forward_post']['result']
    scenarios={v['name']:v['result'] for v in q2['scenarios']}
    months=q3['monthly'];peak=max(months,key=lambda v:v['required_person_hours'])
    drought=next(v for v in q3['sensitivity'] if v['scenario']=='base' and v['abnormal_drought'])
    wet=months[0];vs=q3['verification_summary'];policy={v['scenario']:v for v in q4['policy_comparisons']}
    joint={(v['staff'],v['drone_budget']):v for v in q4['joint_peak_scenarios']}
    hours=sum(t['support_area_km2'] for t in d['targets'])
    reach=sum(t['support_area_km2'] for t in d['targets'] if t['response_eligible'])
    audit4=read('output/question4/q4_independent_verification.json')
    values={
      'TARGETS':str(len(d['targets'])),'VARIABLES':str(3*len(d['targets'])),'H':f(d['human_budget'],0),'U':f(d['drone_budget'],0),
      'AREA':f(hours),'SCORE':f(base['score']),'SCORE_FULL':f'{base["score"]:.8f}',
      'Q2_H':f(base['total_person_hours']),'Q2_U':f(base['drone_flight_hours']),
      'Q2_H_ROUND':f(base['total_person_hours'],0),'Q2_U_ROUND':f(base['drone_flight_hours'],0),
      'FORWARD_SCORE':f(fw['score']),'FORWARD_GAIN':f(fw['score']-base['score']),
      'MOBILE_H':f(d['human_budget']-d['response_reserved_hours'],0),'OPERATOR_H':f(base['drone_operator_hours']),
      'CHECKS':f(sum(t['planned_checks_month'] for t in d['targets'])),
      'IDLE_H':f(d['human_budget']-base['total_person_hours']),'IDLE_U':f(d['drone_budget']-base['drone_flight_hours']),
      'REACHABLE':str(sum(t['response_eligible'] for t in d['targets'])),'REACH_SHARE':f(100*reach/hours),
      'NODRONE_H':f(scenarios['无人机停用']['total_person_hours']),
      'PEAK_N':str(peak['required_staff']),'PEAK_H':f(peak['required_person_hours']),'PEAK_U':f(peak['flight_hours']),
      'UNREACH_FIRE':f(peak['unreachable_extra_fire_checks']),'REACH_FIRE':f(peak['extra_fire_checks']),
      'WATER_DRY':f(peak['water_hours']),'WATER_WET':f(wet['water_hours']),'WATER_DROUGHT':f(drought['peak_water_hours']),
      'GLOBAL_Q2_H':f(vs['free_equal_score_baseline_person_hours']),'PATTERN_SAVING':f(vs['free_equal_score_reallocation_saves_person_hours']),
      'BASE_MONITOR':f(peak['base_monitoring_person_hours']),'FIRE_LABOR':f(peak['extra_fire_person_hours']),
      'ONE_LESS_N':str(peak['required_staff']-1),'ONE_LESS_SCORE':f(vs['one_fewer_peak_staff_forward_score']),
      'DROUGHT_N':str(drought['annual_fixed_staff']),'DROUGHT_H':f(drought['peak_person_hours']),'DROUGHT_U':f(drought['peak_flight_hours']),
      'DROUGHT_DELTA_H':f(drought['peak_person_hours']-peak['required_person_hours']),
      'DROUGHT_DELTA_N':str(drought['annual_fixed_staff']-peak['required_staff']),
      'Q4_AUDITED':str(audit4['independently_checked_feasible_solutions']),
      'N57_U160':f(joint[57,160]['score']),'N59_U120':f(joint[59,120]['score']),
      'RETAIN_N59_U120':f(policy['peak_N59_U120']['retained']['score']),
      'DROUGHT_GAIN':f(policy['drought_N59_U120']['gain_points']),'NO_UAV_N':str(vs['no_UAV_peak_staff']),
      'STAGGER_PEAK':f(q4['water_schedule_comparison'][0]['peak_daily_water_hours']),
      'CLUSTER_PEAK':f(q4['water_schedule_comparison'][1]['peak_daily_water_hours']),
      'ROAD20_SCORE':f(scenarios['道路速度20km/h']['score']),'ROAD40_SCORE':f(scenarios['道路速度40km/h']['score']),
      'RESPONSE3_SCORE':f(scenarios['响应期限3小时']['score']),
      'CHITWAN_AREA':f(q6['parks']['chitwan']['polygon_area_km2']),
    }
    rows=sorted(q2['regions'],key=lambda v:-v['demand_weight'])
    values['ENP1_H']=f(next(v for v in rows if v['region_id']=='ENP1')['allocated_monitoring_person_hours'])
    blocks={}
    blocks['TAB_TERMS']=table('tab:terms','Main symbols and their meanings.', ['Symbol','Definition'],[
      [r'$i,j,t$','Reporting region, inspection unit and month.'],
      [r'$A_j,C_j$','Unit area and prescribed monthly checks.'],
      [r'$w_j,s_j$','Relative inspection importance and completion fraction.'],
      [r'$r_j$','1 when ground staff can arrive within the time limit; 0 otherwise.'],
      [r'$x_j,h_j$','Ground screening personnel-hours and drone flight-hours.'],
      [r'$H,U,H_0$','Personnel limit, flight limit and reserved response work.'],
    ],'p{2.1cm}X')
    blocks['TAB_PRIORITIES']=table('tab:priorities','Provisional management priorities.', ['Priority','Challenge and evidence'],[
      ['1','Poaching and illegal entry: the problem identifies continuing rhinoceros losses; priority-object losses are difficult to replace.'],
      ['2','Harmful wildfire and habitat damage: potentially widespread effects on animals and habitats; distinguish prescribed fire.'],
    ],'p{1.3cm}X')
    blocks['TAB_PARAMETERS']=table('tab:parameters','Etosha operating assumptions and resource settings.', ['Item','Setting'],[
      ['Travel speed','Road 30, walking 4, drone flight 40 km/h.'],
      ['Task time / team','Observation 10, preparation 5, dispatch 10 minutes; two people per team.'],
      ['Service / response','8 checks per 100 km$^2$/month; ground arrival within 2 hours.'],
      ['Technology eligibility',r'At most 0.6 flight-hours/check; regional openness at least 60\%.'],
      ['Access / service floor',r'Entry-index decay scale 2 hours; reachable-area service floor 15\%.'],
      ['Personnel',r'295 reference employees; 60\% availability; 120 hours/person-month.'],
      ['Drones','30 aircraft; 2 flight-hours/day for 20 flyable days/month.'],
      ['Readiness','Six candidate posts, two people each, 8 hours/day for 30 days.'],
    ],'p{4.0cm}X')
    rr=[]
    for v in rows:
      name={'PAN_MAIN':'Salt pan*','UNSURVEYED_OTHER':'Other*'}.get(v['region_id'],v['region_id'])
      rr.append([name,*[f(100*v[k]) for k in ['demand_weight','response_reachable_area_fraction','service_completion_fraction']],
                 f(v['allocated_monitoring_person_hours']),f(v['drone_flight_hours'])])
    blocks['TAB_REGIONS']=table('tab:regions','Regional demand and the representative base allocation.',
      ['Region',r'Demand (\%)',r'Reach (\%)',r'Service (\%)','Labor (h)','Flight (h)'],rr,
      note='* Animal values unknown. Regional labor excludes shared readiness. Small positive values below reporting precision are marked $<0.01$.')
    cmp=[]
    for label,key in [('Base','comparisons'),(r'Personnel budget -40\%','scarce_budget_comparisons')]:
      v=q2[key];cmp.append([label,f(v[-1]['result']['human_budget'],0),*[f(z['result']['score']) for z in v]])
    blocks['TAB_COMPARISON']=table('tab:comparison','Scores under equal budgets and service rules.',
      ['Budget','Labor limit','Uniform','Demand-based','Optimized'],cmp)
    forward=[['Original six posts',f(base['response_reserved_hours'],0),f(base['score']),f(base['total_person_hours']),f(base['drone_flight_hours'])]]
    for z in q2['forward_post_options']:
      v=z['result'];forward.append([z['target_region']+' added',f(v['response_reserved_hours'],0),f(v['score']),f(v['total_person_hours']),f(v['drone_flight_hours'])])
    blocks['TAB_FORWARD']=table('tab:forward','Additional-post candidates within the base total budgets.',
      ['Layout','Readiness (h)','Score','Total labor (h)','Flight (h)'],forward)
    blocks['TAB_SEASON_RULES']=table('tab:season','Medium service rules by month.',
      ['Months','Water visits/point','Extra fire checks$^*$'],[
        ['Jan--Apr, Dec','2','0'],['May--Jul','4','2'],['Aug--Oct','4','4'],['Nov','2','4']],
      note='$^*$Checks per 100 km$^2$ of burnable habitat per month; on-site maintenance is 0.5 hour/visit in normal months.')
    blocks['TAB_WATER_RULES']=table('tab:water','Historical-sample maintenance scenarios.',
      ['Rule','Visits/point','On-site hours','Monthly labor'],[
        ['Wet regular','2','0.5',f(wet['water_hours'])],['Dry regular','4','0.5',f(peak['water_hours'])],
        ['Drought pressure','8','1.0',f(drought['peak_water_hours'])]])
    mr=[]
    for label,index in [('Jan--Apr, Dec',0),('May--Jul',4),('Aug--Oct',7),('Nov',10)]:
      v=months[index];mr.append([label,f(v['required_person_hours']),str(v['required_staff']),f(v['flight_hours']),f(v['fixed_reference_score'])])
    blocks['TAB_MONTHLY']=table('tab:monthly','Minimum work and workforce for the medium service target.',
      ['Months','Personnel-hours','People','Flight-hours','177-person score'],mr)
    sr=[]
    for scenario,label in [('low','Low'),('base','Medium'),('high','High')]:
      normal=next(v for v in q3['sensitivity'] if v['scenario']==scenario and not v['abnormal_drought'])
      pressure=next(v for v in q3['sensitivity'] if v['scenario']==scenario and v['abnormal_drought'])
      sr.append([label,str(normal['annual_fixed_staff']),f(normal['peak_person_hours']),str(pressure['annual_fixed_staff']),f(pressure['peak_person_hours'])])
    blocks['TAB_SERVICE_STANDARDS']=table('tab:standards','Workforce under different assumed service rules.',
      ['Rule','Normal people','Normal hours','Drought people','Drought hours'],sr)
    blocks['TAB_LIMITATIONS']=table('tab:limits','Limits that affect interpretation and deployment.',['Limit','Consequence and data needed'],[
      ['Historical / missing objects','Current priority-species locations and surveys are needed; six measured groups do not certify all wildlife.'],
      ['Service proxies and assumptions','Calibrate check frequency, category priorities, fire exposure and ground/drone checklist equivalence.'],
      ['Maps and permissions','Verify roads, barriers, seasons and emergency access; a mapped route is not confirmed permission.'],
      ['Monthly pooled work','Check dates, qualifications, integer visits and concurrent incidents before calling a roster feasible.'],
      ['Incomplete maintenance inventory','Update borehole status, tasks and repair duration; the 17-point sample cannot define all current work.'],
      ['Service versus ecological outcomes','Validate loss, habitat and population outcomes independently; optimal service does not prove adequate protection.'],
    ],'p{4.0cm}X')
    parks=q6['parks'];c,y=parks['chitwan'],parks['yellowstone']
    blocks['TAB_TRANSFER_DATA']=table('tab:transferdata','Spatial trial inputs; Chitwan polygon remains uncalibrated.',
      ['Input','Chitwan polygon','Yellowstone NPS'],[
        ['Land service area (km$^2$)',f(c['land_area_km2']),f(y['land_area_km2'])],
        [r'Forest share (\%)',f(c['forest_share']*100),f(y['forest_share']*100)],
        ['Mapped park roads (km)',f(c['road_metadata']['in_park_road_km']),f(y['road_metadata']['in_park_road_km'])],
        ['Units / grid side',str(c['cell_count'])+' / 1 km',str(y['cell_count'])+' / 2.5 km'],
      ])
    tr=[]
    settings={'0':'Two posts, 30 km/h','1':'20 km/h','2':'Third post added','3':'40 km/h'}
    for z in q6['cases']:
      v=z['solution'];tr.append([z['id'],settings[z['id'][1]],f(z['geographic_cap']),f(z['target_score']),f(v['total_person_hours']) if v else 'Infeasible',str(v['staff_integer']) if v else '--'])
    blocks['TAB_TRANSFER_CASES']=table('tab:transfercases','Conditional land-inspection trials; not actual park staffing.',
      ['Case','Setting','Ceiling','Target','Labor (h)','People'],tr)
    figs=[('FIG_PIPELINE','fig1_framework_pipeline','fig:workflow','How priorities and task work connect to deployment and workforce.'),
      ('FIG_ETOSHA','fig2_etosha_demand_response','fig:etosha','Etosha demand and base area service; stars are candidate posts, red dots fail the response rule.'),
      ('FIG_COSTS','fig3_route_costs','fig:costs',r'Personnel work per check at ENP1\_0000; drone flight time is a separate resource.'),
      ('FIG_MONTHLY','fig4_monthly_workload','fig:monthly','Medium-rule monthly workload and personnel equivalents; reference availability is 177 people.'),
      ('FIG_JOINT','fig5_resource_joint','fig:joint','Peak-month service under joint personnel and flight limits; each cell is reoptimized.'),
      ('FIG_TRANSFER','fig6_transfer_maps','fig:transfer','Published spatial inputs and candidate locations; Chitwan boundary consistency remains unresolved.')]
    for token,name,label,caption in figs:blocks[token]=figure(name,label,caption)
    bibliography=[r'\section*{References}',r'\addcontentsline{toc}{section}{References}',r'\begin{enumerate}',r'\setlength{\itemsep}{2pt}\setlength{\parskip}{0pt}']
    # Numeric citations use thebibliography, preserving a single References heading.
    bibliography=[r'\begingroup',r'\titleformat{\section}{\fontsize{22}{33}\selectfont}{\thesection.}{0.6em}{}',r'\begin{thebibliography}{99}',r'\addcontentsline{toc}{section}{References}',r'\raggedright\setlength{\itemsep}{2pt}\setlength{\parskip}{0pt}']
    for key,text,url in REFERENCES:
      bibliography.append(r'\bibitem{'+key+'} '+text+(r' \href{'+url+r'}{Online source.}' if url else ''))
    bibliography += [r'\end{thebibliography}',r'\endgroup']
    blocks['REFERENCES']='\n'.join(bibliography)
    body=BODY
    for key,value in values.items():body=body.replace('@'+key+'@',value)
    for key,value in blocks.items():body=body.replace('@'+key+'@',value)
    unresolved=re.findall(r'@[A-Z_]+@',body)
    assert not unresolved,unresolved
    assert body.count(r'\clearpage')==23
    tex=PREAMBLE+body+'\n\\end{document}\n'
    OUT.mkdir(parents=True,exist_ok=True)
    source=PAPER/'full_paper.tex';source.write_text(tex,encoding='utf-8')
    sources=['output/question2/q2_results.json','output/question2/q2_model_inputs.json','output/question3/q3_results.json',
      'output/question4/q4_results.json','output/question4/q4_independent_verification.json','output/question6/q6_results.json']
    manifest={'status':'written_compilation_pending','language':'English','team_control_number':'510105201001220151',
      'source':'docs/paper/full_paper.tex','planned_total_pages':24,'letter_pages_planned':[21,22],
      'references_and_AI_included_in_page_limit':True,'body_font_points':12,'heading_font_points':22,'subheading_font_points':16,'title_font_points':14,'caption_font_points':10,'symbol_table_font_points':11,'margin_cm':1.5,'side_margin_points':1.5/2.54*72,'vertical_margin_points':1.5/2.54*72,'figures':6,
      'bibliography_entries':len(REFERENCES),
      'tables':body.count(r'\begin{table}'),'numbered_equations':body.count(r'\begin{equation}'),
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'input_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
      'contents':['summary','contents','study design and terms','questions 1--6','two-page nontechnical letter','references','AI-use report'],
      'scope_limits':['Q2 excludes water/rainfall; Q3 water work separate','Q6 Chitwan boundary fails area calibration','workforce equivalents are conditional monthly task estimates']}
    (OUT/'full_paper_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ['status','language','planned_total_pages','figures','tables','numbered_equations']},ensure_ascii=False))


if __name__=='__main__':main()
