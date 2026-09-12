from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from core.ai.academic_ai_client import build_ai_recommendation


@dataclass(frozen=True)
class GCodePatternRequest:
    prompt: str = "Create a 3x3 gold-like atomic island field with small hexagonal rings."
    pattern: str = "auto"
    refinement_notes: str = ""
    learning_notes: str = ""
    material: str = "PLA"
    nozzle_diameter_mm: float = 0.40
    nozzle_temperature_c: int = 215
    bed_temperature_c: int = 60
    center_x_mm: float = 125.0
    center_y_mm: float = 105.0
    size_mm: float = 30.0
    thickness_mm: float = 0.20
    travel_z_mm: float = 5.0
    feedrate_mm_min: float = 1200.0
    extrusion_per_mm: float = 0.045
    line_spacing_mm: float = 2.5
    output_format: str = "obj"

    @property
    def layer_z_mm(self) -> float:
        return self.thickness_mm


@dataclass(frozen=True)
class GCodeBuildPlan:
    request: GCodePatternRequest
    resolved_pattern: str
    summary: str
    operator_questions: tuple[str, ...]
    review_steps: tuple[str, ...]


def _bounded(value: float, low: float, high: float, label: str) -> float:
    number = float(value)
    if not low <= number <= high:
        raise ValueError(f"{label} must be between {low} and {high}")
    return number


def validate_gcode_request(request: GCodePatternRequest) -> None:
    _bounded(request.center_x_mm, 0.0, 250.0, "center_x_mm")
    _bounded(request.center_y_mm, 0.0, 210.0, "center_y_mm")
    _bounded(request.size_mm, 1.0, 180.0, "size_mm")
    _bounded(request.thickness_mm, 0.05, 2.0, "thickness_mm")
    _bounded(request.travel_z_mm, 1.0, 50.0, "travel_z_mm")
    _bounded(request.feedrate_mm_min, 60.0, 6000.0, "feedrate_mm_min")
    _bounded(request.extrusion_per_mm, 0.0, 0.25, "extrusion_per_mm")
    _bounded(request.line_spacing_mm, 0.2, 30.0, "line_spacing_mm")
    _bounded(request.nozzle_diameter_mm, 0.10, 1.20, "nozzle_diameter_mm")
    _bounded(float(request.nozzle_temperature_c), 0.0, 320.0, "nozzle_temperature_c")
    _bounded(float(request.bed_temperature_c), 0.0, 140.0, "bed_temperature_c")
    if resolved_pattern(request) not in {"hexagon", "gold_3x3", "bravais_3x3", "micro_lines"}:
        raise ValueError("prompt/pattern must resolve to hexagon, gold_3x3, bravais_3x3, or micro_lines")
    if request.output_format not in {"obj", "stl", "gcode"}:
        raise ValueError("output_format must be obj, stl, or gcode")


def resolved_pattern(request: GCodePatternRequest) -> str:
    if request.pattern != "auto":
        return request.pattern
    prompt = request.prompt.lower()
    if "bravais" in prompt or "lattice" in prompt or "crystal" in prompt:
        return "bravais_3x3"
    if "hex" in prompt or "honeycomb" in prompt:
        return "hexagon"
    if "line" in prompt or "grating" in prompt or "stripe" in prompt:
        return "micro_lines"
    return "gold_3x3"


