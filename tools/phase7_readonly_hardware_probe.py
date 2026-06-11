import time
import serial

PORT = "COM5"
BAUD = 115200

print(f"Opening {PORT} at {BAUD}...")
ser = serial.Serial(PORT, BAUD, timeout=2)
time.sleep(2)

def send_readonly(command: str):
    print("")
    print(f">>> {command}")
    ser.write((command + "\n").encode("ascii"))
    time.sleep(1.5)

    end_time = time.time() + 3
    while time.time() < end_time:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)

send_readonly("M115")   # firmware/info only
send_readonly("M105")   # temperature/status only
send_readonly("M119")   # endstop/status only

ser.close()
print("")
print("Closed serial port safely.")
