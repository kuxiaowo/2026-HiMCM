"""Write Q6 from saved REAL spatial calculations; synchronise LaTeX/Markdown."""
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[2];PAPER=ROOT/'docs/paper';OUT=ROOT/'output/question6';FIG=OUT/'paper_figures'

def figure(name,caption,label):
 return '\n'.join([r'\begin{figure}[htbp]',r'\centering',r'\resizebox{\linewidth}{!}{%',(FIG/(name+'.tikz')).read_text(encoding='utf8').strip(),'}','\\caption{'+caption+'}','\\label{'+label+'}',r'\end{figure}'])
def table(caption,label,headers,rows,fmt):
 return '\n'.join([r'\begin{table}[htbp]',r'\centering','\\caption{'+caption+'}','\\label{'+label+'}',r'\begin{tabularx}{\linewidth}{'+fmt+'}',r'\toprule',' & '.join(headers)+r'\\',r'\midrule',*[' & '.join(map(str,row))+r'\\' for row in rows],r'\bottomrule',r'\end{tabularx}',r'\end{table}'])

TEX=r'''\documentclass[UTF8,fontset=fandol,12pt,a4paper]{ctexart}
\usepackage[margin=2cm]{geometry}
\usepackage{amsmath,amssymb,booktabs,tabularx,array}
\usepackage{graphicx,xcolor,tikz,caption,placeins,hyperref}
\usetikzlibrary{arrows.meta}
\hypersetup{hidelinks}
\captionsetup{font=small,labelfont=bf,labelsep=quad}
\setcounter{secnumdepth}{3}\setcounter{section}{5}
\renewcommand{\theequation}{6-\arabic{equation}}
\renewcommand{\thefigure}{6-\arabic{figure}}
\renewcommand{\thetable}{6-\arabic{table}}
\allowdisplaybreaks
\setlength{\parskip}{0.25em}
\setlength{\textfloatsep}{10pt plus 2pt minus 2pt}
\setlength{\intextsep}{9pt plus 2pt minus 2pt}
\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.13}
\emergencystretch=2em
\title{第六部分：保护资源配置模型的跨大陆适配}\author{}\date{}
\begin{document}\maketitle\vspace{-1.5em}
\section{保护资源配置模型的跨大陆适配}

第二、三题以地理可达性、监测任务和人力预算建立保护资源配置模型。跨保护区应用需要保留这些关系，并重新建立当地对象、道路、技术权限和作业成本。本节选择亚洲的奇特旺国家公园与北美洲的黄石国家公园，使用真实边界、道路、位置点与遥感土地覆盖数据进行初步计算，再说明当地保护任务的接入方法。空间验证采用陆域生境服务子模型；速度、巡检协议及驻点配置明确设为情景参数，所得人员当量不作为两园实际编制。

\subsection{模型结构与迁移方法}
\subsubsection{共同结构与本地参数}

保留“保护需求—服务完成—地面响应—资源约束—人员反求”的逻辑。对保护区 \(p\)、空间单元 \(j\) 和时期 \(t\)，沿用地面检查人时 \(x_{jt}^{(p)}\)、无人机机时 \(h_{jt}^{(p)}\) 与服务完成率 \(s_{jt}^{(p)}\)，园内服务评分为
\begin{equation}
P_t^{(p)}=100\sum_jw_j^{(p)}s_{jt}^{(p)},\qquad \sum_jw_j^{(p)}=1.
\label{eq:q6score}
\end{equation}
\(w_j^{(p)}\) 必须随当地的物种、生境及任务重建。埃托沙的动物责任份额与熵权数值不能直接用于其他园区；不同公园的分数只描述各自任务协议的完成程度。将物种数量、冲突记录和游客暴露接入模型时，应记录它们的年份、范围和调查努力，再按同一空间单元汇总。调查覆盖不全的单元需要补测或保留不确定范围，不能赋予虚构的动物数量和风险权重。

本节已有可复算的土地覆盖数据，因此先以单元陆域面积 \(A_j^{\mathrm{land}}\) 定义 \(w_j=A_j^{\mathrm{land}}/\sum_kA_k^{\mathrm{land}}\)，并按相同面积服务密度建立任务量 \(C_j=fA_j^{\mathrm{land}}/100\)。这里的均匀服务密度是协议假设；土地覆盖面积来自真实栅格。该设置验证空间服务结构，尚未校准综合物种保护评分。图\ref{fig:q6flow}说明数据、假设和校准之间的关系。

@@FIG1@@

\subsubsection{可达性、技术与工作量的重建}

先按车辆、步行和技术权限建立当地通行图 \(G_t^{(p)}\)。真实道路几何决定路段长度，实测速度、道路状态与许可再决定边的时间成本。本次以映射道路的几何图计算最短路；奇特旺排除明确禁止机动车或私人进入的道路，黄石排除标为私人道路的记录。图按无向响应情景计算，尚未用当地应急通行权限校准方向。图中不会添加跨河或长距离的虚构连接，仅合并0.5米以内的制图端点差。

设驻点到单元代表位置的最短道路去程与返程时间为 \(T_{jt}^{+}\)、\(T_{jt}^{-}\)，道路外单程时间为 \(v_{jt}\)，派遣延迟为 \(\delta\)。响应资格和单次地面服务成本分别为
\begin{align}
r_{jt}&=\mathbf{1}\{\delta+T_{jt}^{+}+v_{jt}\leq\overline{T}_j\},\label{eq:q6response}\\
a_{jt}&=n_j(T_{jt}^{+}+T_{jt}^{-}+2v_{jt}+\tau_j+\pi_j),\label{eq:q6cost}
\end{align}
其中 \(n_j\) 为小队人数，\(\tau_j\) 为现场观察时间，\(\pi_j\) 为准备时间。驻点投影到道路的距离也进入成本。本次道路外行程按欧式距离和统一步速估算；山地坡度、河流绕行和进入许可仍需当地校准。因此 \(r_{jt}\) 表示所用地图与假设协议内的响应资格，不是实测事件响应率，也不能据此认定现实中的不可达区域。

对固定目标 \(\eta\)，保留服务容量与资源约束，反求所需人时：
\begin{equation}
\begin{aligned}
\min\quad &H_t=H_{0t}+L_t+\sum_j(x_{jt}+\gamma_{jt}h_{jt})\\
\text{s.t.}\quad &C_{jt}s_{jt}\leq x_{jt}/a_{jt}+h_{jt}/b_{jt},\\
&\ell r_{jt}\leq s_{jt}\leq r_{jt},\quad x_{jt},h_{jt}\geq0,\\
&h_{jt}=0\ (m_{jt}=0),\quad \sum_jh_{jt}\leq U_t,\\
&100\sum_jw_js_{jt}\geq\eta.
\end{aligned}
\label{eq:q6constraints}
\end{equation}
\(b_{jt}\) 为单位无人机服务所需机时，\(\gamma_{jt}\) 将其折算为人工；\(m_{jt}\) 表示已获授权且满足观测等效性的技术资格。预算给定时，可增加 \(H_t\leq H_t^{\max}\) 并最大化 \(P_t\)，沿用第二题的资源配置方向；目标给定时使用式\eqref{eq:q6constraints}反求人力。\(L_t\) 包括社区冲突处置、游客管理和设备维护等单独测量的工作量。本次初步计算不设无人机预算，未测量的专属工作量不计入人员数；这些任务在正式部署时必须补入。这里 \(\ell=0.15\)，用于防止只服务低成本区域。

@@PARAMTABLE@@

沿用第三题每人每月120小时有效工时。为比较驻点数量变化，情景中每个响应点预留两人、每天8小时、每月30天；若有 \(K\) 个候选点，则
\begin{equation}
H_0=K\times2\times8\times30=480K,\qquad N=\left\lceil H^{\min}/120\right\rceil.
\label{eq:q6staff}
\end{equation}
预留人时属于模型假设，不能解释为当地现有值守制度。空间代表位置也只是数值积分点；任务量允许为连续的月均工作量，没有将每个网格虚构成一个实测动物点或强制独立巡检地点。

\subsection{两类保护区的适配方案}
\subsubsection{奇特旺：重点物种、森林与季风通行}

奇特旺的保护对象包括独角犀、虎及河流生境相关物种。重点物种核查、森林巡护与边界冲突处置需要分别定义任务；它们对观测方式、时效和人员技能的要求不同。历史管理计划记载季风洪水与车辆通行限制，可作为建立季节图的机制依据；实际封路位置和持续时间应由当前记录补充\cite{chitwan,cnpplan}。本节20 km/h情景仅检验速度降低的影响，不将其称为实测季风通行条件。

本次采用UNEP-WCMC的WDPCA2026年10月发布多边形（site805），配合OSM机动车候选道路和Kasara、Sauraha、Amaltari具名位置作为选址的地理参考\cite{wdpca,osm}。这三个位置并未被认定为现有护林响应设施；Amaltari参考位置来自社区办公室的地图记录，实际响应点需另行核定。官方NTNC门户连接未成功，不能宣称已取得其边界文件。

边界一致性检验发现实质差异：WDPCA记录的报告面积为932平方千米，发布GIS面积约1,213平方千米；本次投影计算为@@CAREA@@平方千米，与DNPWC报告的952.63平方千米相差@@CADIFF@@\%\cite{cnparea}。OSM和ICIMOD公开多边形也出现相近差异，且所用几何有效，不能通过修复自交或重投影消除差别。因此奇特旺的数值仅用于发布多边形范围内的迁移试算，边界校准未通过；本文不据此提出当前法定园区的定量人员配置。不得为匹配官方面积而任意缩放边界。缓冲区社区任务应另建范围。

WorldCover2021分类显示，所用发布多边形内林地约占@@CFOREST@@\%，草地、灌丛与裸地合计约占@@COPEN@@\%\cite{worldcover}。这些分类比例受上述范围差异影响，应在修订边界后重算。森林和高草条件下还应通过地面或固定设备试验校准发现概率与复核时间；无人机只有取得授权、证明任务等效性并满足地面响应时，才能进入式\eqref{eq:q6constraints}。设备维护、河流交通与社区协作工作需要单列人工成本。

\subsubsection{黄石：游客交互、季节交通与技术权限}

黄石的任务应结合重点动物监测、游客与动物交互、道路事件和偏远生境服务建立。NPS游客使用管理资料支持按交通和游览空间识别任务\cite{visitor}，但游客流量不能直接代替动物责任。正式迁移应接入分时客流、事件位置、任务处置时间和当地调查记录，并避免将同一交通事件重复计入多个需求分项。

本次采用NPS官方边界、公开道路和位置点；基准候选点为Norris、Lake两个护林站位置，增加驻点的情景采用South Entrance护林站位置。位置来自真实数据，选点与配置人数属于方案假设，未认定这些站点当前均承担相同响应职责。道路查询共取得2,007条记录并核对总数，排除标为私人道路的记录后，园内使用道路长度约@@YROAD@@千米。NPS公开图层有意排除部分行政及作业道路，因此它不能代替完整护林道路库\cite{npsroads,npsboundary,npspois}。

黄石冬季的游客道路状态与管理人员实际通行条件应分别记录；公开道路关闭不能自动转化为护林人员完全不能到达\cite{conditions}。当前NPS规则限制无人机使用，未获书面授权时本节令 \(U_t=0\)\cite{rules}。适配后的设备重点应围绕合规的地面观测、通信与相应季节交通能力建立，具体数量由当地任务量和可用工具反求。WorldCover分类中，所用边界内林地约占@@YFOREST@@\%，永久水体约占@@YWATER@@\%；这说明开阔景观不能作为整园的统一检测条件。

@@DATATABLE@@

\subsection{真实空间数据验证与部署变化}

将两园数据多边形分别投影到UTM45N和UTM12N，以米为单位计算面积和长度。WorldCover10米源数据采用最近邻采样到100米栅格，保持分类编码，再按数据多边形裁剪；永久水体不承担本次陆域服务需求。奇特旺使用1千米巡检网格，黄石使用2.5千米网格，边缘网格按多边形裁剪并保留实际面积。真实资料地图和候选位置见图\ref{fig:q6network}，统计口径见表\ref{tab:q6geo}。奇特旺全部数值受边界校准未通过的限制。

@@FIG2@@

@@GEOTABLE@@

先计算模型内的条件响应上限，再将各园固定服务目标设为其双驻点、30 km/h基准上限的90\%：
\begin{equation}
P_t^{\mathrm{geo}}=100\sum_jw_jr_{jt},\qquad \eta=0.90P_{\mathrm{base}}^{\mathrm{geo}}.
\label{eq:q6cap}
\end{equation}
这个目标在同一公园的各情景中保持不变，避免速度降低后同步降低目标而掩盖服务损失。它不是全园90分目标；基准无法响应的陆域仍需通过驻点、步道或其他经确认的交通方式补足。响应上限还与所用地图完整性及道路外行程假设有关，不能解释为真实保护率。

@@RESULTTABLE@@

@@RESULTPROSE@@

@@FIG3@@

提高候选驻点数量可以改变路网中的最短出发位置，但增加一个响应点也增加480人时预留。是否值得前置需要同时比较新增响应面积、检查成本和固定预留；仅比较地图覆盖比例不能确定最低人员方案。同样，提高平均速度只是在给定地图和协议下扩大模型响应范围，实际道路条件与安全要求仍应决定可采用的速度。

将巡检网格边长减半后，奇特旺与黄石的条件响应上限分别变化@@CGDIFF@@、@@YGDIFF@@个百分点；采用相同固定目标时的人时结果分别为@@CFINEH@@、@@YFINEH@@。将土地覆盖采样从100米改为50米后，两园林地比例分别变化@@CRDIFF@@、@@YRDIFF@@个百分点。这些复核检验空间离散化影响，没有替代源数据分类精度或现场校准。另以独立的成本排序分配法复算线性规划，核对响应资格、服务底线、人时与人员当量上取整，@@CHECKCOUNT@@个案例的数值核验全部通过；奇特旺边界一致性检验仍未通过，两类核验分别记录。

真实空间计算已经说明跨大陆迁移会改变生境组成、道路成本和服务范围；部署阶段还需将物种分布、风险记录、季节路线、技术发现率及专属任务工时接入同一结构。奇特旺应优先核对边界及季风、河流通行条件，黄石应补齐护林作业路网和分时交通任务。最终人员建议应在这些本地校准完成后给出；本次条件人员当量只包含响应预留和所设陆域巡检协议。

\FloatBarrier
\begin{thebibliography}{12}
\bibitem{chitwan} UNESCO World Heritage Centre. Chitwan National Park. \url{https://whc.unesco.org/en/list/284}. 访问日期：2026-10-06.
\bibitem{cnpplan} Chitwan National Park Office. Management Plan 2013--2017. 历史季节机制资料；FAO存档：\url{https://faolex.fao.org/docs/pdf/nep220147.pdf}.
\bibitem{cnparea} DNPWC. State of Conservation Report of Chitwan National Park, 2021. \url{https://dnpwc.gov.np/media/files/UNESCO_Report_of_Chitwan_National_Park.pdf}.
\bibitem{osm} OpenStreetMap contributors; Geofabrik. Nepal extract, 数据截至2026-10-04 20:20:21 UTC. ODbL1.0. \url{https://download.geofabrik.de/asia/nepal.html}.
\bibitem{wdpca} UNEP-WCMC and IUCN (2026). Protected Planet: World Database on Protected and Conserved Areas, October2026, site805. \url{https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer/1}.
\bibitem{worldcover} Zanaga et al. ESA WorldCover10m2021v200, 2022. \url{https://doi.org/10.5281/zenodo.7254221}. CC BY4.0. \url{https://esa-worldcover.org/en/data-access}. © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium.
\bibitem{npsboundary} US National Park Service. Yellowstone National Park Tract and Boundary Data. 目录更新2025-12-18；\url{https://irma.nps.gov/DataStore/Reference/Profile/2316784}.
\bibitem{npsroads} US National Park Service. NPS Public Roads. \url{https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer/0}. 下载日期：2026-10-06.
\bibitem{npspois} US National Park Service. NPS Public POIs. \url{https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_POIs_Geographic/FeatureServer/0}. 下载日期：2026-10-06.
\bibitem{visitor} US National Park Service. Yellowstone: Visitor Use Management. \url{https://www.nps.gov/yell/learn/management/visitor-use.htm}. 访问日期：2026-10-06.
\bibitem{conditions} US National Park Service. Yellowstone: Current Conditions. \url{https://www.nps.gov/yell/planyourvisit/conditions.htm}. 访问日期：2026-10-06.
\bibitem{rules} US National Park Service. Yellowstone: Laws and Policies. \url{https://www.nps.gov/yell/learn/management/lawsandpolicies.htm}. 访问日期：2026-10-06.
\end{thebibliography}
\end{document}
'''

