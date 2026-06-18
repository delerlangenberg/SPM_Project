from pathlib import Path

p = Path("web/operator_console/index.html")
text = p.read_text(encoding="utf-8")

for line in [
    '  <script src="scan_plan_ui.js"></script>',
    '  <script src="scan_preview_ui.js"></script>',
    '<script src="scan_plan_ui.js"></script>',
    '<script src="scan_preview_ui.js"></script>',
]:
    text = text.replace(line + "\n", "")
    text = text.replace(line, "")

p.write_text(text, encoding="utf-8")
print("removed XY scan planner panels from active Phase 2.2 UI")
