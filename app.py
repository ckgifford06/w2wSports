from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import pytz
import NBArating
import NFLrating
import NHLrating
import MLBrating
import smtplib
from email.mime.text import MIMEText
import sqlite3
import os

app = Flask(__name__)

DB_PATH = "emails.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (
                    email TEXT PRIMARY KEY,
                    verified INTEGER DEFAULT 0
                )''')
    conn.commit()
    conn.close()

init_db()

# Define sports and API endpoints
sports = {
    "nba": {"name": "NBA", "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"},
    "nfl": {"name": "NFL", "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"},
    "nhl": {"name": "NHL", "url": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"},
    "mlb": {"name": "MLB", "url": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"}
}

def calculate_score(home, away, league):
    if league == "NBA":
        return NBArating.calculate_score(home, away)
    elif league == "NFL":
        return NFLrating.calculate_score(home, away)
    elif league == "NHL":
        return NHLrating.calculate_score(home, away)
    elif league == "MLB":
        return MLBrating.calculate_score(home, away)
    else:
        return 0

def rivalryMatchup(home, away, league):
    if league == "NBA":
        return (NBArating.rivalry(home, away) > 5)
    elif league == "NFL":
        return (NFLrating.rivalry(home, away) > 5)
    elif league == "NHL":
        return (NHLrating.rivalry(home, away) > 5)
    elif league == "MLB":
        return (MLBrating.rivalry(home, away) > 5)
    else:
        return False


@app.route('/')
def index():
    selected_league = request.args.get("league", "all")

    timezone_str = request.args.get("tz", "US/Eastern")
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone("US/Eastern")

    today = datetime.now(local_tz).strftime("%Y%m%d")
    all_games = []

    for key, sport in sports.items():

        if selected_league != "all" and sport["name"].lower() != selected_league.lower():
            continue

        try:
            response = requests.get(sport["url"], params={"dates": today})
            data = response.json()

            for event in data.get("events", []):
                competition = event["competitions"][0]
                competitors = competition["competitors"]

                home_abbr = f"{competitors[0]['team']['abbreviation']}_{sport['name']}"
                away_abbr = f"{competitors[1]['team']['abbreviation']}_{sport['name']}"
                home_name = competitors[0]['team']['displayName']
                away_name = competitors[1]['team']['displayName']

                try:
                    game_datetime_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    game_datetime_local = game_datetime_utc.astimezone(local_tz)
                    game_time = game_datetime_local.strftime("%I:%M %p").lstrip("0")
                except:
                    game_time = "TBD"

                status = competition.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
                home_score = competitors[0].get("score", "0")
                away_score = competitors[1].get("score", "0")

                if status == "STATUS_IN_PROGRESS":
                    live_score = f"Live score: {home_score} - {away_score}"
                elif status == "STATUS_FINAL":
                    live_score = f"Final score: {home_score} - {away_score}"
                else:
                    live_score = "Live score: Not Started"

                odds_info = competition.get("odds", [])
                favored_display = "No moneyline"
                spread_display = "No spread"

                rivalInfo = ""
                try:
                    score = calculate_score(home_abbr, away_abbr, sport["name"])
                    if rivalryMatchup(home_abbr, away_abbr, sport["name"]):
                        rivalInfo = "Rivalry Matchup"
                except:
                    score = 0

                try:
                    broadcasts = competition.get("broadcasts", [])
                    geo_broadcasts = competition.get("geoBroadcasts", [])
                    networks = []
                    for b in broadcasts:
                        names = b.get("names", [])
                        if names:
                            networks.extend(names)
                    for gb in geo_broadcasts:
                        if gb.get("media") and gb["media"].get("shortName"):
                            networks.append(gb["media"]["shortName"])
                    where_to_watch = ", ".join(sorted(set(networks))) if networks else "Coming soon..."
                except:
                    where_to_watch = "Coming soon..."

                all_games.append({
                    "matchup": f"{home_name} vs {away_name}",
                    "league": sport["name"],
                    "score": score,
                    "description": rivalInfo,
                    "time": game_time,
                    "favored": favored_display,
                    "favored_spread": spread_display,
                    "where_to_watch": where_to_watch,
                    "live_score": live_score
                })

        except Exception as e:
            print(f"Error fetching {sport['name']}: {e}", flush=True)
            continue

    filtered_ranked = sorted(all_games, key=lambda x: x["score"], reverse=True)[:10]

    return render_template("index.html", matchups=filtered_ranked, selected_league=selected_league)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/formula")
def formula():
    return render_template("formula.html")

@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email")
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO subscribers (email) VALUES (?)", (email,))
    conn.commit()
    conn.close()

    send_verification_email(email)
    return "Verification email sent! Please check your inbox."

def send_verification_email(email):
    verify_link = f"https://yourdomain.com/verify?email={email}"
    msg = MIMEText(f"Click this link to verify your subscription:\n\n{verify_link}")
    msg["Subject"] = "Confirm your subscription"
    msg["From"] = "you@yourdomain.com"
    msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"))
        server.send_message(msg)

@app.route("/verify")
def verify():
    email = request.args.get("email")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE subscribers SET verified = 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return f"Thanks {email}, you’re verified!"

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
