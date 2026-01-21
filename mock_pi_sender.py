import requests
import time
import random

# 配置信息
# 如果你本地运行 Flask，通常是 http://127.0.0.1:5000
# 如果要发给云服务器，就写云服务器的公网 IP
API_URL = "http://34.27.88.95:9000/api/update_weight" 
TARGET_FOOD_ID = 40  # 假设我们要更新 ID 为 1 的菜品

def simulate_weighing():
    # 模拟一个初始重量
    current_weight = 2000.0 
    
    print("🚀 模拟树莓派称重客户端启动...")
    print(f"目标 URL: {API_URL}")

    while True:
        try:
            # 模拟重量缓慢减少（每次减少 0 到 100g）
            reduction = random.uniform(0, 100)
            current_weight = max(0, current_weight - reduction)
            
            # 构造发送给服务器的数据
            payload = {
                "food_id": TARGET_FOOD_ID,
                "weight": round(current_weight, 2)
            }
            
            # 发送请求
            response = requests.post(API_URL, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ 发送成功: {payload['weight']}g | 服务器响应: {response.json()['msg']}")
            else:
                print(f"❌ 发送失败: 状态码 {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ 连接错误: {e}")

        # 如果重量减为 0，模拟重新加满
        if current_weight <= 0:
            print("♻️ 菜品已卖完，模拟重新上菜...")
            current_weight = 2000.0
            time.sleep(5)

        time.sleep(3) # 每 3 秒同步一次数据

if __name__ == "__main__":
    simulate_weighing()