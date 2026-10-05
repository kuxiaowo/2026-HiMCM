"""Refresh audit summaries while retaining earlier retrieval attempts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "model1"
def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))
def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

counts = read("species_region_counts_2015.json")
downloads = read("species_feasibility_downloads.json")
additional = read("additional_species_source_checks.json")
review = {"date": "2026-10-05", "status": "historical_coarse_scale_feasible",
          "report": "output/model1/species_data_feasibility.md",
          "dataset": "output/model1/species_region_counts_2015.json",
          "statistical_units": len(counts["strata"]), "species_tables": len(counts["species"]),
          "region_species_rows": len(counts["rows"]),
          "recommended_core_species": [item["name_zh"] for item in counts["species"] if item["adoption"] == "core_with_flags"],
          "counts_are_2015_dry_season_estimates_not_2026_census": True,
          "raw_stratum_gis_obtained": False,
          "current_plant_density_table_obtained": False,
          "full_2026_law_amendment_audit_completed": False,
          "legal_numeric_weights_exist": False,
          "elephant_crosscheck": counts["crosscheck"],
          "sources": downloads["files"] + additional["files"],
          "plant_occurrence_evidence": {
              "taxon": "Moringa ovalifolia",
              "law_schedule": 9,
              "government_source": "https://www.meft.gov.na/national-parks/etosha-national-park/217/",
              "research_source": "https://academicjournals.org/journal/AJFS/article-full-text/D35946859661",
              "supports": "confirmed sites/occurrence, not whole-park population or density"},
          "newer_census_lead": {
              "year": 2023,
              "source": "https://cites.org/sites/default/files/documents/COP/20/prop/E-CoP20-Prop-13.pdf?gtranslate=zh-CN",
              "retrieval": "indexed reference/text only; PDF download 403; original stratum report not obtained"},
          "quality_conflicts": {
              "black_rhino": "section 1.6 says data omitted, tables include it; numeric block sum 1107 versus total 1280",
              "eland": "summary 1321, individual-table total 1103, numeric block sum 928",
              "springbok": "ENP6 estimate 11 below observed 18 and lower CI 18; ENP16 printed density inconsistent",
              "other_fields": "blue wildebeest CI% typo; red hartebeest and oryx sampling-expansion diagnostics need review"}}
write("species_data_feasibility.json", review)

audit = read("species_sources_audit.json")
if "latest_feasibility_review" not in audit:
    audit["previous_law_review"] = audit.get("law_review")
audit["latest_feasibility_review"] = review
audit["law_review"] = counts["law"]
audit["catalogue_search_evidence"]["subsequent_finding"] = review["quality_conflicts"]["black_rhino"]
write("species_sources_audit.json", audit)

availability = read("data_availability_audit.json")
availability["species_feasibility_review"] = {key: review[key] for key in
    ["status", "report", "dataset", "statistical_units", "species_tables", "region_species_rows",
     "counts_are_2015_dry_season_estimates_not_2026_census", "raw_stratum_gis_obtained",
     "current_plant_density_table_obtained", "full_2026_law_amendment_audit_completed"]}
write("data_availability_audit.json", availability)
print("Updated the feasibility summary and two existing source audits.")
