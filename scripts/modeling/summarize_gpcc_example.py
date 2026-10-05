"""Validate dates and polygon-weight the saved five-year GPCC example subset.

Uses the previously inspected 60-cell bbox, not a new download. Monthly depth
is weighted by area intersections on the project's local equal-area plane.
Results are interpolated coarse-grid estimates, not local station observations.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from pyproj import Geod, Transformer
from shapely.geometry import box, shape
from shapely.ops import transform, unary_union

from inspect_gpcc_example import decode_times

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/rainfall"
INSPECTION = OUT / "gpcc_1971_1975_inspection.json"
REGIONS = ROOT / "data/regions/processed/model_regions.geojson"
LAEA = "+proj=laea +lat_0=-19 +lon_0=15.75 +datum=WGS84 +units=m +no_defs"


def main():
    doc = json.loads(INSPECTION.read_text(encoding="utf-8"))
    time = doc["variables"]["time"]
    dates = decode_times(time["values"], time["attributes"]["units"], time["attributes"].get("calendar"))
    assert dates is not None and len(dates) == 60
    months = [d[:7] for d in dates]
    assert months == [f"{y}-{m:02d}" for y in range(1971, 1976) for m in range(1, 13)]
    doc["time"]["decoded_dates"] = dates
    doc["time"]["monthly_sequence_complete"] = True
    INSPECTION.write_text(json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    coords = doc["coordinates"]
    lats = coords["etosha_bbox_latitude_centers"]
    lons = coords["etosha_bbox_longitude_centers"]
    dx, dy = coords["longitude_spacing_degrees"], coords["latitude_spacing_degrees"]
    projector = Transformer.from_crs("EPSG:4326", LAEA, always_xy=True).transform
    cells = [transform(projector, box(lon - dx/2, lat - dy/2, lon + dx/2, lat + dy/2).segmentize(.001))
             for lat in lats for lon in lons]
    features = json.loads(REGIONS.read_text(encoding="utf-8"))["features"]
    regions = [transform(projector, shape(f["geometry"]).segmentize(.001)) for f in features]
    weights = np.array([[r.intersection(c).area / 1e6 for c in cells] for r in regions])
    areas = np.array([r.area/1e6 for r in regions])
    assert np.allclose(weights.sum(axis=1), areas, rtol=1e-7, atol=1e-6)
    park = unary_union(regions)
    park_weights = np.array([park.intersection(c).area / 1e6 for c in cells])
    assert np.allclose(weights.sum(axis=0), park_weights, rtol=1e-7, atol=1e-6)
    p = np.asarray(doc["variables"]["precip"]["bbox_values"], dtype=float).reshape(60, -1)
    assert p.shape == (60, len(cells)) and np.isfinite(p).all() and (p >= 0).all()
    regional = p @ weights.T / weights.sum(axis=1)
    park_mean = p @ park_weights / park_weights.sum()
    annual = park_mean.reshape(5, 12).sum(axis=1)
    region_records = [{"region_id": f["properties"]["region_id"],
                       "geometry_area_km2": float(areas[i]),
                       "grid_intersection_coverage": float(weights[i].sum()/areas[i]),
                       "number_of_intersecting_cells": int((weights[i] > 1e-8).sum()),
                       "monthly_precipitation_mm": [float(v) for v in regional[:, i]]}
                      for i, f in enumerate(features)]
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_sha256": doc["source_sha256"],
              "regions_sha256": hashlib.sha256(REGIONS.read_bytes()).hexdigest(),
              "source": doc["source"], "field": "precip", "units": "mm/month (monthly total depth)",
              "months": months, "region_records": region_records,
              "park_monthly_precipitation_mm": [float(v) for v in park_mean],
              "park_annual_precipitation_mm": {str(y): float(v) for y, v in zip(range(1971, 1976), annual)},
              "spatial_method": "GPCC grid/region polygon area intersections on local LAEA; geographic lines densified to 0.001 degree",
              "checks": {"60_contiguous_months": True, "17_regions": len(features) == 17,
                         "grid_covers_each_region": True, "regional_weights_sum_to_park_weights": True,
                         "sample_precipitation_nonnegative_and_present": True},
              "limitations": ["Five-year example only; insufficient as a standalone 50-year SPI baseline",
                              "0.25-degree gridded analysis; regional averages do not increase its spatial resolution",
                              "No independent station observation is implied for each region",
                              "No SPI or resource allocation was computed"]}
    (OUT / "gpcc_example_regional_monthly_1971_1975.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    geod = Geod(ellps="WGS84")
    east_width = geod.inv(15.5, -19, 15.75, -19)[2]/1000
    north_height = geod.inv(15.5, -19.125, 15.5, -18.875)[2]/1000
    variable_names = {name: item["attributes"].get("long_name", "") for name, item in doc["variables"].items()
                      if "bbox_diagnostic" in item}
    precip = doc["variables"]["precip"]["bbox_diagnostic"]
    lines = ["# GPCC示例文件检查", "", "日期：2026-10-05。已实际读取，不依赖文件名猜测。", "",
             "## 文件内容", "",
             "- GPCC/DWD月降水空间分析，Version 2025；实际覆盖1971-01至1975-12，共60个月。",
             "- 全球1440×720经纬度格网；0.25°分辨率；埃托沙纬度附近约" + f"{east_width:.1f}×{north_height:.1f} km/格。",
             "- 每个空间变量为60×720×1440。time是可扩展维，实际记录数60，不是缺失。",
             "- precip单位mm/month，按月累计降水深度处理，不再次乘天数，不按格点雨量直接求和。",
             "", "| 变量 | 文件内含义 | 使用位置 |", "|---|---|---|"]
    uses = {"precip": "主降水序列", "gauge": "格点内站点数，质量背景", "err": "插值误差，质量检查",
            "sys_err": "雨量计系统误差订正乘数，本样本区域均缺失", "gauge_int": "插值使用的站点数，质量背景",
            "dist_int": "插值所用站点平均距离，质量背景", "liquid": "液态降水比例，本样本区域均缺失",
            "solid": "固态降水比例，本样本区域均缺失", "precip_infill": "含气候站值填补的替代降水，先作对照"}
    for name, long_name in variable_names.items():
        units = doc["variables"][name]["attributes"].get("units", "")
        lines.append(f"| {name} | {long_name}；{units} | {uses.get(name, '需进一步确认')} |")
    lines += ["", "## 埃托沙样本核验", "",
              f"公园包围盒取到60格，60个月共3600个precip值全部有效；范围{precip['minimum']:.2f}—{precip['maximum']:.2f} mm/月。这不是全园月均值范围。",
              "gauge在包围盒内为0—3；0表示格点内无站点，不表示无雨或降水缺失。",
              "多数格点并无本格雨量站；应将结果称为格网分析估计。插值误差、站点数和距离作为质量背景，不新增保护风险因子。",
              "", "已按公园17个实际分区与0.25°格网的相交面积计算月降水平均深度。",
              f"公园实际相交格点数{int((park_weights > 1e-8).sum())}；各区格网覆盖完整，分区权重和与全园权重一致。",
              f"示例：1971年1月，全园面积加权降水约{park_mean[0]:.2f} mm。它不是包围盒简单平均。",
              "", "| 年份 | 样例全园年累计（mm） |", "|---|---:|"]
    for year, value in zip(range(1971, 1976), annual):
        lines.append(f"| {year} | {value:.2f} |")
    lines += ["", "## 进入模型的结论", "",
              "该文件是空间格网资料，可以形成17区月序列；不是仅有一套全园月均值。",
              "0.25°资料较粗，区内加权不提升原分辨率，小区可能共享相同格点，不能解释为独立高精度雨量。",
              "本文件只有5年。完整50年SPI仍需其余同版本同网格文件，并检查时间连续性、单位及重复月。",
              "主方案仍为完整雨季SPI-6派生一个不足指标；当前只完成样例读取和分区提取，没有SPI实算。",
              "", "[原始检查JSON](gpcc_1971_1975_inspection.json)、[分区月降水JSON](gpcc_example_regional_monthly_1971_1975.json)、[降水指标方案](../../docs/降水指标设计.md)。", ""]
    (OUT / "GPCC示例文件检查.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"time_first_last": [months[0], months[-1]], "months": len(months),
                      "fields": variable_names,
                      "field_units": {name: doc['variables'][name]['attributes'].get('units') for name in variable_names},
                      "bbox_validity": {name: doc['variables'][name]['bbox_diagnostic']['valid_count'] for name in variable_names},
                      "park_intersecting_grid_cells": int((park_weights > 1e-8).sum()),
                      "region_count": len(features), "park_january_1971_mm": float(park_mean[0]),
                      "annual_park_mm": report['park_annual_precipitation_mm'],
                      "checks": report['checks'], "temporary_nc_remaining": (ROOT/'tmp/rainfall/gpcc_1971_1975_inspection.nc').exists()},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