LINKS={'chitwan':('UNESCO','https://whc.unesco.org/en/list/284'),'cnpplan':('历史管理计划','https://faolex.fao.org/docs/pdf/nep220147.pdf'),'cnparea':('DNPWC报告','https://dnpwc.gov.np/media/files/UNESCO_Report_of_Chitwan_National_Park.pdf'),'osm':('OSM/Geofabrik','https://download.geofabrik.de/asia/nepal.html'),'worldcover':('ESA WorldCover','https://esa-worldcover.org/en/data-access'),'npsboundary':('NPS边界','https://irma.nps.gov/DataStore/Reference/Profile/2316784'),'npsroads':('NPS道路','https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer/0'),'npspois':('NPS位置点','https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_POIs_Geographic/FeatureServer/0'),'visitor':('NPS游客管理','https://www.nps.gov/yell/learn/management/visitor-use.htm'),'conditions':('NPS通行条件','https://www.nps.gov/yell/planyourvisit/conditions.htm'),'rules':('NPS规则','https://www.nps.gov/yell/learn/management/lawsandpolicies.htm')}
LINKS['wdpca']=('WDPCA2026-10','https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer/1')
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
 body=body.replace(r'\begin{equation}',r'\[').replace(r'\end{equation}',r'\]').replace(r'\begin{align}',r'\[\begin{aligned}').replace(r'\end{align}',r'\end{aligned}\]')
 return '# 6 保护资源配置模型的跨大陆适配\n\n'+body.strip()+'\n\n复现及证据见[第六题计算说明](../modeling_notes/question6_calculation_notes.md)。\n'

