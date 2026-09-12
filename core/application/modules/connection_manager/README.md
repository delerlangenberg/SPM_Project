# Module 1: Connection Manager

Last updated: 2026-07-15

## Responsibility

Owns COM-port discovery and the connect/disconnect lifecycle. It enables only the desktop read-only handshake and does not grant motion authorization.

## Public interface

- `ConnectionManager.connect(port="")`
- `ConnectionManager.disconnect()`
- `ConnectionManager.getStatus()` and Python-style alias `get_status()`
- `ConnectionManager.accept_payload(payload)` for asynchronous backend integration
- `ConnectionManager.set_simulation_mode(enabled)` reports virtual readiness without opening serial hardware
- `discover_ports(provider=None)`
- Immutable `ConnectionStatus` and `SerialPortInfo` values

## Configuration

`connect()` sets `SPM_WEB_ALLOW_READONLY_HARDWARE=1` for the native desktop process. This permits firmware, endstop, temperature, and position queries only. It does not set any motion environment variable.

## Dependencies

The default backend uses `core.web.system_control`. Serial discovery uses pyserial. Tests inject backends and do not require hardware.

## State machine

`disconnected → connecting → connected/failed → disconnecting → disconnected/connected-on-failure`

## Error handling

Backend exceptions become failed payloads. A failed disconnect preserves the connected state so the UI does not falsely report a safe disconnection.

## Isolated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q core\application\modules\connection_manager\tests.py
```
