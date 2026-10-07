# 第六题真实空间数据计算说明

本轮额外完成奇特旺面积溯源和黄石2022年历史范围的独立权重情景；原面积基准结果未替换。当前6页PDF位于output/pdf/revision_20261006/，细节见[实施报告](revision_implementation_20261006.md)。

当前正式正文为 `docs/paper/question6_adaptation.tex` 和同名 `.md`。以前的合成任务网络已退出正式论文，完整备查目录为 `output/question6/archive/synthetic_20261006`。本次模型使用真实空间输入，作业参数仍为明示假设，计算范围为陆域生境服务子模型。

## 真实资料和口径

- 奇特旺：主计算使用UNEP-WCMC WDPCA2026年10月发布的site805多边形；OSM/Geofabrik2026-10-04快照提供道路和具名地理参考。原始OSM边界与ICIMOD边界用于交叉核对。WDPCA报告面积932、GIS面积1213.00265952与DNPWC报告952.63平方千米存在实质差异；边界校准未通过。奇特旺所有数值仅对应发布多边形试算，不支持当前法定园区的定量人员结论。没有缩放边界来强行匹配面积。
- 黄石：NPS IRMA官方边界（YELL_Boundary层）、NPS公开道路和位置点。道路记录数核对为2,007，第一批2,000加第二批7；位置点为1,425。公开数据排除部分内部及作业设施。
- 生境：ESA WorldCover2021v200真实10米栅格；100米最近邻采样计算分类比例，50米复核。并非2026年实测生境。各园使用UTM45N、UTM12N，栅格中心在边界内才计入统计。
- 原始文件、URL、版本、大小与SHA256见 `data/question6/raw/q6_real_source_manifest.json`。土地覆盖遵循CC BY4.0：© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium。OSM采用ODbL1.0，© OpenStreetMap contributors。
- 奇特旺NTNC官方GIS门户及基础设施PDF连接未成功，未当作已取得的空间数据。官方面积952.63平方千米来源为DNPWC国家报告（见正文参考文献）；计算使用的WDPCA面积与其差异在正文披露。

## 假设与实际计算

统一车速30 km/h、步速4 km/h；车速压力20、较快40 km/h。两人小队、观察10分钟、准备5分钟、派遣10分钟、2小时响应门槛，每100平方千米每月8次服务。有效工时120小时/人/月；每个候选响应点预留480人时/月。两处候选点为基准，第三处为方案。全部为情景协议，未宣称当地实测标准。无人机预算为零。未测量的社区、游客、设备等专属工作量未计入本次条件人员当量。

道路图使用实际线段，无向响应情景；明确私人或机动车禁止线路被过滤。仅加入0.5米以内端点制图连接。路外成本用最近道路投影的欧式距离，不建虚构跨河路段，但欧式步行也尚未落实河流、坡度和许可，因此结果不是实测响应率。现有地图不完整也会产生模型不可达，不能将其直接解释为现实不可达。选用最近道路投影构成当前数值协议，未证明为完整多方式通行的最优路径。

权重为陆域面积份额；永久水体不承担陆域服务需求。不伪造动物分布、检测率、客流或风险。各园固定目标为自身基准条件响应上限的90%，不是全园90分。LP以服务率为变量、成本为每次服务人时乘任务量，和正式容量模型的无无人机特例等价；加入每个可达单元15%服务底线。

## 复现

所有项目成果在当前项目内。使用 `F:/Python/anaconda/envs/himcn-roads/python.exe`。已安装pyshp、pyogrio、rasterio用于读取真实GIS；未安装TeX。

```powershell
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/fetch_question6_real_data.py
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/prepare_question6_geography.py yellowstone
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/prepare_question6_geography.py chitwan
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/build_question6_real.py
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/verify_question6_real.py
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/build_question6_real_figures.py
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/write_question6_real_chapter.py
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/finalize_question6_real_notes.py
```

下载脚本保留既有文件；PBF及栅格已在原始目录中。WorldCover下载使用源清单中的六个公开URL。原始下载脚本的部分失败记录留作证据；数据清单以上述最终清单为准。原始合成计算脚本已标为历史，不得用于覆盖当前正式成果。

## 核验和编译状态

独立按单位服务评分成本排序的分数背包法复算最小人时；核验响应资格、可达底线、固定目标、不可行性和人员当量上取整。共10个情景（含两组细网格）的数值核验通过；奇特旺边界一致性检验未通过，单独列于data_quality_checks，不混同为整体资料有效。另对100米栅格面积与向量面积、50米土地覆盖采样和巡检网格边长减半进行了复核。数值文件见 `output/question6/q6_results.json`、`q6_verification.json`。

LaTeX在原有同名正式文件中修订，图形几何嵌入TikZ，不依赖外部图片路径。内置编译器仍报告“Unable to find standard directories for platform”；本机既有XeLaTeX（TeX Live 2026）已将当前源码成功编译两遍，正式成果为[6页PDF](../../output/pdf/question6_adaptation.pdf)，含6个编号公式、3幅图与4张表。最终6页均经Poppler渲染和逐页视觉检查，当前源文件与PDF哈希见[q6_latex_verification.json](../../output/question6/q6_latex_verification.json)。旧Markdown阅读预览及其核验记录仅为历史备查，不代表当前正文。

运行环境：Python 3.12.15；{"numpy": "2.5.3", "scipy": "1.18.1", "networkx": "3.7", "shapely": "2.1.2", "pyproj": "3.8.0", "rasterio": "1.5.2", "osmium": "4.3.1", "pyogrio": "0.13.0"}。

空间统计与离散化复核摘要（完整分配向量保存在结果JSON，不重复抄入说明）：

