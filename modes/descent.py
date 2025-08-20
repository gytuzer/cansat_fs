import redis
import time
import json
import threading

REDIS_HOST = "localhost"
REDIS_PORT = 6379
flags_file = "flags.json"

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def load_flags():
    with open(flags_file, "r") as f:
        return json.load(f)

def save_flags(flags):
    with open(flags_file, "w") as f:
        json.dump(flags, f, indent=2)

def control_system_loop():
    """Dummy inferro event manager loop (runs until shutdown)."""
    while True:
        flags = load_flags()
        if flags.get("mode") != 4:
            break

        if flags.get("500m_flag") == 1:
            # Control system becomes active
            r.rpush("log_queue", "[Descent] Control system active below 500m")
            # TODO: call inferro control system here
            break

        time.sleep(1)

def altitude_monitor():
    """Check altitude and trigger 500m_flag + switch to controlled descent."""
    while True:
        flags = load_flags()
        if flags.get("mode") != 4:
            break

        # Dummy altitude, TODO: calculate from BME/BMP baseline
        altitude = 1000  

        if altitude <= 500:
            flags["500m_flag"] = 1
            save_flags(flags)
            r.rpush("log_queue", "[Descent] Altitude <= 500m, switching to Mode 5")
            # Switch mode to controlled descent
            flags["mode"] = 5
            save_flags(flags)
            break

        time.sleep(1)

def run_mode4():
    """Main entry for Mode 4: Descent."""
    flags = load_flags()
    flags["mode"] = 4
    flags["drogue"] = 1   # drogue deployed
    flags["500m_flag"] = 0
    save_flags(flags)

    r.rpush("log_queue", "Mode 4 started: Descent, drogue deployed")

    # Start subprocesses
    t1 = threading.Thread(target=control_system_loop, daemon=True)
    t2 = threading.Thread(target=altitude_monitor, daemon=True)
    t1.start()
    t2.start()

    # Keep alive until mode change
    while flags.get("mode") == 4:
        flags = load_flags()
        time.sleep(1)

if __name__ == "__main__":
    run_mode4()
