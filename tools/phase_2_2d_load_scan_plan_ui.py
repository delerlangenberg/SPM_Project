from pathlib import Path

p = Path("web/operator_console/index.html")
text = p.read_text(encoding="utf-8")
line = '  <script src="scan_plan_ui.js"></script>'

if line not in text:
    if "</body>" not in text:
        raise SystemExit("No </body> found")
    text = text.replace("</body>", line + "\n</body>")

p.write_text(text, encoding="utf-8")
print("loaded scan_plan_ui.js")
