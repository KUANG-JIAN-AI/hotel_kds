import RPi.GPIO as GPIO
from hx711 import HX711
import time
import requests

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

hx = HX711(5, 6)

SCALE = 300.0  # ← 校正で求めた値
hx.tare()  # ゼロ点調整

CLOUD_URL = "http://34.27.88.95:9000/api/update_weight"
FOOD_ID = 1  # 这台秤对应哪道菜

while True:
    w = hx.get_weight(5) / SCALE

    try:
        # 构造要发送的数据
        payload = {
            "food_id": FOOD_ID,
            "weight": max(0, w)
        }
        # 通过网络发送到云端
        response = requests.post(CLOUD_URL, json=payload, timeout=5)
        print(f"数据已同步: {w}g, 响应: {response.status_code}")
    except Exception as e:
        print(f"同步失败: {e}")
    
    print(w)
    time.sleep(5)
