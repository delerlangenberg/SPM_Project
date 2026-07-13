from typing import Dict, List


def serial_port_snapshot() -> Dict[str, object]:
    try:
        from serial.tools import list_ports
    except Exception as exc:
        return {
            "available": False,
            "error": str(exc),
            "ports": [],
            "mk4s_candidates": [],
            "hardware_opened": False,
        }

    ports: List[dict] = []
    candidates: List[dict] = []

    for p in list_ports.comports():
        item = {
            "device": p.device,
            "description": p.description,
            "hwid": p.hwid,
        }
        ports.append(item)

        marker = f"{p.description} {p.hwid}".lower()
        if "2c99" in marker or "prusa" in marker:
            candidates.append(item)

    return {
        "available": True,
        "error": "",
        "ports": ports,
        "mk4s_candidates": candidates,
        "hardware_opened": False,
    }
