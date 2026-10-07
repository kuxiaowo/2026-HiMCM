"""English manuscript pages; all numerical tokens are filled from saved results."""

BODY = r'''
% PAGE 1
\thispagestyle{fancy}
\begin{center}
{\fontsize{10}{12}\selectfont Team Control Number}\par
\vspace{2pt}
{\fontsize{18}{21.6}\selectfont\color{red}\TeamNumber}\par
\vspace{3pt}
{\fontsize{10}{12}\selectfont Problem Chosen}\par
{\fontsize{12}{14.4}\selectfont\color{red}Wildlife Protection}\par
{\fontsize{14}{16.8}\selectfont 2026}\par
{\fontsize{10}{12}\selectfont IM$^2$C}\par
{\fontsize{10}{12}\selectfont Summary Sheet}\par
\end{center}
\vspace{4pt}
\noindent\rule{\linewidth}{1.2pt}
\vspace{4pt}
\begin{center}
{\fontsize{14}{16.8}\selectfont Planning Wildlife Protection under Geographic and Resource Constraints}
\end{center}

Protecting a large reserve requires teams to reach important locations and turn observations into action. We develop a monthly planning framework for Etosha National Park that connects conservation priorities, inspection tasks, ground response, personnel and drones. A seasonal extension estimates the workforce needed to maintain a selected service level.

We use 17 reporting regions and @TARGETS@ smaller planning units. Historical animal surveys and burnable-habitat areas establish relative inspection priorities. Road routes determine travel time, and a two-hour ground-response limit determines where monitoring can receive effective follow-up. The service score measures weighted completion of prescribed inspections; it is not a survival rate or a measured reduction in wildlife losses.

The planning baseline makes 60\% of the problem's 295 reference employees available to these tasks: 177 person-months at 120 effective hours each, or \textbf{@H@} personnel-hours. Thirty proposed drones provide \textbf{@U@} flight-hours per month. The optimum score is \textbf{@SCORE@} out of 100. A representative allocation uses \textbf{@Q2_H@} personnel-hours, including response readiness, and \textbf{@Q2_U@} flight-hours. Unused resources show that the binding obstacle is the response layout. Among three additional-post candidates, the ENP5 candidate raises the score to \textbf{@FORWARD_SCORE@} under the same total resource limits.

Seasonal tasks add fire screening and maintenance of 17 historically documented boreholes. Maintaining the same target requires \textbf{@PEAK_N@} personnel in the busiest normal month and \textbf{@DROUGHT_N@} under the specified drought-maintenance scenario. These are conditional workload estimates, not the park's verified staffing requirement. The 177-person reference has ample monthly capacity, while @UNREACH_FIRE@ additional peak fire checks remain outside the assumed response range.

Sensitivity tests distinguish workload shortages from access gaps and show why the timing of visits matters. Adaptations for Chitwan in Asia and Yellowstone in North America use real spatial data with explicit operating assumptions. The Chitwan boundary fails an area-consistency check, so its results remain conditional polygon trials. We recommend validating travel, task effectiveness and response-post locations before adopting personnel recommendations.

\noindent\textbf{Keywords:} wildlife protection; resource allocation; ground response; seasonal workforce; Etosha National Park.
\clearpage

% PAGE 2
\begingroup
\titleformat{\section}{\centering\fontsize{22}{33}\selectfont\bfseries}{}{0pt}{}
\tableofcontents
\endgroup
\vfill
\noindent\textbf{Reading guide.} Sections 4--9 answer Questions 1--6. The letter uses nontechnical language. References and the AI-use report are included within this document's 24-page ceiling.
\clearpage

% PAGE 3
\section{Introduction}
Large reserves need inspections that can lead to timely action. Using Etosha as the starting case, we connect conservation priorities, travel routes and ground response to the allocation of personnel and drones. We then estimate seasonal workforce needs, test changing conditions and examine transfer to two other continents.

\section{Basic Assumptions and Justifications}
The following assumptions define a planning scenario rather than verified park operating rules.

\textbf{Assumption 1:} Work is pooled monthly, using 120 effective hours per person, 60\% personnel availability and 30 drones.

\textbf{Justification:} Declared limits permit comparable deployment tests; monthly feasibility does not prove a daily roster.

\textbf{Assumption 2:} Inspection demand and within-region responsibility are allocated by area, with equal fire exposure on burnable habitat.

\textbf{Justification:} Fine animal locations and multiyear harmful-fire exposure are unavailable; explicit proxies avoid inventing observations.

\textbf{Assumption 3:} Ground and drone teams complete the same checklist only where suitable; credited service needs ground arrival within two hours and shared teams handle infrequent alerts.

\textbf{Justification:} Observations require follow-up. Task equivalence, service standards and concurrency still need field calibration.

\section{Data Description and Symbol Definitions}
The problem gives an approximate area of 22,935 km$^2$; our projected boundary covers @AREA@ km$^2$. We use 2015 animal surveys, 2021 land cover and a fixed 2026 road snapshot \cite{problem,survey,worldcover,osm}, organized into 17 reporting regions and @TARGETS@ inspection units. A representative location supports route calculations, not continuous area coverage. Question 2 excludes water and rainfall; Question 3 separately adds fire screening and maintenance of 17 historical boreholes without forecasting populations or water-delivery volumes.

A personnel-hour is one person's work for one hour; a flight-hour is one aircraft's flight for one hour. The service score measures weighted completion with ground response, separately from ecological outcomes.

@TAB_TERMS@
\clearpage

% PAGE 4
\section{Protection Priorities and a Measurable Standard}
\subsection{Priorities and evidence}
Our provisional priorities use evidence of threats, potential loss, affected extent and the possibility of intervention. They are management judgments rather than a measured ranking of incident probabilities.

@TAB_PRIORITIES@

Human--wildlife conflict, disease, important plants and birds remain data needs. Missing information does not make them low-priority. Black rhinoceros remains a key conservation concern even though the current regional animal score lacks reliable spatial counts for that species. The six measured survey objects are blue wildebeest, plains zebra, giraffe, African savanna elephant, gemsbok and ostrich.

Historical abundance is first expressed as a regional share within each species. Legal protection categories then provide a basis for relative responsibility. This avoids treating a large number of common animals as automatically more important than a smaller priority population. Burnable grassland, shrubland and forest areas provide a separate habitat responsibility measure. Only a single fire-data sample was quality checked, so the base model assumes equal exposure per unit of burnable habitat rather than estimating a multiyear harmful-fire risk.

\subsection{What the service score measures}
A target receives effective service when prescribed screening is completed and a qualified ground team can arrive within the selected response limit. Let $d_j\in[0,1]$ describe screening completion and $r_j\in\{0,1\}$ describe response eligibility. For normalized demand weights $w_j$, define
\begin{equation}
g_j^{\mathrm{service}}=d_jr_j,\qquad
P=100\sum_jw_jg_j^{\mathrm{service}},\qquad
L=\sum_jw_j(1-g_j^{\mathrm{service}}).
\label{eq:protection}
\end{equation}
The allocation model represents effective completion directly by $s_j\le r_j$, giving the same weighted score. With fixed weights, increasing $P$ reduces unmet weighted demand $L$. An area service rate and a demand-weighted park score answer different questions and should be reported separately.

Actual protection needs independent evidence: illegal-loss records with comparable monitoring effort, population surveys, habitat condition and the impact of harmful fires. More detected incidents may reflect better detection. Prescribed burning is not automatically protection failure. A park average cannot certify missing species or replace their dedicated safeguards.
\clearpage

% PAGE 5
\section{Resource Allocation with Ground Teams and Drones}
\subsection{Planning units and resource assumptions}
The 15 survey regions, main salt pan and other survey-external areas form 17 reporting regions $\mathcal I$. A 10 km grid intersected with each region produces @TARGETS@ connected inspection units $\mathcal J$. Each has an interior representative location and support area $A_j$. The location is a route-planning proxy, not proof of continuous coverage of that area.

Six mapped locations serve as candidate response posts: Okaukuejo, Halali, Namutoni, Olifantsrus, Galton Gate and Nehale Gate. Their coordinates are sourced; their use as staffed response posts is assumed. We model monthly personnel availability, not a limit requiring a particular fraction of employees to be on duty simultaneously.

@TAB_PARAMETERS@

The two resource limits and shared response reservation are
\begin{equation}
\begin{aligned}
H&=295(0.60)(120)=@H@\ \text{personnel-hours/month},\\
U&=30(2)(20)=@U@\ \text{flight-hours/month},\\
H_0&=6(2)(8)(30)=2880\ \text{personnel-hours/month}.
\end{aligned}
\label{eq:budgets}
\end{equation}
The available inspection labor before task allocation is $H-H_0=@MOBILE_H@$ hours. Response readiness is charged once for the park. Staffing fractions, flight allowances and service standards are explicit planning assumptions; they are not verified operating rules at Etosha.
\clearpage

% PAGE 6
\subsection{Animal responsibility, habitat and access}
For species $m$, let $N_{im}$ be its surveyed abundance in region $i$, $q_{\ell(m)}$ its category weight, and $\mathcal I_S$ the 15 surveyed regions. Let $A_i^F$ denote burnable-habitat area. Define
\begin{equation}
V_i^A=\frac{\sum_m q_{\ell(m)}(N_{im}/\sum_{v\in\mathcal I_S}N_{vm})}{\sum_mq_{\ell(m)}},
\qquad V_i^F=\frac{A_i^F}{\sum_vA_v^F}.
\label{eq:values}
\end{equation}
Huntable, protected and specially protected categories use the team comparison matrix
\begin{equation}
\mathbf A=\begin{pmatrix}1&1/2&1/3\\2&1&1/2\\3&2&1\end{pmatrix},\qquad
\mathbf q=(0.163424,0.296961,0.539615)^{\mathsf T}.
\label{eq:ahp}
\end{equation}
The normalized principal eigenvector gives $\mathbf q$; $CR=0.007933<0.1$ checks consistency, not ecological truth. The law supplies categories, not these numerical comparisons \cite{law}.

For unit $j$, the shortest entry time from one of 27 road--boundary intersections is $T_j^E=D_j^E/v_g+d_j^\perp/v_w$. Its access index is $E_j=\exp(-T_j^E/2)$ with time in hours. These are potential access sources, not proven poacher entrances. Within a region, $\mu_j=A_j/A_i$ apportions responsibility by area: $R_j^A=V_i^A\mu_jE_j$ and $R_j^F=V_i^F\mu_j$.

@FIG_ETOSHA@

Animal responsibility is unknown outside the survey. Zero coefficients there mean exclusion from the measured-animal component, not zero animal value. The salt pan's zero fuel baseline also does not imply zero ecological value.
\clearpage

% PAGE 7
\subsection{Weights, routes and response eligibility}
We estimate the two component weights over the common 15-region scope. First aggregate $X_{ik}=\sum_{j\in\mathcal J_i}R_j^k$, then calculate
\begin{equation}
p_{ik}=\frac{X_{ik}}{\sum_vX_{vk}},\qquad
e_k=-\frac{\sum_i p_{ik}\ln p_{ik}}{\ln15},\qquad
\alpha_k=\frac{1-e_k}{(1-e_A)+(1-e_F)}.
\label{eq:entropy}
\end{equation}
With $0\ln0=0$, $e_A=0.881596$ and $e_F=0.934989$ give $\alpha_A=0.645551$ and $\alpha_F=0.354449$. Entropy weights express spatial differences in the chosen data, not observed loss shares. Each component is separately normalized over its observed scope, then $w_j=\alpha_Aw_j^A+\alpha_Fw_j^F$ and $W_i=\sum_{j\in\mathcal J_i}w_j$. Thus $\sum_jw_j=1$.

The directed road graph retains original connections and one-way restrictions. Outbound and return distances are calculated separately. A post qualifies only if its round trip is finite and
\begin{equation}
t_d+d_{bj}^+/v_g+d_j^\perp/v_w\le T_{\max};\qquad
r_j=\mathbf1\{\text{at least one qualifying post}\}.
\label{eq:response}
\end{equation}
We choose the qualifying post with the shortest road round trip $D_j=d_{b_j^*j}^++d_{jb_j^*}^-$. Response eligibility concerns the outbound journey; task cost also includes the return. Authorized use of candidate roads and straight-line off-road travel are assumptions requiring field checks.

\begin{equation}
\begin{aligned}
a_j&=n_g(D_j/v_g+2d_j^\perp/v_w+t_o+t_p),\\
b_j&=2d_j^\perp/v_u+t_o,\qquad
o_j=n_u(D_j/v_g+t_p+b_j),\qquad\gamma_j=o_j/b_j.
\end{aligned}
\label{eq:costs}
\end{equation}
Ground cost $a_j$ and drone-support cost $o_j$ are personnel-hours per check; $b_j$ is flight-hours per check. Drone use $h_j$ therefore consumes $\gamma_jh_j$ personnel-hours. Only response-eligible units meeting endurance and openness conditions enter $\mathcal J_U$.

@FIG_COSTS@
\clearpage

% PAGE 8
\subsection{Service capacity and the allocation model}
Decision variables are ground screening hours $x_j$, drone flight-hours $h_j$, and effective completion $s_j$. The prescribed monthly checks are based on area:
\begin{equation}
C_j=8A_j/100,\qquad\sum_jC_j=8\sum_jA_j/100.
\label{eq:checks}
\end{equation}
Areas are in km$^2$, giving @CHECKS@ prescribed checks per month. Refining the grid redistributes area without creating additional total demand. A completed check is a task at a representative location. Fractional checks describe planning intensity and require integer dispatches for implementation.

Define capacity coefficients $g_j=1/a_j$ for eligible ground tasks, otherwise zero; $u_j=1/b_j$ for eligible drone tasks, otherwise zero. Then $C_js_j\le g_jx_j+u_jh_j$. This avoids dividing by undefined costs and permits different checks to be shared between technologies without double-counting the same inspection.

For each region, $Q_i=\sum_{j\in\mathcal J_i}\mu_jr_j$ is reachable area share and $\bar s_i=\sum_{j\in\mathcal J_i}\mu_js_j$ is area-weighted completion. A common floor $\bar s_i\ge0.15Q_i$ protects basic service within the reachable part. If only 20\% of a region is reachable, the full-region floor is 3\%, not 15\%.

\begin{equation}
\boxed{\begin{aligned}
\max_{\mathbf x,\mathbf h,\mathbf s}\quad&100\sum_jw_js_j\\
\mathrm{s.t.}\quad&C_js_j\le g_jx_j+u_jh_j,&&j\in\mathcal J,\\
&\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j\le H-H_0,\\
&\sum_jh_j\le U,\\
&\sum_{j\in\mathcal J_i}\mu_js_j\ge0.15Q_i,&&i\in\mathcal I,\\
&0\le s_j\le r_j,\quad x_j,h_j\ge0,&&j\in\mathcal J,\\
&x_j=0\ (r_j=0),\quad h_j=0\ (j\notin\mathcal J_U).
\end{aligned}}
\label{eq:allocation}
\end{equation}
The fixed coefficients make this a linear program. Completion is capped at one so excess inspections cannot produce unlimited scores. Human and flight budgets have different units and are linked through operator labor, not added together.

Increasing completion by $\Delta s_j$ needs $C_ja_j\Delta s_j$ ground labor or $C_jo_j\Delta s_j$ drone-support labor plus $C_jb_j\Delta s_j$ flight time. Hence high demand alone does not determine allocation: workload, access and both budgets also matter.
\clearpage

% PAGE 9
\subsection{Solution checks and regional allocation}
HiGHS solves @VARIABLES@ variables. Independent checks recalculate task capacity, response and flight eligibility, both budgets, region floors and totals. Mathematical feasibility does not validate road permissions, observation effectiveness or an actual roster.

After maximizing the score, we fix the returned service vector $\mathbf s^{(1)}$ and minimize $H_M=\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j$. This selects the least labor supporting that particular service pattern. It does not search all equal-score service patterns for the global minimum workforce.

The score is @SCORE@. The selected representative uses @Q2_H@ personnel-hours and @Q2_U@ flight-hours, including 2880 response hours and @OPERATOR_H@ drone-support hours. Its ground screening hours are zero; ground operators and response staff are still essential.

@TAB_REGIONS@

Demand percentages are $100W_i$; reach and service percentages are $100Q_i$ and $100\bar s_i$. Regional labor excludes shared response readiness. ENP1 receives @ENP1_H@ screening-support hours. ENP11 has 8.05\% demand weight but only about 0.02\% reachable area. Additional ordinary inspection resources alone cannot remove this gap.

The salt pan's unknown animal value is not filled with zero. Its current score coefficient is zero, while its generic service floor still applies. Equal-score service choices there can change representative labor consumption without changing the park score.
\clearpage

% PAGE 10
\subsection{Strategic comparisons and response posts}
Since $w_j\ge0$ and $s_j\le r_j$, the geographic score bound is
\begin{equation}
P\le P_{\mathrm{geo}}=100\sum_jw_jr_j.
\label{eq:geocap}
\end{equation}
The base reaches this bound with @IDLE_H@ personnel-hours and @IDLE_U@ flight-hours unused. Of @TARGETS@ units, @REACHABLE@ meet the response standard, covering @REACH_SHARE@\% of projected area. The @SCORE@ score is demand-weighted, not an area percentage.

We compare the optimized allocation with uniform completion over reachable units and completion proportional to regional demand density $W_i/A_i$. Costs, resource limits and floors are identical.

@TAB_COMPARISON@

All three methods reach the bound even after a 40\% personnel-budget reduction. Thus this ample-resource comparison provides no score advantage for optimization. Removing drones still achieves @SCORE@, but the returned ground-only plan uses @NODRONE_H@ personnel-hours. Under equal team sizes and checklist times, drones replace slower off-road walking; this saves labor only where the task is technically suitable.

Each tested additional post adds 480 readiness hours within the same total budgets. Routes and response eligibility are recalculated, with demand weights fixed.

@TAB_FORWARD@

The ENP5 candidate improves the score by @FORWARD_GAIN@ points. It is best among three tested locations, not a global siting optimum. Verify access, permissions and operating conditions before treating the site as a recommendation.
\clearpage

% PAGE 11
\section{Seasonal Service and Workforce Requirements}
\subsection{Target, months and additional tasks}
Question 3 asks how service changes through time and how many people are needed to maintain a chosen level. We use the same weights, inspection standard, routes, response locations and technical eligibility as Question 2. The target is its achieved optimum, $\eta=@SCORE_FULL@$; its ecological sufficiency is not established by being mathematically optimal.

Each planning month has 30 days and 120 effective personnel-hours per person. Reference availability is 177 people and @U@ monthly flight-hours. Assignments may change between months. Existing equipment, operators and response staff cannot be charged twice for concurrent tasks.

The dry-season classification is May--October in the cited study; the official fire strategy distinguishes May--July and August--November operating windows \cite{season,fire}. These sources support the timing, not the numerical task frequencies. All frequencies below are team service rules.

@TAB_SEASON_RULES@

Extra fire checks are distinct tasks added to the base checklist. Let $A_j^{\mathrm{fuel}}$ be the unit's support area multiplied by its region's observed burnable-habitat fraction. Then
\begin{equation}
D_{jt}=k_t\frac{A_j^{\mathrm{fuel}}}{100}r_j.
\label{eq:firetasks}
\end{equation}
The same inspection protocol and cost coefficients apply. These are screening tasks, not firefighting or prescribed burning. The factor $r_j$ restricts credited tasks to the existing response range; excluded demand is separately recorded.

At the late-fire rate, @REACH_FIRE@ additional checks are supported inside that range, while @UNREACH_FIRE@ fall outside it. Adding personnel to the same six-post layout cannot guarantee those excluded tasks. We retain this gap rather than claiming park-wide fire coverage.
\clearpage

% PAGE 12
\subsection{Borehole maintenance as ground-only work}
A published 2013 field table contains 42 water-point records; 17 are classified as boreholes \cite{water}. We use those 17 mapped points as a historical maintenance sample. It is not a complete current operational inventory. Natural springs are not assigned pumping-equipment work. Ministry records support solar-powered borehole equipment and maintenance as relevant activities \cite{annual}.

Each visit includes a directed road round trip from a candidate post, any required walking, preparation and on-site inspection. We assume two people travel together. Let $T_\ell^{\mathrm{rt}}$ be elapsed round-trip travel time, $f_t$ visits per point and $\tau_t$ on-site time. Monthly personnel work is
\begin{equation}
a_{\ell t}^{W}=2(T_\ell^{\mathrm{rt}}+\tau_t+1/12),\qquad
W_t=f_t\sum_{\ell\in\mathcal L}a_{\ell t}^{W}.
\label{eq:water}
\end{equation}
The $1/12$ hour term is five minutes of preparation. Every route is independently returned; no travel saving is claimed from combining visits. Drone observation does not replace maintenance of physical equipment.

@TAB_WATER_RULES@

For the 17 points, summed elapsed round-trip travel is 42.87565 hours. The regular dry-month workload is
\begin{equation}
W_{\mathrm{dry}}=4(2)\left[42.87565+17(0.5+1/12)\right]
=@WATER_DRY@\ \text{personnel-hours}.
\label{eq:waterexample}
\end{equation}
Wet-month work is @WATER_WET@ hours; the specified drought-maintenance rule produces @WATER_DROUGHT@ hours. These increases are visit and task assumptions, not inferred water shortages or observed fault rates.

No water-hauling volumes, groundwater response or animal-population changes are modeled. Major repairs, emergency pumping, unlisted points and shared-route opportunities need an updated inventory and operational records. The longest modeled regular visit takes about 6.39 elapsed hours, but fitting an eight-hour day for one task does not prove a complete monthly roster.
\clearpage

% PAGE 13
\subsection{Shared monthly constraints}
For each unit and month, $(x_{jt},h_{jt},s_{jt})$ serve the base inspection protocol. Extra fire work uses ground hours $y_{jt}$ and flight-hours $v_{jt}$. These are separate task quantities with shared personnel and flight budgets. Where a technology is unavailable, its capacity term and investment are zero.

\begin{equation}
\begin{aligned}
C_js_{jt}&\le g_jx_{jt}+u_jh_{jt},\\
D_{jt}&\le g_jy_{jt}+u_jv_{jt},\\
\sum_j(h_{jt}+v_{jt})&\le U,\\
H_t&=H_0+W_t+\sum_j(x_{jt}+y_{jt})
+\sum_{j\in\mathcal J_U}\gamma_j(h_{jt}+v_{jt}).
\end{aligned}
\label{eq:monthlycapacity}
\end{equation}
The remaining conditions retain $0\le s_{jt}\le r_j$, nonnegative investments, technology eligibility and the regional floor
\begin{equation}
\sum_{j\in\mathcal J_i}\mu_js_{jt}\ge0.15\sum_{j\in\mathcal J_i}\mu_jr_j.
\label{eq:monthlyfloor}
\end{equation}
Only base inspections enter $P_t=100\sum_jw_js_{jt}$. Required fire and water tasks must also be completed; they do not change the base score's meaning. Readiness and maintenance are charged once, while operators serve both inspection types. Shared budgets prevent double allocation. Monthly totals support strategic planning; daily schedules, crew availability and simultaneous alerts still require checks. Thirty drones do not imply thirty simultaneous flights. Seasonal rules describe workload scenarios, not forecasts of animal abundance or drought.

@FIG_PIPELINE@
\clearpage

% PAGE 14
\subsection{Forward service and inverse workforce models}
Two uses of the same feasible task set answer different questions. With $N$ available people, the forward model finds the best monthly service. With a fixed service target, the inverse model finds the least total personnel work:
\begin{equation}
\begin{aligned}
P_t^*(N,U)&=\max_{\mathbf z_t\in\mathcal F_t(U),\ H_t\le120N}
100\sum_jw_js_{jt},\\
H_t^{\min}(\eta,U)&=\min_{\mathbf z_t\in\mathcal F_t(U),\ P_t\ge\eta}H_t.
\end{aligned}
\label{eq:forwardinverse}
\end{equation}
Here $\mathbf z_t$ collects all five variable blocks and $\mathcal F_t(U)$ contains the shared constraints. The inverse model removes the reference labor ceiling so that a shortage can be expressed as a required workforce instead of only returning infeasibility. It allows different equal-score service patterns, unlike the fixed-pattern refinement in Question 2.

\begin{equation}
N_t=\left\lceil\frac{H_t^{\min}}{120}\right\rceil,\qquad
N_{\mathrm{year}}=\max_{t=1,\ldots,12}N_t.
\label{eq:staff}
\end{equation}
The maximum, rather than the sum, estimates a constant workforce that meets the busiest month's pooled workload. It does not certify qualifications, exact simultaneous coverage or the completeness of the task inventory.

@FIG_MONTHLY@

With no added seasonal work and Question 2's returned service vector fixed, the calculation reproduces @Q2_H@ hours. Allowing the equal-score pattern to change gives @GLOBAL_Q2_H@ hours, a difference of @PATTERN_SAVING@. This comparison explains why dividing a single representative allocation by 120 need not yield the globally least personnel demand.
\clearpage

% PAGE 15
\subsection{Normal-season results and feasibility}
All months maintain the target with the 177-person reference and @U@ flight-hours. The least-work solutions need fewer personnel equivalents because only specified tasks and the existing response range are modeled.

@TAB_MONTHLY@

The peak occurs in August--October. Its work separates into four parts:
\begin{equation}
H_{\mathrm{peak}}^{\min}
=2880+@BASE_MONITOR@+@FIRE_LABOR@+@WATER_DRY@
=@PEAK_H@\ \text{personnel-hours}.
\label{eq:peak}
\end{equation}
These are readiness, base inspection labor, extra fire inspection labor and borehole maintenance. The flight requirement is @PEAK_U@ hours, well below @U@. Rounding $H_{\mathrm{peak}}^{\min}/120$ gives @PEAK_N@ people. A check with @ONE_LESS_N@ people returns @ONE_LESS_SCORE@, below the target, under the same monthly constraints.

This is a minimum for the selected workload and pooled model. It is not evidence that the real park can reduce its workforce to @PEAK_N@ or that 177 people are currently assigned to protection. The 60\% fraction is a resource scenario, and omitted threats, night service, specialist tasks and incident concurrency could change the required workforce.

Numeric checks independently recalculate each task's supported checks, prohibited allocations, both budgets, floors and aggregation. They confirm feasibility of the saved plans. Field calibration is a separate step: check actual task duration, travel permissions, maintenance status and whether drone and ground observations satisfy the same checklist.

The geographic score ceiling remains @SCORE@ throughout these months. Spare personnel capacity can meet extra tasks, but it cannot enlarge the fixed response range. A decision to raise the target above that ceiling first requires a change in access or response deployment.
\clearpage

% PAGE 16
\subsection{Drought work and service-standard sensitivity}
The abnormal-drought case increases maintenance visits during dry months from four to eight and on-site work from 0.5 to one hour. Timing is a defined workload scenario; it is not a forecast of drought, failures or rainfall. The peak becomes @DROUGHT_H@ hours, or @DROUGHT_N@ personnel equivalents, with @DROUGHT_U@ flight-hours.

The extra work relative to the normal peak is @DROUGHT_DELTA_H@ hours, mainly ground-only maintenance. The required workforce rises by @DROUGHT_DELTA_N@ people relative to the @PEAK_N@-person normal plan. Both remain below the 177-person reference; no additional personnel gap is inferred from that reference.

@TAB_SERVICE_STANDARDS@

The low, medium and high rules vary both visit requirements and extra fire checks. Their outcomes are planning alternatives, not confidence intervals. High service rules can use more flight-hours than the previous six-drone planning budget, while the current thirty-drone allowance supports these modeled tasks. A lower required headcount under a relaxed checklist must not be reported as unchanged ecological protection at lower cost.

\textbf{Operational interpretation.} Prepare workload and visit-date records before the busy months. Count response readiness and maintenance separately from screening. Verify whether a constant team can meet each month's work, then check daily task timing, training and specialist needs. Equipment inventory, available operator-hours and simultaneous flights are different quantities.

The historical 17-point sample is a material limitation. Replicating its workload tests sensitivity to inventory size, but does not establish additional point locations, routes or the actual number of functioning boreholes. Updating that inventory is more informative than adding unsupported water volumes to the equations.
\clearpage

% PAGE 17
\section{Sensitivity and Scenario Analysis}
The new baseline has ample resources: reducing its personnel budget by 40\% still gives @SCORE@. We also test explicitly lower personnel and equipment budgets, keeping weights and required tasks fixed. @Q4_AUDITED@ feasible saved solutions passed independent checks; four cases were infeasible and are not plotted as zero scores.

@FIG_JOINT@

At the medium peak, 57 people with 200 flight-hours maintain the target; 57 with 160 hours reach @N57_U160@. With no drones, the target needs @NO_UAV_N@ people. With 59 people and 120 flight-hours, reallocation reaches @N59_U120@, compared with @RETAIN_N59_U120@ under the retained spatial service rule. Under the specified drought-maintenance pressure at the same low budgets, the gain from reallocation is @DROUGHT_GAIN@ points, but the target is still missed.

Time arrangements also matter. The same 68 borehole visits and @WATER_DRY@ monthly personnel-hours give a maximum gap of 8 days under staggered dates, versus 27 days when visits are concentrated on days 1--4. Daily water-work peaks are @STAGGER_PEAK@ and @CLUSTER_PEAK@ hours. This water-only construction is not a full roster or proof of a strict 7.5-day rule.

Changing road speed from 30 to 20 km/h lowers the base score ceiling to @ROAD20_SCORE@; 40 km/h gives @ROAD40_SCORE@. A three-hour response rule gives @RESPONSE3_SCORE@, but allows later arrival and is a changed service standard. These comparisons are conditional scenarios, not measured operating-speed intervals or event probabilities.
\clearpage

% PAGE 18
\section{Strengths, Limitations and Practical Use}
\subsection{What the model supports}
The framework connects explicit tasks to their travel, observation and operator work. It distinguishes a lack of resources from locations that fail the response standard. Ground and drone inputs share personnel capacity while retaining a separate flight limit. The inverse model explains seasonal workforce changes without forecasting animal populations.

All inputs and saved allocations are traceable. Independent checks cover capacity, floors, prohibited technology use, budgets, response gates and totals. A second calculation reproduces the cross-park optimization results. These checks establish computational consistency; they do not establish measured ecological outcomes.

@TAB_LIMITATIONS@

\subsection{A practical calibration sequence}
First verify current priority-species and maintenance inventories. Then record actual travel, observation and response times, road permissions and equipment use. Compare ground and drone completion of the same checklist in suitable units. Check visit dates and simultaneous tasks after the monthly workload is feasible.

For implementation, preserve generic service floors and add dedicated safeguards for priority objects whose distribution is missing from the score. Use comparable ecological and incident records to test outcomes while controlling for observation effort. More data should revise task priorities and costs; it should not be used only to justify a previously chosen equipment count.
\clearpage

% PAGE 19
\section{Adaptation to Parks on Other Continents}
\subsection{Shared structure and local data}
We examine Chitwan National Park in Asia and Yellowstone National Park in North America. Priority setting, task capacity, response gates, readiness budgets and workforce conversion can remain. Species, habitats, seasonal routes, task protocols, permissions and operating costs must be rebuilt locally. Etosha's animal weights and thirty-drone assumption are not transferred.

The spatial trial uses published boundaries, mapped roads and candidate locations, and WorldCover 2021. It assigns land-area weights $w_j=A_j^{\mathrm{land}}/\sum_kA_k^{\mathrm{land}}$ and $C_j=8A_j^{\mathrm{land}}/100$. Drones are set to zero because authorization and task equivalence are not calibrated. These choices test spatial service, not a complete species-protection score.

@FIG_TRANSFER@

@TAB_TRANSFER_DATA@

\textbf{Boundary restriction.} The Chitwan polygon is @CHITWAN_AREA@ km$^2$, versus 952.63 km$^2$ in the official source: a 27.44\% difference. The published polygon is used only for a conditional trial; it is not accepted as the current legal park boundary. Yellowstone uses the NPS boundary. Both parks still need locally verified emergency access, off-road travel and task costs \cite{wdpca,npsdata,chitwan,unesco,npsrules}.
\clearpage

% PAGE 20
\subsection{Conditional trials and expected deployment changes}
For each park, fix its target at 90\% of its own two-post, 30 km/h response-limited ceiling:
\begin{equation}
P_{\mathrm{geo}}^{(p)}=100\sum_jw_j^{(p)}r_j^{(p)},\qquad
\eta^{(p)}=0.90P_{\mathrm{geo,base}}^{(p)}.
\label{eq:transfertarget}
\end{equation}
The target stays fixed when routes or speed change. It is not a 90-point whole-park target. Two-person teams, 120 hours/person-month, two-hour response and inspection times remain declared assumptions. A two-post readiness budget is 960 personnel-hours; a third post adds 480. Local incident response, community work and visitor management are not yet quantified in these personnel equivalents.

@TAB_TRANSFER_CASES@

Both 20 km/h scenarios place the fixed target above the resulting ceiling, so extra labor alone cannot meet it. Additional posts improve eligible area but also increase readiness work. Higher speed is a sensitivity setting, not permission to drive faster than safe operating conditions allow.

In Chitwan, forest screening, priority-species work, river crossings and monsoon access should shape ground-team tasks and seasonal posts. In Yellowstone, visitor--wildlife interactions, winter routes and specialist transport should change the task list and feasible travel graph. Seasonal closure data for visitors must not automatically be treated as emergency-staff permissions. Drone operations require local authorization.

Halving unit size changes the two ceilings by about $-0.13$ and $-0.20$ percentage points. Finer land-cover sampling changes forest shares by about $-0.002$ and $-0.056$ points. Ten numerical cases pass independent checks, while Chitwan's boundary-consistency check still fails. These workforce equivalents are neither actual staffing estimates nor grounds for comparing the parks' ecological condition.
\clearpage

% PAGE 21
\section*{Letter to IMMC}
\addcontentsline{toc}{section}{Letter to IMMC}
\noindent To the International Mission for Monitoring Conservation\\
\textbf{Subject: A practical protection plan for Etosha and other large reserves}

Dear IMMC Decision-Makers,

We recommend improving the connection between monitoring and ground response before adding further monitoring capacity. Our Etosha study shows that personnel and drones can remain unused while important locations are too far from a response team. Observations need qualified people who can reach the location and follow up.

Our approach divides the park into planning areas, identifies where inspections matter, and calculates the time needed to complete them. Historical animal surveys and burnable-habitat areas guide priorities. Travel routes and candidate response posts determine which checks can be supported. Ground teams and drone operators share a monthly work plan. Drones save walking time in suitable open locations; personnel still transport and operate them and investigate reported problems.

For planning, we make 60\% of the reference workforce of 295 available: the monthly working time of 177 people at 120 effective hours each. We assume thirty drones and require ground arrival within two hours. These are proposed resource conditions, not a verified account of current park staffing and equipment.

The best inspection-service score under these conditions is @SCORE@ out of 100. A representative month uses about @Q2_H_ROUND@ personnel-hours, including readiness, and @Q2_U_ROUND@ flight-hours. Both are well below the resource limits. The score describes completion of important tasks under the selected response rule. Wildlife losses, population health and habitat conditions need separate evaluation.

Three additional response-post candidates were compared within the same total budgets. The ENP5 candidate raises the score to @FORWARD_SCORE@ and performs best among those tested. It is a useful direction for field assessment, rather than a confirmed globally best location. Verify the routes, permissions, site conditions and actual response needs before adopting it.

Seasonal work also needs preparation. Additional fire checks and borehole maintenance raise the modeled normal peak requirement to @PEAK_N@ people. The specified drought-maintenance scenario raises it to @DROUGHT_N@. Both fit within the 177-person reference, but cover only the selected daytime tasks, response range and historical maintenance sample.
\clearpage

% PAGE 22
Our proposed first step is a limited field trial. Record travel time, inspection duration, drone use and follow-up time. Check whether ground and drone-assisted teams complete the same checklist reliably. Update the maintenance inventory and verify road access. These records can replace broad assumptions and show where a different vehicle, route or response location is more useful.

The monthly plan must then become a practical calendar. The same number of borehole visits can leave long gaps if concentrated early in the month. Stagger visits, check daily capacity and retain qualified response staff. Thirty drones in the inventory do not mean thirty simultaneous flights. Operators, readiness and maintenance need their own time allocations.

We also tested adaptation in Chitwan and Yellowstone using real spatial records and explicit operating assumptions. The same task-and-response structure can be retained, while local conservation priorities, travel conditions, service tasks and technology permissions must change. Chitwan's published boundary does not agree with the official reported area, so its numerical trial cannot yet support a legal-park staffing recommendation. In Yellowstone, visitor interactions and winter access require specialized task and route information. Neither park's actual personnel requirement has been established by these preliminary trials.

Important uncertainties remain at Etosha. Animal, habitat and road records come from different years. Detailed distributions are missing for some priority species, including black rhinoceros. We assume shared teams can handle occasional alerts without several serious incidents occurring together. Actual protection may require additional specialist and night work. A favorable service score cannot resolve these data gaps.

We propose three connected actions: validate field assumptions; examine response locations that could close important access gaps; and revise monthly assignments using verified records. Retain basic service in less prominent areas and dedicated safeguards for priority species. Measure progress through completed checks, reliable follow-up and independently observed wildlife and habitat outcomes.

Our central finding is that personnel, equipment and geography must be planned together. Better access to important locations can improve modeled service when the monthly flight allowance already has ample capacity. The framework offers a transparent starting point and a way to revise decisions as evidence improves.

Yours faithfully,\\[5pt]
The Modeling Team\\
Team \TeamNumber
\clearpage

% PAGE 23
@REFERENCES@
\clearpage

% PAGE 24
\begingroup
\titleformat{\section}{\fontsize{16}{24}\selectfont\bfseries}{}{0pt}{}
\section*{Report on Use of AI}
\endgroup
\addcontentsline{toc}{section}{Report on Use of AI}
\textbf{Tool and identification.} OpenAI Codex, based on the GPT-6 model family, was used in this work session \cite{codex}. The exact deployed model version was not exposed in the session metadata. Python/SciPy and XeLaTeX performed numerical optimization and document compilation; those outputs were checked separately from generated prose.

\textbf{Uses.} The assistant helped explain existing formulas, distinguish sourced records from planning assumptions, revise resource parameters specified by the team, synchronize seasonal calculations, shorten chapter drafts, translate the integrated manuscript into English, draft the nontechnical letter and produce numbered figures and tables. Parallel assistants worked on bounded chapter, data-synchronization and visualization tasks.

\textbf{Representative instructions.} The team requested: (1) explain each stage and formula in the existing Question 2 document; (2) keep other parameters unchanged, make 60\% of personnel available and use thirty drones, then shorten Question 2 to eight pages with simple terminology; (3) retrieve remote updates, revise Question 3 to six pages, revise Question 6 similarly, and integrate Questions 1--6, the template sections and a letter into an English paper of at most 24 pages. The team supplied the control number used here.

\textbf{Verification.} Reported Question 2--4 allocations were recomputed or checked against saved inputs and explicit constraints. The cross-park chapter uses the retrieved real-space results and retains its failed Chitwan boundary check. Scripts verify units, capacities, budgets, prohibitions, floors, totals, references, figure/table labels and final page count. Rendered pages were visually reviewed. A computational check is not a validation of real ecological outcomes or a detailed roster.

\textbf{Limits and responsibility.} Generated wording and model choices require team review. The manuscript identifies historical data, scenario assumptions and uncalibrated inputs; it makes no claim that AI supplied current animal distributions, verified staffing inventories, ecological-loss effects or authorized access permissions. Sources are cited separately from the team's calculations. The team remains responsible for accuracy, originality and compliance with the competition's disclosure rules.

The uploaded template's obsolete year, example notation, sample identifiers and unfinished claims were replaced with the current problem, confirmed team number and verified results. The project retains source data, model inputs, allocation arrays, code, provenance and numerical/layout audit records for review.
'''
