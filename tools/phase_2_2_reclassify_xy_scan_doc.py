from pathlib import Path

p = Path("docs/PHASE_2_3A_XY_SCAN_MEASUREMENT_MODEL.md")
text = p.read_text(encoding="utf-8")

text = text.replace(
    "# Phase 2.2B - SPM Scan Method Model",
    "# Phase 2.3A - XY Scan Measurement Model"
)

text = text.replace(
    "Phase 2.2",
    "Phase 2.3"
)

note = """
\n## Reclassification Note

This document was created during early Phase 2.2 work, but it belongs to
Phase 2.3 because it describes XY raster scan measurement. Phase 2.2 is now
reserved for Z-scanner settings and live Z feedback only.
"""

if "## Reclassification Note" not in text:
    text += note

p.write_text(text, encoding="utf-8")
print("reclassified XY scan model as Phase 2.3A")