def main():
 r=json.loads((OUT/'q6_results.json').read_text(encoding='utf8'));c=r['parks']['chitwan'];y=r['parks']['yellowstone'];cases={z['id']:z for z in r['cases']};v=r['grid_verification'];checks=json.loads((OUT/'q6_verification.json').read_text(encoding='utf8'))
 replacements={'CAREA':f"{c['polygon_area_km2']:.2f}",'CADIFF':f"{100*abs(c['polygon_area_km2']/952.63-1):.2f}",'CFOREST':f"{100*c['forest_share']:.2f}",'COPEN':f"{100*c['open_share']:.2f}",'YFOREST':f"{100*y['forest_share']:.2f}",'YWATER':f"{100*y['water_share']:.2f}",'YROAD':f"{y['road_metadata']['in_park_road_km']:.2f}",'CGDIFF':f"{v['chitwan']['cap_difference_pp']:+.2f}",'YGDIFF':f"{v['yellowstone']['cap_difference_pp']:+.2f}",'CFINEH':f"{v['chitwan']['fine_solution']['total_person_hours']:.2f}" if v['chitwan']['fine_solution'] else '目标不可达','YFINEH':f"{v['yellowstone']['fine_solution']['total_person_hours']:.2f}" if v['yellowstone']['fine_solution'] else '目标不可达','CRDIFF':f"{c['landcover_resolution_check']['forest_difference_pp']:+.3f}",'YRDIFF':f"{y['landcover_resolution_check']['forest_difference_pp']:+.3f}",'CHECKCOUNT':str(len(checks['checks']))}
 replacements['FIG1']=figure('fig1_adaptation_flow','真实数据、情景参数与当地校准的迁移关系','fig:q6flow')
 replacements['FIG2']=figure('fig2_real_maps','真实资料的发布多边形、道路与候选位置。奇特旺为WDPCA边界配合OSM道路及位置，边界校准未通过；黄石为NPS公开数据。绿色为模型响应资格','fig:q6network')
 replacements['FIG3']=figure('fig3_real_results','真实路网下的速度与驻点情景；人时及人员当量受所设作业协议约束','fig:q6results')
 replacements['PARAMTABLE']=table('初步验证的作业假设；均不宣称当地实测标准','tab:q6params',['参数','设定','用途'],[['有效工时','120小时/人/月','与第三题一致'],['车速、步速','30、4 km/h','车辆情景另设20、40 km/h'],['派遣、观察、准备','10、10、5分钟','进入响应和检查成本'],['小队与服务密度','2人；8次/100平方千米/月','面积服务协议'],['响应与服务底线','2小时；15\%','与原模型结构一致'],['响应点预留','480人时/点/月','比较驻点固定工作量'],['无人机预算','0小时','授权及等效性未校准']],'p{.2\linewidth}p{.36\linewidth}X')
 replacements['DATATABLE']=table('真实数据来源及正式部署需补充的校准数据','tab:q6data',['项目','奇特旺','黄石'],[['边界与道路','WDPCA2026-10多边形；OSM2026-10-04道路。边界一致性未通过','NPS边界、公开道路；需补护林作业道路'],['候选位置','Kasara、Sauraha、Amaltari具名地理参考，设施待核定','Norris、Lake、South Entrance护林站位置'],['生境分类','ESA WorldCover2021v200','ESA WorldCover2021v200'],['对象与需求校准','重点物种位置、调查努力、社区冲突与巡护日志','动物调查、游客分时暴露与事件处置日志'],['通行与技术校准','季风封路、河流通行、速度与技术试验','季节管理通行、坡度、工具可用性及授权']],'p{.18\linewidth}XX')
 geo=[]
 for title,key,fmt in [('向量面积（平方千米）','polygon_area_km2','area'),('陆域服务面积（平方千米）','land_area_km2','area'),('林地占比（\%）','forest_share','percent'),('草地、灌丛、裸地（\%）','open_share','percent'),('永久水体（\%）','water_share','percent')]:geo.append([title,*[f"{p[key]*(100 if fmt=='percent' else 1):.2f}" for p in [c,y]]])
 geo.append(['园内使用道路（千米）',f"{c['road_metadata']['in_park_road_km']:.2f}",f"{y['road_metadata']['in_park_road_km']:.2f}"])
 geo.append(['服务网格数量',str(c['cell_count']),str(y['cell_count'])])
 replacements['GEOTABLE']=table('所用数据多边形的空间统计；奇特旺范围待校准，土地覆盖为100米采样估计','tab:q6geo',['指标','奇特旺发布范围','黄石NPS范围'],geo,'Xrr')
 rows=[]
 for z in r['cases']:
  s=z['solution'];rows.append([z['id'],z['label'],f"{z['geographic_cap']:.2f}",f"{z['target_score']:.2f}",f"{s['total_person_hours']:.2f}" if s else '不可达',str(s['staff_integer']) if s else '--'])
 replacements['RESULTTABLE']=table('真实空间资料下的条件试算；C类为待校准发布范围，人数均为所设服务的条件当量','tab:q6results',['情景','设置','上限（\%）','固定目标','人时','人数当量'],rows,'cXrrrr')
 prose=[]
 for park,prefix in [('chitwan','C'),('yellowstone','Y')]:
  a,b,d=cases[prefix+'0'],cases[prefix+'1'],cases[prefix+'2'];s=a['solution'];ss=d['solution']
  pressure=(f"达到同一目标所需人时为{b['solution']['total_person_hours']:.2f}" if b['solution'] else '低于固定目标，使该目标在当前模型内不可达')
  prose.append(f"{r['parks'][park]['label']}基准条件响应上限为{a['geographic_cap']:.2f}\\%，固定目标为{a['target_score']:.2f}分，对应{s['total_person_hours']:.2f}人时。车速降至20 km/h时，上限变为{b['geographic_cap']:.2f}\\%；{pressure}。增加第三处候选驻点后，上限变为{d['geographic_cap']:.2f}\\%，达到相同目标所需人时为{ss['total_person_hours']:.2f}。")
 replacements['RESULTPROSE']='\n\n'.join(prose)
 tex=TEX
 for k,value in replacements.items():tex=tex.replace('@@'+k+'@@',value)
 assert '@@' not in tex
 (PAPER/'question6_adaptation.tex').write_text(tex,encoding='utf8');(PAPER/'question6_adaptation.md').write_text(markdown(tex),encoding='utf8')
 manifest=dict(source='docs/paper/question6_adaptation.tex',source_sha256=hashlib.sha256(tex.encode()).hexdigest(),results_sha256=hashlib.sha256((OUT/'q6_results.json').read_bytes()).hexdigest(),equations=6,figures=3,tables=4,figure_geometry_embedded=True,status='real spatial inputs; assumptions distinguished; source compilation pending')
 (OUT/'q6_chapter_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Formal Q6 rewritten from real spatial calculations.')
if __name__=='__main__':main()
