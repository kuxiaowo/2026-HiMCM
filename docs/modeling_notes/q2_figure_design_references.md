# 第二题图表设计来源与原创绘制记录

更新：2026-10-06。本文记录图表表达参考，不将参考论文的模型假设、数值结果或现成图片用于本项目。

## 已查阅的公开论文

1. **Deploying PAWS: Field Optimization of the Protection Assistant for Wildlife Security**，2016。已下载并阅读PDF第4页的Figure 5，参考其“分层输入—分析—模型—巡护策略”的模块和箭头表达。
   - [论文及DOI](https://doi.org/10.1609/aaai.v30i2.19070)
   - [公开PDF](https://ojs.aaai.org/index.php/AAAI/article/download/19070/18824)
   - 本地参考：`tmp/paper_design_references/paws_2016.pdf`、`paws_overview.png`（均相对项目根目录）。
2. **Improving Community-Participated Patrol for Anti-Poaching**，2025。已下载并阅读公开预印本v2第7页的Figure 3，参考地图轮廓、分区结果与预算对照的多面板表达。
   - [论文及DOI](https://doi.org/10.1609/aaai.v39i27.35072)
   - [公开预印本PDF](https://arxiv.org/pdf/2412.10799)
   - 本地参考：`tmp/paper_design_references/community_patrol_2025.pdf`、`community_case.png`。

采用的是流程组织和比较方式。未复制参考图，也未引入安全博弈、偷猎者行为估计或社区巡护数据。

## 本项目图表

| 论文编号 | 原创表达 | 数据与核对重点 |
|---|---|---|
| 图2-1 | 三阶段流程、模块与箭头 | 数据如何形成权重、成本和LP约束 |
| 图2-2 | 横向堆叠条形 | 动物和生境两分项已乘熵权，区域合计为100% |
| 图2-3 | 并列分区地图 | 同一空间范围显示需求与服务，候选驻点、不可响应点、指北及比例尺 |
| 图2-4 | 原创驻点、部署点、目标与无人机简图；成本堆叠 | 示例ENP1_0000源于路线计算，人时与机时分开 |
| 图2-5 | 带数值的分区矩阵 | 显示基准与紧缺服务及人工；各列颜色只表达列内强度 |
| 图2-6 | 分组柱形＋预算堆叠 | 同一预算内比较三种方案，完整显示固定响应与监测人工 |
| 表2-1—2-5 | 三线表 | 参数、熵权、变量、17区配置与前置点候选 |

图号按论文中的出现顺序编排；图2-5对应`fig6_regional_matrix`，图2-6对应`fig5_score_and_budget`。该文件名顺序仅为生成顺序，不影响论文引用。

配色采用蓝色表示基准/动物分项、金色表示紧缺/生境分项、红色表示响应限制。具体含义由每张图的图例确定。颜色附带数值与文字，小正值不显示为精确零。地图轮廓的简化只作用于绘图，模型几何与路线不变；比例尺沿用模型UTM口径。

## 生成及使用

- [图件脚本](../../scripts/modeling/build_question2_paper_figures.py)：读取固定模型输入和结果，生成同一绘图原语的PNG、SVG与TikZ。
- [正式正文脚本](../../scripts/modeling/write_question2_chapter.py)：从JSON生成原地LaTeX正文与Markdown同步稿。
- [生成清单](../../output/question2/paper_figures/figure_manifest.json)：包括数据指纹、成本示例和格式。
- [章节清单](../../output/question2/q2_chapter_manifest.json)：包括章节、公式、图表计数及引用映射。

当前编辑器的独立LaTeX源内嵌所有TikZ图，避免依赖附加项目图件。PNG供预览和Markdown阅读，SVG供后续排版。2026-10-06已用本机TeX Live 2026 / XeLaTeX生成[15页PDF](../../output/pdf/question2_framework.pdf)，全部页已渲染并目视核验。驻点星号使用矢量路径，流程图和检查点标签间距已调整；未修改地图数据或模型结果。内置编辑器仍有独立的平台环境错误，编译核验详见[核验记录](../../output/question2/q2_latex_compile_verification.json)。
