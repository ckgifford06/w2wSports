from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import pytz
import NBArating
import NFLrating
import NHLrating
import MLBrating
import CFBrating
import smtplib
from email.mime.text import MIMEText
import sqlite3
import os

app = Flask(__name__)

DB_PATH = "emails.db"

# In progress...
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
    "mlb": {"name": "MLB", "url": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"},
    "cfb": {"name": "CFB", "url": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"}
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
    elif league == "CFB":
        return CFBrating.calculate_score(home, away)
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
    elif league == "CFB":
        return (CFBrating.rivalry(home, away) > 5)
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

                home_team = competitors[0]["team"]
                away_team = competitors[1]["team"]

                if home_team["abbreviation"] == "TBD" or away_team["abbreviation"] == "TBD":
                    continue

                try:
                    game_datetime_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    game_datetime_local = game_datetime_utc.astimezone(local_tz)
                    
                    # STRICT DATE FILTER - Only include games that match the exact requested date
                    requested_date = datetime.strptime(date, "%Y%m%d").date()
                    if game_datetime_local.date() != requested_date:
                        continue  # Skip games from different dates
                    
                    game_time = game_datetime_local.strftime("%I:%M %p").lstrip("0")
                except:
                    continue

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

                # NHL
                if sport["name"] == "NHL" and odds_info:
                    odds_item = odds_info[0]  
                    details = odds_item.get("details", "")
                    spread = odds_item.get("spread", None)
                
                    away_team = odds_item.get("awayTeamOdds", {}).get("team", {}).get("displayName", "Away")
                    home_team = odds_item.get("homeTeamOdds", {}).get("team", {}).get("displayName", "Home")
                
                    home_ml = odds_item.get("homeTeamOdds", {}).get("moneyLine")
                    away_ml = odds_item.get("awayTeamOdds", {}).get("moneyLine")
                
                    if home_ml is not None and away_ml is not None:
                        if home_ml < away_ml:
                            favored_display = f"{home_team} {home_ml}"
                        else:
                            favored_display = f"{away_team} {away_ml}"
                    elif details:
                        favored_display = details
                
                    if spread is not None:
                        if spread > 0:
                            spread = -abs(spread)
                        if home_ml is not None and away_ml is not None:
                            favored_team = home_team if home_ml < away_ml else away_team
                            spread_display = f"{favored_team} {spread:+}"
                        elif details:
                            favored_team = details.split(" ")[0]
                            spread_display = f"{favored_team} {spread:+}"
                            
                    if status == "STATUS_IN_PROGRESS" or status == "STATUS_FINAL":
                        favored_display = "No odds available - Game in Progress"
                        spread_display = "No odds available - Game in Progress"
                
                # NBA & NFL
                elif sport["name"] in ["NBA", "NFL"] and odds_info:
                    try:
                        spread_display = "No spread"
                
                        for odds_item in odds_info:
                            away_odds = odds_item.get("awayTeamOdds", {})
                            home_odds = odds_item.get("homeTeamOdds", {})
                
                            if away_odds.get("favorite"):
                                fav_team = away_odds.get("team", {}).get("displayName", "Away")
                                spread_val = odds_item.get("spread")
                                if spread_val:
                                    spread_display = f"{fav_team} -{abs(spread_val)}"
                                    break
                
                            elif home_odds.get("favorite"):
                                fav_team = home_odds.get("team", {}).get("displayName", "Home")
                                spread_val = odds_item.get("spread")
                                if spread_val:
                                    spread_display = f"{fav_team} -{abs(spread_val)}"
                                    break
                
                            if odds_item.get("details"):
                                spread_display = odds_item["details"]
                                break
                
                        # Determine moneyline favorite
                        moneyline_data = competition.get("odds", [{}])[0].get("moneyline", {})

                        home_ml = moneyline_data.get("home", {}).get("close", {}).get("odds")
                        away_ml = moneyline_data.get("away", {}).get("close", {}).get("odds")
                        
                        if home_ml and away_ml:
                            # convert strings like "+124" to ints for comparison
                            home_ml_val = int(home_ml)
                            away_ml_val = int(away_ml)
                        
                            if home_ml_val < away_ml_val:
                                favored_display = f"{home_name} {home_ml}"
                            else:
                                favored_display = f"{away_name} {away_ml}"
                        else:
                            favored_display = "No moneyline"

                        if status == "STATUS_IN_PROGRESS" or status == "STATUS_FINAL":
                            favored_display = "No odds available - Game in Progress"
                            spread_display = "No odds available - Game in Progress"
                
                    except Exception:
                        favored_display = "No odds"
                        spread_display = "No spread"

                # CFB (College Football)
                elif sport["name"] == "CFB" and odds_info:
                    try:
                        odds_item = odds_info[0]
                        home_odds = odds_item.get("homeTeamOdds", {})
                        away_odds = odds_item.get("awayTeamOdds", {})
                
                        home_ml = home_odds.get("moneyLine")
                        away_ml = away_odds.get("moneyLine")
                        spread_val = odds_item.get("spread")
                        details = odds_item.get("details")
                
                        # ----- Moneyline -----
                        moneyline = competition.get("odds", [{}])[0].get("moneyline", {})
                        home_ml = moneyline.get("home", {}).get("close", {}).get("odds")
                        away_ml = moneyline.get("away", {}).get("close", {}).get("odds")
                        
                        if home_ml and away_ml:
                            if int(home_ml) < int(away_ml):
                                favored_display = f"{home_name} {home_ml}"
                            else:
                                favored_display = f"{away_name} {away_ml}"
                        else:
                            favored_display = "No moneyline"
                        
                        spread = competition.get("odds", [{}])[0].get("pointSpread", {})
                        home_spread = spread.get("home", {}).get("close", {}).get("line")
                        away_spread = spread.get("away", {}).get("close", {}).get("line")
                        
                        if home_spread and away_spread:
                            if home_ml and away_ml:
                                favored_team = home_name if int(home_ml) < int(away_ml) else away_name
                                spread_display = f"{favored_team} {home_spread}"
                            else:
                                # fallback to home spread if no moneyline
                                spread_display = f"{home_name} {home_spread}"
                        else:
                            spread_display = "No spread"

                        if status == "STATUS_IN_PROGRESS" or status == "STATUS_FINAL":
                            favored_display = "No odds available - Game in Progress"
                            spread_display = "No odds available - Game in Progress"
                    except:
                        favored_display = "No moneyline"
                        spread_display = "No spread"

                rivalInfo = ""
                try:
                    score = calculate_score(home_abbr, away_abbr, sport["name"])
                    if rivalryMatchup(home_abbr, away_abbr, sport["name"]):
                        rivalInfo = "Rivalry Matchup"
                except:
                    score = 0
                    rivalInfo = ""
                    
                if status == "STATUS_FINAL":
                    try:
                        if game_datetime_local.date() < datetime.now(local_tz).date():
                            continue 
                    except:
                        pass
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


@app.route('/api/games/<date>')
def get_games_by_date(date):
    """
    Fetch games for a specific date (format: YYYYMMDD)
    Example: /api/games/20260106
    """
    selected_league = request.args.get("league", "all")
    
    timezone_str = request.args.get("tz", "US/Eastern")
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone("US/Eastern")
    
    all_games = []
    
    for key, sport in sports.items():
        if selected_league != "all" and sport["name"].lower() != selected_league.lower():
            continue
        
        try:
            response = requests.get(sport["url"], params={"dates": date})
            data = response.json()
            
            for event in data.get("events", []):
                competition = event["competitions"][0]
                competitors = competition["competitors"]
                
                home_abbr = f"{competitors[0]['team']['abbreviation']}_{sport['name']}"
                away_abbr = f"{competitors[1]['team']['abbreviation']}_{sport['name']}"
                
                home_name = competitors[0]['team']['displayName']
                away_name = competitors[1]['team']['displayName']
                
                home_team = competitors[0]["team"]
                away_team = competitors[1]["team"]
                
                if home_team["abbreviation"] == "TBD" or away_team["abbreviation"] == "TBD":
                    continue
                
                try:
                    game_datetime_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    game_datetime_local = game_datetime_utc.astimezone(local_tz)
                    game_time = game_datetime_local.strftime("%I:%M %p").lstrip("0")
                except:
                    continue
                
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
                
                # NHL odds parsing
                if sport["name"] == "NHL" and odds_info:
                    odds_item = odds_info[0]  
                    details = odds_item.get("details", "")
                    spread = odds_item.get("spread", None)
                    
                    away_team_odds = odds_item.get("awayTeamOdds", {}).get("team", {}).get("displayName", "Away")
                    home_team_odds = odds_item.get("homeTeamOdds", {}).get("team", {}).get("displayName", "Home")
                    
                    home_ml = odds_item.get("homeTeamOdds", {}).get("moneyLine")
                    away_ml = odds_item.get("awayTeamOdds", {}).get("moneyLine")
                    
                    if home_ml is not None and away_ml is not None:
                        if home_ml < away_ml:
                            favored_display = f"{home_team_odds} {home_ml}"
                        else:
                            favored_display = f"{away_team_odds} {away_ml}"
                    elif details:
                        favored_display = details
                    
                    if spread is not None:
                        if spread > 0:
                            spread = -abs(spread)
                        if home_ml is not None and away_ml is not None:
                            favored_team = home_team_odds if home_ml < away_ml else away_team_odds
                            spread_display = f"{favored_team} {spread:+}"
                        elif details:
                            favored_team = details.split(" ")[0]
                            spread_display = f"{favored_team} {spread:+}"
                    
                    if status == "STATUS_IN_PROGRESS" or status == "STATUS_FINAL":
                        favored_display = "No odds available - Game in Progress"
                        spread_display = "No odds available - Game in Progress"
                
                # NBA & NFL odds parsing
                elif sport["name"] in ["NBA", "NFL"] and odds_info:
                    try:
                        spread_display = "No spread"
                        
                        for odds_item in odds_info:
                            away_odds = odds_item.get("awayTeamOdds", {})
                            home_odds = odds_item.get("homeTeamOdds", {})
                            
                            if away_odds.get("favorite"):
                                fav_team = away_odds.get("team", {}).get("displayName", "Away")
                                spread_val = odds_item.get("spread")
                                if spread_val:
                                    spread_display = f"{fav_team} -{abs(spread_val)}"
                                    break
                            
                            elif home_odds.get("favorite"):
                                fav_team = home_odds.get("team", {}).get("displayName", "Home")
                                spread_val = odds_item.get("spread")
                                if spread_val:
                                    spread_display = f"{fav_team} -{abs(spread_val)}"
                                    break
                            
                            if odds_item.get("details"):
                                spread_display = odds_item["details"]
                                break
                        
                        moneyline_data = competition.get("odds", [{}])[0].get("moneyline", {})
                        home_ml = moneyline_data.get("home", {}).get("close", {}).get("odds")
                        away_ml = moneyline_data.get("away", {}).get("close", {}).get("odds")
                        
                        if home_ml and away_ml:
                            home_ml_val = int(home_ml)
                            away_ml_val = int(away_ml)
                            
                            if home_ml_val < away_ml_val:
                                favored_display = f"{home_name} {home_ml}"
                            else:
                                favored_display = f"{away_name} {away_ml}"
                        else:
                            favored_display = "No moneyline"
                        
                        if status == "STATUS_IN_PROGRESS" or status == "STATUS_FINAL":
                            favored_display = "No odds available - Game in Progress"
                            spread_display = "No odds available - Game in Progress"
                    
                    except Exception:
                        favored_display = "No odds"
                        spread_display = "No spread"
                
                # CFB odds parsing
                elif sport["name"] == "CFB" and odds_info:
                    try:
                        moneyline = competition.get("odds", [{}])[0].get("moneyline", {})
                        home_ml = moneyline.get("home", {}).get("close", {}).get("odds")
                        away_ml = moneyline.get("away", {}).get("close", {}).get("odds")
                        
                        if home_ml and away_ml:
                            if int(home_ml) < int(away_ml):
                                favored_display = f"{home_name} {home_ml}"
                            else:
                                favored_display = f"{away_name} {away_ml}"
                        else:
                            favored_display = "No moneyline"
                        
                        spread = competition.get("odds", [{}])[0].get("pointSpread", {})
                        home_spread = spread.get("home", {}).get("close", {}).get("line")
                        away_spread = spread.get("away", {}).get("close", {}).get("line")
                        
                        if home_spread and away_spread:
                            if home_ml and away_ml:
                                favored_team = home_name if int(home_ml) < int(away_ml) else away_name
                                spread_display = f"{favored_team} {home_spread}"
                            else:
                                spread_display = f"{home_name} {home_spread}"
                        else:
                            spread_display = "No spread"
                        
                        if status == "STATUS_IN_PROGRESS" or status == "STATUS_FINAL":
                            favored_display = "No odds available - Game in Progress"
                            spread_display = "No odds available - Game in Progress"
                    except Exception as e:
                        favored_display = "No moneyline"
                        spread_display = "No spread"
                
                rivalInfo = ""
                try:
                    score = calculate_score(home_abbr, away_abbr, sport["name"])
                    if rivalryMatchup(home_abbr, away_abbr, sport["name"]):
                        rivalInfo = "Rivalry Matchup"
                except:
                    score = 0
                    rivalInfo = ""
                
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
            print(f"Error fetching {sport['name']} for date {date}: {e}", flush=True)
            continue
    
    # Sort and return top 10
    filtered_ranked = sorted(all_games, key=lambda x: x["score"], reverse=True)[:10]
    
    return jsonify({
        "games": filtered_ranked,
        "count": len(filtered_ranked),
        "date": date
    })
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
