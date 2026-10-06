# 第六题计算、证据与写作说明

2026-10-06。用户已确认“奇特旺（亚洲）＋黄石（北美洲）”及小规模迁移演示路线，授权继续直至完成正文。本轮不提交、推送或修改其他题目结果。

## 正式成果

- [LaTeX正文](../paper/question6_adaptation.tex)，自包含TikZ图，不依赖附加LaTeX项目文件。
- [同步阅读稿](../paper/question6_adaptation.md)、[精简框架](../paper/question6_framework.md)。
- [明确假设](../../data/modeling/q6_assumptions.json)、[原始来源清单](../../data/question6/raw/source_manifest.json)。
- [七情景结果](../../output/question6/q6_results.json)、[汇总CSV](../../output/question6/q6_summary.csv)、[独立核验](../../output/question6/q6_verification.json)。
- [图件及生成清单](../../output/question6/paper_figures/figure_manifest.json)。
- [PDF阅读预览](../../output/pdf/question6_adaptation_reading.pdf)。由同步正文排版，不是TeX编译产物。

## 事实、假设与结果的界线

公开资料支持：奇特旺的重点物种、森林与洪泛平原、社区冲突及历史季风巡护限制；黄石的游客活动集中、季节道路条件、无人机授权要求。资料**不支持**本轮原型的定量权重、检查次数、路段长度或速度、四类任务分区、候选驻点、额外地面人时、95分目标与人数。

本轮原型是每园四个任务单元的**合成网络**，不是当地GIS或统计分区。沿用120小时/人月、两人同行、日间8小时与两小时响应门槛，均用于迁移演示，不称两园工作制度。没有迁入埃托沙水点、SPI、物种数量或57.26分目标。

同一园情景中冻结权重与需求，未知或不可响应对象不删除后再归一化。两园分数不作生态横向比较。黄石冬季额外地面工作保持72人时，专为控制比较；尚未拟合实际冬季游客数量或工作量。

奇特旺C1无人机仅是“已取得授权且任务协议等效”的条件情景，本轮没有证实当地实际授权。仅J2开阔地可以替代部分合格检查，地面移动和操作人工仍计入。黄石没有取得书面授权，所以全部原型机时为零；固定摄像装置和卫星也不自动计为可替代的巡护容量。

## 来源与资料年份

已在`data/question6/raw`保存8份原始来源，包括管理计划PDF和7份网页；完整URL、抓取状态及SHA-256见来源清单。网页按2026-10-06访问日期记录；奇特旺计划为**2013—2017年的历史文件**，FAO FAOLEX保存主管机构原文，不解释为现行完整制度。

- UNESCO奇特旺资料与2025年委员会决定：对象、生境、反偷猎与犀牛死亡原因。
- 奇特旺计划PDF第29页（正文5页）：季风洪水；第37页（正文11页）：季风车辆巡护限制和特殊巡护；第86页（正文60页）：作业季节安排。原官方旧下载地址404，改用FAO存档并保留实际下载源。
- NPS Laws and Policies：无人机须园长书面批准；公众道路规则和行政权限需要区分。自动无人值守摄影装置同样不能默认获准。
- NPS Current Conditions：季节交通与有限雪地方式，不能代替工作人员的速度、装备或路线记录。
- NPS Visitor Use Management：访客集中于道路和已开发地区，管理压力不等于已证明全园生态损害。
- NPS Science Publications & Reports、Wolf Management：后续当地生态与GIS校准入口，本轮未从中取种群数或效能系数。

## 七个情景及结果解释

| 情景 | 95分所需人时 | 原型人数 | 固定11人表现 |
|---|---:|---:|---|
| C0 非季风、地面 | 1265.0133 | 11 | 100分 |
| C1 条件授权无人机 | 1243.4133 | 11 | 100分；机时实际7.20 |
| C2 季风通行压力 | 目标不可达 | 不给人数 | 75.8913分，地理上限85分 |
| C3 季风＋J4前置点 | 1834.5600 | 16 | 响应预留1440人时已超1320预算 |
| Y0 常规道路 | 1304.8444 | 11 | 98.3596分 |
| Y1 冬季通行压力 | 目标不可达 | 不给人数 | 60分，达到地理上限 |
| Y2 冬季＋J2前置点 | 1740.5778 | 15 | 响应预留1440人时已超1320预算 |

每个前置点增480响应人时，地面任务另外计算。前置后的月度人时能满足目标不等于已经证明岗位资格、访问间隔、整数出勤或并发响应可行。11、15、16仅为原型任务集人员需求，不能称真实公园最低编制。

## 初步验证

独立验证使用Floyd-Warshall复算NetworkX Dijkstra路径；每个情景的技术上限足以完成唯一允许无人机任务，因此可独立化为按价值/工时排序的分数背包，与HiGHS最优值对照。最少人时最大差约`2.27e-13`。另检查服务容量、区域底线、不可响应单元、技术禁用、预算、整数人数、前置点480人时，以及把预算增至100000后地理上限仍不改变。

这些属于原型数值和行为验证，**尚未完成两园运行参数校准、现实部署验证或生态成效检验**。为实际应用补齐任务空间分布、授权、交通/驻点条件、工作日志与保护目标后，再替换合成网络和服务假设。

## 复现

在项目根目录依次执行：

```powershell
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/build_question6.py
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/verify_question6.py
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/build_question6_paper_figures.py
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/write_question6_chapter.py
```

`fetch_question6_sources.py`仅在需要刷新原始资料时运行。计算优先使用指定conda环境；PDF读取和排版核查可使用Codex捆绑依赖。全部成果和中间文件保存在本项目内。

## LaTeX编译限制与可读预览

内置编译器返回`Unable to find standard directories for platform`，没有给出源码语法诊断。本机现有TeX目录在`E:/texlive/2026`；XeLaTeX程序不可用，LuaLaTeX也缺少格式文件。本轮保留源码和内置编辑器，不安装或修改系统TeX；因此**LaTeX编译尚未验证**。

为方便直接阅读，用同一Markdown正文生成PDF阅读预览，公式以数学渲染器排版，保留三图三表及公式编号。其生成方式与TeX编译的限制明确写在预览首页，不能把该预览当作成功编译的证明。复现阅读预览：

```powershell
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/render_question6_reading_pdf.py math
& 'C:/Users/Pang zhengxin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 scripts/modeling/render_question6_reading_pdf.py pdf
```
