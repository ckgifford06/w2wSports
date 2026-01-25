from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import pytz
import NBArating
import NFLrating
import NHLrating
import MLBrating
import CFBrating
import CBBrating
import smtplib
from email.mime.text import MIMEText
import sqlite3
import os
import anthropic

app = Flask(__name__)

DB_PATH = "emails.db"

# initializing Anthropic (Claude AI) here
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def init_db():
    """Initialize database with subscribers and blurb cache tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (
                    email TEXT PRIMARY KEY,
                    verified INTEGER DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS blurb_cache (
                    cache_key TEXT PRIMARY KEY,
                    blurb TEXT,
                    created_at TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

def get_cached_blurb(cache_key):
    """Retrieve a cached blurb from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT blurb FROM blurb_cache WHERE cache_key = ?", (cache_key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error retrieving cached blurb: {e}")
        return None

def save_cached_blurb(cache_key, blurb):
    """Save a blurb to database cache"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO blurb_cache (cache_key, blurb, created_at) VALUES (?, ?, ?)",
                  (cache_key, blurb, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving cached blurb: {e}")

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
    elif league == "CBB":
        return CBBrating.calculate_score(home, away)
    else:
        return 15

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
    elif league == "CBB":
        return (CBBrating.rivalry(home, away) > 5)
    else:
        return False

def get_rivalry_score(home, away, league):
    """Get the actual rivalry score value"""
    if league == "NBA":
        return NBArating.rivalry(home, away)
    elif league == "NFL":
        return NFLrating.rivalry(home, away)
    elif league == "NHL":
        return NHLrating.rivalry(home, away)
    elif league == "MLB":
        return MLBrating.rivalry(home, away)
    elif league == "CFB":
        return CFBrating.rivalry(home, away)
    elif league == "CBB":
        return CBBrating.rivalry(home, away)
    return 0

# blurb function using Claude AI
def generate_game_blurb(game_info, use_fallback_if_not_cached=False):
    """Use Claude AI to generate an exciting game blurb with database caching"""
    
    # create a unique cache key for this game (includes today's date)
    today = datetime.now().strftime('%Y%m%d')
    cache_key = f"{today}_{game_info['league']}_{game_info['home_team']}_{game_info['away_team']}"
    
    # check if we already generated this blurb today (from database)
    cached_blurb = get_cached_blurb(cache_key)
    if cached_blurb:
        print(f"Using cached blurb for {game_info['home_team']} vs {game_info['away_team']}")
        return cached_blurb
    
    # since I want the website to actually load fast and so people don't have to wait a while, I chose to use a fallback if it is taking a while
    if use_fallback_if_not_cached:
        print(f"Using fallback for {game_info['home_team']} vs {game_info['away_team']}")
        return generate_fallback_blurb(game_info)
    
    try:
        # generating the prompt here (prompt rules, good examples, and bad examples for Anthropic to use)
        prompt = f"""Generate a brief, exciting 1-sentence description (max 15 words) for this sports matchup. Be VERY SPECIFIC using the exact data provided.

League: {game_info['league']}
Matchup: {game_info['home_team']} vs {game_info['away_team']}
Home Record: {game_info.get('home_record', 'N/A')}
Away Record: {game_info.get('away_record', 'N/A')}
Home Rank: {game_info.get('home_rank', 'Unranked')}
Away Rank: {game_info.get('away_rank', 'Unranked')}
Conference: {game_info.get('conference', 'N/A')}
Rivalry Score: {game_info.get('rivalry_score', 0)} out of 12
Is Rivalry: {game_info.get('is_rivalry', False)}

IMPORTANT RULES:
1. USE SPECIFIC RANKINGS when available (e.g., "#3 Michigan" not just "top-ranked")
2. MENTION EXACT RECORDS when they tell a story (e.g., "18-1 Saint Louis" or "undefeated in conference")
3. NAME THE CONFERENCE specifically (e.g., "Big Ten", "A-10", "ACC")
4. If it's a rivalry (score > 7), mention that it's a rivalry
5. Highlight what makes THIS specific matchup interesting TODAY
6. Make sure the home and away teams are correct. 

