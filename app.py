
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_ai_panel'

def get_db():
    conn = sqlite3.connect('ai_panel.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    username TEXT UNIQUE, 
                    password TEXT)''')
    # Settings
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY, 
                    api_key TEXT, 
                    model TEXT, 
                    memory INTEGER, 
                    temperature REAL, 
                    instruction TEXT, 
                    base_context TEXT)''')
    # Conversations
    c.execute('''CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    user_id INTEGER, 
                    title TEXT, 
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    # Messages
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    conversation_id INTEGER, 
                    role TEXT, 
                    content TEXT, 
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('index.html', logged_in=False)
    return render_template('index.html', logged_in=True, username=session['username'])

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    action = data.get('action')
    username = data.get('username')
    password = data.get('password')
    conn = get_db()
    c = conn.cursor()

    if action == 'register':
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, generate_password_hash(password)))
            user_id = c.lastrowid
            # Default settings
            c.execute("INSERT INTO settings (user_id, api_key, model, memory, temperature, instruction, base_context) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (user_id, "sk-gJI1851Li5z70HphGjIjkxjNGjNGMIGdZ1y3Y4NtI11SvUWa", "gpt-4o", 5, 0.7, "", ""))
            conn.commit()
            session['user_id'] = user_id
            session['username'] = username
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'error': 'نام کاربری تکراری است.'})
    
    elif action == 'login':
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'نام کاربری یا رمز عبور اشتباه است.'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute("SELECT * FROM settings WHERE user_id = ?", (session['user_id'],))
        s = c.fetchone()
        return jsonify(dict(s) if s else {})
        
    if request.method == 'POST':
        data = request.json
        c.execute('''UPDATE settings SET api_key=?, model=?, memory=?, temperature=?, instruction=?, base_context=? WHERE user_id=?''',
                  (data.get('api_key'), data.get('model'), data.get('memory'), data.get('temperature'), data.get('instruction'), data.get('base_context'), session['user_id']))
        conn.commit()
        return jsonify({'success': True})

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    user_message = request.form.get('message')
    conv_id = request.form.get('conversation_id')
    file = request.files.get('file')
    
    conn = get_db()
    c = conn.cursor()
    
    # Get Settings
    c.execute("SELECT * FROM settings WHERE user_id = ?", (session['user_id'],))
    settings = c.fetchone()
    if not settings: return jsonify({'error': 'Settings not found'}), 400
    
    # Create conversation if not exists
    if not conv_id or conv_id == 'null' or conv_id == '':
        title = user_message[:30] + "..." if len(user_message) > 30 else user_message
        c.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?)", (session['user_id'], title))
        conv_id = c.lastrowid
    
    # Process File
    file_content = ""
    if file:
        file_content = f"\n\n[محتوای فایل ضمیمه شده:]\n{file.read().decode('utf-8', errors='ignore')[:5000]}"
    
    full_user_message = user_message + file_content
    
    # Save User Message
    c.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", (conv_id, 'user', full_user_message))
    
    # Build Messages Payload for API
    messages_payload = []
    if settings['instruction']:
        messages_payload.append({"role": "system", "content": settings['instruction']})
    if settings['base_context']:
        messages_payload.append({"role": "system", "content": f"Base Context:\n{settings['base_context']}"})
        
    # Get history based on memory limit
    memory_limit = int(settings['memory']) * 2 # Each pair is 2 messages (user, assistant)
    c.execute("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?", (conv_id, memory_limit))
    history = c.fetchall()
    for row in reversed(history):
        messages_payload.append({"role": row['role'], "content": row['content']})
        
    # API Call
    try:
        client = OpenAI(base_url="https://api.gapgpt.app/v1", api_key=settings['api_key'])
        response = client.chat.completions.create(
            model=settings['model'],
            messages=messages_payload,
            temperature=float(settings['temperature'])
        )
        ai_response = response.choices[0].message.content
        
        # Save AI Response
        c.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", (conv_id, 'assistant', ai_response))
        conn.commit()
        
        return jsonify({'success': True, 'response': ai_response, 'conversation_id': conv_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def history():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
    convs = [dict(row) for row in c.fetchall()]
    return jsonify({'conversations': convs})

@app.route('/conversation/<int:conv_id>', methods=['GET'])
def get_conversation(conv_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC", (conv_id,))
    msgs = [dict(row) for row in c.fetchall()]
    return jsonify({'messages': msgs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8282, debug=True)
