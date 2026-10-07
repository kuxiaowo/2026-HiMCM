"""Rename the current English manuscript's weighted completion metric.

Model values and internal result keys are preserved. This revision is compiled
without subsequent PDF/layout validation, as explicitly requested by the user.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import zipfile

import build_full_paper_figures as figures

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'docs/paper/full_paper.tex'
OUT=ROOT/'output/full_paper'


def main():
    text=SOURCE.read_text(encoding='utf-8')
    assert '% EFFECTIVE_INSPECTION_RATE_20261006' not in text
    history=OUT/'history/before_effective_inspection_rate_20261006.zip'
    with zipfile.ZipFile(history,'x',zipfile.ZIP_DEFLATED) as archive:
        for relative in ['docs/paper/full_paper.tex','output/pdf/full_paper.pdf',
                         'output/full_paper/full_paper_manifest.json',
                         'output/full_paper/full_paper_validation.json',
                         'output/full_paper/full_paper_layout_validation.json']:
            archive.write(ROOT/relative,relative)
        for name in ['fig1_framework_pipeline','fig4_monthly_workload','fig5_resource_joint']:
            for extension in ['tikz','png','svg']:
                p=ROOT/f'output/full_paper/figures/{name}.{extension}'
                archive.write(p,p.relative_to(ROOT))

    replacements={
      'The score measures inspection service, not wildlife survival.':
        r'The Effective Inspection Completion Rate measures prescribed inspections completed with timely ground response, weighted by conservation priorities; it does not measure wildlife survival.',
      r'The best score is \textbf{57.26} out of 100;':
        r'The maximum effective inspection completion rate is \textbf{57.26\%};',
      r'raises the score to \textbf{64.27}':r'raises the rate to \textbf{64.27\%}',
      'change the scoring scale':'change the priority-weighted percentage',
      'We combine these completion levels using normalized importance weights to produce a score from 0 to 100. This score measures delivery of the selected tasks, rather than wildlife survival or a measured reduction in ecological losses.':
        r'We combine these completion levels using normalized importance weights to obtain the Effective Inspection Completion Rate, expressed from 0 to 100\%. It measures completion of prescribed inspections with timely ground response; wildlife survival and ecological losses require separate evidence.',
      'The baseline reaches 57.26 points.':r'The baseline effective inspection completion rate is 57.26\%.',
      'raises the score to 64.27':r'raises the completion rate to 64.27\%',
      "The service score measures weighted completion with ground response, separately from ecological outcomes.":
        'The Effective Inspection Completion Rate measures prescribed inspections completed with timely ground response, weighted by conservation priorities. It is separate from ecological outcomes and area coverage.',
      'regional animal score':'regional animal-priority measure',
      r'\subsection{What the service score measures}':r'\subsection{What effective inspection completion measures}',
      r'giving the same weighted score. With fixed weights, increasing $P$ reduces unmet weighted demand $L$. An area service rate and a demand-weighted park score answer different questions and should be reported separately.':
        r'giving the same Effective Inspection Completion Rate $P$. Here $P$ is reported in percent: $P=57.26$ means 57.26\%. With fixed weights, increasing $P$ reduces unmet weighted demand $L$. This priority-weighted rate differs from an area completion rate and does not measure the proportion of animals protected.',
      'excess inspections cannot produce unlimited scores':'excess inspections cannot raise the completion rate above 100\%',
      'After maximizing the score':'After maximizing the effective inspection completion rate',
      'equal-score service patterns':'equal-rate inspection patterns',
      'The score is 57.26.':r'The effective inspection completion rate is 57.26\%.',
      'Its current score coefficient is zero':'Its current objective weight is zero',
      'Equal-score service choices':'Equal-rate inspection choices',
      'without changing the park score':'without changing the park completion rate',
      'the geographic score bound':'the geographic upper bound on effective inspection completion',
      'The 57.26 score is demand-weighted, not an area percentage.':
        r'The 57.26\% effective inspection completion rate uses priority weights; the 34.12\% figure measures response-eligible area.',
      r'\caption{Scores under equal budgets and service rules.}':
        r'\caption{Effective inspection completion rates (\%) under equal budgets and service rules.}',
      'provides no score advantage for optimization':'provides no completion-rate advantage for optimization',
      'Removing drones still achieves 57.26,':r'Removing drones still achieves 57.26\%,',
      r'Layout & Readiness (h) & Score & Total labor (h) & Flight (h)':
        r'Layout & Readiness (h) & Rate (\%) & Total labor (h) & Flight (h)',
      'improves the score by 7.01 points':'improves the completion rate by 7.01 percentage points',
      r'The target is its achieved optimum, $\eta=57.26016128$;':
        r'The target is its achieved optimum of 57.26\%, using the unrounded percentage value $\eta=57.26016128$;',
      "they do not change the base score's meaning":"they do not change the base inspection completion rate's meaning",
      'Allowing the equal-score pattern to change':'Allowing the equal-rate pattern to change',
      '177-person score':r'Rate at 177 staff (\%)',
      'The geographic score ceiling remains 57.26':r'The geographic completion-rate ceiling remains 57.26\%',
      r'Reducing baseline personnel-hours by 40\% still gives 57.26.':
        r'Reducing baseline personnel-hours by 40\% still gives 57.26\% effective inspection completion.',
      'plotted as zero scores':'plotted as zero completion',
      '57 with 160 hours reach 56.97.':r'57 with 160 hours reach 56.97\%.',
      'reallocation reaches 57.24, compared with 57.14':r'reallocation reaches 57.24\%, compared with 57.14\%',
      'the gain from reallocation is 6.83 points':'the gain from reallocation is 6.83 percentage points',
      'the score ceilings are 35.76 and 64.69.':r'the completion-rate ceilings are 35.76\% and 64.69\%.',
      'three hours gives 80.64 under':r'three hours gives 80.64\% under',
      'own-weight scores from original-weight evaluation':'completion rates under each weight choice from evaluation using the original weights',
      r'\caption{Weight sensitivity: scores under each case\'s weights and a common baseline evaluation.}':
        r'\caption{Weight sensitivity: effective inspection completion (\%) under each weight choice and original-weight evaluation.}',
      r'Weight choice & Animal (\%) & Own score & Base score & Tight-budget base score':
        r'Weight choice & Animal (\%) & Own weights & Original weights & Tight budget',
      'a baseline score of 57.26.':r'a baseline completion rate of 57.26\%.',
      'fixed-baseline scores span only 29.86--29.88.':r'rates evaluated with the original weights span only 29.86--29.88\%.',
      'the score effect is small':'the completion-rate effect is small',
      'Tight-budget score losses stay below 0.002 points.':'Tight-budget completion-rate losses stay below 0.002 percentage points.',
      'Its service score also cannot':'Its effective inspection completion rate also cannot',
      'whose distribution is missing from the score':'whose distribution is missing from the weighted completion measure',
      'not a complete species-protection score':'not a complete evaluation of species protection',
      'The best inspection-service score under these conditions is 57.26 out of 100.':
        r'The highest effective inspection completion rate under these conditions is 57.26\%.',
      'The score describes completion of important tasks under the selected response rule.':
        'This rate combines task completion and ground-response eligibility using conservation-priority weights.',
      'a favorable service score':'a high inspection completion rate',
    }
    # Apostrophes in the caption are ordinary text, not TeX escapes.
    replacements[r"\caption{Weight sensitivity: scores under each case's weights and a common baseline evaluation.}"]=replacements.pop(r"\caption{Weight sensitivity: scores under each case\'s weights and a common baseline evaluation.}")
    missing=[]
    for old,new in replacements.items():
        if old not in text:missing.append(old)
        text=text.replace(old,new)
    if missing:raise ValueError('Unmatched authoring replacements: '+repr(missing))
    text=text.replace(r'g_j^{\mathrm{service}}',r'g_j^{\mathrm{eff}}')
    # The metric is a percentage value; optimization coefficients stay unchanged.
    text=text.replace(r'$w_j,s_j$ & Relative inspection importance and completion fraction. \\',
                      r'$w_j,s_j$ & Relative inspection importance and completion fraction. \\'+'\n'+
                      r'$P,\eta$ & Effective inspection completion rate and target, expressed in percent. \\')
    text=text.replace('Finer land-cover sampling changes forest shares by about $-0.002$ and $-0.056$ points.',
                      'Finer land-cover sampling changes forest shares by about $-0.002$ and $-0.056$ percentage points.')
    text=text.replace(r'\caption{Conditional land-inspection trials; not actual park staffing.}',
                      r'\caption{Conditional land-inspection trials; ceiling and target are percentages, not actual park staffing.}')
    # Refresh the figure labels in the source, plus their PNG/SVG/TikZ exports.
    q2=figures.read('output/question2/q2_results.json');q2in=figures.read('output/question2/q2_model_inputs.json')
    q3=figures.read('output/question3/q3_results.json');q4=figures.read('output/question4/q4_results.json')
    figures.pipeline(q2,q3);figures.monthly_workload(q3,q2in);figures.resource_joint(q4)
    for label,name in [('fig:workflow','fig1_framework_pipeline'),('fig:monthly','fig4_monthly_workload'),
                       ('fig:joint','fig5_resource_joint')]:
        pattern=r'\\begin\{figure\}\[!htbp\](?:(?!\\end\{figure\}).)*?\\label\{'+re.escape(label)+r'\}\s*\\end\{figure\}'
        match=re.search(pattern,text,re.S)
        if not match:raise ValueError(label)
        figure=match.group()
        tikz=(OUT/f'figures/{name}.tikz').read_text(encoding='utf-8').strip()
        figure=re.sub(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}',lambda m:tikz,figure,flags=re.S)
        text=text[:match.start()]+figure+text[match.end():]
    text=text.replace(r'\caption{Peak-month service under joint personnel and flight limits; each cell is reoptimized.}',
                      r'\caption{Peak-month effective inspection completion under joint personnel and flight limits; each cell is reoptimized.}')
    text=text.replace('% PRESENTATION_REVISION_20261006','% PRESENTATION_REVISION_20261006\n% EFFECTIVE_INSPECTION_RATE_20261006')
    # Disclose that earlier reviews remain historical rather than claiming that
    # this terminology-only PDF received a new visual audit.
    text=text.replace('Rendered pages were visually reviewed.',
                      'Earlier rendered versions were visually reviewed. The final terminology revision was compiled without a further PDF or layout audit at the team\'s request.')
    SOURCE.write_text(text,encoding='utf-8')
    manifest_path=OUT/'full_paper_manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest.update(status='terminology_revision_pending_compilation',
                    source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    metric_name='Effective Inspection Completion Rate',metric_display_unit='percent',
                    numerical_model_changed=False,post_compile_validation='omitted_at_explicit_user_request',
                    previous_verified_pages=manifest.get('actual_total_pages'),actual_total_pages=None,
                    revision_history=str(history.relative_to(ROOT)),
                    revised_at_utc=datetime.now(timezone.utc).isoformat())
    for stale in ['pdf_sha256','letter_pages_actual','references_page','AI_report_page']:
        manifest.pop(stale,None)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fig_manifest_path=OUT/'figures/figure_manifest.json'
    m=json.loads(fig_manifest_path.read_text(encoding='utf-8'))
    updated={row['name']:row for row in figures.FIGURES}
    m['figures']=[updated.get(row['name'],row) for row in m['figures']]
    m['metric_name']='Effective Inspection Completion Rate'
    m['builder_sha256']=hashlib.sha256((ROOT/'scripts/modeling/build_full_paper_figures.py').read_bytes()).hexdigest()
    m['visual_review']={'status':'not_repeated_at_user_request','previous_revision_review':'historical'}
    fig_manifest_path.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    print('English manuscript, percentage expressions and three figure exports updated; model values unchanged.')


if __name__=='__main__':main()
