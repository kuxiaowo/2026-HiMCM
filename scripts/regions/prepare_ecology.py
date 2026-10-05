"""Fetch WorldCover 2021 intersecting tiles, crop the park, and measure class areas.

Run in the himcn-roads conda environment. Classification values remain unchanged:
the native EPSG:4326 grid is mosaicked without interpolation. Zonal areas use the
WGS84 ellipsoidal area of each native pixel row, not a constant 100 m2 per pixel.
Boundary cells use centre inclusion; the vector/raster area discrepancy is reported.
"""
from __future__ import annotations

import argparse
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
import pandas as pd
import pyproj
import rasterio
import requests
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from rasterio.features import rasterize
from rasterio.transform import Affine
from rasterio.windows import Window
from requests.adapters import HTTPAdapter
from shapely import box, make_valid
from shapely.geometry import Point
from shapely.geometry import mapping
from shapely.geometry.polygon import orient
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
CLASS_LABELS = {
    10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
    50: "Built-up", 60: "Bare / sparse vegetation", 70: "Snow and ice",
    80: "Permanent water", 90: "Herbaceous wetland", 95: "Mangroves",
    100: "Moss and lichen",
}
CLASS_COLORS = {
    0: "#ffffff", 10: "#006400", 20: "#ffbb22", 30: "#ffff4c",
    40: "#f096ff", 50: "#fa0000", 60: "#b4b4b4", 70: "#f0f0f0",
    80: "#0064c8", 90: "#0096a0", 95: "#00cf75", 100: "#fae6a0",
}
FUEL_PROXY_CODES = (10, 20, 30)
GEOD = pyproj.Geod(ellps="WGS84")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "Etosha-model-ecology/1.0"})
    return s


def polygon_area(geom) -> float:
    if geom.geom_type == "Polygon":
        # GeoJSON/rasterize interpret edges as lon/lat straight segments. Feeding
        # a long segment directly to Geod instead interprets a geodesic arc.
        # Densification preserves that lon/lat footprint before area integration.
        return abs(GEOD.geometry_area_perimeter(orient(geom.segmentize(0.001), sign=1.0))[0])
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        return sum(polygon_area(g) for g in geom.geoms)
    return 0.0


def read_polygons(path: Path) -> gpd.GeoDataFrame:
    g = gpd.read_file(path)
    if g.crs is None:
        raise ValueError(f"Input has no declared CRS: {path}")
    g = g.to_crs(4326)
    g.geometry = g.geometry.map(make_valid)
    if g.geometry.is_empty.any():
        raise ValueError(f"Input contains empty geometry: {path}")
    return g


