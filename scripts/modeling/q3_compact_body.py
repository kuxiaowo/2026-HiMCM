"""Six-page Q3 narrative. Values are filled from audited saved solutions."""

BODY = r'''
\section{季节需求下的保护服务评估与人员需求模型}

第三题研究两个问题：同一批人员能否应对不同月份的工作；全年保持同一检查标准需要多少人？我们继承第二题的监测与日间响应任务，再单独加入季节火险检查和人工水点维护，用月度工作量反求人员需求。

\noindent\textbf{术语速读。}“人时”是人数乘工作小时；“机时”是单架无人机累计飞行小时。“点次”是完成一次规定检查。“检查单元”是计算路线与投入的小片区域，“父区”是汇总结果的大区。“完成率”是规定检查量完成的比例；“服务分”按重要程度汇总完成率，不能当成动物存活率。“人工水点”在本题指需要维护抽水设备的钻井样本。下文的优化是在给定条件下选择最省人工或服务分最高的配置，不预测动物数量。

\subsection{服务目标与基本设置}
\subsubsection{第二题接口与基准服务目标}
沿用17个父区、599个检查单元和六处候选驻点；固定需求权重\(w_j\)、规定点次\(C_j\)、地面人时成本\(a_j\)、无人机机时成本\(b_j\)及每机时配套人工\(\gamma_j\)。\(r_j=1\)表示地面能在2小时内到场，\(r_j=0\)表示不能；\(s_{jt}\)为单元\(j\)在月\(t\)的基准检查完成率。保持第二题目标：
\begin{equation}
P_t=100\sum_jw_js_{jt},\qquad
\eta=P_2^*=57.26\ldots,\qquad 0\le s_{jt}\le r_j.
\label{eq:score}
\end{equation}
计算采用完整精度，显示到两位小数。固定驻点下的上限为\(P_{\mathrm{geo}}=100\sum_jw_jr_j\)，本基线恰好等于\(\eta\)。新增火险与水点任务必须完成，但不重复加到服务分中；因此各月仍按同一监测目标比较。增加人员不会自动解决到场范围外的缺口。

\subsubsection{月度口径与资源参数}
按12个标准30天月规划，单人月有效工时固定120小时。基准资源设为60\%人员可用、30架无人机，其余参数沿用第二题：
\begin{equation}
N_0=295\times0.6=177,\qquad H^{\mathrm{ref}}=177\times120=21240.
\label{eq:reference}
\end{equation}
单位为人、人时/月。60\%表示供模型内保护任务使用的月度人员资源比例，不是某时刻同时在岗人数。295来自原题；比例与有效工时为规划假设。

共享响应仍预留2880人时/月，六驻点、每点两人在日间值守；无人机预算为\(30\times2\times20=1200\)机时/月。每100\(\mathrm{km}^2\)每月8点次、2小时响应期限、作业速度和单位成本均不变。

30架表示设备库存，不能直接推成30组同时作业。无人机实际使用的运输、准备和操作人工，已由\(\gamma_j\)逐点计入；详细排班仍需另行核实。本题只覆盖日间监测、响应及所列新增任务，不能给出全园所有岗位的真实编制。

\clearpage
\subsection{季节服务工作量}
\subsubsection{季节窗口与月份划分}
一项埃托沙东北部研究采用5—10月旱季、11—4月湿季的分类\cite{season}；官方火管理策略区分5—7月早期、8—11月晚期窗口\cite{fire}。据此形成表\ref{tab:season}。时间窗口有资料依据，具体访问频次与现场耗时是团队的服务设定，不能称为公园现行定额或火灾预测。

@TAB_SEASON@

\subsubsection{额外火险检查需求}
令\(\rho_i^F\)为父区可燃生境比例，\(A_j\)为单元面积，按区域比例分配可燃面积，再计算新增检查：
\begin{equation}
A_j^F=\rho_{i(j)}^F A_j,\qquad
D_{jt}^{\mathrm{all}}=k_t\frac{A_j^F}{100},\qquad
D_{jt}=r_jD_{jt}^{\mathrm{all}}.
\label{eq:fire}
\end{equation}
面积用\(\mathrm{km}^2\)，\(k_t\)是表\ref{tab:season}的月度额外频次。区域比例下分是空间近似，不是逐点测量。新增检查沿用第二题成本、独立计算，不把一次基准检查同时算作新增检查。

晚期可响应部分为@FIRE_REACH@点次/月；响应范围外另有\(\sum_j(1-r_j)D_{jt}^{\mathrm{all}}=@FIRE_OUT@\)点次/月，明确记为未服务。增加的是预防性观察，未计算扑救和计划燃烧人工。

\subsubsection{人工水点运维人时}
2013年5月调查有42条水点记录，我们仅选17处BH钻井样本\cite{water}。官方年报记载水点太阳能系统改造\cite{annual}，因此新增任务设为抽水设备检查、清理与小修，不假定运水量。样本当前是否运行、是否完整仍未知。

各水点从六驻点择最短完整往返，保留单行约束。道路速度30、步行速度4\(\mathrm{km/h}\)，道路距离\(d^+,d^-\)与道路外单程距离\(d^\perp\)均用km：
\begin{equation}
T_\ell^{\mathrm{rt}}=\min_b\left[\frac{d_{b\ell}^++d_{\ell b}^-}{30}+\frac{2d_\ell^\perp}{4}\right],\qquad
W_t=\sum_{\ell=1}^{17}2f_t\left(T_\ell^{\mathrm{rt}}+\tau_t+\frac1{12}\right).
\label{eq:water}
\end{equation}
\(f_t\)为每点月访问次数，\(\tau_t\)为现场小时；两人同行，每次准备5分钟。仅在去返程有限的驻点中取最小值。维护是预先安排的作业，不用事件2小时到场门槛。

17处合计往返@TRAVEL_SUM@小时；正常现场0.5小时，则湿季@WATER_WET@、旱季@WATER_DRY@人时/月。无人机不能替代现场维护。各次往返单独计时，未抵扣串点省下的路程，可能高估出行人工。

\clearpage
@FIG_WATER@

\subsection{月度服务评估与人时优化}
\subsubsection{决策变量与共同约束}
基准监测用地面人时\(x_{jt}\)、无人机机时\(h_{jt}\)和完成率\(s_{jt}\)；新增火险用独立地面人时\(y_{jt}\)、机时\(v_{jt}\)。水点人工\(W_t\)预先算定，不能被优化过程删掉。

令\(g_j=1/a_j\)、\(u_j=1/b_j\)为适用方式每小时完成的点次；不适用方式令系数和投入均为0。两个任务分别满足：
\begin{equation}
C_js_{jt}\le g_jx_{jt}+u_jh_{jt},\qquad
D_{jt}\le g_jy_{jt}+u_jv_{jt}.
\label{eq:capacity}
\end{equation}
左侧是要完成的点次，右侧是资源能支持的点次。基准与新增任务各计一次，不能重复使用同一次作业。无人机和所有父区的通用服务要求为：
\begin{equation}
\sum_j(h_{jt}+v_{jt})\le1200,\qquad
\sum_{j\in\mathcal J_i}\mu_js_{jt}\ge0.15\sum_{j\in\mathcal J_i}\mu_jr_j.
\label{eq:budgets}
\end{equation}
\(\mu_j\)是单元占父区的面积比例，15\%底线针对可响应部分。工时非负，完成率不超过\(r_j\)，不适用或不可响应处投入为0。将这些条件合记为\(\mathcal F_t\)。总人工为：
\begin{equation}
H_t=2880+W_t+\sum_j(x_{jt}+y_{jt})+\sum_j\gamma_j(h_{jt}+v_{jt}).
\label{eq:hours}
\end{equation}
2880是共享响应人时，只预留一次；飞行占用的配套人员也完整计入。两类模型共同使用这些条件，避免同一人或同一机时在任务间重复计算。

\clearpage
\subsubsection{固定人数的服务水平评估}
给定177人的月度容量，先完成必要水点与火险任务，再使基准服务分最高：
\begin{equation}
\begin{aligned}
P_t^*(177)=\max_{\mathbf z_t}\quad &100\sum_jw_js_{jt}\\
\text{满足}\quad &\mathbf z_t\in\mathcal F_t,\qquad H_t\le21240,
\end{aligned}
\label{eq:forward}
\end{equation}
其中\(\mathbf z_t\)包括上述五组变量。目标缺口为\(\max\{0,\eta-P_t^*(177)\}\)。预算有余量时，季节工作增加不一定使分数下降；预算连必要任务和底线都不够时，应报告不可行，不能把有缺漏的服务称为达标。

\subsubsection{固定目标的最小人时模型}
保持同一服务目标，取消177人的人工上限，反求最少总人工：
\begin{equation}
\begin{aligned}
H_t^*(\eta)=\min_{\mathbf z_t}\quad&H_t\\
\text{满足}\quad&\mathbf z_t\in\mathcal F_t,\qquad100\sum_jw_js_{jt}\ge\eta.
\end{aligned}
\label{eq:inverse}
\end{equation}
机时、响应条件与季节服务标准保持不变。与修订后的第二题一致，各单元完成率可在同分方案中重新选择。若同时保留人工上限，只能判断当前人数够不够，无法估计超出预算时到底需要多少人。

\subsection{求解与人员需求换算}
\subsubsection{月度求解与基本核验}
逐月读取第二题成本，生成新增点次\(D_{jt}\)与水点人时\(W_t\)，求解两种模型并保存分区结果。599单元各有五个变量，共2995个；参数固定后关系均为线性，使用HiGHS求解。

独立脚本重新计算点次容量、火险必要任务、区域底线、人时与机时、评分及人数取整，84组已保存方案通过核验。高于地理上限的目标被拒绝，低于固定响应人工的预算返回不可行。

去掉新增任务后，第三题独立构建的反求模型得到@FREE_BASE@人时，与修订后第二题的@Q2_BASE@人时一致。两题均保留最优分数并在所有同分方案中最小化人工，零权重单元仍满足区域通用服务底线。

\subsubsection{月度人数与全年固定配置}
最少人工除以120并向上取整；全年采用同一批人员时，取月度峰值：
\begin{equation}
N_t^{\mathrm{plan}}=\left\lceil\frac{H_t^*(\eta)}{120}\right\rceil,\qquad
N_{\mathrm{year}}^{\mathrm{plan}}=\max_tN_t^{\mathrm{plan}}.
\label{eq:staff}
\end{equation}
各月人数不能相加，年平均人工也不能替代峰值月要求。结果是当前任务的月度容量规划人数；连续工时允许小数点次，尚未证明整数派遣、每次访问间隔或个人详细排班。

\clearpage
\subsection{结果与人员配置解释}
\subsubsection{固定177人的月度服务}
中档规则下，177人在12个月均能达到57.26分，目标缺口为0。峰值@PEAK_HOURS@人时低于21240，余量@PEAK_SPARE@人时。图\ref{fig:monthly}显示季节工作变化；余量不能使服务超过固定到场布局的上限。

@FIG_MONTHLY@

\subsubsection{季节人时与全年人数}
5—7月增加水点与早期火险任务；8—10月晚期火险加密，形成全年峰值。11月水点恢复湿季规则，但火险加密仍持续，故需56人。

@TAB_RESULTS@

\begin{equation}
H_{\mathrm{peak}}^*=2880+@BASE_MONITOR@+@FIRE_HOURS@+@WATER_DRY@=@PEAK_HOURS@.
\label{eq:peak}
\end{equation}
四项依次是响应、基准监测、额外火险和水点人时。全年固定需@ANNUAL_STAFF@人；56人在峰值月最高@FEWER_SCORE@分，低于目标，验证了月度容量口径下的取整结果。

\clearpage
\subsubsection{异常干旱下的人员变化}
压力情景只把旱季每水点访问提高到8次/月、现场作业提高到1小时，其余设置不变。它表示条件性的运维负担，不是降雨预测，不计算SPI、运水量或动物种群。

\begin{equation}
W_{\mathrm{drought}}=@WATER_STRESS@,\quad
H_{\mathrm{peak,drought}}^*=@STRESS_HOURS@,\quad
N_{\mathrm{year,drought}}^{\mathrm{plan}}=@STRESS_STAFF@.
\label{eq:drought}
\end{equation}
两个人时量单位均为人时/月。对照表\ref{tab:drought}，干旱压力使水点人工增加558.34人时，全年需求由57升为62人，即较常规方案增加5人。

@TAB_DROUGHT@

\textbf{177人的参考配置无需追加人员。}常规与异常干旱均维持57.26分，峰值机时仍为210.61，低于1200；新增地面水点任务主要增加人工。

\textbf{部署解释。}在本文范围内，可先以57人的月度容量满足常规要求，并为所设干旱工作准备达到62人的容量；这不是对真实岗位编制的裁减建议。若要提高可服务范围，应先核查前置驻点和道路到场条件，再计算新增服务与人工，而非只增加人数或设备。

\textbf{结果边界。}历史样本不能代表当前完整水点清单；作业标准需要日志校准。布局外的火险计划量仍未完成，月度模型也未证明每驻点并发或详细排班。大修、夜间保护、扑救、计划燃烧和行政工作未纳入。57与62是所列假设下的规划结果，不是公园真实最低编制。完整敏感性与评价由第四、五题讨论。

\FloatBarrier
@REFERENCES@
'''
