from pathlib import Path

p = Path("web/operator_console/index.html")
text = p.read_text(encoding="utf-8")

line = '<script src="remove_old_floating_log_buttons.js"></script>'

if line not in text:
    if "</body>" in text:
        text = text.replace("</body>", "  " + line + "\n</body>")
    else:
        text += "\n" + line + "\n"

p.write_text(text, encoding="utf-8")
print("loaded remove_old_floating_log_buttons.js")
