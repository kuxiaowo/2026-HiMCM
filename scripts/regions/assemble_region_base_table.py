"""Join frozen spatial units, WorldCover structure and historical animal inputs.

This is a regional data table, not a conservation score or resource allocation.
Quality fields and alternative masks must not all be weighted as independent factors.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/regions"
REGIONS = ROOT / "data/regions/processed/model_regions.geojson"
ECOLOGY = OUT / "ecology/region_ecology.json"
SPECIES = ROOT / "output/model1/species_region_counts_2015.json"
CLASS_ZH = {10: "林地", 20: "灌丛", 30: "草地", 40: "农田", 50: "建成区", 60: "裸地/稀疏植被", 70: "冰雪", 80: "永久水面", 90: "草本湿地", 95: "红树林", 100: "苔藓/地衣"}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    spatial = json.loads(REGIONS.read_text(encoding="utf-8"))["features"]
    ecol_doc = json.loads(ECOLOGY.read_text(encoding="utf-8"))
    if ecol_doc["regions_sha256"] != digest(REGIONS):
        raise ValueError("Ecology was not computed for this frozen region file; rerun zonal statistics")
    ecol = {r["region_id"]: r for r in ecol_doc["regions"]}
    census = json.loads(SPECIES.read_text(encoding="utf-8"))
    core = [s for s in census["species"] if s["adoption"] == "core_with_flags"]
    count_rows = {(r["stratum"], r["species_code"]): r for r in census["rows"]}
    ids = {f["properties"]["region_id"] for f in spatial}
    assert len(ids) == 17 and set(ecol) == ids and len(core) == 6
    rows, schema = [], []
    for feature in spatial:
        s = feature["properties"]
        rid = s["region_id"]
        e = ecol[rid]
        shares = {k: e[f"wc_{k}_share_valid"] for k in CLASS_ZH}
        assert abs(sum(shares.values()) - 1) < 1e-10
        assert abs(s["area_km2"] - e["area_km2"]) < 0.00001
        dominant = max(shares, key=shares.get)
        row = {
            "region_id": rid,
            "region_kind": s["region_kind"],
            "display_name_zh": s["display_name_zh"],
            "geometry_area_km2": s["area_km2"],
            "survey_area_report_2015_km2": s["survey_area_report_km2"],
            "geometry_area_difference_flag": s["area_difference_flag"],
            "animal_data_status": "historical_candidates_with_quality_flags" if s["region_kind"] == "survey_stratum" else "unknown_not_zero",
            "landcover_year": 2021,
            "landcover_valid_coverage": e["valid_coverage"],
            "dominant_landcover_code": dominant,
            "dominant_landcover_name_zh": CLASS_ZH[dominant],
            "tree_share_wc2021": shares[10],
            "shrub_share_wc2021": shares[20],
            "grass_share_wc2021": shares[30],
            "bare_sparse_share_wc2021": shares[60],
            "permanent_water_share_wc2021": shares[80],
            "herbaceous_wetland_share_wc2021": shares[90],
            "other_landcover_share_wc2021": sum(shares[k] for k in (40, 50, 70, 95, 100)),
            "fuel_proxy_raw_area_wc2021_km2": e["fuel_proxy_before_pan_mask_km2"],
            "fuel_proxy_baseline_area_wc2021_km2": e["fuel_proxy_area_km2"],
            "main_pan_fuel_mask_applied": e["main_pan_excluded_from_fuel"],
        }
        for sp in core:
            original = count_rows.get((rid, sp["species_code"]))
            row[f"candidate_count_{sp['species_code']}_2015"] = original.get("candidate_baseline_count") if original else None
        rows.append(row)
    for sp in core:
        schema.append({"column": f"candidate_count_{sp['species_code']}_2015", "species_code": sp["species_code"], "name_zh": sp["name_zh"], "report_taxon": sp["report_taxon"], "unit": "individuals, historical aerial survey estimate / source-approved candidate", "source": "output/model1/species_region_counts_2015.json candidate_baseline_count", "quality_details": "output/regions/core_species_region_link_2015.csv; blank/non-detection treatment is a modelling assumption recorded in the source feasibility audit"})
    null_rows = [r for r in rows if r["region_kind"] != "survey_stratum"]
    animal_cols = [f"candidate_count_{sp['species_code']}_2015" for sp in core]
    assert all(r[c] is None for r in null_rows for c in animal_cols)
    with (OUT / "region_base_data.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    document = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "spatial_partition_and_base_data_complete; value/risk/allocation_not_yet_computed",
        "regional_rows": rows,
        "animal_columns": schema,
        "field_usage": {
            "geometry_area_km2": "spatial overlay and area-weighted aggregation; final WGS84 densified geometry area",
            "survey_area_report_2015_km2": "historical animal density denominator; keep distinct from generalized GIS area",
            "*_share_wc2021": "dimensionless habitat composition, already in [0,1]; code numbers are categories, not continuous scores; do not add an independent weight for every composition and fuel derivative",
            "fuel_proxy_raw_area_wc2021_km2": "class 10/20/30 potential combustible habitat proxy, not observed fuel load",
            "fuel_proxy_baseline_area_wc2021_km2": "same proxy, with PAN_MAIN set to zero only in baseline mask; raw pan vegetation retained for sensitivity",
            "candidate_count_*_2015": "six historical candidates for subsequent conservation value calculation; density, legal category and quality flags remain in the long table",
            "dominant_landcover_code": "descriptive class only, never normalize or use as an ordered factor",
            "landcover_valid_coverage": "data completeness QA, not ecological quality or classification accuracy",
        },
        "later_tasks": ["value V with species normalization and declared legal-category weight assumptions", "road-entry proxy E and station response matrix T on the actual road graph", "historical late-dry-season fire exposure F", "verified water-point context W and plant/habitat contribution", "rainfall anomaly R; use one park-wide climate scenario if subregional data remain unavailable", "explicit missing-value scenario for supplementary unsurveyed units before full-park resource allocation"],
        "quality_checks": {"region_id_one_to_one": True, "all_ecology_hashes_match": True, "all_class_shares_sum_to_one": True, "geometry_ecology_area_agreement_km2_tolerance": 0.00001, "unsurveyed_animal_values_preserved_null": True, "field_count_is_not_number_of_independent_factors": True},
        "source_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in (REGIONS, ECOLOGY, SPECIES, Path(__file__))},
    }
    (OUT / "region_base_data.json").write_text(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    qa = json.loads((OUT / "partition_quality_report.json").read_text(encoding="utf-8"))
    table = "\n".join(f"| {r['region_id']} | {r['geometry_area_km2']:.2f} | {r['dominant_landcover_name_zh']} | {'2015候选值' if r['region_kind']=='survey_stratum' else '缺失，非零'} |" for r in rows)
    (OUT / "分区成果说明.md").write_text(f"""# 国家公园分区成果：第一版