def acquire_tiles(s, boundary, raw_dir: Path, offline: bool) -> dict:
    manifest_file = raw_dir / "worldcover_2021_source_manifest.json"
    if offline:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    else:
        params = {
            "collections": "esa-worldcover", "bbox": ",".join(map(str, boundary.bounds)),
            "datetime": "2021-01-01T00:00:00Z/2021-12-31T23:59:59Z", "limit": 100,
        }
        stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
        response = s.get(stac_url, params=params, timeout=(15, 90))
        response.raise_for_status()
        result = response.json()
        if any(link.get("rel") == "next" for link in result.get("links", [])):
            raise RuntimeError("Unexpected paginated catalogue response; do not silently omit tiles")
        items = sorted(result["features"], key=lambda x: x["id"])
        if not items:
            raise RuntimeError("No WorldCover 2021 tiles returned for boundary")
        manifest = {
            "retrieved_at_utc": utc_now(), "product": "ESA WorldCover 2021 v200 (2.0.0)",
            "stac_url": stac_url, "query_parameters": params,
            "documentation_url": "https://esa-worldcover.org/en/data-access",
            "license": "CC BY 4.0 (attribute ESA WorldCover project / 2021 product)",
            "selection": "Only 3x3-degree COG tiles intersecting the park bounding box; not global download",
            "tiles": [],
        }
        for item in items:
            asset = item["assets"]["map"]
            filename = Path(asset["href"].split("?")[0]).name
            public_url = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/" + filename
            manifest["tiles"].append({
                "item_id": item["id"], "bbox": item["bbox"],
                "product_version": item["properties"].get("esa_worldcover:product_version"),
                "download_url": public_url, "catalogue_asset_url": asset["href"].split("?")[0],
                "file": str((raw_dir / filename).relative_to(ROOT)).replace("\\", "/"),
                "asset_metadata": {k: asset[k] for k in ("proj:shape", "proj:transform", "raster:bands", "classification:classes")},
            })
    raw_dir.mkdir(parents=True, exist_ok=True)
    for tile in manifest["tiles"]:
        path = ROOT / tile["file"]
        if not path.exists():
            if offline:
                raise FileNotFoundError(path)
            print(f"Downloading intersecting tile: {tile['item_id']}", flush=True)
            response = s.get(tile["download_url"], stream=True, timeout=(15, 120))
            response.raise_for_status()
            if response.status_code != 200:
                raise RuntimeError("Full tile download must return HTTP 200, not a truncated range")
            temporary = path.with_suffix(path.suffix + ".part")
            with temporary.open("wb") as f:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
            with rasterio.open(temporary) as src:
                if src.count != 1 or src.nodata != 0 or src.dtypes != ("uint8",):
                    raise RuntimeError("Unexpected WorldCover map band semantics")
            temporary.replace(path)
        tile["bytes"] = path.stat().st_size
        tile["sha256"] = digest(path)
        with rasterio.open(path) as src:
            tile["crs"] = str(src.crs)
            tile["transform"] = list(src.transform)[:6]
            tile["width"] = src.width
            tile["height"] = src.height
            tile["nodata"] = src.nodata
    write_json(manifest_file, manifest)
    return manifest


