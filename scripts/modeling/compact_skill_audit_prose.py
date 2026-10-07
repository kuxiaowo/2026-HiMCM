"""Remove explanations duplicated by the new standalone captions; preserve mathematics."""
from pathlib import Path
import re,sys,shutil
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import revise_full_paper_presentation as presentation

REPLACEMENTS={
'Table~\\ref{tab:terms} defines':'Table~\\ref{tab:terms} distinguishes spatial units, completion and the two resource budgets. Service measures checklist work supported by response, independently of ecological outcomes.',
'Historical abundance is first':'Historical abundance is converted to within-species regional shares, then category preferences determine responsibility. Burnable-habitat area forms a separate component. Equal baseline fire exposure avoids extrapolating a single sample into multiyear harmful-fire risk.',
'The allocation model represents':'The allocation uses $s_j\\le r_j$ directly. With fixed weights, larger $P$ means less unmet weighted demand; $P=57.26$ denotes 57.26\\%, independently of area coverage or animals protected.',
'Table~\\ref{tab:parameters} gives':'Table~\\ref{tab:parameters} states the settings. Six sourced locations are assumed response posts; monthly availability does not require a fixed fraction of employees on duty simultaneously.',
'Animal responsibility is unknown':'Outside-survey animal responsibility remains unknown; zero measured coefficients and zero salt-pan fuel do not imply zero ecological value.',
'Demand percentages are':'Table~\\ref{tab:regions} reports $100W_i$, $100Q_i$ and $100\\bar s_i$ for demand, reach and service. Regional labor excludes shared readiness.',
'The salt pan\'s animal value':'The zero-weight salt pan retains its regional service floor; the second stage chooses its least-cost floor service.',
'Figure~\\ref{fig:deployment} locates':'Figure~\\ref{fig:deployment} maps every region from Table~\\ref{tab:regions}. ENP9 has no qualified response unit; ENP11 combines substantial demand with almost no reachable area. Monitoring support and aircraft time therefore follow response access as well as demand. These are monthly resource totals under assumed posts, not integer station assignments.',
'Table~\\ref{tab:comparison} shows':'Table~\\ref{tab:comparison} locates the advantage under scarcity. Removing drones still gives 57.26\\%, at 6084.98 personnel-hours. Equal crews and checklist times make suitable drone use save off-road walking rather than eliminate personnel.',
'The ENP5 candidate improves':'ENP5 is best among three candidates, adding 7.01 percentage points; it is not a global siting optimum. Verify facilities and access before adoption.',
'The $1/12$ hour term':'The $1/12$ preparation term is five minutes. Physical maintenance remains ground work. Table~\\ref{tab:water} compares the three rules.',
'Table~\\ref{tab:water} compares':'Summed round-trip travel is 42.87565 elapsed hours. The regular dry-month workload is',
'Wet-month work is':'The 211.17-hour wet and 980.68-hour drought workloads arise from prescribed visits and on-site work, not measured shortages.',
'No water-hauling volumes':'Major repairs, unlisted points and route-sharing need updated records. The longest visit takes about 6.39 elapsed hours; a single task fitting an eight-hour day does not prove a roster.',
'Only base inspections enter':'Only basic checks enter $P_t=100\\sum_jw_js_{jt}$. Required seasonal tasks use the same budgets without changing that score. Readiness is charged once; monthly feasibility still requires date, qualification and concurrent-alert checks.',
'This is a minimum for':'This is a task-specific monthly minimum, not an operational staffing recommendation. Specialist, night and simultaneous incident work are omitted.',
'Numeric checks independently':'Independent task-capacity, qualification, budget and floor checks verify the saved plans. Field costs, permissions and checklist effectiveness require separate calibration.',
'The geographic completion-rate ceiling remains':'Extra seasonal work uses spare capacity without expanding the fixed response range. Raising the basic target requires improved access or deployment.',
'The abnormal-drought case':'The drought-maintenance case doubles dry-month visits and on-site time. Its peak is 7390.17 personnel-hours, or 62 equivalents, with 210.61 flight-hours. Table~\\ref{tab:standards} compares alternative rules.',
'The extra work relative':'The 558.34-hour increase adds five personnel equivalents; both normal and drought requirements remain below the 177-person reference.',
'The rules in Table~\\ref{tab:standards}':'Different seasonal rules alter the prescribed service. Fewer personnel under a relaxed rule do not establish equal ecological protection.',
'At $e=0.75$':'Protocol changes in Table~\\ref{tab:protocol} restore ground screening while the ample-budget completion rate remains geographically limited.',
'In Table~\\ref{tab:grid}':'Representative locations and response eligibility cause discretization sensitivity; this is not a statistical confidence interval.',
'At 21240 personnel-hours, all four':'Under ample resources, the four rules satisfy all reachable positive-weight demand; only their scoring scales differ.',
'Begin implementation by verifying':'Field implementation should first verify response access and task durations, update maintenance records and compare ground/drone checklist effectiveness.',
'For implementation, preserve':'Retain regional floors and dedicated safeguards for missing priority objects. Validate outcomes with comparable incident and ecological records, controlling for monitoring effort.',
'Table~\\ref{tab:transfercases} compares':'Table~\\ref{tab:transfercases} holds each park\'s target fixed across trials. Two posts reserve 960 personnel-hours and a third adds 480. Unmeasured local incident, community and visitor tasks remain outside these equivalents.',
'Both 20 km/h scenarios':'Both 20 km/h trials become infeasible. A post changes access and readiness; a speed scenario does not authorize unsafe driving.',
'In Chitwan, forest screening':'Chitwan needs forest, river and community task calibration. Yellowstone needs visitor, winter and specialist-access data. Visitor closures cannot determine staff permissions; drones require local authorization.',
'At a 50\\% historical-use share':'The 50\\% scenario changes 61 units, retaining its new-weight target while reducing land-weight service. The result illustrates a local priority trade-off rather than ecological improvement; current species priorities and seasonal permissions still need calibration \\cite{npsrules}.',
}

