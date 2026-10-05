"""Inspect the user's GPCC gzip NetCDF without loading the global array in RAM.

The example is decompressed temporarily, read with SciPy's classic-NetCDF mmap,
and its metadata plus an Etosha bounding-box diagnostic saved as JSON. The box
is NOT a park/region area-weighted rainfall result. The source is unchanged.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import shutil
import struct
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy.io import netcdf_file
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "output/gpcc_precipitation_analysis_monthly_1971_1975_v2025_025.nc.gz"
TMP = ROOT / "tmp/rainfall"
NC = TMP / "gpcc_1971_1975_inspection.nc"
OUT = ROOT / "output/rainfall"


def clean(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").rstrip("\x00")
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def decode_times(values, units, calendar):
    if calendar not in {"standard", "gregorian", "proleptic_gregorian", None}:
        return None
    match = re.match(r"(days?|hours?|minutes?|seconds?) since (.+)", units)
    if not match:
        return None
    try:
        base = match[2].strip().replace(" UTC", "").replace("Z", "+00:00")
        date_match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})(.*)", base)
        if date_match:
            year, month, day, rest = date_match.groups()
            base = f"{int(year):04d}-{int(month):02d}-{int(day):02d}{rest}"
        origin = datetime.fromisoformat(base)
    except ValueError:
        return None
    factor = {"day": 86400, "hour": 3600, "minute": 60, "second": 1}[match[1].rstrip("s")]
    return [(origin + timedelta(seconds=float(v) * factor)).isoformat() for v in values]


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with SOURCE.open("rb") as f:
        f.seek(-4, 2)
        expected = struct.unpack("<I", f.read(4))[0]
    if not NC.exists() or NC.stat().st_size != expected:
        if shutil.disk_usage(TMP).free < expected + 100_000_000:
            raise RuntimeError("Insufficient space for temporary NetCDF inspection")
        with gzip.open(SOURCE, "rb") as src, NC.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=4 * 1024 * 1024)
    features = json.loads((ROOT / "data/regions/processed/model_regions.geojson").read_text(encoding="utf-8"))["features"]
    bounds = unary_union([shape(f["geometry"]) for f in features]).bounds
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "source": str(SOURCE), "compressed_bytes": SOURCE.stat().st_size,
              "uncompressed_bytes": NC.stat().st_size, "park_bounds_lon_lat": bounds,
              "bbox_is_not_polygon_weighted_park_rainfall": True}
    with netcdf_file(NC, "r", mmap=True) as dataset:
        report["dimensions"] = dict(dataset.dimensions)
        report["global_attributes"] = clean(dataset._attributes)
        lat_name = next(n for n in ("lat", "latitude") if n in dataset.variables)
        lon_name = next(n for n in ("lon", "longitude") if n in dataset.variables)
        lat = np.array(dataset.variables[lat_name][:], dtype=float, copy=True)
        lon = np.array(dataset.variables[lon_name][:], dtype=float, copy=True)
        canonical_lon = (lon + 180) % 360 - 180
        dy = float(np.median(np.abs(np.diff(lat))))
        dx = float(np.median(np.abs(np.diff(lon))))
        lat_ids = np.where((lat >= bounds[1] - dy / 2) & (lat <= bounds[3] + dy / 2))[0]
        lon_ids = np.where((canonical_lon >= bounds[0] - dx / 2) & (canonical_lon <= bounds[2] + dx / 2))[0]
        assert len(lat_ids) and len(lon_ids)
        assert np.all(np.diff(lat_ids) == 1) and np.all(np.diff(lon_ids) == 1)
        report["coordinates"] = {"latitude_first_last": [lat[0], lat[-1]],
                                 "longitude_first_last": [lon[0], lon[-1]],
                                 "latitude_spacing_degrees": dy, "longitude_spacing_degrees": dx,
                                 "etosha_bbox_latitude_centers": lat[lat_ids].tolist(),
                                 "etosha_bbox_longitude_centers": canonical_lon[lon_ids].tolist(),
                                 "bbox_cells_per_month": len(lat_ids) * len(lon_ids)}
        time = dataset.variables.get("time")
        if time is not None:
            tv = np.array(time[:], dtype=float, copy=True)
            ta = clean(time._attributes)
            dates = decode_times(tv, ta.get("units", ""), ta.get("calendar"))
            report["time"] = {"count": len(tv), "attributes": ta,
                              "raw_first_last": [tv[0], tv[-1]], "decoded_dates": dates}
        time = None
        variables = {}
        for name, variable in dataset.variables.items():
            attributes = clean(variable._attributes)
            entry = {"dimensions": variable.dimensions, "shape": variable.shape,
                     "dtype": str(variable.data.dtype), "attributes": attributes}
            if lat_name in variable.dimensions and lon_name in variable.dimensions:
                indices = tuple(slice(int(lat_ids[0]), int(lat_ids[-1]) + 1) if dim == lat_name else
                                slice(int(lon_ids[0]), int(lon_ids[-1]) + 1) if dim == lon_name else
                                slice(None) for dim in variable.dimensions)
                raw = np.array(variable[indices], dtype=float, copy=True)
                valid = np.isfinite(raw)
                for attr in ("_FillValue", "missing_value"):
                    missing = variable._attributes.get(attr)
                    if missing is not None:
                        for marker in np.atleast_1d(missing):
                            valid &= raw != float(marker)
                values = raw * float(variable._attributes.get("scale_factor", 1)) + float(variable._attributes.get("add_offset", 0))
                valid &= np.isfinite(values)
                selection = values[valid]
                entry["bbox_diagnostic"] = {
                    "shape": values.shape, "valid_count": int(valid.sum()), "total_count": int(valid.size),
                    "minimum": float(selection.min()) if selection.size else None,
                    "maximum": float(selection.max()) if selection.size else None,
                    "mean_unweighted_not_park_average": float(selection.mean()) if selection.size else None}
                if variable.dimensions == ("time", lat_name, lon_name):
                    month_means = [float(a[m].mean()) if m.any() else None for a, m in zip(values, valid)]
                    entry["bbox_diagnostic"]["monthly_means_unweighted_not_park_average"] = month_means
                    entry["bbox_values"] = clean(np.where(valid, values, np.nan))
            elif variable.data.size <= 100:
                entry["values"] = clean(np.array(variable[:], copy=True))
            variables[name] = entry
        variable = None
        report["variables"] = variables
    with SOURCE.open("rb") as f:
        report["source_sha256"] = hashlib.file_digest(f, "sha256").hexdigest()
    (OUT / "gpcc_1971_1975_inspection.json").write_text(
        json.dumps(clean(report), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    # Only this known temporary file is removed; never remove the user's source.
    assert NC.resolve().is_relative_to((ROOT / "tmp/rainfall").resolve())
    NC.unlink()
    compact = {"dimensions": report["dimensions"], "title": report["global_attributes"].get("title"),
               "coordinates": report["coordinates"],
               "time_count": report["time"]["count"],
               "dates_first_last": [report["time"]["decoded_dates"][0],
                                    report["time"]["decoded_dates"][-1]] if report["time"]["decoded_dates"] else None}
    compact["variables"] = {name: {"shape": item["shape"], "attributes": item["attributes"],
                                   "bbox_diagnostic": {k: v for k, v in item.get("bbox_diagnostic", {}).items()
                                                      if k != "monthly_means_unweighted_not_park_average"}}
                            for name, item in variables.items()}
    print(json.dumps(clean(compact), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
