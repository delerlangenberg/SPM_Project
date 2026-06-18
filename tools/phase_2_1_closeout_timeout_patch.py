from pathlib import Path

p = Path("core/web/mk4s_health_motion.py")
text = p.read_text(encoding="utf-8")

text = text.replace(
'''        for cmd in commands:
            log.extend(_send(ser, cmd, timeout=8.0))''',
'''        for cmd in commands:
            cmd_timeout = 90.0 if cmd == "M400" else 20.0
            log.extend(_send(ser, cmd, timeout=cmd_timeout))'''
)

text = text.replace(
'''        for cmd in ["G90", f"G1 Z{SAFE_RETRACT_TARGET_Z:.1f} F300", "M400", "M114", "M119"]:
            log.extend(_send(ser, cmd, timeout=10.0))''',
'''        for cmd in ["G90", f"G1 Z{SAFE_RETRACT_TARGET_Z:.1f} F300", "M400", "M114", "M119"]:
            cmd_timeout = 90.0 if cmd == "M400" else 20.0
            log.extend(_send(ser, cmd, timeout=cmd_timeout))'''
)

text = text.replace(
    "HEALTH MOTION COMPLETE: tiny X/Y/Z hardware jogs completed.",
    "HEALTH MOTION COMPLETE: X/Y/Z hardware health movement completed."
)

p.write_text(text, encoding="utf-8")
print("patched long-move timeout and health wording")
