#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatické zveřejňování domény přes mDNS (Bonjour)
Funguje na počítači i mobilu bez nutnosti konfigurace
"""

from zeroconf import ServiceInfo, Zeroconf
import socket
import time
import threading

def get_local_ip():
    """Zjistí lokální IP adresu"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())

def start_mdns_service():
    """Spustí mDNS službu pro auto-discovery"""
    
    local_ip = get_local_ip()
    port = 5000
    
    print("=" * 70)
    print("SPUŠTĚNÍ CHAT SLUŽBY S AUTO-DISCOVERY")
    print("=" * 70)
    print(f"\n🌐 Přístup:")
    print(f"   Z počítače: http://privatechat.local:5000")
    print(f"   Z mobilu: http://privatechat.local:5000")
    print(f"   IP adresa: http://{local_ip}:5000")
    print(f"\n📱 Jak to používat:")
    print(f"   1. Na mobilu jsi ve stejné WiFi")
    print(f"   2. Otevři prohlížeč a zadej: http://chat.local:5000")
    print(f"   3. Nebo: http://{local_ip}:5000")
    print(f"\n✅ Služba je aktivní...")
    print("=" * 70)
    
    try:
        # Vytvoření mDNS služby
        service_info = ServiceInfo(
            "_http._tcp.local.",
            "privatechat._http._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={
                'path': '/',
                'description': 'Privátní Chat Aplikace'
            },
            server="privatechat.local."
        )
        
        # Registrace služby
        zeroconf = Zeroconf()
        zeroconf.register_service(service_info)
        
        print(f"\n✨ Služba zaregistrována!")
        print(f"   Jméno: privatechat.local")
        print(f"   IP: {local_ip}:5000")
        
        # Udržování služby aktivní
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Zastavuji službu...")
        finally:
            zeroconf.unregister_service(service_info)
            zeroconf.close()
            
    except Exception as e:
        print(f"❌ Chyba při registraci: {e}")
        print("\n💡 Alternativa: Používej přímou IP adresu")
        print(f"   http://{local_ip}:5000")

if __name__ == '__main__':
    try:
        start_mdns_service()
    except ImportError:
        print("❌ Chyba: Musíš nainstalovat 'zeroconf'")
        print("\nInstalace: pip install zeroconf")
