from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)

def get_rating_module(league):
    if league == "NBA":
        import NBArating
        return NBArating
    elif league == "NFL":
        import NFLrating
        return NFLrating
    elif league == "NHL":
        import NHLrating
        return NHLrating
    elif league == "MLB":
        import MLBrating
        return MLBrating
    elif league == "CFB":
        import CFBrating
        return CFBrating
    elif league == "CBB":
        import CBBrating
        return CBBrating
    elif league == "EPL":
        import EPLrating
        return EPLrating
    return None

sports = {
    "nba": {"name": "NBA", "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"},
    "nfl": {"name": "NFL", "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"},
    "nhl": {"name": "NHL", "url": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"},
    "mlb": {"name": "MLB", "url": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"},
    "cfb": {"name": "CFB", "url": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"},
    "cbb": {"name": "CBB", "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=50"},
    "epl": {"name": "EPL", "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"},
}

def calculate_score(home, away, league):
    module = get_rating_module(league)
    if module:
        return module.calculate_score(home, away)
    return 15

def calculate_score_breakdown(home, away, league):
    module = get_rating_module(league)
    if module and hasattr(module, 'calculate_score_breakdown'):
        return module.calculate_score_breakdown(home, away)
    return {"rivalry": 0, "marketability": 0, "competitiveness": 0, "quality": 0, "importance": 0}

def rivalryMatchup(home, away, league):
    module = get_rating_module(league)
    if module:
        return module.rivalry(home, away) > 5
    return False

def get_rivalry_score(home, away, league):
    module = get_rating_module(league)
    if module:
        return module.rivalry(home, away)
    return 0

def generate_fallback_blurb(game_info):
    parts = []

    if game_info.get('home_rank') and game_info['home_rank'] != "Unranked":
        if game_info.get('away_rank') and game_info['away_rank'] != "Unranked":
            parts.append(f"{game_info['home_rank']} {game_info['home_team']} hosts {game_info['away_rank']} {game_info['away_team']}")
        else:
            parts.append(f"{game_info['home_rank']} {game_info['home_team']} faces {game_info['away_team']}")
    elif game_info.get('away_rank') and game_info['away_rank'] != "Unranked":
        parts.append(f"{game_info['away_rank']} {game_info['away_team']} visits {game_info['home_team']}")

    if game_info.get('is_rivalry'):
        if parts:
            parts.append("in rivalry matchup")
        else:
            parts.append(f"{game_info['home_team']} vs {game_info['away_team']} rivalry")

    if game_info.get('conference') and game_info['conference'] != "N/A":
        if parts:
            parts.append(f"in {game_info['conference']}")
        else:
            parts.append(f"{game_info['conference']} matchup")

    if not parts:
        home_rec = game_info.get('home_record', '')
        away_rec = game_info.get('away_record', '')
        if '18-' in home_rec or '17-' in home_rec or '-0' in home_rec:
            parts.append(f"{home_rec} {game_info['home_team']} hosts {game_info['away_team']}")
        elif '18-' in away_rec or '17-' in away_rec or '-0' in away_rec:
            parts.append(f"{away_rec} {game_info['away_team']} visits {game_info['home_team']}")

    return " ".join(parts) if parts else f"{game_info['home_team']} vs {game_info['away_team']}"

def fetch_games_for_date(date_str, local_tz):
    all_games = []

    for key, sport in sports.items():
        try:
            response = requests.get(sport["url"], params={"dates": date_str}, timeout=8)
            if not response.ok:
                continue
            data = response.json()

            for event in data.get("events", []):
                competition = event["competitions"][0]
                competitors = competition["competitors"]

                home_competitor = None
                away_competitor = None
                for comp in competitors:
                    if comp.get("homeAway") == "home":
                        home_competitor = comp
                    elif comp.get("homeAway") == "away":
                        away_competitor = comp

                if not home_competitor or not away_competitor:
                    home_competitor = competitors[0]
                    away_competitor = competitors[1]

                home_abbr = f"{home_competitor['team']['abbreviation']}_{sport['name']}"
                away_abbr = f"{away_competitor['team']['abbreviation']}_{sport['name']}"
                home_name = home_competitor['team']['displayName']
                away_name = away_competitor['team']['displayName']
                home_team = home_competitor["team"]
                away_team = away_competitor["team"]

                if home_team["abbreviation"] == "TBD" or away_team["abbreviation"] == "TBD":
                    continue

                try:
                    game_datetime_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    game_datetime_local = game_datetime_utc.astimezone(local_tz)
                    game_time = game_datetime_local.strftime("%I:%M %p").lstrip("0")
                except:
                    continue

                status = competition.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
                home_score = home_competitor.get("score", "0")
                away_score = away_competitor.get("score", "0")

                if status == "STATUS_IN_PROGRESS":
                    live_score = f"Live score: {home_score} - {away_score}"
                elif status == "STATUS_FINAL":
                    live_score = f"Final score: {home_score} - {away_score}"
                else:
                    live_score = "Live score: Not Started"

                odds_info = competition.get("odds", [])
                favored_display = "No moneyline"
                spread_display = "No spread"

                if sport["name"] == "NHL" and odds_info:
                    odds_item = odds_info[0]
                    details = odds_item.get("details", "")
                    spread = odds_item.get("spread", None)
                    away_team_odds = odds_item.get("awayTeamOdds", {}).get("team", {}).get("displayName", "Away")
                    home_team_odds = odds_item.get("homeTeamOdds", {}).get("team", {}).get("displayName", "Home")
                    home_ml = odds_item.get("homeTeamOdds", {}).get("moneyLine")
                    away_ml = odds_item.get("awayTeamOdds", {}).get("moneyLine")
                    if home_ml is not None and away_ml is not None:
                        favored_display = f"{home_team_odds} {home_ml}" if home_ml < away_ml else f"{away_team_odds} {away_ml}"
                    elif details:
                        favored_display = details
                    if spread is not None:
                        if spread > 0:
                            spread = -abs(spread)
                        if home_ml is not None and away_ml is not None:
                            favored_team = home_team_odds if home_ml < away_ml else away_team_odds
                            spread_display = f"{favored_team} {spread:+}"
                        elif details:
                            spread_display = f"{details.split(' ')[0]} {spread:+}"
                    if status in ("STATUS_IN_PROGRESS", "STATUS_FINAL"):
                        favored_display = "Game Started - No Live Moneyline"
                        spread_display = "Game Started - No Live Spread"

                elif sport["name"] in ["NBA", "NFL", "CBB"] and odds_info:
                    try:
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
                            favored_display = f"{home_name} {home_ml}" if int(home_ml) < int(away_ml) else f"{away_name} {away_ml}"
                        if status in ("STATUS_IN_PROGRESS", "STATUS_FINAL"):
                            favored_display = "Game Started - No Live Moneyline"
                            spread_display = "Game Started - No Live Spread"
                    except Exception:
                        pass

                elif sport["name"] == "CFB" and odds_info:
                    try:
                        moneyline = competition.get("odds", [{}])[0].get("moneyline", {})
                        home_ml = moneyline.get("home", {}).get("close", {}).get("odds")
                        away_ml = moneyline.get("away", {}).get("close", {}).get("odds")
                        if home_ml and away_ml:
                            favored_display = f"{home_name} {home_ml}" if int(home_ml) < int(away_ml) else f"{away_name} {away_ml}"
                        spread = competition.get("odds", [{}])[0].get("pointSpread", {})
                        home_spread = spread.get("home", {}).get("close", {}).get("line")
                        if home_spread:
                            favored_team = home_name if (home_ml and away_ml and int(home_ml) < int(away_ml)) else away_name
                            spread_display = f"{favored_team} {home_spread}"
                        if status in ("STATUS_IN_PROGRESS", "STATUS_FINAL"):
                            favored_display = "Game Started - No Live Moneyline"
                            spread_display = "Game Started - No Live Spread"
                    except:
                        pass

                try:
                    home_record = home_competitor.get("records", [{}])[0].get("summary", "0-0-0")
                    away_record = away_competitor.get("records", [{}])[0].get("summary", "0-0-0")
                    home_rank = home_competitor.get("curatedRank", {}).get("current")
                    away_rank = away_competitor.get("curatedRank", {}).get("current")
                    conference = competition.get("groups", {}).get("shortName", "N/A")
                    home_rank_str = f"#{home_rank}" if home_rank and home_rank != 99 else "Unranked"
                    away_rank_str = f"#{away_rank}" if away_rank and away_rank != 99 else "Unranked"

                    if sport["name"] == "EPL":
                        module = get_rating_module("EPL")
                        score = module.calculate_score(home_abbr, away_abbr, home_record, away_record) if module else 15
                        breakdown = module.calculate_score_breakdown(home_abbr, away_abbr, home_record, away_record) if module and hasattr(module, 'calculate_score_breakdown') else {"rivalry": 0, "marketability": 0, "competitiveness": 0, "quality": 0, "importance": 0}
                    elif sport["name"] == "CBB":
                        module = get_rating_module("CBB")
                        hr = home_competitor.get("curatedRank", {}).get("current")
                        ar = away_competitor.get("curatedRank", {}).get("current")
                        hr = int(hr) if hr and hr != 99 else None
                        ar = int(ar) if ar and ar != 99 else None
                        score = module.calculate_score(home_abbr, away_abbr, home_record, away_record, hr, ar) if module else 15
                        breakdown = module.calculate_score_breakdown(home_abbr, away_abbr, home_record, away_record, hr, ar) if module and hasattr(module, 'calculate_score_breakdown') else {"rivalry": 0, "marketability": 0, "competitiveness": 0, "quality": 0, "importance": 0}
                    else:
                        score = calculate_score(home_abbr, away_abbr, sport["name"])
                        breakdown = calculate_score_breakdown(home_abbr, away_abbr, sport["name"])

                    is_rivalry = rivalryMatchup(home_abbr, away_abbr, sport["name"])
                    rivalry_score = get_rivalry_score(home_abbr, away_abbr, sport["name"])
                    description = generate_fallback_blurb({
                        'league': sport['name'], 'home_team': home_name, 'away_team': away_name,
                        'home_record': home_record, 'away_record': away_record,
                        'home_rank': home_rank_str, 'away_rank': away_rank_str,
                        'conference': conference, 'rivalry_score': rivalry_score, 'is_rivalry': is_rivalry
                    })
                except Exception as e:
                    score = 0
                    breakdown = {"rivalry": 0, "marketability": 0, "competitiveness": 0, "quality": 0, "importance": 0}
                    description = "Exciting matchup"
                    is_rivalry = False

                try:
                    broadcasts = competition.get("broadcasts", [])
                    geo_broadcasts = competition.get("geoBroadcasts", [])
                    networks = []
                    for b in broadcasts:
                        networks.extend(b.get("names", []))
                    for gb in geo_broadcasts:
                        if gb.get("media") and gb["media"].get("shortName"):
                            networks.append(gb["media"]["shortName"])
                    where_to_watch = ", ".join(sorted(set(networks))) if networks else "No networks..."
                except:
                    where_to_watch = "No networks..."

                all_games.append({
                    "matchup": f"{home_name} vs {away_name}",
                    "league": sport["name"],
                    "score": score,
                    "breakdown": breakdown,
                    "description": description,
                    "time": game_time,
                    "favored": favored_display,
                    "favored_spread": spread_display,
                    "where_to_watch": where_to_watch,
                    "live_score": live_score,
                    "is_rivalry": is_rivalry,
                })

        except Exception as e:
            print(f"Error fetching {sport['name']}: {e}", flush=True)
            continue

    return sorted(all_games, key=lambda x: x["score"], reverse=True)

@app.route('/')
def index():
    selected_league = request.args.get("league", "top10")
    timezone_str = request.args.get("tz", "US/Eastern")
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone("US/Eastern")

    today = datetime.now(local_tz).strftime("%Y%m%d")
    all_ranked = fetch_games_for_date(today, local_tz)
    return render_template("index.html", matchups=all_ranked, selected_league=selected_league, active_page="home")

@app.route("/calendar")
def calendar():
    return render_template("calendar.html", active_page="calendar")

@app.route("/api/games")
def api_games():
    date_str = request.args.get("date")
    timezone_str = request.args.get("tz", "US/Eastern")
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone("US/Eastern")

    if not date_str:
        return jsonify({"error": "date parameter required"}), 400

    games = fetch_games_for_date(date_str, local_tz)
    return jsonify(games)

@app.route("/api/live")
def api_live():
    timezone_str = request.args.get("tz", "US/Eastern")
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone("US/Eastern")

    today = datetime.now(local_tz).strftime("%Y%m%d")
    games = fetch_games_for_date(today, local_tz)

    live_data = [
        {
            "matchup": g["matchup"],
            "league":  g["league"],
            "score":   g["live_score"].replace("Live score: ", "").replace("Final score: ", ""),
            "status":  "STATUS_IN_PROGRESS" if g["live_score"].startswith("Live score:") and "Not Started" not in g["live_score"]
                       else "STATUS_FINAL" if g["live_score"].startswith("Final score:")
                       else "STATUS_SCHEDULED",
            "detail":  "",
        }
        for g in games
    ]
    return jsonify(live_data)

@app.route("/leaderboard")
def leaderboard():
    try:
        from subscribe import get_top_games
        league_filter = request.args.get("league", "all")
        league = None if league_filter == "all" else league_filter
        games = get_top_games(limit=100, league=league)
    except Exception as e:
        print(f"Leaderboard error: {e}", flush=True)
        games = []
        league_filter = "all"
    return render_template("leaderboard.html", games=games, selected_league=league_filter, active_page="leaderboard")


@app.route("/api/save-scores")
def api_save_scores():
    """
    Cron endpoint — called at midnight ET to store the day's final scores.
    Protected by the same CRON_SECRET as the digest endpoint.
    """
    token = request.args.get("token")
    if token != os.environ.get("CRON_SECRET"):
        return jsonify({"error": "Unauthorized"}), 401

    from subscribe import save_game_scores, trim_game_scores
    import pytz as _pytz
    from datetime import datetime as _dt, timedelta as _td

    et = _pytz.timezone("US/Eastern")
    # At midnight ET, "yesterday" is the day whose games just finished
    yesterday = (_dt.now(et) - _td(days=1)).strftime("%Y%m%d")
    date_label = (_dt.now(et) - _td(days=1)).strftime("%Y-%m-%d")

    games = fetch_games_for_date(yesterday, et)
    if not games:
        return jsonify({"message": "No games found"}), 200

    ok = save_game_scores(games, date_label)
    trim_game_scores(keep=100)
    return jsonify({"success": ok, "saved": len(games), "date": date_label}), 200


@app.route('/about')
def about():
    return render_template('about.html', active_page='about')

@app.route("/formula")
def formula():
    return render_template("formula.html", active_page="formula")

@app.route("/api/subscribe", methods=["POST"])
def api_subscribe():
    from subscribe import add_pending_subscriber, send_confirmation_email
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email or "@" not in email:
        return jsonify({"error": "Invalid email"}), 400

    result = add_pending_subscriber(email)
    if result.get("success"):
        send_confirmation_email(email, result["token"])
        return jsonify({"success": True, "pending": True}), 200
    return jsonify({"error": result.get("error", "Something went wrong")}), 500


@app.route("/confirm")
def confirm():
    from subscribe import confirm_subscriber
    token = request.args.get("token", "").strip()
    if not token:
        return render_template("confirm.html", success=False, error="No token provided.")
    result = confirm_subscriber(token)
    if result.get("success"):
        return render_template("confirm.html", success=True, email=result["email"])
    return render_template("confirm.html", success=False, error=result.get("error", "Something went wrong."))

@app.route("/unsubscribe")
def unsubscribe():
    from subscribe import SUPABASE_URL, SUPABASE_KEY
    import requests as req

    email = request.args.get("email", "").strip().lower()
    if email and SUPABASE_URL and SUPABASE_KEY:
        url = f"{SUPABASE_URL}/rest/v1/subscribers?email=eq.{email}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
        req.delete(url, headers=headers)

    return render_template("unsubscribe.html")

@app.route("/api/send-digest")
def api_send_digest():
    token = request.args.get("token")
    if token != os.environ.get("CRON_SECRET"):
        return jsonify({"error": "Unauthorized"}), 401

    from daily_digest import run_digest
    run_digest()
    return jsonify({"success": True}), 200