def build_gcode_plan(request: GCodePatternRequest) -> GCodeBuildPlan:
    validate_gcode_request(request)
    pattern = resolved_pattern(request)
    concept = {
        "gold_3x3": "a 3 x 3 field of small gold-like atomic islands",
        "hexagon": "a clean hexagonal / honeycomb geometry",
        "bravais_3x3": "an oblique Bravais-style lattice concept",
        "micro_lines": "a parallel micro-line / grating concept",
    }[pattern]
    summary = (
        f"AI build plan: {concept}. Size {request.size_mm:.1f} mm, "
        f"thickness/layer Z {request.thickness_mm:.3f} mm, feedrate {request.feedrate_mm_min:.0f} mm/min, "
        f"line spacing {request.line_spacing_mm:.2f} mm where applicable. "
        f"Material {request.material}, nozzle {request.nozzle_diameter_mm:.2f} mm, "
        f"temperatures {request.nozzle_temperature_c} C / bed {request.bed_temperature_c} C. "
        "The output is a review-only model or G-code file and will not be sent to hardware."
    )
    return GCodeBuildPlan(
        request=request,
        resolved_pattern=pattern,
        summary=summary,
        operator_questions=(
            "Is the generated concept the correct physical idea?",
            "Is the size safe for the intended printer bed and sample area?",
            "Is the thickness/layer Z compatible with nozzle, material, and slicer profile?",
            "Should this be viewed in PrusaSlicer before printing?",
        ),
        review_steps=(
            "Generate the final file only after the plan matches the user wish.",
            "Prefer saving OBJ or STL for normal PrusaSlicer import.",
            "Use G-code only as an expert review file through PrusaSlicer's G-code Preview.",
            "Open the saved model in PrusaSlicer, slice/export from there, and inspect the path before printing.",
        ),
    )


def _hexagon_points(cx: float, cy: float, radius: float) -> list[tuple[float, float]]:
    return [
        (cx + radius * math.cos(math.tau * index / 6.0), cy + radius * math.sin(math.tau * index / 6.0))
        for index in range(6)
    ]


def _segment_lines(points: list[tuple[float, float]], close: bool = False) -> list[list[tuple[float, float]]]:
    if close:
        return [points + [points[0]]]
    return [[a, b] for a, b in zip(points, points[1:])]


def pattern_segments(request: GCodePatternRequest) -> list[list[tuple[float, float]]]:
    size = float(request.size_mm)
    cx = float(request.center_x_mm)
    cy = float(request.center_y_mm)
    pattern = resolved_pattern(request)
    if pattern == "hexagon":
        return _segment_lines(_hexagon_points(cx, cy, size / 2.0), close=True)

    if pattern == "gold_3x3":
        spacing = size / 4.0
        radius = max(0.8, spacing * 0.20)
        segments: list[list[tuple[float, float]]] = []
        for row in range(3):
            for col in range(3):
                x = cx + (col - 1) * spacing
                y = cy + (row - 1) * spacing
                segments.append(_hexagon_points(x, y, radius) + [_hexagon_points(x, y, radius)[0]])
        return segments

    if pattern == "micro_lines":
        y0 = cy - size / 2.0
        count = max(2, int(size / max(0.2, request.line_spacing_mm)) + 1)
        segments = []
        for index in range(count):
            y = y0 + index * request.line_spacing_mm
            if y > cy + size / 2.0:
                break
            segments.append([(cx - size / 2.0, y), (cx + size / 2.0, y)])
        return segments

    spacing = size / 4.0
    skew = spacing * 0.42
    nodes = [
        (cx + (col - 1) * spacing + (row - 1) * skew, cy + (row - 1) * spacing)
        for row in range(3)
        for col in range(3)
    ]
    segments = []
    for row in range(3):
        segments.append([nodes[row * 3 + col] for col in range(3)])
    for col in range(3):
        segments.append([nodes[row * 3 + col] for row in range(3)])
    return segments


