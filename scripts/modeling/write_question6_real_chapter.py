"""Write six-page Q6 from saved real spatial results; synchronise LaTeX/Markdown.

The template controls prose and page breaks. Model results are not recomputed.
"""
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[2];PAPER=ROOT/'docs/paper';OUT=ROOT/'output/question6';FIG=OUT/'paper_figures'

def figure(name,caption,label):
 return '\n'.join([r'\begin{figure}[htbp]',r'\centering',r'\resizebox{\linewidth}{!}{%',(FIG/(name+'.tikz')).read_text(encoding='utf8').strip(),'}','\\caption{'+caption+'}','\\label{'+label+'}',r'\end{figure}'])
def table(caption,label,headers,rows,fmt):
 return '\n'.join([r'\begin{table}[htbp]',r'\centering','\\caption{'+caption+'}','\\label{'+label+'}',r'\begin{tabularx}{\linewidth}{'+fmt+'}',r'\toprule',' & '.join(headers)+r'\\',r'\midrule',*[' & '.join(map(str,row))+r'\\' for row in rows],r'\bottomrule',r'\end{tabularx}',r'\end{table}'])

TEX=Path(__file__).with_name('question6_compact_template.tex').read_text(encoding='utf8')

LINKS={'chitwan':('UNESCO','https://whc.unesco.org/en/list/284'),'cnpplan':('历史管理计划','https://faolex.fao.org/docs/pdf/nep220147.pdf'),'cnparea':('DNPWC报告','https://dnpwc.gov.np/media/files/UNESCO_Report_of_Chitwan_National_Park.pdf'),'osm':('OSM/Geofabrik','https://download.geofabrik.de/asia/nepal.html'),'worldcover':('ESA WorldCover','https://esa-worldcover.org/en/data-access'),'npsboundary':('NPS边界','https://irma.nps.gov/DataStore/Reference/Profile/2316784'),'npsroads':('NPS道路','https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer/0'),'npspois':('NPS位置点','https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_POIs_Geographic/FeatureServer/0'),'visitor':('NPS游客管理','https://www.nps.gov/yell/learn/management/visitor-use.htm'),'conditions':('NPS通行条件','https://www.nps.gov/yell/planyourvisit/conditions.htm'),'rules':('NPS规则','https://www.nps.gov/yell/learn/management/lawsandpolicies.htm')}
LINKS['wdpca']=('WDPCA2026-10','https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer/1')
LINKS['gis2020']=('DNPWC2020 GIS报告','https://giwmscdntwo.gov.np/media/pages/files/Final%20Report_GIS%20Database_v4olikj.pdf')
LINKS['wolf']=('NPS2022狼群历史GIS','https://www.nps.gov/yell/learn/nature/upload/1995_2022-YELL-wolf-data.zip')
def markdown(tex):
 body=tex.split(r'\section{保护资源配置模型的跨大陆适配}',1)[1].split(r'\FloatBarrier')[0]
 names=['fig1_adaptation_flow','fig2_real_maps','fig3_real_results'];i=[0];ti=[0]
 def fig(m):
  n=names[i[0]];i[0]+=1;cap=re.search(r'\\caption\{([^\n]+)\}',m.group()).group(1)
  return f'\n![{cap}](../../output/question6/paper_figures/{n}.png)\n\n图6-{i[0]} {cap}\n'
 def tab(m):
  ti[0]+=1;cap=re.search(r'\\caption\{([^\n]+)\}',m.group()).group(1);s=m.group().split(r'\toprule')[1].split(r'\bottomrule')[0].replace(r'\midrule','')
  rows=[[x.strip() for x in row.split('&')] for row in s.split(r'\\') if '&' in row]
  return '\n表6-'+str(ti[0])+' '+cap+'\n\n'+'\n'.join(['| '+' | '.join(rows[0])+' |','| '+' | '.join(['---']*len(rows[0]))+' |']+['| '+' | '.join(row)+' |' for row in rows[1:]])+'\n'
 body=re.sub(r'\\begin\{figure\}.*?\\end\{figure\}',fig,body,flags=re.S);body=re.sub(r'\\begin\{table\}.*?\\end\{table\}',tab,body,flags=re.S)
 refs={'eq:q6score':'（6-1）','eq:q6response':'（6-2）','eq:q6cost':'（6-3）','eq:q6constraints':'（6-4）','eq:q6staff':'（6-5）','eq:q6cap':'（6-6）','fig:q6flow':'6-1','fig:q6network':'6-2','fig:q6results':'6-3','tab:q6params':'6-1','tab:q6data':'6-2','tab:q6geo':'6-3','tab:q6results':'6-4'}
 body=re.sub(r'\\(?:eqref|ref)\{([^}]+)\}',lambda m:refs[m[1]],body)
 body=re.sub(r'\\cite\{([^}]+)\}',lambda m:'（'+'、'.join(f'[{LINKS[k][0]}]({LINKS[k][1]})' for k in m[1].split(','))+'）',body)
 body=re.sub(r'\\subsubsection\{([^}]+)\}',r'### \1',body);body=re.sub(r'\\subsection\{([^}]+)\}',r'## \1',body)
 body=re.sub(r'\\label\{[^}]+\}','',body).replace(r'\%','%')
 body=re.sub(r'\\textbf\{([^}]+)\}',r'**\1**',body)
 body=body.replace(r'\clearpage','').replace(r'\newpage','')
 body=body.replace(r'\begin{equation}',r'\[').replace(r'\end{equation}',r'\]').replace(r'\begin{align}',r'\[\begin{aligned}').replace(r'\end{align}',r'\end{aligned}\]')
 return '# 6 保护资源配置模型的跨大陆适配\n\n'+body.strip()+'\n\n复现及证据见[第六题计算说明](../modeling_notes/question6_calculation_notes.md)。\n'

