import redis
import json

class RedisHelper:
    def __init__(self, host="localhost", port=6379, db=0):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    # ---- Publish to a channel ----
    def publish(self, channel, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        self.r.publish(channel, data)

    # ---- Subscribe to a channel ----
    def subscribe(self, channel):
        pubsub = self.r.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    # ---- Set key-value ----
    def set_value(self, key, value):
        if isinstance(value, dict):
            value = json.dumps(value)
        self.r.set(key, value)

    # ---- Get key-value ----
    def get_value(self, key, as_json=False):
        val = self.r.get(key)
        if val and as_json:
            return json.loads(val)
        return val
