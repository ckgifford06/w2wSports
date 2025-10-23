from flask import Flask, render_template, request
import requests
from datetime import datetime
import pytz
import NBArating
import NFLrating
import NHLrating
import MLBrating

app = Flask(__name__)

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
        return false

@app.route('/')
def index():
    # Get timezone from user (defaults to US/Eastern)
    timezone_str = request.args.get("tz", "US/Eastern")
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone("US/Eastern")

    today = datetime.now(local_tz).strftime("%Y%m%d")
    all_games = []

    # Fetch matchups from all sports
    for key, sport in sports.items():
        try:
            print(f"Fetching {sport['name']} games...", flush=True)
            response = requests.get(sport["url"], params={"dates": today})
            data = response.json()

            for event in data.get("events", []):
                competition = event["competitions"][0]
                competitors = competition["competitors"]

                home_abbr = f"{competitors[0]['team']['abbreviation']}_{sport['name']}"
                away_abbr = f"{competitors[1]['team']['abbreviation']}_{sport['name']}"

                home_name = competitors[0]['team']['displayName']
                away_name = competitors[1]['team']['displayName']

                # --- 🕒 Get Game Time ---
                try:
                    game_datetime_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    game_datetime_local = game_datetime_utc.astimezone(local_tz)
                    game_time = game_datetime_local.strftime("%I:%M %p").lstrip("0")
                except Exception:
                    game_time = "TBD"

                # --- 📊 Odds & Spread ---
                favored_display = "No odds"
                spread_display = "No spread"

                odds_info = competition.get("odds", [])
                if odds_info:
                    odds_item = odds_info[0]

                    # Handle NBA moneylines specifically
                    if sport["name"] == "NBA":
                        moneyline = odds_item.get("moneyline", {})
                        home_ml = moneyline.get("home")
                        away_ml = moneyline.get("away")
                        
                        # If they exist as dicts, extract the numeric value
                        if isinstance(home_ml, dict):
                            home_ml = home_ml.get("current")
                        if isinstance(away_ml, dict):
                            away_ml = away_ml.get("current")
                        
                        # Now compare safely
                        if home_ml is not None and away_ml is not None:
                            if home_ml < away_ml:
                                favored_display = f"{home_name} {home_ml}"
                            else:
                                favored_display = f"{away_name} {away_ml}"

                        spread = odds_item.get("spread")
                        if spread is not None:
                            favored_team = home_name if spread < 0 else away_name
                            spread_display = f"{favored_team} {abs(spread)}"

                    else:
                        # For other leagues: use 'details' and 'spread'
                        details = odds_item.get("details", "")
                        spread = odds_item.get("spread", None)
                        if details:
                            favored_display = details
                        if details and spread is not None:
                            favored_team = details.split(" ")[0]
                            spread_display = f"{favored_team} {spread}"

                # --- 🔢 Safe scoring ---
                rivalInfo = ""
                try:
                    score = calculate_score(home_abbr, away_abbr, sport["name"])
                    if rivalryMatchup(home_abbr, away_abbr, sport["name"]):
                        rivalInfo = " (Rivalry Matchup)"
                except Exception as e:
                    print(f"Error scoring {home_abbr} vs {away_abbr}: {e}", flush=True)
                    score = 0

                all_games.append({
                    "matchup": f"{home_name} vs {away_name}",
                    "league": sport["name"],
                    "score": score,
                    "description": rivalInfo,
                    "time": game_time,
                    "favored": favored_display,
                    "favored_spread": spread_display
                })

        except Exception as e:
            print(f"Error fetching {sport['name']}: {e}", flush=True)
            continue

    # Sort and display top 10
    print(f"Fetched {len(all_games)} total games", flush=True)
    top_10_games = sorted(all_games, key=lambda x: x["score"], reverse=True)[:10]

    print("Top Games (for debugging):", flush=True)
    for game in top_10_games:
        print(f"  [{game['league']}] {game['matchup']} — Score: {game['score']}", flush=True)

    return render_template('index.html', matchups=top_10_games)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
