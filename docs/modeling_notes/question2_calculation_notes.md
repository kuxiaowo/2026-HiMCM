# 第二题计算备查

当前主结果是条件性规划LP，不是现有部署评估或完整生态成效认证。正文已按2.1—2.6扩写为[正式Markdown稿](../paper/question2_resource_allocation.md)及当前打开的[LaTeX源](../paper/question2_framework.tex)，含30个编号公式、6幅原创图、5张表。此次写作未更改模型参数与数值。

## 可复现过程

1. 按团队最新决定删除水源与降雨因素，当前复现流程不读取降水文件、不计算SPI、不生成降水图。既有数据和旧版结果仅留历史备查。
2. summarize_fire_sample_q2.py提取2022年9月单月MODIS样例，使用QA陆地/有效标志，排除缩短映射期、负日期，按DOY244—273统计；WorldCover草灌林最近邻至MODIS格网，主盐沼燃料设为零。有效可燃面积17617.90km²中检出过火50.87km²，仅作单月质检，不用于声称多年火灾风险。主模型火侧等暴露假设仍需替换为可靠历史序列。
3. build_question2.py读动物/法规/生境基表，完成三类别AHP；复用园内有向道路图，尊重单行方向和原OSM连接。基准假设管理车辆有权使用机动车候选道路，尚未确认全部权限及门禁延误。
4. 10km格网与分区相交后逐连通片取内部代表点；片面积权重合计覆盖各区。最近道路投影按路段长度分配到两端，再用Dijkstra计算候选驻点去程/返程，另加道路外步行。图只保留真实节点连接，不用直线补道路。道路外连线是明确的步行近似，未验证每处地形障碍。
5. 资源分配采用每100km²每月8次合格检查的面积口径，避免格网细化改变服务总量。针对每片的完整作业成本计算LP服务率。去程和返程同一驻点；无人机移动部署的人工往返纳入o_j，机时只计飞行。
6. 解主LP后固定最优s、最小化人工；计算面积均衡、需求密度比例两种同预算启发式。基准预算都达到地理上限，不输出虚假优化提升；另比较人时减少40%的相同模型。
7. 检查人时/机时减少、设备停用、作业成本、固定权重下的路速/响应期限、5/15km尺度。枚举三处道路节点新增前置点，额外响应人时扣预算；仅证明候选中最好，不证明全园最优选址。

## 变量与评分边界

每片支持面积A_j，区域内权重μ_j=A_j/A_i。已知六类动物只在15调查区分项归一化；两区动物值在区域结果仍为null。其“动物分项目标系数为0”表示不在这个已测分项中，不表示真实动物价值为0。可燃生境分项覆盖17区、主盐沼燃料为0；盐沼生态价值仍未知，保留通用服务底线。

动物分项：w_j^A=V_i^A μ_j E_j / Σ(V_i^A μ_j E_j)，E_j=exp(-进入时间/2h)。进入源为道路/边界交点，属于进入候选，不证明偷猎发生。可燃生境分项：w_j^F=(区域可燃面积/全园可燃面积)μ_j。主目标w_j=αw_j^A+(1−α)w_j^F，α由共同15区熵权确定，不再固定0.7/0.3。另测试CRITIC、0.5/0.5和0.9/0.1，不能把不同需求下的分数升高解释为保护改善。两分项未覆盖的对象仍未知，熵权不能填补这些缺失，也不能消除动物类别AHP的判断成分。

每区约束Σμ_j s_j≥0.15Σμ_j r_j，仅保障可响应部分的通用下限；该值不是绝对全区15%，更不是黑犀牛专项底线。观测协议假定无人机与地面能完成同类筛查，隐蔽目标/密林、执法与消防不随意折算。r_j只表示规定日间窗口的规划响应可达性，并非事件成功处置概率；多目标共享队伍采用稀疏事件假设。

输出区域人时x_i=Σx_j、机时h_i=Σh_j、操作人时Σ(o_j/b_j)h_j，响应2880人时在驻点共享、不按区重复扣。区域面积加权完成率Σμ_j s_j与需求加权全园已知对象评分P不是同一个量。

