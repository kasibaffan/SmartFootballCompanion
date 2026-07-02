# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import random
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'nexus_athlete_2025'

DB = 'nexus.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT,
        name TEXT, age INTEGER, position TEXT, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, streak INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY, user_id INTEGER,
        matches INTEGER, distance REAL, calories INTEGER, heart_rate INTEGER,
        travel REAL, minutes INTEGER, challenges INTEGER, goals INTEGER, assists INTEGER,
        timestamp TEXT
    )''')
    conn.commit(); conn.close()

init_db()

# === AI LOGIC ===
def analyze_performance(stats_list):
    if not stats_list: return {}, [], "Beginner", "Start tracking!", "Log your first session."

    latest = stats_list[-1]
    avg_hr = sum(s[3] for s in stats_list) / len(stats_list)
    total_goals = sum(s[7] for s in stats_list)

    score = min(100, int(
        (latest[0] * 5) + (latest[1] * 2) + (latest[2] / 100) + (latest[7] * 10) + (latest[8] * 8)
    ))

    reviews = []
    if latest[3] > 180: reviews.append("High heart rate! Focus on recovery.")
    if latest[1] < 5: reviews.append("Increase distance covered per match.")
    if latest[7] == 0: reviews.append("Time to score! Work on finishing.")

    level = "Rookie" if score < 40 else "Pro" if score < 70 else "Elite" if score < 90 else "Legend"
    advice = random.choice([
        "Add interval sprints to boost stamina.",
        "Focus on core strength for better balance.",
        "Hydrate more — performance starts with recovery."
    ])
    suggestion = f"Score {max(1, 3 - total_goals)} goals this week!"

    return {"score": score}, reviews, level, suggestion, advice

# === ROUTES ===
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = sqlite3.connect(DB).execute(
            "SELECT * FROM users WHERE username=?", (request.form['username'],)
        ).fetchone()
        if user and user[2] == request.form['password']:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/dashboard')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = sqlite3.connect(DB)
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                        (request.form['username'], request.form['password']))
            conn.commit()
            return redirect('/login')
        except: pass
        finally: conn.close()
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/login')
    
    conn = sqlite3.connect(DB)
    stats = conn.execute("SELECT * FROM stats WHERE user_id=? ORDER BY timestamp", 
                        (session['user_id'],)).fetchall()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    
    latest = stats[-1] if stats else None
    perf = analyze_performance(stats) if stats else ({}, [], "Beginner", "", "")
    
    return render_template('dashboard.html',
        username=session['username'],
        stats=stats,
        latest=latest._asdict() if latest else None,
        performance_score=perf[0].get('score', 0),
        ai_reviews=perf[1],
        performance_level=perf[2],
        suggestion_text=perf[3],
        training_advice=perf[4],
        user_level=user[6], user_xp=user[7], streak=user[8]
    )

@app.route('/health', methods=['GET', 'POST'])
def health():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        conn = sqlite3.connect(DB)
        conn.execute("""INSERT INTO stats (user_id, matches, distance, calories, heart_rate, travel,
                        minutes, challenges, goals, assists, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session['user_id'], *(request.form.get(k) for k in [
                'matches','distance','calories','heart_rate','travel',
                'minutes','challenges','goals','assists'
            ]), datetime.now().isoformat()))
        conn.commit(); conn.close()
        return redirect('/dashboard')
    return render_template('health.html')

@app.route('/eco', methods=['GET', 'POST'])
def eco():
    if 'user_id' not in session: return redirect('/login')
    result = None
    if request.method == 'POST':
        mode = request.form['mode']
        dist = float(request.form['distance'])
        co2 = {'car': 0.4, 'bus': 0.1, 'bike': 0, 'walk': 0}[mode] * dist
        time = dist / {'car': 50, 'bus': 30, 'bike': 15, 'walk': 5}[mode]
        result = {
            'city': request.form['city'],
            'temp': random.randint(15, 32),
            'condition': random.choice(['Sunny', 'Cloudy', 'Rainy']),
            'time': round(time, 1),
            'co2': round(co2, 2),
            'fuel_cost': round(dist * 0.12 * 80, 0) if mode == 'car' else 0,
            'eco_tip': "Go green: Bike or walk when possible!" if mode in ['car','bus'] else "Great choice! Zero emissions!",
            'weather_tip': "Wear light clothes!" if result['temp'] > 28 else "Carry a jacket.",
            'mode': mode
        }
    return render_template('eco.html', result=result)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect('/login')
    conn = sqlite3.connect(DB)
    user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    if request.method == 'POST':
        conn.execute("UPDATE users SET name=?, age=?, position=? WHERE id=?",
                    (request.form['name'], request.form['age'], request.form['position'], session['user_id']))
        conn.commit()
    conn.close()
    return render_template('profile.html', user={ 'profile': { 'name': user[3], 'age': user[4], 'position': user[5] }})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)