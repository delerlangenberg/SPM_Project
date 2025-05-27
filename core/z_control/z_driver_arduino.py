# z_driver_arduino.py

class ArduinoZDriver:
    def __init__(self, port="COM3", baudrate=115200):
        import serial
        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
        except serial.SerialException as e:
            raise RuntimeError(f"Unable to open serial port: {e}")
        self.position = 0.0

    def move_to(self, z_position):
        self.serial.write(f"MOVE {z_position}\n".encode())
        self.position = z_position

    def get_position(self):
        self.serial.write(b"GET_POS\n")
        response = self.serial.readline().decode().strip()
        try:
            return float(response)
        except ValueError:
            return self.position  # fallback if communication fails

    def close(self):
        self.serial.close()