def generate_gcode(request: GCodePatternRequest) -> str:
    validate_gcode_request(request)
    segments = pattern_segments(request)
    pattern = resolved_pattern(request)
    e_value = 0.0
    lines = [
        "; SPM Prusa Academic AI assisted pattern export",
        "; REVIEW BEFORE PRINTING. Open in PrusaSlicer or another G-code viewer before any print.",
        "; This file is generated only; the operator software does not send it to hardware.",
        f"; prompt: {request.prompt}",
        f"; refinement_notes: {request.refinement_notes or 'none'}",
        f"; resolved_pattern: {pattern}",
        f"; material: {request.material}",
        f"; nozzle_diameter_mm: {request.nozzle_diameter_mm:.2f}",
        f"; nozzle_temperature_c: {request.nozzle_temperature_c}",
        f"; bed_temperature_c: {request.bed_temperature_c}",
        f"; thickness_mm: {request.thickness_mm:.3f}",
        f"; size_mm: {request.size_mm:.3f}",
        f"; feedrate_mm_min: {request.feedrate_mm_min:.0f}",
        "; Add printer-specific start/end G-code, heating, purge, and bed preparation in your normal slicer workflow if needed.",
        "G21 ; millimeters",
        "G90 ; absolute positioning",
        "M83 ; relative extrusion mode",
        f"G1 Z{request.travel_z_mm:.3f} F600",
    ]
    last: tuple[float, float] | None = None
    for segment in segments:
        if not segment:
            continue
        start = segment[0]
        if last != start:
            lines.append(f"G0 X{start[0]:.3f} Y{start[1]:.3f} F3000")
            lines.append(f"G1 Z{request.layer_z_mm:.3f} F300")
        for point in segment[1:]:
            distance = math.hypot(point[0] - start[0], point[1] - start[1])
            e_value = distance * request.extrusion_per_mm
            lines.append(f"G1 X{point[0]:.3f} Y{point[1]:.3f} E{e_value:.5f} F{request.feedrate_mm_min:.0f}")
            start = point
        lines.append(f"G1 Z{request.travel_z_mm:.3f} F600")
        last = segment[-1]
    lines.extend(["M400", "; End generated Academic AI pattern"])
    return "\n".join(lines) + "\n"