def crop_park(boundary, boundary_path: Path, manifest: dict, destination: Path,
              force: bool, block_rows: int) -> dict:
    metadata_file = destination.with_suffix(".json")
    fingerprint = {
        "boundary_sha256": digest(boundary_path),
        "source_sha256": {t["item_id"]: t["sha256"] for t in manifest["tiles"]},
        "mask_rule": "pixel centre inside park; outside set to nodata=0",
    }
    if destination.exists() and metadata_file.exists() and not force:
        old = json.loads(metadata_file.read_text(encoding="utf-8"))
        if old.get("fingerprint") == fingerprint:
            print("Reusing identical native-grid park crop", flush=True)
            return old
    sources = [rasterio.open(ROOT / t["file"]) for t in manifest["tiles"]]
    try:
        reference = sources[0]
        dx, dy = reference.transform.a, -reference.transform.e
        if any(s.crs != reference.crs or abs(s.transform.a - dx) > 1e-12
               or abs(s.transform.e + dy) > 1e-12 for s in sources):
            raise ValueError("Tiles must share their native EPSG:4326 grid")
        xmin, ymin, xmax, ymax = boundary.bounds
        left_col = math.floor((xmin - reference.bounds.left) / dx)
        right_col = math.ceil((xmax - reference.bounds.left) / dx)
        top_row = math.floor((reference.bounds.top - ymax) / dy)
        bottom_row = math.ceil((reference.bounds.top - ymin) / dy)
        width, height = right_col - left_col, bottom_row - top_row
        transform = Affine(dx, 0, reference.bounds.left + left_col * dx,
                           0, -dy, reference.bounds.top - top_row * dy)
        profile = dict(driver="GTiff", height=height, width=width, count=1, dtype="uint8",
                       crs=reference.crs, transform=transform, nodata=0, tiled=True,
                       blockxsize=512, blockysize=512, compress="DEFLATE", predictor=1,
                       BIGTIFF="IF_SAFER", NUM_THREADS="2")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp.tif")
        with rasterio.open(temporary, "w", **profile) as dst:
            for row in range(0, height, block_rows):
                n = min(block_rows, height - row)
                array = np.zeros((n, width), dtype="uint8")
                for src in sources:
                    col_offset = round((src.bounds.left - transform.c) / dx)
                    row_offset = round((transform.f - src.bounds.top) / dy)
                    dcol0, dcol1 = max(0, col_offset), min(width, col_offset + src.width)
                    drow0, drow1 = max(row, row_offset), min(row + n, row_offset + src.height)
                    if dcol1 <= dcol0 or drow1 <= drow0:
                        continue
                    window = Window(dcol0 - col_offset, drow0 - row_offset,
                                    dcol1 - dcol0, drow1 - drow0)
                    array[drow0-row:drow1-row, dcol0:dcol1] = src.read(1, window=window)
                stripe_transform = transform * Affine.translation(0, row)
                inside = rasterize([(mapping(boundary), 1)], out_shape=array.shape,
                                   transform=stripe_transform, fill=0, all_touched=False,
                                   dtype="uint8")
                array[inside == 0] = 0
                dst.write(array, 1, window=Window(0, row, width, n))
                if row % (block_rows * 8) == 0:
                    print(f"Crop rows {row:,}/{height:,}", flush=True)
            dst.update_tags(product="ESA WorldCover 2021 v200", class_nodata="0",
                            resampling="none; exact native-grid tile concatenation",
                            park_mask="pixel centre inside polygon")
            dst.write_colormap(1, {code: tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                                  + ((0,) if code == 0 else (255,))
                                  for code, color in CLASS_COLORS.items()})
        temporary.replace(destination)
        metadata = {
            "created_at_utc": utc_now(), "fingerprint": fingerprint,
            "file": str(destination.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(destination), "bytes": destination.stat().st_size,
            "crs": str(reference.crs), "transform": list(transform)[:6],
            "width": width, "height": height,
            "resolution_degrees": [dx, dy], "nominal_resolution_metres": 10,
            "nodata": 0, "resampling": "none", "boundary_rule": fingerprint["mask_rule"],
        }
        write_json(metadata_file, metadata)
        return metadata
    finally:
        for src in sources:
            src.close()


def pixel_row_areas(transform, first_row: int, count: int) -> np.ndarray:
    """Ellipsoidal area is constant along each row of this regular lon/lat grid."""
    x0, x1 = transform.c, transform.c + transform.a
    result = []
    for row in range(first_row, first_row + count):
        y0, y1 = transform.f + row * transform.e, transform.f + (row + 1) * transform.e
        area, _ = GEOD.polygon_area_perimeter([x0, x1, x1, x0], [y0, y0, y1, y1])
        result.append(abs(area))
    return np.asarray(result, dtype="float64")


def verify_native_samples(raster: Path, manifest: dict, boundary) -> dict:
    """Audit the crop against source classes on both sides of the tile seam."""
    rng = np.random.default_rng(20261005)
    count = 400
    sources = [rasterio.open(ROOT / t["file"]) for t in manifest["tiles"]]
    checked_inside = checked_outside = mismatches = 0
    per_tile = {t["item_id"]: 0 for t in manifest["tiles"]}
    try:
        with rasterio.open(raster) as dst:
            rows = rng.integers(0, dst.height, size=count)
            cols = rng.integers(0, dst.width, size=count)
            for row, col in zip(rows, cols):
                x, y = dst.xy(int(row), int(col))
                actual = int(dst.read(1, window=Window(int(col), int(row), 1, 1))[0, 0])
                if not boundary.covers(Point(x, y)):
                    checked_outside += 1
                    mismatches += actual != 0
                    continue
                found = False
                for src, tile in zip(sources, manifest["tiles"]):
                    if src.bounds.left <= x < src.bounds.right and src.bounds.bottom < y <= src.bounds.top:
                        sr, sc = src.index(x, y)
                        expected = int(src.read(1, window=Window(sc, sr, 1, 1))[0, 0])
                        mismatches += actual != expected
                        checked_inside += 1
                        per_tile[tile["item_id"]] += 1
                        found = True
                        break
                if not found:
                    raise RuntimeError("Crop sample inside park has no source tile")
    finally:
        for src in sources:
            src.close()
    audit = {"method": "fixed-seed native-pixel crop/source equality; exterior cells required nodata=0",
             "seed": 20261005, "sample_count": count, "inside_park_samples": checked_inside,
             "outside_park_samples": checked_outside, "inside_samples_per_source_tile": per_tile,
             "mismatch_count": int(mismatches)}
    if mismatches:
        raise RuntimeError(f"Native-grid crop/source verification failed: {audit}")
    return audit


def class_statistics(raster: Path, regions: gpd.GeoDataFrame, boundary,
                     block_rows: int) -> tuple[list[dict], dict]:
    if "region_id" not in regions:
        raise ValueError("Regions must have region_id")
    if regions.region_id.duplicated().any() or regions.region_id.isna().any():
        raise ValueError("region_id must be nonmissing and unique")
    regions = regions.copy().reset_index(drop=True)
    regions.geometry = regions.geometry.map(lambda g: g.intersection(boundary))
    geometries = list(regions.geometry)
    labels = [(mapping(g), n + 1) for n, g in enumerate(geometries) if not g.is_empty]
    counts = np.zeros((len(regions) + 1, 256), dtype="int64")
    areas = np.zeros((len(regions) + 1, 256), dtype="float64")
    cell_sizes = []
    with rasterio.open(raster) as src:
        for row in range(0, src.height, block_rows):
            n = min(block_rows, src.height - row)
            win = Window(0, row, src.width, n)
            a = src.read(1, window=win)
            stripe_transform = src.transform * Affine.translation(0, row)
            stripe_bounds = rasterio.windows.bounds(win, src.transform)
            intersects = box(*stripe_bounds)
            stripe_labels = [(mapping(g), i + 1) for i, g in enumerate(geometries)
                             if not g.is_empty and g.intersects(intersects)]
            if not stripe_labels:
                continue
            ids = rasterize(stripe_labels, out_shape=a.shape, transform=stripe_transform,
                            fill=0, all_touched=False, dtype="int32")
            row_areas = pixel_row_areas(src.transform, row, n)
            cell_sizes.extend([float(row_areas.min()), float(row_areas.max())])
            for j in range(n):
                combined = ids[j].astype("int64") * 256 + a[j]
                histogram = np.bincount(combined, minlength=(len(regions)+1)*256)
                histogram = histogram.reshape(len(regions)+1, 256)
                counts += histogram
                areas += histogram * row_areas[j]
            if row % (block_rows * 8) == 0:
                print(f"Zonal statistics rows {row:,}/{src.height:,}", flush=True)
    result = []
    unknown = set(np.nonzero(counts[1:].sum(axis=0))[0]) - set(CLASS_LABELS) - {0}
    if unknown:
        raise ValueError(f"Unknown classification codes present: {sorted(unknown)}")
    for idx, feature in regions.iterrows():
        label = regions.index.get_loc(idx) + 1
        vector_area = polygon_area(feature.geometry)
        raster_area = areas[label].sum()
        valid_area = sum(areas[label, c] for c in CLASS_LABELS)
        region_type = str(feature.get("region_type", feature.get("region_kind", "unspecified")))
        survey_id = feature.get("survey_id", feature.region_id if region_type == "survey_stratum" else None)
        aed_id = feature.get("aed_stratum_id")
        entry = {"region_id": str(feature.region_id), "region_type": region_type,
                 "region_kind": region_type,
                 "survey_id": None if pd.isna(survey_id) else str(survey_id),
                 "aed_stratum_id": None if pd.isna(aed_id) else int(aed_id),
                 "area_km2": vector_area / 1e6, "raster_footprint_area_km2": raster_area / 1e6,
                 "raster_vs_vector_area_relative_error": raster_area / vector_area - 1 if vector_area else None,
                 "valid_area_km2": valid_area / 1e6, "nodata_area_km2": areas[label, 0] / 1e6,
                 "valid_coverage": min(1.0, max(0.0, valid_area / raster_area)) if raster_area else None,
                 "valid_pixel_count": int(sum(counts[label, c] for c in CLASS_LABELS))}
        for code in CLASS_LABELS:
            entry[f"wc_{code}_area_km2"] = areas[label, code] / 1e6
            entry[f"wc_{code}_share_valid"] = areas[label, code] / valid_area if valid_area else None
        fuel = sum(areas[label, c] for c in FUEL_PROXY_CODES)
        entry["fuel_proxy_codes"] = "10|20|30"
        entry["fuel_proxy_before_pan_mask_km2"] = fuel / 1e6
        entry["fuel_proxy_before_pan_mask_share_valid"] = fuel / valid_area if valid_area else None
        entry["fuel_proxy_before_pan_mask_share_region"] = fuel / raster_area if raster_area else None
        entry["main_pan_excluded_from_fuel"] = entry["region_type"] == "main_pan"
        if entry["main_pan_excluded_from_fuel"]:
            fuel = 0.0
        entry["fuel_proxy_area_km2"] = fuel / 1e6
        entry["fuel_proxy_share_valid"] = fuel / valid_area if valid_area else None
        entry["fuel_proxy_share_region"] = fuel / raster_area if raster_area else None
        result.append(entry)
    meta = {
        "area_method": "WGS84 ellipsoidal pixel quadrilateral area, calculated per latitude row; each cell assigned by centre point",
        "vector_area_method": "densify lon/lat straight segments to <=0.001 degree, then pyproj.Geod.geometry_area_perimeter on oriented WGS84 rings",
        "resampling_for_statistics": "none",
        "pixel_area_min_m2": min(cell_sizes), "pixel_area_max_m2": max(cell_sizes),
        "valid_coverage_denominator": "all region-assigned native cells including nodata; independent vector/raster discrepancy reported",
        "class_share_denominator": "valid classified area, not whole region area",
        "fuel_proxy_share_denominators": "share_valid uses valid classified area; share_region uses complete assigned footprint including nodata, so use valid_coverage alongside it",
        "fuel_proxy_definition": "WorldCover classes 10/20/30 (tree/shrub/grass), minus explicit region_type=main_pan",
        "fuel_proxy_limitation": "Habitat proxy, not measured fuel load or predicted fire probability; wetlands/cropland excluded in baseline",
        "salt_pan_rule": "Only independently mapped main_pan is excluded explicitly; class 60 is never synonymous with salt pan",
    }
    return result, meta


def write_csv(path: Path, entries: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(entries[0]))
        writer.writeheader()
        writer.writerows(entries)


def preview(raster: Path, boundary, regions, output: Path) -> None:
    keys = [0] + list(CLASS_LABELS)
    cmap = ListedColormap([CLASS_COLORS[k] for k in keys])
    norm = BoundaryNorm(np.arange(-0.5, len(keys)+0.5), len(keys))
    with rasterio.open(raster) as src:
        factor = max(1, src.width / 2200)
        arr = src.read(1, out_shape=(round(src.height/factor), round(src.width/factor)),
                       resampling=rasterio.enums.Resampling.nearest)
        index = np.zeros_like(arr)
        for i, code in enumerate(keys):
            index[arr == code] = i
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
    fig, ax = plt.subplots(figsize=(15, 6.8))
    ax.imshow(index, extent=extent, origin="upper", cmap=cmap, norm=norm,
              interpolation="nearest", aspect="equal")
    gpd.GeoSeries([boundary], crs=4326).boundary.plot(ax=ax, color="black", linewidth=1)
    if regions is not None:
        regions.boundary.plot(ax=ax, color="#294557", linewidth=0.55, alpha=.8)
        for _, region in regions.iterrows():
            geom = region.geometry
            label = "OTHER" if str(region.region_id) == "UNSURVEYED_OTHER" else str(region.region_id)
            if geom.geom_type == "MultiPolygon":
                components = list(geom.geoms)
                kind = region.get("region_type", region.get("region_kind"))
                if kind == "survey_stratum":
                    label_geometries = [g for g in components if g.area >= geom.area * .01]
                else:
                    label_geometries = [max(components, key=lambda g: g.area)]
            else:
                label_geometries = [geom]
            for label_geom in label_geometries:
                p = label_geom.representative_point()
                ax.text(p.x, p.y, label, fontsize=6,
                        ha="center", va="center", bbox=dict(facecolor="white", alpha=.65, edgecolor="none", pad=.4))
    present = [k for k in CLASS_LABELS if k in np.unique(arr)]
    ax.legend(handles=[Patch(facecolor=CLASS_COLORS[k], label=f"{k}: {CLASS_LABELS[k]}")
                       for k in present], loc="upper center", bbox_to_anchor=(.5, -.10),
              ncol=4, fontsize=8, frameon=False)
    ax.set_title("Etosha National Park | ESA WorldCover 2021 v200\nNative classes; reduced-resolution preview only", fontsize=13)
    ax.set_xlabel("Longitude (degrees east)")
    ax.set_ylabel("Latitude (degrees)")
    ax.text(.01, .015, "Source: ESA WorldCover 2021 | Park: OSM relation 2982497\nClass 60 includes bare / sparse vegetation; it does not identify salt pans.\nOTHER = UNSURVEYED_OTHER; repeated ENP3410 labels denote one multipart survey unit.",
            transform=ax.transAxes, fontsize=7, bbox=dict(facecolor="white", alpha=.8, edgecolor="none"))
    fig.subplots_adjust(bottom=.22)
    fig.savefig(output, dpi=180, facecolor="white")
    plt.close(fig)


def documentation(path: Path, whole: dict, metadata: dict, entries: list[dict] | None,
                  quality: dict) -> None:
    table = "\n".join(f"| {c} | {CLASS_LABELS[c]} | {whole[f'wc_{c}_area_km2']:.3f} | {whole[f'wc_{c}_share_valid']*100:.3f}% |"
                      for c in CLASS_LABELS)
    regional_section = ""
    if entries is not None:
        regional_table = "\n".join(
            f"| {r['region_id']} | {r['area_km2']:.2f} | {r['wc_20_share_valid']*100:.2f}% | "
            f"{r['wc_30_share_valid']*100:.2f}% | {r['wc_60_share_valid']*100:.2f}% | "
            f"{r['fuel_proxy_share_valid']*100:.2f}% | {r['valid_coverage']*100:.2f}% |" for r in entries)
        pans = [r for r in entries if r["main_pan_excluded_from_fuel"]]
        pan_note = "\n".join(
            f"- {p['region_id']} 原始林地/灌丛/草地近似 {p['fuel_proxy_before_pan_mask_km2']:.3f} km²，"
            f"占有效分类面积 {p['fuel_proxy_before_pan_mask_share_valid']*100:.4f}%；全部置零会排除这些"
            f"像元（相当于全园原始近似面积的 {p['fuel_proxy_before_pan_mask_km2']/whole['fuel_proxy_before_pan_mask_km2']*100:.4f}%）。"
            "这可能包含岸缘草地、季节植被或边界概化误差，不能据置零宣称盐沼绝无可燃植被；"
            "保留原始面积用于盐沼掩膜敏感性。" for p in pans)
        regional_section = f"""
## 分区生态结构

| 区域 | 矢量面积 km² | 灌丛 | 草地 | 裸地/稀疏植被 | 可燃近似（盐沼约束后） | 有效覆盖 |
|---|---:|---:|---:|---:|---:|---:|
{regional_table}

上表类别比例分母均为有效分类面积，不代表生态质量评分。完整11类面积见区域CSV。

{pan_note}

- 区域分配的有效像元面积占全园有效面积 {quality['region_assigned_valid_area_fraction']*100:.6f}%；
  区域合计与全园差 {quality['region_class_area_sum_check_km2']:.6f} km²。边界像元由中心规则离散分配，
  导出地理坐标的线段近似也会形成细小边缘差；本步骤保留差异，不虚构补齐像元。
- 矢量分区检查为对导出WGS84坐标作几何运算；与主分区脚本在等面积坐标中实施的拓扑检查分开记录，
  指标见 `region_partition_geometry`。有效分类覆盖率与区域像元归属覆盖率不是同一个概念。
"""
    path.write_text(f"""# 埃托沙生态底图获取与区域统计记录

## 数据与复现

- 数据：ESA WorldCover 2021，算法 v200 / 产品 2.0.0，名义分辨率 10 m。
- 官方说明：https://esa-worldcover.org/en/data-access；目录通过 Planetary Computer STAC 检索。
- 仅下载与公园包络相交的两块 3°×3° COG（S21E012、S21E015），未下载全球图层。
- 各原始文件下载 URL（无签名参数）、字节数和 SHA-256 见 `data/ecology/raw/worldcover_2021_source_manifest.json`。
- 原生 EPSG:4326 网格逐块拼接，不插值、不重分类。0 保留为 nodata，公园以外设为 0。
- 脚本：`scripts/regions/prepare_ecology.py`；使用 conda 环境 `himcn-roads`，Python / rasterio 等版本见质量报告。
- 运行：`D:/Python/Conda/envs/himcn-roads/python.exe scripts/regions/prepare_ecology.py --regions data/regions/processed/model_regions.geojson`。
- 公园裁切文件及其边界/source 指纹见 `data/ecology/processed/worldcover_2021_etosha.json`。再次运行可用 `--offline` 复用本地瓦片，不请求目录。

## 统计口径

1. 区域边界变换到 WGS84，按像元中心落在区域内分配原生像元；未做边界像元面积分数分摊。
2. 对每个纬度行，以 WGS84 椭球计算单个像元四边形面积，再乘该行各类型像元数。实际像元面积范围 {metadata['pixel_area_min_m2']:.4f}—{metadata['pixel_area_max_m2']:.4f} m²，不能统一视为 100 m²。
3. `area_km2` 为矢量椭球面积。先将经纬度直线边界以最长0.001°（约100 m）加密，再积分椭球面积，避免把长线端点误解释为不同的椭球弧线。`raster_footprint_area_km2` 为中心落点分配的像元面积。二者相对差异单独报告，反映边缘离散误差。
4. `valid_coverage` = 有效分类像元面积 / 分配到区域的所有像元面积；缺失不能记成裸地或草地。`wc_<code>_share_valid` 分母是有效分类面积。
5. 可燃生境近似只使用 10/20/30（林地/灌丛/草地），它是生境代理，不能称为实测燃料量或火灾概率。草本湿地、农田等未纳入基准，可另做掩膜情景。
6. `region_type=main_pan` 显式排除可燃生境；仍保留其原始生态类别比例。其他裸地不自动等于盐沼。独立盐沼边界若为地图配准近似，其不确定性承袭自分区成果。
7. 地类面积比例描述结构，不给林地、草地统一赋价值排序；WorldCover InputQuality 不是分类概率，因此本步骤未用其作生态质量分数。
8. 2021 土地覆盖与2015 动物调查年份不同。可作固定生境近似，不能称2026实测，也不能直接与2020图对比后断言地类真实变化。

## 全园统计

- 矢量椭球面积：{whole['area_km2']:.3f} km²。
- 原生像元覆盖面积：{whole['raster_footprint_area_km2']:.3f} km²；与矢量差异 {whole['raster_vs_vector_area_relative_error']*100:.5f}%。
- 有效覆盖率：{whole['valid_coverage']*100:.5f}%；有效像元 {whole['valid_pixel_count']:,}。
- 可燃生境近似（未扣独立盐沼）：{whole['fuel_proxy_before_pan_mask_km2']:.3f} km²。

| 编码 | 类别 | 面积 km² | 有效面积占比 |
|---:|---|---:|---:|
{table}

## 输出字段与模型连接

`region_id` 与模型区域表一对一连接；`region_type`、`survey_id` 保留分区属性。按区输出 `area_km2`、`valid_area_km2`、`valid_coverage`、各类面积/比例、`fuel_proxy_area_km2`、`fuel_proxy_share_valid`、`fuel_proxy_share_region`。燃料近似比例的前者以有效分类面积为分母，后者以整个像元覆盖面积为分母，需配合有效覆盖率使用。

区域统计状态：{'已对最终 model_regions.geojson 计算。' if entries is not None else '最终分区未到位，当前仅完成全园统计；分区完成后使用 --regions 复跑。'}

{regional_section}

预览仅最近邻降采样用于显示；统计使用原生全分辨率分类值。图见 `output/regions/ecology/worldcover_2021_preview.png`。区域和全园 CSV 均为 UTF-8 BOM，便于中文 Excel 查看。
""", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary", type=Path, default=ROOT / "data/roads/processed/park_boundary.geojson")
    parser.add_argument("--regions", type=Path, default=None)
    parser.add_argument("--offline", action="store_true", help="Use previously downloaded tile manifest and tiles")
    parser.add_argument("--force-crop", action="store_true")
    parser.add_argument("--block-rows", type=int, default=256)
    args = parser.parse_args()
    if args.block_rows <= 0:
        parser.error("--block-rows must be positive")
    boundary_path = args.boundary.resolve()
    park = read_polygons(boundary_path).geometry.union_all()
    raw_dir = ROOT / "data/ecology/raw"
    out_dir = ROOT / "output/regions/ecology"
    out_dir.mkdir(parents=True, exist_ok=True)
    raster = ROOT / "data/ecology/processed/worldcover_2021_etosha.tif"
    with session() as s:
        manifest = acquire_tiles(s, park, raw_dir, args.offline)
    crop_metadata = crop_park(park, boundary_path, manifest, raster, args.force_crop, args.block_rows)
    native_sample_audit = verify_native_samples(raster, manifest, park)
    whole_regions = gpd.GeoDataFrame([{"region_id": "PARK", "region_type": "whole_park", "geometry": park}], crs=4326)
    whole_entries, area_meta = class_statistics(raster, whole_regions, park, args.block_rows)
    write_csv(out_dir / "park_ecology.csv", whole_entries)
    regions = None
    region_entries = None
    if args.regions is not None:
        regions = read_polygons(args.regions.resolve())
        region_entries, _ = class_statistics(raster, regions, park, args.block_rows)
        write_csv(out_dir / "region_ecology.csv", region_entries)
        write_json(out_dir / "region_ecology.json", {"schema_version": 1, "regions_file": str(args.regions),
                                                   "regions_sha256": digest(args.regions.resolve()),
                                                   "metadata": area_meta, "regions": region_entries})
    preview(raster, park, regions, out_dir / "worldcover_2021_preview.png")
    region_partition = None
    if regions is not None:
        clipped_geometries = [g.intersection(park) for g in regions.geometry]
        union = gpd.GeoSeries(clipped_geometries, crs=4326).union_all()
        pairwise_overlaps = [a.intersection(b) for i, a in enumerate(clipped_geometries)
                             for b in clipped_geometries[i+1:] if a.intersects(b)]
        overlap_union = gpd.GeoSeries(pairwise_overlaps, crs=4326).union_all() if pairwise_overlaps else None
        region_partition = {
            "missing_park_area_km2": polygon_area(park.difference(union)) / 1e6,
            "overlap_union_area_km2": polygon_area(overlap_union) / 1e6 if overlap_union is not None else 0.0,
            "geodesic_sum_minus_union_area_km2": (sum(polygon_area(g) for g in clipped_geometries) - polygon_area(union)) / 1e6,
            "outside_park_area_km2": sum(polygon_area(g.difference(park)) for g in regions.geometry) / 1e6,
            "statistics_clip_rule": "all supplied region geometries clipped to park before centre-cell assignment",
            "area_note": "True geometric overlap uses pairwise intersections; geodesic sum-minus-union can differ because long rings have different segmentation",
        }
    quality = {
        "generated_at_utc": utc_now(), "product": manifest["product"], "source_manifest": "data/ecology/raw/worldcover_2021_source_manifest.json",
        "crop": crop_metadata, "area_statistics": area_meta,
        "native_grid_sample_verification": native_sample_audit,
        "software": {"python": platform.python_version(), "rasterio": rasterio.__version__, "gdal": rasterio.__gdal_version__,
                     "geopandas": gpd.__version__, "pyproj": pyproj.__version__, "numpy": np.__version__},
        "whole_park": whole_entries[0], "region_count": len(region_entries) if region_entries else 0,
        "region_partition_geometry": region_partition,
        "region_class_area_sum_check_km2": sum(x["valid_area_km2"] for x in region_entries) - whole_entries[0]["valid_area_km2"] if region_entries else None,
        "region_assigned_valid_area_fraction": sum(x["valid_area_km2"] for x in region_entries) / whole_entries[0]["valid_area_km2"] if region_entries else None,
        "limitations": ["2021 class map is historical static habitat proxy", "Centre-rule boundary pixels; area discrepancy reported",
                        "Class 60 is bare / sparse vegetation, not an independent salt-pan map", "Fuel proxy is not observed fuel load"]}
    write_json(out_dir / "ecology_quality_report.json", quality)
    documentation(out_dir / "生态底图处理说明.md", whole_entries[0], area_meta, region_entries, quality)
    print(json.dumps({"park_valid_coverage": whole_entries[0]["valid_coverage"],
                      "region_count": quality["region_count"], "outputs": str(out_dir)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
