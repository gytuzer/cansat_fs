import redis
import time
import json
import threading
from datetime import datetime

# Config
TEAM_ID = "TEAM123"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
flags_file = "flags.json"

packet_count = 0

def load_flags():
    with open(flags_file, "r") as f:
        return json.load(f)

def save_flags(flags):
    with open(flags_file, "w") as f:
        json.dump(flags, f, indent=2)

def telemetry_loop():
    """Continuously collect sensor data and publish telemetry packets."""
    global packet_count
    while True:
        flags = load_flags()
        if flags.get("mode") != 3:  # Stop if not in Mode 3
            break

        # === Collect data from Redis ===
        imu = r.lrange("imu", -1, -1)
        bme = r.lrange("bme", -1, -1)
        adc = r.lrange("adc", -1, -1)
        gps = r.lrange("gps", -1, -1)

        # Parse values (dummy fallback if missing)
        imu_data = imu[0] if imu else "0,0,0"
        bme_data = bme[0].split(",") if bme else ["0","0","0"]  # temp, press, humid
        adc_data = adc[0] if adc else "0.0"
        gps_data = gps[0].split(",") if gps else ["00:00:00","0.0","0.0","0.0","0"]

        temp = bme_data[0]
        press = bme_data[1]
        altitude = "100.0"  # TODO: calculate from pressure baseline
        voltage = adc_data
        gnss_time, gnss_lat, gnss_lon, gnss_alt, gnss_sats = gps_data
        accel = imu_data  # full accel vector
        gyro = "0,0,0"    # dummy for now
        sw_state = "MODE3"
        optional = "N/A"

        # === Build telemetry packet ===
        packet_count += 1
        packet = f"{TEAM_ID},{datetime.utcnow().isoformat()},{packet_count},{altitude}," \
                  f"{press},{temp},{voltage},{gnss_time},{gnss_lat},{gnss_lon},{gnss_alt}," \
                  f"{gnss_sats},{accel},{gyro},{sw_state},{optional}"

        # Publish + log
        r.publish("data", packet)
        r.rpush("log_queue", f"[Telemetry] {packet}")

        time.sleep(1)

def run_mode3():
    """Main entry for Mode 3: Arm + Launch"""
    flags = load_flags()
    flags["mode"] = 3
    flags["cam"] = 1
    flags["data"] = 1
    save_flags(flags)

    r.rpush("log_queue", "Mode 3 started: Arm + Launch")

    # Start telemetry in background
    t = threading.Thread(target=telemetry_loop, daemon=True)
    t.start()

    # Launch + apogee detection loop (dummy logic for now)
    while flags.get("mode") == 3:
        flags = load_flags()
        # TODO: implement launch/apogee detection here
        time.sleep(1)

if __name__ == "__main__":
    run_mode3()
