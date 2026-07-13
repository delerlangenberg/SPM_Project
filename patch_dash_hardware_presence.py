from pathlib import Path

path = Path("tools/stage_2f_dash_probe_dashboard.py")
text = path.read_text(encoding="utf-8")

if "from core.probe_framework.hardware_presence import serial_port_snapshot" not in text:
    text = text.replace(
        "from core.probe_framework import WorkstationProbeContract\n",
        "from core.probe_framework import WorkstationProbeContract\n"
        "from core.probe_framework.hardware_presence import serial_port_snapshot\n",
    )

if 'hardware = serial_port_snapshot()' not in text:
    text = text.replace(
        '        adapter = setup["adapter"]\n',
        '        adapter = setup["adapter"]\n'
        '        hardware = serial_port_snapshot()\n',
    )

old = '''            card(
                "SPM PC Readiness",
                html.Ul(
                    [
                        html.Li("Dashboard may run beside the real MK4S."),
                        html.Li("Real MK4S commands remain blocked."),
                        html.Li("CR Touch direct connection remains blocked."),
                        html.Li("Use this stage for visual/operator testing only."),
                    ]
                ),
            ),'''

new = '''            card(
                "Hardware Presence",
                html.Ul(
                    [
                        html.Li(f'Port scan available: {hardware["available"]}'),
                        html.Li(f'Ports visible: {len(hardware["ports"])}'),
                        html.Li(f'MK4S candidates: {len(hardware["mk4s_candidates"])}'),
                        html.Li(f'Hardware opened: {hardware["hardware_opened"]}'),
                    ]
                    + [
                        html.Li(f'Candidate: {p["device"]} | {p["description"]}')
                        for p in hardware["mk4s_candidates"]
                    ]
                ),
            ),
            card(
                "SPM PC Readiness",
                html.Ul(
                    [
                        html.Li("Dashboard may run beside the real MK4S."),
                        html.Li("Real MK4S commands remain blocked."),
                        html.Li("CR Touch direct connection remains blocked."),
                        html.Li("Use this stage for visual/operator testing only."),
                    ]
                ),
            ),'''

text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
print("DASH_HARDWARE_PRESENCE_PATCHED")
