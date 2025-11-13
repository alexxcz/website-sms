#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spustí vše - QR gateway + chat server
"""

import subprocess
import sys
import time
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())

if __name__ == '__main__':
    local_ip = get_local_ip()
    
    print("\n" + "=" * 70)
    print("🚀 SPOUŠTĚNÍ CHAT APLIKACE")
    print("=" * 70)
    print(f"\n✅ Tvá IP adresa: {local_ip}")
    print(f"\n🌐 Přístup:")
    print(f"   Doména: http://privatechat.local:5000")
    print(f"   QR Gateway: http://localhost:5001")
    print(f"   Přímě (IP): http://{local_ip}:5000")
    print(f"\n📱 Z mobilu:")
    print(f"   Doména: http://privatechat.local:5000")
    print(f"   QR kód: http://{local_ip}:5001")
    print("=" * 70 + "\n")
    
    try:
        # Spuštění mDNS služby
        print("📡 Spouštím mDNS službu (privatechat.local)...")
        p_mdns = subprocess.Popen([sys.executable, "mdns_service.py"])
        
        # Čekání na start mDNS
        time.sleep(2)
        
        # Spuštění chat serveru
        print("📡 Spouštím chat server na portu 5000...")
        p1 = subprocess.Popen([sys.executable, "chat_server_db.py"])
        
        # Čekání na start serveru
        time.sleep(3)
        
        # Spuštění QR gateway
        print("🔗 Spouštím QR gateway na portu 5001...")
        p2 = subprocess.Popen([sys.executable, "qr_gateway.py"])
        
        print("\n✨ Všechno běží!")
        print("   Zavřením okna se vše zastaví.")
        
        # Čekání na procesy
        p_mdns.wait()
        p1.wait()
        p2.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Zastavuji...")
        p_mdns.terminate()
        p1.terminate()
        p2.terminate()
        sys.exit(0)