```json
{
  "parks": {
    "chitwan": {
      "label": "奇特旺",
      "epsg": 32645,
      "polygon_area_km2": 1214.0634646073454,
      "raster_area_km2": 1213.9,
      "counts_100m": {
        "10": 110596,
        "20": 216,
        "30": 1231,
        "40": 3553,
        "50": 26,
        "60": 1951,
        "80": 3810,
        "90": 7
      },
      "forest_share": 0.9110799901145069,
      "open_share": 0.02799242112200346,
      "water_share": 0.03138644039871489,
      "grid_m": 1000,
      "cell_count": 1376,
      "land_area_km2": 1175.6540840718685,
      "bases": [
        {
          "name": "Kasara",
          "source_name": "Kasara",
          "source_id": 5252165737,
          "xy": [
            236498.63457253488,
            3050206.899587405
          ],
          "lonlat": [
            84.3315888,
            27.5501114
          ],
          "role": "existing mapped location used as candidate; active response staffing not assumed observed"
        },
        {
          "name": "Sauraha",
          "source_name": "सौराहा",
          "source_id": 12969605791,
          "xy": [
            253430.26190736244,
            3053185.618333402
          ],
          "lonlat": [
            84.5023058,
            27.5801633
          ],
          "role": "existing mapped location used as candidate; active response staffing not assumed observed"
        },
        {
          "name": "Amaltari",
          "source_name": "Amaltari home stay office",
          "source_id": 3453240299,
          "xy": [
            214435.51166301023,
            3052704.99808446
          ],
          "lonlat": [
            84.1077927,
            27.5681671
          ],
          "role": "existing mapped location used as candidate; active response staffing not assumed observed"
        }
      ],
      "road_metadata": {
        "in_park_road_km": 248.2902481598978,
        "source_features_used": 12283,
        "graph_nodes": 155772,
        "graph_edges": 160693,
        "components": 112,
        "cartographic_links_under_half_metre": 51,
        "direction": "undirected response geometry scenario; permissions not locally calibrated"
      },
      "landcover_resolution_check": {
        "resolution_m": 50,
        "forest_share": 0.9110581229421613,
        "water_share": 0.03128635643878322,
        "area_km2": 1214.1075,
        "forest_difference_pp": -0.00218671723456465
      }
    },
    "yellowstone": {
      "label": "黄石",
      "epsg": 32612,
      "polygon_area_km2": 8894.416142994862,
      "raster_area_km2": 8894.59,
      "counts_100m": {
        "10": 559693,
        "20": 36,
        "30": 218466,
        "40": 124,
        "50": 448,
        "60": 19565,
        "70": 35,
        "80": 42363,
        "90": 8,
        "100": 48721
      },
      "forest_share": 0.6292510391147877,
      "open_share": 0.267653708602645,
      "water_share": 0.04762782770200762,
      "grid_m": 2500,
      "cell_count": 1520,
      "land_area_km2": 8470.072426281971,
      "bases": [
        {
          "name": "Norris Ranger Station",
          "source_name": "Norris Ranger Station",
          "source_id": 3578,
          "xy": [
            524179.0609882919,
            4953863.499285288
          ],
          "lonlat": [
            -110.69460860006633,
            44.73774750051991
          ],
          "role": "existing mapped location used as candidate; active response staffing not assumed observed"
        },
        {
          "name": "Lake Ranger Station",
          "source_name": "Lake Ranger Station",
          "source_id": 5323,
          "xy": [
            548079.7685400525,
            4933259.838705455
          ],
          "lonlat": [
            -110.39467749970777,
            44.55106750045157
          ],
          "role": "existing mapped location used as candidate; active response staffing not assumed observed"
        },
        {
          "name": "South Entrance Ranger Station",
          "source_name": "South Entrance Ranger Station",
          "source_id": 1569,
          "xy": [
            526686.4406867202,
            4887039.49848805
          ],
          "lonlat": [
            -110.66638060054942,
            44.136064399723644
          ],
          "role": "existing mapped location used as candidate; active response staffing not assumed observed"
        }
      ],
      "road_metadata": {
        "in_park_road_km": 619.6046021681074,
        "source_features_used": 1478,
        "graph_nodes": 10619,
        "graph_edges": 10992,
        "components": 24,
        "cartographic_links_under_half_metre": 12,
        "direction": "undirected response geometry scenario; permissions not locally calibrated"
      },
      "landcover_resolution_check": {
        "resolution_m": 50,
        "forest_share": 0.6286932366749198,
        "water_share": 0.047625779936652235,
        "area_km2": 8894.5525,
        "forest_difference_pp": -0.0557802439867916
      }
    }
  },
  "grid_verification": {
    "chitwan": {
      "fine_grid_m": 500.0,
      "coarse_cap": 37.569228900391984,
      "fine_cap": 37.43759592939014,
      "cap_difference_pp": -0.13163297100184224,
      "fine_solution": {
        "score": 33.812306010353254,
        "patrol_hours": 125.02488775237845,
        "reserved_hours": 960,
        "total_person_hours": 1085.0248877523784,
        "staff_equivalent": 9.041874064603153,
        "staff_integer": 10,
        "max_residual": 0
      },
      "fine_target": 33.812306010352785
    },
    "yellowstone": {
      "fine_grid_m": 1250.0,
      "coarse_cap": 18.718005272970085,
      "fine_cap": 18.515688151745145,
      "cap_difference_pp": -0.20231712122494017,
      "fine_solution": {
        "score": 16.84620474567326,
        "patrol_hours": 583.7328579376461,
        "reserved_hours": 960,
        "total_person_hours": 1543.7328579376463,
        "staff_equivalent": 12.864440482813718,
        "staff_integer": 13,
        "max_residual": 0
      },
      "fine_target": 16.846204745673077
    }
  }
}
```
