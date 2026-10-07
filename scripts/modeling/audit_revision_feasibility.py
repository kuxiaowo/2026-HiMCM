"""Audit existing inputs without changing the manuscript or model results.

Run with the project's himcn-roads conda environment. PDF table transcription
is checked separately against the rendered source pages. All calculations here
are provenance or internal-consistency checks, not ecological calibration.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from pyproj import Geod, Transformer
import pyogrio
from shapely import from_wkb, make_valid
from shapely.geometry import mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import transform
from shapely.validation import explain_validity


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/revision_feasibility/20261006"
GEOD = Geod(ellps="WGS84")
PROJECT = Transformer.from_crs(4326, 32645, always_xy=True).transform


def read_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def fingerprint(relative: str):
    path = ROOT / relative
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def polygons(geometry):
    if geometry.geom_type == "Polygon":
        return [geometry]
    if hasattr(geometry, "geoms"):
        return [p for g in geometry.geoms for p in polygons(g)]
    return []


def metrics(geometry):
    pieces = polygons(geometry)
    geodesic = sum(
        abs(GEOD.geometry_area_perimeter(orient(g, sign=1.0))[0])
        for g in pieces
    )
    return {
        "type": geometry.geom_type,
        "valid": bool(geometry.is_valid),
        "validity_detail": explain_validity(geometry),
        "bounds": list(geometry.bounds) if not geometry.is_empty else None,
        "polygon_components": len(pieces),
        "interior_rings": sum(len(g.interiors) for g in pieces),
        "utm45n_area_km2": transform(PROJECT, geometry).area / 1e6,
        "wgs84_geodesic_area_km2": geodesic / 1e6,
    }


def audit_crosspark_files():
    archive = ROOT / "data/revision_feasibility/20261006/yellowstone_wolf_1995_2022.zip"
    wolf_rows, wolf_features = [], []
    with zipfile.ZipFile(archive) as source:
        for member in source.namelist():
            if "/2022_Wolf Territory Shapefiles/" not in member or not member.endswith(".shp"):
                continue
            metadata, _, geometries, values = pyogrio.raw.read(
                "/vsizip/" + archive.as_posix() + "/" + member)
            convert = Transformer.from_crs(metadata["crs"], 4326, always_xy=True).transform
            for i, encoded in enumerate(geometries):
                original = from_wkb(encoded)
                geometry = transform(convert, original)
                props = {str(key): column[i].item() if hasattr(column[i], "item") else column[i]
                         for key, column in zip(metadata["fields"], values)}
                props.update(source_file=member, year=2022,
                             interpretation="historical 95% minimum convex polygon; not population density or current distribution")
                wolf_features.append({"type": "Feature", "geometry": mapping(geometry), "properties": props})
                wolf_rows.append({"file": member, "crs": metadata["crs"],
                                  "valid": bool(original.is_valid), "bounds": list(geometry.bounds),
                                  "source_properties": props})
    (OUT / "yellowstone_wolf_2022_territories.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": wolf_features}, ensure_ascii=False), encoding="utf-8")
    wolf_audit = {"wolf_zip_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                  "year2022_features": len(wolf_features), "rows": wolf_rows}
    (OUT / "crosspark_ecology_file_audit.json").write_text(
        json.dumps(wolf_audit, ensure_ascii=False, indent=2), encoding="utf-8")

    preview = (ROOT / "data/revision_feasibility/20261006/dryad_data_csv_public_preview.txt").read_text(encoding="utf-8")
    clean = lambda value: html.unescape(re.sub("<[^>]+>", "", value)).strip()
    headers = [clean(value) for value in re.findall(r"<th>(.*?)</th>", preview, re.S)]
    body = preview.split("<tbody>", 1)[1].split("</tbody>", 1)[0]
    candidate_rows = [[clean(value) for value in re.findall(r"<td>(.*?)</td>", row, re.S)]
                      for row in re.findall(r"<tr>(.*?)</tr>", body, re.S)]
    rows = [row for row in candidate_rows if len(row) == len(headers)]
    with (OUT / "chitwan_tiger_PUBLIC_PREVIEW_ONLY.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
    tiger_audit = {
        "scope": "PUBLIC PREVIEW ONLY; not complete Data.csv and not model input",
        "preview_complete_rows": len(rows), "columns": headers,
        "preview_incomplete_rows": sum(len(row) != len(headers) for row in candidate_rows),
        "incomplete_row_handling": "Server preview ends during a row; no missing fields filled.",
        "full_file_api_size_bytes": 783106,
        "full_file_api_sha256": "38c7acba5a0e1237e871e75a25e9c68ae420ec1786e1d56ee2ea60a955b22260",
        "year_conflict": "Dryad description: Dec2020-Feb2021; article abstract/PubMed: Dec2021-Feb2022. Preview Date omits year, so cannot resolve from preview alone.",
        "source": "https://doi.org/10.5061/dryad.7h44j1057",
        "complete_csv_obtained": False,
    }
    (OUT / "chitwan_tiger_preview_field_audit.json").write_text(
        json.dumps(tiger_audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"yellowstone_2022_wolf_features": len(wolf_features),
            "all_wolf_geometries_valid": all(row["valid"] for row in wolf_rows),
            "chitwan_tiger_preview_complete_rows": len(rows),
            "chitwan_tiger_complete_csv_obtained": False}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    crosspark_file_summary = audit_crosspark_files()
    species_source = read_json("output/model1/species_region_counts_2015.json")
    species_checks = []
    for species in species_source["species"]:
        rows = [r for r in species_source["rows"]
                if r["species_code"] == species["species_code"]]
        columns = ["no_seen", "count_estimate", "variance"]
        totals = {key: sum(r[key] or 0 for r in rows) for key in columns}
        printed = {key: species["individual_table_total"][key] for key in columns}
        summary = ({key: species["summary_table"][key] for key in columns}
                   if species["summary_table"] is not None else None)
        species_checks.append({
            "code": species["species_code"],
            "name_zh": species["name_zh"],
            "numeric_row_totals": totals,
            "individual_table_totals": printed,
            "summary_table_totals": summary,
            "count_gap_individual_minus_rows": printed["count_estimate"] - totals["count_estimate"],
            "column_gaps_individual_minus_numeric_rows": {
                key: printed[key] - totals[key] for key in columns},
            "column_gaps_individual_minus_summary": {
                key: printed[key] - summary[key] for key in columns} if summary else None,
            "blank_count_strata": [r["stratum"] for r in rows if r["count_estimate"] is None],
            "blank_handling": "Numeric rows only; blanks are not observed zeros.",
        })

    def species_row(code, stratum):
        return next(r for r in species_source["rows"]
                    if r["species_code"] == code and r["stratum"] == stratum)

    springbok6 = species_row("Am", "ENP6")
    springbok16 = species_row("Am", "ENP16")
    wildebeest15 = species_row("Ct", "ENP15")
    field_conflicts = {
        "springbok_ENP6": {
            "seen": springbok6["no_seen"],
            "estimate": springbok6["count_estimate"],
            "lower": springbok6["ci_lower"],
            "upper": springbok6["ci_upper"],
            "finding": "Printed estimate is below both seen and lower limit; correct count is unresolved.",
        },
        "springbok_ENP16": {
            "estimate": springbok16["count_estimate"],
            "survey_area_km2": springbok16["area_km2"],
            "printed_density": springbok16["density_as_printed_per_km2"],
            "density_derived_from_printed_count_and_area": springbok16["count_estimate"] / springbok16["area_km2"],
            "finding": "Density can be recalculated only conditional on the printed count and area.",
        },
        "wildebeest_ENP15": {
            "estimate": wildebeest15["count_estimate"],
            "printed_CI_halfwidth": wildebeest15["ci_halfwidth"],
            "printed_CI_percent": wildebeest15["ci_percent_as_printed"],
            "CI_percent_from_rounded_printed_fields": 100 * wildebeest15["ci_halfwidth"] / wildebeest15["count_estimate"],
            "finding": "Percentage field is inconsistent; derived rounded-field ratio is not the unknown unrounded source value.",
        },
    }

    published = read_json("data/question6/raw/chitwan_wdpca.json")["features"][0]["attributes"]
    wdpca = shape(read_json("data/question6/processed/chitwan_boundary.geojson")["features"][0]["geometry"])
    osm = shape(read_json("data/question6/processed/chitwan_osm_boundary.geojson")["features"][0]["geometry"])
    icimod_features = read_json("data/question6/raw/icimod_nepal_pa.geojson")["features"]
    icimod_park = shape(next(f["geometry"] for f in icimod_features if f["properties"]["PA"] == "Chitwan"))
    icimod_buffer = shape(next(f["geometry"] for f in icimod_features if f["properties"]["PA"] == "Chitwan Buffer Zone"))
    repaired_park = make_valid(icimod_park)
    wdpca_metrics = metrics(wdpca)
    official_area = 952.63
    boundary_checks = {
        "published_attributes": {key: published[key] for key in [
            "site_id", "rep_area", "gis_area", "verif", "metadataid"]},
        "official_reported_park_area_km2": official_area,
        "official_reported_buffer_area_km2": 729.37,
        "WDPCA": wdpca_metrics,
        "OSM": metrics(osm),
        "ICIMOD_park_raw": metrics(icimod_park),
        "ICIMOD_park_after_make_valid": metrics(repaired_park),
        "ICIMOD_buffer": metrics(icimod_buffer),
        "WDPCA_vs_ICIMOD_symmetric_difference": metrics(wdpca.symmetric_difference(repaired_park)),
        "WDPCA_vs_OSM_symmetric_difference": metrics(wdpca.symmetric_difference(osm)),
        "WDPCA_overlap_with_ICIMOD_buffer": metrics(wdpca.intersection(icimod_buffer)),
        "geodesic_minus_published_gis_km2": wdpca_metrics["wgs84_geodesic_area_km2"] - published["gis_area"],
        "projection_minus_geodesic_km2": wdpca_metrics["utm45n_area_km2"] - wdpca_metrics["wgs84_geodesic_area_km2"],
        "geodesic_excess_over_official_percent": 100 * (wdpca_metrics["wgs84_geodesic_area_km2"] / official_area - 1),
        "utm_excess_over_official_percent": 100 * (wdpca_metrics["utm45n_area_km2"] / official_area - 1),
        "scope": "Differences establish a source-level area inconsistency, not which legal boundary or area should be corrected.",
    }

    with (ROOT / "data/question3/raw/koedoe_water_points_2013.csv").open(encoding="utf-8-sig", newline="") as file:
        water = list(csv.DictReader(file))
    water_audit = {
        "all_sample_points": len(water),
        "BH_sample_points": sum(r["type"] == "BH" for r in water),
        "nonblank_sample_years": sorted({r["sample_date"][:4] for r in water if r["sample_date"]}),
        "blank_sample_dates": [{"name": r["name"], "type": r["type"]}
                               for r in water if not r["sample_date"]],
        "finding": "Historical water-chemistry sample, not a complete current maintenance inventory.",
    }

    q2_config = read_json("output/question2/q2_model_inputs.json")["config"]
    inputs = [
        "data/species/raw/etosha_aerial_census_2015.pdf",
        "output/model1/species_region_counts_2015.json",
        "data/question6/raw/chitwan_wdpca.json",
        "data/question6/processed/chitwan_boundary.geojson",
        "data/question6/processed/chitwan_osm_boundary.geojson",
        "data/question6/raw/icimod_nepal_pa.geojson",
        "data/question3/raw/koedoe_water_points_2013.csv",
        "output/question2/q2_model_inputs.json",
        "docs/paper/full_paper.tex",
        "output/pdf/full_paper.pdf",
        "data/revision_feasibility/20261006/dnpwc_gis_database_final_2020.pdf",
        "data/revision_feasibility/20261006/iucn_traffic_cop20_analyses_v4.pdf",
        "data/revision_feasibility/20261006/rhino_movement_2019.html",
        "data/revision_feasibility/20261006/yellowstone_wolf_1995_2022.zip",
        "data/revision_feasibility/20261006/yellowstone_wolf_cougar_elk_2025.pdf",
        "data/revision_feasibility/20261006/dryad_data_csv_public_preview.txt",
    ]
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Revision feasibility audit; no production model results changed.",
        "pdf_source_pages_visually_checked_this_round": [8, 9],
        "species_aggregate_checks": species_checks,
        "species_field_conflicts": field_conflicts,
        "chitwan_boundary_checks": boundary_checks,
        "water_inventory_scope": water_audit,
        "crosspark_new_files": crosspark_file_summary,
        "baseline_config_retained": q2_config,
        "input_fingerprints": [fingerprint(path) for path in inputs],
    }
    destination = OUT / "data_conflict_audit.json"
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": destination.relative_to(ROOT).as_posix(),
        "species_gaps": [{"species": s["name_zh"], "gap": s["count_gap_individual_minus_rows"]}
                         for s in species_checks if s["count_gap_individual_minus_rows"]],
        "WDPCA_geodesic_km2": wdpca_metrics["wgs84_geodesic_area_km2"],
        "source_gis_difference_km2": boundary_checks["geodesic_minus_published_gis_km2"],
        "park_buffer_overlap_km2": boundary_checks["WDPCA_overlap_with_ICIMOD_buffer"]["utm45n_area_km2"],
        "ICIMOD_repair_area_km2": boundary_checks["ICIMOD_park_after_make_valid"]["utm45n_area_km2"],
        "water": water_audit,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
