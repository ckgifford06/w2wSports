import requests
url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
data = requests.get(url).json()

season_length = 13
playoffs = false

def buildRecords():
    records = {}
    for event in data.get("events", []):
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_CFB"
            record_summary = None
            if "records" in competitor and len(competitor["records"]) > 0:
                record_summary = competitor["records"][0].get("summary", "0-0")
            records[team_abbr] = record_summary or "0-0"
    return records

def buildSeeds():
  # gets the seeding or playoff rank if present
    seeds = {}
    for event in data.get("events", []):
        for competitor in event["competitions"][0]["competitors"]:
            team_abbr = competitor["team"]["abbreviation"] + "_CFB"
            seed = competitor.get("seed", {}).get("rank")
            if not seed and "curatedRank" in competitor:
                seed = competitor["curatedRank"].get("current")
            seeds[team_abbr] = int(seed) if seed else None
    return seeds
  
def calculate_score(home, away):
    r = rivalry(home, away)
    m = marketability(home, away)
    c = competitiveness(home, away)
    q = qualityOfPlay(home, away)
    g = gameImportance(home, away)

    print(f"DEBUG {home} vs {away} → R:{r} M:{m} C:{c} Q:{q} G:{g}")
    return round((r + m + c + q + g), 2)

def rivalry(home, away):
    rating = 0
    if team_division.get(home) == team_division.get(away):
        rating += 5
    for t1, t2, r in rivalries:
        if (t1 == home and t2 == away) or (t2 == home and t1 == away):
            rating += r
    return rating
  
def marketability(home, away):
    return team_marketability.get(home, 5) + team_marketability.get(away, 5)

def qualityOfPlay(home, away):
    seeds = buildSeeds()
    records = buildRecords()
    homeRank = seeds.get(home, 0)
    awayRank = seeds.get(home, 0)
    homeRecord = list(map(int, records.get(home, "0-0").split("-")))
    awayRecord = list(map(int, records.get(away, "0-0").split("-")))
    combinedWins = float(homeRecord[0] + awayRecord[0])
    gamesPlayed = float(homeRecord[0] + homeRecord[1] + awayRecord[0] + awayRecord[1])
    if gamesPlayed == 0:
        return 0
    quality = round(((combinedWins / gamesPlayed)*10), 3)
    if homeRank != 0:
      quality += (25 - homeRank) // 2
    if awayRank != 0:
      quality += (25 - awayRank) // 2
    return quality

def competitiveness(home, away):
    records = buildRecords()
    homeRecord = records.get(home, "0-0").split("-")
    awayRecord = records.get(away, "0-0").split("-")
    winDiff = abs(int(homeRecord[0]) - int(awayRecord[0]))
    return max(1, 10 - winDiff)

def gameImportance(home, away):
    records = buildRecords()
    seeds = buildSeeds()
    importance = 2
    homeRecord = records.get(home, "0-0").split("-")
    awayRecord = records.get(away, "0-0").split("-")
    homeGamesPlayed = sum(map(int, homeRecord))
    awayGamesPlayed = sum(map(int, awayRecord))
    home_seed = seeds.get(home)
    away_seed = seeds.get(away)
    gamesLeft = season_length - max(homeGamesPlayed, awayGamesPlayed)
    
    if gamesLeft <= 10:
        importance += 1
    if gamesLeft <= 6:
        importance += 1
    if gamesLeft <= 3:
        importance += 1
    if home_seed and home_seed <= 10:
        importance += 2
    if away_seed and away_seed <= 10:
        importance += 2
    return importance