def main():
 r=json.loads((OUT/'q6_results.json').read_text(encoding='utf8'));c=r['parks']['chitwan'];y=r['parks']['yellowstone'];cases={z['id']:z for z in r['cases']};v=r['grid_verification'];checks=json.loads((OUT/'q6_verification.json').read_text(encoding='utf8'))
 replacements={'CAREA':f"{c['polygon_area_km2']:.2f}",'CADIFF':f"{100*abs(c['polygon_area_km2']/952.63-1):.2f}",'CFOREST':f"{100*c['forest_share']:.2f}",'COPEN':f"{100*c['open_share']:.2f}",'YFOREST':f"{100*y['forest_share']:.2f}",'YWATER':f"{100*y['water_share']:.2f}",'YROAD':f"{y['road_metadata']['in_park_road_km']:.2f}",'CGDIFF':f"{v['chitwan']['cap_difference_pp']:+.2f}",'YGDIFF':f"{v['yellowstone']['cap_difference_pp']:+.2f}",'CFINEH':f"{v['chitwan']['fine_solution']['total_person_hours']:.2f}" if v['chitwan']['fine_solution'] else '目标不可达','YFINEH':f"{v['yellowstone']['fine_solution']['total_person_hours']:.2f}" if v['yellowstone']['fine_solution'] else '目标不可达','CRDIFF':f"{c['landcover_resolution_check']['forest_difference_pp']:+.3f}",'YRDIFF':f"{y['landcover_resolution_check']['forest_difference_pp']:+.3f}",'CHECKCOUNT':str(len(checks['checks']))}
 replacements['FIG1']=figure('fig1_adaptation_flow','真实数据、情景参数与当地校准的迁移关系','fig:q6flow')
 replacements['FIG2']=figure('fig2_real_maps','发布边界、道路与候选位置；绿色表示模型内可响应。奇特旺范围待校准，黄石使用NPS公开资料','fig:q6network')
 replacements['FIG3']=figure('fig3_real_results','真实路网下的速度与驻点情景；人时及人员当量受所设作业协议约束','fig:q6results')
 replacements['PARAMTABLE']=table('初步验证的作业假设；均不宣称当地实测标准','tab:q6params',['参数','设定','用途'],[['有效工时','120小时/人/月','与第三题一致'],['车速、步速','30、4 km/h','车辆情景另设20、40 km/h'],['派遣、观察、准备','10、10、5分钟','进入响应和检查成本'],['小队与服务密度','2人；8次/100平方千米/月','面积服务协议'],['响应与服务底线',r'2小时；15\%','与原模型结构一致'],['响应点预留','480人时/点/月','比较驻点固定工作量'],['无人机预算','0小时','授权及等效性未校准']],r'p{.2\linewidth}p{.36\linewidth}X')
 replacements['DATATABLE']=table('真实数据来源及正式部署需补充的校准数据','tab:q6data',['项目','奇特旺','黄石'],[['边界与道路','WDPCA2026-10多边形；OSM2026-10-04道路。边界一致性未通过','NPS边界、公开道路；需补护林作业道路'],['候选位置','Kasara、Sauraha、Amaltari具名地理参考，设施待核定','Norris、Lake、South Entrance护林站位置'],['生境分类','ESA WorldCover2021v200','ESA WorldCover2021v200'],['对象与需求校准','重点物种位置、调查努力、社区冲突与巡护日志','动物调查、游客分时暴露与事件处置日志'],['通行与技术校准','季风封路、河流通行、速度与技术试验','季节管理通行、坡度、工具可用性及授权']],r'p{.18\linewidth}XX')
 geo=[]
 for title,key,fmt in [('向量面积（平方千米）','polygon_area_km2','area'),('陆域服务面积（平方千米）','land_area_km2','area'),(r'林地占比（\%）','forest_share','percent'),(r'草地、灌丛、裸地（\%）','open_share','percent'),(r'永久水体（\%）','water_share','percent')]:geo.append([title,*[f"{p[key]*(100 if fmt=='percent' else 1):.2f}" for p in [c,y]]])
 geo.append(['园内使用道路（千米）',f"{c['road_metadata']['in_park_road_km']:.2f}",f"{y['road_metadata']['in_park_road_km']:.2f}"])
 geo.append(['服务网格数量',str(c['cell_count']),str(y['cell_count'])])
 replacements['GEOTABLE']=table('所用数据多边形的空间统计；奇特旺范围待校准，土地覆盖为100米采样估计','tab:q6geo',['指标','奇特旺发布范围','黄石NPS范围'],geo,'Xrr')
 rows=[]
 for z in r['cases']:
  s=z['solution'];rows.append([z['id'],z['label'],f"{z['geographic_cap']:.2f}",f"{z['target_score']:.2f}",f"{s['total_person_hours']:.2f}" if s else '不可达',str(s['staff_integer']) if s else '--'])
 replacements['RESULTTABLE']=table('真实空间资料下的条件试算；C类为待校准发布范围，人数均为所设服务的条件当量','tab:q6results',['情景','设置',r'上限（\%）','固定目标','人时','人数当量'],rows,'cXrrrr')
 prose=[]
 for park,prefix in [('chitwan','C'),('yellowstone','Y')]:
  a,b,d=cases[prefix+'0'],cases[prefix+'1'],cases[prefix+'2'];s=a['solution'];ss=d['solution']
  pressure=(f"达到同一目标所需人时为{b['solution']['total_person_hours']:.2f}" if b['solution'] else '低于固定目标，使该目标在当前模型内不可达')
  prose.append(f"{r['parks'][park]['label']}基准条件响应上限为{a['geographic_cap']:.2f}\\%，固定目标为{a['target_score']:.2f}分，对应{s['total_person_hours']:.2f}人时。车速降至20 km/h时，上限变为{b['geographic_cap']:.2f}\\%；{pressure}。增加第三处候选驻点后，上限变为{d['geographic_cap']:.2f}\\%，达到相同目标所需人时为{ss['total_person_hours']:.2f}。")
 replacements['RESULTPROSE']='\n\n'.join(prose)
 for case_id,case in cases.items():
  if case['solution']:
   replacements[case_id+'H']=f"{case['solution']['total_person_hours']:.2f}"
   replacements[case_id+'N']=str(case['solution']['staff_integer'])
 tex=TEX
 for k,value in replacements.items():tex=tex.replace('@@'+k+'@@',value)
 assert '@@' not in tex
 (PAPER/'question6_adaptation.tex').write_text(tex,encoding='utf8');(PAPER/'question6_adaptation.md').write_text(markdown(tex),encoding='utf8')
 manifest=dict(source='docs/paper/question6_adaptation.tex',template='scripts/modeling/question6_compact_template.tex',source_sha256=hashlib.sha256(tex.encode()).hexdigest(),results_sha256=hashlib.sha256((OUT/'q6_results.json').read_bytes()).hexdigest(),equations=6,figures=3,tables=4,figure_geometry_embedded=True,page_target=6,status='real spatial inputs; assumptions distinguished; see q6_latex_verification for compilation')
 (OUT/'q6_chapter_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Formal Q6 rewritten from real spatial calculations.')
if __name__=='__main__':main()
