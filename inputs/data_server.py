# data_server.py
import threading
import time
import redis
import serial
import json

# ---- Redis Setup ----
r = redis.Redis(host="localhost", port=6379, db=0)

# ---- Helper ----
def publish(channel, data):
    """Publish a dict with timestamp to Redis channel"""
    payload = {
        "timestamp": time.time(),
        "data": data
    }
    r.publish(channel, json.dumps(payload))

# ---- Sensor Threads ----
def imu_thread():
    while True:
        try:
            # TODO: Replace with actual IMU read
            imu_data = {"ax": 0.0, "ay": 0.0, "az": 0.0}
            publish("imu", imu_data)
            time.sleep(0.05)  # ~20Hz
        except Exception as e:
            print("IMU error:", e)
            time.sleep(1)

def bme_thread():
    while True:
        try:
            # TODO: Replace with actual BME read
            bme_data = {"temp": 25.0, "press": 1013.2, "humid": 50.0}
            publish("bme", bme_data)
            time.sleep(1)  # slower sensor
        except Exception as e:
            print("BME error:", e)
            time.sleep(1)

def bmp_thread():
    while True:
        try:
            # TODO: Replace with actual BMP read
            bmp_data = {"press": 1012.8, "alt": 123.4}
            publish("bmp", bmp_data)
            time.sleep(1)
        except Exception as e:
            print("BMP error:", e)
            time.sleep(1)

def adc_thread():
    while True:
        try:
            # TODO: Replace with actual ADS1115 read
            adc_data = {"battery": 3.7, "ctrl": 2.5, "motor": 1.2}
            publish("adc", adc_data)
            time.sleep(0.5)
        except Exception as e:
            print("ADC error:", e)
            time.sleep(1)

def gps_thread():
    while True:
        try:
            # TODO: Replace with actual GPS read (serial, NMEA parsing)
            gps_data = {"lat": 12.34, "lon": 56.78, "alt": 123.0}
            publish("gps", gps_data)
            time.sleep(1)
        except Exception as e:
            print("GPS error:", e)
            time.sleep(1)

# ---- XBee RX (Ground Station Commands) ----
def gs_thread():
    try:
        xbee = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)
    except Exception as e:
        print("XBee init error:", e)
        return

    while True:
        try:
            line = xbee.readline().decode("ascii", errors="ignore").strip()
            if not line:
                continue

            if line.startswith("C-"):
                publish("commands", {"cmd": line})
            elif line.startswith("O-"):
                publish("override", {"cmd": line})
            else:
                print("Unknown GS message:", line)

        except Exception as e:
            print("GS RX error:", e)
            time.sleep(1)

# ---- Main Entrypoint ----
if __name__ == "__main__":
    threads = [
        threading.Thread(target=imu_thread, daemon=True),
        threading.Thread(target=bme_thread, daemon=True),
        threading.Thread(target=bmp_thread, daemon=True),
        threading.Thread(target=adc_thread, daemon=True),
        threading.Thread(target=gps_thread, daemon=True),
        threading.Thread(target=gs_thread, daemon=True),
    ]

    for t in threads:
        t.start()

    print("Data server running. Publishing to Redis channels: imu, bme, bmp, adc, gps, commands, override")

    # Keep alive
    while True:
        time.sleep(5)
