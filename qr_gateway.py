#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jednoduchý web s automatickým QR kódem
Mobil se připojí bez nutnosti zadávat IP
"""

from flask import Flask, render_template_string
import qrcode
from io import BytesIO
import base64
import socket

app = Flask(__name__)

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

def generate_qr_base64():
    """Generuje QR kód a vrací ho jako base64"""
    # Vytvoříme QR kód, který směřuje na gateway, aby gateway zpracovala přesměrování
    local_ip = get_local_ip()
    url = f"http://{local_ip}:5001/chat"

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Konvertovat na base64
    img_io = BytesIO()
    img.save(img_io, 'PNG', optimize=True)
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.getvalue()).decode()
    
    return img_base64, url

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat - Připojení</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            max-width: 500px;
            width: 100%;
            text-align: center;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }

        .qr-container {
            background: #f5f5f5;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
        }

        .qr-container img {
            max-width: 300px;
            height: 300px;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
            border: 2px solid #ddd;
            border-radius: 10px;
        }

        .url-box {
            background: #f0f2f5;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            word-break: break-all;
        }

        .url-box p {
            color: #667eea;
            font-weight: 600;
            font-size: 16px;
        }

        .instructions {
            text-align: left;
            margin-top: 30px;
        }

        .instructions h2 {
            color: #333;
            font-size: 18px;
            margin-bottom: 15px;
        }

        .instructions ol {
            color: #666;
            padding-left: 20px;
            line-height: 1.8;
        }

        .instructions li {
            margin-bottom: 10px;
        }

        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 40px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 20px;
            cursor: pointer;
            border: none;
            font-size: 16px;
            transition: opacity 0.2s;
        }

        .button:hover {
            opacity: 0.9;
        }

        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
            text-align: left;
        }

        .info-box p {
            color: #333;
            font-size: 14px;
            margin: 5px 0;
        }

        @media (max-width: 600px) {
            .container {
                padding: 25px;
            }

            h1 {
                font-size: 24px;
            }

            .qr-container {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💬 Chat</h1>
        <p class="subtitle">Připoj se bez IP adresy!</p>

        <div class="qr-container">
            <img src="data:image/png;base64,{{ qr_code }}" alt="QR Code" loading="lazy">
        </div>

        <div class="url-box">
            <p>{{ chat_url }}</p>
        </div>

        <a href="{{ chat_url }}" class="button">Přejít na Chat →</a>

        <div class="instructions">
            <h2>📱 Jak se připojit z mobilu:</h2>
            <ol>
                <li>Otevři <strong>fotoaparát</strong> nebo <strong>QR scanner</strong></li>
                <li>Naskenuj QR kód výše</li>
                <li>Klikni na odkaz</li>
                <li>Hotovo! Jsi v chatu 🎉</li>
            </ol>
        </div>

        <div class="info-box">
            <p><strong>💡 Tip:</strong> Mobil musí být ve <strong>stejné WiFi síti</strong> jako počítač!</p>
            <p><strong>🔗 Přímý odkaz:</strong> http://privatechat.local:5000  nebo  http://{{ local_ip }}:5000</p>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    qr_code, url = generate_qr_base64()
    local_ip = get_local_ip()
    
    return render_template_string(HTML_TEMPLATE, qr_code=qr_code, chat_url=url, local_ip=local_ip)

@app.route('/chat')
def chat():
    """Přesměrování na chat"""
        # Stránka, která zkusí nejdříve otevřít doménu privatechat.local
        # Pokud načtení na doméně selže, JavaScript přesměruje na IP adresu serveru.
        local_ip = get_local_ip()
        domain = 'http://privatechat.local:5000'
        ip_url = f'http://{local_ip}:5000'

        html = f"""
<!doctype html>
<html>
<head>
    <meta charset='utf-8'>
    <title>Přesměrování...</title>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <style>body{{font-family:Arial,Helvetica,sans-serif;text-align:center;padding:40px}}</style>
</head>
<body>
    <h2>Přesměrování na chat...</h2>
    <p>Zkusím doménu <strong>privatechat.local</strong>, pokud to nefunguje, otevřu IP.</p>
    <p><a id='link' href='{ip_url}'>Pokud nic nefunguje, klikni sem</a></p>
    <script>
        // Vytvoříme obrazek z domény; pokud se načte, doména funguje
        (function(){{
            var domain = '{domain}';
            var ip = '{ip_url}';
            var img = new Image();
            img.onload = function(){{ window.location.href = domain; }};
            img.onerror = function(){{ window.location.href = ip; }};
            // Zkusíme načíst favicon z domény
            img.src = domain + '/favicon.ico?rnd=' + Math.random();
            // Po 2s fallback pro případy, kdy onerror nemusí být vyvolán
            setTimeout(function(){{ window.location.href = ip; }}, 2000);
        }})();
    </script>
</body>
</html>
"""

        return html

if __name__ == '__main__':
    local_ip = get_local_ip()
    
    print("=" * 70)
    print("QR KÓD GATEWAY PRO CHAT")
    print("=" * 70)
    print(f"\n🌐 Přístup:")
    print(f"   Z počítače: http://localhost:5001")
    print(f"   Z mobilu: http://{local_ip}:5001")
    print(f"\n📱 Nastav mobil:")
    print(f"   1. Naskenuj QR kód")
    print(f"   2. Nebo zadej: http://{local_ip}:5001")
    print("=" * 70)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
