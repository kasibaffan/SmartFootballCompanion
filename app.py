from flask import Flask, render_template, request, redirect, url_for, session
import json, os

app = Flask(__name__)
app.secret_key = 'smartfootballsecret'


# ---------- HOME ----------
@app.route('/')
def home():
    return render_template('home.html')


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if os.path.exists('users.json'):
            with open('users.json', 'r') as f:
                users = json.load(f)
        else:
            users = {}

        if username in users:
            return "User already exists! Try logging in."

        users[username] = {'password': password, 'stats': []}

        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

        return redirect(url_for('login'))
    return render_template('register.html')


# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not os.path.exists('users.json'):
            return "No users found. Register first."

        with open('users.json', 'r') as f:
            users = json.load(f)

        if username in users and users[username]['password'] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password."

    return render_template('login.html')


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ---------- HEALTH + INJURY TRACKER ----------
@app.route('/health', methods=['GET', 'POST'])
def health():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            matches = int(request.form['matches'])
            distance = float(request.form['distance'])
            calories = int(request.form['calories'])
            heart_rate = int(request.form['heart_rate'])
            travel = float(request.form['travel'])
            minutes = int(request.form['minutes'])
            challenges = int(request.form['challenges'])
            goals = int(request.form['goals'])
            assists = int(request.form['assists'])

            # Health and Mobility scores
            health_score = min(100, (calories / 50) + (matches * 5) + (heart_rate / 2))
            mobility_score = min(100, (distance * 3) - (travel / 2))

            # Injury Risk Calculation
            injury_risk = (minutes * 0.05) + (challenges * 0.1) - ((goals + assists) * 0.03)
            injury_risk = max(0, min(100, round(injury_risk, 2)))

            if injury_risk < 40:
                risk_level = "🟢 Low"
            elif injury_risk < 70:
                risk_level = "🟡 Moderate"
            else:
                risk_level = "🔴 High"

            # Load users data
            if os.path.exists('users.json'):
                with open('users.json', 'r') as f:
                    users = json.load(f)
            else:
                users = {}

            username = session['user']
            if username not in users:
                users[username] = {}

            if 'stats' not in users[username]:
                users[username]['stats'] = []

            users[username]['stats'].append({
                "matches": matches,
                "distance": distance,
                "calories": calories,
                "heart_rate": heart_rate,
                "travel": travel,
                "minutes": minutes,
                "challenges": challenges,
                "goals": goals,
                "assists": assists,
                "injury_risk": injury_risk,
                "risk_level": risk_level,
                "health_score": round(health_score, 2),
                "mobility_score": round(mobility_score, 2)
            })

            with open('users.json', 'w') as f:
                json.dump(users, f, indent=4)

            return redirect(url_for('dashboard'))

        except Exception as e:
            print("Error:", e)
            return "Error saving stats"

    return render_template('health.html')


# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']

    if not os.path.exists('users.json'):
        return "No data found."

    with open('users.json', 'r') as f:
        users = json.load(f)

    user_data = users.get(username, {})
    stats = user_data.get('stats', [])

    latest = stats[-1] if stats else None
    health_score = latest.get('health_score', 0) if latest else 0
    mobility_score = latest.get('mobility_score', 0) if latest else 0

    if latest:
        avg_performance = (health_score + mobility_score) / 2
        if avg_performance > 80:
            performance_level = "🔥 Excellent"
        elif avg_performance > 50:
            performance_level = "⚡ Good"
        else:
            performance_level = "💤 Needs Improvement"
    else:
        performance_level = "No data yet"

    ai_reviews = []
    suggestion_text = ""
    training_advice = ""

    if latest:
        injury_risk = latest["injury_risk"]
        goals = latest["goals"]
        assists = latest["assists"]
        matches = latest["matches"]
        heart_rate = latest["heart_rate"]
        calories = latest["calories"]
        travel = latest["travel"]

        # ----- PERFORMANCE PREDICTION -----
        performance_score = 50 + (matches * 2) + (goals * 3) + (assists * 2)
        performance_score += (calories / 100)
        performance_score -= (heart_rate - 90) * 0.2
        performance_score -= (travel / 10)
        performance_score = max(0, min(100, round(performance_score, 1)))

        if performance_score > 80:
            suggestion_text = f"🔥 Excellent form! You can perform at {performance_score}% efficiency and potentially score 2–3 goals."
        elif performance_score > 60:
            suggestion_text = f"⚽ Good form! Expect around {performance_score}% match fitness and decent passing accuracy."
        elif performance_score > 40:
            suggestion_text = f"⚠️ Moderate condition ({performance_score}%). Take light training to improve stamina."
        else:
            suggestion_text = f"🩹 Low energy ({performance_score}%). Recovery and rest recommended."

        # ----- TRAINING ADVICE ENGINE -----
        if injury_risk < 40:
            training_advice = "✅ Low injury risk — continue your regular training and focus on endurance drills."
        elif injury_risk < 70:
            training_advice = "🟡 Moderate risk — reduce physical load and emphasize stretching & recovery exercises."
        else:
            training_advice = "🔴 High risk — avoid high-impact drills; prioritize physiotherapy and rest."

        # ----- AI REVIEW LOGIC -----
        if injury_risk > 70:
            ai_reviews.append("⚠️ High injury risk detected — consider rest or lighter sessions.")
        elif injury_risk > 40:
            ai_reviews.append("🟡 Moderate injury risk — focus on recovery and hydration.")
        else:
            ai_reviews.append("✅ Low injury risk — maintain your current performance routine!")

        if goals >= 2:
            ai_reviews.append("⚽ Great goal-scoring performance!")
        if assists >= 2:
            ai_reviews.append("🎯 Excellent playmaking contribution!")

    else:
        performance_score = 0
        suggestion_text = ""
        training_advice = ""

    return render_template(
        'dashboard.html',
        username=username,
        latest=latest,
        stats=stats,
        health_score=health_score,
        mobility_score=mobility_score,
        performance_level=performance_level,
        ai_reviews=ai_reviews,
        performance_score=performance_score,
        suggestion_text=suggestion_text,
        training_advice=training_advice
    )

    


# ---------- ECO TRAVEL ----------
@app.route('/eco', methods=['GET', 'POST'])
def eco():
    carbon_saved = None
    travel_mode = None
    suggestion = None

    if request.method == 'POST':
        try:
            distance = float(request.form.get('distance', 0))

            car_emission = distance * 0.21
            eco_emission = distance * 0.05
            carbon_saved = round(car_emission - eco_emission, 2)

            if distance <= 3:
                travel_mode = "🚶 Walking"
            elif distance <= 8:
                travel_mode = "🚴 Cycling"
            elif distance <= 25:
                travel_mode = "🚌 Public Transport"
            else:
                travel_mode = "🚗 Carpooling / EV"

            suggestion = f"By switching to {travel_mode}, you saved approximately {carbon_saved} kg of CO₂ this week!"
        except:
            suggestion = "Please enter a valid distance!"

    return render_template('eco.html', suggestion=suggestion, carbon_saved=carbon_saved, travel_mode=travel_mode)


# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)
