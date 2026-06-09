from core.motion.prusa_gcode_backend import PrusaGcodeBackend
import time

PORT = "COM5"

p = PrusaGcodeBackend(
    port=PORT,
    x_limits=(20, 80),
    y_limits=(20, 80),
    z_limits=(5, 50),
)

points = [
    (45, 45),
    (55, 45),
    (55, 55),
    (45, 55),
    (45, 45),
    (50, 50),
]

try:
    p.connect()
    print("Connected:", p.get_state())

    print("Moving to safe height Z20...")
    p.move_to(z=20, feedrate=300)

    for x, y in points:
        print(f"Moving to X{x} Y{y}")
        p.move_to(x=x, y=y, feedrate=900)
        print("State:", p.get_state())
        time.sleep(0.5)

finally:
    p.disconnect()
    print("Disconnected")
