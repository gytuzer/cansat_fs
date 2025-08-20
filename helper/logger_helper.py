import time
import json
from redis_helper import RedisHelper

redis_client = RedisHelper()

LOG_FILE = "events.log"

def log_event(source, message, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "time": timestamp,
        "level": level,
        "source": source,
        "message": message
    }

    # Print to console
    print(f"[{timestamp}] [{level}] [{source}] {message}")

    # Save to file
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    # Publish to Redis (optional channel: "events")
    redis_client.publish("events", log_entry)
