from core.motion.prusa_gcode_backend import PrusaGcodeBackend

PORT = "COM5"

p = PrusaGcodeBackend(
    port=PORT,
    x_limits=(20, 80),
    y_limits=(20, 80),
    z_limits=(5, 50),
)

try:
    p.connect()
    print("Connected:", p.get_state())

    print("Moving safely to Z20...")
    p.move_to(z=20, feedrate=300)

    print("Moving safely to X50 Y50...")
    p.move_to(x=50, y=50, feedrate=1200)

    print("Final state:", p.get_state())

finally:
    p.disconnect()
    print("Disconnected")
