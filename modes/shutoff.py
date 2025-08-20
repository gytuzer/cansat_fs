import json
import redis
import time

REDIS_HOST = "localhost"
REDIS_PORT = 6379
flags_file = "flags.json"

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def reset_flags():
    """Reset all flags and subflags to 0 after shutdown."""
    flags = {
        "mode": 0,
        "powerup": 0,
        "handshake": 0,
        "wait": 0,
        "calib_complete": 0,
        "arm": 0,
        "cam": 0,
        "data": 0,
        "launch": 0,
        "apogee": 0,
        "drogue": 0,
        "500m": 0,
        "delv0": 0,
        "beacon": 0
    }
    with open(flags_file, "w") as f:
        json.dump(flags, f, indent=2)
    return flags

def run_mode7():
    """Main entry for Mode 7: Shutdown."""
    flags = reset_flags()
    r.rpush("log_queue", "Mode 7: Shutdown complete, all flags reset")
    print("[Shutdown] All flags cleared, system idle")

    # Optionally notify GS
    r.publish("commands", "SHUTDOWN_COMPLETE")

    # System halts here
    while True:
        time.sleep(1)  # Keep alive in case of GS diagnostics

if __name__ == "__main__":
    run_mode7()
