"""Reconstruct modelling units from public AED 2015 outlines, with explicit QA.

No unobserved animal counts are created. Survey areas remain the denominators
for historical census densities; GIS areas describe the current spatial units.
The public map is generalized, not authenticated original survey GIS.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pyproj
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch
from PIL import Image
from shapely import make_valid
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/regions/processed"
OUTPUT = ROOT / "output/regions"
RAW_MAP = ROOT / "data/regions/raw/source_audit/aed_2015_map.geojson"
FIGURE = ROOT / "data/regions/raw/source_audit/figure1_stratification_2015.jpg"
CENSUS = ROOT / "output/model1/species_region_counts_2015.json"
BOUNDARY = ROOT / "data/roads/processed/park_boundary.geojson"
LAEA_PROJ = "+proj=laea +lat_0=-19 +lon_0=15.75 +datum=WGS84 +units=m +no_defs"
LAEA = pyproj.CRS.from_proj4(LAEA_PROJ)
GEOD = pyproj.Geod(ellps="WGS84")
PAN_RADIUS_M = 500
MIN_SOURCE_PART_M2 = 100_000  # Only isolated source components, not true region holes.
NEAR_NEIGHBOR_M = 500
AREA_QA_TOLERANCE_M2 = 1.0
DENSIFY_MAX_DEGREES = 0.001
REGION_ORDER = ["ENP1", "ENP2", "ENP3410", "ENP5", "ENP6", "ENP7", "ENP8", "ENP9", "ENP11", "ENP12", "ENP13", "ENP14", "ENP15", "ENP16", "ENP17"]


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parts(g):
    if isinstance(g, Polygon):
        return [g] if not g.is_empty else []
    if isinstance(g, (MultiPolygon, GeometryCollection)):
        return [p for item in g.geoms for p in parts(item)]
    return []


def polygon_only(g):
    ps = parts(make_valid(g))
    return unary_union(ps) if ps else Polygon()


def geod_area(g) -> float:
    return sum(abs(GEOD.geometry_area_perimeter(orient(p, sign=1))[0]) for p in parts(g)) / 1e6


def csv_write(path: Path, rows: list[dict], fields=None):
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def normalized_source() -> gpd.GeoDataFrame:
    raw = json.loads(RAW_MAP.read_text(encoding="utf-8"))
    records = []
    for f in raw["features"]:
        geom = f.get("geometry") or {"type": f["type"], "coordinates": f["coordinates"]}
        records.append({**f["properties"], "region_id": f["properties"]["aed_name"].replace(" ", ""), "geometry": shape(geom)})
    source = gpd.GeoDataFrame(records, crs="EPSG:4326")
    if set(source.region_id) != set(REGION_ORDER) or len(source) != 15:
        raise ValueError("AED map IDs differ from the 15 verified survey units")
    return source.set_index("region_id", drop=False).loc[REGION_ORDER].reset_index(drop=True)


def repair_mosaic(clipped: dict, report_areas: dict, reverse: bool = False):
    """Keep the map-confirmed ENP9 enclave, then resolve narrow overlaps explicitly."""
    base = dict(clipped)
    base["ENP11"] = polygon_only(base["ENP11"].difference(base["ENP9"]))
    order = sorted(REGION_ORDER, key=lambda k: (report_areas[k], k), reverse=reverse)
    occupied = Polygon()
    allocated = {}
    changes = {}
    for region_id in order:
        current = polygon_only(base[region_id].difference(occupied))
        changes[region_id] = {
            "enclave_removed_km2": (clipped[region_id].area - base[region_id].area) / 1e6,
            "other_overlap_removed_km2": (base[region_id].area - current.area) / 1e6,
            "priority_rank": order.index(region_id) + 1,
        }
        if current.is_empty:
            raise ValueError(f"Topology repair emptied {region_id}")
        allocated[region_id] = current
        occupied = unary_union([occupied, current])
    return allocated, changes, order


def extract_pan(residual, radius: float):
    cores = parts(polygon_only(residual.buffer(-radius)))
    if not cores:
        raise ValueError("No broad unsurveyed component available to approximate the main pan")
    largest = max(cores, key=lambda p: p.area)
    return polygon_only(largest.buffer(radius).intersection(residual))


def font_setup():
    f = Path("C:/Windows/Fonts/msyh.ttc")
    if f.exists():
        fp = FontProperties(fname=str(f))
        plt.rcParams["font.family"] = fp.get_name()
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["svg.fonttype"] = "path"


def draw_map(ax, regions, park, labels=True):
    surveys = regions[regions.region_kind == "survey_stratum"]
    surveys.plot(ax=ax, color="#ebe8d8", edgecolor="#686658", linewidth=0.65)
    surveys[surveys.region_id == "ENP3410"].plot(ax=ax, color="#e5cbb6", edgecolor="#756658", linewidth=0.65, hatch="///")
    regions[regions.region_kind == "main_pan"].plot(ax=ax, color="#9fcddd", edgecolor="#4b7f96", linewidth=0.65)
    regions[regions.region_kind == "unsurveyed_residual"].plot(ax=ax, color="#b6b9bd", edgecolor="#878c91", linewidth=0.25)
    gpd.GeoSeries([park], crs=LAEA).boundary.plot(ax=ax, color="#292f33", linewidth=1.1)
    if labels:
        for _, row in surveys.iterrows():
            if row.region_id == "ENP3410":
                ps = sorted(parts(row.geometry), key=lambda p: p.centroid.x)
                for p, code in zip(ps, ("3", "4", "10")):
                    pt = p.representative_point()
                    ax.text(pt.x, pt.y, code + "\n(3410)", ha="center", va="center", fontsize=8, color="#353633")
            else:
                pt = row.geometry.representative_point()
                ax.text(pt.x, pt.y, row.region_id.replace("ENP", ""), ha="center", va="center", fontsize=10, color="#303735")
        pan = regions[regions.region_kind == "main_pan"].iloc[0].geometry.representative_point()
        ax.text(pan.x, pan.y, "主盐沼\n近似范围", ha="center", va="center", fontsize=11, color="#235f78")
    x0, y0, x1, y1 = park.bounds
    ax.set_xlim(x0 - 6000, x1 + 6000)
    ax.set_ylim(y0 - 6500, y1 + 8000)
    ax.set_aspect("equal")
    ax.axis("off")


def make_maps(regions, park):
    font_setup()
    fig, ax = plt.subplots(figsize=(14, 7.4))
    draw_map(ax, regions, park)
    fig.subplots_adjust(top=0.84, bottom=0.18, left=0.03, right=0.98)
    fig.text(0.04, 0.95, "埃托沙国家公园：建模分区", fontsize=20, weight="bold", color="#253735")
    fig.text(0.04, 0.9, "15 个历史动物调查统计单元 + 主盐沼近似区 + 其他调查外残余", fontsize=12, color="#50645d")
    handles = [
        Patch(facecolor="#ebe8d8", edgecolor="#686658", label="2015 调查单元"),
        Patch(facecolor="#e5cbb6", edgecolor="#756658", hatch="///", label="ENP3410：3 / 4 / 10 合并统计"),
        Patch(facecolor="#9fcddd", edgecolor="#4b7f96", label="主盐沼近似区"),
        Patch(facecolor="#b6b9bd", edgecolor="#878c91", label="其他调查外残余（含细小边界缝隙）"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.09), ncol=2, frameon=False, fontsize=10)
    x0, y0, x1, y1 = park.bounds
    scale_x, scale_y = x0 + 14000, y0 + 2500
    ax.plot([scale_x, scale_x + 50000], [scale_y, scale_y], color="#333", lw=2)
    for x in (scale_x, scale_x + 25000, scale_x + 50000):
        ax.plot([x, x], [scale_y - 850, scale_y + 850], color="#333", lw=1)
    ax.text(scale_x, scale_y - 1600, "0", ha="center", va="top", fontsize=9)
    ax.text(scale_x + 50000, scale_y - 1600, "50 km", ha="center", va="top", fontsize=9)
    ax.annotate("N", xy=(x1 - 10000, y1 - 11000), xytext=(x1 - 10000, y1 - 24000), ha="center", fontsize=11, arrowprops={"arrowstyle": "-|>", "color": "#303a3e"})
    fig.text(0.04, 0.055, "分区：African Elephant Database 2015 公开概化地图；园界：OpenStreetMap；本项目完成拓扑修复。", fontsize=9, color="#586265")
    fig.text(0.04, 0.027, "空间边界为近似范围。历史动物密度仍按原报告面积计算；调查外动物数量保留缺失。", fontsize=9, color="#586265")
    fig.savefig(OUTPUT / "partition_map.png", dpi=220)
    fig.savefig(OUTPUT / "partition_map.svg")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    axes[0].imshow(Image.open(FIGURE))
    axes[0].axis("off")
    axes[0].set_title("原报告图 1：颜色表示抽样强度", fontsize=12)
    draw_map(axes[1], regions, park)
    axes[1].set_title("建模分区：保留统计单元并修复空间拓扑", fontsize=12)
    fig.text(0.05, 0.04, "仅作结构目视核对；左图没有地理配准。3 / 4 / 10 在模型中始终共用 ENP3410 的动物数据。", fontsize=10)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(OUTPUT / "partition_source_comparison.png", dpi=180)
    plt.close(fig)


def species_join(regions_wgs, census):
    meta = {s["species_code"]: s for s in census["species"]}
    records = {(r["stratum"], r["species_code"]): r for r in census["rows"]}
    rows = []
    for _, region in regions_wgs.iterrows():
        for code, s in meta.items():
            original = records.get((region.region_id, code))
            row = {
                "region_id": region.region_id,
                "region_kind": region.region_kind,
                "census_year": 2015,
                "species_code": code,
                "species_name_zh": s["name_zh"],
                "species_report_taxon": s["report_taxon"],
                "species_adoption": s["adoption"],
                "animal_data_status": "source_row_preserved" if original else "not_surveyed_or_not_matched",
                "survey_area_report_km2": None if pd.isna(region.survey_area_report_km2) else float(region.survey_area_report_km2),
                "geometry_area_km2": float(region.area_km2),
                "density_denominator": "survey_area_report_km2" if original else None,
                "model_weight_is_assumption": True,
                "candidate_weight": s.get("candidate_weight"),
            }
            if original:
                for k, v in original.items():
                    if k not in {"stratum", "species_code", "species", "area_km2"}:
                        row[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
            else:
                row.update({"candidate_baseline_count": None, "count_estimate": None, "no_seen": None, "recommended_core_input": False})
            rows.append(row)
    csv_write(OUTPUT / "species_region_link_2015.csv", rows)
    core_rows = [r for r in rows if r["species_adoption"] == "core_with_flags"]
    csv_write(OUTPUT / "core_species_region_link_2015.csv", core_rows)
    missing_extra = [r for r in rows if r["region_kind"] != "survey_stratum"]
    assert len(rows) == len(regions_wgs) * len(meta)
    assert sum(r["animal_data_status"] == "source_row_preserved" for r in rows) == len(census["rows"])
    assert all(r.get("candidate_baseline_count") is None and r.get("count_estimate") is None for r in missing_extra)
    return {"source_rows_preserved": len(census["rows"]), "joined_rows": len(rows), "core_joined_rows": len(core_rows), "unsurveyed_species_rows_kept_null": len(missing_extra), "duplicate_region_species_keys": 0, "unmatched_original_rows": 0, "report_area_denominator_preserved": True}


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    report_areas = {r["stratum"]: r["area_km2"] for r in census["strata"]}
    source = normalized_source()
    source.to_file(PROCESSED / "source_strata_normalized.geojson", driver="GeoJSON")
    # GeoJSON/rasterio interprets edges as straight in longitude/latitude.
    # Densify before projecting so long edges do not become a different chord
    # on inverse projection. Otherwise planar QA can pass but raster cells near
    # the boundary are lost when the geometries are clipped in EPSG:4326.
    metric = source.set_geometry(source.geometry.segmentize(DENSIFY_MAX_DEGREES)).to_crs(LAEA)
    original_park_gdf = gpd.read_file(BOUNDARY).to_crs(4326)
    original_park_wgs = polygon_only(unary_union(original_park_gdf.geometry))
    park_gdf = original_park_gdf.set_geometry(original_park_gdf.geometry.segmentize(DENSIFY_MAX_DEGREES)).to_crs(LAEA)
    park = polygon_only(unary_union(park_gdf.geometry))
    raw = {r.region_id: polygon_only(r.geometry) for _, r in metric.iterrows()}
    clean, clipped, dropped = {}, {}, {}
    for rid, g in raw.items():
        ps = parts(g)
        kept = [p for p in ps if p.area >= MIN_SOURCE_PART_M2]
        if not kept:
            raise ValueError(f"All source parts too small for {rid}")
        clean[rid] = polygon_only(unary_union(kept))
        dropped[rid] = sum(p.area for p in ps if p.area < MIN_SOURCE_PART_M2) / 1e6
        clipped[rid] = polygon_only(clean[rid].intersection(park))
    overlap_pairs = []
    for i, a in enumerate(REGION_ORDER):
        for b in REGION_ORDER[i + 1:]:
            overlap = raw[a].intersection(raw[b]).area / 1e6
            if overlap > 1e-7:
                overlap_pairs.append({"region_a": a, "region_b": b, "overlap_laea_km2": overlap})
    allocated, changes, priority = repair_mosaic(clipped, report_areas)
    alternative, _, reverse_priority = repair_mosaic(clipped, report_areas, reverse=True)
    surveyed_union = unary_union(list(allocated.values()))
    residual = polygon_only(park.difference(surveyed_union))
    pan = extract_pan(residual, PAN_RADIUS_M)
    rest = polygon_only(residual.difference(pan))
    pan_sensitivity = []
    for radius in (250, 500, 1000):
        alternative_pan = extract_pan(residual, radius)
        pan_sensitivity.append({"opening_radius_m": radius, "main_pan_laea_km2": alternative_pan.area / 1e6, "remaining_residual_laea_km2": (residual.area - alternative_pan.area) / 1e6, "symmetric_difference_vs_500m_km2": alternative_pan.symmetric_difference(pan).area / 1e6})
    records, change_rows = [], []
    source_meta = source.set_index("region_id")
    for rid in REGION_ORDER:
        g = allocated[rid]
        diff = (g.area / 1e6 / report_areas[rid] - 1) * 100
        row = {"region_id": rid, "region_kind": "survey_stratum", "display_name_zh": rid + "调查统计单元", "aed_stratum_id": int(source_meta.loc[rid, "aed_stratum"]), "census_year": 2015, "animal_count_status": "historical_source_table", "survey_area_report_km2": report_areas[rid], "area_laea_km2": g.area / 1e6, "geometry_vs_report_pct": diff, "geometry_quality": "generalized_public_map_topology_repaired", "area_difference_flag": abs(diff) > 5, "geometry": g}
        if rid == "ENP3410":
            row["display_name_zh"] = "ENP3、4、10合并调查单元"
        records.append(row)
        change_rows.append({"region_id": rid, "survey_area_report_km2": report_areas[rid], "raw_laea_km2": raw[rid].area / 1e6, "source_micro_parts_to_residual_km2": dropped[rid], "outside_park_removed_km2": (clean[rid].area - clipped[rid].area) / 1e6, "clipped_before_overlap_km2": clipped[rid].area / 1e6, **changes[rid], "final_laea_km2": g.area / 1e6, "geometry_vs_report_pct": diff, "reverse_priority_final_km2": alternative[rid].area / 1e6, "reverse_priority_minus_primary_km2": (alternative[rid].area - g.area) / 1e6, "reverse_priority_symmetric_difference_km2": alternative[rid].symmetric_difference(g).area / 1e6})
    for rid, kind, label, g, quality in [
        ("PAN_MAIN", "main_pan", "主盐沼近似区", pan, "approx_pan_from_unsurveyed_residual_and_figure1"),
        ("UNSURVEYED_OTHER", "unsurveyed_residual", "其他调查外残余", rest, "unsurveyed_unknown_and_boundary_slivers"),
    ]:
        records.append({"region_id": rid, "region_kind": kind, "display_name_zh": label, "aed_stratum_id": None, "census_year": None, "animal_count_status": "unknown_not_zero", "survey_area_report_km2": None, "area_laea_km2": g.area / 1e6, "geometry_vs_report_pct": None, "geometry_quality": quality, "area_difference_flag": None, "geometry": g})
    regions = gpd.GeoDataFrame(records, crs=LAEA)
    regions["n_components"] = regions.geometry.map(lambda g: len(parts(g)))
    union = unary_union(regions.geometry)
    gaps_m2 = park.difference(union).area
    outside_m2 = union.difference(park).area
    overlap_m2 = max(0, sum(g.area for g in regions.geometry) - union.area)
    max_pair_overlap_m2 = max(regions.geometry.iloc[i].intersection(regions.geometry.iloc[j]).area for i in range(len(regions)) for j in range(i + 1, len(regions)))
    checks = {"all_geometries_valid": bool(regions.is_valid.all()), "no_empty_regions": bool((~regions.is_empty).all()), "unique_region_ids": bool(regions.region_id.is_unique), "coverage_gap_laea_m2": gaps_m2, "outside_park_laea_m2": outside_m2, "sum_minus_union_overlap_laea_m2": overlap_m2, "max_pair_overlap_laea_m2": max_pair_overlap_m2, "area_tolerance_m2": AREA_QA_TOLERANCE_M2}
    assert checks["all_geometries_valid"] and checks["no_empty_regions"] and checks["unique_region_ids"]
    assert max(gaps_m2, outside_m2, overlap_m2, max_pair_overlap_m2) <= AREA_QA_TOLERANCE_M2
    regions_wgs = regions.to_crs(4326)
    regions_wgs["area_km2"] = regions_wgs.geometry.map(geod_area)
    area_by_id = regions_wgs.set_index("region_id").area_km2.to_dict()
    regions["area_km2"] = regions.region_id.map(area_by_id)
    regions_wgs.to_file(PROCESSED / "model_regions.geojson", driver="GeoJSON")
    reread = gpd.read_file(PROCESSED / "model_regions.geojson").to_crs(LAEA)
    reread_union = unary_union(reread.geometry)
    checks["saved_geojson_all_valid"] = bool(reread.is_valid.all())
    checks["saved_geojson_park_symmetric_difference_m2"] = park.symmetric_difference(reread_union).area
    checks["saved_geojson_overlap_m2"] = max(0, sum(reread.area) - reread_union.area)
    assert checks["saved_geojson_all_valid"] and checks["saved_geojson_park_symmetric_difference_m2"] < 10 and checks["saved_geojson_overlap_m2"] < 10
    wgs_union = unary_union(regions_wgs.geometry)
    checks["against_original_park_lonlat_gap_geodesic_km2"] = geod_area(original_park_wgs.difference(wgs_union))
    checks["against_original_park_lonlat_outside_geodesic_km2"] = geod_area(wgs_union.difference(original_park_wgs))
    # An additional check in the CRS of the raster, independent of planar QA.
    assert max(checks["against_original_park_lonlat_gap_geodesic_km2"], checks["against_original_park_lonlat_outside_geodesic_km2"]) < 0.00001
    gpkg = OUTPUT / "etosha_model_regions.gpkg"
    # This file is a generated artifact owned by this script, never a source file.
    if gpkg.exists():
        gpkg.unlink()
    regions_wgs.to_file(gpkg, layer="model_regions", driver="GPKG")
    regions.to_file(gpkg, layer="model_regions_laea", driver="GPKG")
    source.to_file(gpkg, layer="aed_public_source", driver="GPKG")
    gpd.GeoDataFrame({"name": ["current_OSM_park_boundary"]}, geometry=[park], crs=LAEA).to_file(gpkg, layer="park_boundary_laea", driver="GPKG")
    points = gpd.GeoDataFrame(regions[["region_id", "region_kind"]].copy(), geometry=regions.geometry.representative_point(), crs=LAEA)
    points_wgs = points.to_crs(4326)
    points_wgs["longitude"] = points_wgs.geometry.x
    points_wgs["latitude"] = points_wgs.geometry.y
    points_wgs["purpose"] = "label_point_only_not_routing_or_ecological_centre"
    points_wgs.to_file(PROCESSED / "region_representative_points.geojson", driver="GeoJSON")
    part_records = []
    for _, row in regions.iterrows():
        for n, g in enumerate(sorted(parts(row.geometry), key=lambda p: p.area, reverse=True), 1):
            part_records.append({"part_id": row.region_id + f"_P{n}", "region_id": row.region_id, "region_kind": row.region_kind, "part_area_laea_km2": g.area / 1e6, "animal_count_link": "parent_region_only", "geometry": g})
    gpd.GeoDataFrame(part_records, crs=LAEA).to_crs(4326).to_file(PROCESSED / "model_region_parts.geojson", driver="GeoJSON")
    csv_write(OUTPUT / "region_catalog.csv", [{k: (None if pd.isna(v) else v) for k, v in row.items() if k != "geometry"} for _, row in regions_wgs.iterrows()])
    csv_write(OUTPUT / "region_geometry_changes.csv", change_rows)
    neighbor_rows = []
    for i, a in regions.iterrows():
        for j, b in regions.iloc[i + 1:].iterrows():
            distance = a.geometry.distance(b.geometry)
            shared = a.geometry.boundary.intersection(b.geometry.boundary).length
            if distance <= NEAR_NEIGHBOR_M:
                neighbor_rows.append({"region_a": a.region_id, "region_b": b.region_id, "minimum_distance_m": distance, "shared_boundary_m": shared, "relationship": "shared_boundary" if shared > 1 else ("point_or_numeric_touch" if distance < 0.01 else "near_boundary_within_500m"), "routing_use_allowed": False})
    csv_write(OUTPUT / "region_neighbors.csv", neighbor_rows)
    joined_checks = species_join(regions_wgs, census)
    flags = [r["region_id"] for r in records if r.get("area_difference_flag")]
    report = {
        "status": "completed_spatial_partition_v1_not_completed_resource_model",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_map_crs": "not declared by AED endpoint; WGS84 longitude/latitude assumed from coordinates and park match",
        "metric_crs": LAEA_PROJ,
        "metric_crs_wkt": LAEA.to_wkt(),
        "edge_interpretation": "Straight line segments in EPSG:4326 coordinates, as used by rasterio; source edges densified to max 0.001 degree before LAEA reprojection",
        "area_conventions": {"area_km2": "WGS84 ellipsoidal area of final geometry", "area_laea_km2": "local Lambert azimuthal equal-area plane, used for overlay, topology QA and additive totals", "survey_area_report_km2": "2015 Table 1, used only as historical animal density denominator; never forced onto geometry"},
        "counts": {"survey_statistical_units": 15, "supplementary_spatial_units": 2, "total_model_units": 17, "actual_geometry_components": len(part_records)},
        "areas": {"park_laea_km2": park.area / 1e6, "park_geodesic_km2": geod_area(gpd.GeoSeries([park], crs=LAEA).to_crs(4326).iloc[0]), "park_geodesic_original_vertices_reference_only_km2": geod_area(original_park_wgs), "report_survey_total_km2": sum(report_areas.values()), "raw_strata_sum_laea_km2": sum(g.area for g in raw.values()) / 1e6, "raw_strata_union_laea_km2": unary_union(list(raw.values())).area / 1e6, "raw_overlapping_excess_laea_km2": (sum(g.area for g in raw.values()) - unary_union(list(raw.values())).area) / 1e6, "corrected_survey_total_laea_km2": surveyed_union.area / 1e6, "main_pan_approx_laea_km2": pan.area / 1e6, "other_unsurveyed_residual_laea_km2": rest.area / 1e6, "final_all_regions_sum_laea_km2": float(regions.area_laea_km2.sum()), "final_all_regions_sum_geodesic_km2": float(regions_wgs.area_km2.sum()), "coverage_percent_laea": union.intersection(park).area / park.area * 100},
        "topology_checks": checks,
        "repair_rules": {"geographic_segmentize_max_degrees": DENSIFY_MAX_DEGREES, "source_micro_component_threshold_km2": MIN_SOURCE_PART_M2 / 1e6, "source_micro_component_destination": "unsurveyed residual, never deletion from park coverage", "enclave": "ENP9 subtracted from ENP11, directly confirmed by report Figure 1", "other_overlap_rule": "smaller Table 1 area has priority; a reproducible boundary repair assumption, not a claim of true ownership", "other_overlap_priority": priority, "outside_park": "clip to current OSM boundary, do not silently assign removed area to another census unit", "gaps": "all remaining gaps kept as unsurveyed; no nearest-region expansion and no animal imputation", "pan_extraction": "negative buffer of residual; keep largest core; positive buffer; intersect original residual; Figure 1 structural review", "pan_opening_radius_m": PAN_RADIUS_M, "geometry_area_not_adjusted_to_report": True},
        "original_overlap_pairs_laea": sorted(overlap_pairs, key=lambda r: r["overlap_laea_km2"], reverse=True),
        "area_difference_over_5_percent_units": flags,
        "pan_sensitivity": pan_sensitivity,
        "overlap_priority_sensitivity": {"alternative_order": reverse_priority, "ENP9_ENP11_constraint_in_both": True, "max_absolute_region_area_change_km2": max(abs(r["reverse_priority_minus_primary_km2"]) for r in change_rows), "max_relative_region_area_change_percent": max(abs(r["reverse_priority_minus_primary_km2"]) / r["final_laea_km2"] * 100 for r in change_rows), "full_per_region_results": "output/regions/region_geometry_changes.csv"},
        "historical_species_link_checks": joined_checks,
        "neighbors": {"rows": len(neighbor_rows), "near_distance_m": NEAR_NEIGHBOR_M, "purpose": "descriptive neighborhood only; multipart parent region and residual cannot be routing nodes; use road graph for travel"},
        "limitations": ["Generalized public map coordinates, not verified original survey GIS; the source has about 300 m coordinate quantization and some larger shape discrepancies.", "ENP8 and ENP9 geometry area differs materially from report area. Use report area for historical density and examine spatial-factor sensitivity before interpreting close rankings.", "PAN_MAIN is a morphology-and-report-guided approximate spatial unit, not an observed land-cover polygon. UNSURVEYED_OTHER includes genuine unknown areas and mapping slivers.", "2015 species estimates and 2021 land cover have different dates; neither is a 2026 measurement.", "Animal quantities in supplementary units are null, not zero. Full-park allocation requires an explicit treatment of missing value later.", "Missing subregional rainfall does not change the partition; use park-wide climate scenarios if needed."]
    }
    dump(OUTPUT / "partition_quality_report.json", report)
    make_maps(regions, park)
    used_packages = ("geopandas", "shapely", "pyproj", "pyogrio", "pandas", "numpy", "matplotlib", "Pillow", "rasterio", "requests")
    versions = {p: importlib.metadata.version(p) for p in used_packages}
    (ROOT / "environment-regions.yml").write_text("name: himcn-regions\nchannels:\n  - defaults\ndependencies:\n  - python=3.12\n  - pip\n  - pip:\n" + "".join(f"      - {p}=={v}\n" for p, v in versions.items()), encoding="utf-8")
    manifest = {
        "created_at_utc": report["executed_at_utc"], "python": platform.python_version(), "software_versions": versions,
        "conda_environment_used": "himcn-roads", "environment_recipe": "environment-regions.yml",
        "reproduce": ["conda env create -f environment-regions.yml", "conda run -n himcn-regions python scripts/regions/build_model_regions.py", "conda run -n himcn-regions python scripts/regions/prepare_ecology.py --offline --regions data/regions/processed/model_regions.geojson"],
        "sources": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(p)} for p in (RAW_MAP, FIGURE, CENSUS, BOUNDARY, Path(__file__))],
        "aed_source_url": "https://africanelephantdatabase.org/population_submissions/722/map",
        "aed_license": "CC BY-NC-SA 4.0; source attribution and noncommercial/share-alike terms retained",
        "boundary_attribution": "OpenStreetMap contributors; ODbL 1.0, see roads provenance",
        "outputs": [{"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(p)} for p in (PROCESSED / "model_regions.geojson", PROCESSED / "model_region_parts.geojson", OUTPUT / "region_catalog.csv", OUTPUT / "region_geometry_changes.csv", OUTPUT / "partition_quality_report.json", gpkg)],
    }
    dump(OUTPUT / "partition_build_manifest.json", manifest)
    print(json.dumps({"model_units": 17, "survey_units": 15, "park_laea_km2": report["areas"]["park_laea_km2"], "main_pan_approx_km2": pan.area/1e6, "other_residual_km2": rest.area/1e6, "topology_checks": checks, "geometry_area_flags": flags, "species_link_checks": joined_checks}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
