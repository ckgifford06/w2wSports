from flask import Flask, render_template, request, jsonify
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
    timezone_str = request.args.get("tz", "US/Eastern")
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone("US/Eastern")

    today = datetime.now(local_tz).strftime("%Y%m%d")
    all_games = []

    for key, sport in sports.items():
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

                # Game Time
                try:
                    game_datetime_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    game_datetime_local = game_datetime_utc.astimezone(local_tz)
                    game_time = game_datetime_local.strftime("%I:%M %p").lstrip("0")
                except Exception:
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

                # Odds
                odds_info = competition.get("odds", [])
                favored_display = "No odds"
                spread_display = "No spread"

                if odds_info:
                    odds_item = odds_info[0]

                    # NHL
                    if sport["name"] == "NHL":
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

                    # NBA & NFL
                    elif sport["name"] in ["NBA", "NFL"]:
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

                            home_odds_data = odds_item.get("homeTeamOdds", odds_item.get("home", {}))
                            away_odds_data = odds_item.get("awayTeamOdds", odds_item.get("away", {}))
                            home_ml = home_odds_data.get("moneyLine")
                            away_ml = away_odds_data.get("moneyLine")

                            if home_ml is not None and away_ml is not None:
                                if home_ml < away_ml:
                                    favored_display = f"{home_name} {home_ml}"
                                elif home_ml > away_ml:
                                    favored_display = f"{away_name} {away_ml}"
                                else:
                                    favored_display = f"Both teams {away_ml})"
                            elif odds_item.get("details"):
                                favored_display = odds_item["details"]

                        except Exception as e:
                            favored_display = "No odds"
                            spread_display = "No spread"

                rivalInfo = ""
                try:
                    score = calculate_score(home_abbr, away_abbr, sport["name"])
                    if rivalryMatchup(home_abbr, away_abbr, sport["name"]):
                        rivalInfo = "Rivalry Matchup"
                except Exception:
                    score = 0

                # Broadcasts
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
                except Exception:
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

    top_10_games = sorted(all_games, key=lambda x: x["score"], reverse=True)[:10]
    return render_template('index.html', matchups=top_10_games)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
