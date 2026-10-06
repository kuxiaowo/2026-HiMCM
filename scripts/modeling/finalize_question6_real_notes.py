from pathlib import Path
import json,hashlib,sys,datetime,importlib.metadata
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/question6';RAW=ROOT/'data/question6/raw'
URLS={
 'chitwan_wdpca.json':'https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer/1/query?where=site_id%3D805&outFields=*&outSR=4326&f=json',
 'icimod_nepal_pa.geojson':'https://geoapps.icimod.org/icimodarcgis/rest/services/Nepal/BaseMap/MapServer/3/query?where=1%3D1&outFields=*&outSR=4326&f=geojson',
 'nepal-latest.osm.pbf':'https://download.geofabrik.de/asia/nepal-latest.osm.pbf',
 'yellowstone_boundary.zip':'https://irma.nps.gov/DataStore/DownloadFile/754058?Reference=2316784',
 'yellowstone_roads.geojson':"https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer/0/query?where=UNITCODE%3D%27YELL%27&outFields=*&outSR=4326&f=geojson&resultRecordCount=2000",
 'yellowstone_roads_page2.geojson':"https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Roads/MapServer/0/query?where=UNITCODE%3D%27YELL%27&outFields=*&outSR=4326&f=geojson&resultRecordCount=2000&resultOffset=2000",
 'yellowstone_pois.geojson':"https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_POIs_Geographic/FeatureServer/0/query?where=UNITCODE%3D%27YELL%27&outFields=*&outSR=4326&f=geojson&resultRecordCount=2000",
}
def main():
 r=json.loads((OUT/'q6_results.json').read_text(encoding='utf8'));v=json.loads((OUT/'q6_verification.json').read_text(encoding='utf8'))
 sources=[]
 for f,u in URLS.items():
  p=RAW/f;sources.append(dict(file=p.relative_to(ROOT).as_posix(),url=u,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 for p in sorted((RAW/'worldcover').glob('*.tif')):sources.append(dict(file=p.relative_to(ROOT).as_posix(),url='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/'+p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 manifest=dict(download_date='2026-10-06',wdpca_release='October2026',chitwan_boundary_source='UNEP-WCMC WDPCA site805',chitwan_boundary_validation='failed area consistency: rep_area932, published gis_area1213.00265952, DNPWC report952.63; computed polygon used only for conditional migration trial',osm_snapshot='2026-10-04T20:20:21Z',landcover_year=2021,landcover_algorithm='v200',nps_boundary_catalog_update='2025-12-18',yellowstone_road_records=2007,yellowstone_poi_records=1425,sources=sources,licenses={'osm':'ODbL 1.0; © OpenStreetMap contributors','worldcover':'CC BY4.0; © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium','wdpca_attribution':'UNEP-WCMC and IUCN (2026), Protected Planet: WDPCA, October2026, Cambridge, UK'},unavailable_sources=[dict(url='https://geoportal.ntnc.org.np/layers/ntnc:Chitwan_National_Park/',reason='TLS hostname mismatch and HTTP502; not used in calculations'),dict(url='https://giwmscdntwo.gov.np/media/pages/files/Final%20Report_GIS%20Database_v4olikj.pdf',reason='connection failure; not used in calculations')])
 (RAW/'q6_real_source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 versions={m:importlib.metadata.version(m) for m in ['numpy','scipy','networkx','shapely','pyproj','rasterio','osmium','pyogrio']}
 notes='''# 第六题真实空间数据计算说明

当前正式正文为 `docs/paper/question6_adaptation.tex` 和同名 `.md`。以前的合成任务网络已退出正式论文，完整备查目录为 `output/question6/archive/synthetic_20261006`。本次模型使用真实空间输入，作业参数仍为明示假设，计算范围为陆域生境服务子模型。

## 真实资料和口径

- 奇特旺：OSM/Geofabrik尼泊尔PBF，快照时间2026-10-04T20:20:21Z；提取公园边界、周边道路与具名位置。社区数据，不宣称法定边界或完整巡护路线。
- 黄石：NPS IRMA官方边界（YELL_Boundary层）、NPS公开道路和位置点。道路记录数核对为2,007，第一批2,000加第二批7；位置点为1,425。公开数据排除部分内部及作业设施。
- 生境：ESA WorldCover2021v200真实10米栅格；100米最近邻采样计算分类比例，50米复核。并非2026年实测生境。各园使用UTM45N、UTM12N，栅格中心在边界内才计入统计。
- 原始文件、URL、版本、大小与SHA256见 `data/question6/raw/q6_real_source_manifest.json`。土地覆盖遵循CC BY4.0：© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium。OSM采用ODbL1.0，© OpenStreetMap contributors。
- 奇特旺NTNC官方GIS门户及基础设施PDF连接未成功，未当作已取得的空间数据。官方面积952.63平方千米来源为DNPWC国家报告（见正文参考文献）；计算使用的OSM面积与其差异在正文披露。

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

独立按单位服务评分成本排序的分数背包法复算最小人时；核验响应资格、可达底线、固定目标、不可行性和人员当量上取整。共10个情景（含两组细网格）通过。另对100米栅格面积与向量面积、50米土地覆盖采样和巡检网格边长减半进行了复核。数值文件见 `output/question6/q6_results.json`、`q6_verification.json`。

LaTeX在原有同名正式文件中修订，图形几何嵌入TikZ，不依赖外部图片路径。内置编译器当前报告“Unable to find standard directories for platform”；现有本地TeX格式也不可用，源码编译未验证。`output/pdf/question6_adaptation_reading.pdf` 是从同步Markdown生成的阅读预览，不能宣称LaTeX成功编译。预览需要逐页视觉检查，核验记录在 `q6_reading_pdf_verification.json`。
'''
 notes=notes.replace('奇特旺：OSM/Geofabrik尼泊尔PBF，快照时间2026-10-04T20:20:21Z；提取公园边界、周边道路与具名位置。社区数据，不宣称法定边界或完整巡护路线。','奇特旺：主计算使用UNEP-WCMC WDPCA2026年10月发布的site805多边形；OSM/Geofabrik2026-10-04快照提供道路和具名地理参考。原始OSM边界与ICIMOD边界用于交叉核对。WDPCA报告面积932、GIS面积1213.00265952与DNPWC报告952.63平方千米存在实质差异；边界校准未通过。奇特旺所有数值仅对应发布多边形试算，不支持当前法定园区的定量人员结论。没有缩放边界来强行匹配面积。')
 notes=notes.replace('计算使用的OSM面积与其差异在正文披露','计算使用的WDPCA面积与其差异在正文披露')
 notes=notes.replace('共10个情景（含两组细网格）通过','共10个情景（含两组细网格）的数值核验通过；奇特旺边界一致性检验未通过，单独列于data_quality_checks，不混同为整体资料有效')
 notes+='\n运行环境：Python '+sys.version.split()[0]+'；'+json.dumps(versions,ensure_ascii=False)+'。\n'
 grid_summary={}
 for park,item in r['grid_verification'].items():
  short=dict(item)
  if short.get('fine_solution'):short['fine_solution']={k:v for k,v in short['fine_solution'].items() if k!='s'}
  grid_summary[park]=short
 notes+='\n空间统计与离散化复核摘要（完整分配向量保存在结果JSON，不重复抄入说明）：\n\n```json\n'+json.dumps(dict(parks=r['parks'],grid_verification=grid_summary),ensure_ascii=False,indent=2)+'\n```\n'
 (ROOT/'docs/modeling_notes/question6_calculation_notes.md').write_text(notes,encoding='utf8')
 (ROOT/'docs/paper/question6_framework.md').write_text('''# 6 保护资源配置模型的跨大陆适配

当前正文为同名LaTeX与Markdown。案例为奇特旺与黄石；按用户2026-10-06要求，已用真实发布多边形、道路、位置点与ESA遥感生境替换合成网络。奇特旺主边界为WDPCA2026-10，边界面积一致性未通过，数值仅对应发布范围的有条件试算。原型移入历史备查，不混入正式结果。

## 6.1 模型结构与迁移方法
### 6.1.1 共同结构与本地参数
保留需求、服务、响应与预算关系；当地物种权重需校准。初步验证使用真实陆域面积份额。
### 6.1.2 可达性、技术与工作量的重建
给出真实路网成本、权限、服务LP及条件人员反求；逐项区分作业假设。
## 6.2 两类保护区的适配方案
### 6.2.1 奇特旺：重点物种、森林与季风通行
真实WDPCA发布多边形、OSM道路与位置；面积一致性检验未通过，限定为发布范围试算，明确季风、河流、冲突任务所需校准。
### 6.2.2 黄石：游客交互、季节交通与技术权限
真实NPS数据；补内部路网、季节管理交通、游客任务和授权。
## 6.3 真实空间数据验证与部署变化
真实空间统计与地图、8个速度和驻点情景、细网格和50米采样复核、独立优化核验。人员当量只对应所设陆域服务协议，不代表当地实际编制；不新增细碎三级标题。
''',encoding='utf8')
 print('Notes, provenance and revised framework saved.')
if __name__=='__main__':main()
