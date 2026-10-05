# GPCC示例文件检查

日期：2026-10-05。已实际读取，不依赖文件名猜测。

## 文件内容

- GPCC/DWD月降水空间分析，Version 2025；实际覆盖1971-01至1975-12，共60个月。
- 全球1440×720经纬度格网；0.25°分辨率；埃托沙纬度附近约26.3×27.7 km/格。
- 每个空间变量为60×720×1440。time是可扩展维，实际记录数60，不是缺失。
- precip单位mm/month，按月累计降水深度处理，不再次乘天数，不按格点雨量直接求和。

| 变量 | 文件内含义 | 使用位置 |
|---|---|---|
| precip | gpcc monthly version 2025, precipitation per grid cell；mm/month | 主降水序列 |
| gauge | gpcc monthly version 2025, number of gauges per grid cell；number of gauges per grid cell | 格点内站点数，质量背景 |
| err | gpcc monthly version 2025, interpolation error (YAMAMOTO) per grid cell；mm/month | 插值误差，质量检查 |
| sys_err | gpcc monthly version 2025, gpcc mean systematic gauge error correction factor per grid cell；multiplier | 雨量计系统误差订正乘数，本样本区域均缺失 |
| gauge_int | gpcc monthly version 2025, number of gauges used by interpolation per grid cell；number gauges used per grid cell interpolation | 插值使用的站点数，质量背景 |
| dist_int | gpcc monthly version 2025, mean distance of gauges used by interpolation per grid cell；mean distance in kilometer | 插值所用站点平均距离，质量背景 |
| liquid | gpcc monthly version 2025, proportion of liquid precipitation per grid cell；%/month | 液态降水比例，本样本区域均缺失 |
| solid | gpcc monthly version 2025, proportion of solid precipitation per grid cell；%/month | 固态降水比例，本样本区域均缺失 |
| precip_infill | gpcc monthly version 2025, precipitation per grid cell with climatological station values infilling；mm/month | 含气候站值填补的替代降水，先作对照 |

## 埃托沙样本核验

公园包围盒取到60格，60个月共3600个precip值全部有效；范围0.00—432.38 mm/月。这不是全园月均值范围。
gauge在包围盒内为0—3；0表示格点内无站点，不表示无雨或降水缺失。
多数格点并无本格雨量站；应将结果称为格网分析估计。插值误差、站点数和距离作为质量背景，不新增保护风险因子。

已按公园17个实际分区与0.25°格网的相交面积计算月降水平均深度。
公园实际相交格点数46；各区格网覆盖完整，分区权重和与全园权重一致。
示例：1971年1月，全园面积加权降水约110.41 mm。它不是包围盒简单平均。

| 年份 | 样例全园年累计（mm） |
|---|---:|
| 1971 | 414.65 |
| 1972 | 376.10 |
| 1973 | 305.69 |
| 1974 | 699.85 |
| 1975 | 390.52 |

## 进入模型的结论

该文件是空间格网资料，可以形成17区月序列；不是仅有一套全园月均值。
0.25°资料较粗，区内加权不提升原分辨率，小区可能共享相同格点，不能解释为独立高精度雨量。
本文件只有5年。完整50年SPI仍需其余同版本同网格文件，并检查时间连续性、单位及重复月。
主方案仍为完整雨季SPI-6派生一个不足指标；当前只完成样例读取和分区提取，没有SPI实算。

[原始检查JSON](gpcc_1971_1975_inspection.json)、[分区月降水JSON](gpcc_example_regional_monthly_1971_1975.json)、[降水指标方案](../../docs/降水指标设计.md)。
