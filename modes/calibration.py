import time
import redis
import json
import serial
import numpy as np

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

def calibrate_imu():
    """Collect 300 IMU samples from Redis and compute offsets."""
    accel_samples = []
    gyro_samples = []
    mag_samples = []

    log_event("Calibration started: collecting IMU data")

    for _ in range(300):  # 300 samples (~30s if 0.1s delay)
        msg = r.get("last_imu")
        if msg:
            try:
                data = json.loads(msg.decode())
                accel_samples.append(data["accel"])
                gyro_samples.append(data["gyro"])
                mag_samples.append(data["mag"])
            except Exception as e:
                log_event(f"Bad IMU data: {e}")
        time.sleep(0.1)

    if not accel_samples:
        log_event("No IMU data collected! Calibration failed.")
        return None

    # Compute means
    accel_offset = np.mean(accel_samples, axis=0).tolist()
    gyro_offset = np.mean(gyro_samples, axis=0).tolist()
    mag_offset = np.mean(mag_samples, axis=0).tolist()

    offsets = {
        "accel_offset": accel_offset,
        "gyro_offset": gyro_offset,
        "mag_offset": mag_offset
    }

    with open(CAL_OFFSETS, "w") as f:
        json.dump(offsets, f, indent=4)

    log_event("Calibration complete, offsets stored")
    return offsets

def mode2_calibrate():
    flags = load_flags()
    flags["mode"] = 2
    flags["subprocess"] = 1
    save_flags(flags)

    xbee.write(b"Calibration in progress...\n")
    offsets = calibrate_imu()

    if offsets:
        flags["calib_complete"] = 1
        save_flags(flags)
        xbee.write(b"Calibration complete\n")
        log_event("Mode 2 finished, entering Mode 3 (Arming)")
        flags["mode"] = 3
        flags["arm"] = 0  # ready for GS arming
        save_flags(flags)
    else:
        xbee.write(b"Calibration failed\n")
        log_event("Mode 2 failed, staying in calibration mode")

if __name__ == "__main__":
    mode2_calibrate()
