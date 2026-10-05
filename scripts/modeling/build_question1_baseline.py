"""Compute the available Q1 baseline without inventing missing threat data.

Run with the project's conda Python. Inputs are frozen regional JSON and the
audited historical species JSON. Outputs deliberately do not contain a final
park protection score or a purported complete conservation-priority ranking.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from protection_metrics import check_metric_semantics

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "output/regions/region_base_data.json"
SPECIES = ROOT / "output/model1/species_region_counts_2015.json"
OUT = ROOT / "output/question1"
WEIGHTS = {
    "equal_categories": (1, 1, 1),
    "compressed_categories": (1, 1.5, 2),
    "baseline_categories": (1, 2, 3),
    "emphasized_categories": (1, 3, 5),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def category_weight(species, weights):
    if species["law_class"] == "specially_protected_game":
        return weights[2]
    if species["law_class"] in {"protected_game", "protected_game_birds"}:
        return weights[1]
    if species["law_class"] == "huntable_game":
        return weights[0]
    raise ValueError(f"Unknown law category: {species['law_class']}")


def responsibility(rows, selected_species, weights):
    totals = {
        s["species_code"]: math.fsum(r[f"candidate_count_{s['species_code']}_2015"] for r in rows)
        for s in selected_species
    }
    if any(n <= 0 for n in totals.values()):
        raise ValueError("A zero or unknown species denominator is not valid")
    ws = {s["species_code"]: category_weight(s, weights) for s in selected_species}
    wsum = math.fsum(ws.values())
    values = {
        r["region_id"]: math.fsum(
            ws[s] * r[f"candidate_count_{s}_2015"] / totals[s] for s in totals
        ) / wsum
        for r in rows
    }
    return values, totals, ws


def ranks(values):
    # There are no tied baseline values in these inputs; stable region-ID tie break.
    return {rid: rank for rank, (rid, _) in enumerate(
        sorted(values.items(), key=lambda item: (-item[1], item[0])), 1)}


def main():
    base = json.loads(BASE.read_text(encoding="utf-8"))
    audit = json.loads(SPECIES.read_text(encoding="utf-8"))
    rows = base["regional_rows"]
    surveyed = [r for r in rows if r["region_kind"] == "survey_stratum"]
    unknown = [r for r in rows if r["region_kind"] != "survey_stratum"]
    core = [s for s in audit["species"] if s["adoption"] == "core_with_flags"]
    assert len(surveyed) == 15 and len(unknown) == 2 and len(core) == 6
    for r in surveyed:
        assert r["survey_area_report_2015_km2"] > 0
        for s in core:
            n = r[f"candidate_count_{s['species_code']}_2015"]
            assert n is not None and math.isfinite(n) and n >= 0
    assert all(r[f"candidate_count_{s['species_code']}_2015"] is None
               for r in unknown for s in core)
    values, totals, ws = responsibility(surveyed, core, WEIGHTS["baseline_categories"])
    assert all(math.isclose(totals[s["species_code"]], s["individual_table_total"]["count_estimate"])
               for s in core)
    assert math.isclose(math.fsum(values.values()), 1, abs_tol=1e-12)
    baseline_rank = ranks(values)
    density = {r["region_id"]: values[r["region_id"]] / r["survey_area_report_2015_km2"]
               for r in surveyed}
    density_rank = ranks(density)
    weighted_counts = {r["region_id"]: math.fsum(
        ws[s] * r[f"candidate_count_{s}_2015"] for s in totals) for r in surveyed}
    count_total = math.fsum(weighted_counts.values())
    raw_values = {rid: v / count_total for rid, v in weighted_counts.items()}
    raw_rank = ranks(raw_values)
    direct_species_share = {s: ws[s] * totals[s] / count_total for s in totals}
    balanced_species_share = {s: ws[s] / math.fsum(ws.values()) for s in totals}
    fuel_total = math.fsum(r["fuel_proxy_baseline_area_wc2021_km2"] for r in rows)
    assert fuel_total > 0
    fuel_values = {r["region_id"]: r["fuel_proxy_baseline_area_wc2021_km2"] / fuel_total
                   for r in rows}
    scenarios = []
    for name, weights in WEIGHTS.items():
        vv, _, _ = responsibility(surveyed, core, weights)
        rr = ranks(vv)
        scenarios.append({"scenario": name, "category_weights_huntable_protected_special": weights,
                          "values": vv, "ranks": rr,
                          "top5": sorted(vv, key=rr.get)[:5],
                          "max_rank_change_from_baseline": max(abs(rr[i] - baseline_rank[i]) for i in rr)})
    leave_one_out = []
    for omitted in core:
        vv, _, _ = responsibility(surveyed, [s for s in core if s != omitted],
                                  WEIGHTS["baseline_categories"])
        rr = ranks(vv)
        leave_one_out.append({"omitted_species": omitted["species_code"],
                              "top5": sorted(vv, key=rr.get)[:5],
                              "max_rank_change": max(abs(rr[i] - baseline_rank[i]) for i in rr)})
    # Scaling one species' entire population should not change its relative distribution.
    doubled = [dict(r, candidate_count_Eb_2015=r["candidate_count_Eb_2015"] * 2) for r in surveyed]
    scaled, _, _ = responsibility(doubled, core, WEIGHTS["baseline_categories"])
    assert all(math.isclose(values[rid], scaled[rid], abs_tol=1e-12) for rid in values)
    quality_lookup = {(r["stratum"], r["species_code"]): r["quality_flags"] for r in audit["rows"]}
    result_rows = []
    for r in rows:
        rid = r["region_id"]
        result_rows.append({
            "region_id": rid, "region_kind": r["region_kind"],
            "geometry_area_km2": r["geometry_area_km2"],
            "survey_area_report_2015_km2": r["survey_area_report_2015_km2"],
            "animal_responsibility_share_2015": values.get(rid),
            "animal_responsibility_rank_among_15_survey_units": baseline_rank.get(rid),
            "animal_responsibility_per_survey_km2": density.get(rid),
            "density_rank_among_15_survey_units": density_rank.get(rid),
            "direct_weighted_count_share_alternative": raw_values.get(rid),
            "direct_weighted_count_rank_alternative": raw_rank.get(rid),
            "fuel_habitat_responsibility_share_2021": fuel_values[rid],
            "fuel_proxy_baseline_area_km2": r["fuel_proxy_baseline_area_wc2021_km2"],
            "fuel_proxy_raw_area_km2": r["fuel_proxy_raw_area_wc2021_km2"],
            "tree_share": r["tree_share_wc2021"], "shrub_share": r["shrub_share_wc2021"],
            "grass_share": r["grass_share_wc2021"],
            "geometry_area_difference_flag": r["geometry_area_difference_flag"],
            "species_quality_flags": {s["species_code"]: quality_lookup.get((rid, s["species_code"]),
                                               ["outside_original_survey_unknown_not_zero"]) for s in core},
            "road_entry_index": None, "late_season_fire_exposure_index": None,
            "rhino_priority_distribution": None,
            "rare_plant_and_bird_value": None, "combined_demand": None,
            "deployed_protection_score": None,
            "status": "partial_baseline_not_final_priority_or_protection_score",
        })
    checks = {"surveyed_responsibilities_sum_to_one": True,
              "source_species_totals_match": True, "outside_survey_animals_remain_unknown": True,
              "species_population_scale_does_not_dominate_score": True,
              "metric_semantics": check_metric_semantics()}
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Q1 quantitative definition plus historical baseline; not Q2/Q3 optimization",
        "sources_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in (BASE, SPECIES)},
        "script_sha256": sha256(Path(__file__)),
        "metric_script_sha256": sha256(Path(__file__).with_name("protection_metrics.py")),
        "species": [{"code": s["species_code"], "name_zh": s["name_zh"],
                     "law_class_in_reviewed_compilation": s["law_class"],
                     "weight_is_team_assumption": True, "weight": ws[s["species_code"]],
                     "survey_total": totals[s["species_code"]]} for s in core],
        "direct_count_species_contributions": direct_species_share,
        "balanced_species_contributions": balanced_species_share,
        "regions": result_rows, "weight_sensitivity": scenarios,
        "leave_one_species_out_sensitivity": leave_one_out, "checks": checks,
        "planning_target_assumptions": {"park_score_minimum_each_shift": 80,
            "critical_target_service_minimum": 0.9,
            "not_a_problem_requirement_or_real_success_probability": True},
        "limitations": ["2015 counts are historical survey estimates, not 2026 populations",
            "Six selected taxa do not represent full biodiversity or all poaching targets",
            "Black rhino remains a critical object despite conflicting public count tables",
            "Fuel-habitat area is not rare-plant value, harmful-fire probability or loss",
            "Null threat/distribution fields cannot be interpreted as zero or omitted from full-park claims",
            "No staffing estimate, causal resource-effect calibration or optimized deployment was computed"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "question1_baseline.json").write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                                           allow_nan=False) + "\n", encoding="utf-8")
    top = sorted(values, key=baseline_rank.get)
    by_id = {r["region_id"]: r for r in result_rows}
    lines = ["# 第一题：现有数据的基线实算", "", "由`scripts/modeling/build_question1_baseline.py`生成。",
        "", "**这里的排序仅表示2015年六类动物的区域保护责任，不是最终保护优先级或已部署保护水平。**",
        "两个调查外单元的动物值仍为未知。黑犀牛、植物、盐沼鸟类和重点生境没有因缺数量而退出保护目标。",
        "", "## 1. 动物责任及面积对照", "",
        "先计算各区占每一物种调查总量的份额，再按共享法定类别映射假设1/2/3加权。",
        "法规提供分类依据；数值权重是团队假设，未审计2026全部修订，也不等于濒危等级。",
        "密度使用原调查报告面积。按密度排序是分配强度的对照，不能再次与总量责任加权。", "",
        "| 调查区 | 动物责任份额 | 责任排名 | 每1000 km²责任（份额） | 密度排名 | 直接加权数量排名 |",
        "|---|---:|---:|---:|---:|---:|"]
    for rid in top:
        r = by_id[rid]
        lines.append(f"| {rid} | {values[rid]:.2%} | {baseline_rank[rid]} | {density[rid]*1000:.4f} | {density_rank[rid]} | {raw_rank[rid]} |")
    lines += ["", "## 2. 物种数量规模的影响", "",
              "| 物种 | 历史估计数量 | 假设权重 | 直接加权数量贡献 | 先按物种份额平衡后的贡献 |",
              "|---|---:|---:|---:|---:|"]
    for s in core:
        code = s["species_code"]
        lines.append(f"| {s['name_zh']} | {totals[code]:,.0f} | {ws[code]} | {direct_species_share[code]:.2%} | {balanced_species_share[code]:.2%} |")
    lines += ["", "## 3. 已执行的敏感性", "",
              "| 类别权重（可猎/保护/特别保护） | 前五区 | 相对基准最大名次变化 |",
              "|---|---|---:|"]
    for s in scenarios:
        lines.append(f"| {'/'.join(str(v) for v in s['category_weights_huntable_protected_special'])} | {'、'.join(s['top5'])} | {s['max_rank_change_from_baseline']} |")
    lines += ["", "| 暂去掉物种 | 前五区 | 相对基准最大名次变化 |", "|---|---|---:|"]
    names = {s["species_code"]: s["name_zh"] for s in core}
    for s in leave_one_out:
        lines.append(f"| {names[s['omitted_species']]} | {'、'.join(s['top5'])} | {s['max_rank_change']} |")
    lines += ["", "这些检查只支持当前六类历史动物价值的稳定性判断；没有检验缺失的黑犀牛、火暴露或资源配置结果。",
              "动物数量的不确定区间及源表质量问题仍保留在JSON，不因排名稳定而消失。", "",
              "## 4. 生境与待完成字段", "",
              f"可燃生境基准合计为{fuel_total:,.3f} km²，逐区面积责任已计算。",
              "这是草/灌/林面积代理，并非珍稀植物数量或真实火损失。主盐沼基准燃料掩膜为零，原始植被面积保留供敏感性检查。",
              "道路进入便利度、历史晚旱季火暴露、实际雨季距平、重点物种分布、部署后保护分数均保持null。",
              "这些字段补齐或选择明确的不确定性情景后，才能计算全园需求和配置成效。", "",
              "## 5. 已通过的模型语义检查", "",
              "- 动物责任在原15调查单元内合计为1，物种数量合计与原表一致；调查外未知没有填零。",
              "- 同一物种所有区域的数量一起成比例变化时，相对责任不变。",
              "- 有监测而没有有效响应时，处置保护分项为零。",
              "- 零需求返回不适用，不赋100分；未知需求拒绝计算。",
              "- 配置前后共用需求向量及尺度；不同地点的发现与响应不能相乘制造虚假保护。",
              "", "保护定义见[第一题正文](../../docs/paper/question1_protection_definition.md)；",
              "三题接口见[统一框架](../../docs/q1_q2_q3_model_framework.md)。", ""]
    (OUT / "第一题基线实算.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"regions": len(rows), "survey_units": len(surveyed),
                      "top5_historical_animal_responsibility": top[:5],
                      "animal_responsibility_sum": math.fsum(values.values()),
                      "direct_zebra_contribution": direct_species_share["Eb"],
                      "checks_passed": True, "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
