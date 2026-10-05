"""Extract the 2015 survey tables and keep source errors distinct from assumptions.

Uses the reviewed PDF text dump, preserving the original numeric values.
Outputs JSON only; it does not create a GIS partition or a fitted allocation model.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "model1"
TEXT = (OUT / "etosha_aerial_census_2015_extracted.txt").read_text(encoding="utf-8-sig")
SOURCE_URL = "https://rhinoresourcecenter.com/wp-content/uploads/2022/01/1642693511.pdf"
LAW_URL = "https://namibiatradeportal.gov.na/application/files/3617/2986/2681/Nature_Conservation_Ordinance_4_of_1975.pdf"

# Code, table, Chinese name, report taxon, law class, schedule, PDF page, adoption.
SPECS = [
    ("Ab", 3, "红狷羚", "Alcelaphus buselaphus", "protected_game", "4(i)", 7, "hold_row_check"),
    ("Am", 4, "跳羚", "Antidorcas marsupialis", "huntable_game", "5", 8, "hold_invalid_estimate"),
    ("Ct", 5, "蓝角马", "Connochaetes taurinus", "protected_game", "4(i)", 8, "core_with_flags"),
    ("Db", 6, "黑犀牛", "Diceros bicornis", "specially_protected_game", "3", 9, "hold_source_conflicts"),
    ("Eb", 7, "平原斑马", "Equus burchelli / Equus quagga", "specially_protected_game", "3", 9, "core_with_flags"),
    ("Hz", 8, "哈特曼山斑马", "Equus zebra hartmannae", "specially_protected_game", "3", 10, "optional_partial_rows"),
    ("Gc", 9, "长颈鹿", "Giraffa camelopardalis (report aggregate)", "specially_protected_game", "3", 10, "core_with_flags"),
    ("La", 10, "非洲草原象", "Loxodonta africana", "specially_protected_game", "3", 11, "core_with_flags"),
    ("Og", 11, "南非剑羚", "Oryx gazella", "huntable_game", "5", 11, "core_with_flags"),
    ("Sc", 12, "鸵鸟", "Struthio camelus", "protected_game_birds", "4(ii), excluding 6", 12, "core_with_flags"),
    ("To", 13, "大羚羊（Eland）", "Taurotragus oryx", "protected_game", "4(i)", 12, "hold_source_conflicts"),
]
WEIGHTS = {"specially_protected_game": 3, "protected_game": 2,
           "protected_game_birds": 2, "huntable_game": 1}

positions = list(re.finditer(r"(?m)^Table\s*(\d+)\s*\.", TEXT))
tables = {}
for index, match in enumerate(positions):
    end = positions[index + 1].start() if index + 1 < len(positions) else TEXT.index("PAGE 13")
    tables[int(match.group(1))] = TEXT[match.start():end]

def numeric(token):
    return float(token.rstrip("%"))

strata = []
for line in tables[1].splitlines():
    fields = line.split()
    if fields and re.fullmatch(r"ENP\d+", fields[0]):
        assert len(fields) == 10, line
        values = list(map(numeric, fields[1:]))
        strata.append({"stratum": fields[0], "area_km2": values[1],
                       "area_searched_km2": values[7], "searched_percent": values[8],
                       "source_table": 1, "source_pdf_page": 6, "raw_line": line.strip()})
assert len(strata) == 15
areas = {item["stratum"]: item["area_km2"] for item in strata}

def parse_statistics(line):
    fields = line.split()
    values = list(map(numeric, fields[1:]))
    result = {"no_seen": None, "ci_lower": None, "count_estimate": None,
              "ci_upper": None, "variance": None, "ci_halfwidth": None,
              "ci_percent_as_printed": None, "density_as_printed_per_km2": None,
              "raw_line": line.strip(), "quality_flags": []}
    if len(values) == 8:
        keys = ["no_seen", "ci_lower", "count_estimate", "ci_upper", "variance",
                "ci_halfwidth", "ci_percent_as_printed", "density_as_printed_per_km2"]
        result.update(zip(keys, values))
    elif len(values) == 6:  # Table 8 total omits the two CI-detail fields.
        result.update(zip(["no_seen", "ci_lower", "count_estimate", "ci_upper", "variance",
                           "density_as_printed_per_km2"], values))
    elif len(values) == 1:
        result["density_as_printed_per_km2"] = values[0]
        result["quality_flags"].append("blank_count_with_source_zero_density")
    elif not values:
        result["quality_flags"].append("source_blank_row")
    else:
        raise ValueError(f"Unexpected column count: {line}")
    return result

summary = {}
for line in tables[2].splitlines():
    fields = line.split()
    if fields and fields[0] in {spec[0] for spec in SPECS}:
        stats = parse_statistics("row " + " ".join(fields[-8:]))
        stats["raw_line"] = line.strip()
        stats.update(source_table=2, source_pdf_page=7)
        summary[fields[0]] = stats

rows, species, checks = [], [], []
for code, table, name, taxon, category, schedule, page, adoption in SPECS:
    block_rows, total = [], None
    for line in tables[table].splitlines():
        fields = line.split()
        if fields and (re.fullmatch(r"ENP\d+", fields[0]) or fields[0] == "Total"):
            row = parse_statistics(line)
            row.update(species_code=code, species=name, source_table=table, source_pdf_page=page)
            if fields[0] == "Total":
                total = row
                continue
            row.update(stratum=fields[0], area_km2=areas[fields[0]])
            if (code, row["stratum"]) in [("Ab", "ENP7"), ("Og", "ENP1"), ("Db", "ENP8")]:
                row["quality_flags"].append("sampling_expansion_crosscheck_requires_review")
            estimate = row["count_estimate"]
            row["density_from_estimate_per_km2"] = estimate / row["area_km2"] if estimate is not None else None
            if estimate is not None:
                if not row["ci_lower"] <= estimate <= row["ci_upper"]:
                    row["quality_flags"].append("estimate_outside_reported_ci")
                if estimate < row["no_seen"]:
                    row["quality_flags"].append("estimate_below_observed_count")
                density_token = fields[-1]
                decimals = len(density_token.split(".")[1]) if "." in density_token else 0
                tolerance = 0.5 * 10 ** (-decimals) + 1e-8
                if abs(row["density_from_estimate_per_km2"] - row["density_as_printed_per_km2"]) > tolerance:
                    row["quality_flags"].append("density_inconsistent_with_count_and_area")
                if row["ci_halfwidth"] is not None:
                    expected_percent = 100 * row["ci_halfwidth"] / estimate
                    if abs(expected_percent - row["ci_percent_as_printed"]) > max(3, 0.04 * expected_percent):
                        row["quality_flags"].append("ci_percentage_inconsistent")
                    row["ci_halfwidth_over_estimate"] = row["ci_halfwidth"] / estimate
            # Assumed zero is a scenario convention for surveyed zero-density rows,
            # never an assertion that a species is ecologically absent.
            row["candidate_baseline_count"] = (
                estimate if estimate is not None else
                0 if row["density_as_printed_per_km2"] == 0 else None)
            if estimate is None and row["candidate_baseline_count"] == 0:
                row["quality_flags"].append("baseline_zero_is_explicit_nondetection_assumption")
            row["recommended_core_input"] = adoption == "core_with_flags"
            block_rows.append(row)
    assert len(block_rows) == 15 and total is not None, code
    row_sum = sum(row["count_estimate"] or 0 for row in block_rows)
    seen_sum = sum(row["no_seen"] or 0 for row in block_rows)
    item = {"species_code": code, "name_zh": name, "report_taxon": taxon,
            "law_class": category, "law_schedule": schedule,
            "law_pdf_pages": [78, 79, 80] if code == "Sc" else [79] if code in ["Am", "Ab", "Og", "To"] else [78],
            "candidate_weight": WEIGHTS[category], "weight_is_model_assumption": True,
            "adoption": adoption, "summary_table": summary.get(code),
            "individual_table_total": total, "sum_of_numeric_block_estimates": row_sum,
            "block_sum_minus_table_total": row_sum - total["count_estimate"],
            "sum_of_numeric_block_observations": seen_sum,
            "observation_sum_minus_total": seen_sum - total["no_seen"],
            "numeric_count_rows": sum(row["count_estimate"] is not None for row in block_rows),
            "blank_count_rows": sum(row["count_estimate"] is None for row in block_rows)}
    if code in summary:
        item["individual_total_minus_summary_total"] = total["count_estimate"] - summary[code]["count_estimate"]
    species.append(item)
    checks.append({"species": name, "block_sum": row_sum, "table_total": total["count_estimate"],
                   "summary_total": summary.get(code, {}).get("count_estimate"),
                   "flags": [{"stratum": row["stratum"], "flags": row["quality_flags"]}
                             for row in block_rows if any(flag not in
                                ["blank_count_with_source_zero_density", "source_blank_row",
                                 "baseline_zero_is_explicit_nondetection_assumption"]
                                for flag in row["quality_flags"])]})
    rows.extend(block_rows)

core = [item for item in species if item["adoption"] == "core_with_flags"]
weighted_total = sum(item["individual_table_total"]["count_estimate"] * item["candidate_weight"] for item in core)
naive_contributions = [{"species": item["name_zh"],
                       "weighted_individuals": item["individual_table_total"]["count_estimate"] * item["candidate_weight"],
                       "share": item["individual_table_total"]["count_estimate"] * item["candidate_weight"] / weighted_total}
                      for item in core]
examples = []
for block in ["ENP1", "ENP17"]:
    block_rows = [row for row in rows if row["stratum"] == block and row["recommended_core_input"]]
    raw_value = sum(row["candidate_baseline_count"] * WEIGHTS[next(item["law_class"] for item in core if item["species_code"] == row["species_code"])] for row in block_rows)
    examples.append({"stratum": block, "area_km2": areas[block],
                     "six_species_weighted_individuals": raw_value,
                     "weighted_individuals_per_km2": raw_value / areas[block],
                     "is_illustration_not_validated_ecological_score": True})

payload = {"date": "2026-10-05", "status": "historical_feasibility_audit_not_2026_census",
           "survey": {"year": 2015, "dates": ["2015-09-04", "2015-09-21"], "season": "dry",
                      "area_km2_as_printed": 18551.14, "sum_of_stratum_areas_km2": sum(areas.values()),
                      "area_searched_km2": 4196.9, "sampling_coverage_percent": 22.62354,
                      "statistical_units": 15, "main_pan_excluded": True,
                      "method": "stratified aerial sample count; Jolly method 2",
                      "source_url": SOURCE_URL, "local_pdf": "data/species/raw/etosha_aerial_census_2015.pdf",
                      "visually_reviewed_pdf_pages": [5, 6, 7, 8, 9, 10, 11, 12, 16]},
           "law": {"source_url": LAW_URL, "local_pdf": "data/species/raw/nature_conservation_annotated_tradeportal.pdf",
                   "reviewed_pages": [78, 79, 80, 83, 84],
                   "numeric_weights_are_not_statutory": True,
                   "2026_complete_amendment_audit": False},
           "strata": strata, "species": species, "rows": rows,
           "automated_quality_checks": checks,
           "illustration": {"naive_weighted_total": weighted_total,
                            "naive_species_contributions": naive_contributions, "regions": examples},
           "crosscheck": {"url": "https://africanelephantdatabase.org/population_submissions/722",
                          "result": "2015 elephant total 2911 and all 15 stratum estimates agree, including explicit database zeros",
                          "independent_survey": False,
                          "database_area_rounding_note": "rounded stratum areas sum to 18549 km2; use source PDF areas"},
           "limitations": ["no current full-park species density matrix obtained",
                           "no machine-readable original stratum polygons obtained",
                           "taxon names follow historical report and law; modern taxon matching still required",
                           "nondetection baseline zeros do not demonstrate true absence",
                           "do not derive count from the coarsely rounded printed densities",
                           "selected large animals do not measure complete biodiversity"]}
(OUT / "species_region_counts_2015.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"strata": len(strata), "species": len(species), "rows": len(rows),
                  "quality_checks": checks, "illustration": payload["illustration"]}, ensure_ascii=False, indent=2))
