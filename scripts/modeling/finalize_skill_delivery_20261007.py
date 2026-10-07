"""Record the completed review and build a checked saved-input support archive.

This does not compile, edit the paper, or invent visual-review results. Every
review record must already match the current PDF fingerprint before packaging.
The final archive fingerprint is a sidecar, avoiding a self-referential hash.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / 'output/full_paper/skill_audit_20261007'
PDF_DIR = 'output/pdf/skill_checked_20261007'
ARCHIVE = AUDIT / 'review_support.zip'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, data):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def audit_path(name):
    return 'output/full_paper/skill_audit_20261007/' + name


def review_record(delivery):
    numeric = read(audit_path('numerical_data_audit.json'))
    layout = read(audit_path('english_layout_audit.json'))
    whitespace = read(audit_path('whitespace_audit.json'))
    code = read(audit_path('appendix_code_verification.json'))
    scanner = read(audit_path('raw_scanner_adjudication.json'))
    assert all(x['passed'] for x in [numeric, layout, whitespace, code])
    assert layout['pdf_sha256'] == sha(PDF_DIR + '/full_paper.pdf')
    assert scanner['raw_exit_code'] == 1 and scanner['all_adjudicated_as_same_figure_bands']
    assert len(scanner['remaining_raw_messages']) == 7
    for doc in delivery['documents'].values():
        assert sha(doc['source']) == doc['source_sha256']
        assert sha(doc['pdf']) == doc['pdf_sha256']
        assert doc['visual_review']['status'] == 'passed'
        assert doc['visual_review']['pdf_sha256'] == doc['pdf_sha256']
        assert doc['visual_review']['reviewed_pages'] == list(range(1, doc['pages'] + 1))

    # Scores reflect the completed internal review, not an automatic contest rank.
    rows = [
        ('方法选取', 4, '在条件性工作量规划范围内合理',
         '路网约束LP与逆向工作量问题相匹配；同预算均衡/需求对照已计算。替代方法是回顾性适用性比较，未伪称完成缺数据的轮班或概率实验。',
         [audit_path('modeling_doc.json'), 'output/question2/q2_results.json']),
        ('题目要求', 4, '六题与非技术信件均有可指认答案',
         '逐项对应章节4—9及第22页信。纸张、边距、普通文字字号和页数满足所核对题面；动物代理仅覆盖六类历史调查，迁移与现场执行仍明确附条件。',
         [audit_path('task_package.json'), 'output/full_paper/full_paper_validation.json']),
        ('谬误与矛盾', 4, '本轮发现的文稿和口径不一致已关闭',
         '前向最大分数与逆向最少人时一致；地面筛查与地面响应分别列账，Q2报告区底线与Q6单元底线明确区别；19式的量纲、界限及数值交叉核验通过。',
         [audit_path('numerical_data_audit.json'), 'output/full_paper/revision_delivery_validation.json']),
        ('数值合理性', 4, '在声明假设下约束与独立复算通过',
         '599个基准单元、84组季节复核、127个可行敏感性解及4个不可行案例、10个两园案例分别核验；有效工时固定120，人数按向上取整解释。参数并非实测。',
         ['output/question3/q3_independent_verification.json', 'output/question4/q4_independent_verification.json', 'output/question6/q6_verification.json']),
        ('创新性', 4, '有具体的检验设计贡献，未声称新算法',
         '贡献在验证设计：前向/逆向及可达权重解析上界互证；技术效率与最低地面任务反事实暴露协议敏感性；黄石历史生态权重改变后，仍用原陆域标准评价取舍。不是给常规LP改名。',
         ['output/revision_feasibility/20261006/revision_results.json', 'output/revision_feasibility/20261006/yellowstone_historical_priority_scenario.json']),
        ('图表位置', 5, '24个真实图表对象的引用距离检查通过',
         '全部7图17表有前置正文引用，首次引用在同页或相邻页；编号连续，无孤儿图表。说明长度采用原skill计数函数，均为100—150。',
         [audit_path('english_layout_audit.json')]),
        ('正文页数', 5, '按本题及用户页数规定合规',
         '主体解答18页，不超过题面20页；摘要、目录、主体和信合计21页，不超过题面24页；PDF共24页，不超过用户25页。skill通用21—30页目标服从本题上限。',
         ['output/full_paper/full_paper_validation.json', audit_path('style_contract.json')]),
        ('页面布局', 4, '逐页渲染与目视记录通过',
         '90页材料均已300dpi渲染，记录绑定当前指纹；英文中间主体页按90pt目标及4pt测量容差通过，独立结束页自然留白；长说明增加阅读密度，仍可继续做编辑性精炼。',
         ['output/full_paper/revision_visual_review.json', audit_path('whitespace_audit.json')]),
        ('图片乱码', 5, '三道检查无缺字或乱码迹象',
         '当前编译日志无Missing character/Glyph missing，PDF文本层无替换符或豆腐块，已审页图可读；交付字体均嵌入。',
         ['output/full_paper/revision_delivery_validation.json', 'output/full_paper/revision_visual_review.json']),
    ]
    dimensions = {name: dict(score=score, verdict=verdict, notes=notes, evidence=evidence)
                  for name, score, verdict, notes, evidence in rows}
    issues = [
        ('R01', '红线级', '题注10pt、符号表11pt低于题面普通文字12pt', '按用户本轮明确决定改为12pt；页眉和封面普通文字同步；保留正文与标题样式', ['output/full_paper/full_paper_validation.json', audit_path('style_contract.json')]),
        ('C01', '一致性级', '24条图表说明短于skill要求', '补充范围、来源、关键数值及解释，删重复正文；均100—150统计长度', [audit_path('english_layout_audit.json')]),
        ('C02', '一致性级', '资源地图仅显示四个区域名称，易被误读为部分配置', '完整标注17个报告区，3410/P/O另说明，移位标签加引线，星号解释六个固定候选响应点', ['output/full_paper/figures/deployment_figure_manifest.json', 'output/full_paper/revision_visual_review.json']),
        ('C03', '一致性级', '完整优化约束排版缺大括号', '将原LP约束等价排为大括号形式，没有改变计算目标或约束', ['docs/paper/full_paper.tex', audit_path('numerical_data_audit.json')]),
        ('C04', '一致性级', '迁移的区域/单元服务底线差异易混淆', '正文明确Q2按报告区、Q6按可达单元15%底线及适用原因', ['docs/paper/full_paper.tex', audit_path('modeling_doc.json')]),
        ('C05', '一致性级', '少数图表与首次引用距离不合适', '将现有相关解释前移并重排；全部真实对象检查为同页或相邻页', [audit_path('english_layout_audit.json')]),
        ('C06', '一致性级', '压缩段落时引入三个不匹配引用键', '统一成已有npsdata引用并重编译；源码与当前日志均无未定义引用', ['output/full_paper/revision_delivery_validation.json']),
        ('C07', '一致性级', '空白种群表项易被解释为真实不存在', '明确为没有记录的估计；保留源表质量标记，未把六类历史记录写成完整当前种群', [audit_path('numerical_data_audit.json'), 'docs/paper/full_paper.tex']),
        ('A01', '美观级', '部分正文中间页有大块留白，总体框架位置和画法不合适', '保留字号与行距重排；总体框架改为引言五层图，完整历史情景表移入相邻补充附录', [audit_path('whitespace_audit.json'), 'output/full_paper/revision_visual_review.json']),
        ('C08', '一致性级', '需能核对附录与交付代码是否为同一份', 'filecontents*内嵌真实复现入口，lstinputlisting载入；与交付.py逐字一致并已执行', [audit_path('appendix_code_verification.json')]),
        ('T01', '工具误报', '原扫描器把同一TikZ图拆成多个绘制带，仍返回7条图挨图', '原退出码1保留；逐条图对象归属与页图核对，增强检查保持原计数和面积阈值', [audit_path('original_layout_final.log'), audit_path('raw_scanner_adjudication.json'), audit_path('english_layout_audit.json')]),
    ]
    closed = [dict(id=i, level=l, discovered=d, action=a, evidence=e, status='closed_after_recheck')
              for i, l, d, a, e in issues]
    scores = {'题目合规': 4, '方法选取': 4, '模型正确性': 4, '数值合理性': 4,
              '创新性': 4, '可解释性': 5, '数据严谨': 4, '论文质量': 4, '版面布局': 4, '可视化': 5}
    extended_notes = {
        '可解释性': '容量、单位、响应门槛与任务成本有明确含义，假设和观测分开；服务完成率不写成存活率。',
        '数据严谨': '来源、版本、空白和质量标记保留，犀牛冲突不混入主输入；历史性和奇特旺面积未校准限制使此项不评满分。',
        '论文质量': '摘要按问题组织，题目与章节对应，重复和套话减少；人工编辑性判断无法保证任何AI检测器分数。',
        '可视化': '资源地图完整17区，图内标注12pt，字体、图例、独立颜色尺度及地图比例已核验。',
    }
    limits = [
        dict(id='L01', status='retained_external_limit', detail='六类2015调查及质量标记未被当前全物种调查取代；犀牛1107/1280源冲突仍排除主输入。'),
        dict(id='L02', status='retained_external_limit', detail='奇特旺发布多边形与952.63平方千米官方面积未闭合；投影仅约0.087%影响，具体错误边段未定位，试算保留条件性。'),
        dict(id='L03', status='retained_external_limit', detail='技术效率、检查频次、通行权限、设施现状和工时是待现场校准的规划条件；月人数不是轮班、并发响应或资格验证。'),
        dict(id='L04', status='retained_external_limit', detail='服务完成率及黄石2022历史范围情景未验证动物存活或实际生态改善；不认证当前法定规则的完整性。'),
        dict(id='L05', status='platform_limitation', detail='内置编译器仍报Unable to find standard directories for platform；保留编辑器，按用户已有授权使用本机XeLaTeX。'),
    ]
    report = dict(
        status='completed_internal_review', review_date_local='2026-10-07',
        reviewed_at_utc=datetime.now(timezone.utc).isoformat(),
        verdict='通过（已披露的条件性规划与文稿核验范围）',
        scope='Internal mathematical, numerical, source, manuscript and layout review; not contest ranking, field validation or ecological certification.',
        source='docs/paper/full_paper.tex', source_sha256=sha('docs/paper/full_paper.tex'),
        pdf=PDF_DIR + '/full_paper.pdf', pdf_sha256=sha(PDF_DIR + '/full_paper.pdf'),
        dimensions=dimensions, nine_dimension_total=sum(r[1] for r in rows), nine_dimension_max=45,
        score=scores, extended_score_notes=extended_notes, extended_total=sum(scores.values()), extended_max=50,
        issue_resolution=closed, open_redline_issues=0, open_consistency_issues=0,
        remaining_limits=limits, generic_skill_scanner=dict(
            raw_exit_code=1, remaining_raw_messages=7, English_reference_recognition='unsupported by original scanner',
            disposition='all seven are drawing bands inside the same figure; original exit code retained',
            evidence=[audit_path('original_layout_final.log'), audit_path('raw_scanner_adjudication.json')],
            original_checker_copy=audit_path('original_check_layout.py'), checker_sha256=sha(audit_path('original_check_layout.py'))),
        applicability_exceptions=[
            '用户指定的既有article及字体模板保留，不换国赛cumcmthesis类。',
            '原题主体最多20页，优先于skill通用主体21—30页目标；计入摘要、目录及信后为21页。',
            '定义/评价问题不机械增加五张冗余图；总体架构一张，实际数据图各有用途。',
            '无统计预测训练，CV/残差/训练泄露条款不适用；未虚构概率或人口预测。',
            'CP1/CP2使用本轮已有的用户范围授权；方法备选明确为回顾性复核。',
            '中文教学稿40页不套用英文参赛页数或英文说明长度。',
            '结束页自然留白允许；中间主体页用90pt目标及4pt测量容差，没有扩行距凑页。',
        ],
        requirement_crosswalk=read(audit_path('task_package.json'))['questions'],
        cross_checks='output/full_paper/revision_delivery_validation.json',
        visual_record='output/full_paper/revision_visual_review.json',
        visual_reviewed_pages=sum(d['pages'] for d in delivery['documents'].values()),
        all_applicable_dimensions_at_least_four=all(r[1] >= 4 for r in rows) and min(scores.values()) >= 4,
    )
    write(audit_path('scored_review.json'), report)
    old = ROOT / 'output/full_paper/revision_review_report.json'
    historical = ROOT / 'output/full_paper/history/revision_review_20261006.json'
    if old.exists() and read('output/full_paper/revision_review_report.json').get('status') == 'revision_scope_review_complete':
        historical.parent.mkdir(parents=True, exist_ok=True)
        if not historical.exists():
            shutil.copyfile(old, historical)
    write('output/full_paper/revision_review_report.json', report)
    return report


def instructions():
    text = '''# 本轮支撑材料与复现

范围：2026-10-07保存输入的复算、论文源/PDF及核查证据。解压到一个新目录，在解压根目录执行；模型文件使用项目相对路径。当前项目计算使用conda，Python及依赖版本见同目录env_check.json。优先沿用已有conda环境，不需重新安装本机运行环境。

快速复算（实际在解压副本中执行过）：

    python -X utf8 scripts/modeling/reproduce_baseline_for_paper.py

应输出57.26、5286.11、144.34，分别为完成率%、人时、机时。这个入口读取保存的真实模型输入重新求解，不是打印结果文件。论文附录自动载入的代码与该.py一致。

完整保存输入重算顺序：

    python -X utf8 scripts/modeling/build_question2.py
    python -X utf8 scripts/modeling/verify_question2.py
    python -X utf8 scripts/modeling/build_question3.py
    python -X utf8 scripts/modeling/verify_question3.py
    python -X utf8 scripts/modeling/build_question4.py
    python -X utf8 scripts/modeling/verify_question4.py
    python -X utf8 scripts/modeling/build_question6_real.py
    python -X utf8 scripts/modeling/verify_question6_real.py
    python -X utf8 scripts/modeling/build_revision_supplement.py

必须按顺序运行，因为后题读取前题结果与指纹。保存结果含生成时间，新复算可产生不同字节SHA，但对应关键数值应一致；这时要重新登记输入、源码和PDF的指纹，不可冒用旧审阅记录。单独对解压后的保存解运行四份verify脚本也已核验。

数值依赖见requirements_saved_input.txt，记录本轮实际版本；prepare_question3.py保留用于来源与代码指纹，重建它还需要requests、osmium和原始OSM快照，保存输入复算无需运行该上游准备脚本。

正文仍为docs/paper/full_paper.tex；中文学习稿为full_paper_zh.tex。两者图件内嵌，英文复现代码也通过filecontents*内嵌，不需要独立图片或代码文件才能编译。保持既有编辑器，直接编译同一源。Windows本机编译入口：

    & ./scripts/modeling/compile_revision_pdfs.ps1

编译及PDF工具路径按本机既有TeX Live2026配置；异机应先将脚本中的可执行程序路径适配到已有环境。无需安装LaTeX编辑器插件。内置编译器的平台目录错误未解决，本轮XeLaTeX导出已获用户授权且成功。

审计入口：scripts/modeling/audit_full_skill_20261007.py。它使用包内未修改的original_check_layout.py，支持英文编号及真实图表分组。PyMuPDF本机临时目录已安装1.28.2；异机可在已有conda环境安装相同版本。原版扫描器的原退出码1及7条误报、逐条裁定均保留，未改原脚本或放宽说明/面积阈值。

PDF重新编译后，依次渲染、文字/字体核验、逐页目视，再运行validate_revision_delivery.py；人工记录必须匹配新PDF指纹。finalize_skill_delivery_20261007.py只接受已有且指纹一致的记录，不会代替目视检查自动填“通过”。本轮300dpi渲染测量与目视记录在包内，90页PNG为节约体积不纳入。

包内包含当前分区/道路处理输入、六类历史调查的质量标记、第三题17处历史BH证据、第六题真实几何与50/100m裁园遥感缓存、当前结果、必要代码、原始来源记录和审计证据。旧方案备份仅有补充对照实际依赖的before_multispecies_revision_20261006.zip；不混入旧合成方案作为当前证据。

本包支持保存输入复算，不承诺从全球raw重建：全国OSM PBF、全球WorldCover瓦片、未用GPCC、其他巨大历史缓存不纳入。重建原始预处理需按data/question6/raw/q6_real_source_manifest.json及其他来源清单补齐原始文件、版本和许可证；修改边界或破坏缓存标签会使第六题需要原始瓦片。奇特旺面积冲突、历史资料质量和现场生态验证限制仍保留。

包内SUPPORT_SHA256.json逐条列出文件指纹，除清单自身；ZIP的SHA和解压复算结果记录在项目旁置support_archive_validation.json/review_support.zip.sha256。ZIP、最终旁置核验和大体积页图不包含于自身。包内复现入口以本说明为准，项目入口中对ZIP及旁置记录的链接指向原项目交付目录。
'''
    (AUDIT / 'REPRODUCE.md').write_text(text, encoding='utf-8')
    packages = ['numpy', 'scipy', 'networkx', 'shapely', 'pyproj', 'rasterio', 'matplotlib', 'pandas']
    versions = {}
    for p in packages:
        try:
            versions[p] = version(p)
        except PackageNotFoundError:
            raise RuntimeError('Missing required numerical package: ' + p)
    (AUDIT / 'requirements_saved_input.txt').write_text(
        '\n'.join(k + '==' + v for k, v in versions.items()) + '\n', encoding='utf-8')
    env = read(audit_path('env_check.json'))
    env['saved_input_reproduction_packages'] = versions
    env['effective_audit_PyMuPDF'] = {'version': '1.28.2', 'installation': 'tmp/skill_audit_20261007/python_packages; available only in the original workspace, not bundled'}
    env['original_checker_copy_sha256'] = sha(audit_path('original_check_layout.py'))
    env['builtin_compile_last_check'] = {'kind': 'compile-failed', 'diagnostic': 'Unable to find standard directories for platform', 'export': 'User-authorized installed XeLaTeX succeeded, original editor remains open'}
    write(audit_path('env_check.json'), env)


def package_files():
    files = set()

    def add(path):
        p = ROOT / path
        assert p.is_file(), path
        files.add(p.relative_to(ROOT).as_posix())

    def tree(folder, exclude_parts=(), suffixes=None):
        for p in (ROOT / folder).rglob('*'):
            if p.is_file() and not set(exclude_parts) & set(p.relative_to(ROOT / folder).parts):
                if suffixes is None or p.suffix.lower() in suffixes:
                    add(p.relative_to(ROOT))

    for folder in ['data/modeling', 'data/roads/processed', 'data/regions/processed',
                   'data/regions/raw/source_audit', 'data/question3', 'data/question6/processed',
                   'data/revision_feasibility/20261006', 'output/revision_feasibility/20261006']:
        tree(folder, exclude_parts=('history', 'archive', '__pycache__'))
    # Smaller raw evidence only; no global raster tiles or nationwide PBF.
    for p in (ROOT / 'data/question6/raw').iterdir():
        if p.is_file() and p.suffix.lower() in {'.json', '.geojson', '.html', '.md', '.txt', '.pdf', '.zip'}:
            add(p.relative_to(ROOT))
    for folder in ['output/question1', 'output/question2', 'output/question3', 'output/question4', 'output/question6']:
        tree(folder, exclude_parts=('history', 'archive', '__pycache__'),
             suffixes={'.json', '.csv', '.geojson', '.tikz', '.png'})
    tree('docs/paper', suffixes={'.md', '.tex'})
    tree(PDF_DIR, suffixes={'.pdf', '.log', '.aux', '.toc', '.out', '.py'})
    tree('output/full_paper/figures', suffixes={'.json', '.tikz', '.png'})
    for p in AUDIT.iterdir():
        if p.is_file() and p.suffix in {'.json', '.log', '.txt', '.md', '.py'} and p.name not in {
            'support_archive_validation.json', 'support_sha256.json', 'final_link_check.json'}:
            add(p.relative_to(ROOT))
    for p in (ROOT / 'docs/modeling_notes').glob('*.md'):
        add(p.relative_to(ROOT))
    for path in ['README.md', 'AGENTS.md', 'docs/项目状态与上传说明.md', 'docs/modeling_process.md',
                 'output/2026数模训练.pdf', 'output/2026数模训练_中文.pdf',
                 'output/model1/species_region_counts_2015.json', 'output/regions/region_base_data.json',
                 'output/full_paper/history/before_multispecies_revision_20261006.zip',
                 'tmp/pdfs/skill_checked_20261007/render_measurements.json']:
        add(path)
    for p in (ROOT / 'output/full_paper').glob('*.json'):
        add(p.relative_to(ROOT))
    scripts = ['build_question2.py', 'verify_question2.py', 'build_question3.py', 'verify_question3.py',
               'prepare_question3.py', 'build_question4.py', 'verify_question4.py', 'build_question6_real.py',
               'verify_question6_real.py', 'build_revision_supplement.py', 'revise_full_paper_presentation.py',
               'build_full_paper_figures.py', 'build_question2_paper_figures.py',
               'reproduce_baseline_for_paper.py', 'audit_full_skill_20261007.py',
               'review_revision_pdf_layout.py', 'validate_full_paper.py', 'validate_revision_delivery.py',
               'compile_revision_pdfs.ps1', 'finalize_skill_delivery_20261007.py']
    for name in scripts:
        add('scripts/modeling/' + name)
    # Validate all explicit baseline and supplemental input dependencies exist.
    dependency_paths = set(read('output/question2/q2_results.json')['source_sha256'])
    dependency_paths.update(read('output/question3/q3_results.json')['source_and_code_sha256'])
    dependency_paths.update(read('output/revision_feasibility/20261006/revision_results.json')['input_sha256'])
    dependency_paths = {p.replace('\\', '/') for p in dependency_paths}
    assert dependency_paths <= files, sorted(dependency_paths - files)
    return sorted(files)


def archive_and_verify():
    files = package_files()
    manifest = dict(scope='saved-input numerical reproduction and review evidence',
                    entries=[dict(path=p, bytes=(ROOT / p).stat().st_size, sha256=sha(p)) for p in files],
                    virtual_entries=['REPRODUCE.md (same bytes as audit REPRODUCE.md)', 'SUPPORT_SHA256.json'],
                    excluded=['archive itself/final fingerprint sidecars', '300dpi PNG pages',
                              'global raw rasters', 'nationwide OSM PBF', 'unused GPCC', 'unneeded historical model outputs'])
    write(audit_path('support_sha256.json'), manifest)
    # A fixed ZIP timestamp improves repeatability without changing source bytes.
    def entry(z, name, data):
        info = zipfile.ZipInfo(name, date_time=(2026, 10, 7, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)

    with zipfile.ZipFile(ARCHIVE, 'w') as z:
        for p in files:
            entry(z, p, (ROOT / p).read_bytes())
        entry(z, 'REPRODUCE.md', (AUDIT / 'REPRODUCE.md').read_bytes())
        entry(z, 'SUPPORT_SHA256.json', (AUDIT / 'support_sha256.json').read_bytes())
    with zipfile.ZipFile(ARCHIVE) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist())) == len(files) + 2
        assert all(not Path(p).is_absolute() and '..' not in Path(p).parts for p in z.namelist())
        for p in manifest['entries']:
            assert hashlib.sha256(z.read(p['path'])).hexdigest() == p['sha256'], p['path']
        # Use a new numbered extraction target; never delete any existing work.
        parent = ROOT / 'tmp/skill_audit_20261007'
        number = 1
        while (parent / f'package_replay_{number:02}').exists():
            number += 1
        replay = parent / f'package_replay_{number:02}'
        replay.mkdir(parents=True)
        z.extractall(replay)
    commands = ['reproduce_baseline_for_paper.py', 'verify_question2.py', 'verify_question3.py',
                'verify_question4.py', 'verify_question6_real.py']
    results = []
    for script in commands:
        process = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/modeling/' + script],
                                 cwd=replay, capture_output=True, text=True, encoding='utf-8')
        log = process.stdout + process.stderr
        (parent / ('package_' + script.removesuffix('.py') + '.log')).write_text(log, encoding='utf-8')
        assert process.returncode == 0, (script, log[-2500:])
        if script == commands[0]:
            assert all(v in process.stdout for v in ['score 57.26', 'total_person_hours 5286.11', 'drone_flight_hours 144.34'])
        results.append(dict(script=script, exit_code=process.returncode, log=(parent / ('package_' + script.removesuffix('.py') + '.log')).relative_to(ROOT).as_posix()))
    checksum = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    (AUDIT / 'review_support.zip.sha256').write_text(checksum + '  review_support.zip\n', encoding='ascii')
    result = dict(status='passed', archive=ARCHIVE.relative_to(ROOT).as_posix(), sha256=checksum,
                  bytes=ARCHIVE.stat().st_size, entries=len(files) + 2, source_entries_checked=len(files),
                  CRC_check='passed', all_entry_SHA256_match=True, duplicate_or_unsafe_paths=False,
                  replay_root=replay.relative_to(ROOT).as_posix(), saved_input_replay=results,
                  verified_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope='Saved input baseline LP re-solved and Q2/Q3/Q4/Q6 independent saved-solution checks in extracted archive; not a global-raw rebuild or a fresh visual review.')
    write(audit_path('support_archive_validation.json'), result)
    return result


def main():
    delivery = read('output/full_paper/revision_delivery_validation.json')
    assert delivery['status'] == 'passed_numerical_source_compilation_and_visual_checks'
    review = review_record(delivery)
    instructions()
    stage = read(audit_path('stage_status.json'))
    stage.update(status='completed_applicable_workflow', stages={
        '0_environment': 'completed; versions and compiler limitation recorded; project-local PyMuPDF available',
        '1_parsing': 'completed; full problem reread, seven deliverables and source inventory checked',
        '2_method_choice': 'completed; suitability and retrospective alternatives reviewed within prior user authorization',
        '3_code_solution': 'completed; Q2/Q3/Q4/Q6 and supplement rerun, independent cases and baseline cross-checks passed',
        '4_visualization': 'completed; 17-region map, layered architecture, logical float checks and current page reviews passed',
        '5_manuscript': 'completed; prose minimum 12pt, 24 descriptions 100--150 tokens, references/formulas/page constraints checked',
        '6_review': 'completed; nine dimensions scored, issue-resolution evidence and 90-page visual record checked',
        '7_delivery': 'completed if referenced archive validation passes; source/PDF/input fingerprints and extracted replay verified',
    }, review=audit_path('scored_review.json'), support_archive=audit_path('review_support.zip'),
       support_validation=audit_path('support_archive_validation.json'),
       implementation_report='docs/modeling_notes/skill_full_audit_20261007.md',
       limits_remain=review['remaining_limits'], applicability_exceptions=review['applicability_exceptions'])
    write(audit_path('stage_status.json'), stage)
    archive = archive_and_verify()
    print(json.dumps(dict(status='completed_applicable_workflow', scores=review['score'],
                         total_pdf_pages=24, support_entries=archive['entries'],
                         archive_MB=round(archive['bytes'] / 1e6, 2), extracted_replay='passed',
                         archive_SHA256=archive['sha256']), ensure_ascii=False))


if __name__ == '__main__':
    main()
