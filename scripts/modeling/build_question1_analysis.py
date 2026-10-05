"""Q1 tables, conditional uncertainty envelopes, and publication figures.

Run build_question1_baseline.py first, using the project's conda environment.
All quantities are historical responsibility components, never current threat
probabilities, an optimized deployment, or a calibrated protection score.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from build_question1_baseline import responsibility, ranks, WEIGHTS
from protection_metrics import check_metric_semantics, evaluate_protection_standard

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/question1"
INPUTS = [ROOT / "output/question1/question1_baseline.json",
          ROOT / "output/regions/region_base_data.json",
          ROOT / "output/model1/species_region_counts_2015.json",
          ROOT / "data/regions/processed/model_regions.geojson"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def interval_envelopes(rows, core, audit_rows, weights):
    """Exact value extrema over a rectangular count scenario set.

    Source marginal CI endpoints define the set, not a joint confidence set.
    Blank estimates with printed zero density are fixed to zero conditionally.
    Different regions' extrema occur in DIFFERENT count configurations.
    """
    ws = {s["species_code"]: weights[s["species_code"]] for s in core}
    wsum = math.fsum(ws.values())
    cells, conditional_zero = {}, []
    for row in rows:
        rid = row["region_id"]
        for s in ws:
            source = audit_rows[(rid, s)]
            point = row[f"candidate_count_{s}_2015"]
            low, high = source["ci_lower"], source["ci_upper"]
            if low is None or high is None:
                flags = source["quality_flags"]
                if point != 0 or "baseline_zero_is_explicit_nondetection_assumption" not in flags:
                    raise ValueError(f"Unusable count interval: {rid}/{s}")
                low = high = 0.0
                conditional_zero.append({"region_id": rid, "species_code": s})
            low = max(0.0, low)
            assert low <= point <= high, (rid, s, low, point, high)
            cells[(rid, s)] = (low, high)
    low_total = {s: math.fsum(cells[(r["region_id"], s)][0] for r in rows) for s in ws}
    high_total = {s: math.fsum(cells[(r["region_id"], s)][1] for r in rows) for s in ws}
    result = {}
    for row in rows:
        rid = row["region_id"]
        low_share, high_share = {}, {}
        for s in ws:
            low, high = cells[(rid, s)]
            low_denom = low + high_total[s] - high
            high_denom = high + low_total[s] - low
            assert low_denom > 0 and high_denom > 0
            low_share[s] = low / low_denom
            high_share[s] = high / high_denom
        result[rid] = {
            "lower": math.fsum(ws[s] * low_share[s] for s in ws) / wsum,
            "upper": math.fsum(ws[s] * high_share[s] for s in ws) / wsum,
        }
        # Verify each claimed bound by evaluating its attaining configuration.
        for endpoint, own, other in [("lower", 0, 1), ("upper", 1, 0)]:
            scenario = [dict(r, **{f"candidate_count_{s}_2015":
                        cells[(r["region_id"], s)][own if r["region_id"] == rid else other]
                        for s in ws}) for r in rows]
            achieved, _, _ = responsibility(scenario, core, WEIGHTS["baseline_categories"])
            assert math.isclose(achieved[rid], result[rid][endpoint], abs_tol=1e-12)
    return result, conditional_zero


def nondetection_scenarios(rows, core, baseline_ranks):
    result = []
    for fraction in (.01, .05):
        scenario = [dict(row) for row in rows]
        additions = {}
        for species in core:
            s = species["species_code"]
            total = math.fsum(r[f"candidate_count_{s}_2015"] for r in rows)
            zero_rows = [r for r in scenario if r[f"candidate_count_{s}_2015"] == 0]
            area = math.fsum(r["survey_area_report_2015_km2"] for r in zero_rows)
            if not zero_rows:
                continue
            reserve = total * fraction
            for row in zero_rows:
                row[f"candidate_count_{s}_2015"] = reserve * row["survey_area_report_2015_km2"] / area
            assert math.isclose(math.fsum(r[f"candidate_count_{s}_2015"] for r in scenario),
                                total + reserve, abs_tol=1e-9)
            additions[s] = reserve
        values, _, _ = responsibility(scenario, core, WEIGHTS["baseline_categories"])
        rank = ranks(values)
        result.append({"fraction_of_survey_species_total_added_to_nondetected_units": fraction,
                       "allocation_basis": "original_survey_area_among_zero_baseline_rows",
                       "scenario_not_population_estimate": True,
                       "added_counts_by_species": additions, "values": values, "ranks": rank,
                       "top5": sorted(values, key=rank.get)[:5],
                       "max_rank_change": max(abs(rank[i] - baseline_ranks[i]) for i in rank)})
    return result


def configure_plots():
    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
                         "axes.unicode_minus": False, "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "path"})


def make_figures(baseline, result):
    configure_plots()
    surveyed = [r for r in baseline["regions"] if r["region_kind"] == "survey_stratum"]
    surveyed.sort(key=lambda r: r["animal_responsibility_rank_among_15_survey_units"])
    labels = [r["region_id"] for r in surveyed]
    point = np.array([r["animal_responsibility_share_2015"] for r in surveyed]) * 100
    lower = np.array([result["conditional_count_interval_envelopes"][i]["lower"] for i in labels]) * 100
    upper = np.array([result["conditional_count_interval_envelopes"][i]["upper"] for i in labels]) * 100
    fig, (ax, habitat) = plt.subplots(1, 2, figsize=(13, 7.8), gridspec_kw={"width_ratios": [1.15, 1]})
    y = np.arange(len(labels))
    ax.barh(y, point, color=["#136a77" if i < 5 else "#acd3d8" for i in y], height=.65)
    ax.errorbar(point, y, xerr=[point - lower, upper - point], fmt="o", color="#263e4a",
                elinewidth=1.1, capsize=3, markersize=3)
    ax.set(yticks=y, yticklabels=labels, xlabel="动物责任份额（%）", title="六类动物：历史责任及条件性范围（2015）")
    ax.invert_yaxis()
    ax.set_xlim(0, max(upper) * 1.18)
    for i, v in enumerate(point):
        ax.text(upper[i] + .35, i, f"{v:.2f}%", va="center", fontsize=9)
    ax.grid(axis="x", color="#e4e8ec", zorder=0)
    ax.set_axisbelow(True)
    fuel = sorted(baseline["regions"], key=lambda r: -r["fuel_habitat_responsibility_share_2021"])
    fy = np.arange(len(fuel))
    fv = np.array([r["fuel_habitat_responsibility_share_2021"] for r in fuel]) * 100
    habitat.barh(fy, fv, color="#668251", height=.65)
    habitat.set(yticks=fy, yticklabels=[r["region_id"] for r in fuel],
                xlabel="可燃生境面积责任（%）", title="生境：草 / 灌 / 林面积责任（2021）")
    habitat.invert_yaxis()
    habitat.set_xlim(0, max(fv) * 1.24)
    for i, v in enumerate(fv):
        habitat.text(v + .15, i, f"{v:.2f}%", va="center", fontsize=9)
    habitat.grid(axis="x", color="#e4e8ec", zorder=0)
    habitat.set_axisbelow(True)
    fig.suptitle("不同保护对象形成不同的区域责任", fontsize=18, fontweight="bold", x=.055, ha="left")
    fig.text(.055, .052, "横线是源表区间构造的条件性范围，不是责任份额的联合95%置信区间；未检出单元暂固定为零。", fontsize=9)
    fig.text(.055, .025, "动物调查外值未知；PAN_MAIN的燃料基准为零，盐沼生态价值仍保留。两图均非综合风险或实际保护分数。", fontsize=9)
    fig.tight_layout(rect=[.025, .09, .99, .94], w_pad=3)
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"question1_responsibility_comparison.{suffix}", dpi=180, facecolor="white")
    plt.close(fig)

    regions = gpd.read_file(INPUTS[3]).to_crs("+proj=laea +lat_0=-19 +lon_0=15.75 +datum=WGS84 +units=m +no_defs")
    values = {r["region_id"]: r["animal_responsibility_share_2015"] for r in baseline["regions"]}
    regions["animal_percent"] = regions["region_id"].map(lambda rid: None if values[rid] is None else values[rid] * 100)
    fig, ax = plt.subplots(figsize=(12, 5.8))
    regions.plot(column="animal_percent", ax=ax, cmap="YlGnBu", vmin=0, vmax=max(point),
                 edgecolor="#7c8b93", linewidth=.55, legend=True,
                 legend_kwds={"label": "六类动物责任份额（%）", "shrink": .73},
                 missing_kwds={"color": "#eeeeea", "hatch": "///", "edgecolor": "#b4b7ad"})
    for _, row in regions.iterrows():
        if row["region_id"] == "UNSURVEYED_OTHER":
            continue
        geom = row.geometry
        part = max(geom.geoms, key=lambda x: x.area) if geom.geom_type == "MultiPolygon" else geom
        loc = part.representative_point()
        label = "主盐沼\n动物值未知" if row["region_id"] == "PAN_MAIN" else row["region_id"]
        ax.text(loc.x, loc.y, label, ha="center", va="center", fontsize=8,
                color="#20272c", bbox=dict(facecolor="white", edgecolor="none", alpha=.78, pad=1.7))
    ax.set_title("2015年六类动物区域责任：全园空间口径", fontsize=17, loc="left", pad=18)
    ax.legend(handles=[Patch(facecolor="#eeeeea", hatch="///", edgecolor="#b4b7ad",
                             label="调查外动物值未知，继续保留保护对象")],
              loc="lower left", frameon=False, fontsize=9, bbox_to_anchor=(0, -.12))
    ax.set_axis_off()
    fig.text(.075, .035, "分区为公开概化坐标修复后的模型单元；黑犀牛等重点对象未进入该动物数量分项。", fontsize=9)
    fig.tight_layout(rect=[0, .085, 1, 1])
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"question1_animal_responsibility_map.{suffix}", dpi=180, facecolor="white")
    plt.close(fig)


def main():
    baseline, base, audit = [load(path) for path in INPUTS[:3]]
    for source in INPUTS[1:3]:
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        assert baseline["sources_sha256"][str(source.relative_to(ROOT))] == actual, "Stale baseline source"
    assert baseline["metric_script_sha256"] == hashlib.sha256(
        Path(__file__).with_name("protection_metrics.py").read_bytes()).hexdigest(), "Rerun baseline after metric changes"
    rows = [r for r in base["regional_rows"] if r["region_kind"] == "survey_stratum"]
    core = [s for s in audit["species"] if s["adoption"] == "core_with_flags"]
    source_rows = {(r["stratum"], r["species_code"]): r for r in audit["rows"]}
    weights = {s["code"]: s["weight"] for s in baseline["species"]}
    baseline_rank = {r["region_id"]: r["animal_responsibility_rank_among_15_survey_units"]
                     for r in baseline["regions"] if r["region_kind"] == "survey_stratum"}
    envelopes, zeros = interval_envelopes(rows, core, source_rows, weights)
    sensitivity = nondetection_scenarios(rows, core, baseline_rank)
    top = sorted(baseline_rank, key=baseline_rank.get)
    animal_lookup = {r["region_id"]: r["animal_responsibility_share_2015"] for r in baseline["regions"]}
    for rid, bound in envelopes.items():
        assert bound["lower"] <= animal_lookup[rid] <= bound["upper"]
    habitat_top = sorted(baseline["regions"], key=lambda r: -r["fuel_habitat_responsibility_share_2021"])
    metric_demo = dict(demands=[9, 1], services=[8.05 / 9, .95], critical_services={"rhino": .95},
                       safeguards={"water_status_checked": True, "pan_monitoring": True}, scope_complete=True)
    # Entirely constructed examples explaining the definition; no park data.
    examples = {
        "complete_constructed_example": evaluate_protection_standard(**metric_demo),
        "same_score_but_critical_failure": evaluate_protection_standard(
            **dict(metric_demo, services=[8.3 / 9, .7], critical_services={"rhino": .7})),
        "same_score_but_water_unknown": evaluate_protection_standard(
            **dict(metric_demo, safeguards={"water_status_checked": None, "pan_monitoring": True})),
    }
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime_versions": {"python": platform.python_version(), "numpy": np.__version__,
                             "matplotlib": matplotlib.__version__, "geopandas": gpd.__version__},
        "historical_six_taxa_top5_share": math.fsum(animal_lookup[rid] for rid in top[:5]),
        "historical_six_taxa_top2_share": math.fsum(animal_lookup[rid] for rid in top[:2]),
        "fuel_habitat_top5": [{"region_id": r["region_id"], "share": r["fuel_habitat_responsibility_share_2021"]} for r in habitat_top[:5]],
        "conditional_count_interval_envelopes": envelopes,
        "envelope_semantics": "Extrema over rectangular source-CI-endpoint scenarios; conditional on fixed nondetection zeros. Not a joint 95% CI, not a population forecast, not simultaneously attainable across regions.",
        "nondetection_fixed_zero_cells": zeros,
        "nondetection_sensitivity": sensitivity,
        "constructed_standard_examples_not_park_observations": examples,
        "checks": {"baseline_matches_current_sources_and_metric_code": True,
                   "conditional_envelopes_attained_by_explicit_scenarios": True,
                   "baseline_inside_all_envelopes": True,
                   "nondetection_reserve_counts_conserved": True,
                   "metric_semantics": check_metric_semantics()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "question1_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (OUT / "question1_regional_indicators.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["region_id", "animal_share_2015", "animal_rank_15", "conditional_lower", "conditional_upper",
                  "survey_area_2015_km2", "geometry_area_km2", "fuel_share_2021", "fuel_area_km2", "data_status"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in baseline["regions"]:
            rid = row["region_id"]
            envelope = envelopes.get(rid, {})
            writer.writerow(dict(region_id=rid, animal_share_2015=row["animal_responsibility_share_2015"],
                animal_rank_15=row["animal_responsibility_rank_among_15_survey_units"],
                conditional_lower=envelope.get("lower"), conditional_upper=envelope.get("upper"),
                survey_area_2015_km2=row["survey_area_report_2015_km2"], geometry_area_km2=row["geometry_area_km2"],
                fuel_share_2021=row["fuel_habitat_responsibility_share_2021"], fuel_area_km2=row["fuel_proxy_baseline_area_km2"],
                data_status="historical_candidate_with_quality_flags" if rid in baseline_rank else "animal_unknown_not_zero"))
    lines = ["# 第一问补充实算：调查不确定性与保护判定", "",
             "由`scripts/modeling/build_question1_analysis.py`生成。源文件SHA-256、完整场景与语义检查见JSON。", "",
             "## 1. 历史责任的集中程度", "",
             f"动物责任前二区合计{result['historical_six_taxa_top2_share']:.2%}，前五区合计{result['historical_six_taxa_top5_share']:.2%}。",
             "这是六类动物的加权责任份额，不能解释为全园全部动物个体占比或推荐预算比例。", "",
             "## 2. 区域责任的条件性区间范围", "",
             "各物种使用源表逐区上下限构造矩形场景集；目标区取下限、其余区取上限得到该区最小份额，反向得到最大份额。",
             f"未检出且未提供区间的{len(zeros)}个单元格固定为基准零，因此范围有条件性。不同区域端点对应不同场景，不能将端点相加。",
             "此范围不是联合95%置信区间，不修复原表质量问题；未假定抽样误差独立、正态或已知相关性。", "",
             "| 区域 | 基准责任 | 条件性下界 | 条件性上界 |", "|---|---:|---:|---:|"]
    for rid in top:
        lines.append(f"| {rid} | {animal_lookup[rid]:.2%} | {envelopes[rid]['lower']:.2%} | {envelopes[rid]['upper']:.2%} |")
    lines += ["", "区间有明显重叠；精确名次不能只凭基准权重敏感性就称为稳健。", "",
              "## 3. 未检出不等于不存在：压力情景", "",
              "对存在基准零分区的物种，额外设置相当于其调查总量1%/5%的假设未检出数量，按原调查面积分配给零分区。",
              "1%/5%是压力测试幅度，不是漏检率估计、置信区间或新增实测数量；没有零分区的物种不添加。", "",
              "| 假设额外数量 | 前五区 | 最大名次变化 |", "|---|---|---:|"]
    for case in sensitivity:
        lines.append(f"| {case['fraction_of_survey_species_total_added_to_nondetected_units']:.0%} | {'、'.join(case['top5'])} | {case['max_rank_change']} |")
    lines += ["", "## 4. 可燃生境面积责任", "", "| 区域 | 面积责任份额 |", "|---|---:|"]
    for row in habitat_top:
        lines.append(f"| {row['region_id']} | {row['fuel_habitat_responsibility_share_2021']:.2%} |")
    lines += ["", "该排序是面积分项，不是实际火灾风险排序；主盐沼燃料基准为零，不抹去鸟类与盐沼生态价值。", "",
              "## 5. 保护判定的纯构造示例", "",
              "假设两目标需求为9/1，第二目标是重点对象；第一/三例服务为0.894444…/0.95，第二例为0.922222…/0.70。",
              "三个例子均为90分，所有值仅为公式演示，不是公园部署结果；每例重点服务与同一目标的总分输入一致。", "",
              "| 示例 | 重点对象服务 | 水源检查状态 | 判定 |", "|---|---:|---|---|",
              "| 范围完整且底线齐全 | 0.95 | 已达标 | 满足规划标准 |",
              "| 同分但重点对象失守 | 0.70 | 已达标 | 未达标 |",
              "| 同分但水源信息缺失 | 0.95 | 未知 | 资料不全，不能认证 |", "",
              "逐班次判定代码见`protection_metrics.py`。80分/重点0.90为团队阈值，尚未验证可达性。", "",
              "## 6. 图表", "",
              "![责任与条件性范围](question1_responsibility_comparison.png)", "",
              "![动物责任地图](question1_animal_responsibility_map.png)", ""]
    (OUT / "第一问补充实算.md").write_text("\n".join(lines), encoding="utf-8")
    make_figures(baseline, result)
    print(json.dumps({"top5_share": result["historical_six_taxa_top5_share"],
                      "top2_share": result["historical_six_taxa_top2_share"],
                      "fuel_top5": result["fuel_habitat_top5"],
                      "nondetection_scenarios": [{k: x[k] for k in ["fraction_of_survey_species_total_added_to_nondetected_units", "top5", "max_rank_change"]} for x in sensitivity],
                      "checks_passed": True, "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
