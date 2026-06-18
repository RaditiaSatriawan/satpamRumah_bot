import os
import threading
import paho.mqtt.client as mqtt
import requests
import json
from flask import Flask

# --- Kredensial HiveMQ ---
MQTT_BROKER = "ced73b07cef94101ae6ce9a615c5e1fa.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "raditia"
MQTT_PASS = "Raditia1"
TOPIC_NODE1 = "iot/kelasC/kelompok03/node1/data"
TOPIC_NODE2 = "iot/kelasC/kelompok03/node2/data"

# --- Kredensial Telegram ---
# Ganti teks di bawah dengan token dari BotFather
TELEGRAM_TOKEN = "8318055528:AAF7hmI1BLWz-p4QRHtyilzHWA1M7JmFHWU" 
# ID Grup IOT Anda
CHAT_ID = "-5246241932" 

# --- Setup Web Server Bohongan (Flask) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Sistem Jembatan IoT-Telegram Berjalan Sempurna!"

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": pesan}
    requests.post(url, json=payload)

# --- Setup MQTT ---
def on_connect(client, userdata, flags, rc):
    print("Terhubung ke HiveMQ! Menyadap data kampus...")
    client.subscribe(TOPIC_NODE1)
    client.subscribe(TOPIC_NODE2)
    kirim_telegram("🤖 Sistem Bot Pemantau Aktif! Menunggu data dari alat IoT di kampus...")

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    try:
        data = json.loads(payload)
        
        if msg.topic == TOPIC_NODE1:
            suhu = data.get("temperature")
            # Filter agar tidak spam: hanya lapor jika suhu > 30
            if suhu > 30.0:
                kirim_telegram(f"⚠️ PERINGATAN SUHU PANAS!\nSuhu saat ini: {suhu}°C")
                
        elif msg.topic == TOPIC_NODE2:
            hazard = data.get("hazard")
            if hazard == 1:
                kirim_telegram("🚨 DARURAT API/GAS TERDETEKSI DI KAMPUS! 🚨")
                
    except Exception as e:
        print("Error parsing JSON:", e)

def run_mqtt():
    client = mqtt.Client(client_id="Node4_TelegramBridge_Render")
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set() 
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print("Gagal koneksi MQTT:", e)

if __name__ == "__main__":
    # Jalankan proses sadap MQTT di latar belakang (Thread)
    mqtt_thread = threading.Thread(target=run_mqtt)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Jalankan Web Server untuk mengecoh Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
