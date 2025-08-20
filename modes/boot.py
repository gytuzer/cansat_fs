import time
import redis
import json
import serial

FLAGS_FILE = "flags.json"
CAL_OFFSETS = "cal_offsets.json"

# Setup Redis
r = redis.Redis()

# Setup XBee UART
xbee = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

def load_flags():
    try:
        with open(FLAGS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_flags(flags):
    with open(FLAGS_FILE, "w") as f:
        json.dump(flags, f, indent=4)

def log_event(event):
    msg = {"time": time.time(), "event": event}
    r.publish("logs", json.dumps(msg))

def boot_mode():
    flags = load_flags()
    flags["mode"] = 1
    flags["subprocess"] = 1
    save_flags(flags)

    # --- Subprocess 1: Handshake ---
    log_event("Boot: Sending PWR_ON")
    xbee.write(b"PWR_ON\n")

    ack_received = False
    start_time = time.time()
    while time.time() - start_time < 10:  # 10s window for ack
        if xbee.in_waiting:
            msg = xbee.readline().decode().strip()
            if msg.lower() == "ack":
                ack_received = True
                break
        time.sleep(0.1)

    if ack_received:
        log_event("GS ACK received -> comms_est 0")
        xbee.write(b"comms_est 0\n")
        flags["handshake"] = 1
    else:
        log_event("GS ACK not received -> comms_est 1")
        xbee.write(b"comms_est 1\n")
        flags["handshake"] = 0

    flags["subprocess"] = 2
    save_flags(flags)

    # --- Subprocess 2: Wait for calibration ---
    log_event("Boot: Waiting for calibration command")
    xbee.write(b"waiting for calibration command\n")
    flags["wait"] = 1
    save_flags(flags)

    start_wait = time.time()
    calib_received = False

    while time.time() - start_wait < 30:  # 30s wait for GS command
        msg = r.get("last_command")
        if msg:
            msg = msg.decode()
            if msg.startswith("C-") and "calibrate" in msg:
                calib_received = True
                log_event("Calibration command received")
                break
        time.sleep(0.5)

    if not calib_received:
        log_event("Auto-calibration triggered after 30s")

    # Transition to Mode 2 (calibration)
    flags["mode"] = 2
    flags["calib_complete"] = 0
    save_flags(flags)

    log_event("Switching to Mode 2: Calibration")
    return

if __name__ == "__main__":
    boot_mode()
