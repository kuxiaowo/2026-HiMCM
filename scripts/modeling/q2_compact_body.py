"""Eight-page Q2 narrative; numerical tokens come from saved model results."""

BODY = r'''
\section{有限资源下的人机协同保护资源配置模型}

第二题研究：有限人员和无人机应投入哪些地方，才能完成更多重要区域的检查？我们先确定各地的重要程度，再计算到场条件和作业时间，最后在资源上限内选择配置。

\noindent\textbf{术语速读。}“父区”是报告结果的大区；“检查单元”是大区内用于计算路线的小片区域。“点次”指对一个代表点完成一次规定检查。“人时”指人数乘工作小时，“机时”指单架累计飞行小时。“响应”指地面人员接到任务后到场；“需求权重”表示检查的重要程度；“完成率”表示规定点次完成的比例。“服务分”是按重要程度加权的完成率，不能当作动物存活率。\textbf{层次分析（AHP）}用成对比较确定类别权重；\textbf{熵权法}按各区数据的差异确定指标的组合比例。

\subsection{配置目标、研究单元与基本假设}
\subsubsection{区域、检查单元与规划时期}
沿用15个动物调查区，加主盐沼和其他调查外区域，共17个父区，记为\(\mathcal I\)。用10 km格网切分后得到\(\mathcal J\)中的@TARGETS@个检查单元；区\(i\)内的单元组成\(\mathcal J_i\)。面积\(A_j\)分配任务，内部代表点计算路线；一次检查不表示整片连续覆盖。按月规划，仅考察规定日间窗口。

\subsubsection{地面人员与无人机的服务职责}
两种方式在适用区域完成同一动物及可燃生境异常筛查清单，不同检查点次可以相加。无人机仍需运输、准备和操作人员，现场核查依靠地面队伍。六处候选驻点为Okaukuejo、Halali、Namutoni、Olifantsrus、Galton Gate、Nehale Gate；地点有来源，驻点用途是假设。假设事件较少，可共享响应人员。

\subsubsection{资源统计口径与规划假设}
295人为原题部门工作人员参考数。设60\%的人员资源用于模型任务，相当于177人的月工时，\textbf{不是同时在岗人数限制}。动物、土地覆盖、道路分别来自2015、2021、2026年资料\cite{survey,worldcover,osm}；其余参数为规划假设，保持表\ref{tab:parameters}的口径。

@TAB_PARAMETERS@
\clearpage

\subsection{区域保护需求与配置权重}
\subsubsection{动物保护责任与可燃生境责任}
对六类调查对象，先计算同一物种在各区的数量份额，再按保护类别加权，避免数量多的物种支配结果。设\(N_{im}\)为区\(i\)对象\(m\)的历史数量，\(q_{\ell(m)}\)为类别权重；\(\mathcal I_S\)为15个有动物资料的区，\(A_i^F\)为区内草、灌、林可燃面积。定义
\begin{equation}
V_i^A=\frac{\sum_{m\in\mathcal M}q_{\ell(m)}(N_{im}/\sum_{v\in\mathcal I_S}N_{vm})}{\sum_{m\in\mathcal M}q_{\ell(m)}},
\qquad V_i^F=\frac{A_i^F}{\sum_{v\in\mathcal I}A_v^F}.
\label{eq:responsibility}
\end{equation}
六类对象为蓝角马、平原斑马、长颈鹿、非洲草原象、南非剑羚和鸵鸟。两类责任分别合计为1。依据法规类别\cite{law}，按可猎、保护、特别保护顺序作团队判断：
\begin{equation}
\mathbf A=\begin{pmatrix}1&1/2&1/3\\2&1&1/2\\3&2&1\end{pmatrix},
\qquad\mathbf q=(@AHP_WEIGHTS@)^{\mathsf T}.
\label{eq:ahp}
\end{equation}
权重取最大特征值对应的正特征向量并归一化；一致性比率\(CR=(\lambda_{\max}-3)/(2\times0.58)=@AHP_CR@<0.1\)。比较倍数不是法定值。火侧缺少多年暴露资料，暂按可燃面积分责任；它不是火灾概率。主盐沼燃料设为零，不代表生态价值为零。

\subsubsection{道路进入便利度与监测需求修正}
将道路与边界的@ENTRIES@个交点作为进入候选源，求最短道路距离\(D_j^E\)，再加道路外接近距离\(d_j^\perp\)对应的步行时间：
\begin{equation}
T_j^E=\frac{D_j^E}{v_g}+\frac{d_j^\perp}{v_w},\qquad
E_j=\exp(-T_j^E/\tau_E),\quad\tau_E=2\ \mathrm h.
\label{eq:entry}
\end{equation}
\(v_g,v_w\)为道路、步行速度；进入越快，\(E_j\)越大。交点并非已证实的偷猎入口。缺少区内细分布时，按面积分摊责任，得到原始监测需求：
\begin{equation}
\mu_j=\frac{A_j}{A_i},\quad\sum_{j\in\mathcal J_i}\mu_j=1,
\qquad R_j^A=V_i^A\mu_jE_j,\quad R_j^F=V_i^F\mu_j.
\label{eq:raw}
\end{equation}

\subsubsection{基于共同数据范围的熵权计算}
先按父区汇总\(X_{ik}=\sum_{j\in\mathcal J_i}R_j^k\)，在共同有资料的15区计算，\(k\in\{A,F\}\)：
\begin{equation}
p_{ik}=\frac{X_{ik}}{\sum_{v\in\mathcal I_S}X_{vk}},\quad
e_k=-\frac{\sum_i p_{ik}\ln p_{ik}}{\ln15},\quad
\alpha_k=\frac{1-e_k}{(1-e_A)+(1-e_F)}.
\label{eq:entropy}
\end{equation}
约定\(0\ln0=0\)。分布越均匀，熵\(e_k\)越高，区分能力越低。当前\(e_A=0.881596,e_F=0.934989\)，得到\(\alpha_A=@ALPHA_A@,\alpha_F=@ALPHA_F@\)。这些比例反映数据差异，不是真实损失占比；列总量或差异度总和为零时停止赋权。

\subsubsection{检查单元权重与区域汇总}
动物分项只在有调查资料的单元集合\(\mathcal J_S\)中归一化，生境分项覆盖全体单元：
\begin{equation}
\begin{aligned}
w_j^A&=R_j^A/\sum_{\ell\in\mathcal J_S}R_\ell^A\ (j\in\mathcal J_S),
&w_j^F&=R_j^F/\sum_{\ell\in\mathcal J}R_\ell^F,\\
w_j&=\alpha_Aw_j^A+\alpha_Fw_j^F,
&W_i&=\sum_{j\in\mathcal J_i}w_j.
\end{aligned}
\label{eq:weights}
\end{equation}
调查外令动物评分系数为零，但原始动物值保留未知。由两分项各自合计为1，得\(\sum_jw_j=1\)。\(W_i\)是区的重要性份额；配置还取决于作业成本和响应条件。
\clearpage

\subsection{地理可达性与单位作业成本}
\subsubsection{有向路网、最短路径与响应门槛}
道路保留真实连接和单行方向，去程、返程分别求最短路。假设管理车辆可通行候选道路，道路外按直线步行估计；道路权限及障碍尚需现场核查。驻点集合为\(\mathcal B\)，驻点\(b\)到目标道路接入点的去返距离为\(d_{bj}^+,d_{jb}^-\)。合格驻点及响应指示为
\begin{equation}
\begin{aligned}
\mathcal B_j^R&=\{b\in\mathcal B:t_d+d_{bj}^+/v_g+d_j^\perp/v_w\le T_{\max},\
d_{bj}^+,d_{jb}^-<\infty\},\\
r_j&=\mathbf1\{\mathcal B_j^R\ne\varnothing\},\qquad t_d=10\ \mathrm{min},\quad T_{\max}=2\ \mathrm h.
\end{aligned}
\label{eq:response}
\end{equation}
在合格驻点中选往返时间最短者\(b_j^*\)，记可响应集合\(\mathcal J_R=\{j:r_j=1\}\)。后文\(D_j=d_{b_j^*j}^++d_{jb_j^*}^-\)。响应期限只限制到场时间，成本另计返程。基准可响应@REACHABLE@个单元，面积@REACH_AREA@ km\(^2\)，占@REACH_SHARE@\%；\(r_j\)不表示处置成功概率。

\subsubsection{地面检查的路线与人时计算}
一次检查包含道路往返、道路外步行往返、观察和准备；用距离除以速度得到时长，再乘队伍人数：
\begin{equation}
a_j=n_g\left(\frac{D_j}{v_g}+\frac{2d_j^\perp}{v_w}+t_o+t_p\right),\quad j\in\mathcal J_R.
\label{eq:ground}
\end{equation}
\(a_j\)单位为人时/点次，\(n_g=2\)，\(t_o=10\)分钟、\(t_p=5\)分钟均换算为小时。各目标独立往返，未做串点路线优化。

\subsubsection{无人机机时与配套人工计算}
人员沿道路把设备运到部署点，无人机替代道路外步行。一次检查的飞行机时\(b_j\)、配套人时\(o_j\)及换算系数为
\begin{equation}
b_j=\frac{2d_j^\perp}{v_u}+t_o,\qquad
o_j=n_u\left(\frac{D_j}{v_g}+t_p+b_j\right),\qquad\gamma_j=\frac{o_j}{b_j}.
\label{eq:drone}
\end{equation}
\(n_u=2\)。投入\(h_j\)机时支持\(h_j/b_j\)点次，消耗\(\gamma_jh_j\)人时。无人机适用集合为\(\mathcal J_U=\{j\in\mathcal J_R:b_j\le0.6\ \mathrm h,\ O_{i(j)}\ge0.6\}\)，\(O_i\)为父区开阔程度。@DRONE_ELIGIBLE@个可响应单元均满足该条件；起降条件仍需核查。

@FIG_COSTS@
同一单元@COST_TARGET@，地面需@GROUND_EXAMPLE@人时/点次，无人机需@OPERATOR_EXAMPLE@配套人时和@FLIGHT_EXAMPLE@机时/点次，数值由路线计算，非实测作业日志。
\clearpage

\subsection{人机协同资源配置的线性规划模型}
\subsubsection{决策变量与需求加权目标函数}
求解器选择单元\(j\)的地面监测人时\(x_j\)、无人机机时\(h_j\)和服务完成率\(s_j\)。前两项单位为人时/月、机时/月；\(s_j=0.5\)表示完成一半规定点次。目标为
\begin{equation}
\max P=100\sum_{j\in\mathcal J}w_js_j.
\label{eq:objective}
\end{equation}
因\(\sum_jw_j=1\)，服务分在0至100之间。权重0.02的单元完成一半服务，贡献1分。比较配置时保持权重和服务标准相同；该分值不直接衡量事故减少或完整生态成效。

\subsubsection{单位面积需求与服务容量约束}
按每100 km\(^2\)每月8点次规定任务：
\begin{equation}
C_j=\kappa A_j/A_{\mathrm{ref}},\quad\kappa=8,\quad A_{\mathrm{ref}}=100\ \mathrm{km}^2,
\qquad\sum_jC_j=\frac\kappa{A_{\mathrm{ref}}}\sum_jA_j.
\label{eq:demand}
\end{equation}
总规定量为@CHECKS@点次/月。50 km\(^2\)单元需4点次/月。改格网只重新分摊面积，不改变总任务量。连续点次是规划近似，实际执行需安排整数次数。

可响应时令\(g_j=1/a_j\)，否则\(g_j=0\)；无人机适用时令\(u_j=1/b_j\)，否则\(u_j=0\)。资源支持的点次必须不少于计划完成量：
\begin{equation}
C_js_j\le g_jx_j+u_jh_j.
\label{eq:capacity}
\end{equation}
两种方式可分担不同检查点次，同一次重复检查不重复记分。完全采用地面方式，提高完成率\(\Delta s_j\)需\(C_ja_j\Delta s_j\)人时；无人机需\(C_jo_j\Delta s_j\)人时和\(C_jb_j\Delta s_j\)机时。每人时得分效率分别为\(100w_j/(C_ja_j)\)、\(100w_j/(C_jo_j)\)，因此不能只按区域权重比例分人。

\subsubsection{人员预算、机时预算与响应预留}
设60\%人员资源可用于保护，配置30架无人机。单人有效工时为120小时；每架每日2机时、每月20个可飞行日；六个响应驻点各2人、每日8小时、每月30天：
\begin{equation}
\begin{aligned}
H&=295\times0.6\times120=@HUMAN_BUDGET@\quad\text{人时/月},\\
U&=30\times2\times20=@DRONE_BUDGET@\quad\text{机时/月},\\
H_0&=6\times2\times8\times30=2880\quad\text{人时/月}.
\end{aligned}
\label{eq:budgets_values}
\end{equation}
总人工包括监测、无人机配套及固定响应；机时另设上限：
\begin{equation}
\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j+H_0\le H,
\qquad\sum_jh_j\le U.
\label{eq:budgets}
\end{equation}
响应预留全园只扣一次，人时不能与机时直接相加。监测人工可用上限为@MONITORING_BUDGET@人时。60\%和30架均为规划设定，不称公园现有编制或设备清单。
\clearpage

\subsubsection{区域服务底线与技术适用性约束}
为避免低权重区完全没有检查，令\(Q_i=\sum_{j\in\mathcal J_i}\mu_jr_j\)为可响应面积比例，\(\bar s_i=\sum_{j\in\mathcal J_i}\mu_js_j\)为全区面积加权完成率，要求
\begin{equation}
\bar s_i\ge\beta Q_i,\qquad\beta=0.15,\quad i\in\mathcal I.
\label{eq:floor}
\end{equation}
它保障可响应部分的15\%服务。若某区仅20\%面积可响应，全区底线为3\%；若完全不可响应，现有布局无法保障该区。这是通用检查要求，不能代替重点物种专项保护。

参数固定后，完整模型为
\begin{equation}
\boxed{\begin{aligned}
\max_{\mathbf x,\mathbf h,\mathbf s}\quad &100\sum_jw_js_j\\
\text{s.t.}\quad&C_js_j\le g_jx_j+u_jh_j,&&j\in\mathcal J,\\
&\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j\le H-H_0,\\
&\sum_jh_j\le U,\\
&\sum_{j\in\mathcal J_i}\mu_js_j\ge\beta\sum_{j\in\mathcal J_i}\mu_jr_j,&&i\in\mathcal I,\\
&0\le s_j\le r_j,\quad x_j,h_j\ge0,&&j\in\mathcal J,\\
&x_j=0\ (j\notin\mathcal J_R),\quad h_j=0\ (j\notin\mathcal J_U).
\end{aligned}}
\label{eq:lp}
\end{equation}
目标与约束都按投入成比例变化，构成线性规划。\(s_j\le1\)使完成全部要求后不再加分；不可响应单元不计服务。代码另限单种投入不超过完成该单元全部任务所需的资源，去掉无收益的超额投入。

\subsection{模型求解与可行性分析}
\subsubsection{模型求解与约束核验}
将@VARIABLES@个变量和上述约束交给SciPy的HiGHS求解器。随后独立复算逐点容量、响应及飞行条件、预算、各区底线和汇总。基准与减员方案均求得最优解，最大约束正残差小于\(10^{-6}\)，未知动物值仍为空。这证明解满足模型，不证明真实作业或生态结果已验证。

\subsubsection{同分方案选择与人工消耗核算}
同一最高分可能有不同配置。第一阶段求得最高服务分\(P^*\)，第二阶段保留该分数并重新选择全部完成率及投入：
\begin{equation}
\min_{\mathbf x,\mathbf h,\mathbf s}H_M=\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j,
\qquad100\sum_jw_js_j\ge P^*.
\label{eq:tie}
\end{equation}
其余约束不变，因此得到模型内所有最优同分方案中的全局最少人工。达到地理上限时，正权重可响应单元必须完成全部检查；零权重单元仍按区域底线配置。正文人时采用这一统一口径，真实人员编制还取决于任务清单和实际作业条件。
\clearpage

\subsubsection{地理上限、预算不足与替代机制}
由\(w_j\ge0\)和\(s_j\le r_j\)，有
\begin{equation}
P\le P_{\mathrm{geo}}=100\sum_jw_jr_j.
\label{eq:geo}
\end{equation}
这就是固定响应布局的评分上限：再多人员或飞行小时，也不能让地面响应不到的单元获得有效服务。若\(H<H_0\)，连响应预留都不足，模型必无解；\(H\ge H_0\)仍需额外人工满足检查底线。

两类队伍人数、准备和观察协议相同，单次人工差为
\begin{equation}
a_j-o_j=2n_gd_j^\perp\left(\frac1{v_w}-\frac1{v_u}\right)>0
\quad(d_j^\perp>0).
\label{eq:substitution}
\end{equation}
在当前假设下，飞行替代较慢的道路外步行，节省人工但占用机时。改变人数或检查协议后须重新比较；本模型不把这种替代外推到执法、消防等现场处置。

@FIG_MAPS@
图\ref{fig:maps}将重要程度与实际可提供的服务并列。需求较高并不意味着到场容易：ENP11权重8.05\%，可响应面积却仅约0.02\%。反之，靠近驻点和道路的区域，更容易用较少时间完成检查。\textbf{地图右侧的面积完成率与全园加权服务分采用不同权重，不能互换。}

需要核实的主要条件是道路权限、实际行驶和步行时间、无人机筛查能力、当前重点物种分布以及事件并发。当前动物历史调查、区内按面积分摊和等火暴露只支持条件性规划；黑犀牛等缺资料对象仍需专门调查。水源和降雨不纳入本题。
\clearpage

\subsection{配置结果与战略部署解释}
\subsubsection{基准预算下的分区资源配置}
在@HUMAN_BUDGET@人时和@DRONE_BUDGET@机时预算下，服务分为@BASE_SCORE@，等于地理上限。最优同分方案中的最少人工配置使用@BASE_FLIGHT@机时、@BASE_OPERATOR@无人机配套人时及2880响应人时，总计@BASE_HUMAN@人时；剩余@HUMAN_IDLE@人时和@DRONE_IDLE@机时。地面例行检查为0，\textbf{但部署、操作和响应仍由地面人员承担}。

各区投入由单元相加，共享响应预留不重复分摊：
\begin{equation}
H_i^M=\sum_{j\in\mathcal J_i}x_j+
\sum_{j\in\mathcal J_i\cap\mathcal J_U}\gamma_jh_j,
\qquad U_i=\sum_{j\in\mathcal J_i}h_j.
\label{eq:regional}
\end{equation}
@TAB_REGIONS@
表\ref{tab:regions}前三个百分数分别为需求权重、可响应面积比例和面积加权服务率。人工是监测及配套人工，另加全园2880响应人时才得到总消耗。

ENP1需求占19.06\%，投入@ENP1_HOURS@监测人时；ENP12投入@ENP12_HOURS@人时。ENP11虽然需求较高，响应限制使投入很少，不能按需求比例机械分人。主盐沼动物未知、可燃责任为零，当前评分未表达其完整价值，但区域底线仍要求通用检查。

最少人工方案在主盐沼提供@PAN_SERVICE@\%面积加权服务，满足该区可响应部分的15\%通用底线。第二阶段允许同分方案重新选择；这里的人工最低限于当前任务清单和共享响应模型，换算岗位仍需检查日期、资格和实际作业条件。
\clearpage

\subsubsection{资源紧缺下的同预算方案比较}
面积均衡方案让可响应单元完成率相同；需求比例方案按区内需求密度\(W_i/A_i\)安排；两者与优化方案采用相同成本、底线和上限。两类预算下的结果为：

@TAB_COMPARISON@
人时减少40\%至12744后仍有资源余量，三种方案均达到地理上限，当前对照未显示优化的分数优势。停用无人机仍达@NODRONE_SCORE@分，使用@NODRONE_HUMAN@人时；技术作用主要体现为作业人工差异。@MOBILE_NOTE@

\subsubsection{响应范围瓶颈与前置驻点情景}
预算仍有余额，应优先核查响应范围的改善。在ENP11、ENP3410、ENP5各选一个新增道路节点，保持权重和总预算不变；每点增加\(2\times8\times30=480\)响应人时，再计算路线和配置。

@TAB_FORWARD@
三个候选中，ENP5方向最高为@FORWARD_SCORE@分，比原布局增加@FORWARD_GAIN@分。它仅是已枚举候选中的最好方案，实际使用前需核实权限和通行条件。

第二题向第三题传递权重、服务量、作业成本、响应条件及设备预算。第三题给定目标后重新求最少人时，再换算人数；本题不直接估计人员需求。完整敏感性分析和局限讨论分别放第四、五题。

@REFERENCES@
'''
