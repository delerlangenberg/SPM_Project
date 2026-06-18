from pathlib import Path

p = Path("core/web/operator_console_server.py")
text = p.read_text(encoding="utf-8")

if "/api/scan/plan" in text:
    print("scan plan route already present")
    raise SystemExit(0)

needle = "parsed = urlparse(self.path)"
if needle not in text:
    raise SystemExit("Could not find parsed = urlparse(self.path)")

route = '''
        if parsed.path == "/api/scan/plan":
            from core.web.spm_scan_plan_api import build_scan_plan_from_query
            self._send_json(build_scan_plan_from_query(parsed.query))
            return

'''

insert_at = text.find(needle)
line_end = text.find("\n", insert_at)
text = text[:line_end+1] + route + text[line_end+1:]

p.write_text(text, encoding="utf-8")
print("patched /api/scan/plan route")