## 不确定性与第三题接口

关键未知包括当前黑犀牛和珍稀植物/鸟类分布、本园实际保护岗位人数、巡护/飞行速度与核查日志、多年有害火、候选驻点权限。动物历史值、生态2021和道路2026混用，代表规划示范，不是同年完整回测。水源与降雨均在当前范围之外。

第三题复用C、r、区域底线和设备条件，给定所选服务目标，最小化Σx+Σ(o/b)h+H_0，再按该期有效人时换算规划人数。不同月份重配置，常设人数考虑最紧张时期；不能由本题基准59名假设直接宣布真实最低编制。没有复杂轮班或预测动物数量。

运行命令（项目根目录，现有conda Python）：

```powershell
& 'D:/Python/Conda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/summarize_fire_sample_q2.py
& 'D:/Python/Conda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/build_question2.py
& 'D:/Python/Conda/envs/himcn-roads/python.exe' -X utf8 scripts/modeling/write_question2_report.py
```

假设入口：[q2_assumptions.json](../../data/modeling/q2_assumptions.json)。修改后重跑模型和报告；图表数值由实算生成，不手工改排名。原始资料未修改，未提交推送。

现行`write_question2_report.py`依次运行独立核验、论文绘图及正式正文生成。旧简稿生成器仅保存在`scripts/modeling/archive/write_question2_report_legacy.py.txt`作历史备查，其FLIGHT/SCARCEFLIGHT替换顺序错误已经修正。正式稿直接读取JSON，不再使用该占位符替换方式。只更新写作时可以单独运行`write_question2_chapter.py`；更新图件后需重新生成正文以同步内嵌TikZ。

论文图表从[图件脚本](../../scripts/modeling/build_question2_paper_figures.py)生成，来源记录见[图表设计参考](q2_figure_design_references.md)。该脚本不创建新数据或新求解情景。2026-10-06已使用本机TeX Live 2026 / XeLaTeX编译并核验[15页PDF](../../output/pdf/question2_framework.pdf)。内置编辑器仍返回“Unable to find standard directories for platform”，属于独立的预览环境错误。

本轮[静态章节核验](../../output/question2/q2_chapter_validation.json)检查环境及括号、唯一标签与引用、章节/图表/公式计数、Markdown表格/图片/相对链接及文件指纹，已通过。指纹按Windows实际保存的字节计算，避免文本换行转换造成不同摘要；模型输入和结果指纹未改变。

## 本地LaTeX编译与版式核验

本机编译器为`D:/texlive/2026/bin/windows/xelatex.exe`。在项目根目录执行以下命令两遍以稳定交叉引用；PATH只在当前PowerShell进程中补充，不修改系统设置。

```powershell
$env:Path = 'D:/texlive/2026/bin/windows;' + $env:Path
& 'D:/texlive/2026/bin/windows/xelatex.exe' -interaction=nonstopmode -halt-on-error -file-line-error -no-shell-escape -output-directory=output/pdf docs/paper/question2_framework.tex
& 'D:/texlive/2026/bin/windows/xelatex.exe' -interaction=nonstopmode -halt-on-error -file-line-error -no-shell-escape -output-directory=output/pdf docs/paper/question2_framework.tex
```

本轮将驻点星号改为绘图路径，避免Unicode字符的字体依赖；调整流程图两行文字与检查点标签间距，参考文献采用左对齐。图件和同源正文已重新生成，模型输入与结果未更改。

最终15页A4 PDF全部渲染并目视核验，字体全部嵌入，中文正文提取正常。最终日志中LaTeX错误、未定义引用、缺字、Overfull及Underfull均为0。详情和源文件/PDF指纹见[编译核验记录](../../output/question2/q2_latex_compile_verification.json)，编译日志保存在`output/pdf/question2_framework.log`；本轮仅验证排版和编译，不增加生态成效或人员需求结论。
