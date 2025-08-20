import json
import os

CAL_FILE = "cal_offsets.json"

def load_calibration():
    if not os.path.exists(CAL_FILE):
        return {}
    with open(CAL_FILE, "r") as f:
        return json.load(f)

def save_calibration(data):
    with open(CAL_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_offset(sensor, axis, default=0.0):
    calib = load_calibration()
    return calib.get(sensor, {}).get(axis, default)

def set_offset(sensor, axis, value):
    calib = load_calibration()
    if sensor not in calib:
        calib[sensor] = {}
    calib[sensor][axis] = value
    save_calibration(calib)
