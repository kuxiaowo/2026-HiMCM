# 第六题原始数据上传说明

按用户要求，超过100 MB（100,000,000字节）的文件保留本地并加入项目根目录 `.gitignore`，不上传GitHub：

| 文件 | 字节数 |
| --- | ---: |
| `nepal-latest.osm.pbf` | 414519125 |
| `worldcover/ESA_WorldCover_10m_2021_v200_N27E081_Map.tif` | 104848806 |
| `worldcover/ESA_WorldCover_10m_2021_v200_N27E084_Map.tif` | 104225123 |
| `worldcover/ESA_WorldCover_10m_2021_v200_N42W111_Map.tif` | 105959600 |

其余小于阈值的原始资料、处理后的数据、脚本、结果、正式正文和历史备查一并上传。所有原始资料的下载URL、大小与SHA256保存在 `q6_real_source_manifest.json`。已保存的处理数据足以运行空间模型，重新从原始资料提取时需恢复缺少的大文件。

在项目根目录运行以下命令，可按源URL下载缺少的PBF和全部六块WorldCover栅格；已存在文件会保留：

```powershell
& 'F:/Python/anaconda/envs/himcn-roads/python.exe' scripts/modeling/fetch_question6_real_data.py
```

OSM的`latest`下载地址随发布变化；新下载不保证等于2026-10-04快照。应核对源清单SHA256，精确复现使用对应日期的Geofabrik存档，并保留已经上传的处理数据作为本次计算证据。
