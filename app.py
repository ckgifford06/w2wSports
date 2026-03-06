from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# load rating modules only when needed to save memory
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
    return None

# define sports and API endpoints
sports = {
    "nba": {"name": "NBA", "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"},
    "nfl": {"name": "NFL", "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"},
    "nhl": {"name": "NHL", "url": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"},
    "mlb": {"name": "MLB", "url": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"},
    "cfb": {"name": "CFB", "url": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"},
    "cbb": {"name": "CBB", "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"}
}

def calculate_score(home, away, league):
    module = get_rating_module(league)
    if module:
        return module.calculate_score(home, away)
    return 15

def rivalryMatchup(home, away, league):
    module = get_rating_module(league)
    if module:
        return module.rivalry(home, away) > 5
    return False

def get_rivalry_score(home, away, league):
    """Get the actual rivalry score value"""
    module = get_rating_module(league)
    if module:
        return module.rivalry(home, away)
    return 0

def generate_fallback_blurb(game_info):
    parts = []
    
    # add rankings if both teams are ranked
    if game_info.get('home_rank') and game_info['home_rank'] != "Unranked":
        if game_info.get('away_rank') and game_info['away_rank'] != "Unranked":
            parts.append(f"{game_info['home_rank']} {game_info['home_team']} hosts {game_info['away_rank']} {game_info['away_team']}")
        else:
            parts.append(f"{game_info['home_rank']} {game_info['home_team']} faces {game_info['away_team']}")
    elif game_info.get('away_rank') and game_info['away_rank'] != "Unranked":
        parts.append(f"{game_info['away_rank']} {game_info['away_team']} visits {game_info['home_team']}")
    
    # add rivalry info
    if game_info.get('is_rivalry'):
        if parts:
            parts.append("in rivalry matchup")
        else:
            parts.append(f"{game_info['home_team']} vs {game_info['away_team']} rivalry")
    
    # add conference
    if game_info.get('conference') and game_info['conference'] != "N/A":
        if parts:
            parts.append(f"in {game_info['conference']}")
        else:
            parts.append(f"{game_info['conference']} matchup")
    
    # add record highlights
    if not parts:
        home_rec = game_info.get('home_record', '')
        away_rec = game_info.get('away_record', '')
        if '18-' in home_rec or '17-' in home_rec or '-0' in home_rec:
            parts.append(f"{home_rec} {game_info['home_team']} hosts {game_info['away_team']}")
        elif '18-' in away_rec or '17-' in away_rec or '-0' in away_rec:
            parts.append(f"{away_rec} {game_info['away_team']} visits {game_info['home_team']}")
    
    return " ".join(parts) if parts else f"{game_info['home_team']} vs {game_info['away_team']}"


@app.route('/')
def index():
    selected_league = request.args.get("league", "all")

    #gets whatever timezone you are in, trying to figure out how to cater the time it shoes you to your time zone still
    timezone_str = request.args.get("tz", "US/Eastern")
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone("US/Eastern")

    today = datetime.now(local_tz).strftime("%Y%m%d")
    all_games = []

    # now is the good part, going through each matchup finally
    for key, sport in sports.items():

        if selected_league != "all" and sport["name"].lower() != selected_league.lower():
            continue

        try:
            response = requests.get(sport["url"], params={"dates": today})
            data = response.json()

            # getting every event that day
            for event in data.get("events", []):
                competition = event["competitions"][0]
                competitors = competition["competitors"]

                # determine which team is home and which is away based on homeAway field
                home_competitor = None
                away_competitor = None
                for comp in competitors:
                    if comp.get("homeAway") == "home":
                        home_competitor = comp
                    elif comp.get("homeAway") == "away":
                        away_competitor = comp
                
                # fallback to index-based if homeAway not found
                if not home_competitor or not away_competitor:
                    home_competitor = competitors[0]
                    away_competitor = competitors[1]

                # home and away abbreviations
                home_abbr = f"{home_competitor['team']['abbreviation']}_{sport['name']}"
                away_abbr = f"{away_competitor['team']['abbreviation']}_{sport['name']}"

                #home and away team names
                home_name = home_competitor['team']['displayName']
                away_name = away_competitor['team']['displayName']

                home_team = home_competitor["team"]
                away_team = away_competitor["team"]

                if home_team["abbreviation"] == "TBD" or away_team["abbreviation"] == "TBD":
                    continue

                try:
                    #getting gametime
                    game_datetime_utc = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    game_datetime_local = game_datetime_utc.astimezone(local_tz)

                    if game_datetime_local.date() != datetime.now(local_tz).date():
                        continue

                    game_time = game_datetime_local.strftime("%I:%M %p").lstrip("0")
                except:
                    continue

                #getting live scores here
                status = competition.get("status", {}).get("type", {}).get("name", "STATUS_SCHEDULED")
                home_score = home_competitor.get("score", "0")
                away_score = away_competitor.get("score", "0")

                # live scores
                if status == "STATUS_IN_PROGRESS":
                    live_score = f"Live score: {home_score} - {away_score}"
                elif status == "STATUS_FINAL":
                    live_score = f"Final score: {home_score} - {away_score}"
                else:
                    live_score = "Live score: Not Started"

                # now getting the betting odds
                # !!!!NOTE!!!!! - ESPN weirdly puts different variables for each of the sports (I am not sure why, but I want to find out)
                # because of this, I have to split the odds parsing logic into three different parts. Each one does the same with different variables.
                odds_info = competition.get("odds", [])
                favored_display = "No moneyline"
                spread_display = "No spread"

                # NHL
                if sport["name"] == "NHL" and odds_info:
                    #getting spread and moneyline
                    odds_item = odds_info[0]  
                    details = odds_item.get("details", "")
                    spread = odds_item.get("spread", None)

                    away_team_odds = odds_item.get("awayTeamOdds", {}).get("team", {}).get("displayName", "Away")
                    home_team_odds = odds_item.get("homeTeamOdds", {}).get("team", {}).get("displayName", "Home")
                
                    home_ml = odds_item.get("homeTeamOdds", {}).get("moneyLine")
                    away_ml = odds_item.get("awayTeamOdds", {}).get("moneyLine")

                    # determining what moneyline to send out (ie. whos favored)
                    if home_ml is not None and away_ml is not None:
                        if home_ml < away_ml:
                            favored_display = f"{home_team_odds} {home_ml}"
                        else:
                            favored_display = f"{away_team_odds} {away_ml}"
                    elif details:
                        favored_display = details
                        
                    # determining what spread to send out (ie. whos favored)
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
                
                # NBA, NFL, and CBB
                elif sport["name"] in ["NBA", "NFL", "CBB"] and odds_info:
                    # getting spread
                    try:
                        spread_display = "No spread"

                        # different from NHL logic in the face that it labels the team as favorite, so I just made it so that if "x" team is
                        # the favorite, then it just gets the odds off of that
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
                
                        # determining moneyline
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

                        # Not working right now, but I want it to say "No odds available - Game in Progress" instead of "No odds available"
                        if status == "STATUS_IN_PROGRESS" or status == "STATUS_FINAL":
                            favored_display = "No odds available - Game in Progress"
                            spread_display = "No odds available - Game in Progress"
                
                    except Exception:
                        favored_display = "No odds"
                        spread_display = "No spread"

                # CFB
                elif sport["name"] == "CFB" and odds_info:
                    try:
                        # gets the spread and moneyline for both teams
                        odds_item = odds_info[0]
                        home_odds = odds_item.get("homeTeamOdds", {})
                        away_odds = odds_item.get("awayTeamOdds", {})
                
                        home_ml = home_odds.get("moneyLine")
                        away_ml = away_odds.get("moneyLine")
                        spread_val = odds_item.get("spread")
                        details = odds_item.get("details")
                
                        moneyline = competition.get("odds", [{}])[0].get("moneyline", {})
                        home_ml = moneyline.get("home", {}).get("close", {}).get("odds")
                        away_ml = moneyline.get("away", {}).get("close", {}).get("odds")

                        # sees which moneyline to send out
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

                        # Sees which spread to send out
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
                    except:
                        favored_display = "No moneyline"
                        spread_display = "No spread"

                try:
                    score = calculate_score(home_abbr, away_abbr, sport["name"])
                    is_rivalry = rivalryMatchup(home_abbr, away_abbr, sport["name"])
                    rivalry_score = get_rivalry_score(home_abbr, away_abbr, sport["name"])
                    
                    home_record = home_competitor.get("records", [{}])[0].get("summary", "N/A")
                    away_record = away_competitor.get("records", [{}])[0].get("summary", "N/A")
                    home_rank = home_competitor.get("curatedRank", {}).get("current")
                    away_rank = away_competitor.get("curatedRank", {}).get("current")
                    conference = competition.get("groups", {}).get("shortName", "N/A")
                    
                    # format ranks
                    home_rank_str = f"#{home_rank}" if home_rank and home_rank != 99 else "Unranked"
                    away_rank_str = f"#{away_rank}" if away_rank and away_rank != 99 else "Unranked"
                    
                    game_blurb_info = {
                        'league': sport['name'],
                        'home_team': home_name,
                        'away_team': away_name,
                        'home_record': home_record,
                        'away_record': away_record,
                        'home_rank': home_rank_str,
                        'away_rank': away_rank_str,
                        'conference': conference,
                        'rivalry_score': rivalry_score,
                        'is_rivalry': is_rivalry
                    }
                    
                    description = generate_fallback_blurb(game_blurb_info)
                    
                except Exception as e:
                    print(f"Error generating game info: {e}")
                    score = 0
                    description = "Exciting matchup"
                
                try:
                    # gets the network where each game is being broadcasted
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
                    where_to_watch = ", ".join(sorted(set(networks))) if networks else "No networks..."
                except:
                    where_to_watch = "No networks..."

                all_games.append({
                    "matchup": f"{home_name} vs {away_name}",
                    "league": sport["name"],
                    "score": score,
                    "description": description,
                    "time": game_time,
                    "favored": favored_display,
                    "favored_spread": spread_display,
                    "where_to_watch": where_to_watch,
                    "live_score": live_score
                })

        except Exception as e:
            print(f"Error fetching {sport['name']}: {e}", flush=True)
            continue

    # sort and get top 10 games
    filtered_ranked = sorted(all_games, key=lambda x: x["score"], reverse=True)[:10]

    return render_template("index.html", matchups=filtered_ranked, selected_league=selected_league, active_page="home")

# routes for each page
@app.route('/about')
def about():
    return render_template('about.html', active_page='about')

@app.route("/formula")
def formula():
    return render_template("formula.html", active_page="formula")
