from flask import Flask, render_template
import requests
from datetime import datetime

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
    "LAL": 10, "BOS": 9, "NY": 9, "DAL": 8, "NYG": 8, "NE": 10, "NYR": 9, "NYY": 10, "BOSMLB": 9
}
rivalries = [
    ("LAL", "BOS"), ("NYG", "DAL"), ("NYY", "BOSMLB"), ("NYR", "BOS")
]

def calculate_score(home, away):
    rivalry = 5 if (home, away) in rivalries or (away, home) in rivalries else 0
    marketability = team_marketability.get(home, 5) + team_marketability.get(away, 5)
    return rivalry + marketability

@app.route('/')
def index():
    today = datetime.today().strftime('%Y%m%d')
    all_games = []

    # Fetch matchups from all sports
    for key, sport in sports.items():
        try:
            response = requests.get(sport["url"], params={"dates": today})
            data = response.json()

            for event in data.get("events", []):
                competitors = event["competitions"][0]["competitors"]
                home_team = competitors[0]["team"]["abbreviation"]
                away_team = competitors[1]["team"]["abbreviation"]
                score = calculate_score(home_team, away_team)
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
    app.run(debug=True, port=5001)