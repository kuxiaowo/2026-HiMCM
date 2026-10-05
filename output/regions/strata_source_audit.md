# 2015 年埃托沙调查分区来源与空间质量核查

核查日期：2026-10-05。用途：支撑模型一分区与论文中的数据来源、预处理和局限性说明。本文只核查来源和原始几何；最终分区及其修复结果由主流程另行记录。

## 结论

已找到与 2015 年动物统计单元一一对应的公开分区坐标，来自 IUCN African Elephant Database（AED）的调查网页地图接口。共 15 个分区，不必先用网格、Voronoi 或凭空划分替代调查分区。

但该接口的几何是概化地图边界：坐标约 300 m 量化、缺少 CRS 声明、分区间有重叠，ENP11 尤其遗漏了扣除内嵌 ENP9 的洞。没有查到可证明为主管部门原始精确调查 GIS 的公开矢量。论文宜称“基于 AED 公开地图坐标，并参照 2015 年调查图修复的近似统计分区”，不能称官方精确调查边界。

## 来源与获取记录

| 来源 | 已核查内容 | 获取结果 / 保存位置 |
|---|---|---|
| Kilian, J. W. (2015). *Aerial Survey of Etosha National Park: Internal Report to the Ministry of Environment and Tourism* | 第 3-4 页方法，第 5 页 Figure 1/2，第 6 页 Table 1 | 本地原始 PDF：`data/species/raw/etosha_aerial_census_2015.pdf`；已完整目视核对第 5、6 页 |
| [Rhino Resource Center 原始下载](https://rhinoresourcecenter.com/wp-content/uploads/2022/01/1642693511.pdf) | 调查报告来源 | 已有文件继续复用，没有覆盖 |
| [EIS 2015 年条目](https://the-eis.com/elibrary/search/23915) | 作者、年份、报告名称、附件 | 搜索引擎可读；本机请求发生 TLS 错误；未从这里取得 GIS |
| [AED 调查条目 722](https://africanelephantdatabase.org/population_submissions/722) | 2015 年、旱季、18,551 km²、15 个调查统计单元、2911 头大象 | HTTP 200，网页保存在 `data/regions/raw/source_audit/aed_submission.html` |
| [AED 地图接口](https://africanelephantdatabase.org/population_submissions/722/map) | 网页 Leaflet 明确调用的接口；含坐标、分区编号、报告面积、大象估计数 | HTTP 200，11,127 字节；原样保存在 `data/regions/raw/source_audit/aed_2015_map.geojson` |
| [AED ENP1 条目](https://africanelephantdatabase.org/survey_aerial_sample_count_strata/3620) | 与报告 ENP1 的数量、面积和抽样率相符 | HTTP 200；`data/regions/raw/source_audit/aed_stratum.html` |
| ArcGIS 公共目录 | 搜索 `Etosha strata`、`Etosha census`、`Etosha survey`、`Etosha boundary` | 前两项 0 个结果；survey 的 11 个结果没有可确认的本调查分区；boundary 只检出公园边界。原始结果保存在 `data/regions/raw/source_audit/arcgis_search_*.json` |
| [EIS 2012 年报告](https://the-eis.com/elibrary/sites/default/files/downloads/literature/2012%20Etosha%20NP_Aerial%20census%202012.pdf) | 搜索/网页抽取显示旧年调查合并单元和实际覆盖不同 | 本机及网页完整页面取图均失败，未完成视觉核对；不能将旧年边界直接当作 2015 年边界 |
| [EIS Kaross 2009 年报告](https://the-eis.com/elibrary/sites/default/files/downloads/literature/Kaross_Aerial%20census%202009.pdf) | 确有 Kaross 单独调查报告条目 | 取图失败，未获得能明确解释 2015 年西南条纹块的原文图例 |

获取清单见 `data/regions/raw/source_audit/html_fetch_manifest.json`。AED 网页列出 CC BY-NC-SA 4.0 许可，并把调查报告标为“Report restricted by data provider”；应保留来源与许可说明，不能声称获得了限制报告背后的原始调查记录。

原报告、AED 接口以及两张地图的 SHA-256、字节数、提取页码和保留路径见 `data/regions/raw/source_audit/source_manifest.json`；地图也已持久保存为 `figure1_stratification_2015.jpg`、`figure2_flight_paths_2015.jpg`，不依赖临时渲染目录。

## PDF 地图是否可直接提取矢量

PDF 共 24 页，页面尺寸 595 × 842 pt。第 5 页包含两张 1125 × 627 像素 JPEG：

- Figure 1（调查分区与抽样强度）：`tmp/regions/source_audit/R34.jpg`。
- Figure 2（实际飞行航迹）：`tmp/regions/source_audit/R35.jpg`。
- 完整页面渲染：`tmp/regions/source_audit/census2015-05.png`。
- Table 1 完整页面渲染：`tmp/regions/source_audit/census2015-06.png`。

第 5 页内容流只有两次图像 `Do` 操作，图像外是标题和图注文字；两次 `re` 操作用于图像剪裁矩形，不是调查多边形。没有分区边界的矢量路径，也没有 `/VP` 或 `/LGIDict` 地理配准对象。

Figure 1 未显示经纬度格网、投影 / CRS、比例尺、指北针或带坐标的地名点。独立配准只能依据现有公园边界显著折点与盐沼轮廓进行近似匹配；它可以验证分区形态，不能从地图自身恢复主管部门的精确坐标。原始 JPEG 不能通过高 DPI 再渲染获得额外细节。

## 地图结构与解释

1. Figure 1 显示 3、4、10 三个实质不相连的块；Table 1 和 AED 将它们合为 **ENP3410**。不能把同一统计估计复制到三个块，也不能假装有三个独立动物估计。
2. Figure 1 对 ENP11 使用两处编号，但 ENP9 北侧可见窄的连接带，不能仅凭双标签断定为两个大部件。AED 中 ENP11 主要为一个连通部件，另有约 0.00129 km² 三角伪片。
3. ENP13 的第二部件约 0.0440 km²，亦是描摹伪片。ENP3410 的三个部件约 232.21、1465.88、745.40 km²，属于有实际意义的多部件。
4. 图注说明红色、蓝色、淡红色分别对应 40%、20%、10% 设计抽样强度。主盐沼虽着蓝色，但正文说明它未纳入调查，不能因为颜色相同就视为 20% 抽样分区。
5. Figure 1 西南角有无编号的竖条纹附加区；Figure 2 对应白色且无航迹。2015 年图注没有解释该条纹符号，不能强行划入 ENP1。它可能与西南 Kaross 区有关，但本轮缺直接原文证据，因此保留为“调查图未明确编号的残余区 / 待核查”。
6. 图中零碎盐沼 / 水体着色有时覆盖分区颜色，但调查分区图本身未给完整可独立恢复的水体统计规则；不可将全园所有蓝色斑块都认定为调查外主盐沼。

## AED 接口格式与几何质量

接口返回类似 GeoJSON 的 `FeatureCollection`，但每个 `features` 项直接使用 `type: MultiPolygon`、`coordinates` 和 `properties`，未按标准包装 `type: Feature` 和 `geometry`。已只做格式规范化，保留原始所有坐标及属性：

`data/regions/raw/source_audit/aed_2015_map_normalized.geojson`

接口未声明 CRS。坐标范围 14.3568-17.1573、-19.4832--18.4992 与园区经纬度相符，因此质量比较暂按 WGS84 / EPSG:4326 解释；这是有据推定而非源元数据声明。大部分相邻坐标是约 0.002703213° 的整数倍偏移，东西/南北角度步长相同，相当于当地约 284-299 m 的刻度。可称“约 300 m 坐标量化”，不能据此认定它是真正 300 m 栅格产品或确定实际位置精度。

15 个原始 MultiPolygon 在 Shapely 中均有效；这不意味着它们组成正确的无重叠分区。WGS84 椭球面积比较如下，未修复、未裁剪。

| 统计单元 | 源几何面积 km² | 报告面积 km² | 相对差异 |
|---|---:|---:|---:|
| ENP1 | 1775.46 | 1728.118 | +2.74% |
| ENP2 | 270.43 | 259.7612 | +4.11% |
| ENP3410 | 2443.50 | 2396.1 | +1.98% |
| ENP5 | 999.77 | 1006.661 | -0.68% |
| ENP6 | 729.92 | 701.0328 | +4.12% |
| ENP7 | 578.18 | 600.6719 | -3.74% |
| ENP8 | 386.45 | 441.8536 | -12.54% |
| ENP9 | 581.36 | 665.4298 | -12.63% |
| ENP11 | 3414.65 | 2811.934 | +21.43% |
| ENP12 | 1466.88 | 1489.425 | -1.51% |
| ENP13 | 1401.92 | 1427.367 | -1.78% |
| ENP14 | 1121.60 | 1145.296 | -2.07% |
| ENP15 | 2066.71 | 2038.162 | +1.40% |
| ENP16 | 910.84 | 918.1365 | -0.80% |
| ENP17 | 947.05 | 921.1887 | +2.81% |

- 源分区面积之和 19,094.71 km²，并集面积 18,464.48 km²，存在约 630.23 km² 重叠。
- 最主要重叠：ENP9 与 ENP11 为 580.50 km²，几乎整个 ENP9。参照 Figure 1，应从 ENP11 中扣去 ENP9，不应双重归属。
- 其他重叠包括 ENP12 / ENP3410 为 13.07 km²、ENP5 / ENP11 为 8.76 km²、ENP3410 / ENP5 为 6.36 km²、ENP7 / ENP6 为 5.58 km²。这些也需要修复或显式标记边界不确定性。
- 与现有 `data/roads/processed/park_boundary.geojson` 比较，约 94.11 km² 源分区在当前 OSM 园界外，当前园界内约 4534.59 km² 未被分区并集覆盖。后者同时含主盐沼与残余区，不能全部认作主盐沼。
- 本比较的当前公园范围面积约 22,904.74 km²，同属公开 OSM 边界，不能视为法律勘界面积。

详细数值和全部重叠对分别见 `data/regions/raw/source_audit/aed_geometry_audit.json`、`data/regions/raw/source_audit/aed_geometry_overlap.json`。

## 对主流程的建议

采用 AED 地图坐标作为有来源的近似分区种子，参照 Figure 1 修复拓扑并裁剪至当前公园边界。保留原始与修复图层，记录每次操作及面积变化；不要通过强制扩大多边形来伪造与报告面积完全一致。

保留 `area_report_km2` 和 `area_geometry_km2` 两套面积：历史动物调查密度、抽样率复算用报告面积；火灾 / 地表覆盖 / 水源等 GIS 叠加的面积比例使用实际几何面积。需说明不同统计支持范围导致的空间误差，并在 ENP8、ENP9 等差异较大区域做敏感性检验。

ENP3410 作为一个资源分配统计单元；如要对它的三个部件分别操作，必须注明部件动物数量来自区域内均匀密度或生境分摊假设，并保证三个部件合计守恒。主盐沼和无调查估计残余区必须单列为 NA，不能把未知动物数量置零。

本轮未向第三方发消息、未取得受限 GIS、未改写原始调查表、未提交或推送代码。

## 对拟议修复规则的评估

主流程提出在局部 LAEA 投影下，以原表面积由小到大给统计区处理优先级，依序从后续统计区扣除已归属的交集；从未覆盖残余范围作 500 m 开运算，取最大部件后 buffer 恢复并与原残余取交，构成主盐沼近似掩膜。以下是实施前的风险评估，具体数值与修复结果以主流程报告为准。

- ENP9 从 ENP11 扣除有 Figure 1 直接支持。其余小重叠的“小区优先”是保证可重复、避免覆盖嵌套小区的拓扑假设，不是官方边界归属证据。需逐区保留扣除面积及占比；若后续排名对边界敏感，可对剩余小重叠反向优先做敏感性比较。
- 残余范围并不天然等于盐沼。500 m 开运算可切断宽约 1 km 以下的狭窄连接，但也可能删除真实盐沼窄湾。恢复后与原残余取交，能保证盐沼掩膜不侵入已归属调查区；仍需与 Figure 1 主盐沼轮廓进行视觉验证。
- 建议记录 250、500、1000 m 三种开运算的盐沼面积与差集，确认主盐沼核心提取对操作尺度是否稳定。得到的是近似盐沼掩膜，不应称为独立遥感土地覆盖分类。
- 主盐沼与其他残余区的动物估计保留 null / NA；不得以未调查为理由赋零。微小三角伪片可保留，也可按明确阈值转入残余，但要记录阈值、原部件编号和处理面积。
