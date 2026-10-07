"""Apply the user-requested introduction and concise captions in the existing source.

Explanations are integrated into nearby prose; numeric tables, equations, TikZ
geometry and model outputs are preserved. This script is applied once only.
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/full_paper/caption_revision_20261007'
SOURCE = ROOT / 'docs/paper/full_paper.tex'
MARKER = '% USER_SHORT_CAPTIONS_20261007'
FLOAT = re.compile(r'\\begin\{(figure|table)\}.*?\\end\{\1\}', re.S)
CAP = re.compile(r'\\caption\{([^\n]+)\}')

TITLES = {
    'fig:workflow': 'Overview of the data, models, checks and recommendations.',
    'tab:terms': 'Main symbols and units used in the protection-planning model.',
    'tab:priorities': 'Conservation priorities used to define the Etosha inspection tasks.',
    'tab:parameters': 'Baseline operating assumptions for the Etosha allocation model.',
    'fig:etosha': 'Regional responsibility and response-supported area service in Etosha.',
    'fig:costs': r'Modeled personnel-hours for ground and drone-assisted inspection at ENP1\_0000.',
    'fig:deployment': "Monthly monitoring-support personnel-hours and drone flight-hours across Etosha's 17 reporting regions.",
    'tab:regions': 'Regional demand, response reach and minimum-labor allocation at the optimal completion rate.',
    'tab:comparison': 'Completion rates under uniform, demand-based and optimized allocation with identical budgets.',
    'tab:forward': 'Additional response-post candidates tested within the original resource budgets.',
    'tab:season': 'Seasonal visit frequencies and extra fire checks under the medium service rules.',
    'tab:water': 'Monthly maintenance workloads for the 17 historical boreholes under three service rules.',
    'fig:monthly': 'Monthly workload by task for maintaining the baseline inspection target.',
    'tab:monthly': 'Minimum monthly workload and personnel equivalents under the medium seasonal rules.',
    'tab:standards': 'Peak personnel requirements under alternative seasonal and drought-maintenance rules.',
    'fig:joint': 'Peak-month completion rates under joint personnel and drone-flight budgets.',
    'tab:protocol': 'Technology allocation under alternative drone-efficiency and minimum-ground-share assumptions.',
    'tab:grid': 'Sensitivity of completion rates and workload to inspection-grid size.',
    'tab:weights': 'Allocation scores under alternative responsibility weights and the common reference weights.',
    'tab:limits': 'Operational limitations and the evidence required for field validation.',
    'fig:transfer': 'Published geography and candidate response posts for Chitwan and Yellowstone.',
    'tab:transferdata': 'Spatial inputs used in the Chitwan and Yellowstone land-inspection trials.',
    'tab:transfercases': 'Conditional land-inspection workloads under local speed and response-post scenarios.',
    'tab:wolf': 'Yellowstone historical-priority scenarios with roads and inspection tasks held fixed.',
}


def once(text, old, new):
    assert text.count(old) == 1, (old[:90], text.count(old))
    return text.replace(old, new, 1)


def signatures(text):
    return {re.search(r'\\label\{([^}]+)\}', m[0])[1]:
            hashlib.sha256(CAP.sub('', m[0]).encode()).hexdigest()
            for m in FLOAT.finditer(text)}


def main():
    before = SOURCE.read_text(encoding='utf-8')
    assert MARKER not in before, 'Already applied; edit the current source incrementally.'
    OUT.mkdir(parents=True, exist_ok=True)
    backup = OUT / 'before_caption_revision.zip'
    assert not backup.exists(), 'Preserve the existing backup.'
    with zipfile.ZipFile(backup, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in ['docs/paper/full_paper.tex', 'output/pdf/skill_checked_20261007/full_paper.pdf',
                     'output/full_paper/full_paper_manifest.json', 'output/full_paper/full_paper_validation.json',
                     'output/full_paper/revision_visual_review.json']:
            z.write(ROOT / name, name)

    text = before
    start = text.index(r'\section{Introduction}') + len(r'\section{Introduction}')
    end = text.index(r'\begin{figure}', start)
    introduction = r'''
Large wildlife reserves are difficult to protect because important areas are spread over a very large space, while staff, equipment and travel time are limited. Observations are useful only when qualified teams can reach the location and respond in time. We use Etosha National Park as our main case, with a reported area of about 22,935 km$^2$ and a supplied workforce reference of 295 employees \cite{problem}. We ask how different areas should be prioritized, how ground teams and drones should be allocated, and whether the same service level can be maintained when seasonal work increases.

Our model divides the park into planning units and combines historical animal data, burnable habitat and mapped access with inspection tasks. An inspection receives effective-service credit when its required screening is completed and a ground team can arrive within two hours. The Effective Inspection Completion Rate measures the weighted inspection work supported in this way. It does not directly represent wildlife survival or continuous coverage of the whole park. Six surveyed animal groups enter the quantitative model; missing species and current animal distributions still require field data.

We build a two-stage linear programming model. The first stage finds the highest completion rate under the stated constraints, and the second minimizes personnel-hours while preserving that rate. For seasonal work, we add fire screening and maintenance of 17 historical boreholes. Personnel requirements are estimated from workload using 120 effective working hours per person per month. We vary resources, inspection rules, grid size and weights to examine how the assumptions affect the result. For Chitwan and Yellowstone, we rebuild local geography and priorities instead of directly copying Etosha's staffing results.

Under the baseline setting, completion reaches 57.26\%, using 5286.11 personnel-hours and 144.34 flight-hours. Resources remain unused, so the main constraint is response access rather than the total amount of staff or drones. The busiest normal seasonal period requires 57 personnel equivalents; the drought-maintenance scenario requires 62. These task-based estimates are not the park's exact staffing needs. Figure~\ref{fig:workflow} gives an overview of the data, models, checks and recommendations.

'''
    text = text[:start] + introduction + text[end:]

    replacements = [
        (r'Table~\ref{tab:terms} distinguishes spatial units, completion and the two resource budgets. Service measures checklist work supported by response, independently of ecological outcomes.',
         r'Table~\ref{tab:terms} distinguishes reporting regions, local inspection units and months. Normalized weights represent responsibility, while completion records checklist work supported by ground response. Personnel-hours and flight-hours remain separate: drone operation also consumes personnel work, and response readiness is counted once for the park.'),
        (r'Table~\ref{tab:priorities} ranks concerns using threat evidence, potential loss, affected extent and the possibility of intervention. They are management judgments rather than a measured ranking of incident probabilities.',
         r'Table~\ref{tab:priorities} ranks concerns using threat evidence, potential loss, affected extent and opportunities for intervention. Illegal entry and poaching lead to animal-monitoring and response tasks; harmful fire and habitat disturbance lead to habitat-monitoring tasks. The ranking is a management judgment, rather than measured incident probabilities or an exhaustive risk inventory.'),
        (r'Table~\ref{tab:parameters} states the settings. Six sourced locations are assumed response posts; monthly availability does not require a fixed fraction of employees on duty simultaneously.',
         r'Table~\ref{tab:parameters} states the operating assumptions. Speeds convert mapped routes into costs and response times; checklist, endurance and openness rules determine where drones can be used. Six sourced locations are assumed response posts. Monthly availability does not mean a fixed fraction of employees must be on duty simultaneously.'),
        ('Outside-survey animal responsibility remains unknown; zero measured coefficients and zero salt-pan fuel do not imply zero ecological value.',
         r'In Figure~\ref{fig:etosha}, the demand panel uses historical animal responsibility, burnable habitat and potential entry access; the service panel shows area-weighted completion from the same 599 units. Stars mark the assumed response posts, and red points fail the two-hour response rule. Priority-weighted completion and area service have different denominators. Outside-survey animal responsibility remains unknown; zero measured coefficients and zero salt-pan fuel do not imply zero ecological value.'),
        (r'Figure~\ref{fig:costs} compares work for one example check.',
         r'Figure~\ref{fig:costs} compares an example check at ENP1\_0000: ground screening takes 4.981 personnel-hours, while the drone-assisted task takes 4.271 personnel-hours and 0.206 flight-hours. The segments separate travel, walking, observation or flight, and preparation. The saving replaces off-road walking; both tasks retain transport and human involvement. These are modeled costs, so checklist equivalence still needs field testing.'),
        (r'HiGHS solves 1797 variables; independent checks verify capacity, budgets, floors and prohibited allocations. Figure~\ref{fig:deployment} maps all regions, and Table~\ref{tab:regions} supplies their numerical totals. ENP9 has no qualified response unit, while ENP11 combines substantial demand with almost no reachable area.',
         r'''HiGHS solves 1797 variables; independent checks verify capacity, budgets, floors and prohibited allocations. Figure~\ref{fig:deployment} maps monitoring-support labor and drone flight-hours across all 17 reporting regions. The two color scales are normalized independently, so matching colors do not mean equal resource quantities.

Numeric labels identify ENP regions; 3410 is the combined survey unit, P is the main pan and O denotes survey-external areas. Leaders connect displaced labels to their regions. The six stars mark assumed response posts, each reserving 480 personnel-hours outside the regional shading. The maps show pooled monthly work, rather than where employees or aircraft are permanently stationed.'''),
        (r'Table~\ref{tab:comparison} compares equal-budget rules before considering new response sites.',
         r'Table~\ref{tab:comparison} compares the three rules under identical tasks, weights, response gates and budgets. All reach 57.26\% at the baseline and after a 40\% labor reduction. Under a separate 3600-hour stress budget, including 2880 readiness hours and 1200 flight-hours, their rates are 16.47\%, 19.87\% and 29.88\%. The advantage appears under scarcity; there is no baseline rate improvement to claim.'),
        (r'Table~\ref{tab:comparison} locates the advantage under scarcity. Removing drones still gives 57.26\%, at 6084.98 personnel-hours.',
         r'Removing drones still gives 57.26\%, at 6084.98 personnel-hours.'),
        (r'Table~\ref{tab:forward} compares additional posts, each adding 480 readiness hours within the same total budgets. Routes and response eligibility are recalculated, with demand weights fixed.',
         r'Table~\ref{tab:forward} compares three additional response-post candidates. Each adds 480 readiness hours within the original total budgets; routes, response eligibility and inspection costs are rebuilt, while weights stay fixed. This isolates the effect of improved response access without increasing the labor allowance.'),
        (r'ENP5 is best among three candidates, adding 7.01 percentage points; it is not a global siting optimum. Verify facilities and access before adoption.',
         r'ENP5 raises completion from 57.26\% to 64.27\%, using 6202.08 personnel-hours. Its 7.01-point gain is the largest among the three candidates, rather than a global siting optimum. Facilities, permissions and access need verification before adoption.'),
        (r'Table~\ref{tab:season} gives the assumed frequencies.',
         r'Table~\ref{tab:season} gives the assumed frequencies. Wet months use two maintenance visits per point and dry months use four; extra fire screening rises from zero to two and then four checks per 100 km$^2$ of burnable habitat. November combines wet maintenance with the late-fire rule. These additional tasks use the shared resources without redefining the base inspection score.'),
        (r'Figure~\ref{fig:monthly} separates monthly work. The maximum, rather than the sum, estimates a constant workforce meeting the busiest month\'s pooled workload.',
         r'Figure~\ref{fig:monthly} separates response readiness, basic inspection support, extra fire checks and borehole maintenance. The reference capacity of 177 people is outside the plotted workload scale. The maximum monthly requirement, rather than the sum of monthly headcounts, estimates a constant workforce for the busiest month.'),
        (r'Different seasonal rules alter the prescribed service. Fewer personnel under a relaxed rule do not establish equal ecological protection.',
         r'The low, medium and high rules require normal peak equivalents of 51, 57 and 71; their drought-maintenance counterparts require 53, 62 and 77. These are consequences of prescribed visit and screening frequencies, rather than forecasts or confidence limits. Fewer personnel under a relaxed rule do not establish equal ecological protection.'),
        (r'All 127 feasible saved solutions pass independent checks; four infeasible cases are excluded rather than plotted as zero completion.',
         r'All 127 feasible saved solutions pass independent checks; four infeasible cases are excluded rather than plotted as zero completion. Matrix rows specify personnel at 120 effective hours each, and columns specify flight-hours. Each cell is reoptimized for the same medium peak-month tasks, including mandatory maintenance and extra fire screening.'),
        (r'Protocol changes in Table~\ref{tab:protocol} restore ground screening while the ample-budget completion rate remains geographically limited.',
         r'At 75\% drone efficiency, ground screening returns at 1731.55 personnel-hours and total work rises to 5786.37. A 25\% ground-check requirement uses 801.56 ground hours and 5486.15 total hours. All tested protocols still reach 57.26\% with ample budgets. Thus zero baseline ground screening depends on checklist equivalence; operators and responders remain necessary.'),
        (r'Table~\ref{tab:grid} changes only grid size while retaining the area-based task density.',
         r'Table~\ref{tab:grid} changes grid size while holding area-based task density, budgets and response rules fixed. The 5, 10 and 15 km grids contain 1554, 599 and 392 connected units. Refinement changes representative locations without creating extra aggregate check demand.'),
        ('Representative locations and response eligibility cause discretization sensitivity; this is not a statistical confidence interval.',
         r'The three grids yield 56.39\%, 57.26\% and 59.99\% completion. Relative to the baseline, the finer result is 0.87 points lower and the coarser result is 2.73 points higher. Differences arise from representative locations and response qualification near the deadline, rather than statistical sampling uncertainty.'),
        (r'Table~\ref{tab:weights} distinguishes completion rates under each weight choice from evaluation using the original weights.',
         r'Table~\ref{tab:weights} separates each plan\'s own-weight score from its score under the original entropy weights. At the ample baseline, all four allocations are identical and original-weight completion stays at 57.26\%, despite changes in the scoring scale. This common evaluation prevents a changed definition of importance from being read as improved service.'),
        (r'Figure~\ref{fig:transfer} locates the spatial inputs; Table~\ref{tab:transferdata} summarizes their published boundaries, roads and WorldCover 2021 classification. It assigns land-area weights $w_j=A_j^{\mathrm{land}}/\sum_kA_k^{\mathrm{land}}$ and $C_j=8A_j^{\mathrm{land}}/100$. Drones are set to zero because authorization and task equivalence are not calibrated. These choices test spatial service, not a complete evaluation of species protection. The park trials impose the 15\% floor in each reachable cell because reporting regions are unavailable; Etosha retains regional floors. The safeguard scale is locally modified.',
         r'Figure~\ref{fig:transfer} shows the published geography and candidate response locations. Chitwan uses a public protected-area polygon, mapped roads and geographic anchors; Yellowstone uses NPS geography, public roads and station locations. Stars denote candidates for the trial, rather than observed staffing assignments. Metric projections support travel calculations, while local speeds, task times and permissions remain assumptions.'),
        ('Higher speed is a sensitivity assumption, not a driving recommendation.',
         r'At 20 km/h, both parks\' fixed targets exceed their new response ceilings, so adding people alone cannot meet the target. A third post expands response reach but adds readiness work. Higher speed is a sensitivity assumption, rather than a driving recommendation. These land-inspection trials do not determine actual park staffing.'),
        (r'Table~\ref{tab:wolf} uses $w_j^{(\lambda)}=(1-\lambda)w_j^{\mathrm{land}}+\lambda w_j^{\mathrm{hist}}$, preserving Y0\'s new-weight score. At a 50\% historical share, 61 units change, labor is 1474.68 hours, and land-weight service falls from 16.85\% to 15.12\%. These are historical priority trade-offs, not ecological gains \cite{wolf}. The adjacent appendix gives the full comparison.',
         r'''The NPS 2022 wolf-pack activity files contain ten published records and nine distinct geometries. Their clipped union covers 4093.87 km$^2$; it describes historical activity extent, rather than current density, measured threat or official management priorities \cite{wolf}.

Table~\ref{tab:wolf} mixes normalized historical overlap, adjusted by existing cell land fraction, with land-area responsibility: $w_j^{(\lambda)}=(1-\lambda)w_j^{\mathrm{land}}+\lambda w_j^{\mathrm{hist}}$. Each trial preserves Y0's score under its new weights and minimizes labor with roads, tasks and service floors unchanged. At a 50\% historical share, 61 units change, labor is 1474.68 hours, and land-weight service falls from 16.85\% to 15.12\%. This is a priority trade-off, rather than an ecological gain. The adjacent appendix gives the complete comparison.'''),
    ]
    # Python raw strings preserve TeX; ordinary apostrophes are not TeX escapes.
    for old, new in replacements:
        text = once(text, old.replace("\\'", "'"), new.replace("\\'", "'"))

    limitations = r'''Some species and facility records are historical and incomplete, so the responsibilities we can measure are limited. Checklist and cost assumptions affect how service completion is interpreted. Mapped roads do not guarantee legal or seasonal access, and total monthly working hours cannot ensure that qualified crews are available at every time. The 17-point maintenance sample may omit current facilities or repair tasks.

For these reasons, the calculated 57.26\% optimum and the 57 or 62 personnel equivalents do not establish sufficient ecological protection or exact park staffing needs. Table~\ref{tab:limits} links each limitation to its consequences and the evidence still needed. Independent mathematical checks confirm feasibility and numerical consistency within the specified model; incident, survey, habitat and field-work records are needed to evaluate real outcomes.'''
    text = once(text,
                r'Table~\ref{tab:limits} links model limitations to their consequences and the field evidence needed for operational use.',
                limitations)

    before_float = {
        'tab:regions': r'''Table~\ref{tab:regions} gives the regional totals. Demand uses priority weights; reach and service use area shares within each region. Monitoring labor excludes the shared 2880 readiness hours. ENP1 receives 487.89 support hours and 29.31 flight-hours, while ENP12 receives 385.64 support hours. ENP9 has no qualified response unit; ENP11 has almost no reachable area. The salt pan retains its service floor despite zero measured-component weight.''',
        'tab:transferdata': r'''Table~\ref{tab:transferdata} summarizes the boundaries, roads and WorldCover 2021 classification. The trials use land-area weights $w_j=A_j^{\mathrm{land}}/\sum_kA_k^{\mathrm{land}}$ and $C_j=8A_j^{\mathrm{land}}/100$. Drone investment is zero because authorization and task equivalence are not calibrated. The 15\% floor applies in each reachable cell where reporting regions are unavailable; Etosha keeps regional floors. This changes the safeguard scale locally, and tests land service rather than complete species protection.''',
    }
    after_float = {
        'tab:water': r'''Two regular visits per borehole require 211.17 personnel-hours monthly. The drought-maintenance rule assumes eight visits and one hour on site, giving 980.68 personnel-hours. Each visit is a separate round trip, so the calculation claims no combined-route savings; the increases reflect assumed service rules, rather than recorded faults or measured shortages.''',
    }
    old_captions = []
    def revise(m):
        block = m[0]
        key = re.search(r'\\label\{([^}]+)\}', block)[1]
        assert key in TITLES, key
        old = CAP.search(block)[1]
        short = TITLES[key]
        assert short.count('.') == 1 and short.endswith('.')
        block = CAP.sub(lambda _: r'\caption{' + short + '}', block)
        old_captions.append(dict(label=key, kind=m[1], before=old, after=short,
                                 explanation='integrated into adjacent manuscript prose'))
        prefix = before_float.get(key, '')
        suffix = after_float.get(key, '')
        return (prefix + '\n\n' if prefix else '') + block + ('\n\n' + suffix if suffix else '')
    text = FLOAT.sub(revise, text)
    text = text.replace('% FULL_SKILL_AUDIT_20261007', '% FULL_SKILL_AUDIT_20261007\n' + MARKER, 1)
    if MARKER not in text:
        text = text.replace(r'\begin{document}', MARKER + '\n' + r'\begin{document}', 1)
    assert len(old_captions) == 24
    assert signatures(before) == signatures(text), 'Figure geometry or table data changed'
    equations = lambda s: re.findall(r'\\begin\{equation\}.*?\\end\{equation\}', s, re.S)
    assert equations(before) == equations(text) and len(equations(text)) == 19
    labels = lambda s: re.findall(r'\\label\{([^}]+)\}', s)
    assert labels(before) == labels(text)
    SOURCE.write_text(text, encoding='utf-8')
    result = dict(user_authority='One concise sentence per caption; explanations in body, overriding generic 100--150 caption rule.',
                  source=SOURCE.relative_to(ROOT).as_posix(),
                  before_sha256=hashlib.sha256(before.encode()).hexdigest(),
                  after_sha256=hashlib.sha256(text.encode()).hexdigest(),
                  modified_captions=old_captions, tables_and_TikZ_unchanged=True,
                  all_19_numbered_equations_unchanged=True, labels_unchanged=True,
                  previous_delivery='output/pdf/skill_checked_20261007/full_paper.pdf',
                  backup=backup.relative_to(ROOT).as_posix())
    (OUT / 'source_revision.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['source', 'after_sha256', 'tables_and_TikZ_unchanged', 'all_19_numbered_equations_unchanged']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
