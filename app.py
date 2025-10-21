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
    #NBA
    "BOS_NBA": 9, "BKN_NBA": 7, "NY_NBA": 10, "PHI_NBA": 8, "TOR_NBA": 6,
    "CHI_NBA": 8, "CLE_NBA": 7, "DET_NBA": 5, "IND_NBA": 6, "MIL_NBA": 7,
    "ATL_NBA": 7, "CHA_NBA": 5, "MIA_NBA": 7, "ORL_NBA": 6, "WAS_NBA": 6.5,
    "DEN_NBA": 7, "MIN_NBA": 6, "OKC_NBA": 6, "POR_NBA": 5:, "UTAH_NBA": 5,
    "GS_NBA": 9, "LAC_NBA": 7, "LAL_NBA": 10, "PHX_NBA":7, "SAC_NBA": 5,
    "DAL_NBA": 8, "HOU_NBA": 7.5, "MEM_NBA": 5, "NO_NBA": 6, "SAS_NBA": 7,

    #NFL
    "ARI_NFL": 6, "ATL_NFL": 6.5, "BAL_NFL": 8, "BUF_NFL": 8, "CAR_NFL": 5,
    "CHI_NFL": 9, "CIN_NFL": 8, "CLE_NFL": 7, "DAL_NFL": 10, "DEN_NFL": 8,
    "DET_NFL": 7.5, "GB_NFL": 9, "HOU_NFL": 6.5, "IND_NFL": 6, "JAX_NFL": 6,
    "KC_NFL": 10, "LV_NFL": 9, "LAC_NFL": 6.5, "LAR_NFL": 8, "MIA_NFL": 8,
    "MIN_NFL": 7.5, "NE_NFL": 10, "NO_NFL": 8, "NYG_NFL": 9, "NYJ_NFL": 8.5,
    "PHI_NFL": 9.5, "PIT_NFL": 9, "SF_NFL": 10, "SEA_NFL": 8, "TB_NFL": 8,
    "TEN_NFL": 6.5, "WAS_NFL": 7

    #MLB
    "ARI_MLB": 6, "ATL_MLB": 8, "BAL_MLB": 7.5, "BOS_MLB": 10, "CHC_MLB": 9,
    "CHW_MLB": 7, "CIN_MLB": 6.5, "CLE_MLB": 7, "COL_MLB": 6, "DET_MLB": 7,
    "HOU_MLB": 9, "KC_MLB": 6, "LAA_MLB": 7.5, "LAD_MLB": 10, "MIA_MLB": 5.5,
    "MIL_MLB": 6.5, "MIN_MLB": 7, "NYM_MLB": 9, "NYY_MLB": 10, "OAK_MLB": 4.5,
    "PHI_MLB": 8.5, "PIT_MLB": 6.5, "SD_MLB": 8, "SF_MLB": 9, "SEA_MLB": 7.5,
    "STL_MLB": 9, "TB_MLB": 7, "TEX_MLB": 8, "TOR_MLB": 8, "WSH_MLB": 7,
    
    #NHL
    "ANA_NHL": 6, "UTA_NHL": 5.5, "BOS_NHL": 10, "BUF_NHL": 7, "CAR_NHL": 6,
    "CBJ_NHL": 6.5, "CGY_NHL": 7, "CHI_NHL": 8, "COL_NHL": 6.5, "DAL_NHL": 7.5,
    "DET_NHL": 8, "EDM_NHL": 6, "FLA_NHL": 6.5, "LA_NHL": 9, "MIN_NHL": 7,
    "MTL_NHL": 8.5, "NJD_NHL": 7, "NSH_NHL": 7.5, "NYI_NHL": 8, "NYR_NHL": 9,
    "OTT_NHL": 6, "PHI_NHL": 8, "PIT_NHL": 9, "SJS_NHL": 7, "SEA_NHL": 7,
    "STL_NHL": 7, "TBL_NHL": 8, "TOR_NHL": 9, "VAN_NHL": 6.5, "VGK_NHL": 7.5,
    "WPG_NHL": 7, "WSH_NHL": 8
}

rivalries = [
    #NBA
    ("LAL_NBA", "BOS_NBA"), ("NY_NBA", "BOS_NBA"),("NY_NBA", "IND_NBA") 
    ("CHI_NBA", "IND_NBA"), ("MIA_NBA", "BOS_NBA"),("MIA_NBA", "NY_NBA"),
    ("DAL_NBA", "SAS_NBA"),("GS_NBA", "LAL_NBA"),("PHX_NBA", "SAS_NBA"), 
    ("TOR_NBA", "BOS_NBA"),("NY_NBA", "PHI_NBA"),("DAL_NBA", "LAL_NBA")
    ("OKC_NBA", "GS_NBA"),("LAC_NBA", "GS_NBA"), ("LAL_NBA", "SAS_NBA")  

    #NFL

    #MLB

    #NHL
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
                home_abbr = f"{competitors[0]['team']['abbreviation']}_{sport['name']}"
                away_abbr = f"{competitors[1]['team']['abbreviation']}_{sport['name']}"

                home_name = competitors[0]['team']['displayName']
                away_name = competitors[1]['team']['displayName']

                score = calculate_score(home_abbr, away_abbr)

                all_games.append({
                    "matchup": f"{home_name} vs {away_name}",
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
