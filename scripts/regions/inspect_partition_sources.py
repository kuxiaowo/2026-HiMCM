"""Inspect public 2015 strata against the current park boundary; no edits to data."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tmp/regions/diagnostics"
OUT.mkdir(parents=True, exist_ok=True)
CRS = "+proj=laea +lat_0=-19 +lon_0=15.75 +datum=WGS84 +units=m +no_defs"
strata = gpd.read_file(ROOT / "data/regions/raw/source_audit/aed_2015_map_normalized.geojson").to_crs(CRS)
park = gpd.read_file(ROOT / "data/roads/processed/park_boundary.geojson").to_crs(CRS)
park_geom = unary_union(park.geometry)
remaining = park_geom.difference(unary_union(strata.geometry))
parts = list(remaining.geoms) if hasattr(remaining, "geoms") else [remaining]
parts = sorted(parts, key=lambda x: x.area, reverse=True)
print("columns", list(strata.columns))
print("residual components", len(parts))
for i, g in enumerate(parts[:20]):
    wgs = gpd.GeoSeries([g], crs=CRS).to_crs(4326).iloc[0]
    print(i, round(g.area / 1e6, 6), list(wgs.bounds), list(wgs.representative_point().coords)[0])
fig, axes = plt.subplots(2, 1, figsize=(14, 11), constrained_layout=True)
strata.plot(ax=axes[0], color=[plt.get_cmap("tab20")(i) for i in range(len(strata))], edgecolor="#333", linewidth=0.5, alpha=0.55)
for _, row in strata.iterrows():
    p = row.geometry.representative_point()
    label = row["aed_name"]
    axes[0].text(p.x, p.y, str(label), fontsize=8, ha="center")
park.boundary.plot(ax=axes[0], color="black", linewidth=1)
gpd.GeoSeries([remaining], crs=CRS).plot(ax=axes[1], color="#ccdce9", edgecolor="#446677", linewidth=0.4)
park.boundary.plot(ax=axes[1], color="black", linewidth=1)
strata.boundary.plot(ax=axes[1], color="#888", linewidth=0.4)
for i, g in enumerate(parts[:20]):
    p = g.representative_point()
    axes[1].text(p.x, p.y, str(i), fontsize=8, ha="center")
axes[0].set_title("Public AED 2015 strata (raw outlines) and current OSM park boundary")
axes[1].set_title("Park area not covered by raw strata: numbered components")
for ax in axes:
    ax.set_aspect("equal")
    ax.set_xlabel("Local equal-area easting (m)")
    ax.set_ylabel("Local equal-area northing (m)")
fig.savefig(OUT / "source_geometry_overview.png", dpi=160)
print(OUT / "source_geometry_overview.png")
fig, axes = plt.subplots(3, 1, figsize=(14, 13), constrained_layout=True)
opening_rows = []
for ax, radius in zip(axes, (250, 500, 1000)):
    erosion = remaining.buffer(-radius)
    cores = list(erosion.geoms) if hasattr(erosion, "geoms") else [erosion]
    core = max(cores, key=lambda g: g.area)
    main = core.buffer(radius).intersection(remaining)
    rest = remaining.difference(main)
    print("main opening radius", radius, "main_km2", main.area/1e6, "other_km2", rest.area/1e6)
    opening_rows.append({"radius_m": radius, "main_pan_approx_area_km2": main.area/1e6, "other_residual_area_km2": rest.area/1e6})
    gpd.GeoSeries([main], crs=CRS).plot(ax=ax, color="#94c4de", linewidth=0)
    gpd.GeoSeries([rest], crs=CRS).plot(ax=ax, color="#ad775e", linewidth=0.5)
    strata.boundary.plot(ax=ax, color="#888", linewidth=0.5)
    park.boundary.plot(ax=ax, color="black", linewidth=0.8)
    ax.set_aspect("equal")
    ax.set_title(f"Main pan approximate separation: opening radius {radius} m")
fig.savefig(OUT / "pan_separation_sensitivity.png", dpi=140)
(OUT / "pan_separation_sensitivity.json").write_text(json.dumps(opening_rows, indent=2), encoding="utf-8")
