from pathlib import Path

p = Path("web/operator_console/index.html")
text = p.read_text(encoding="utf-8")

for line in [
    '  <script src="hardware_dev_log.js"></script>',
    '  <script src="remove_old_floating_log_buttons.js"></script>',
    '<script src="hardware_dev_log.js"></script>',
    '<script src="remove_old_floating_log_buttons.js"></script>',
]:
    text = text.replace(line + "\n", "")
    text = text.replace(line, "")

p.write_text(text, encoding="utf-8")
print("removed legacy floating hardware-log scripts from index")
