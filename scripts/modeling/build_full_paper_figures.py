"""English paper figures from saved, verified model outputs only.

Owns output/full_paper/figures; does not run models or alter chapter files.
PNG, SVG and TikZ share the same centimetre-scale drawing primitives.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
from matplotlib import colors, pyplot as plt
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform, unary_union

import build_question2_paper_figures as drawing
from build_question2 import FWD, load_geometry, polygons

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/full_paper/figures"
OUT.mkdir(parents=True, exist_ok=True)
drawing.OUT = OUT
plt.rcParams.update({"font.family": "Times New Roman", "svg.fonttype": "path"})
BLUE, GOLD, RED = drawing.BLUE, drawing.GOLD, drawing.RED
INK, GREY, PALE = drawing.INK, drawing.GREY, drawing.PALE
TEAL = "#41988c"
W = 16.8
PHYSICAL_WIDTH = 16.8
FIGURES: list[dict] = []


def read(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class Canvas(drawing.Canvas):
    def __init__(self, w, h):
        # Reposition geometry at the selected paper figure width.
        # Font sizes remain 12pt; TikZ is never wrapped in a resize command.
        self.layout_scale = PHYSICAL_WIDTH / w
        self.vertical_offset = (h - h * self.layout_scale) / 2
        super().__init__(PHYSICAL_WIDTH, h)

    def position(self, x, y):
        return x * self.layout_scale, y * self.layout_scale + self.vertical_offset

    def coordinates(self, xy):
        points = np.asarray(xy, dtype=float) * self.layout_scale
        points[:, 1] += self.vertical_offset
        return points

    def text(self, x, y, s, size=12, c=INK, ha="center", va="center", bold=False):
        assert size >= 12, f"Small figure label: {s}"
        assert not re.search(r"[\u4e00-\u9fff]", s), f"Non-English figure label: {s}"
        x, y = self.position(x, y)
        super().text(x, y, s, size, c, ha, va, bold)

    def rect(self, x, y, w, h, fill=PALE, edge=None, lw=.6):
        x, y = self.position(x, y)
        super().rect(x, y, w * self.layout_scale, h * self.layout_scale, fill, edge, lw)

    def line(self, xy, c=INK, lw=.8, dashed=False, arrow=False):
        super().line(self.coordinates(xy), c, lw, dashed, arrow)

    def circle(self, x, y, r, fill=BLUE, edge=None, lw=.5):
        x, y = self.position(x, y)
        super().circle(x, y, r * self.layout_scale, fill, edge, lw)

    def poly(self, rings, fill, edge="white", lw=.45):
        super().poly([self.coordinates(ring) for ring in rings], fill, edge, lw)

    def save(self, name):
        super().save(name)
        # Verify text geometry at the export size; retain diagnostics for review.
        fig, ax = plt.subplots(figsize=(self.w / 2.54, self.h / 2.54), dpi=240)
        fig.subplots_adjust(0, 0, 1, 1)
        ax.set_xlim(0, self.w)
        ax.set_ylim(0, self.h)
        ax.set_aspect("equal")
        texts = []
        for item in self.items:
            if item[0] != "text":
                continue
            _, x, y, value, fs, color, ha, va, bold = item
            artist = ax.text(x, y, value, fontsize=fs, color=color, ha=ha, va=va,
                             weight="bold" if bold else "normal")
            texts.append((value, artist))
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        frame = fig.bbox
        boxes = [(value, artist.get_window_extent(renderer)) for value, artist in texts]
        outside = [value for value, box in boxes
                   if box.x0 < frame.x0 - 1 or box.x1 > frame.x1 + 1
                   or box.y0 < frame.y0 - 1 or box.y1 > frame.y1 + 1]
        overlaps = []
        for i, (value, box) in enumerate(boxes):
            for other, obox in boxes[i + 1:]:
                if box.overlaps(obox):
                    overlaps.append([value, other])
        plt.close(fig)
        FIGURES.append({"name": name, "width_cm": self.w, "height_cm": self.h,
                        "minimum_font_pt": 12, "outside_labels": outside,
                        "overlapping_labels": overlaps,
                        "primitive_count": len(self.items)})
        assert not outside, f"Labels outside canvas: {name}: {outside}"


def legend(c, entries, x, y, spacing):
    for i, (label, color) in enumerate(entries):
        xx = x + i * spacing
        c.rect(xx, y - .08, .22, .16, color)
        c.text(xx + .34, y, label, ha="left")


def pipeline(q2, q3):
    c = Canvas(W, 4.6)
    boxes = [(.2, 2.8, 4.8, 1.15, BLUE, "Priorities", "Animals + habitat"),
             (5.9, 2.8, 4.8, 1.15, BLUE, "Routes + response", "Travel time"),
             (11.6, 2.8, 5.0, 1.15, BLUE, "Deployment", "People + drones")]
    for x, y, width, height, color, title, detail in boxes:
        c.rect(x, y, width, height, color)
        c.text(x + width / 2, y + .78, title, c="white", bold=True)
        c.text(x + width / 2, y + .32, detail, c="white")
    for a, b in [(5.05, 5.8), (10.75, 11.5)]:
        c.line([(a, 3.37), (b, 3.37)], GREY, 1.2, arrow=True)
    c.rect(.2, .75, 4.8, 1.0, PALE)
    c.text(2.6, 1.46, "Seasonal tasks", bold=True)
    c.text(2.6, .94, "Fire + water tasks")
    c.rect(5.9, .75, 4.8, 1.0, "#f6e7cf")
    c.text(8.3, 1.46, "Inspection target", bold=True)
    c.text(8.3, .94, f"{q3['target_score']:.2f}%")
    c.rect(11.6, .75, 5.0, 1.0, PALE)
    c.text(14.1, 1.46, "Monthly staff", bold=True)
    hours = q2["assumptions"]["effective_hours_month"]
    c.text(14.1, .94, f"Minimum hours / {hours:g}")
    c.line([(5.05, 1.25), (5.8, 1.25)], GREY, 1.2, arrow=True)
    c.line([(10.75, 1.25), (11.5, 1.25)], GOLD, 1.2, arrow=True)
    c.line([(14.1, 2.75), (14.1, 1.8)], GREY, 1.2, arrow=True)
    c.text(W / 2, .22, "Checks receive service credit only where a ground team can respond.", c=GREY)
    c.save("fig1_framework_pipeline")


def etosha_maps(data, report):
    c = Canvas(W, 6.2)
    geoms = load_geometry()
    rows = {row["region_id"]: row for row in report["regions"]}
    xmin = min(g.bounds[0] for _, g in geoms)
    ymin = min(g.bounds[1] for _, g in geoms)
    xmax = max(g.bounds[2] for _, g in geoms)
    ymax = max(g.bounds[3] for _, g in geoms)
    scale = min(7.5 / (xmax - xmin), 4.1 / (ymax - ymin))
    cmap = plt.get_cmap("Blues")
    roads = read("data/roads/processed/park_edges.geojson")["features"]
    maximum_weight = max(row["demand_weight"] for row in rows.values())
    for panel, field, title, maximum in [
        (0, "demand_weight", "(a) Regional demand weight", maximum_weight),
        (1, "service_completion_fraction", "(b) Area-weighted service", 1.0),
    ]:
        x0 = .35 + 8.4 * panel
        ox = x0 + (7.5 - (xmax - xmin) * scale) / 2
        oy = 1.45 + (4.1 - (ymax - ymin) * scale) / 2
        def xy(coords):
            return np.asarray([(ox + (x - xmin) * scale, oy + (y - ymin) * scale)
                               for x, y in coords])
        c.text(x0 + 3.75, 5.85, title, bold=True)
        for region, geometry in geoms:
            fill = colors.to_hex(cmap(.08 + .85 * rows[region][field] / maximum))
            for polygon in polygons(geometry.simplify(600, preserve_topology=True)):
                if polygon.area < 200_000:
                    continue
                rings = [xy(polygon.exterior.coords)] + [xy(ring.coords) for ring in polygon.interiors]
                c.poly(rings, fill, "white", .35)
        if panel == 0:
            for feature in roads:
                geometry = transform(FWD, shape(feature["geometry"])).simplify(350)
                if geometry.geom_type == "LineString":
                    c.line(xy(geometry.coords), "#7d8b95", .22)
        else:
            for target in data["targets"]:
                if not target["response_eligible"]:
                    x, y = xy([FWD(target["lon"], target["lat"])])[0]
                    c.circle(x, y, .018, RED)
        for base in data["bases"]:
            x, y = xy([FWD(base["lon"], base["lat"])])[0]
            c.star(x, y, .12, GOLD)
        for i in range(8):
            c.rect(x0 + 3.2 + i * .37, 1.02, .37, .18, colors.to_hex(cmap(.08 + .85 * i / 7)))
        c.text(x0 + 3.2, .70, "0", ha="left")
        c.text(x0 + 6.16, .70, f"{100 * maximum:.1f}%", ha="right")
        c.line([(x0 + .25, 1.05), (x0 + .25 + 50_000 * scale, 1.05)], INK, 1.5)
        c.text(x0 + .25 + 25_000 * scale, .7, "50 km")
        c.line([(x0 + .3, 4.45), (x0 + .3, 4.80)], INK, 1, arrow=True)
        c.text(x0 + .3, 5.03, "N")
    c.star(.55, .24, .105, GOLD)
    c.text(.78, .24, "Response-post candidates", ha="left")
    c.circle(7.0, .24, .045, RED)
    c.text(7.22, .24, "Outside the two-hour ground-response limit", ha="left", c=GREY)
    c.save("fig2_etosha_demand_response")


def route_costs(data):
    target = next(t for t in data["targets"] if t["target_id"] == "ENP1_0000")
    config = data["config"]
    n = config["team_size"]
    nu = config["drone_team_size"]
    walk = 2 * target["offroad_km"] / config["walking_speed_kmh"]
    observation, preparation = config["observation_hours"], config["preparation_hours"]
    flight = target["flight_hours_per_check"]
    road = target["ground_hours_per_check"] / n - walk - observation - preparation
    ground = [n * road, n * walk, n * observation, n * preparation]
    drone = [nu * road, 0.0, nu * flight, nu * preparation]
    assert abs(sum(ground) - target["ground_hours_per_check"]) < 1e-10
    assert abs(sum(drone) - target["operator_hours_per_check"]) < 1e-10
    c = Canvas(W, 5.6)
    c.text(W / 2, 5.2, f"{target['target_id']}: personnel time for one check", bold=True)
    left, width = 3.2, 11.8
    maximum = math.ceil(max(sum(ground), sum(drone)) * 2) / 2 + .5
    palette = [BLUE, GOLD, TEAL, GREY]
    for value in [0, 2, 4]:
        x = left + width * value / maximum
        c.line([(x, 2.45), (x, 4.7)], "#e0e6ea", .4)
        c.text(x, 2.2, str(value))
    for y, label, values in [(4.15, "Ground crew", ground), (3.1, "Drone crew", drone)]:
        c.text(left - .2, y, label, ha="right")
        start = left
        for value, color in zip(values, palette):
            w = width * value / maximum
            if w:
                c.rect(start, y - .22, w, .44, color)
            start += w
        c.text(start + .18, y, f"{sum(values):.3f}", ha="left", bold=True)
    legend(c, [("Road travel", BLUE), ("Off-road walk", GOLD),
               ("Observe / fly", TEAL), ("Preparation", GREY)], .4, 1.53, 4.1)
    c.text(W / 2, .95, f"Two-person teams; drone flight adds {flight:.3f} flight-hours per check.")
    c.text(W / 2, .35, "Person-hours and flight-hours use separate budgets.", c=GREY)
    c.save("fig3_route_costs")
    return {"target_id": target["target_id"], "ground_person_hours": sum(ground),
            "drone_operator_person_hours": sum(drone), "flight_hours": flight,
            "ground_components": ground, "drone_components": drone}


def monthly_workload(result, data):
    rows = result["monthly"]
    c = Canvas(W, 7.0)
    c.text(W / 2, 6.68, f"Monthly work at {result['target_score']:.2f}% inspection completion", bold=True)
    legend(c, [("Response", GREY), ("Monitoring", BLUE),
               ("Fire checks", GOLD), ("Water points", TEAL)], 1.55, 6.1, 3.8)
    left, right, bottom, height = 1.8, 16.4, 1.75, 3.6
    maximum = math.ceil(max(r["required_person_hours"] for r in rows) / 1000) * 1000
    c.text(left, 5.57, "Person-hours / month", ha="left")
    for value in range(0, maximum + 1, 2000):
        y = bottom + height * value / maximum
        c.line([(left, y), (right, y)], "#e0e6ea", .45)
        c.text(left - .18, y, str(value), ha="right", c=GREY)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i, row in enumerate(rows):
        x = left + (right - left) * (i + .5) / len(rows)
        start = bottom
        for key, color in zip(["response_hours", "base_monitoring_person_hours",
                               "extra_fire_person_hours", "water_hours"], [GREY, BLUE, GOLD, TEAL]):
            h = height * row[key] / maximum
            c.rect(x - .38, start, .76, h, color)
            start += h
        c.text(x, start + .2, f"{row['required_person_hours']:.0f}")
        c.text(x, 1.32, months[row["month"] - 1])
        c.text(x, .79, str(row["required_staff"]), c=BLUE, bold=True)
    c.text(.9, .79, "Staff", c=BLUE)
    budget = result["fixed_reference_staff"] * data["config"]["effective_hours_month"]
    c.text(W / 2, .23, f"Annual team: {result['annual_fixed_staff_base_scenario']}; reference: {result['fixed_reference_staff']} staff ({budget:,.0f} h/month, off scale).", c=GREY)
    c.save("fig4_monthly_workload")


def resource_joint(result):
    cases = {(row["staff"], row["drone_budget"]): row for row in result["joint_peak_scenarios"]}
    staff = [45, 55, 57, 62, 67, result["current_reference_staff"]]
    capacities = [0, 80, 160, 200, 240, result["current_drone_budget"]]
    assert all((n, u) in cases for n in staff for u in capacities)
    target = result["target_score"]
    c = Canvas(W, 5.6)
    c.text(W / 2, 5.25, "Mid-level seasonal peak: joint personnel and flight capacity", bold=True)
    c.text(.6, 4.65, "Staff", ha="left")
    left, cell_width, top, cell_height = 2.1, 2.30, 4.18, .57
    for column, capacity in enumerate(capacities):
        c.text(left + (column + .5) * cell_width, 4.65, f"{capacity:g}")
    cmap = plt.get_cmap("Blues")
    for rownum, n in enumerate(staff):
        y = top - rownum * cell_height
        c.text(left - .25, y, str(n), ha="right", bold=n == result["current_reference_staff"])
        for column, u in enumerate(capacities):
            solution = cases[n, u]
            value = solution["score"] if solution["success"] else None
            ratio = value / target if value is not None else 0
            fill = colors.to_hex(cmap(.08 + .85 * ratio)) if value is not None else "#ececec"
            x = left + column * cell_width
            c.rect(x, y - .25, cell_width - .08, .50, fill)
            c.text(x + (cell_width - .08) / 2, y,
                   f"{value:.1f}%" if value is not None else "Infeasible",
                   c="white" if ratio > .68 else INK)
    c.text(W / 2, .81, "Columns: flight-hours/month; cells: effective inspection completion (%).")
    c.text(W / 2, .26, f"Target {target:.2f}%; {result['current_reference_staff']} staff and {result['current_drone_budget']:g} flight-hours are the reference.", c=GREY)
    c.save("fig5_resource_joint")
    return {"staff_rows": staff, "flight_capacity_columns": capacities,
            "scores": [[cases[n, u]["score"] for u in capacities] for n in staff]}


def parts(geometry):
    return list(geometry.geoms) if hasattr(geometry, "geoms") else [geometry]


def transfer_maps(result):
    c = Canvas(W, 5.2)
    source = ROOT / "data/question6/processed"
    for panel, park in enumerate(["chitwan", "yellowstone"]):
        data = result["parks"][park]
        project = Transformer.from_crs(4326, data["epsg"], always_xy=True).transform
        boundary = transform(project, shape(read(f"data/question6/processed/{park}_boundary.geojson")["features"][0]["geometry"]))
        xmin, ymin, xmax, ymax = boundary.bounds
        scale = min(7.3 / (xmax - xmin), 3.25 / (ymax - ymin))
        x0 = .45 + 8.4 * panel + (7.3 - (xmax - xmin) * scale) / 2
        y0 = 1.12 + (3.25 - (ymax - ymin) * scale) / 2
        def xy(point):
            return x0 + (point[0] - xmin) * scale, y0 + (point[1] - ymin) * scale
        title = "Chitwan (boundary unresolved)" if park == "chitwan" else "Yellowstone (NPS boundary)"
        c.text(4.2 + 8.4 * panel, 4.85, title, bold=True)
        for polygon in parts(boundary.simplify(100, preserve_topology=True)):
            if polygon.geom_type != "Polygon":
                continue
            rings = [[xy(z) for z in polygon.exterior.coords]]
            rings += [[xy(z) for z in ring.coords] for ring in polygon.interiors]
            c.poly(rings, PALE, GREY, .6)
        roads = []
        for feature in read(f"data/question6/processed/{park}_roads.geojson")["features"]:
            prop = feature["properties"]
            if park == "yellowstone" and prop.get("RDCLASS") == "Private":
                continue
            if park == "chitwan" and (prop.get("highway") in ["path", "footway", "steps", "cycleway", "construction"]
                                      or prop.get("access") in ["no", "private"]):
                continue
            geometry = transform(project, shape(feature["geometry"])).intersection(boundary)
            if geometry.length > 800:
                roads.append(geometry)
        merged = unary_union(roads).simplify(160)
        for line in parts(merged):
            if line.geom_type == "LineString":
                c.line([xy(z) for z in line.coords], BLUE, .5)
        for i, base in enumerate(data["bases"]):
            x, y = xy(base["xy"])
            color = GOLD if i < 2 else RED
            c.star(x, y, .125, color)
            name = base["name"].replace(" Ranger Station", "")
            if name == "South Entrance":
                name = "South"
            if park == "chitwan" and name == "Kasara":
                c.text(x, y - .43, name)
            else:
                c.text(x + .18, y + .26, name, ha="left")
        length = 10 if park == "chitwan" else 20
        xx = .6 + panel * 8.4
        c.line([(xx, 1.10), (xx + length * 1000 * scale, 1.10)], INK, 1.4)
        c.text(xx + length * 500 * scale, .74, f"{length} km")
        xx = .65 + panel * 8.4
        c.line([(xx, 3.98), (xx, 4.33)], INK, 1, arrow=True)
        c.text(xx, 4.56, "N")
    c.line([(3.0, .24), (3.5, .24)], BLUE, 1)
    c.text(3.68, .24, "Roads", ha="left")
    c.star(6.5, .24, .105, GOLD)
    c.text(6.72, .24, "Base candidates", ha="left")
    c.star(11.6, .24, .105, RED)
    c.text(11.82, .24, "Extra candidate", ha="left")
    c.save("fig6_transfer_maps")


def main():
    input_paths = ["output/question2/q2_model_inputs.json", "output/question2/q2_results.json",
                   "output/question3/q3_results.json", "output/question4/q4_results.json",
                   "output/question6/q6_results.json"]
    q2in, q2, q3, q4, q6 = map(read, input_paths)
    assert q2in["human_budget"] == 21240 and q2in["drone_budget"] == 1200
    assert q3["fixed_reference_staff"] == q4["current_reference_staff"] == 177
    assert q4["current_drone_budget"] == 1200
    assert q2["excluded_factors"] == ["water_supply", "precipitation"]
    pipeline(q2, q3)
    etosha_maps(q2in, q2)
    costs = route_costs(q2in)
    monthly_workload(q3, q2in)
    joint = resource_joint(q4)
    transfer_maps(q6)
    geometry_sources = ["data/regions/processed/model_regions.geojson",
                        "data/roads/processed/park_edges.geojson",
                        "data/question6/processed/chitwan_boundary.geojson",
                        "data/question6/processed/chitwan_roads.geojson",
                        "data/question6/processed/yellowstone_boundary.geojson",
                        "data/question6/processed/yellowstone_roads.geojson"]
    drought = next(row for row in q3["sensitivity"]
                   if row["scenario"] == "base" and row["abnormal_drought"])
    manifest = {"figures": FIGURES, "formats": ["png", "svg", "tikz"],
                "physical_width_cm": PHYSICAL_WIDTH, "minimum_font_pt": 12,
                "font_family": "Times New Roman",
                "route_costs": costs, "resource_joint": joint,
                "chitwan_scope": "Published boundary used for illustration; boundary calibration unresolved.",
                "verified_context": {"q2_representative_person_hours": q2["optimum"]["total_person_hours"],
                                     "q3_annual_base_staff": q3["annual_fixed_staff_base_scenario"],
                                     "q3_annual_base_drought_staff": drought["annual_fixed_staff"],
                                     "q3_monthly_chart_scope": "base seasonal scenario, not abnormal drought"},
                "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "visual_review": {"status": "pending"},
                "source_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                                   for path in input_paths + geometry_sources}}
    (OUT / "figure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"figures": [{k: v for k, v in row.items() if k != "overlapping_labels"} for row in FIGURES],
                      "label_overlap_pairs": {row["name"]: row["overlapping_labels"] for row in FIGURES}}, indent=2))


if __name__ == "__main__":
    main()
