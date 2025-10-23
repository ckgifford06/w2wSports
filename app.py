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
                competitors = event["competitions"][0]["competitors"]
                home_abbr = f"{competitors[0]['team']['abbreviation']}_{sport['name']}"
                away_abbr = f"{competitors[1]['team']['abbreviation']}_{sport['name']}"

                home_name = competitors[0]['team']['displayName']
                away_name = competitors[1]['team']['displayName']

                odds_info = competition.get("odds", [])
                favored_team = None
                favored_spread = None
                favored_odds = None
                
                if odds_info:
                    odds_data = odds_info[0]
                    home_odds = odds_data.get("homeTeamOdds", {})
                    away_odds = odds_data.get("awayTeamOdds", {})
                
                    if home_odds.get("favorite") is True:
                        favored_team = home_name
                        favored_spread = home_odds.get("spread")
                        favored_odds = home_odds.get("moneyLine")
                    elif away_odds.get("favorite") is True:
                        favored_team = away_name
                        favored_spread = away_odds.get("spread")
                        favored_odds = away_odds.get("moneyLine")

# Clean defaults if missing
if not favored_team:
    favored_team = "Even matchup"
if not favored_spread:
    favored_spread = "N/A"
if not favored_odds:
    favored_odds = "N/A"
                    
                # Safe scoring
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
                    "description": rivalInfo
                    "favored_team": favored_team,
                    "favored_spread": favored_spread,
                    "favored_odds": favored_odds,
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
