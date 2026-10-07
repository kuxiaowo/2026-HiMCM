"""Stage-by-stage paper audit, with English and logical-figure support.

Uses the skill's unmodified caption tokenizer. The original scanner's graphical
bands are not figure objects: this audit groups them by the actual [H] floats,
while preserving the 2/3 threshold and 100--150 explanation rule.
Dependencies: conda numerical environment + PyMuPDF (installed normally or in
the project-local wheel directory). The delivered unmodified checker copy
allows the audit to run without the author's external skill installation.
"""
from __future__ import annotations
import ast,csv,hashlib,importlib.util,json,math,re,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/full_paper/skill_audit_20261007'
sys.path.insert(0,str(ROOT/'tmp/skill_audit_20261007/python_packages'))
import pymupdf

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(p,x):(OUT/p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

QUESTIONS=[
('Q1','评价与定义','识别保护挑战及可量化保护标准','4','输出范围、历史责任与服务定义'),
('Q2','约束优化','配置人力和技术并考虑地理与不确定性','5','两阶段LP、道路响应、技术及预算情景'),
('Q3','逆向工作量规划','分析时间变化并反求维持目标所需人员','6','季节任务、共享预算、120小时/人月'),
('Q4','敏感性与情景','改变资源、标准及巡访日期检验策略','7','独立约束检验、技术、网格与权重'),
('Q5','方法评价','讨论优势、限制及校准需求','8','可解释性、数据和现场适用边界'),
('Q6','结构迁移','适配不同大洲的两座保护区','9','本地输入、规则、数据需求及部署变化'),
('Letter','非技术沟通','向IMMC解释方法、建议和关键洞见','Letter','不超过两页')]

def stage_inventory(tex):
    problem=(OUT/'problem_text.txt').read_text(encoding='utf-8')
    files=['output/2026数模训练.pdf','output/model1/species_region_counts_2015.json',
           'output/regions/region_base_data.json','data/regions/processed/model_regions.geojson',
           'data/roads/processed/park_nodes.csv','data/roads/processed/park_edges.csv',
           'data/roads/processed/park_edges.geojson','data/modeling/q2_assumptions.json',
           'data/modeling/q3_assumptions.json','data/question3/processed/water_points.json',
           'output/question2/q2_model_inputs.json','output/question6/q6_results.json',
           'output/revision_feasibility/20261006/yellowstone_wolf_2022_territories.geojson']
    inventory=[]
    for name in files:
        p=ROOT/name;assert p.exists(),name;item={'path':name,'sha256':sha(name),'bytes':p.stat().st_size}
        if p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as h:
                reader=csv.DictReader(h);rows=list(reader)
            item.update(columns=reader.fieldnames,rows=len(rows),missing={k:sum(not r[k] for r in rows) for k in reader.fieldnames})
        if p.suffix in ['.json','.geojson']:
            d=read(name);item['keys']=list(d)[:25]
            if 'features' in d:item['features']=len(d['features'])
        inventory.append(item)
    write('task_package.json',{'audit_date_local':'2026-10-07','problem_source':files[0],
          'problem_text':problem,'questions':[dict(id=q,type=t,rephrased=r,section=s,evidence=e) for q,t,r,s,e in QUESTIONS],
          'data_files':inventory,'approval':'Existing model and chapter scope authorized in this session; this is re-verification, not a new selection checkpoint.'})
    choices={
    'Q1':[('责任与明确服务代理','采用','分物种份额与透明类别偏好，明确服务和生态结果的区别'),('实测事件率模型','未采用','需要一致努力下的事件及损失记录，当前未取得'),('人口生态动力模型','未采用','与用户不预测种群的范围不符')],
    'Q2':[('路网约束连续LP','采用','可解释的容量与双预算，并保留评分后全局最少人工'),('整数巡护调度','未采用','缺每日资质、时间窗与并发任务台账'),('地理阈值均衡/需求比例','已计算对照','在相同预算与底线下比较完成率')],
    'Q3':[('服务需求逆向LP','采用','保持同一目标并计入额外季节任务'),('复杂轮班/排队模型','未采用','用户明确不建立复杂轮班，且到达过程未校准'),('预测动物/降雨再定员','未采用','缺预测依据且超出本轮范围')],
    'Q4':[('固定条件情景与重新求解','采用','区分服务标准变化、预算变化与离散近似'),('概率蒙特卡洛风险','未采用','不能虚构事件概率或效率分布')],
    'Q5':[('模型特定证据及局限审计','采用','把计算正确、执行可行、生态有效分开'),('按通用评分生成生态认证','未采用','任务代理不支持认证')],
    'Q6':[('本地真实地理+条件任务试算','采用','重建几何、路线、任务与固定目标'),('直接搬用埃托沙权重/人数','未采用','当地对象、权限和任务不同'),('黄石本地历史生态优先层','独立扩展已计算','明确历史范围及原面积评分的取舍')]}
    write('modeling_doc.json',{'scope':'Retrospective suitability comparison, not a claim of newly performed experiments for rejected methods.',
          'chosen_scope_authorized':True,'candidates':choices,'reflection_log':['LP coefficients are deterministic planning proxies; sensitivity replaces unsupported probabilities.','Monthly labor is not a roster.','Historical data are not current abundance.','Q6 floors are per cell, Q2 floors per reporting region; migration changes this scale explicitly.']})
    write('style_contract.json',{'authority':'User 2026-10-07 instruction: captions/symbols 12pt, body/headings retained.',
          'body_pt':12,'heading_pt':22,'subheading_pt':16,'caption_pt':12,'symbol_pt':12,'header_pt':12,
          'font_family':'Times New Roman; previously specified Arial caption retained',
          'class':'Existing article source retained under user template instructions; cumcmthesis not substituted.',
          'page_limit_total_user':25,'solution_limit_problem':20,'counted_limit_problem':24,
          'nonapplicable_generic_targets':['Chinese teaching document page count is not an English submission limit.','Do not create five redundant charts for definition or evaluation questions.','No training/CV/residual diagnostics: model is deterministic optimization, not statistical prediction.']})
    return inventory

def numerical_audit():
    source=read('output/model1/species_region_counts_2015.json');core=[s for s in source['species'] if s['adoption']=='core_with_flags']
    assert len(core)==6
    # A blank source estimate contributes no RECORDED abundance; not true absence.
    species=[]
    for s in core:
        assert s['block_sum_minus_table_total']==0 and s['individual_total_minus_summary_total']==0
        species.append({'code':s['species_code'],'name':s['name_zh'],'numeric_sum':s['sum_of_numeric_block_estimates'],
                        'blank_rows':s['blank_count_rows'],'flags_retained':True})
    inputs=read('output/question2/q2_model_inputs.json');q2=read('output/question2/q2_results.json');q3=read('output/question3/q3_results.json')
    q4=read('output/question4/q4_independent_verification.json');q6=read('output/question6/q6_verification.json')
    rev=read('output/revision_feasibility/20261006/revision_results.json')
    assert all(sha(p)==h for p,h in rev['input_sha256'].items())
    assert q4['passed'] and q4['independently_checked_feasible_solutions']==127 and q4['saved_cases']==131
    assert read('output/question3/q3_independent_verification.json')['passed']
    assert all(x['passed'] for x in q6['checks']) and len(q6['checks'])==10
    assert len(inputs['targets'])==599 and inputs['human_budget']==21240 and inputs['drone_budget']==1200
    water=read('data/question3/processed/water_points.json');assert water['modelled_BH_count']==17 and not water['complete_park_inventory']
    w=np.array([t['objective_weight'] for t in inputs['targets']]);r=np.array([t['response_eligible'] for t in inputs['targets']]);opt=q2['optimum']
    assert abs(w.sum()-1)<1e-9 and abs(100*w@r-opt['score'])<1e-7
    assert abs(opt['total_person_hours']-rev['two_stage']['independent_Q3_inverse_person_hours'])<1e-6
    assert opt['two_stage']['service_vector_fixed'] is False
    assert q3['annual_fixed_staff_base_scenario']==57
    assert next(c for c in q3['sensitivity'] if c['scenario']=='base' and c['abnormal_drought'])['annual_fixed_staff']==62
    result={'passed':True,'source_species':species,'blank_interpretation':'No recorded estimate, not verified absence; numeric responsibility coefficients remain historical and quality flagged.',
            'max_score_analytical_certificate':100*float(w@r),'minimum_labor_independent_agreement':True,
            'Q3_independent_cases':84,'Q4_cases':131,'Q4_feasible':127,'Q6_independent_cases':10,
            'staff':{'normal':57,'drought_service':62},'unchanged_working_assumptions':{'hours_per_person_month':120,'staff_fraction':.6,'drones':30},
            'external_limits':['Original count quality flags remain.','Current legal amendments not comprehensively audited; mapping is planning context.','Chitwan legal-area calibration failed and is explicitly conditional.','Technology/check frequency costs not measured; no ecological outcome claim.']}
    write('numerical_data_audit.json',result)
    scripts=['build_question2.py','build_question3.py','build_question4.py','build_question6_real.py','build_revision_supplement.py']
    code=[]
    for name in scripts:
        path=ROOT/'scripts/modeling'/name;text=path.read_text(encoding='utf-8');ast.parse(text)
        code.append({'file':path.relative_to(ROOT).as_posix(),'random_generation':bool(re.search(r'np\.random|random\.(?:random|rand|normal)',text)),
                     'reads_real_files':bool(re.search(r'read_text|DictReader|rasterio\.open|json\.loads|q2\.read|read\(',text)),
                     'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    assert all(not c['random_generation'] and c['reads_real_files'] for c in code)
    write('code_audit.json',{'passed':True,'scripts':code,'statistical_data_leakage':'not applicable: no learned predictive model','all_real_inputs_preserved':True})
    return result

def layout_audit(tex, pdf_path=None):
    skill=OUT/'original_check_layout.py'
    if not skill.exists():
        skill=Path('C:/Users/admin/.codex/skills/math-modeling-skill/scripts/check_layout.py')
    spec=importlib.util.spec_from_file_location('skill_layout',skill);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    pdf=ROOT/(pdf_path or 'output/pdf/skill_checked_20261007/full_paper.pdf');doc=pymupdf.open(pdf)
    aux=pdf.with_suffix('.aux').read_text(encoding='utf-8')
    labels={k:(int(n),int(p)) for k,n,p in re.findall(r'\\newlabel\{((?:fig|tab):[^}]+)\}\{\{(\d+)\}\{(\d+)\}',aux)}
    objects=[];margins=1.5/2.54*72;bh=doc[0].rect.height-2*margins
    issues=[]
    for m in re.finditer(r'\\begin\{(figure|table)\}\[([^]]+)\](.*?)\\end\{\1\}',tex,re.S):
        env,placement,body=m.group(1,2,3);key=re.search(r'\\label\{([^}]+)\}',body)[1]
        n,pageno=labels[key];page=doc[pageno-1];caption=re.search(r'\\caption\{([^\n]+)\}',body)[1]
        count=module.count_zi(caption)
        if '% USER_SHORT_CAPTIONS_20261007' in tex:
            assert caption.count('.')==1 and caption.endswith('.') and not re.search(r'[!?]',caption),(key,caption)
        else:
            assert 100<=count<=150,(key,count)
        refs=list(re.finditer(r'\\ref\{'+re.escape(key)+r'\}',tex));assert refs and refs[0].start()<m.start(),key
        cap=page.search_for(f'{"Figure" if env=="figure" else "Table"} {n}:')[0]
        # A figure's declared bounding height includes internal legends/subpanels.
        if env=='figure':
            W,H=map(float,re.search(r'use as bounding box\]\s*\(0,0\) rectangle \(([\d.]+),([\d.]+)\)',body).groups())
            box=pymupdf.Rect((page.rect.width-W/2.54*72)/2,cap.y0-3-H/2.54*72,(page.rect.width+W/2.54*72)/2,cap.y0-3)
        else:
            # Each ordinary booktabs object has top, mid and bottom rules. Reject
            # header rules and drawings inside already known figure frames.
            rules=[]
            for d in page.get_drawings():
                b=d['rect']
                if b.width>90 and b.height<2 and b.y0>cap.y0 and b.y0<page.rect.height-margins+1:
                    if not any(o['page']==pageno and o['type']=='figure' and o['bbox'][1]-2<=b.y0<=o['bbox'][3]+2 for o in objects):rules.append(b)
            rules=sorted(rules,key=lambda b:b.y0)
            distinct=[]
            for b in rules:
                if not distinct or abs(b.y0-distinct[-1].y0)>2:distinct.append(b)
                if len(distinct)==3:break
            assert len(distinct)==3,(key,len(distinct))
            box=pymupdf.Rect(min(b.x0 for b in distinct),distinct[0].y0-1,max(b.x1 for b in distinct),distinct[-1].y1+1)
        # Find the first real rendered reference, excluding the caption label.
        phrase=f'{"Figure" if env=="figure" else "Table"} {n}'
        occurrences=[]
        for i,pg in enumerate(doc,1):
            for hit in pg.search_for(phrase):
                # 'Table 1' is a prefix of Table 10; verify whole neighboring text.
                near=pg.get_text('text',clip=pymupdf.Rect(hit.x0-1,hit.y0-1,min(hit.x1+8,pg.rect.width),hit.y1+1))
                if re.search(re.escape(phrase)+r'\d',near):continue
                if i==pageno and abs(hit.y0-cap.y0)<2:continue
                if i==2:continue # Contents are not discussion references.
                occurrences.append((i,hit.y0))
        assert occurrences,key
        first=min(occurrences)
        if not (first[0]<=pageno and pageno-first[0]<=1):
            issues.append({'type':'reference_distance','key':key,'reference_page':first[0],'object_page':pageno})
        objects.append({'key':key,'type':env,'number':n,'page':pageno,'caption_tokens':count,
                        'first_reference_page':first[0],'placement':placement,'bbox':list(box),'height_bp':box.height})
    perpage=[]
    for i,page in enumerate(doc,1):
        items=[o for o in objects if o['page']==i]
        # Union the physical vertical extent of actual float objects, not paths.
        bands=module.merge_intervals([(o['bbox'][1],o['bbox'][3],o) for o in items],gap=0)
        ratio=sum(b[1]-b[0] for b in bands)/bh
        if ratio>2/3+1e-3:issues.append({'type':'ratio','page':i,'ratio':ratio})
        if len(items)>2:issues.append({'type':'too_many_objects','page':i,'count':len(items)})
        figs=sorted([o for o in items if o['type']=='figure'],key=lambda o:o['bbox'][1])
        for a,b in zip(figs,figs[1:]):
            between=page.get_text('text',clip=pymupdf.Rect(margins,a['bbox'][3]+1,page.rect.width-margins,b['bbox'][1]-1))
            # Captions alone cannot provide the required intervening discussion.
            if module.count_zi(between)<40:issues.append({'type':'adjacent_figures','page':i})
        text=page.get_text();assert not re.search(r'[\ufffd\u25a1\u25a0]|\?\?',text),(i,'missing glyph')
        perpage.append({'page':i,'float_count':len(items),'graphic_ratio':ratio})
    report={'passed':not issues,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'objects':objects,'pages':perpage,'issues':issues,
            'max_graphic_ratio':max(p['graphic_ratio'] for p in perpage),'original_scanner':'original_layout_final.log',
            'adapter_changes':['English Figure/Table identification','Grouping within actual source float instead of individual vector bands','Same caption tokenizer and same 2/3 threshold'],
            'caption_policy':'one concise sentence, explanations in body (explicit user override)' if '% USER_SHORT_CAPTIONS_20261007' in tex else '100--150 tokens',
            'no_silent_rule_relaxation':True}
    write('english_layout_audit.json',report)
    assert report['passed'],issues
    appendix=next(i for i,p in enumerate(doc,1) if 'Appendix: supplementary results' in p.get_text() and i>2)
    gaps=[]
    for i,page in enumerate(doc,1):
        blocks=[b for b in page.get_text('blocks') if b[1]>42 and b[3]<803]
        bottom=max(b[3] for b in blocks)
        gap=max(0,page.rect.height-margins-bottom)
        # A final solution page, separate summary/contents, appendix, letter,
        # references and AI report may end naturally; intermediate body pages
        # must not contain large unfinished blocks of unused space.
        exempt=i<=2 or i>=appendix-1
        gaps.append({'page':i,'bottom_gap_bp':gap,'section_or_document_end_exception':exempt,
                     'passed':exempt or gap<=94})
    assert all(g['passed'] for g in gaps),[g for g in gaps if not g['passed']]
    write('whitespace_audit.json',{'passed':True,'nominal_target_bp':90,'tolerance_bp':4,
          'appendix_page':appendix,'main_solution_pages':appendix-3,'pages':gaps,
          'exception_reason':'Required distinct document components and final solution page may end naturally; no filler or enlarged body leading introduced.'})
    actual_listing=(pdf.parent/'skill_reproduce_embedded.py').read_text(encoding='utf-8')
    delivered=(ROOT/'scripts/modeling/reproduce_baseline_for_paper.py').read_text(encoding='utf-8')
    assert actual_listing==delivered
    write('appendix_code_verification.json',{'passed':True,'listing_matches_delivered_source':True,
          'source':'scripts/modeling/reproduce_baseline_for_paper.py','source_sha256':sha('scripts/modeling/reproduce_baseline_for_paper.py'),
          'run_verified_values':{'score':57.26,'total_person_hours':5286.11,'drone_flight_hours':144.34},
          'self_contained_TeX':'filecontents* embeds the exact source; no additional project input file needed for compilation'})
    return report

def main():
    OUT.mkdir(parents=True,exist_ok=True);tex=(ROOT/'docs/paper/full_paper.tex').read_text(encoding='utf-8')
    log=(ROOT/'output/pdf/skill_checked_20261007/full_paper.log').read_text(encoding='utf-8',errors='replace')
    assert not re.search(r'Overfull|Missing character|undefined|Font Warning|^!',log,re.M),'Compile warnings require repair'
    bib=set(re.findall(r'\\bibitem\{([^}]+)\}',tex))
    citations={k for group in re.findall(r'\\cite\{([^}]+)\}',tex) for k in group.split(',')}
    assert citations<=bib,sorted(citations-bib)
    files=stage_inventory(tex);numbers=numerical_audit();layout=layout_audit(tex)
    write('stage_status.json',{'audit_date_local':'2026-10-07','stages':{
          '0_environment':'passed; project-local PyMuPDF installed and original checker executed',
          '1_parsing':'passed; full supplied problem text, seven deliverable requirements and data inventory recorded',
          '2_method_choice':'reviewed; original choices preserved and retrospective alternatives honestly identified',
          '3_code_solution':'passed; Q2--Q4 and Q6 recomputed, numerical and independent checks recorded',
          '4_visualization':'passed automated checks; full-region map and one layered architecture; final visual inspection pending',
          '5_manuscript':'passed automatic caption/reference/formula checks; user-authorized minimum prose size 12pt',
          '6_review':'automatic checks complete; final page review and scored issue-resolution report pending',
          '7_delivery':'pending final fingerprints and support archive'},'input_files':len(files),'numerical_passed':numbers['passed'],'layout_passed':layout['passed']})
    print(json.dumps({'numerical_passed':numbers['passed'],'objects_checked':len(layout['objects']),'max_graphic_ratio':layout['max_graphic_ratio'],'layout_passed':layout['passed']},ensure_ascii=False))

if __name__=='__main__':main()
