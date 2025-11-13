from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import sqlite3
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'tvoje_tajna_klic_2024'

# Databáze
DB_FILE = 'chat_database.db'

def init_db():
    """Inicializace databáze"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabulka uživatelů
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabulka zpráv
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender) REFERENCES users(username),
            FOREIGN KEY (recipient) REFERENCES users(username)
        )
    ''')
    
    # Tabulka kontaktů
    c.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY,
            user TEXT NOT NULL,
            contact TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user, contact),
            FOREIGN KEY (user) REFERENCES users(username),
            FOREIGN KEY (contact) REFERENCES users(username)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hashování hesla"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Ověření hesla"""
    return hash_password(password) == password_hash

# Inicializace databáze
init_db()
conv_counter = 0

# HTML šablona
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privátní Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #fff;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Login stránka */
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            width: 100%;
            max-width: 400px;
        }

        .login-box h1 {
            margin-bottom: 30px;
            color: #333;
            text-align: center;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }

        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.2s;
        }

        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 5px rgba(102, 126, 234, 0.2);
        }

        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        .btn:hover {
            opacity: 0.9;
        }

        .error-message {
            color: #e74c3c;
            font-size: 14px;
            margin-bottom: 20px;
            padding: 10px;
            background: #fadbd8;
            border-radius: 5px;
            display: none;
        }

        .success-message {
            color: #27ae60;
            font-size: 14px;
            margin-bottom: 20px;
            padding: 10px;
            background: #d5f4e6;
            border-radius: 5px;
            display: none;
        }

        .toggle-auth {
            text-align: center;
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }

        .toggle-auth a {
            color: #667eea;
            cursor: pointer;
            text-decoration: none;
            font-weight: 600;
        }

        /* Chat interface */
        .chat-interface {
            display: none;
            width: 100%;
            height: 100%;
            flex-direction: column;
        }

        .chat-interface.active {
            display: flex;
        }

        .top-bar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .user-info {
            font-weight: 600;
        }

        .logout-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid white;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }

        .logout-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .chat-main {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .sidebar {
            width: 350px;
            border-right: 1px solid #e5e5e5;
            display: flex;
            flex-direction: column;
            background: #f9f9f9;
        }

        .sidebar-section {
            padding: 15px;
            border-bottom: 1px solid #e5e5e5;
        }

        .sidebar-section h3 {
            font-size: 14px;
            margin-bottom: 10px;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
        }

        .add-contact {
            display: flex;
            gap: 8px;
        }

        .add-contact input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }

        .add-contact button {
            padding: 10px 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }

        .add-contact button:hover {
            background: #5568d3;
        }

        .contacts-list {
            flex: 1;
            overflow-y: auto;
        }

        .contact {
            padding: 12px 15px;
            border-bottom: 1px solid #e5e5e5;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .contact:hover {
            background: #f0f0f0;
        }

        .contact.active {
            background: #e7f3ff;
            border-left: 3px solid #667eea;
        }

        .contact-name {
            font-weight: 500;
            color: #333;
        }

        .contact-remove {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }

        .contact-remove:hover {
            background: #c0392b;
        }

        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: white;
        }

        .chat-header {
            padding: 15px 20px;
            border-bottom: 1px solid #e5e5e5;
            font-weight: 600;
            color: #333;
        }

        .chat-header.empty {
            text-align: center;
            color: #999;
            display: none;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .message {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
        }

        .message.sent {
            justify-content: flex-end;
        }

        .message.received {
            justify-content: flex-start;
        }

        .message-text {
            max-width: 60%;
            padding: 12px 15px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.4;
        }

        .message.sent .message-text {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.received .message-text {
            background: #e5e5e5;
            color: #333;
            border-bottom-left-radius: 4px;
        }

        .message-time {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
            text-align: center;
        }

        .input-area {
            padding: 15px 20px;
            border-top: 1px solid #e5e5e5;
            display: flex;
            gap: 10px;
        }

        .input-area input {
            flex: 1;
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }

        .input-area button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
        }

        .input-area button:hover {
            background: #5568d3;
        }

        .empty-chat {
            display: flex;
            align-items: center;
            justify-content: center;
            flex: 1;
            color: #999;
            font-size: 16px;
        }

        @media (max-width: 768px) {
            .sidebar {
                width: 280px;
            }

            .message-text {
                max-width: 80%;
            }
        }

        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        ::-webkit-scrollbar-thumb {
            background: #ccc;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #999;
        }
    </style>
</head>
<body>
    <!-- Login -->
    <div id="loginContainer" class="login-container">
        <div class="login-box">
            <h1 id="authTitle">Přihlášení</h1>
            <div class="error-message" id="errorMsg"></div>
            <div class="success-message" id="successMsg"></div>
            
            <div id="loginForm">
                <div class="form-group">
                    <label>Uživatelské jméno:</label>
                    <input type="text" id="loginUsername" placeholder="Zadej uživatelské jméno">
                </div>
                <div class="form-group">
                    <label>4místné heslo:</label>
                    <input type="password" id="loginPassword" placeholder="1234" maxlength="4">
                </div>
                <button class="btn" onclick="login()">Přihlásit se</button>
                
                <div class="toggle-auth">
                    Ještě nemáš účet? <a onclick="toggleAuth()">Zaregistruj se</a>
                </div>
            </div>

            <div id="registerForm" style="display: none;">
                <div class="form-group">
                    <label>Uživatelské jméno:</label>
                    <input type="text" id="registerUsername" placeholder="Vymysli si jméno">
                </div>
                <div class="form-group">
                    <label>4místné heslo:</label>
                    <input type="password" id="registerPassword" placeholder="1234" maxlength="4">
                </div>
                <button class="btn" onclick="register()">Zaregistrovat se</button>
                
                <div class="toggle-auth">
                    Máš již účet? <a onclick="toggleAuth()">Přihláš se</a>
                </div>
            </div>
        </div>
    </div>

    <!-- Chat Interface -->
    <div id="chatContainer" class="chat-interface">
        <div class="top-bar">
            <div class="user-info">Přihlášen(a) jako: <span id="currentUser"></span></div>
            <button class="logout-btn" onclick="logout()">Odhlásit se</button>
        </div>

        <div class="chat-main">
            <!-- Sidebar -->
            <div class="sidebar">
                <div class="sidebar-section">
                    <h3>Přidat kontakt</h3>
                    <div class="add-contact">
                        <input type="text" id="contactUsername" placeholder="Uživatelské jméno">
                        <button onclick="addContact()">+</button>
                    </div>
                </div>

                <div class="sidebar-section">
                    <h3>Moje kontakty</h3>
                </div>

                <div class="contacts-list" id="contactsList">
                    <!-- Kontakty se načítají JavaScriptem -->
                </div>
            </div>

            <!-- Chat area -->
            <div class="chat-area">
                <div class="chat-header empty" id="chatHeaderEmpty">Vyber kontakt nebo přidej nový</div>
                <div class="chat-header" id="chatHeader" style="display: none;">Rozhovor s: <span id="chatWith"></span></div>
                
                <div id="emptyChatState" class="empty-chat">
                    Vyber kontakt z levé strany
                </div>

                <div id="messagesArea" style="display: none; flex: 1; display: flex; flex-direction: column;">
                    <div class="messages" id="messagesList"></div>
                    
                    <div class="input-area">
                        <input type="text" id="messageInput" placeholder="Napiš zprávu..." onkeypress="handleKeyPress(event)">
                        <button onclick="sendMessage()">Poslat</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let currentContact = null;

        async function login() {
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;

            if (!username || !password) {
                showError('Vyplň uživatelské jméno a heslo!');
                return;
            }

            if (password.length !== 4 || isNaN(password)) {
                showError('Heslo musí být přesně 4 číslice!');
                return;
            }

            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                currentUser = username;
                showChat();
            } else {
                showError(data.message);
            }
        }

        async function register() {
            const username = document.getElementById('registerUsername').value;
            const password = document.getElementById('registerPassword').value;

            if (!username || !password) {
                showError('Vyplň uživatelské jméno a heslo!');
                return;
            }

            if (password.length !== 4 || isNaN(password)) {
                showError('Heslo musí být přesně 4 číslice!');
                return;
            }

            const response = await fetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                showSuccess('Účet byl vytvořen! Teď se přihláš.');
                toggleAuth();
            } else {
                showError(data.message);
            }
        }

        async function addContact() {
            const contactUsername = document.getElementById('contactUsername').value;

            if (!contactUsername) {
                showError('Zadej uživatelské jméno kontaktu!');
                return;
            }

            const response = await fetch('/add_contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contact: contactUsername })
            });

            const data = await response.json();

            if (data.success) {
                document.getElementById('contactUsername').value = '';
                loadContacts();
            } else {
                showError(data.message);
            }
        }

        async function loadContacts() {
            const response = await fetch('/get_contacts');
            const data = await response.json();

            const list = document.getElementById('contactsList');
            list.innerHTML = data.contacts.map(contact => `
                <div class="contact" onclick="selectContact('${contact}')" id="contact-${contact}">
                    <div class="contact-name">${contact}</div>
                    <button class="contact-remove" onclick="removeContact('${contact}', event)">Odebrat</button>
                </div>
            `).join('');
        }

        async function selectContact(contact) {
            currentContact = contact;

            // Update UI
            document.querySelectorAll('.contact').forEach(el => el.classList.remove('active'));
            document.getElementById(`contact-${contact}`).classList.add('active');

            document.getElementById('emptyChatState').style.display = 'none';
            document.getElementById('messagesArea').style.display = 'flex';
            document.getElementById('chatHeader').style.display = 'block';
            document.getElementById('chatWith').textContent = contact;

            loadMessages();
        }

        async function loadMessages() {
            const response = await fetch(`/get_messages?contact=${currentContact}`);
            const data = await response.json();

            const list = document.getElementById('messagesList');
            list.innerHTML = data.messages.map(msg => `
                <div class="message ${msg.sender === currentUser ? 'sent' : 'received'}">
                    <div>
                        <div class="message-text">${msg.text}</div>
                        <div class="message-time">${msg.time}</div>
                    </div>
                </div>
            `).join('');

            list.scrollTop = list.scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const text = input.value.trim();

            if (!text || !currentContact) return;

            const response = await fetch('/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipient: currentContact, text: text })
            });

            const data = await response.json();

            if (data.success) {
                input.value = '';
                loadMessages();
            } else {
                showError(data.message);
            }
        }

        async function removeContact(contact, event) {
            event.stopPropagation();

            const response = await fetch('/remove_contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contact: contact })
            });

            const data = await response.json();

            if (data.success) {
                loadContacts();
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function showChat() {
            document.getElementById('loginContainer').style.display = 'none';
            document.getElementById('chatContainer').classList.add('active');
            document.getElementById('currentUser').textContent = currentUser;
            loadContacts();

            // Načítání zpráv každou sekundu
            setInterval(() => {
                if (currentContact) {
                    loadMessages();
                }
            }, 2000);
        }

        function logout() {
            fetch('/logout', { method: 'POST' });
            currentUser = null;
            currentContact = null;
            document.getElementById('loginContainer').style.display = 'flex';
            document.getElementById('chatContainer').classList.remove('active');
            clearForms();
        }

        function toggleAuth() {
            const loginForm = document.getElementById('loginForm');
            const registerForm = document.getElementById('registerForm');
            const title = document.getElementById('authTitle');

            if (loginForm.style.display !== 'none') {
                loginForm.style.display = 'none';
                registerForm.style.display = 'block';
                title.textContent = 'Registrace';
            } else {
                loginForm.style.display = 'block';
                registerForm.style.display = 'none';
                title.textContent = 'Přihlášení';
            }
            clearForms();
        }

        function clearForms() {
            document.getElementById('loginUsername').value = '';
            document.getElementById('loginPassword').value = '';
            document.getElementById('registerUsername').value = '';
            document.getElementById('registerPassword').value = '';
            document.getElementById('errorMsg').style.display = 'none';
            document.getElementById('successMsg').style.display = 'none';
        }

        function showError(message) {
            const err = document.getElementById('errorMsg');
            err.textContent = message;
            err.style.display = 'block';
        }

        function showSuccess(message) {
            const succ = document.getElementById('successMsg');
            succ.textContent = message;
            succ.style.display = 'block';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template('index.html') if os.path.exists('templates/index.html') else HTML_TEMPLATE

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Vyplň všechna pole!'})

    if not password.isdigit() or len(password) != 4:
        return jsonify({'success': False, 'message': 'Heslo musí být přesně 4 číslice!'})

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        password_hash = hash_password(password)
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                 (username, password_hash))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Registrace úspěšná!'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Uživatel již existuje!'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()

    if not result or not verify_password(password, result[0]):
        return jsonify({'success': False, 'message': 'Chybné uživatelské jméno nebo heslo!'})

    session['user'] = username
    return jsonify({'success': True})

@app.route('/logout', methods=['POST'])
def logout_user():
    session.clear()
    return jsonify({'success': True})

@app.route('/add_contact', methods=['POST'])
def add_contact():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Nejprve se přihláš!'})

    data = request.json
    contact = data.get('contact', '').strip()

    if not contact:
        return jsonify({'success': False, 'message': 'Zadej uživatelské jméno!'})

    if contact not in users_db:
        return jsonify({'success': False, 'message': 'Uživatel neexistuje!'})

    if contact == session['user']:
        return jsonify({'success': False, 'message': 'Nemůžeš přidat sám sebe!'})

    user = session['user']
    if 'contacts' not in session:
        session['contacts'] = []

    if contact not in session['contacts']:
        session['contacts'].append(contact)
        session.modified = True

    return jsonify({'success': True})

@app.route('/remove_contact', methods=['POST'])
def remove_contact():
    if 'user' not in session:
        return jsonify({'success': False})

    data = request.json
    contact = data.get('contact')

    if 'contacts' in session and contact in session['contacts']:
        session['contacts'].remove(contact)
        session.modified = True

    return jsonify({'success': True})

@app.route('/get_contacts')
def get_contacts():
    if 'user' not in session:
        return jsonify({'contacts': []})

    contacts = session.get('contacts', [])
    return jsonify({'contacts': contacts})

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Nejprve se přihláš!'})

    data = request.json
    sender = session['user']
    recipient = data.get('recipient')
    text = data.get('text', '').strip()

    if not text or not recipient:
        return jsonify({'success': False, 'message': 'Neplatná zpráva!'})

    # Vytvoření unikátního ID konverzace
    conv_id = tuple(sorted([sender, recipient]))
    conv_key = '_'.join(conv_id)

    if conv_key not in conversations:
        conversations[conv_key] = {
            'users': list(conv_id),
            'messages': []
        }

    timestamp = datetime.now().strftime('%H:%M')
    conversations[conv_key]['messages'].append({
        'sender': sender,
        'text': text,
        'time': timestamp
    })

    return jsonify({'success': True})

@app.route('/get_messages')
def get_messages():
    if 'user' not in session:
        return jsonify({'messages': []})

    user = session['user']
    contact = request.args.get('contact')

    if not contact:
        return jsonify({'messages': []})

    conv_id = tuple(sorted([user, contact]))
    conv_key = '_'.join(conv_id)

    messages = conversations.get(conv_key, {}).get('messages', [])
    return jsonify({'messages': messages})

if __name__ == '__main__':
    # Vytvoření templates složky
    os.makedirs('templates', exist_ok=True)
    
    # Uložení HTML šablony
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)

    print("=" * 50)
    print("PRIVÁTNÍ CHAT APLIKACE")
    print("=" * 50)
    print("\n✅ Server spuštěn!")
    print("🌐 Otevři: http://localhost:5000")
    print("\n📝 Jak to funguje:")
    print("1. Registruj se s 4místným heslem")
    print("2. Přihláš se")
    print("3. Přidej kontakt (uživatelské jméno)")
    print("4. Piš si s ním!")
    print("\n💡 Každý uživatel vidí jen své chaty!")
    print("=" * 50)

    app.run(debug=True, port=5000)
