from core.ai.academic_gcode_generator import (
    GCodePatternRequest,
    build_academic_gcode_job,
    build_gcode_plan,
    generate_ascii_stl,
    generate_export_file,
    generate_gcode,
    generate_obj,
    pattern_segments,
)


def test_academic_gcode_generator_exports_review_only_gold_3x3():
    request = GCodePatternRequest(prompt="gold surface 3x3", size_mm=30.0)
    gcode = generate_gcode(request)

    assert "; SPM Prusa Academic AI assisted pattern export" in gcode
    assert "REVIEW BEFORE PRINTING" in gcode
    assert "Open in PrusaSlicer" in gcode
    assert "resolved_pattern: gold_3x3" in gcode
    assert "thickness_mm" in gcode
    assert "G21 ; millimeters" in gcode
    assert "M83 ; relative extrusion mode" in gcode
    assert "G1 X" in gcode
    assert "E" in gcode
    assert len(pattern_segments(request)) == 9


def test_academic_gcode_job_never_executes_motion(monkeypatch):
    monkeypatch.setenv("ACADEMIC_AI_DISABLE_LOCAL_FILE", "1")
    monkeypatch.delenv("ACADEMIC_AI_CLIENT_ID", raising=False)
    monkeypatch.delenv("ACADEMIC_AI_CLIENT_SECRET", raising=False)
    payload = build_academic_gcode_job(GCodePatternRequest(prompt="hexagon"))

    assert payload["ok"] is True
    assert payload["safety"]["gcode_sent"] is False
    assert payload["safety"]["execution_allowed"] is False
    assert payload["safety"]["review_required"] is True
    assert payload["file_extension"] == "obj"
    assert "file_text" in payload


def test_academic_gcode_generator_rejects_oversize_pattern():
    try:
        generate_gcode(GCodePatternRequest(size_mm=300.0))
    except ValueError as exc:
        assert "size_mm" in str(exc)
    else:
        raise AssertionError("oversize pattern should be rejected")


def test_academic_gcode_prompt_can_resolve_micro_lines():
    request = GCodePatternRequest(prompt="make a fine grating with parallel lines", line_spacing_mm=2.0)
    gcode = generate_gcode(request)

    assert "resolved_pattern: micro_lines" in gcode


def test_academic_gcode_plan_precedes_generation():
    plan = build_gcode_plan(GCodePatternRequest(prompt="make a honeycomb surface"))

    assert plan.resolved_pattern == "hexagon"
    assert "AI build plan" in plan.summary
    assert "Prefer saving OBJ or STL for normal PrusaSlicer import." in plan.review_steps


def test_academic_export_generates_importable_obj_and_stl():
    request = GCodePatternRequest(prompt="make a honeycomb surface", output_format="obj")
    obj = generate_obj(request)
    assert obj.startswith("# SPM Prusa Academic AI model export")
    assert "\nv " in obj
    assert "\nf " in obj

    stl = generate_ascii_stl(GCodePatternRequest(prompt="make a honeycomb surface", output_format="stl"))
    assert stl.startswith("solid spm_academic_ai_model")
    assert "facet normal" in stl


def test_academic_hexagon_with_half_sphere_generates_printable_connected_model():
    request = GCodePatternRequest(
        prompt="create a hexagon with a half sphere in the center and all corners well connected for good printing",
        size_mm=36.0,
        thickness_mm=0.4,
        nozzle_diameter_mm=0.4,
        output_format="obj",
    )
    obj = generate_obj(request)

    vertex_count = obj.count("\nv ")
    face_count = obj.count("\nf ")

    assert "# resolved_pattern: hexagon" in obj
    assert "# printable_joined_hex_frame: True" in obj
    assert "# central_hemisphere: True" in obj
    assert vertex_count > 1200
    assert face_count > 400
    assert " 0.40000" in obj


def test_academic_hexagon_stl_with_half_sphere_is_rich_mesh():
    stl = generate_ascii_stl(
        GCodePatternRequest(
            prompt="hexagon frame with dome in the middle",
            size_mm=30.0,
            thickness_mm=0.35,
            output_format="stl",
        )
    )

    assert stl.startswith("solid spm_academic_ai_model")
    assert stl.count("facet normal") > 400


def test_academic_export_file_prefers_model_formats():
    text, extension, instruction = generate_export_file(GCodePatternRequest(output_format="stl"))

    assert extension == "stl"
    assert text.startswith("solid")
    assert "Import STL/3MF/STEP/OBJ/AMF" in instruction


def test_academic_print_parameters_are_carried_into_plan_and_exports():
    request = GCodePatternRequest(
        prompt="make a clean hexagon",
        refinement_notes="make it thin and easy to slice",
        material="PETG",
        nozzle_diameter_mm=0.60,
        nozzle_temperature_c=240,
        bed_temperature_c=85,
    )

    plan = build_gcode_plan(request)
    obj = generate_obj(request)
    gcode = generate_gcode(request)

    assert "Material PETG" in plan.summary
    assert "nozzle 0.60 mm" in plan.summary
    assert "# material: PETG" in obj
    assert "# nozzle_diameter_mm: 0.60" in obj
    assert "; material: PETG" in gcode
    assert "; nozzle_temperature_c: 240" in gcode


def test_academic_job_includes_learning_and_refinement_context(monkeypatch):
    captured = {}

    def fake_ai(task, context):
        captured["task"] = task
        captured["context"] = context
        return {"recommendation": ["Keep the geometry simple."]}

    monkeypatch.setattr("core.ai.academic_gcode_generator.build_ai_recommendation", fake_ai)
    build_academic_gcode_job(
        GCodePatternRequest(
            prompt="make a test coupon",
            refinement_notes="avoid fragile walls",
            learning_notes="User prefers STL and slow PETG prints.",
        )
    )

    assert "print model" in captured["task"]
    assert captured["context"]["refinement_notes"] == "avoid fragile walls"
    assert captured["context"]["learning_notes"] == "User prefers STL and slow PETG prints."
