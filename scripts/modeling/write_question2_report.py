"""Write concise Q2 paper and calculation notes from the actual solver output."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def main():
    r=json.loads((ROOT/'output/question2/q2_results.json').read_text(encoding='utf-8'))
    data=json.loads((ROOT/'output/question2/q2_model_inputs.json').read_text(encoding='utf-8'))
    best=r['optimum'];scarce=r['scarce_budget_comparisons'][-1]['result'];forward=r['best_forward_post']
    q=r['AHP']['category_weights']
    table='\n'.join(f"| {a['name']} | {a['result']['score']:.2f} | {b['result']['score']:.2f} |" for a,b in zip(r['comparisons'],r['scarce_budget_comparisons']))
    top=sorted(r['regions'],key=lambda a:a['allocated_monitoring_person_hours'],reverse=True)[:5]
    regiontable='\n'.join(f"| {a['region_id']} | {100*a['demand_weight']:.2f} | {a['allocated_monitoring_person_hours']:.1f} | {a['drone_flight_hours']:.1f} | {100*a['service_completion_fraction']:.1f} |" for a in top)
    paper=r'''# 第二题：有限资源下的地面响应与无人机监测配置

## 数据与规划假设

本研究以17个分区组织资源，将10 km格网与分区相交后的各连通片设为代表性检查单元，共形成599个检查点。利用2015年六类动物调查、2021年WorldCover和2026年OSM道路，分别计算动物保护责任、可燃生境责任及道路进入便利度。对可猎、保护和特别保护三个类别建立团队判断的AHP矩阵，权重为 **QWEIGHTS**，一致性比率 **CRVALUE**；这些数值依据法规类别作比较，不是法定权重。动物数量先转为同物种的区域份额，防止数量多的物种主导评价；区内分布暂按面积均匀假设。

保护需求由反偷猎监测和可燃生境监测两个已知对象分项组成，分项权重改由共同有数据的15区熵权法计算，分别为 **OBJECTIVEWEIGHTS**，替代原手设0.7/0.3。各分项先取区域原始非负需求，按同列合计归一化，以信息差异度确定权重；不对599格网直接赋权，也不将调查外缺失动物填零。熵权反映区域差异带来的信息量，不等于真实危害或生态重要性。前者用动物责任乘道路进入指数，后者用可燃生境面积份额；由于多年完整火暴露尚缺，后者采用等暴露规划假设，不解释为真实火灾风险。盐沼及调查外区域保留通用监测底线，但该底线不能替代黑犀牛、鸟类和植物专项要求。赋权过程与方法敏感性见[客观赋权说明](../modeling_notes/q2_objective_weights.md)。

研究范围按团队决定限定为选定对象的反偷猎与可燃生境监测服务；水源及降雨不纳入指标、资源约束或图表。该简化限制模型对其他生态保障工作的解释范围。

| 共享规划条件 | 基准假设及用途 |
|---|---|
| 人员预算 | 题目295名部门工作人员中假设20%参与保护，每人每月120有效人时，合计7080人时；不是实测岗位配置 |
| 响应驻点 | 四处营地与两处入口作为六个候选点，每处2人、每日8小时、每月30日，共预留2880人时；仅分析日间窗口 |
| 技术预算 | 新增规划无人机6架，每架每日2机时、每月20作业日，合计240机时 |
| 监测标准 | 每100 km²每月8个标准检查点次，按面积分配，不随格网数改变总需求 |
| 通行与作业 | 道路30 km/h、道路外步行4 km/h；地面与无人机作业组均2人；单次观测10分钟、准备5分钟 |
| 飞行与响应 | 无人机40 km/h，单次安全飞行上限36分钟；调度10分钟，地面到场期限2小时 |

## 模型建立与求解

令检查单元 \(j\) 面积为 \(A_j\)，规定服务量 \(C_j=8A_j/100\)。令 \(x_j\)、\(h_j\) 为地面监测人时、无人机机时，\(s_j\) 为该单元规定服务完成率。沿有向路网计算候选驻点到检查点的去程和返程，另加道路外接近时间；地面单次人时 \(a_j\) 包含往返、准备、观察及两名队员。无人机在附近道路部署，单次机时 \(b_j\) 包含空中往返与观察，配套人时 \(o_j\) 包含人员到部署点的地面往返、准备和飞行操作，因此无人机不会产生“免费人工”。

设 \(r_j\in\{0,1\}\) 表示该单元能否在规定期限内获得地面响应，需求权重 \(w_j\) 合计为1。求解：

\[
\max P=100\sum_j w_js_j,
\quad C_js_j\leq\frac{x_j}{a_j}+\frac{h_j}{b_j},
\quad 0\leq s_j\leq r_j,
\]

\[
\sum_j x_j+\sum_j\frac{o_j}{b_j}h_j+H_0\leq H,
\qquad \sum_jh_j\leq U.
\]

无人机不适用的单元限制 \(h_j=0\)；每区至少完成其可响应部分15%的面积加权服务，防止已知权重较低区域被完全放弃。两类资源配比由模型决定，现场处置由已预留的地面队伍承担。以HiGHS求解线性规划，再在保持最优服务的条件下最小化人工消耗，选择同分解中的节省人时方案。连续点次是战略规划近似，不是逐日飞行或排班表。\(P\)仅衡量所选已知对象的监测服务，不能解释为动物存活率或完整全园保护认证。

## 结果与部署建议

基准预算下，三种部署均达到固定地理条件的 **BASESCORE** 分上限。优化方案使用 **FLIGHT** 机时和 **OPHOURS** 配套人时，加上2880响应人时，共 **TOTALHOURS** 人时；在本观测协议假设下，可替代筛查由无人机完成，地面人员负责部署、核查响应。关闭无人机仍能达到同分，但需NODRONEHOURS人时，说明此时技术主要节省人工，尚不能突破响应范围。基准人时尚有余量，不能宣称调整分配在该情景下提高了评分。

将可用人时减少40%至4248后，固定响应预留不变，余下1368人时需要竞争配置。此时优化部署取得 **SCARCESCORE** 分，比面积均衡和需求比例部署分别高AREAGAIN、DEMANDGAIN个百分点；使用SCARCEFLIGHT机时。若同一紧缺情景停用无人机，优化分数下降至SCARCENODRONE，技术替代的收益开始体现。基准与紧缺情景的对照见表和图1。

| 部署方式 | 基准7080人时：服务分 | 紧缺4248人时：服务分 |
|---|---:|---:|
COMPARISONTABLE

![图1：人时紧缺情景的分区人工投入与同预算部署比较](../../output/question2/scarce_budget/q2_resources_and_comparison.png)

基准方案的主要人工投入集中于ENP1、ENP12、ENP15、ENP13、ENP17；表中人工已含无人机配套人员，不另与机时相加。完整17区结果见计算附表。ENP9及部分北部单元的低分主要来自当前候选驻点和道路下的响应限制，不能据此认定这些区域没有保护价值。

| 区域 | 需求权重/% | 监测配套人工/人时 | 无人机/机时 | 面积加权服务完成/% |
|---|---:|---:|---:|---:|
REGIONTABLE

![图2：基准需求分布与响应条件下的服务完成率，星号为候选驻点](../../output/question2/q2_allocation_map.png)

在相同总资源上限下，另枚举三处现有道路节点作为新增前置响应点，并计入每月额外480响应人时。三个候选中，面向ENP5目标、位于 \(14.96728^\circ E,18.77332^\circ S\) 的道路节点效果最好，使服务分提高至 **FORWARDSCORE**；该位置是建模候选，不是现有保护站，也不是全园选址的全局最优证明。因此建议先核验北部/西北部前置响应的通行条件，再决定是否增加技术，而不是仅增加飞行时间。

道路速度20/40 km/h时，在固定基准需求权重下，评分分别为SPEED20/SPEED40；这反映通行与到场能力的敏感性。放宽到场期限至3小时得到RESPONSE3分，但同时改变了保护标准，不能称真实保护改善。保持单位面积服务标准，5/10/15 km检查格网分别得到GRID5/BASESCORE/GRID15分，说明边界和代表点仍有尺度影响。以上配置依赖历史动物、候选道路权限、等火暴露及合格观测可替代假设，应以巡护/飞行日志校准；缺失的重点对象数据不能用较高平均分补偿。

## 资料与计算附件

原题参考人员数与资源要求；[2015航空调查](https://rhinoresourcecenter.com/wp-content/uploads/2022/01/1642693511.pdf)；[法规汇编](https://namibiatradeportal.gov.na/application/files/3617/2986/2681/Nature_Conservation_Ordinance_4_of_1975.pdf)；[AHP方法](https://doi.org/10.1504/IJSSCI.2008.017590)；[WorldCover](https://esa-worldcover.org/en/data-access)；[OSM/Geofabrik](https://download.geofabrik.de/africa/namibia.html)。法规类别的数值判断、人员参与比例、检查频次、设备与工时均为团队规划假设。

[完整结果JSON](../../output/question2/q2_results.json)、[17区基准配置](../../output/question2/q2_regional_allocation.csv)、[紧缺配置](../../output/question2/q2_scarce_regional_allocation.csv)、[技术与质检说明](../modeling_notes/question2_calculation_notes.md)。
'''
    replacements={'QWEIGHTS':'、'.join(f'{x:.4f}' for x in q),'CRVALUE':f"{r['AHP']['CR']:.4f}",'BASESCORE':f"{best['score']:.2f}",'FLIGHT':f"{best['drone_flight_hours']:.2f}",'OPHOURS':f"{best['drone_operator_hours']:.1f}",'TOTALHOURS':f"{best['total_person_hours']:.1f}",'SCARCESCORE':f"{scarce['score']:.2f}",'FORWARDSCORE':f"{forward['result']['score']:.2f}",'COMPARISONTABLE':table,'REGIONTABLE':regiontable}
    for key,value in replacements.items():paper=paper.replace(key,value)
    scenarios={s['name']:s['result'] for s in r['scenarios']}
    extra={'OBJECTIVEWEIGHTS':'、'.join(f'{v:.4f}' for v in r['management_weight_estimation']['weights']),
           'NODRONEHOURS':f"{scenarios['无人机停用']['total_person_hours']:.1f}",
           'AREAGAIN':f"{scarce['score']-r['scarce_budget_comparisons'][0]['result']['score']:.2f}",
           'DEMANDGAIN':f"{scarce['score']-r['scarce_budget_comparisons'][1]['result']['score']:.2f}",
           'SCARCEFLIGHT':f"{scarce['drone_flight_hours']:.2f}",
           'SCARCENODRONE':f"{scenarios['人时减少40%且无人机停用']['score']:.2f}",
           'SPEED20':f"{scenarios['道路速度20km/h']['score']:.2f}",'SPEED40':f"{scenarios['道路速度40km/h']['score']:.2f}",
           'RESPONSE3':f"{scenarios['响应期限3小时']['score']:.2f}",
           'GRID5':f"{r['grid_sensitivity'][0]['result']['score']:.2f}",'GRID15':f"{r['grid_sensitivity'][1]['result']['score']:.2f}"}
    for key,value in extra.items():paper=paper.replace(key,value)
    (ROOT/'docs/paper/question2_resource_allocation.md').write_text(paper,encoding='utf-8')
    notes=r'''# 第二题计算备查

当前主结果是条件性规划LP，不是现有部署评估或完整生态成效认证。正文见[第二题论文段落](../paper/question2_resource_allocation.md)。

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
'''
    (ROOT/'docs/modeling_notes/question2_calculation_notes.md').write_text(notes,encoding='utf-8')
    print('Wrote paper and computation notes from q2_results.json')

if __name__=='__main__':main()
