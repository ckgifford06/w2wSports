from flask import Flask, render_template, request
import requests
from datetime import datetime
import pytz

app = Flask(__name__)

# Define sports and API endpoints
sports = {
    "nba": {"name": "NBA", "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"},
    "nfl": {"name": "NFL", "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"},
    "nhl": {"name": "NHL", "url": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"},
    "mlb": {"name": "MLB", "url": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"}
}

# Mock marketability and rivalry scores
team_marketability = {
    "LAL_NBA": 10, "BOS_NBA": 9, "NY_NBA": 9,
    "DAL_NFL": 8, "NYG_NFL": 8, "NE_NFL": 10,
    "NYR_NHL": 9, "NYY_MLB": 10, "BOS_MLB": 9
}

rivalries = [
    ("LAL_NBA", "BOS_NBA"),
    ("NYG_NFL", "DAL_NFL"),
    ("NYY_MLB", "BOS_MLB"),
    ("NYR_NHL", "BOS_NHL")
]

def calculate_score(home, away):
    rivalry = 5 if (home, away) in rivalries or (away, home) in rivalries else 0
    marketability = team_marketability.get(home, 5) + team_marketability.get(away, 5)
    return rivalry + marketability


@app.route('/')
def index():
    # ✅ Get timezone dynamically from user (defaults to US/Eastern)
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
            response = requests.get(sport["url"], params={"dates": today})
            data = response.json()

            for event in data.get("events", []):
                competitors = event["competitions"][0]["competitors"]
                home_team = f"{competitors[0]['team']['abbreviation']}_{sport['name']}"
                away_team = f"{competitors[1]['team']['abbreviation']}_{sport['name']}"
                score = calculate_score(home_team, away_team)

                display_home = home_team.split("_")[0]
                display_away = away_team.split("_")[0]
                
                all_games.append({
                    "matchup": f"{home_team} vs {away_team}",
                    "league": sport["name"],
                    "score": score
                })

        except Exception as e:
            continue

    # Sort all games by score descending and take top 10
    top_10_games = sorted(all_games, key=lambda x: x["score"], reverse=True)[:10]

    return render_template('index.html', matchups=top_10_games)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
