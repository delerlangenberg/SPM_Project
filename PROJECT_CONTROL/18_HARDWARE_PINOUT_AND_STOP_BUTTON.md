# Hardware Pinout & Stop Button Configuration

Authoritative Mapping on **Arduino Mega 2560 + Grove Base Shield V2**:

| Peripheral | Grove Socket / Port | Arduino Mega Pins | Signal & Role |
|---|---|---|---|
| **CR-Touch Probe** | **D2** + **D8** | `D3` (Input, INT5), `D8` (PWM Output) | `D3` = Sensor trigger (Blue wire)<br>`D8` = Servo deploy/stow control (Yellow wire) |
| **RGB Status Light** | **D6** | `D6` (Clock), `D7` (Data) | Visual machine and safety state indicator |
| **Manual Stop Button** | **D7** | `D7` (Digital Input) | Seeed Studio Grove Button v1.3 manual abort/stop input |
| **LCD Status Display** | **I2C (12C)** | `SDA` (Pin 20), `SCL` (Pin 21) | Grove I2C RGB Backlight LCD display (I2C address `0x3E`) |

---

## Safety Verification
1. **Software Stop Button**:
   - Integrated into `DeterministicHardwareSafetyGate` and `SafetySupervisor`.
   - Latches `E_STOP` immediately upon click, blocking all subsequent motion authorization until reset.
2. **Physical Stop Button on D7**:
   - Separated from the I2C bus lines to prevent bus clock-stretching lockups.
   - Provides physical operator abort capability.
3. **I2C LCD Display**:
   - Operates on dedicated hardware TWI bus pins (SDA=20, SCL=21, address `0x3E`).