Good Examples:
- "#3 Michigan hosts rival Ohio State in crucial Big Ten battle"
- "18-1 Saint Louis defends perfect A-10 record at St. Bonaventure"
- "#1 Duke faces #5 UNC in college basketball's fiercest rivalry"
- "Undefeated Gonzaga visits conference rival Saint Mary's in WCC showdown"

Bad Examples (too generic):
- "Top teams clash in important game"
- "Conference matchup features ranked opponents"
- "Rivals meet in exciting contest"

Only return the blurb, nothing else. Be specific with numbers, names, and details."""

        print(f"Generating NEW AI blurb for {game_info['home_team']} vs {game_info['away_team']}")
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        blurb = message.content[0].text.strip()
        # remove any quotes that might be added
        blurb = blurb.strip('"').strip("'")
        
        # cache the result in database for future use
        save_cached_blurb(cache_key, blurb)
        
        print(f"Generated: {blurb}")
        return blurb
    except Exception as e:
        print(f"Error generating blurb: {e}")
        print(f"API Key present: {bool(os.environ.get('ANTHROPIC_API_KEY'))}")
        
        # fallback to simple description
        if game_info.get('is_rivalry'):
            return "Rivalry matchup"
        return generate_fallback_blurb(game_info)

def generate_fallback_blurb(game_info):
    """Generate a quick rule-based blurb when AI isn't cached yet"""
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

                # get game info for blurb generation
                try:
                    score = calculate_score(home_abbr, away_abbr, sport["name"])
                    is_rivalry = rivalryMatchup(home_abbr, away_abbr, sport["name"])
                    rivalry_score = get_rivalry_score(home_abbr, away_abbr, sport["name"])
                    
                    # gather additional info for blurb (but don't generate yet)
                    home_record = home_competitor.get("records", [{}])[0].get("summary", "N/A")
                    away_record = away_competitor.get("records", [{}])[0].get("summary", "N/A")
                    home_rank = home_competitor.get("curatedRank", {}).get("current")
                    away_rank = away_competitor.get("curatedRank", {}).get("current")
                    conference = competition.get("groups", {}).get("shortName", "N/A")
                    
                    # format ranks
                    home_rank_str = f"#{home_rank}" if home_rank and home_rank != 99 else "Unranked"
                    away_rank_str = f"#{away_rank}" if away_rank and away_rank != 99 else "Unranked"
                    
                    # store game info for later blurb generation
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
                    
                except Exception as e:
                    print(f"Error generating game info: {e}")
                    score = 0
                    game_blurb_info = None
                
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
                    "description": None,  # will be filled in later for top 10
                    "game_blurb_info": game_blurb_info,  # store info for later
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

    # NOW generate AI blurbs ONLY for the top 10 games to save data, memory, and better for environment
    for game in filtered_ranked:
        if game.get("game_blurb_info"):
            try:
                # always try AI first, use cached if available
                game["description"] = generate_game_blurb(game["game_blurb_info"], use_fallback_if_not_cached=False)
            except Exception as e:
                print(f"Error generating blurb for {game['matchup']}: {e}")
                # use fallback only on error
                if game.get("game_blurb_info"):
                    game["description"] = generate_fallback_blurb(game["game_blurb_info"])
                else:
                    game["description"] = "Exciting matchup"
        else:
            game["description"] = "Exciting matchup"
        
        # remove the temp blurb info
        if "game_blurb_info" in game:
            del game["game_blurb_info"]

    return render_template("index.html", matchups=filtered_ranked, selected_league=selected_league)

# routes for each page
@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/formula")
def formula():
    return render_template("formula.html")

# email stuff (coming soon...)
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
    return f"Thanks {email}, you're verified!"

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