def main():
    path=ROOT/'docs/paper/full_paper.tex';s=path.read_text(encoding='utf-8')
    assert '% SKILL_PROSE_COMPACT_20261007' not in s
    lines=s.splitlines()
    for start,value in REPLACEMENTS.items():
        ids=[i for i,line in enumerate(lines) if line.startswith(start)]
        assert len(ids)==1,(start,ids)
        lines[ids[0]]=value
    s='\n'.join(lines)+'\n'
    s=s.replace(r'\Needspace*{10\baselineskip}',r'\Needspace*{3\baselineskip}')
    # Put the existing map interpretation BEFORE its figure, providing actual
    # prose between the regional table and map and resolving the first reference.
    line=next(line for line in s.splitlines() if line.startswith(r'Figure~\ref{fig:deployment} maps'))
    s=s.replace(line+'\n','')
    m=next(m for m in re.finditer(r'\\begin\{figure\}.*?\\end\{figure\}',s,re.S) if r'\label{fig:deployment}' in m[0])
    s=s[:m.start()]+line+'\n\n'+s[m.start():]
    # Explicit references must precede their corresponding [H] float.
    leads={'tab:comparison':'Table~\\ref{tab:comparison} compares equal-budget rules before considering new response sites.',
           'tab:grid':'Table~\\ref{tab:grid} changes only grid size while retaining the area-based task density.'}
    for key,lead in leads.items():
        m=next(m for m in re.finditer(r'\\begin\{table\}.*?\\end\{table\}',s,re.S) if '\\label{'+key+'}' in m[0])
        s=s[:m.start()]+lead+'\n\n'+s[m.start():]
    # Complete objective + brace-enclosed original constraints, same equation ID.
    m=next(m for m in re.finditer(r'\\begin\{equation\}.*?\\end\{equation\}',s,re.S) if r'\label{eq:allocation}' in m[0])
    equation=r'''\begin{equation}
\begin{aligned}
\max_{\mathbf x,\mathbf h,\mathbf s}\quad &100\sum_jw_js_j\\
\mathrm{s.t.}\quad &\left\{\begin{aligned}
C_js_j&\le g_jx_j+u_jh_j, &&j\in\mathcal J,\\
\sum_jx_j+\sum_{j\in\mathcal J_U}\gamma_jh_j&\le H-H_0,\\
\sum_jh_j&\le U,\\
\sum_{j\in\mathcal J_i}\mu_js_j&\ge0.15Q_i, &&i\in\mathcal I,\\
0\le s_j&\le r_j, &&j\in\mathcal J,\\
x_j,h_j&\ge0, &&j\in\mathcal J,\\
x_j&=0, &&r_j=0,\\
h_j&=0, &&j\notin\mathcal J_U.
\end{aligned}\right.
\end{aligned}
\label{eq:allocation}
\end{equation}'''
    s=s[:m.start()]+equation+s[m.end():]
    s=s.replace('Figure~\\ref{fig:workflow} connects tasks and deployment. ','')
    a='These choices test spatial service, not a complete evaluation of species protection.'
    s=s.replace(a,a+' The park trials impose the 15\\% floor in each reachable cell because reporting regions are unavailable; Etosha retains regional floors. The safeguard scale is locally modified.')
    # Refresh the final map after the station-label collision fix.
    presentation.allocation_map(presentation.read('output/question2/q2_model_inputs.json'),presentation.read('output/question2/q2_results.json'))
    m=next(m for m in re.finditer(r'\\begin\{figure\}.*?\\end\{figure\}',s,re.S) if r'\label{fig:deployment}' in m[0]);b=m[0];a=b.index(r'\begin{tikzpicture}');z=b.index(r'\end{tikzpicture}')+len(r'\end{tikzpicture}');b=b[:a]+(ROOT/'output/full_paper/figures/fig7_optimal_resource_deployment.tikz').read_text(encoding='utf-8').strip()+b[z:];s=s[:m.start()]+b+s[m.end():]
    s=s.replace(r'\begin{document}','% SKILL_PROSE_COMPACT_20261007\n'+r'\begin{document}',1)
    path.write_text(s,encoding='utf-8',newline='\n')
    new=ROOT/'output/pdf/skill_checked_20261007';new.mkdir(parents=True,exist_ok=True)
    for p in (ROOT/'output/pdf/revision_20261006').glob('question*'):
        if p.is_file():shutil.copy2(p,new/p.name)
    print('Repeated explanations compacted; references moved before figures/tables; mathematical constraints unchanged.')

if __name__=='__main__':main()
