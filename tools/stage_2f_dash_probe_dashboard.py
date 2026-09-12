import argparse
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.probe_framework import WorkstationProbeContract
from core.probe_framework.simulated_topography import simulated_topography, topography_csv_text


def build_app():
    from dash import Dash, Input, Output, State, dcc, html
    import plotly.graph_objects as go

    contract = WorkstationProbeContract()
    events = ["Dashboard started: simulation only"]
    samples = [{"t": 0, "value": 0.0}]

    app = Dash(__name__)
    app.title = "SPM Probe Dashboard"

    def card(title, body):
        return html.Div(
            [html.H3(title), body],
            style={
                "border": "1px solid #384152",
                "borderRadius": "14px",
                "padding": "18px",
                "background": "#151922",
                "boxShadow": "0 0 0 1px rgba(255,255,255,0.03)",
                "minHeight": "150px",
            },
        )

    def badge(text, ok=True):
        return html.Span(
            text,
            style={
                "display": "inline-block",
                "padding": "4px 9px",
                "borderRadius": "999px",
                "background": "#12381f" if ok else "#4a1515",
                "border": "1px solid #39d353" if ok else "1px solid #ff6b6b",
                "color": "#d7ffe2" if ok else "#ffd7d7",
                "fontWeight": "bold",
                "marginRight": "8px",
            },
        )

    def make_topography_heatmap_figure():
        topo = simulated_topography()
        return {
            "data": [
                {
                    "z": topo,
                    "type": "heatmap",
                    "colorscale": "Viridis",
                    "colorbar": {"title": "Height"},
                }
            ],
            "layout": {
                "template": "plotly_dark",
                "title": "Simulated 2D Topography Heatmap",
                "xaxis": {"title": "X pixel"},
                "yaxis": {"title": "Y line"},
                "height": 520,
            },
        }

    app.layout = html.Div(
        style={
            "fontFamily": "Arial",
            "background": "#0b0f17",
            "color": "#eef2f7",
            "padding": "24px",
            "maxWidth": "1400px",
            "margin": "0 auto",
        },
        children=[
            html.H1("SPM Operator Workstation — Stage 2H"),
            html.Div(
                "Dash SPM operator prototype: simulation active, hardware commands blocked",
                style={"color": "#aab4c0", "marginBottom": "10px"},
            ),
            html.Div(
                "HARDWARE LOCK ACTIVE — no serial, no GPIO, no G-code, no MK4S motion",
                style={
                    "background": "#3a1010",
                    "border": "1px solid #ff5a5a",
                    "borderRadius": "10px",
                    "padding": "12px",
                    "fontWeight": "bold",
                    "marginBottom": "18px",
                },
            ),
            html.Div(
                [
                    html.Button("Refresh", id="btn-refresh", n_clicks=0),
                    html.Button("Sim Connect", id="btn-connect", n_clicks=0),
                    html.Button("Sim Read", id="btn-read", n_clicks=0),
                    html.Button("Sim Disconnect", id="btn-disconnect", n_clicks=0),
                ],
                style={"display": "flex", "gap": "10px", "marginBottom": "18px"},
            ),
            html.Div(
                id="cards",
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(2, minmax(360px, 1fr))",
                    "gap": "14px",
                },
            ),
            html.Div(style={"height": "16px"}),
            dcc.Graph(id="probe-chart"),
            html.H3("Simulated 2D Topography Heatmap"),
            dcc.Graph(id="topography-heatmap", figure=make_topography_heatmap_figure()),
            html.H3("Event Log"),
            html.Pre(id="event-log", style={"background": "#111827", "padding": "12px"}),
        ],
    )

    @app.callback(
        Output("cards", "children"),
        Output("probe-chart", "figure"),
        Output("topography-heatmap", "figure"),
        Output("event-log", "children"),
        Input("btn-refresh", "n_clicks"),
        Input("btn-connect", "n_clicks"),
        Input("btn-read", "n_clicks"),
        Input("btn-disconnect", "n_clicks"),
        prevent_initial_call=False,
    )
    def update(refresh, connect, read, disconnect):
        import dash

        trigger = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        now = time.strftime("%H:%M:%S")

        if trigger == "btn-connect":
            payload = contract.connect()
            events.append(f"{now} simulated connect")
        elif trigger == "btn-read":
            payload = contract.read()
            value = payload["probe_reading"]["value"]
            samples.append({"t": len(samples), "value": value})
            events.append(f"{now} simulated read value={value}")
        elif trigger == "btn-disconnect":
            payload = contract.disconnect()
            events.append(f"{now} simulated disconnect")
        else:
            payload = contract.setup_summary()
            events.append(f"{now} refresh")

        setup = contract.setup_summary()
        active = setup["active_probe"]
        adapter = setup["adapter"]
        hardware = contract.hardware_presence_summary()

        cards = [

            card(
                "Main System",
                html.Ul(
                    [
                        html.Li("System state: SIMULATION"),
                        html.Li("Operator mode: SPM dashboard prototype"),
                        html.Li("MK4S physical presence: detected by port list only"),
                        html.Li("Hardware command bus: disabled"),
                    ]
                ),
            ),
            card(
                "Probe / Z Control",
                html.Ul(
                    [
                        html.Li("Probe type: simulated CR Touch module"),
                        html.Li("Z approach: disabled"),
                        html.Li("Retract: simulated only"),
                        html.Li("Live Z readout: placeholder"),
                    ]
                ),
            ),
            card(
                "XY Scan Setup",
                html.Ul(
                    [
                        html.Li("X range: placeholder"),
                        html.Li("Y range: placeholder"),
                        html.Li("Step size: placeholder"),
                        html.Li("Raster direction: serpentine simulation"),
                        html.Li("Start motion: BLOCKED"),
                    ]
                ),
            ),
            card(
                "Raster Preview",
                html.Ul(
                    [
                        html.Li("Preview mode: simulated grid"),
                        html.Li("Lines: placeholder"),
                        html.Li("Pixels per line: placeholder"),
                        html.Li("Real path execution: blocked"),
                    ]
                ),
            ),
            card(
                "Probe Status",
                html.Ul(
                    [
                        html.Li(f'Active probe: {active["probe_id"]} / {active["kind"]}'),
                        html.Li(f'Connected: {active["connected"]}'),
                        html.Li(f'Deployed: {active["deployed"]}'),
                        html.Li(f'Simulation: {active["simulation"]}'),
                        html.Li(f'Hardware enabled: {active["hardware_enabled"]}'),
                    ]
                ),
            ),
            card(
                "Safety Interlocks",
                html.Ul([html.Li(item) for item in setup["blocked_interfaces"]]),
            ),
            card(
                "USB Probe Adapter",
                html.Ul(
                    [
                        html.Li(f'Port: {adapter["port"]}'),
                        html.Li(f'Connected: {adapter["connected"]}'),
                        html.Li(f'Simulation: {adapter["simulation"]}'),
                    ]
                ),
            ),
            card(
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
            ),
            card(
                "Measurement Workflow",
                html.Ul(
                    [
                        html.Li("1. Main system: simulated dashboard online."),
                        html.Li("2. Probe/Z: simulated CR Touch state available."),
                        html.Li("3. XY scan: blocked until explicit hardware gate."),
                        html.Li("4. Live signal: Plotly simulation only."),
                        html.Li("5. Export: planned next stage."),
                    ]
                ),
            ),
            card(
                "Safety Gate",
                html.Ul(
                    [
                        html.Li("Motion permission: BLOCKED"),
                        html.Li("Serial permission: BLOCKED"),
                        html.Li("G-code permission: BLOCKED"),
                        html.Li("Hardware mode: NOT ENABLED"),
                    ]
                ),
            ),
            card(
                "Simulated Scan Controls",
                html.Ul(
                    [
                        html.Li("Scan area: 10 mm × 10 mm placeholder"),
                        html.Li("Resolution: 32 × 32 placeholder"),
                        html.Li("Raster mode: simulated serpentine"),
                        html.Li("Start scan: blocked until explicit hardware gate"),
                        html.Li("Current action: simulation preview only"),
                    ]
                ),
            ),
            card(
                "Export Placeholder",
                html.Ul(
                    [
                        html.Li("CSV export: planned"),
                        html.Li("PNG plot export: planned"),
                        html.Li("Metadata export: planned"),
                        html.Li("No hardware data recorded in this stage"),
                    ]
                ),
            ),
            card(
                "Simulated Topography Engine",
                html.Ul(
                    [
                        html.Li("Grid: 32 × 32 simulated height map"),
                        html.Li("Surface: hill + wave + slope model"),
                        html.Li("Source: software simulation only"),
                        html.Li("Hardware data: none"),
                    ]
                ),
            ),
            card(
                "CSV Export Model",
                html.Ul(
                    [
                        html.Li(f'Rows generated: {len(topography_csv_text(simulated_topography()).splitlines()) - 1}'),
                        html.Li("Columns: y_index, x_index, height_simulated"),
                        html.Li("Export status: model ready"),
                        html.Li("Real measurement export: blocked"),
                    ]
                ),
            ),
            card(
                "System Mode",
                html.Div(
                    [
                        html.Div([badge("SIMULATION ONLY", ok=True)]),
                        html.Br(),
                        html.Div("SPM PC Mode: hardware may be physically present, but commands are blocked."),
                        html.Br(),
                        html.Div("No serial. No GPIO. No G-code. No MK4S motion."),
                    ]
                ),
            ),
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[s["t"] for s in samples],
            y=[s["value"] for s in samples],
            mode="lines+markers",
            name="simulated probe value",
        ))
        fig.update_layout(
            template="plotly_dark",
            title="Simulated Probe Signal",
            xaxis_title="Sample",
            yaxis_title="Value",
        )
        return cards, fig, "\n".join(events[-20:])

    return app


def self_test() -> int:
    app = build_app()
    assert app.title == "SPM Probe Dashboard"
    contract = WorkstationProbeContract()
    setup = contract.setup_summary()
    assert setup["hardware_enabled"] is False
    assert setup["simulation"] is True
    assert setup["active_probe"]["probe_id"] == "001"
    print("STAGE_2F_DASH_PROBE_DASHBOARD_SELF_TEST_PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8050, type=int)
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    app = build_app()
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
