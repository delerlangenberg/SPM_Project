from pathlib import Path

p = Path(".gitignore")
text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

rules = [
    "",
    "# Generated hardware session logs",
    "docs/hardware_logs/",
    "/docs/hardware_logs/",
]

for rule in rules:
    if rule and rule not in text:
        text = text.rstrip() + "\n" + rule + "\n"

p.write_text(text, encoding="utf-8")
print("gitignore hardware log rules written")
