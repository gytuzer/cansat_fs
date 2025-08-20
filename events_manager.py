# event_manager.py
import redis
import json
import time
import threading
import os

FLAGS_FILE = "flags.json"

# ---- Redis ----
r = redis.Redis(host="localhost", port=6379, db=0)

def load_flags():
    """Read current flags from JSON file"""
    if not os.path.exists(FLAGS_FILE):
        return {}
    with open(FLAGS_FILE, "r") as f:
        return json.load(f)

def save_flags(flags):
    """Write updated flags to JSON file"""
    with open(FLAGS_FILE, "w") as f:
        json.dump(flags, f, indent=2)

# ---- Handlers ----
def handle_command(cmd):
    flags = load_flags()
    print(f"[COMMAND] {cmd}")

    if cmd == "C-calibrate":
        flags["wait"] = 0
        flags["mode"] = 2  # Calibration mode
        flags["calib_complete"] = 0
        save_flags(flags)

    elif cmd == "C-arm":
        flags["mode"] = 3  # Arming mode
        flags["arm"] = 1
        save_flags(flags)

    elif cmd == "C-cleanup":
        flags = {k: 0 for k in flags}  # Clear all flags
        flags["mode"] = 0
        save_flags(flags)

    # Add more C- commands here

def handle_override(cmd):
    flags = load_flags()
    print(f"[OVERRIDE] {cmd}")

    if cmd == "O23":
        flags["override_code"] = 23
        save_flags(flags)

    # Add more O- codes here

def handle_sensor(channel, data):
    """For reacting to sensor triggers (launch, apogee, altitude thresholds, etc.)"""
    flags = load_flags()

    if channel == "bmp":  # example: altitude-based event
        alt = data.get("alt", 0)
        if alt > 100 and flags.get("mode") == 3 and not flags.get("launch_detected"):
            print(">>> Launch detected by altitude")
            flags["launch_detected"] = 1
            save_flags(flags)

        if alt <= 500 and flags.get("mode") == 4 and not flags.get("500m"):
            print(">>> 500m detected, controlled descent")
            flags["500m"] = 1
            flags["mode"] = 5  # Controlled descent
            save_flags(flags)

    # Add more sensor-driven events here

# ---- Redis Subscriber Loop ----
def redis_listener():
    pubsub = r.pubsub()
    pubsub.subscribe("commands", "override", "imu", "bme", "bmp", "adc", "gps")

    for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        channel = msg["channel"].decode()
        payload = json.loads(msg["data"].decode())

        if channel == "commands":
            handle_command(payload["data"]["cmd"])
        elif channel == "override":
            handle_override(payload["data"]["cmd"])
        else:
            handle_sensor(channel, payload["data"])

# ---- Main ----
if __name__ == "__main__":
    print("Event Manager started. Listening for events...")
    threading.Thread(target=redis_listener, daemon=True).start()

    # Background housekeeping loop
    while True:
        time.sleep(1)
