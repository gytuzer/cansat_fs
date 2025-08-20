import time
import json
import importlib
import redis
import threading
from pathlib import Path

FLAGS_FILE = "flags.json"
MODES = {
    1: "mode1_boot",
    2: "mode2_calibration",
    3: "mode3_arm_launch",
    4: "mode4_descent",
    5: "mode5_control_systems",
    6: "mode6_touchdown",
    7: "mode7_shutdown"
}

r = redis.Redis(host="localhost", port=6379, db=0)

def load_flags():
    try:
        with open(FLAGS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_flags(flags):
    with open(FLAGS_FILE, "w") as f:
        json.dump(flags, f, indent=2)

def run_mode(mode, flags):
    if mode not in MODES:
        return
    module_name = MODES[mode]
    try:
        module = importlib.import_module(module_name)
        module.run(flags, r)   # pass flags + redis handle
    except Exception as e:
        print(f"[MAIN] Error running {module_name}: {e}")

def redis_listener():
    pubsub = r.pubsub()
    pubsub.subscribe("commands", "override")
    for msg in pubsub.listen():
        if msg["type"] == "message":
            data = msg["data"].decode()
            print(f"[MAIN] Redis event: {data}")
            if data.startswith("O"):  # override
                try:
                    new_mode = int(data[1])
                    flags = load_flags()
                    flags["mode"] = new_mode
                    save_flags(flags)
                except:
                    print("[MAIN] Bad override code")

def main_loop():
    # Power on
    flags = load_flags()
    flags["powered_on"] = 1
    save_flags(flags)

    # Start Redis listener thread
    threading.Thread(target=redis_listener, daemon=True).start()

    last_mode = None
    while True:
        flags = load_flags()
        mode = flags.get("mode", 0)
        if mode != last_mode and mode in MODES:
            print(f"[MAIN] Switching to mode {mode}")
            run_mode(mode, flags)
            last_mode = mode
        time.sleep(1)

if __name__ == "__main__":
    main_loop()
