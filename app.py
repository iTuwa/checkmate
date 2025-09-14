from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime
import os
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Users ---
USERS = {
    "tuwa": "tuwaspec1",
    "mercy": "primrose"
}

# --- Letters Dictionary ---
letters = {
    "sad": [
        "I don't think you know it but I really like listening to you. Can you text me please. 💖",
        "If you ever need a safe place to land, I've got room.",
        "Even the darkest night will end and the sun will rise. You're not alone.",
        "Tough times never last, but tough people do. You're tougher than you think."
    ],
    "miss": [
        "I miss you too! You're always on my mind, and I can't wait till we talk or hang out again. 💌",
        "If you ever need someone in your corner... I know a guy.",
        
        
    ],
    "bored": [
        "Here's a tiny mission: count 5 things you love about yourself. Or... message me 😉",
        "Boredom is just the universe nudging you to create something new!",
        "Try something you've never done before, even if it's just a silly dance.",
        "Bored? Write a letter to your future self or doodle your dreams."
    ],
    "happy": [
        "Yay! I'm glad you're smiling. You deserve all the joy in the world 🌞💫",
        "Happiness looks so good on you!",
        "Keep shining, your joy is contagious.",
        "Celebrate every little win. You earned it!"
    ],
    "growth": [
        "Growth is never by mere chance; it is the result of forces working together.",
        "The only way to grow is to step outside your comfort zone.",
        "Every day is a chance to become a better version of yourself.",
        "Growth is painful. Change is painful. But nothing is as painful as staying stuck somewhere you don't belong."
    ],
    "consistency": [
        "Small steps, every day. That's how mountains move.",
        "Growth is not always visible, but it is happening when you show up.",
        "Mastery is built on the foundation of consistency.",
        "Be loyal to your future, not your comfort zone."
    ],
    "extraordinary": [
        "Don't be afraid to be extraordinary. The world needs your magic.",
        "Ordinary people believe only in the possible. Extraordinary people visualize not what is possible or probable, but rather what is impossible.",
        "You were born to stand out, not fit in.",
        "You don't wake up extraordinary. You grow into it with every choice you make."
    ]
}

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    receiver TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

# --- Routes ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/open/<mood>')
def open_letter(mood):
    messages = letters.get(mood)
    if isinstance(messages, list):
        message = random.choice(messages)
    else:
        message = messages or "No letter found for this mood 😢"
    return render_template('letter.html', mood=mood, message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USERS and USERS[username] == password:
            session["username"] = username
            return redirect(url_for("chat"))
        return render_template("login.html", error="Invalid login")
    return render_template("login.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "username" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        msg = request.form["message"]
        current_user = session["username"]
        other_user = "Pullie" if current_user == "tuwa" else "tuwa"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect("messages.db")
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender, receiver, content, timestamp) VALUES (?, ?, ?, ?)",
                  (current_user, other_user, msg, timestamp))
        conn.commit()
        conn.close()
        return redirect(url_for("chat"))
    
    return render_template("chat.html", current_user=session["username"])

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

@app.route("/messages")
def get_messages():
    if "username" not in session:
        return jsonify({"success": False})
    
    current_user = session["username"]
    other_user = "Pullie" if current_user == "tuwa" else "tuwa"
    since_id = request.args.get('since', default=0, type=int)

    conn = sqlite3.connect('messages.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT id, sender, receiver, content, timestamp 
                 FROM messages 
                 WHERE ((sender=? AND receiver=?) OR (sender=? AND receiver=?))
                 AND id > ?
                 ORDER BY id ASC''',
              (current_user, other_user, other_user, current_user, since_id))
    messages = [{
        "id": row["id"],
        "sender": row["sender"],
        "recipient": row["receiver"],
        "content": row["content"],
        "timestamp": row["timestamp"]
    } for row in c.fetchall()]
    conn.close()
    return jsonify({
        "success": True,
        "messages": messages
    })

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    content = data.get('content')
    sender = session.get('username')
    recipient = "Pullie" if sender == "tuwa" else "tuwa"
    
    if not sender or not content:
        return jsonify(success=False, error="Missing sender or content")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, receiver, content, timestamp) VALUES (?, ?, ?, ?)",
              (sender, recipient, content, timestamp))
    conn.commit()
    conn.close()
    return jsonify(success=True)

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Created templates directory - please add your template files")

    app.run(debug=True)