完成17个空间单元：15个2015动物调查统计单元、主盐沼近似区、其他调查外残余。采用African Elephant Database公开概化坐标，依据原报告图核对与修复拓扑；没有重新把历史动物数量分摊到生态小区。ENP3、4、10保持ENP3410合并统计。

## 当前成果

- [分区图](partition_map.png)与[可编辑矢量图](partition_map.svg)、[源图对照](partition_source_comparison.png)。
- [GeoJSON分区](../../data/regions/processed/model_regions.geojson)和[QGIS GeoPackage](etosha_model_regions.gpkg)。
- [模型区域基础表](region_base_data.csv)与[字段解释、物种映射及质控](region_base_data.json)。
- [完整生态统计](ecology/region_ecology.csv)、[生态底图](ecology/worldcover_2021_preview.png)、[生态处理说明](ecology/生态底图处理说明.md)。
- [6物种关联长表](core_species_region_link_2015.csv)与[全部原始物种行关联表](species_region_link_2015.csv)。
- [全过程记录](../../docs/modeling_process.md)、[论文分区方法段](../../docs/paper/partition_methods.md)、[源资料审计](strata_source_audit.md)。

## 单元与生态结构

主导地类用于描述各区，完整地类比例参与栖息地/火灾掩膜构造，不把类别编码或主导地类直接变成保护价值等级。下面的面积是空间几何面积；2015动物密度继续使用原报告面积。

| 区域编号 | 空间面积 km² | WorldCover 2021主导地类 | 动物数据状态 |
|---|---:|---|---|
{table}

## 核验与局限

- 空间单元无效几何、空单元、重复编号均为0；局部等面积拓扑在1 m²容差内完整覆盖公园，未发现重叠或漏区。另在原EPSG:4326园界口径独立核对，缺口/外溢均低于0.01 m²。
- 17区原生分类像元归属合计与全园一致至浮点误差，分类有效覆盖率100%；这不是分类准确率100%。
- ENP8、ENP9与报告面积偏差约13%–14%，已留标记；几何面积不强制匹配报告。其余窄重叠采用小区优先假设，反向优先比较最大相对面积变化约{qa['overlap_priority_sensitivity']['max_relative_region_area_change_percent']:.3f}%，不等于已验证风险/资源排序稳定。
- 主盐沼用未覆盖范围形态学提取并与源图核对。250/500/1000 m尺度的面积敏感性已保存；主盐沼内约3.60%的原始林/灌/草分类保留，基准燃料置零是掩膜假设，不认为盐沼绝无植被。
- 调查外动物数量保留null，不作零价值处理。全园配置前仍需明确这些单元的价值缺失情景。
- 2015动物、2021土地覆盖、2026道路资料合用是静态演示的时间近似，不冒充2026实测。
- 降水数据不参与划界。分区逐月降水若无法取得，使用全园统一气候情景，不人为制造各区降雨差异。

## 下一步与复现

基础表已经可以按region_id连接道路、水源与历史燃烧指标。当前没有计算最终保护评分或资源分配，也没有给生态比例、动物数量、质量标记分别叠加自由权重。

使用conda环境；包版本在[环境文件](../../environment-regions.yml)，空间处理源/输出哈希在[分区清单](partition_build_manifest.json)，生态源下载URL/哈希在[生态清单](../../data/ecology/raw/worldcover_2021_source_manifest.json)。工作区原始文件已在位时依次运行：

```powershell
conda run -n himcn-regions python scripts/regions/build_model_regions.py
conda run -n himcn-regions python scripts/regions/prepare_ecology.py --offline --regions data/regions/processed/model_regions.geojson
conda run -n himcn-regions python scripts/regions/assemble_region_base_table.py
```

首次建立环境先运行 `conda env create -f environment-regions.yml`；当前实际运行环境为已有的 `himcn-roads`。若生态原始瓦片缺失，取消 `--offline` 让脚本从清单公开地址下载。图、数据和论文需保留African Elephant Database、OpenStreetMap contributors、ESA WorldCover的来源与许可归属。
""", encoding="utf-8")
    print(json.dumps({"regional_rows": len(rows), "core_species": [s["species_code"] for s in core], "base_fields": len(rows[0]), "quality_checks": document["quality_checks"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
