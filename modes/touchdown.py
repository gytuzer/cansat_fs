import time
import json
import redis
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

def beacon_loop():
    """Beacon transmitter loop."""
    while True:
        flags = load_flags()
        if flags.get("mode") != 6 or flags.get("beacon") != 1:
            break
        r.publish("beacon", "BEACON: Touchdown - unit alive and waiting for cleanup")
        r.rpush("log_queue", "[Beacon] Sent beacon packet")
        print("[Beacon] Ping sent")
        time.sleep(5)  # beacon ping every 5s

def listen_for_cleanup():
    """Listen to GS commands and trigger cleanup."""
    pubsub = r.pubsub()
    pubsub.subscribe("commands")

    for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        cmd = msg["data"]
        if cmd == "C-cleanup":
            r.rpush("log_queue", "[Touchdown] Cleanup command received, shutting down")
            flags = load_flags()
            flags["mode"] = 7   # shift to shutdown
            flags["beacon"] = 0
            save_flags(flags)
            break

def run_mode6():
    """Main entry for Mode 6: Touchdown."""
    flags = load_flags()
    flags["mode"] = 6
    flags["beacon"] = 1
    save_flags(flags)

    r.rpush("log_queue", "Mode 6 started: Touchdown, beacon activated")
    print("[Touchdown] Mode 6 entered, beacon ON")

    # Start beacon + GS listener
    threading.Thread(target=beacon_loop, daemon=True).start()
    threading.Thread(target=listen_for_cleanup, daemon=True).start()

    # Keep alive until mode changes
    while True:
        flags = load_flags()
        if flags.get("mode") != 6:
            break
        time.sleep(1)

if __name__ == "__main__":
    run_mode6()