def _segment_box_triangles(
    start: tuple[float, float],
    end: tuple[float, float],
    width: float,
    height: float,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return []
    nx = -dy / length * width / 2.0
    ny = dx / length * width / 2.0
    bottom = [
        (x1 + nx, y1 + ny, 0.0),
        (x1 - nx, y1 - ny, 0.0),
        (x2 - nx, y2 - ny, 0.0),
        (x2 + nx, y2 + ny, 0.0),
    ]
    top = [(x, y, height) for x, y, _z in bottom]
    b0, b1, b2, b3 = bottom
    t0, t1, t2, t3 = top
    return [
        (b0, b1, b2),
        (b0, b2, b3),
        (t0, t2, t1),
        (t0, t3, t2),
        (b0, t0, t1),
        (b0, t1, b1),
        (b1, t1, t2),
        (b1, t2, b2),
        (b2, t2, t3),
        (b2, t3, b3),
        (b3, t3, t0),
        (b3, t0, b0),
    ]


def _wants_center_dome(request: GCodePatternRequest) -> bool:
    text = f"{request.prompt} {request.refinement_notes}".lower()
    return any(word in text for word in ("half sphere", "hemisphere", "dome", "sphere", "ball", "half-ball"))


def _hex_frame_triangles(
    cx: float,
    cy: float,
    outer_radius: float,
    inner_radius: float,
    height: float,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    outer_bottom = [(x, y, 0.0) for x, y in _hexagon_points(cx, cy, outer_radius)]
    inner_bottom = [(x, y, 0.0) for x, y in _hexagon_points(cx, cy, inner_radius)]
    outer_top = [(x, y, height) for x, y, _z in outer_bottom]
    inner_top = [(x, y, height) for x, y, _z in inner_bottom]
    triangles = []
    for index in range(6):
        next_index = (index + 1) % 6
        ob0, ob1 = outer_bottom[index], outer_bottom[next_index]
        ib0, ib1 = inner_bottom[index], inner_bottom[next_index]
        ot0, ot1 = outer_top[index], outer_top[next_index]
        it0, it1 = inner_top[index], inner_top[next_index]

        triangles.extend(
            [
                (ot0, ot1, it1),
                (ot0, it1, it0),
                (ob0, ib1, ob1),
                (ob0, ib0, ib1),
                (ob0, ob1, ot1),
                (ob0, ot1, ot0),
                (ib0, it1, ib1),
                (ib0, it0, it1),
            ]
        )
    return triangles


def _cylinder_triangles(
    cx: float,
    cy: float,
    radius: float,
    height: float,
    *,
    segments: int = 36,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    bottom_center = (cx, cy, 0.0)
    top_center = (cx, cy, height)
    bottom = [
        (cx + radius * math.cos(math.tau * index / segments), cy + radius * math.sin(math.tau * index / segments), 0.0)
        for index in range(segments)
    ]
    top = [(x, y, height) for x, y, _z in bottom]
    triangles = []
    for index in range(segments):
        next_index = (index + 1) % segments
        b0, b1 = bottom[index], bottom[next_index]
        t0, t1 = top[index], top[next_index]
        triangles.extend(
            [
                (bottom_center, b1, b0),
                (top_center, t0, t1),
                (b0, b1, t1),
                (b0, t1, t0),
            ]
        )
    return triangles


def _hemisphere_triangles(
    cx: float,
    cy: float,
    base_z: float,
    radius: float,
    *,
    segments: int = 48,
    rings: int = 12,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    top = (cx, cy, base_z + radius)
    ring_points: list[list[tuple[float, float, float]]] = []
    for ring in range(1, rings + 1):
        theta = (math.pi / 2.0) * ring / rings
        ring_radius = radius * math.sin(theta)
        z = base_z + radius * math.cos(theta)
        ring_points.append(
            [
                (
                    cx + ring_radius * math.cos(math.tau * index / segments),
                    cy + ring_radius * math.sin(math.tau * index / segments),
                    z,
                )
                for index in range(segments)
            ]
        )

    triangles = []
    first = ring_points[0]
    for index in range(segments):
        triangles.append((top, first[index], first[(index + 1) % segments]))

    for ring_index in range(len(ring_points) - 1):
        upper = ring_points[ring_index]
        lower = ring_points[ring_index + 1]
        for index in range(segments):
            next_index = (index + 1) % segments
            triangles.extend(
                [
                    (upper[index], lower[index], lower[next_index]),
                    (upper[index], lower[next_index], upper[next_index]),
                ]
            )
    return triangles


def _printable_hexagon_model_triangles(
    request: GCodePatternRequest,
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    cx = float(request.center_x_mm)
    cy = float(request.center_y_mm)
    outer_radius = float(request.size_mm) / 2.0
    frame_width = max(request.nozzle_diameter_mm * 3.0, min(outer_radius * 0.24, max(1.2, request.line_spacing_mm * 0.7)))
    inner_radius = max(outer_radius - frame_width, outer_radius * 0.45)
    base_height = max(float(request.thickness_mm), 0.35)
    triangles = _hex_frame_triangles(cx, cy, outer_radius, inner_radius, base_height)

    if not _wants_center_dome(request):
        return triangles

    dome_radius = max(1.0, min(inner_radius * 0.45, outer_radius * 0.22))
    hub_radius = dome_radius * 1.08
    triangles.extend(_cylinder_triangles(cx, cy, hub_radius, base_height, segments=48))
    triangles.extend(_hemisphere_triangles(cx, cy, base_height, dome_radius, segments=48, rings=14))

    spoke_width = max(request.nozzle_diameter_mm * 2.5, frame_width * 0.45)
    for index in range(6):
        angle = math.tau * index / 6.0
        start = (cx + hub_radius * 0.82 * math.cos(angle), cy + hub_radius * 0.82 * math.sin(angle))
        end = (cx + (inner_radius + frame_width * 0.28) * math.cos(angle), cy + (inner_radius + frame_width * 0.28) * math.sin(angle))
        triangles.extend(_segment_box_triangles(start, end, spoke_width, base_height))
    return triangles


def _model_triangles(request: GCodePatternRequest) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    validate_gcode_request(request)
    if resolved_pattern(request) == "hexagon":
        return _printable_hexagon_model_triangles(request)
    line_width = max(0.40, min(2.0, request.line_spacing_mm * 0.35))
    triangles = []
    for segment in pattern_segments(request):
        for start, end in zip(segment, segment[1:]):
            triangles.extend(_segment_box_triangles(start, end, line_width, request.thickness_mm))
    return triangles


def generate_obj(request: GCodePatternRequest) -> str:
    triangles = _model_triangles(request)
    lines = [
        "# SPM Prusa Academic AI model export",
        "# Import this OBJ in PrusaSlicer, slice it there, then export printer G-code from PrusaSlicer.",
        f"# prompt: {request.prompt}",
        f"# refinement_notes: {request.refinement_notes or 'none'}",
        f"# resolved_pattern: {resolved_pattern(request)}",
        f"# material: {request.material}",
        f"# nozzle_diameter_mm: {request.nozzle_diameter_mm:.2f}",
        f"# printable_joined_hex_frame: {resolved_pattern(request) == 'hexagon'}",
        f"# central_hemisphere: {_wants_center_dome(request)}",
    ]
    vertex_index = 1
    for tri in triangles:
        for x, y, z in tri:
            lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
        lines.append(f"f {vertex_index} {vertex_index + 1} {vertex_index + 2}")
        vertex_index += 3
    return "\n".join(lines) + "\n"


def _normal(triangle: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]) -> tuple[float, float, float]:
    a, b, c = triangle
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / length, ny / length, nz / length


def generate_ascii_stl(request: GCodePatternRequest) -> str:
    triangles = _model_triangles(request)
    lines = ["solid spm_academic_ai_model"]
    for tri in triangles:
        nx, ny, nz = _normal(tri)
        lines.append(f"  facet normal {nx:.6f} {ny:.6f} {nz:.6f}")
        lines.append("    outer loop")
        for x, y, z in tri:
            lines.append(f"      vertex {x:.6f} {y:.6f} {z:.6f}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid spm_academic_ai_model")
    return "\n".join(lines) + "\n"


def generate_export_file(request: GCodePatternRequest) -> tuple[str, str, str]:
    if request.output_format == "stl":
        return generate_ascii_stl(request), "stl", "Import STL/3MF/STEP/OBJ/AMF in PrusaSlicer, then slice/export."
    if request.output_format == "gcode":
        return generate_gcode(request), "gcode", "Open through PrusaSlicer's G-code Preview, not normal Import."
    return generate_obj(request), "obj", "Import STL/3MF/STEP/OBJ/AMF in PrusaSlicer, then slice/export."


def build_academic_gcode_job(request: GCodePatternRequest) -> dict[str, Any]:
    plan = build_gcode_plan(request)
    file_text, extension, viewing_instruction = generate_export_file(request)
    advice = build_ai_recommendation(
        task="generate safe review-only print model or G-code pattern",
        context={
            "prompt": request.prompt,
            "refinement_notes": request.refinement_notes,
            "learning_notes": request.learning_notes,
            "resolved_pattern": resolved_pattern(request),
            "material": request.material,
            "nozzle_diameter_mm": request.nozzle_diameter_mm,
            "nozzle_temperature_c": request.nozzle_temperature_c,
            "bed_temperature_c": request.bed_temperature_c,
            "center_x_mm": request.center_x_mm,
            "center_y_mm": request.center_y_mm,
            "size_mm": request.size_mm,
            "thickness_mm": request.thickness_mm,
            "feedrate_mm_min": request.feedrate_mm_min,
            "line_spacing_mm": request.line_spacing_mm,
            "output_format": request.output_format,
            "execution_allowed": False,
            "generated_by_local_safety_template": True,
        },
    )
    return {
        "ok": True,
        "file_text": file_text,
        "file_extension": extension,
        "viewing_instruction": viewing_instruction,
        "gcode": file_text if extension == "gcode" else "",
        "line_count": len(file_text.splitlines()),
        "plan_summary": plan.summary,
        "resolved_pattern": plan.resolved_pattern,
        "ai_advice": advice,
        "safety": {
            "gcode_sent": False,
            "execution_allowed": False,
            "review_required": True,
        },
    }
