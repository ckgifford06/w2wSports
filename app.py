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
        return False


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

                # --- 🕒 Game Time ---
                try:
                    game_datetime_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    game_datetime_local = game_datetime_utc.astimezone(local_tz)
                    game_time = game_datetime_local.strftime("%I:%M %p").lstrip("0")
                except Exception:
                    game_time = "TBD"

                odds_info = competition.get("odds", [])
                favored_display = "No odds"
                spread_display = "No spread"
                favored_team = None

                # --- 💰 Odds per sport ---
                competition = event["competitions"][0]
                odds_info = competition.get("odds", [])
                favored_display = "No odds"
                spread_display = "No spread"
                
                if odds_info:
                    odds_item = odds_info[0]
                
                    # --- NHL (improved) ---
                    if sport["name"] == "NHL":
                        details = odds_item.get("details", "")
                        spread = odds_item.get("spread", None)
                        if details:
                            favored_team = details.split(" ")[0]
                            favored_display = details  # e.g., "NYI -135"
                        if favored_team and spread is not None:
                            # ESPN sometimes lists favorite spread as positive, flip it to negative
                            try:
                                spread_value = float(spread)
                                if spread_value > 0:
                                    spread_value = -spread_value
                                spread_display = f"{favored_team} {spread_value:.1f}"
                            except ValueError:
                                spread_display = f"{favored_team} {spread}"

                    # --- NBA & NFL (improved) ---
                    elif sport["name"] in ["NBA", "NFL"]:
                        try:
                            home_odds_data = odds_item.get("homeTeamOdds") or {}
                            away_odds_data = odds_item.get("awayTeamOdds") or {}

                            home_ml = home_odds_data.get("moneyLine")
                            away_ml = away_odds_data.get("moneyLine")
                            home_spread = home_odds_data.get("spread")
                            away_spread = away_odds_data.get("spread")

                            # Try top-level fallback if team odds missing
                            if home_spread is None and away_spread is None:
                                home_spread = odds_item.get("spread")

                            # Determine favored team based on moneyline (lower = favored)
                            if home_ml is not None and away_ml is not None:
                                if home_ml < away_ml:
                                    favored_display = f"{competitors[0]['team']['displayName']} {home_ml}"
                                    if home_spread is not None:
                                        spread_display = f"{competitors[0]['team']['displayName']} {home_spread}"
                                else:
                                    favored_display = f"{competitors[1]['team']['displayName']} {away_ml}"
                                    if away_spread is not None:
                                        spread_display = f"{competitors[1]['team']['displayName']} {away_spread}"
                            elif odds_item.get("details"):
                                favored_display = odds_item["details"]

                        except Exception as e:
                            print(f"Odds parsing error ({sport['name']}): {e}", flush=True)
                            favored_display = "No odds"
                            spread_display = "No spread"

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
    top_10_games = sorted(all_games, key=lambda x: x["score"], reverse=True)[:10]

    return render_template('index.html', matchups=top_10_games)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
