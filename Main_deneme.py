import network
import socket
import json
import time
from machine import Pin
from encoder_portable import Encoder 
from twowheel import TwoWheel
from PID import PID

# --- 1. DONANIM VE PID KURULUMU ---
robot = TwoWheel(motor1_pins=(6, 7), motor2_pins=(20, 19))
enc_left = Encoder(Pin(2, Pin.IN), Pin(3, Pin.IN))
enc_right = Encoder(Pin(10, Pin.IN), Pin(11, Pin.IN))

pid_left = PID(kp=150, ki=150, kd=0.1, output_limits=(0, 65535))
pid_right = PID(kp=150, ki=150, kd=0.1, output_limits=(0, 65535))

# --- 2. AĞ BAĞLANTISI ---
SSID = "ROMER_Mech_2.4"
PASSWORD = "K0van1231"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Wi-Fi'ye bağlanılıyor...")
while not wlan.isconnected(): 
    time.sleep(0.5)

print("Bağlantı Başarılı! IP:", wlan.ifconfig()[0])

# UDP Soket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', 5005))
s.setblocking(False)

# --- 3. GÜVENLİK (FAILSAFE) AYARLARI ---
last_packet_time = time.ticks_ms()
TIMEOUT_MS = 600  

# --- 4. ANA DÖNGÜ ---
target_v = 0.0
current_cmd = "STOP"

print("Kobot Kontrol Döngüsü Hazır...")

while True:
    # A. Veri Paketini Çöz
    try:
        data, addr = s.recvfrom(1024)
        packet = json.loads(data.decode())
        current_cmd = packet["cmd"]
        target_v = packet["speed"]
        last_packet_time = time.ticks_ms()
        
        # --- GÜNCELLEME: GELEN KOMUTU TERMİNALE YAZDIR ---
        print("Gelen Komut:", current_cmd, "| Hedef Hız:", target_v)
        
    except:
        pass 

    # B. Acil Durdurma Kontrolü
    if time.ticks_diff(time.ticks_ms(), last_packet_time) > TIMEOUT_MS:
        if current_cmd != "STOP":
            print("!!! BAĞLANTI KESİLDİ - MOTORLAR DURDURULUYOR !!!")
            current_cmd = "STOP"
            target_v = 0

    # C. Hızları Oku ve PID Hesapla
    v_l = abs(enc_left.velocity())
    v_r = abs(enc_right.velocity())

    pid_left.setpoint = target_v